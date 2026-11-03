# Day 18: Specs that agents can execute

Phase 3 starts. Question for the day: does a written spec make an AI coding agent's output better than a vague prompt, and which parts of the spec did the work?

## What I did
- **A spec format** (`specs/README.md`, `specs/TEMPLATE.md`). The plan asked for goal, context, acceptance criteria, out of scope. I added **Deliverables** (exact paths and
  signatures), **Constraints**, **Verification** (commands and expected results) and **Open questions** (decisions the agent must raise, not make). Each addition answers a
  specific way an agent goes wrong; the table in the README says which.
- **Spec 001, BillPay page object + 5 tests** (`specs/001-billpay-page-and-tests.md`). The app facts in it came from probing the live page first (message texts, which ones repeat,
  that all 13 messages sit hidden in the DOM, that `#fromAccountId` exists only on the confirmation page, balance and activity after a payment, that 0 and -5 are accepted).
- **The comparison.** Two agents of the same model as me (Sonnet 5.5, spawned with the Agent tool, fresh context, each in its own git worktree, same operating notes):
  - *vague*: "Add a BillPay page object and 5 tests for ParaBank's Bill Pay page." Its checkout was built from `main`, so it had no `specs/` folder.
  - *spec*: "Implement `specs/001-billpay-page-and-tests.md`."
  - The rubric is the spec's own acceptance criteria as a script, `scripts/spec_scorecard.py`, **committed before either output was scored**. Evidence: `reports/day18/`.
- **Adopted the spec run's code into the repo, unedited**, so Day 20 reviews an unmodified baseline. The vague run is kept as `reports/day18/vague.patch`.

## Results (one run each)

| | Spec run | Vague run |
|---|---|---|
| Tests collected / passing, serial and 3 x `-n 3`, reruns off | 5 / 5, 5 / 5 | 5 / 5, 5 / 5 |
| Repo checks (locator quality, lint, docstrings, parse) | pass | pass |
| Banned constructs (sleep, `.nth`, `.first`, XPath) | none | none |
| Every test ends in `expect(...)`; assertions in the page object | yes; 0 | yes; 0 |
| Interface and test names as specified | yes | no: 4 of 10 members named differently, 5 of 5 test names differ (**it could not know them**) |
| Files changed outside the deliverables | none | 1: `accounts_page.py` (+1 small method) |
| Non-semantic locators (registered in `ACCEPTED`) | 3 | **0** |
| Locator audit score (baseline 2.58) | 2.56 | **2.70** |
| Lines (page object + tests) | 87 + 113 | 92 + 105 |
| Effort reported by the harness | 17 tool calls, ~78k tokens, 4.3 min | 26 tool calls, ~97k tokens, 6.3 min |

Full suite with the spec run's code merged in: 499 passed, 1 skipped, 2 xfailed, serial and `-n 3`, reruns off.

Reading the two outputs side by side:
- **Coverage was decided by the spec.** The spec run has a "form shows every field" test and checks the activity row after paying. The vague run spent two of its five tests on a
  payment (confirmation, balance) and has neither of those.
- **Assertion strength is mixed.** The vague run's three "rejected" tests also record the browser's POSTs and assert none was sent, so "rejected" means nothing reached the server.
  I checked that its filter (`POST` + `/bank/billpay`) matches a real payment request (`.../services_proxy/bank/billpay?accountId=...`), so it is not vacuous. The spec run asserts only
  that the confirmation is absent. The spec run checks the balance with an exact pattern and the activity debit; the vague run uses `to_contain_text` on the balance and does not look at activity.
- **Both probed the live page** before writing locators. The spec's fact section did not replace that; it made it shorter (fewer tool calls), and all four facts the spec run re-checked matched.

## What made the spec work
1. **A fixed interface and a named list of tests.** This is what makes the output reviewable and scoreable by a script. A vague prompt gets reasonable but unpredictable names, so
   two runs cannot be diffed, and the agent chooses the coverage.
2. **Deliverables + Out of scope held the scope.** The vague run edited an existing page object (a sensible addition, but it is exactly the kind of change a reviewer has to notice).
3. **Facts with a date** probably saved effort (about 20% fewer tokens, one run, so not a measurement).
4. **Verification commands.** Both runs ran the repo's own checks, the spec run because it was told to, the vague run on its own initiative.

## What did not work, and a defect in my spec
- **An agent follows a spec's mistakes faithfully.** I wrote that the form fields have no accessible name, so the selectors are non-semantic and must be registered in `ACCEPTED`.
  The vague run found that every input is reachable through its table row's accessible name (`get_by_role("row", name=re.compile("^Payee Name:"))` then `get_by_role("textbox")`), which made
  all its locators semantic. My sentence was an assumption written as a fact, and it closed off the better option. I would not have found out without the control run. Rule for specs:
  **state facts, and mark design hints as hints.**
- **The repo already enforces most conventions with tests** (locator quality, lint, docstrings, parse). The vague agent ran them and met them without being told. Where a convention is
  enforced by a test, a written spec adds little about style; the spec earns its keep on *what to build and what to leave alone*. For Day 19 this suggests instruction files matter most for
  rules that no test enforces.

## Limits of this comparison
- One run per arm, one model, and the model is the same family as the one that wrote the spec. This shows what a spec changed in these two runs, not how often.
- The scorecard measures structure and stability. It does not measure whether a test would catch a defect; there is no mutation check yet.
- **Rubric weaknesses, left as they are so Day 19 stays comparable:** criteria 1 and 4 (names) cannot be met by a run that never saw the spec, so read them as "conformance", not "quality".
  `7_payment_test_uses_new_customer_page` is `False` for the vague run only because the scorecard finds the payment test by the word "success" in its name; I read it, and both its payment tests do use `new_customer_page`.
- The vague run reports two ParaBank behaviours I have not verified: `12abc` as an amount passes the client-side check and gives an internal error; and, as I saw myself, 0 and -5 are accepted.

## Carried to Day 20 (review of the adopted, unedited spec-run tests)
- Replace the id-based `field_error` and the name-attribute inputs with the row-based semantic locators from the vague run; then delete the three `ACCEPTED` entries and raise `MIN_SCORE`.
- The reused `ACCEPTED["input[name='{}']"]` entry still says "registration inputs"; and the `MIN_SCORE` comment ("current score is 2.58") is stale (2.56 now).
- The three "rejected" tests assert absence of a confirmation only. Add the no-request assertion.
- Check the assertion on the balance and the activity row against the review checklist (Day 20), and add a mutation-style check to the scorecard if the checklist needs one.

## Process notes
- My first probe of the success flow read the overview table right after `goto` and saw no rows: the tables fill in asynchronously. That went into the spec as a fact.
- A later probe timed out after submitting an amount of `1e3`; not investigated.
