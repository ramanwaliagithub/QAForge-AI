# Incorrect Transfer Success Heading

| | |
|---|---|
| Id | `bug-2fcb9864` |
| Triage (the model's call, unverified) | **app_bug**, severity major |
| Failing test | `framework/healing/sample_tests/test_broken_locators.py::test_sample_wrong_text_on_found_element` |
| Page | ParaBank | Transfer Funds (http://localhost:8080/parabank/transfer.htm) |
| Failure collected | 2026-10-30T10:29:13+00:00 |

## Summary
The ParaBank website displays incorrect text on the transfer success heading. The expected text is 'Transfer Done!', but the actual text is 'Transfer Complete!'.

## Steps to reproduce
1. Log in to the ParaBank website.
2. Navigate to the Transfer Funds page.
3. Initiate a transfer of $10 from account #521835 to account #521835.

## Expected
The transfer success heading should display 'Transfer Done!'.

## Actual
The transfer success heading displays 'Transfer Complete!'.

## Evidence (checked: each quote occurs in the failure)
- `Locator expected to have text 'Transfer Done!' Actual value: Transfer Complete! `
- `unexpected value "Transfer Complete!"`

## Suspected cause
The page's heading text is incorrect.

## Next action
The development team should investigate and correct the heading text to display the expected 'Transfer Done!' text.

## About this draft
- Drafted by `llama3.1:8b` from the failure log and the page's accessibility text; it did not see the screenshot (`sample_wrong_text.png`).
- Attempts: 1.
- Triage and severity are a draft. A person confirms whether this is a product bug before it is filed.
