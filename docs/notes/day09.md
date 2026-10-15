# Day 09: grounding generation in the real page

## What was built
- `ai_testgen/grounding.py`: captures two views of a screen with Playwright (logged in, `#rightPanel`): the **accessibility snapshot** (`aria`) and a compact **interactive elements list** with exact CSS selectors (`elements`). Includes a token trimmer (drops bare row/cell noise, cuts at a line boundary to a budget, default 2000 tokens) and `build_context(mode)`.
- `scripts/capture_snapshots.py` saves snapshots to `ai_testgen/snapshots/` (committed, so generation is repeatable and offline). `scripts/gen_tests.py [none|aria|elements|both]` selects the context.
- Snapshots are tiny: ~140-400 tokens per story, far under the budget. Trimming matters for bigger apps, not ParaBank.
- Account ids in dropdowns are masked ("never hardcode"), and uuid-style ids (ParaBank gives the phone field a random one) are skipped in favour of `name=`.
- Codegen got stricter: pyflakes undefined-name check with feedback, prompt rules (declare fixtures as parameters, navigate with `goto(f"{base_url}/<screen>")`, `registered_user` has no accounts, don't invent CSS classes), and a 15s action timeout so bad locators fail faster.

## Finding 1: the aria snapshot cannot ground ParaBank's forms
ParaBank's inputs have **no accessible names** (the snapshot shows bare `textbox`), so `get_by_label` can never work. A selector list built from the DOM (`name`, `id`, button `value`) was needed. Accessibility-first locators (Day 12) only work on pages that are accessible; the snapshot is also a way to see that they are not.

## Finding 2: result, 15 test cases, llama3.1:8b, T=0, local ParaBank
| Context | Valid code (passed static checks) | Passed | Main failure types among those that ran |
|---|---|---|---|
| none (control, same rules) | 14/15 | **0** | 6 locator timeouts, 3 assertion, 3 invented page-object methods, 2 helper misuse |
| aria | 13/15 | **0** | 5 playwright errors, 4 invented methods, 3 assertion, 1 timeout |
| elements | 11/15 | **0** | 4 assertion, 3 timeouts, 2 helper misuse (`Page.fill` given a Locator), 2 invented methods |
(Day 8 baseline: 0/15, 7 of 15 were locator timeouts.)

**Grounding did not raise the pass rate (0 -> 0), but it changed what goes wrong.** In the `elements` runs the model uses real selectors (`#fromAccountId`, `input[value='Open New Account']`, `#amount`). What still fails:
- Invented fields/messages: `input[name='initialBalance']`, "Error: Insufficient funds in funding account". Many Day 7 test cases describe behaviour ParaBank does not have, so even a perfect coder cannot make them pass. **The test case content is now the bottleneck.**
- Code muddle by the 8B model: `expect(error_message)` on a string, `logged_in_page.click("...")` mixed with page-object calls, `AccountsPage.goto`.
- The model repeats the same mistake after feedback: 4 of the 4 `elements` codegen failures were "Undefined name: page" three times in a row, so the retry loop did not help.
- More context did not help here: `elements` produced valid code for the fewest cases (11/15 vs 14/15 for none).
- Not yet tried: a bigger model, few-shot examples of correct tests, or generating a constrained action list (e.g. JSON steps) that we turn into code ourselves instead of free-form Python.

## Environment lessons (cost most of the day)
- The public ParaBank demo started returning HTTP 500 on registration, which broke everything. Switched to **local Docker** (`docker compose up -d`): same app, suite 10s -> ~1.2s.
- ParaBank also has a **race on registration under parallel workers**: ~3 in 18 concurrent signups were rejected with "This username already exists" for a random uuid. `registered_user` now retries with a new username (12/12 clean parallel runs afterwards, vs 1 failure in 8 before).
- Early v2 numbers were invalid because of these setup failures. Always check *where* a test failed (setup vs call) before blaming the model.
