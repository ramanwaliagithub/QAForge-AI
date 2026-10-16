# Day 08
- `ai_testgen/codegen.py`: renders `prompts/codegen.md` with the test case JSON plus a **signature-only summary of the real page objects** (built with `ast`, so it never goes stale), asks the model for one pytest test, strips fences, and statically checks it (`ast.parse`, exactly one `test_` function, no sleeps, has an assertion). On a failed check the error is fed back and the model retries (max 2). Files are written as `ai_testgen/generated/test_<story>_<nn>_<slug>.py`.
- `scripts/gen_tests.py` generates from the saved test cases; `scripts/run_generated.py <label>` runs them (`-m ai`) and writes `reports/testgen/<label>.json`.
- Moved `tests/conftest.py` to the repo root so generated tests share the same fixtures.
- Safety: generated code runs unsandboxed in the pytest process. I audited the imports (only pytest, playwright, our page objects) before running and the files are committed for review. Do not auto-run generated code from untrusted prompts.

## Result: 0 / 15 passed (llama3.1:8b, T=0, no page context)

All 15 files passed the static checks (valid Python, one test, has an assertion) and still none passed. Static validity says nothing about correctness.

| Failure reason | Count | Detail |
|---|---|---|
| Guessed locator never matched (30s timeout) | 7 | Transfer Funds and Bill Pay have no page objects; the model invented labels like "Transfer Amount" |
| Invented page-object API | 4 | `accounts.get_by_role(...)`, `accounts.get_by_label(...)` do not exist on `AccountsPage` |
| Misused a real helper | 2 | `BasePage.click/fill` take a `Locator`; the model passed a Locator to `page.click` or a plain string |
| Undefined name | 1 | called bare `get_by_role(...)` without `page.` |
| Invented expected text | 1 | asserted "No funding account selected"; ParaBank's real wording is different |

Other observations:
- The model ignored the provided example and the rule to prefer page-object methods: the open-account tests call `open_new_account(...)` correctly at the end but first try a made-up manual form flow.
- Several tests inherited bad test-case content from Day 7 (e.g. "account not owned", opening an account with a typed "Initial Balance" field that does not exist).
- A wrong locator costs 30s (Playwright default action timeout), so a bad run is slow. Worth lowering the action timeout for generated tests.
- Day 9 target: give the model the real page DOM/accessibility snapshot so locators are real, then compare against this 0/15 baseline.
