# Day 14: LLM locator suggestion with validation

## What was built (`framework/healing/`)
- `suggestion.py`: a suggestion is **data**: `{strategy: role|label|text|placeholder|css, role, name, exact, text, css}`. We validate the fields and build the Playwright locator ourselves. The model's output is never executed (a test proves a hostile string is only quoted into source).
- Validation against the DOM captured in the failure context (loaded as a static page, JS off, offline, so counts are exactly what was captured). Rejected: unchanged locator, fragile CSS (class, structure, position, XPath), **zero or many matches**, an element the intended action cannot work on (a `fill` needs a text input, `select_option` a `<select>`), and an element of a different role than the failed locator asked for.
- `suggester.py`: builds the prompt, calls the LLM (JSON mode), validates, and on rejection **re-prompts with the reason and the list of everything already rejected** (max 3 attempts). `should_attempt()` is the guard: only `heal_hint == "locator"` is attempted by default.
- Evaluation: `scripts/heal_eval.py` scores against `ground_truth.py` (the element a person would pick), not just "matched one element". Four sample sets of broken locators plus 2 controls; `tests/test_healing_ground_truth.py` proves every sample contains its right answer exactly once, so a "miss" is never an unanswerable sample.

## Result for the plan's measurement ("how many of your 3 broken locators were healed")
**3 of 3** at temperature 0 (2 first try, 1 after one rejection). **That number is not trustworthy on its own**: I changed the prompt four times while looking at those exact three samples. What matters is below.

## The honest numbers (llama3.1:8b, local, T=0 unless stated)
Each set was measured **before** I fixed what it revealed, so these are unbiased at the time of measurement:

| Set | Correct | Healed the WRONG element | Not healed | Note |
|---|---|---|---|---|
| tuned (3) | 3/3 | 0 | 0 | prompt was built around these; optimistic |
| held-out 1 (4) | 2/4 | 0 | 2 | copied the old broken locator 3 times; wrote invalid `#customer.firstName` |
| held-out 2 (4) | 2/4 | **1** | 1 | healed a button to an unrelated link; copied the `css=` prefix |
| held-out 3 (4) | 1/4 | 0 | 3 | dotted ids again (2); chained expect precondition (1) |
| **pooled unbiased (12)** | **5/12 = 42%** | **1/12** | 6 | |

After the generic fixes below, re-measured (these sets are now *diagnosed*, so optimistic):
- T=0: **14/15 correct, 0 wrong**. The only miss is the chained-expect precondition case.
- T=0.7, 3 runs each (45 cases): **41/45 correct**; among cases the guard would attempt (`heal_hint=locator`): **38/39 correct, 0 wrong, 1 not healed**. The 2 wrong heals are both `maybe`-class cases.
- Controls (an assertion failed; no locator is at fault): **6/6 "healed" if the guard is off, 0 attempted with the guard on.**

## What I learned
1. **DOM validation cannot tell a real fix from a plausible wrong one.** `get_by_text("Transfer Complete!")` matches exactly one element, so it passes every check, and it "heals" a failed assertion. The same happened for a button healed to a link. Three layers were needed: the `heal_hint` guard, keeping the failed locator's role, and (planned for Day 15) re-running the test step to see whether it passes, not just whether the locator resolves.
2. **How the page is presented mattered more than prompt wording.** Going from 0/3 to 3/3 came from: (a) a prompt bug of mine (the model copied `"role | label | ..."` literally), (b) listing only elements the intended action can work on, (c) describing each as the accessibility tree does: role and accessible name, or "NO accessible name; css=...". The model had been picking the loudest text on the page (the heading) because nothing told it an `<input type=submit value=Transfer>` is a button named "Transfer".
3. **Failure patterns of the 8B model:** it anchors on the failed locator and repeats it; it ignores rejection feedback and repeats the same wrong suggestion; it rewrites a ready-made `[id='customer.lastName']` into the invalid `#customer.lastName` every time (same trap as Day 9). Fixes: the "already rejected, do not repeat" list, and a mechanical repair that only fires when an element with exactly that dotted id exists (and the result is still validated). Repairs are recorded (`repaired_from`).
4. **Assertions raised inside page objects were misclassified** (found by generating samples): `expect(...).to_have_count()` in a page object looks like a product assertion but means the page object's locator is stale. New kind `page_object_precondition` (hint `maybe`). These are also the hardest for the suggester: with no `fill`/`click` on the failing line there is nothing to narrow candidates by, and the model produced nonsense (`get_by_role("option", name="Open New Account")`).
5. **Iterating on the samples you score on inflates the score.** After each fix the set that exposed it stops being held-out, so I wrote a fresh set (3 sets in total). Unbiased pooled accuracy is 42%, not the 100% of the tuned samples.

## Limits (be honest in the Day 17 write-up)
- 17 samples on one app (ParaBank), all synthetic renames; real redesigns are messier. Pages are tiny (about 30 elements). A bigger page would need ranking/trimming of candidates.
- Validation uses the DOM captured at failure time. It does not prove the *test* passes with the new locator: Day 15 must retry the step.
- One model (llama3.1:8b). A stronger model would likely reduce repeats and wrong picks; the harness and numbers make that comparison easy.
- The evaluation runs on saved failure contexts, so it needs only Ollama, not a running ParaBank; regenerating the samples does need ParaBank.

## Files
`framework/healing/{suggestion,suggester,ground_truth}.py`, `framework/healing/prompts/suggest_locator.md`, sample sets in `framework/healing/samples*/`, evaluation results in `reports/healing/` (day14_t0 -> v4 show the prompt iterations; `day14_heldout*_t0` are the unbiased pre-fix measurements; `day14_all_*` are the post-fix runs).
