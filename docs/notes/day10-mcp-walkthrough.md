# ParaBank flow map from a Playwright MCP walkthrough

Driven by `scripts/mcp_walkthrough.py` through the MCP server (new user `mcp_8df59719`), 12 tool calls.

## Tool calls

| # | tool | what | result |
|---|---|---|---|
| 1 | `browser_navigate` | open home | ok |
| 2 | `browser_click` | click Register | ok |
| 3 | `browser_fill_form` | fill registration form | ok |
| 4 | `browser_click` | submit registration | ok |
| 5 | `browser_click` | menu Open New Account | ok |
| 6 | `browser_click` | menu Accounts Overview | ok |
| 7 | `browser_click` | menu Transfer Funds | ok |
| 8 | `browser_click` | menu Bill Pay | ok |
| 9 | `browser_click` | menu Find Transactions | ok |
| 10 | `browser_click` | menu Update Contact Info | ok |
| 11 | `browser_click` | menu Request Loan | ok |
| 12 | `browser_click` | log out | ok |

## Pages

### Home (logged out)

- URL: `http://localhost:8080/parabank/index.htm`  Title: ParaBank | Welcome | Online Banking
- Headings: ['Customer Login', 'Latest News']
- Controls: 2 textboxes, 0 dropdowns, buttons ['Log In']
- Text: ['Experience the difference', 'Username', 'Password', '© Parasoft. All rights reserved.']

### Registration form

- URL: `http://localhost:8080/parabank/register.htm;jsessionid=0276681359DDEE5D1D072A392EEBA134`  Title: ParaBank | Register for Free Online Account Access
- Headings: ['Customer Login', 'Signing up is easy!']
- Controls: 13 textboxes, 0 dropdowns, buttons ['Log In', 'Register']
- Text: ['Experience the difference', 'Username', 'Password', 'If you have an account with us you can sign-up for free instant online access. You will have to provide some personal information.', '© Parasoft. All rights reserved.']

### After registration

- URL: `http://localhost:8080/parabank/register.htm`  Title: ParaBank | Customer Created
- Headings: ['Account Services', 'Welcome mcp_8df59719']
- Controls: 0 textboxes, 0 dropdowns, buttons -
- Text: ['Experience the difference', 'Welcome Mcp Explorer', 'Your account was created successfully. You are now logged in.', '© Parasoft. All rights reserved.']

### Open New Account

- URL: `http://localhost:8080/parabank/openaccount.htm`  Title: ParaBank | Open Account
- Headings: ['Account Services', 'Open New Account']
- Controls: 0 textboxes, 2 dropdowns, buttons ['Open New Account']
- Text: ['Experience the difference', 'Welcome Mcp Explorer', 'What type of Account would you like to open?', 'A minimum of $100.00 must be deposited into this account at time of opening. Please choose an existing account to transfer funds into the new account.', '© Parasoft. All rights reserved.']

### Accounts Overview

- URL: `http://localhost:8080/parabank/overview.htm`  Title: ParaBank | Accounts Overview
- Headings: ['Account Services', 'Accounts Overview']
- Controls: 0 textboxes, 0 dropdowns, buttons -
- Text: ['Experience the difference', 'Welcome Mcp Explorer', '© Parasoft. All rights reserved.']

### Transfer Funds

- URL: `http://localhost:8080/parabank/transfer.htm`  Title: ParaBank | Transfer Funds
- Headings: ['Account Services', 'Transfer Funds']
- Controls: 1 textboxes, 2 dropdowns, buttons ['Transfer']
- Text: ['Experience the difference', 'Welcome Mcp Explorer', '© Parasoft. All rights reserved.']

### Bill Pay

- URL: `http://localhost:8080/parabank/billpay.htm`  Title: ParaBank | Bill Pay
- Headings: ['Account Services', 'Bill Payment Service']
- Controls: 9 textboxes, 1 dropdowns, buttons ['Send Payment']
- Text: ['Experience the difference', 'Welcome Mcp Explorer', 'Enter payee information', '© Parasoft. All rights reserved.']

### Find Transactions

- URL: `http://localhost:8080/parabank/findtrans.htm`  Title: ParaBank | Find Transactions
- Headings: ['Account Services', 'Find Transactions']
- Controls: 5 textboxes, 1 dropdowns, buttons ['Find Transactions', 'Find Transactions', 'Find Transactions', 'Find Transactions']
- Text: ['Experience the difference', 'Welcome Mcp Explorer', 'Find by Date Range', '© Parasoft. All rights reserved.']

### Update Contact Info

- URL: `http://localhost:8080/parabank/updateprofile.htm`  Title: ParaBank | Update Profile
- Headings: ['Account Services', 'Update Profile']
- Controls: 7 textboxes, 0 dropdowns, buttons ['Update Profile']
- Text: ['Experience the difference', 'Welcome Mcp Explorer', '© Parasoft. All rights reserved.']

### Request Loan

- URL: `http://localhost:8080/parabank/requestloan.htm`  Title: ParaBank | Loan Request
- Headings: ['Account Services', 'Apply for a Loan']
- Controls: 2 textboxes, 1 dropdowns, buttons ['Apply Now']
- Text: ['Experience the difference', 'Welcome Mcp Explorer', '© Parasoft. All rights reserved.']

### After log out

- URL: `http://localhost:8080/parabank/index.htm?ConnType=JDBC`  Title: ParaBank | Welcome | Online Banking
- Headings: ['Customer Login', 'Latest News']
- Controls: 2 textboxes, 0 dropdowns, buttons ['Log In']
- Text: ['Experience the difference', 'Username', 'Password', '© Parasoft. All rights reserved.']
