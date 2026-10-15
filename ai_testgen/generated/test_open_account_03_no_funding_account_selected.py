import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_open_checking_account_without_funding(logged_in_page, base_url):
    accounts = AccountsPage(logged_in_page, base_url)
    accounts.open_new_account("CHECKING")
    select_account_type = logged_in_page.locator("#type")
    select_account_type.select_option("CHECKING")
    select_funding_account = logged_in_page.locator("#fromAccountId")
    select_funding_account.select_option("")  # Select an empty option to indicate no funding account selected
    submit_button = logged_in_page.locator("input[value='Open New Account']")
    submit_button.click()
    error_message = logged_in_page.locator("text=No funding account selected")
    expect(error_message).to_be_visible()
