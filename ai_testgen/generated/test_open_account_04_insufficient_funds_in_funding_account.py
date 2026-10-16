import pytest
from playwright.sync_api import expect


@pytest.mark.ai
def test_insufficient_funds_in_funding_account(logged_in_page, base_url, registered_user):
    logged_in_page.goto(f"{base_url}/newaccount.htm")
    logged_in_page.locator("input[value='Open New Account']").click()
    logged_in_page.locator("#type").select_option(index=0)
    logged_in_page.locator("#accounttype").select_option(index=0)
    logged_in_page.locator("#initdeposit").fill("1000")
    logged_in_page.locator("#initdeposit").click()
    logged_in_page.locator("input[value='Open Account']").click()
    expect(logged_in_page.get_by_text("Insufficient funds in funding account")).to_be_visible()
