# Transfer larger than balance is not rejected

| | |
|---|---|
| Id | `bug-3a92ea8a` |
| Triage (the model's call, unverified) | **app_bug**, severity critical |
| Failing test | `tests/test_transfer_edge_cases.py::test_transfer_larger_than_balance_is_rejected` |
| Page | ParaBank | Transfer Funds (http://localhost:8080/parabank/transfer.htm) |
| Failure collected | 2026-10-28T05:59:07+00:00 |
| Same failure as | `bug-035b7f10` (equal kind, locator and message shape): probably a duplicate |

## Summary
The page failed to reject a transfer larger than the balance. The test expected the transfer to be rejected.

## Steps to reproduce
1. Open the ParaBank website and navigate to the Transfer Funds page.
2. Attempt to transfer an amount larger than the balance from one account to another.

## Expected
The transfer to be rejected with an error message.

## Actual
The transfer was not rejected and the page timed out waiting for the amount field to be visible.

## Evidence (checked: each quote occurs in the failure)
- `Locator.wait_for: Timeout 2000ms exceeded.`
- `Call log:  - waiting for locator("#amt") to be visible`

## Suspected cause
The page's validation logic for transfers may be faulty.

## Next action
The development team should review the page's validation logic for transfers and ensure it correctly rejects transfers larger than the balance.

## About this draft
- Drafted by `llama3.1:8b` from the failure log and the page's accessibility text; it did not see the screenshot (`stale_amt_larger.png`).
- Attempts: 1.
- Triage and severity are a draft. A person confirms whether this is a product bug before it is filed.
