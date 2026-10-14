import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_open_savings_account(logged_in_page, base_url):
    accounts = AccountsPage(logged_in_page, base_url)
    accounts.click(accounts.get_by_role("button", name="Open New Account"))
    accounts.fill(accounts.get_by_label("Account Type"), "SAVINGS")
    accounts.fill(accounts.get_by_label("Initial Balance"), "1000")
    accounts.fill(accounts.get_by_label("From Account"), "12345")
    accounts.click(accounts.get_by_role("button", name="Add Account"))
    expect(accounts.open_account_result).to_contain_text("Account Opened!")
    assert accounts.accounts_table.get_by_text("SAVINGS").is_visible()
