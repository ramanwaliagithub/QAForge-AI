Scenario: Valid Bill Payment
Type: happy
Priority: high
Given I am logged in to ParaBank with a valid account
And I have a payee saved with name "John Doe", address "123 Main St", city "Anytown", state "CA", zip "12345", phone "555-1234"
And I have two accounts with balances: an account with a balance of 100 and an account with a balance of 500
When I navigate to the Bill Payment page and fill in the payee fields with the saved payee's information
And I enter the account number "123456789" in both account number fields
And I enter an amount of "50" in the amount field
And I select the account with a balance of 100 as the "from" account
When I submit the Bill Payment form
Then the Bill Payment Service form shows "Bill Payment Complete" with the payee name "John Doe", amount "50", and from-account "Account with a balance of 100"

Scenario: Missing Payee Fields
Type: negative
Priority: medium
Given I am logged in to ParaBank with a valid account
And I have two accounts with balances: an account with a balance of 100 and an account with a balance of 500
When I navigate to the Bill Payment page and do not fill in any payee fields
When I submit the Bill Payment form
Then an error message is shown next to each empty payee field

Scenario: Non-Matching Account Numbers
Type: negative
Priority: medium
Given I am logged in to ParaBank with a valid account
And I have a payee saved with name "John Doe", address "123 Main St", city "Anytown", state "CA", zip "12345", phone "555-1234"
And I have two accounts with balances: an account with a balance of 100 and an account with a balance of 500
When I navigate to the Bill Payment page and fill in the payee fields with the saved payee's information
And I enter the account number "123456789" in the first account number field
And I enter the account number "987654321" in the second account number field
And I enter an amount of "50" in the amount field
And I select the account with a balance of 100 as the "from" account
When I submit the Bill Payment form
Then an error message is shown indicating that the account numbers do not match

Scenario: Non-numeric Amount
Type: negative
Priority: medium
Given I am logged in to ParaBank with a valid account
And I have a payee saved with name "John Doe", address "123 Main St", city "Anytown", state "CA", zip "12345", phone "555-1234"
And I have two accounts with balances: an account with a balance of 100 and an account with a balance of 500
When I navigate to the Bill Payment page and fill in the payee fields with the saved payee's information
And I enter the account number "123456789" in both account number fields
And I enter an amount of "abc" in the amount field
And I select the account with a balance of 100 as the "from" account
When I submit the Bill Payment form
Then an error message is shown indicating that the amount is not a valid number
