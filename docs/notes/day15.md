# Day 15: opt-in self-healing fixture

## How it works
```
page object -> BasePage.click / fill / select_option -> _act()
   wait for element, perform the action
   on a Playwright error and a healer is active (--heal):
       classify the failure  -> guard: only `locator` problems are attempted
       ask the model for a replacement (validated on the LIVE page: exactly one match, right element kind, same role)
       retry the action ONCE with it
           works  -> outcome "healed"  (test continues; reported, never silent)
           fails  -> the ORIGINAL error is raised
```
Code: `framework/healing/runtime.py` (Healer), `framework/healing/plugin.py` (pytest flag, report), `framework/pages/base_page.py` (the hook).

## Safety rules, and where each is enforced
| Rule | How |
|---|---|
| Off by default | no healer is active without `--heal`; with none, errors propagate exactly as before (test) |
| Never heal an assertion | assertions are in tests, not in the helpers, so they never reach the healer; the guard also refuses non-`locator` kinds. E2E: with an EMPTY replay file the model would raise if asked; the report shows 0 events |
| Never write source | the only file written is the report. E2E tests hash every `.py` file before and after each `pytest --heal` subprocess |
| No silent passes | every verified heal raises `HealedLocatorWarning` (pytest warnings summary), is attached to Allure, listed in a "self-healing" summary section, and written to `reports/healing.json`. `-W error::framework.healing.plugin.HealedLocatorWarning` turns any heal into a failure for CI |
| A bad answer cannot hide the real failure | failed retry, no acceptable suggestion, a model outage or timeout: the test fails with its original error (all tested) |
| Bounded cost | one retry per action; `--heal-max-per-test` (default 3); model answers cached per (page, locator, action); the model client is created only on the first heal; `OLLAMA_TIMEOUT_S` |
| Page objects stay covered | ratchet test: page objects may only act through the BasePage helpers |

## Flags and outputs
`--heal`, `--heal-allow-maybe` (also try ambiguous kinds such as not_actionable), `--heal-max-per-test N`. Report `reports/healing.json` (override `HEAL_REPORT`; merged across xdist workers). Each event has: test, action, failed locator, kind, outcome, suggestion + reason + confidence, the element it resolved to, whether the retry verified it, where the locator is defined in source, the calling lines, attempts and rejection reasons, and `status: proposed` (the review step on Day 16 sets approved/rejected).

## Results
- **Unit (real browser page, scripted model), 13 tests:** heals fill/click/select; one retry only; failed retry re-raises the original error; guard skips `not_actionable` and never asks the model; `--heal-allow-maybe` opts in; assertions never healed; cache = one model call for two identical failures; per-test budget; model outage handled.
- **End to end (subprocess `pytest --heal`, real ParaBank, replay model), 6 tests:** heal + report + warning + source untouched; no flag = no change and no report; assertion failure untouched; unacceptable suggestions = original failure; `-n 2` merges worker events; `-W error` turns a heal into a failure.
- **Real model (llama3.1:8b) driving the real fixture over all 17 sample tests:** **13/13 locator failures healed, verified, and all 13 resolve to the correct element**, each in 1.3 to 4.3 s including the model call. The 4 that still fail are by design: 2 assertion controls (never attempted) and 2 `expect()` preconditions inside page objects (see limits). Evidence: `reports/healing_real_model.json`.

## Limits (be honest in the Day 17 write-up)
- **Coverage:** only click/fill/select via the BasePage helpers. A stale locator inside an `expect()` or wait in a page object (`TransferPage.open`, `AccountsPage.open_new_account`) is not healed (those 2 samples fail). Closing that gap means routing waits through a helper too.
- **"The retry succeeded" is not "the right element".** Verification proves the action worked, not that it hit the intended element: an unrelated but clickable element would also pass. The role constraint and validation reduce that risk (Day 14 measured 1 wrong heal in 12 unbiased cases); the report records the resolved element so a human can check it, and that is what the Day 16 review is for.
- The 13/13 uses the samples from Day 14, which the suggester was diagnosed on; the unbiased accuracy figure from Day 14 (42% at first sight, 38/39 on the guard-eligible cases afterwards) is the one to quote.
- Each heal costs a model call (cached within a worker process; xdist workers each have their own cache). In a real suite the first heal of a broken locator is slow; the rest reuse it.
- The warning fires per heal event, and reruns count separately; a flaky test that heals and then reruns will appear twice.
