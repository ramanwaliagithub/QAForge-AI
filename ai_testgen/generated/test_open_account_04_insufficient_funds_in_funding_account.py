import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_open_checking_account_with_insufficient_funds(logged_in_page, base_url, registered_user):
    logged_in_page.goto(f"{base_url}/openaccount.htm")
    logged_in_page.click("input[value='Open New Account']")
    accounts_page = AccountsPage(logged_in_page, base_url)
    accounts_page.open_new_account("CHECKING")
    select_funding_account = logged_in_page.locator("#fromAccountId")
    select_funding_account.select_option(index=0)  # Select the first funding account
    logged_in_page.fill("input[name='initialBalance']", "0")  # Enter an initial deposit amount of 0
    logged_in_page.click("input[value='Open New Account']")
    error_message = logged_in_page.get_by_text("Error: Insufficient funds in funding account").text_content()
    expect(error_message).to_contain_text("Insufficient funds")
