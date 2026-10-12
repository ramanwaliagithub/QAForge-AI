Scenario: Open Checking Account
Type: happy
Priority: high
Given the user is logged in to the ParaBank web application
And the user navigates to the Open New Account page
And the user selects CHECKING as the account type
And the user selects a valid funding account with a sufficient balance
When the user submits the Open New Account form
Then an "Account Opened!" message is shown with the new account number
And the new checking account appears in the Accounts Overview page
And the funding account balance decreases by the initial deposit amount

Scenario: No Funding Account Selected
Type: negative
Priority: medium
Given the user is logged in to the ParaBank web application
And the user navigates to the Open New Account page
And the user selects CHECKING as the account type
And the user does not select a funding account
When the user submits the Open New Account form
Then an error message is shown

Scenario: Insufficient Funding Account Balance
Type: negative
Priority: high
Given the user is logged in to the ParaBank web application
And the user navigates to the Open New Account page
And the user selects CHECKING as the account type
And the user selects a funding account with an insufficient balance
When the user submits the Open New Account form
Then an error message is shown
