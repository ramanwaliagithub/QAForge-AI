"""Draft a bug report for each saved failure and flag the ones that look like duplicates of an earlier report.

    uv run python -m scripts.draft_bug_reports [failure.json ...] [--out=reports/bugs] [--inputs=reports/bugs/inputs] [--threshold=0.75] [--prompt=strict]

Default input is every JSON file in reports/bugs/inputs (copies of saved failures, so the run can be repeated). Writes <out>/<id>.md and <out>/<id>.json (the draft as data) per failure,
<out>/index.json (the embedding index) and <out>/summary.json (one row per failure: triage, attempts, dropped quotes, nearest earlier report).
The index is rebuilt from scratch on every run, so the result does not depend on an earlier run.
"""
import json
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from ai_testgen.bug_report import PROMPT, PROMPT_STRICT, DraftError, draft_bug_report, read_test_source, render_markdown, report_id
from ai_testgen.duplicates import SIMILAR_THRESHOLD, DuplicateIndex, as_dict, fingerprint
from framework.healing.collector import load_failure_context
from framework.llm_client import get_client
from scripts.flags import parse_flags

ROOT = Path(__file__).resolve().parent.parent


def main(argv: list[str]) -> None:
    """Draft, check and save one report per failure; print a one-line result for each."""
    load_dotenv()
    flags, positional = parse_flags(argv, __doc__)
    out = ROOT / flags.get("out", "reports/bugs")
    threshold = float(flags.get("threshold", SIMILAR_THRESHOLD))
    inputs = [Path(a) for a in positional] or sorted((ROOT / flags.get("inputs", "reports/bugs/inputs")).glob("*.json"))
    out.mkdir(parents=True, exist_ok=True)
    client = get_client()
    model = getattr(client, "model", "unknown")
    index_path = out / "index.json"
    index_path.unlink(missing_ok=True)
    index = DuplicateIndex(getattr(client, "embed_model", "unknown"), index_path)
    rows: list[dict[str, Any]] = []
    for path in inputs:
        ctx = load_failure_context(path)
        start = time.perf_counter()
        try:
            report, info = draft_bug_report(client, ctx, read_test_source(ctx.test_id, ROOT), prompt=PROMPT_STRICT if flags.get("prompt") == "strict" else PROMPT)
        except DraftError as error:
            rows.append({"input": path.stem, "id": report_id(ctx), "error": str(error)})
            print(f"{path.stem:28} NO DRAFT ({error})", flush=True)
            continue
        rid = report_id(ctx)
        match = index.check_and_add(client, rid, report, threshold, fingerprint(ctx))
        nearest = index.nearest(index.records[-1]["vector"], exclude=rid)  # the closest earlier report, duplicate or not
        (out / f"{rid}.json").write_text(json.dumps({"input": path.stem, "report": report.model_dump(), "info": info}, indent=2, ensure_ascii=False) + "\n")
        (out / f"{rid}.md").write_text(render_markdown(report, ctx, info, model, as_dict(match)))
        rows.append({"input": path.stem, "id": rid, "test": ctx.test_id, "classification": report.classification, "severity": report.severity,
                     "title": report.title, "attempts": info["attempts"], "dropped_quotes": info["dropped_quotes"],
                     "matches": as_dict(match), "nearest": as_dict(nearest), "seconds": round(time.perf_counter() - start, 1)})
        print(f"{path.stem:28} {report.classification:11} dup={(match.kind + ' ' + match.id) if match else '-':32} {rows[-1]['seconds']}s", flush=True)
    index.save()
    (out / "summary.json").write_text(json.dumps({"model": model, "prompt": flags.get("prompt", "default"), "threshold": threshold, "rows": rows}, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
    sys.exit(0)
