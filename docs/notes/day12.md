# Day 12: resilient locators

## What I did
- **Locator audit** (`framework/locator_audit.py`, `scripts/locator_audit.py`): reads the page objects with `ast` and ranks each locator by tier (semantic > form `name` attr > hand-written `#id` > other CSS > fragile), also flags `.nth/.first/.last`.
- **Refactor** of 8 locators to role/text based ones (details and before/after table in `docs/locator-quality-checklist.md`). Average score 2.00 -> 2.58 of 3; fragile 2 -> 1; position-dependent 2 -> 0.
- **Ratchet test** (`tests/test_locator_quality.py`): a new non-semantic locator fails the build unless it is in the `ACCEPTED` register with a reason; stale entries also fail; XPath/position banned; score floor 2.5.
- **Checklist** (`docs/locator-quality-checklist.md`) with the preference order, how to find a locator from the accessibility tree, and ParaBank's accessibility gaps.

## Things I learned about locators
- Role-based locators resolved to exactly one element in every case I tested; the CSS ones were the ones that were not unique (`p.error` matched 3 elements).
- `get_by_text("Your new account number:")` returns the `<b>` around the text, not the paragraph, so `.get_by_role("link")` inside it found nothing. Scope with `get_by_role("paragraph").filter(has_text=...)`.
- Many things stay non-semantic because ParaBank gives inputs and dropdowns no accessible name (labels are table cells). Those 8 locators are in the `ACCEPTED` register with reasons. The honest fix is in the app (labels, `role=alert`), not in the tests.
- A selector bug I had written without noticing: `#customer.firstName` (id with a dot) is "id + class" in CSS. Now `[id='customer.firstName']` (Day 9 follow-up, covered by a test).
- Correction to Day 11: an empty transfer amount shows two real validation messages **and** an internal error. My MCP digest had missed the first two; Playwright strict mode exposed them.

## Stability re-run: what I found (this was the surprise of the day)
Looping the whole suite (`-n 3`) turned up flakes that **were not caused by locators**; the same test failed with old and new locators.

**Root cause (reproduced): a ParaBank race on login.** `scripts/repro_parabank_login_race.py` runs bad logins while other users log in:
about 2.5% of failed logins (2/80, then 1/40) come back as a logged-in session belonging to another customer. With only bad logins, or bad logins plus registrations, 0 of 100. This is an application bug (session mix-up under concurrency; a security issue in a real system). It shows up in the suite as:
- `test_invalid_login_shows_error` landing on someone's Accounts Overview (screenshot evidence in the failure artifacts);
- valid logins ending up back on the login page (`test_logout_returns_to_login_form`);
- random setup timeouts in logged-in flows, and registration being rejected ("This username already exists" for a fresh uuid).

**Measured:** baseline loop of the suite with `-n 3` (stopped at about run 78 because the machine ran out of memory): 4 runs failed because of this race (runs 6, 45, 57, 59: about 5%), 1 run was lost to `BrowserType.launch: Timeout 180000ms` (not ParaBank: the laptop was out of free memory with Firefox, Chrome, Slack, VS Code and the Docker VM open), and 1 run needed a rerun.

**Mitigations**
1. `register_new_customer()` in `conftest.py`: one helper, retries registration with a new username up to 3 times; used by both `registered_user` and `new_customer_page`. (`new_customer_page` had no retry: that was my bug from Day 11 and it caused one of the failing runs.)
2. `--reruns 2 --reruns-delay 1` in `pytest.ini` for the suite (pytest-rerunfailures). The rerun count is printed in the summary line, so flakes are visible instead of hidden. `scripts/run_generated.py` passes `--reruns 0` because a pass-rate experiment must not hide failures.

**After:** 40 runs, 0 failing, 0 needed a rerun. That is **not proof** the policy works: at a ~5% flake rate, 0 in 40 happens about 1 time in 8 by chance. It is consistent with it. An earlier run with a one-test rerun did save run 30 (one rerun, then pass).

## Tradeoffs and open items
- Blanket reruns can mask a genuinely flaky new test. Mitigation: the rerun count is visible; Day 15-17 should track flake rate per test (a flaky-test report) instead of relying on a summary line.
- The race is an app bug worth filing against ParaBank; the reproduction script is the evidence.
- Do not run huge test loops while the machine is low on memory: the numbers get polluted (browser launch timeouts).
