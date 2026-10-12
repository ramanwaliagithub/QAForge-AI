Here are the test scenarios:

**Scenario: Open New Account Page**
Type: happy
Priority: high
Given I am logged in to ParaBank as a customer with a valid account
When I navigate to the Open New Account page
Then the page displays an account type dropdown with options CHECKING and SAVINGS
And the page displays a funding account dropdown with my existing accounts

**Scenario: Successful Account Opening**
Type: happy
Priority: high
Given I am logged in to ParaBank as a customer with a valid account
And I have selected a funding account with sufficient balance
When I select an account type and submit the form with the required initial deposit
Then the page displays "Account Opened!" with the new account number
And the new account appears in my Accounts Overview

**Scenario: Insufficient Funding**
Type: negative
Priority: high
Given I am logged in to ParaBank as a customer with a valid account
And I have selected a funding account with insufficient balance
When I select an account type and submit the form with the required initial deposit
Then the page displays an error message "Insufficient funds in funding account"

**Scenario: Invalid Initial Deposit**
Type: negative
Priority: medium
Given I am logged in to ParaBank as a customer with a valid account
And I have selected a funding account with sufficient balance
When I select an account type and submit the form with an invalid initial deposit (e.g. negative number)
Then the page displays an error message "Invalid initial deposit amount"

**Scenario: No Funding Account Selected**
Type: negative
Priority: medium
Given I am logged in to ParaBank as a customer with a valid account
When I navigate to the Open New Account page
Then the page displays an error message "Please select a funding account"

**Scenario: Edge Case - Zero Initial Deposit**
Type: edge
Priority: low
Given I am logged in to ParaBank as a customer with a valid account
And I have selected a funding account with sufficient balance
When I select an account type and submit the form with an initial deposit of $0
Then the page displays an error message "Initial deposit must be greater than $0"
