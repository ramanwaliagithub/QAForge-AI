import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_insufficient_funds_in_funding_account(logged_in_page, base_url):
    accounts = AccountsPage(logged_in_page, base_url)
    accounts.open_new_account("CHECKING")
    accounts.fill(accounts.get_by_label("Funding Account").locator, registered_user["username"])
    accounts.fill(accounts.get_by_label("Initial Balance").locator, "0.00")
    accounts.click(accounts.get_by_text("Submit").locator)
    expect(accounts.error_message).to_contain_text("Insufficient funds in funding account")
