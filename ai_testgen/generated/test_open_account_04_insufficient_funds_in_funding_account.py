import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_open_checking_account_with_insufficient_funds(logged_in_page, base_url):
    accounts = AccountsPage(logged_in_page, base_url)
    accounts.open_new_account("CHECKING")
    select_account = logged_in_page.locator("#fromAccountId")
    select_account.select_option("1")  # Select a funding account with insufficient funds
    logged_in_page.locator("input[value='Open New Account']").click()
    expect(logged_in_page.locator(".error-message")).to_be_visible()
