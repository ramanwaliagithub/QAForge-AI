import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_account_number_entries_do_not_match(logged_in_page, base_url):
    accounts = AccountsPage(logged_in_page, base_url)
    accounts.wait_for_url("accounts")
    accounts.open_new_account("SAVINGS")  # Open a new savings account to have an account number
    accounts.wait_for_url("accounts")
    accounts.open_new_account("CHECKING")  # Open a new checking account to have another account number
    accounts.wait_for_url("accounts")
    accounts.fill("accountNumber", "123456789")  # Enter a different account number in the first field
    accounts.fill("secondAccountNumber", "987654321")  # Enter a different account number in the second field
    accounts.click("submit")  # Submit the form
    expect(accounts.error_message).to_contain_text("Invalid account number")
