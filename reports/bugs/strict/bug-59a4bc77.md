# Negative transfer amount is not rejected

| | |
|---|---|
| Id | `bug-59a4bc77` |
| Triage (the model's call, unverified) | **test_bug**, severity major |
| Failing test | `tests/test_transfer_edge_cases.py::test_negative_amount_is_rejected` |
| Page | ParaBank | Transfer Funds (http://localhost:8080/parabank/transfer.htm) |
| Failure collected | 2026-10-28T05:59:04+00:00 |
| Same failure as | `bug-035b7f10` (equal kind, locator and message shape): probably a duplicate |

## Summary
The test expects a negative transfer amount to be rejected, but the test times out waiting for the result heading.

## Steps to reproduce
1. Open the ParaBank website and navigate to the Transfer Funds page.
2. Attempt to transfer a negative amount from one account to another.

## Expected
The test should fail with an assertion error, indicating that the negative transfer amount was accepted.

## Actual
The test times out waiting for the result heading, indicating that the transfer was not rejected.

## Evidence (checked: each quote occurs in the failure)
- `Locator.wait_for: Timeout 2000ms exceeded.`
- `Locator waited for: locator("#amt")`

## Suspected cause
The test code does not correctly wait for the result heading to appear after attempting a negative transfer amount.

## Next action
Review the test code and ensure that it correctly waits for the result heading to appear after attempting a negative transfer amount.

## About this draft
- Drafted by `llama3.1:8b` from the failure log and the page's accessibility text; it did not see the screenshot (`stale_amt_negative.png`).
- Attempts: 2.
- Triage and severity are a draft. A person confirms whether this is a product bug before it is filed.
