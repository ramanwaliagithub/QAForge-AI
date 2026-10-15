import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_zero_initial_deposit_amount(logged_in_page, base_url):
    accounts = AccountsPage(logged_in_page, base_url)
    accounts.open_new_account("CHECKING")
    select_account = accounts.page.locator("#fromAccountId")
    select_account.select_option("1")  # Select a funding account
    accounts.page.locator("input[value='Open New Account']").click()
    expect(accounts.error_message).to_contain_text("The initial deposit must be greater than 0")
