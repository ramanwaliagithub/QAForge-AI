# Invalid amount not detected

| | |
|---|---|
| Id | `bug-f0e4ae00` |
| Triage (the model's call, unverified) | **app_bug**, severity major |
| Failing test | `ai_testgen/generated/test_bill_pay_04_amount_is_not_a_number.py::test_amount_is_not_a_number` |
| Page | ParaBank | Bill Pay (http://localhost:8080/parabank/billpay.htm) |
| Failure collected | 2026-10-30T11:04:34+00:00 |

## Summary
The page did not detect an invalid amount, allowing a non-numeric value to be submitted. This is a security risk.

## Steps to reproduce
1. Go to the Bill Pay page
2. Fill in a valid payee and address
3. Enter a non-numeric value in the Amount field
4. Click Send Payment

## Expected
The page should detect the invalid amount and display an error message

## Actual
The page allowed the non-numeric value to be submitted and did not display an error message

## Evidence (checked: each quote occurs in the failure)
- `Locator expected to be visible Actual value: None Error: element(s) not found`
- `Expect "to_be_visible" get_by_text("Invalid amount") with timeout 10000ms`

## Suspected cause
The page's validation logic may be faulty.

## Next action
The development team should review the page's validation logic and fix the issue to prevent security risks.

## About this draft
- Drafted by `llama3.1:8b` from the failure log and the page's accessibility text; it did not see the screenshot (`gen_billpay_invalid_amount.png`).
- Attempts: 1.
- Triage and severity are a draft. A person confirms whether this is a product bug before it is filed.
