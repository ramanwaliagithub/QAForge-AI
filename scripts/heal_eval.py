"""Measure the locator suggester on the committed failure samples.

Usage: uv run python -m scripts.heal_eval [label] [temperature] [runs] [tuned|heldout|heldout2|all]
For every sample: would the guard attempt it, and if forced, what does the model do? A suggestion only counts as
CORRECT if it resolves to the element a person would pick (framework/healing/ground_truth.py), not merely to some
single element. Controls have no valid answer, so any "heal" there is a false heal.
`tuned` samples were used while writing the prompt; `heldout` was used to diagnose it afterwards; `heldout2` was written
after that and is the unbiased one. Report them separately.
"""
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from framework.healing.collector import load_failure_context
from framework.healing.ground_truth import CONTROLS, HELDOUT, HELDOUT2, TUNED, matches
from framework.healing.suggester import open_snapshot, should_attempt, suggest_locator
from framework.llm_client import get_client

load_dotenv()
ARGS = [a for a in sys.argv[1:]]
LABEL = ARGS[0] if len(ARGS) > 0 else "heal_eval"
TEMPERATURE = float(ARGS[1]) if len(ARGS) > 1 else 0.0
RUNS = int(ARGS[2]) if len(ARGS) > 2 else 1
WHICH = ARGS[3] if len(ARGS) > 3 else "all"

SETS = []  # (set name, folder, truth dict or None for controls)
if WHICH in ("tuned", "all"):
    SETS += [("tuned", "samples", {n: t for n, t in TUNED.items()}), ("controls", "samples", {n: None for n in CONTROLS})]
if WHICH in ("heldout", "all"):
    SETS += [("heldout", "samples_heldout", {n: t for n, t in HELDOUT.items()})]
if WHICH in ("heldout2", "all"):
    SETS += [("heldout2", "samples_heldout2", {n: t for n, t in HELDOUT2.items()})]

client = get_client()
rows = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    for set_name, folder, truths in SETS:
        for name, truth in truths.items():
            ctx = load_failure_context(next(Path("framework/healing", folder).glob(f"*_{name}.json")))
            for run in range(RUNS):
                context, page = open_snapshot(browser, ctx)
                result = suggest_locator(client, ctx, page, max_attempts=3, temperature=TEMPERATURE)  # guard bypassed on purpose
                context.close()
                first = result.attempts[0] if result.attempts else None
                rows.append({
                    "set": set_name, "sample": name, "kind": ctx.error.kind, "guard_attempts": should_attempt(ctx), "run": run + 1,
                    "healed": result.healed, "correct": bool(result.healed and truth and matches(result.element, truth)),
                    "attempts": len(result.attempts), "suggestion": result.source, "element": result.element,
                    "rejections": [a.rejected_because for a in result.attempts if a.rejected_because],
                    "first_try_valid": bool(first and first.validation and first.validation.ok),
                })
    browser.close()


def summarize(set_name):
    r = [x for x in rows if x["set"] == set_name]
    return {
        "cases": len(r), "correct": sum(x["correct"] for x in r),
        "healed_wrong_element": sum(x["healed"] and not x["correct"] for x in r),
        "not_healed": sum(not x["healed"] for x in r), "first_try_valid": sum(x["first_try_valid"] for x in r),
    }


summary = {"label": LABEL, "temperature": TEMPERATURE, "runs": RUNS}
for s in ("tuned", "heldout", "heldout2"):
    if any(x["set"] == s for x in rows):
        summary[s] = summarize(s)
if any(x["set"] == "controls" for x in rows):
    c = [x for x in rows if x["set"] == "controls"]
    summary["controls"] = {"cases": len(c), "falsely_healed_if_guard_off": sum(x["healed"] for x in c),
                           "attempted_with_guard_on": sum(x["guard_attempts"] for x in c)}
out = Path("reports/healing")
out.mkdir(parents=True, exist_ok=True)
(out / f"{LABEL}.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=2) + "\n")

for r in rows:
    tag = "CORRECT" if r["correct"] else ("healed-WRONG" if r["healed"] else "not healed")
    print(f"[{r['set']:8}] {r['sample']:26} guard={str(r['guard_attempts']):5} attempts={r['attempts']} {tag:12} {r['suggestion']}")
    for why in r["rejections"]:
        print(f"{'':12}   rejected: {why}")
print(json.dumps(summary, indent=1))
