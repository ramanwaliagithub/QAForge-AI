"""Offline probe: what would the healing guard and the suggester do with the failures of the generated tests?

Usage: uv run python -m scripts.probe_generated_failures [failures_dir]
Reads the failure contexts the suite saved for ai_testgen/generated (default reports/failures), reports the guard's
verdict per failure, and for those the guard would attempt, forces one suggestion from the model. Needs Ollama; no
ParaBank. Nothing is executed or written to source. Writes reports/phase2/generated_probe.json.
For these failures there is usually no correct locator (the test asserts on text the app never shows, or fills a field
the app does not have), so any suggestion that validates is a FALSE heal; that is what the probe counts.
"""
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from framework.healing.collector import load_failure_context
from framework.healing.suggester import open_snapshot, should_attempt, suggest_locator
from framework.llm_client import get_client

load_dotenv()
folder = Path(sys.argv[1] if len(sys.argv) > 1 else "reports/failures")
contexts = [load_failure_context(p) for p in sorted(folder.glob("*.json")) if "ai_testgen" in p.name]
client = get_client()
rows = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    for ctx in contexts:
        e = ctx.error
        row = {"test": ctx.test_id.split("::")[-1], "kind": e.kind, "heal_hint": e.heal_hint, "raised_in": e.raised_in,
               "action": e.action, "locator": e.locator, "guard_attempts": should_attempt(ctx),
               "suggestion": None, "validated": False}
        if row["guard_attempts"]:
            context, page = open_snapshot(browser, ctx)
            result = suggest_locator(client, ctx, page, max_attempts=3, temperature=0.0)
            context.close()
            row.update(validated=result.healed, suggestion=result.source,
                       attempts=len(result.attempts), rejections=[a.rejected_because for a in result.attempts if a.rejected_because])
        rows.append(row)
    browser.close()

summary = {"failures": len(rows), "by_kind": {}, "by_hint": {}, "guard_would_attempt": sum(r["guard_attempts"] for r in rows),
           "validated_suggestions": sum(r["validated"] for r in rows),
           "reached_healer_at_run_time": sum(r["raised_in"] == "page_object" for r in rows)}
for r in rows:
    summary["by_kind"][r["kind"]] = summary["by_kind"].get(r["kind"], 0) + 1
    summary["by_hint"][r["heal_hint"]] = summary["by_hint"].get(r["heal_hint"], 0) + 1
out = Path("reports/phase2")
out.mkdir(parents=True, exist_ok=True)
(out / "generated_probe.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=2) + "\n")
for r in rows:
    print(f"{r['kind']:26} hint={r['heal_hint']:8} in={r['raised_in']:11} guard={str(r['guard_attempts']):5} {r['test']}"
          + (f"  -> {r['suggestion']}" if r["suggestion"] else ""))
print(json.dumps(summary, indent=1))
