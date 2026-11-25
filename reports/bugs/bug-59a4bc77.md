# Transfer page does not reject negative amount

| | |
|---|---|
| Id | `bug-59a4bc77` |
| Triage (the model's call, unverified) | **app_bug**, severity critical |
| Failing test | `tests/test_transfer_edge_cases.py::test_negative_amount_is_rejected` |
| Page | ParaBank | Transfer Funds (http://localhost:8080/parabank/transfer.htm) |
| Failure collected | 2026-10-28T05:59:04+00:00 |
| Same failure as | `bug-035b7f10` (equal kind, locator and message shape): probably a duplicate |

## Summary
The transfer page does not reject negative amounts as expected. This is a critical issue as it allows users to transfer invalid amounts.

## Steps to reproduce
1. Open the ParaBank website and navigate to the Transfer Funds page.
2. Attempt to transfer a negative amount from one account to another.

## Expected
The transfer page should reject negative amounts and display an error message.

## Actual
The transfer page did not reject the negative amount and timed out waiting for the locator '#amt' to be visible.

## Evidence (checked: each quote occurs in the failure)
- `Locator.wait_for: Timeout 2000ms exceeded.`
- `Call log:  - waiting for locator("#amt") to be visible`

## Suspected cause
The transfer page's validation logic may be faulty.

## Next action
The development team should review the transfer page's validation logic and ensure it correctly rejects negative amounts.

## About this draft
- Drafted by `llama3.1:8b` from the failure log and the page's accessibility text; it did not see the screenshot (`stale_amt_negative.png`).
- Attempts: 1.
- Triage and severity are a draft. A person confirms whether this is a product bug before it is filed.
