import pytest
from playwright.sync_api import expect


@pytest.mark.ai
def test_open_new_checking_account(logged_in_page, base_url, registered_user):
    logged_in_page.goto(f"{base_url}/openaccount.htm")
    logged_in_page.locator("#type").select_option(index=0)  # Select 'CHECKING' as the account type
    logged_in_page.locator("#fromAccountId").select_option(index=0)  # Select a funding account
    logged_in_page.locator("input[value='Open New Account']").click()
    expect(logged_in_page.get_by_text("Account Opened!")).to_be_visible()
    expect(logged_in_page.get_by_text("with a new checking account number")).to_be_visible()
    expect(logged_in_page.get_by_text("is shown")).to_be_visible()
    expect(logged_in_page.get_by_text("new account appears in Accounts Overview")).to_be_visible()
