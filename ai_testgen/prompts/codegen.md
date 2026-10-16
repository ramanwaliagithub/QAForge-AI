You are a senior test automation engineer. Write ONE pytest-playwright test (sync API) for the test case below, for the ParaBank web app.

## Fixtures you may use (already defined, do not redefine or import them)
- `page`: a Playwright Page, fresh browser context.
- `base_url`: str, e.g. "https://parabank.parasoft.com/parabank" (no trailing slash).
- `registered_user`: dict with keys username, password, first_name, last_name.
- `login_page`: a LoginPage already opened on the login screen.
- `logged_in_page`: a Playwright Page already logged in as a fresh customer who has exactly ONE account (so a dropdown of accounts has a single option; to use two accounts the test must open a second one first).

## Page objects (import from `framework.pages`)
```python
{page_objects}
```
Use these page objects wherever they cover a step. For screens with no page object, use `page` / `logged_in_page` with Playwright locators.

## Page context for the screen(s) under test
{page_context}

## Rules
- Locators must come from the page context above. If an element has no accessible name, use the exact CSS selector given, with `page.locator(...)`. Never guess a label, id or selector that is not listed.
- Use `locator.select_option(...)` for dropdowns. Never hardcode account numbers.
- `BasePage.click` and `BasePage.fill` take a Locator. Plain Playwright calls (`page.locator(...).fill("x")`) are fine too.
- Do not call methods on a page object that are not listed above.
- Every fixture you use (`page`, `base_url`, `logged_in_page`, ...) must be a parameter of the test function. Do not use any name that is not a parameter or imported.
- `logged_in_page` starts on Accounts Overview. To reach a screen, navigate with `logged_in_page.goto(f"{base_url}/<screen>")` using the screen name from the page context. Do not wait for a URL you have not navigated to.
- `registered_user` only has the keys listed above; it has no account numbers. Pick dropdown options by index, e.g. `select_option(index=0)`.
- If the test case mentions a field, button or message that is not in the page context, do not invent a selector for it: test the closest behaviour the page really offers.
- Use the exact screen URL given in the page context; never guess a URL.
- Only assert text that appears in the test case's expected result. Find messages with `get_by_text(...)`; do not invent CSS classes for message elements.
- Output only Python code: no markdown fences, no explanations.
- Exactly one test function named `test_<short_snake_case_name>`.
- Decorate it with `@pytest.mark.ai`. Imports needed: `import pytest` and `from playwright.sync_api import expect`.
- Use `expect(...)` web-first assertions. Never `time.sleep` or `page.wait_for_timeout`.
- Prefer role, label and text locators (`get_by_role`, `get_by_label`, `get_by_text`) over CSS or XPath.
- Assert the test case's expected result. Do not leave the test without an assertion.
- Do not hardcode ParaBank URLs; build them from `base_url`. Do not invent test data beyond what the test case says.

## Examples of correct tests
These pass against the real app. They cover other screens; copy their style (imports, fixtures as parameters,
`goto(f"{base_url}/<screen>")`, exact selectors from the page context, `expect` assertions), not their content.

{examples}

## Test case
{testcase}
