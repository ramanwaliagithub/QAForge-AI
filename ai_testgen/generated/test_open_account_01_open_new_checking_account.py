import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_open_checking_account(logged_in_page, base_url):
    accounts = AccountsPage(logged_in_page, base_url)
    accounts.click(accounts.get_by_role("button", name="Open New Account"))
    accounts.fill(accounts.get_by_label("Account Type"), "CHECKING")
    accounts.fill(accounts.get_by_label("Initial Balance"), "1000")
    accounts.fill(accounts.get_by_label("From Account"), "12345")
    accounts.click(accounts.get_by_role("button", name="Add Account"))
    new_id = accounts.open_new_account("CHECKING")
    expect(accounts.open_account_result).to_contain_text("Account Opened!")
    expect(accounts.accounts_table).to_have_text(new_id)
    assert new_id.isdigit()
