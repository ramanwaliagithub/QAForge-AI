import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_account_with_insufficient_funds_is_selected(logged_in_page, base_url):
    accounts = AccountsPage(logged_in_page, base_url)
    accounts.wait_for_url("accounts")
    accounts.click(accounts.get_by_role("button", name="Bill Payment"))
    accounts.click(accounts.get_by_text("Account: Checking 1456-6"))
    accounts.fill(accounts.get_by_label("Payee"), "Test Payee")
    accounts.fill(accounts.get_by_label("Account"), "1456-6")
    accounts.fill(accounts.get_by_label("Amount"), "1000")
    accounts.click(accounts.get_by_role("button", name="Make Payment"))
    expect(logged_in_page).to_have_title("Parabank - Bill Payment")
    expect(logged_in_page.error_message).to_contain_text("Insufficient funds")
