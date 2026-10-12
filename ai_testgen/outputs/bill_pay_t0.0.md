Here are the test scenarios:

**Scenario: Valid Bill Payment**
Type: happy
Priority: high
Given I am logged in to ParaBank with a valid account
And I have a payee saved in my account
And I have sufficient funds in my account
When I navigate to the Bill Payment page
And I fill in the payee name, address, city, state, zip, phone, and account number
And I enter the same account number in the second field
And I enter a valid amount
And I select a valid "from" account
Then the Bill Payment Service form is submitted successfully
And the payment is processed
And the confirmation message "Bill Payment Complete" is displayed with the payee name, amount, and from-account.

**Scenario: Missing Payee Name**
Type: negative
Priority: high
Given I am logged in to ParaBank with a valid account
And I have sufficient funds in my account
When I navigate to the Bill Payment page
And I leave the payee name field blank
And I fill in the remaining fields
Then a validation message "Payee name is required" is displayed next to the payee name field.

**Scenario: Non-Matching Account Numbers**
Type: negative
Priority: high
Given I am logged in to ParaBank with a valid account
And I have a payee saved in my account
And I have sufficient funds in my account
When I navigate to the Bill Payment page
And I fill in the payee name, address, city, state, zip, phone, and account number
And I enter a different account number in the second field
And I enter a valid amount
And I select a valid "from" account
Then a validation message "Account numbers do not match" is displayed.

**Scenario: Invalid Amount**
Type: negative
Priority: high
Given I am logged in to ParaBank with a valid account
And I have a payee saved in my account
And I have sufficient funds in my account
When I navigate to the Bill Payment page
And I fill in the payee name, address, city, state, zip, phone, and account number
And I enter a valid account number in the second field
And I enter an invalid amount (e.g. "abc")
And I select a valid "from" account
Then a validation message "Amount must be a number" is displayed.

**Scenario: Insufficient Funds**
Type: edge
Priority: medium
Given I am logged in to ParaBank with a valid account
And I have a payee saved in my account
When I navigate to the Bill Payment page
And I fill in the payee name, address, city, state, zip, phone, and account number
And I enter a valid account number in the second field
And I enter a valid amount that exceeds my account balance
And I select a valid "from" account
Then a validation message "Insufficient funds" is displayed.
