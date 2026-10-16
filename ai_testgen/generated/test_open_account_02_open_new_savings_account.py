import pytest
from playwright.sync_api import expect


@pytest.mark.ai
def test_open_new_savings_account(logged_in_page, base_url, registered_user):
    logged_in_page.goto(f"{base_url}/openaccount.htm")
    logged_in_page.locator("#type").select_option(index=0)  # Select 'SAVINGS' as the account type
    logged_in_page.locator("#fromAccountId").select_option(index=0)  # Select a funding account
    logged_in_page.locator("input[value='Open New Account']").click()
    expect(logged_in_page.get_by_text("Account Opened!")).to_be_visible()
    expect(logged_in_page.get_by_text("with a new savings account number")).to_be_visible()
    expect(logged_in_page.accounts_table).to_have_text(registered_user["first_name"] + " " + registered_user["last_name"])
