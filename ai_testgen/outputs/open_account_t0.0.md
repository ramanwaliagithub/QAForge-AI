Scenario: Open New Checking Account
Type: happy
Priority: high
Given the user is logged in and on the Accounts Overview page
When the user clicks the "Open New Account" button and selects CHECKING as the account type
And the user selects an existing account as the funding account
And the user enters an initial deposit amount of 100
When the user clicks the "Open Account" button
Then an error message is shown
And the new account number is displayed on the page
And the new account appears in the Accounts Overview list

Scenario: Open New Account with Insufficient Funds
Type: negative
Priority: medium
Given the user is logged in and on the Accounts Overview page
When the user clicks the "Open New Account" button and selects CHECKING as the account type
And the user selects an existing account as the funding account with a balance of 0
And the user enters an initial deposit amount of 100
When the user clicks the "Open Account" button
Then an error message is shown
And the account balance is not updated

Scenario: Open New Account with Invalid Funding Account
Type: negative
Priority: medium
Given the user is logged in and on the Accounts Overview page
When the user clicks the "Open New Account" button and selects CHECKING as the account type
And the user selects an account that does not exist as the funding account
And the user enters an initial deposit amount of 100
When the user clicks the "Open Account" button
Then an error message is shown

Scenario: Open New Account with Zero Initial Deposit
Type: edge
Priority: low
Given the user is logged in and on the Accounts Overview page
When the user clicks the "Open New Account" button and selects CHECKING as the account type
And the user selects an existing account as the funding account
And the user enters an initial deposit amount of 0
When the user clicks the "Open Account" button
Then an error message is shown
