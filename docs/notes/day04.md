# Day 04
- `allure-pytest` + `--alluredir` in pytest.ini; `--clean-alluredir` avoids stale results mixing in. Allure CLI (`brew install allure`) turns results into HTML. `allure-results/` and `allure-report/` are git-ignored.
- Failure artifacts: a `pytest_runtest_makereport` hook stores the call report on the item; the `page` fixture checks it at teardown and, only on failure, saves a full-page screenshot and a Playwright trace zip to `test-results/` and attaches both to Allure. Tracing is always on (cheap) but only written when the test fails. Teardown order matters: screenshot must be taken before the context closes.
- Open a trace with `uv run playwright show-trace test-results/<name>.zip`.
- `DEMO_FAIL=1 pytest tests/test_failure_artifacts.py` triggers a deliberate failure; it is skipped otherwise.
- Logging: `framework/logging_utils.py` emits JSON lines to stderr (ts, level, logger, msg + any `extra=` fields). BasePage logs open/click/fill. Visible with `pytest -s`.
- Allure categorized the intentional failure as "Product defects" because it is an assertion failure; categories need custom config to separate flaky/locator issues (useful for Day 13+ healing).
