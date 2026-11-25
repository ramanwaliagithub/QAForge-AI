# Transfer larger than balance is not rejected

| | |
|---|---|
| Id | `bug-3a92ea8a` |
| Triage (the model's call, unverified) | **app_bug**, severity major |
| Failing test | `tests/test_transfer_edge_cases.py::test_transfer_larger_than_balance_is_rejected` |
| Page | ParaBank | Transfer Funds (http://localhost:8080/parabank/transfer.htm) |
| Failure collected | 2026-10-28T05:59:07+00:00 |
| Same failure as | `bug-035b7f10` (equal kind, locator and message shape): probably a duplicate |

## Summary
The page failed to reject a transfer larger than the balance, allowing an invalid transaction to proceed.

## Steps to reproduce
1. Open the ParaBank website and navigate to the Transfer Funds page.
2. Attempt to transfer a large amount of money from one account to another, exceeding the balance in the source account.

## Expected
The page should reject the transfer and display an error message.

## Actual
The page allowed the transfer to proceed, exceeding the balance in the source account.

## Evidence (checked: each quote occurs in the failure)
- `Locator.wait_for: Timeout 2000ms exceeded.`
- `Locator waited for: locator("#amt")`
- `Page: ParaBank | Transfer Funds (http://localhost:8080/parabank/transfer.htm)`

## Suspected cause
The page's validation logic may be faulty, allowing invalid transactions to proceed.

## Next action
Review the page's validation logic and ensure it correctly rejects transfers exceeding the balance in the source account.

## About this draft
- Drafted by `llama3.1:8b` from the failure log and the page's accessibility text; it did not see the screenshot (`stale_amt_larger.png`).
- Attempts: 3. Dropped as not found in the failure: ['TEXT THE PAGE SHOWED: ParaBank | About Us | Services | Products | Locations | Admin Page | home | about | contact | Account Services | Open New Account | Accounts Overview | Transfer Funds | Bill Pay | Find Transactions | Update Contact Info | Request Loan | Log Out | "Amount: $" | "From account #" | 405729 | 405840 | "to account #" | Transfer | Home | "|" | Site Map | Contact Us | Visit us at: | www.parasoft.com'].
- Triage and severity are a draft. A person confirms whether this is a product bug before it is filed.
