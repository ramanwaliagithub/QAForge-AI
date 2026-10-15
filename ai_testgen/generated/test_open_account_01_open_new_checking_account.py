import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_open_checking_account(logged_in_page, base_url):
    accounts = AccountsPage(logged_in_page, base_url)
    accounts.open_new_account("CHECKING")
    expect(accounts.open_account_result).to_contain_text("Account Opened!")
    expect(accounts.accounts_table).to_have_text("CHECKING")
    expect(accounts.accounts_table).to_have_text("new account number")
