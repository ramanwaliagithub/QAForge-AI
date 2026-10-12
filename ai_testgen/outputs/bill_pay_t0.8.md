Scenario: Bill Payment Form Fields
Type: Happy
Priority: High
Given I am logged in to ParaBank and have an account
When I navigate to the Bill Payment page
Then the Bill Payment Service form has fields for payee name, address, city, state, zip, phone, account number (entered twice), amount, and a "from" account

Scenario: Required Payee Fields
Type: Negative
Priority: High
Given I am logged in to ParaBank and have an account, I am on the Bill Payment page
When I submit the Bill Payment form without filling in the payee address
Then an error message is shown next to the payee address field

Scenario: Mismatched Account Numbers
Type: Negative
Priority: Medium
Given I am logged in to ParaBank and have an account, I am on the Bill Payment page
When I fill in the payee fields, account number (entered twice) with different numbers
Then an error message is shown next to the account number field

Scenario: Non-numeric Amount
Type: Negative
Priority: Medium
Given I am logged in to ParaBank and have an account, I am on the Bill Payment page
When I fill in the payee fields, account number (entered twice) and amount with a non-numeric value
Then an error message is shown next to the amount field

Scenario: Successful Bill Payment
Type: Happy
Priority: High
Given I am logged in to ParaBank and have an account, I am on the Bill Payment page
When I fill in the payee fields, account number (entered twice), and a valid amount, then submit the form
Then the page displays "Bill Payment Complete" with the payee name, amount, and from-account.
