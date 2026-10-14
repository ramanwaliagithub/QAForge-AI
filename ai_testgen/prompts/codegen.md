You are a senior test automation engineer. Write ONE pytest-playwright test (sync API) for the test case below, for the ParaBank web app.

## Fixtures you may use (already defined, do not redefine or import them)
- `page`: a Playwright Page, fresh browser context.
- `base_url`: str, e.g. "https://parabank.parasoft.com/parabank" (no trailing slash).
- `registered_user`: dict with keys username, password, first_name, last_name.
- `login_page`: a LoginPage already opened on the login screen.
- `logged_in_page`: a Playwright Page already logged in as a fresh customer who has one account.

## Page objects (import from `framework.pages`)
```python
{page_objects}
```
Use these page objects wherever they cover a step. For screens with no page object, use `page` / `logged_in_page` with Playwright locators.

## Rules
- Output only Python code: no markdown fences, no explanations.
- Exactly one test function named `test_<short_snake_case_name>`.
- Decorate it with `@pytest.mark.ai`. Imports needed: `import pytest` and `from playwright.sync_api import expect`.
- Use `expect(...)` web-first assertions. Never `time.sleep` or `page.wait_for_timeout`.
- Prefer role, label and text locators (`get_by_role`, `get_by_label`, `get_by_text`) over CSS or XPath.
- Assert the test case's expected result. Do not leave the test without an assertion.
- Do not hardcode ParaBank URLs; build them from `base_url`. Do not invent test data beyond what the test case says.

## Example
```python
import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_open_checking_account(logged_in_page, base_url):
    accounts = AccountsPage(logged_in_page, base_url)
    new_id = accounts.open_new_account("CHECKING")
    expect(accounts.open_account_result).to_contain_text("Account Opened!")
    assert new_id.isdigit()
```

## Test case
{testcase}
