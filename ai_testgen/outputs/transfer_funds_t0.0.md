Scenario: Transfer Funds Page
Type: happy
Priority: high
Given the customer is logged in and has two accounts: an account with a balance of 100 and an account with a balance of 200
When the customer navigates to the Transfer Funds page
Then the page asks for an amount, a "from" account, and a "to" account

Scenario: Successful Transfer
Type: happy
Priority: high
Given the customer is logged in and has two accounts: an account with a balance of 100 and an account with a balance of 200
When the customer enters an amount of 50, selects the first account as the "from" account, and selects the second account as the "to" account, then clicks the "Transfer" button
Then an error message is shown with the text "Transfer Complete!" and the amount 50 and both account ids

Scenario: Invalid Amount
Type: negative
Priority: medium
Given the customer is logged in and has two accounts: an account with a balance of 100 and an account with a balance of 200
When the customer enters an amount of -50, selects the first account as the "from" account, and selects the second account as the "to" account, then clicks the "Transfer" button
Then an error message is shown

Scenario: Same Account Selected
Type: negative
Priority: medium
Given the customer is logged in and has two accounts: an account with a balance of 100 and an account with a balance of 200
When the customer enters an amount of 50, selects the first account as both the "from" and "to" accounts, then clicks the "Transfer" button
Then an error message is shown
