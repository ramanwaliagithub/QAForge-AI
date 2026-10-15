import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_open_savings_account(logged_in_page, base_url, registered_user):
    accounts = AccountsPage(logged_in_page, base_url)
    accounts.goto(f"{base_url}/openaccount.htm")
    accounts.open_new_account("SAVINGS")
    expect(accounts.open_account_result).to_contain_text("Account Opened!")
    new_account_link = accounts.get_by_text("New Account").locator
    expect(new_account_link).to_be_visible()
    expect(new_account_link).to_have_text("SAVINGS")
    expect(accounts.accounts_table).to_have_row_count(2)
