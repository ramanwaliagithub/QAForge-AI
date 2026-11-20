# Username input not found

| | |
|---|---|
| Id | `bug-b0ffa18f` |
| Triage (the model's call, unverified) | **ui_change**, severity major |
| Failing test | `framework/healing/sample_tests/test_heldout_locators.py::test_heldout_username_renamed` |
| Page | ParaBank | Welcome | Online Banking (http://localhost:8080/parabank/index.htm) |
| Failure collected | 2026-10-30T10:33:49+00:00 |

## Summary
The test tried to login with a username, but the input field was not found. The page did not show the expected text.

## Steps to reproduce
1. Open the ParaBank website
2. Try to login with a username

## Expected
The username input field should be visible on the login page

## Actual
Locator.wait_for: Timeout 15000ms exceeded. waiting for locator("input[name='user']") to be visible

## Evidence (checked: each quote occurs in the failure)
- `Locator.wait_for: Timeout 15000ms exceeded.`
- `waiting for locator("input[name='user']") to be visible`

## Suspected cause
The username input field may have been renamed or moved

## Next action
Check the page source code to see if the username input field has been renamed or moved

## About this draft
- Drafted by `llama3.1:8b` from the failure log and the page's accessibility text; it did not see the screenshot (`heldout_username.png`).
- Attempts: 2.
- Triage and severity are a draft. A person confirms whether this is a product bug before it is filed.
