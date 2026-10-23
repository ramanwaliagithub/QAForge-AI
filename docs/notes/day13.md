# Day 13: failure context collector (healing step 1)

## What was built
- `framework/healing/errors.py`: turns an exception into facts: `kind`, `heal_hint`, the failing `locator`, the `action`, `timeout_ms`, the project source `frames`, and `raised_in` (page_object | test | other).
- `framework/healing/collector.py`: on failure writes `reports/failures/<test id>.json` and `.png` (override the folder with `FAILURE_DIR`). The JSON has the error, the live page (url, title, ARIA snapshot, a compact list of interactive elements, HTML up to 30 KB) and the screenshot file name. It **never raises**: every capture step is guarded and problems go into `page.capture_errors`.
- `conftest.py`: the report hook now keeps the exception object; the `page` and `new_customer_page` fixtures call the collector when the test body failed. Passing tests write nothing.
- `framework/healing/sample_tests/` + `scripts/make_failure_samples.py`: 3 deliberately broken locators plus 2 controls, run through the real hook; the 5 captured contexts are committed in `framework/healing/samples/` and are the input for Day 14.

## Failure kinds (the key design decision)
Day 15's guard rail is "heal locator failures, never assertion failures". That only works if the two can be told apart, so the collector classifies using Playwright's own wording (captured from real runs):

| kind | how it shows up | `heal_hint` |
|---|---|---|
| `locator_not_found` | timeout, call log says `waiting for <locator>` and never `locator resolved to` | **locator** |
| `strict_mode_violation` | `strict mode violation: ... resolved to N elements` | **locator** |
| `assertion_element_missing` | `expect(...)` failed with `element(s) not found` | **maybe** (renamed? or removed on purpose?) |
| `not_actionable` | locator matched, but wrong element type / not enabled | **maybe** |
| `assertion` | `expect` on a *found* element, or a plain `assert` | **no** (a possible product bug) |
| `timeout_other`, `other` | URL/navigation waits, anything else | no |

## A framework change this forced
`BasePage.click/fill` used `expect(locator).to_be_visible()` as a guard. That turns every broken locator into an *assertion* failure, indistinguishable from a real test assertion. They now use `locator.wait_for(state="visible")`, which raises a Playwright timeout (`locator_not_found`). Rule: **page objects wait, tests assert.** `raised_in` records which side the failure came from.

## Findings
- Two bugs in my own code were caught by tests: (1) `attempt("title", page.title)` evaluated the attribute outside the guard, so a broken page crashed the "never raises" collector; (2) `wait_for()` adds ` to be visible` to the logged locator, which leaked into the extracted locator expression.
- Samples confirm the data contains the answer: for the renamed id (`#amt`) the captured elements include the real `#amount` input; for the changed button text, the real `Transfer` submit button. A test asserts both, so Day 14 has something to find.
- `ErrorInfo.frames` points at the *call site* (`self.fill(self.amount, ...)` in transfer_page.py:49), not at the line that defines the locator. Day 16's apply step has to find the definition by searching the source for the failing locator expression. Noted as a limit.
- Failures raised by `expect()` *inside* page objects (`open_new_account` waits on the dropdown with `expect`) still classify as assertions. Acceptable for now; if it matters, convert those to `wait_for` too.
- Each rerun attempt overwrites the same file, so the JSON always describes the last attempt.
- Cost: ~16 KB JSON + ~125 KB PNG per failed test; `reports/failures/` is git-ignored, the committed samples are the only ones in git.
