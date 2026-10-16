import pytest
from playwright.sync_api import expect


@pytest.mark.ai
def test_open_new_account_requires_funding_account(logged_in_page, base_url, registered_user):
    logged_in_page.goto(f"{base_url}/newaccount.htm")
    logged_in_page.locator("text=Open New Account").click()
    logged_in_page.locator("#accounttype").select_option(index=0)  # Select 'CHECKING'
    logged_in_page.locator("#initialDeposit").fill("1000")
    logged_in_page.locator("input[value='Add Account']").click()
    expect(logged_in_page.get_by_text("Please select a funding account")).to_be_visible()
