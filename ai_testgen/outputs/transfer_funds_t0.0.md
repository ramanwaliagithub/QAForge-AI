Here are the test scenarios:

**Scenario: Transfer Funds - Happy Path**
Type: happy
Priority: high
Given I am logged in as a customer with two accounts, "12345" and "67890", and I am on the Transfer Funds page.
When I enter "100.00" in the Amount field, select "12345" as the From Account and "67890" as the To Account, and click the Transfer button.
Then the page displays "Transfer Complete!" with the amount "100.00" and both account ids "12345" and "67890".

**Scenario: Transfer Funds - Negative - Invalid Amount**
Type: negative
Priority: high
Given I am logged in as a customer with two accounts, "12345" and "67890", and I am on the Transfer Funds page.
When I enter "-100.00" in the Amount field, select "12345" as the From Account and "67890" as the To Account, and click the Transfer button.
Then the page displays an error message "Invalid amount. Please enter a positive number."

**Scenario: Transfer Funds - Negative - Invalid From Account**
Type: negative
Priority: medium
Given I am logged in as a customer with two accounts, "12345" and "67890", and I am on the Transfer Funds page.
When I enter "100.00" in the Amount field, select "67890" as the From Account and "12345" as the To Account, and click the Transfer button.
Then the page displays an error message "Invalid from account. Please select a valid account."

**Scenario: Transfer Funds - Edge - Zero Amount**
Type: edge
Priority: low
Given I am logged in as a customer with two accounts, "12345" and "67890", and I am on the Transfer Funds page.
When I enter "0.00" in the Amount field, select "12345" as the From Account and "67890" as the To Account, and click the Transfer button.
Then the page displays an error message "Invalid amount. Please enter a positive number."
