# Username input not found

| | |
|---|---|
| Id | `bug-b0ffa18f` |
| Triage (the model's call, unverified) | **ui_change**, severity major |
| Failing test | `framework/healing/sample_tests/test_heldout_locators.py::test_heldout_username_renamed` |
| Page | ParaBank | Welcome | Online Banking (http://localhost:8080/parabank/index.htm) |
| Failure collected | 2026-10-30T10:33:49+00:00 |

## Summary
The test failed to find the username input field on the ParaBank login page. The test was trying to login with a username and password.

## Steps to reproduce
1. Open the ParaBank login page
2. Try to login with a username and password

## Expected
The username input field should be visible on the login page

## Actual
Locator.wait_for: Timeout 15000ms exceeded. waiting for locator("input[name='user']") to be visible

## Evidence (checked: each quote occurs in the failure)
- `Locator.wait_for: Timeout 15000ms exceeded.`
- `waiting for locator("input[name='user']") to be visible`

## Suspected cause
The username input field may have been renamed or moved on the login page.

## Next action
Verify the username input field is present on the login page and update the test locator if necessary.

## About this draft
- Drafted by `llama3.1:8b` from the failure log and the page's accessibility text; it did not see the screenshot (`heldout_username.png`).
- Attempts: 1.
- Triage and severity are a draft. A person confirms whether this is a product bug before it is filed.
