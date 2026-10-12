Here are the test scenarios in Given/When/Then format:

**Scenario: Successful Transfer**
Type: happy
Priority: high
Given I am logged in to my ParaBank account and have two valid accounts, "Account 123" and "Account 456", both with sufficient balance.
When I navigate to the Transfer Funds page, select "Account 123" as the "from" account and "Account 456" as the "to" account, and enter a positive amount of $100.00.
Then the Transfer Funds page displays "Transfer Complete!" with the amount "$100.00" and both account IDs ("123" and "456").

**Scenario: Invalid Transfer Amount (Negative)**
Type: negative
Priority: medium
Given I am logged in to my ParaBank account and have two valid accounts, "Account 123" and "Account 456", both with sufficient balance.
When I navigate to the Transfer Funds page, select "Account 123" as the "from" account and "Account 456" as the "to" account, and enter a negative amount of -$100.00.
Then the Transfer Funds page displays an error message "Invalid amount. Please enter a positive number."

**Scenario: Invalid Transfer Amount (Boundary)**
Type: edge
Priority: medium
Given I am logged in to my ParaBank account and have two valid accounts, "Account 123" and "Account 456", both with sufficient balance.
When I navigate to the Transfer Funds page, select "Account 123" as the "from" account and "Account 456" as the "to" account, and enter an amount of $0.00.
Then the Transfer Funds page displays an error message "Invalid amount. Please enter a positive number."

**Scenario: Invalid "To" Account (Negative)**
Type: negative
Priority: medium
Given I am logged in to my ParaBank account and have two valid accounts, "Account 123" and "Account 456", both with sufficient balance.
When I navigate to the Transfer Funds page, select "Account 123" as the "from" account and an invalid account "Account 999" as the "to" account, and enter a positive amount of $100.00.
Then the Transfer Funds page displays an error message "Invalid account. Please select a valid account."

**Scenario: Invalid "From" Account (Negative)**
Type: negative
Priority: medium
Given I am logged in to my ParaBank account and have two valid accounts, "Account 123" and "Account 456", both with sufficient balance.
When I navigate to the Transfer Funds page, select an invalid account "Account 999" as the "from" account and "Account 456" as the "to" account, and enter a positive amount of $100.00.
Then the Transfer Funds page displays an error message "Invalid account. Please select a valid account."
