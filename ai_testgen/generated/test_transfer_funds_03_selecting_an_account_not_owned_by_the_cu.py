import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_select_non_owned_account(logged_in_page, base_url):
    accounts = AccountsPage(logged_in_page, base_url)
    accounts.open_new_account(account_type="SAVINGS")  # Create a new savings account
    accounts.open_new_account(account_type="CHECKING")  # Create a new checking account
    accounts.wait_for_url("accounts")
    accounts.click(accounts.get_by_role("button", name="Transfer Funds"))
    accounts.fill(accounts.get_by_label("From Account"), "SAVINGS")
    accounts.fill(accounts.get_by_label("To Account"), "CHECKING")
    accounts.fill(accounts.get_by_label("Amount"), "50")
    accounts.click(accounts.get_by_role("button", name="Transfer"))
    expect(accounts.error_message).to_contain_text("You do not have permission to perform this transaction.")
