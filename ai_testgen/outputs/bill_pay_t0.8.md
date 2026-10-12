Scenario: Bill Payment Form Happy Path
Type: happy
Priority: high
Given The customer is logged in to the ParaBank web application and navigates to the Bill Payment Service form
When The customer enters a valid payee name, address, city, state, zip, phone, two identical account numbers, a valid amount, and selects a "from" account
Then The Bill Payment Service form shows a "Bill Payment Complete" message with the payee name, amount, and from-account; the payee fields are no longer visible; the account number entries match; and the amount is a number

Scenario: Bill Payment Form Missing Payee Fields
Type: negative
Priority: high
Given The customer is logged in to the ParaBank web application and navigates to the Bill Payment Service form; the payee fields are empty
When The customer clicks the "Pay Bill" button
Then The Bill Payment Service form shows a validation message next to each empty payee field; the "Pay Bill" button is disabled

Scenario: Bill Payment Form Invalid Account Numbers
Type: negative
Priority: high
Given The customer is logged in to the ParaBank web application and navigates to the Bill Payment Service form; the payee fields are populated; the two account number entries are different
When The customer clicks the "Pay Bill" button
Then The Bill Payment Service form shows a validation message next to the account number fields; the "Pay Bill" button is disabled

Scenario: Bill Payment Form Non-numeric Amount
Type: negative
Priority: high
Given The customer is logged in to the ParaBank web application and navigates to the Bill Payment Service form; the payee fields are populated; the two account number entries match
When The customer enters a non-numeric value in the amount field
Then The Bill Payment Service form shows a validation message next to the amount field; the "Pay Bill" button is disabled

Scenario: Bill Payment Form Boundary Case - Zero Amount
Type: edge
Priority: medium
Given The customer is logged in to the ParaBank web application and navigates to the Bill Payment Service form; the payee fields are populated; the two account number entries match
When The customer enters a zero value in the amount field
Then The Bill Payment Service form allows the "Pay Bill" button to be clicked; a successful payment shows "Bill Payment Complete" with the payee name, zero amount, and from-account
