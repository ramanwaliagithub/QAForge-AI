"""Measure the locator suggester on the committed failure samples.

Usage: uv run python -m scripts.heal_eval [label] [temperature] [runs]
For every sample: would the guard attempt it, and if forced, what does the model do? A suggestion only counts as
CORRECT if it resolves to the same element a person would pick (GROUND_TRUTH), not merely to some single element.
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
SAMPLES = Path("framework/healing/samples")
LABEL = sys.argv[1] if len(sys.argv) > 1 else "heal_eval"
TEMPERATURE = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
RUNS = int(sys.argv[3]) if len(sys.argv) > 3 else 1

# The element a person would pick for each broken locator. For the controls there is no valid answer.
GROUND_TRUTH = {
    "id_renamed": {"id": "amount"},
    "button_text_changed": {"tag": "input", "type": "submit", "value": "Transfer"},
    "locator_too_generic": {"id": "fromAccountId"},
}
ORDER = ["id_renamed", "button_text_changed", "locator_too_generic", "expect_on_missing_element", "wrong_text_on_found_element"]


def matches_truth(element: dict, truth: dict) -> bool:
    return all(element.get(k) == v for k, v in truth.items())


client = get_client()
rows = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    for name in ORDER:
        ctx = load_failure_context(next(SAMPLES.glob(f"*test_sample_{name}.json")))
        for run in range(RUNS):
            context, page = open_snapshot(browser, ctx)
            result = suggest_locator(client, ctx, page, max_attempts=3, temperature=TEMPERATURE)  # forced: guard bypassed
            context.close()
            truth = GROUND_TRUTH.get(name)
            correct = bool(result.healed and truth and matches_truth(result.element, truth))
            rows.append({
                "sample": name, "kind": ctx.error.kind, "guard_attempts": should_attempt(ctx), "run": run + 1,
                "healed": result.healed, "correct": correct, "attempts": len(result.attempts),
                "suggestion": result.source, "element": result.element,
                "rejections": [a.rejected_because for a in result.attempts if a.rejected_because],
                "first_try_valid": bool(result.attempts and result.attempts[0].validation and result.attempts[0].validation.ok),
            })
    browser.close()

locator_rows = [r for r in rows if r["sample"] in GROUND_TRUTH]
control_rows = [r for r in rows if r["sample"] not in GROUND_TRUTH]
summary = {
    "label": LABEL, "temperature": TEMPERATURE, "runs": RUNS,
    "locator_cases": len(locator_rows),
    "healed_correctly": sum(r["correct"] for r in locator_rows),
    "healed_wrong_element": sum(r["healed"] and not r["correct"] for r in locator_rows),
    "not_healed": sum(not r["healed"] for r in locator_rows),
    "first_try_valid": sum(r["first_try_valid"] for r in locator_rows),
    "controls": len(control_rows),
    "controls_falsely_healed_if_guard_off": sum(r["healed"] for r in control_rows),
    "controls_attempted_with_guard": sum(r["guard_attempts"] for r in control_rows),
}
out = Path("reports/healing")
out.mkdir(parents=True, exist_ok=True)
(out / f"{LABEL}.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=2) + "\n")

for r in rows:
    tag = "CORRECT" if r["correct"] else ("healed-WRONG" if r["healed"] else "not healed")
    print(f"{r['sample']:28} {r['kind']:26} guard={str(r['guard_attempts']):5} attempts={r['attempts']}  {tag:12} {r['suggestion']}")
    for why in r["rejections"]:
        print(f"{'':28}   rejected: {why}")
print(json.dumps(summary, indent=1))
