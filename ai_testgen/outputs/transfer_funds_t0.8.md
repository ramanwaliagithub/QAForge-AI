Scenario: Transfer Funds - Happy Path
Type: happy
Priority: high
Given the user is logged in to ParaBank and has two accounts: an account with a balance of 100 and another account with a balance of 500.
When the user clicks on the "Transfer Funds" button and navigates to the Transfer Funds page.
Then the Transfer Funds page asks for an amount, a "from" account, and a "to" account.
And the user enters 50 in the amount field, selects the account with a balance of 100 as the "from" account, and selects the account with a balance of 500 as the "to" account.
And when the user clicks the "Transfer" button.
Then the user sees "Transfer Complete!" with the amount 50 and both account ids.
And the account with a balance of 100 has a balance of 50 and the account with a balance of 500 has a balance of 550.

Scenario: Transfer Funds - Negative - Invalid Amount
Type: negative
Priority: high
Given the user is logged in to ParaBank and has two accounts: an account with a balance of 100 and another account with a balance of 500.
When the user clicks on the "Transfer Funds" button and navigates to the Transfer Funds page.
Then the Transfer Funds page asks for an amount, a "from" account, and a "to" account.
And the user enters -50 in the amount field, selects the account with a balance of 100 as the "from" account, and selects the account with a balance of 500 as the "to" account.
And when the user clicks the "Transfer" button.
Then an error message is shown.

Scenario: Transfer Funds - Negative - Insufficient Balance
Type: negative
Priority: high
Given the user is logged in to ParaBank and has two accounts: an account with a balance of 0 and another account with a balance of 500.
When the user clicks on the "Transfer Funds" button and navigates to the Transfer Funds page.
Then the Transfer Funds page asks for an amount, a "from" account, and a "to" account.
And the user enters 50 in the amount field, selects the account with a balance of 0 as the "from" account, and selects the account with a balance of 500 as the "to" account.
And when the user clicks the "Transfer" button.
Then an error message is shown.

Scenario: Transfer Funds - Edge - Minimum Transfer Amount
Type: edge
Priority: medium
Given the user is logged in to ParaBank and has two accounts: an account with a balance of 100 and another account with a balance of 500.
When the user clicks on the "Transfer Funds" button and navigates to the Transfer Funds page.
Then the Transfer Funds page asks for an amount, a "from" account, and a "to" account.
And the user enters 0.01 in the amount field, selects the account with a balance of 100 as the "from" account, and selects the account with a balance of 500 as the "to" account.
And when the user clicks the "Transfer" button.
Then the user sees "Transfer Complete!" with the amount 0.01 and both account ids.
And the account with a balance of 100 has a balance of 99.99 and the account with a balance of 500 has a balance of 500.01.
