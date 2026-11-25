"""Score the model's triage (app_bug, test_bug, ui_change, environment, unclear) against the classes accepted in reports/bugs/ground_truth.json.

    uv run python -m scripts.triage_eval [--dir=reports/bugs]

Reads <dir>/summary.json written by scripts.draft_bug_reports. 'unclear' is counted apart: it is not right, but it is the honest answer when the facts
cannot decide, and it sends the report to a person instead of to the wrong team.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def score(rows: list[dict], truth: dict) -> dict:
    """Right, unclear and wrong counts, and the wrong ones listed as 'input: said X, accepted Y'."""
    right = [r for r in rows if r.get("classification") in truth[r["input"]]["classes"]]
    unclear = [r for r in rows if r.get("classification") == "unclear" and r not in right]
    wrong = [f"{r['input']}: said {r.get('classification')}, accepted {truth[r['input']]['classes']}" for r in rows if r not in right and r not in unclear]
    return {"total": len(rows), "right": len(right), "unclear": len(unclear), "wrong": len(wrong), "wrong_items": wrong}


def main(argv: list[str]) -> None:
    """Print the score for the summary in `--dir`."""
    flags = dict(a[2:].split("=", 1) for a in argv if a.startswith("--") and "=" in a)
    folder = ROOT / flags.get("dir", "reports/bugs")
    truth = json.loads((ROOT / "reports/bugs/ground_truth.json").read_text())["failures"]
    summary = json.loads((folder / "summary.json").read_text())
    result = score(summary["rows"], truth)
    (folder / "triage_eval.json").write_text(json.dumps({"prompt": summary.get("prompt", "default"), **result}, indent=2) + "\n")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
    sys.exit(0)
