import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_open_savings_account(logged_in_page, base_url):
    accounts = AccountsPage(logged_in_page, base_url)
    accounts.open_new_account("SAVINGS")
    expect(accounts.open_account_result).to_contain_text("Account Opened!")
    expect(accounts.accounts_table).to_have_text("SAVINGS")
    expect(accounts.account_links).to_have_text("SAVINGS")
