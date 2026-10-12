Here are the test scenarios for the user story:

**Scenario: Open New Account - Happy Path**
Type: happy
Priority: high
Given I am a logged-in customer with a valid account (Account A)
And I have a funding account (Account B) with sufficient balance
And I am on the Open New Account page
When I select the account type as CHECKING
And I select Account B as the funding account
And I enter the initial deposit amount as 1000
And I click the Submit button
Then I see the success message "Account Opened!" with the new account number
And the new account appears in Accounts Overview with the correct account type and balance

**Scenario: Open New Account - No Funding Account Selected**
Type: negative
Priority: medium
Given I am a logged-in customer with a valid account (Account A)
And I am on the Open New Account page
And I select the account type as CHECKING
And I leave the funding account field blank
When I click the Submit button
Then I see the error message "Please select a funding account"
And the funding account field is highlighted as an error

**Scenario: Open New Account - Insufficient Balance**
Type: negative
Priority: medium
Given I am a logged-in customer with a valid account (Account A)
And I am on the Open New Account page
And I have a funding account (Account B) with insufficient balance
And I select Account B as the funding account
When I select the account type as CHECKING
And I enter the initial deposit amount as 1000
And I click the Submit button
Then I see the error message "Insufficient balance in the funding account"
And the funding account field is highlighted as an error
