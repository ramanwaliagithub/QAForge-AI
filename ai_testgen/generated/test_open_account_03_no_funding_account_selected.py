import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_open_checking_account_without_funding(logged_in_page, base_url):
    logged_in_page.goto(f"{base_url}/openaccount.htm")
    logged_in_page.click("input[value='Open New Account']")
    accounts = AccountsPage(logged_in_page, base_url)
    accounts.open_new_account("CHECKING")
    accounts.locator("#fromAccountId").select_option(index=0)
    logged_in_page.fill("input[name='initialBalance']", "100")
    logged_in_page.click("input[value='Open New Account']")
    error_message = logged_in_page.get_by_text("Error Message").text_content()
    expect(error_message).to_contain_text("No funding account selected")
