# Bill pay
As a logged-in customer, I want to pay a bill to a payee so that I can settle my expenses online.

## Acceptance criteria
- The Bill Payment Service form asks for payee name, address, city, state, zip, phone, account number (entered twice), amount, and a "from" account.
- All payee fields are required; missing fields show a validation message next to the field.
- The two account number entries must match.
- The amount must be a number.
- A successful payment shows "Bill Payment Complete" with the payee name, amount and from-account.
