# Wrong text on Transfer Complete! page

| | |
|---|---|
| Id | `bug-2fcb9864` |
| Triage (the model's call, unverified) | **app_bug**, severity major |
| Failing test | `framework/healing/sample_tests/test_broken_locators.py::test_sample_wrong_text_on_found_element` |
| Page | ParaBank | Transfer Funds (http://localhost:8080/parabank/transfer.htm) |
| Failure collected | 2026-10-30T10:29:13+00:00 |

## Summary
The page shows 'Transfer Complete!' instead of 'Transfer Done!' when a transfer is successful. This is a bug in the application.

## Steps to reproduce
1. Log in to the ParaBank website
2. Go to the Transfer Funds page
3. Transfer $10 from one account to another

## Expected
The page should show 'Transfer Done!' when a transfer is successful

## Actual
The page shows 'Transfer Complete!' when a transfer is successful

## Evidence (checked: each quote occurs in the failure)
- `Locator expected to have text 'Transfer Done!' Actual value: Transfer Complete!`

## Suspected cause
The application's text is not consistent with its expected behavior.

## Next action
The development team should review the application's text and behavior to ensure consistency.

## About this draft
- Drafted by `llama3.1:8b` from the failure log and the page's accessibility text; it did not see the screenshot (`sample_wrong_text.png`).
- Attempts: 3. Dropped as not found in the failure: ["unexpected value 'Transfer Complete!'"].
- Triage and severity are a draft. A person confirms whether this is a product bug before it is filed.
