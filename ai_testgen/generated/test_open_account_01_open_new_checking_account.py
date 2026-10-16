import pytest
from playwright.sync_api import expect


@pytest.mark.ai
def test_open_new_checking_account(logged_in_page, base_url, registered_user):
    logged_in_page.goto(f"{base_url}/account/openaccount.htm")
    logged_in_page.locator("text=Open New Account").click()
    logged_in_page.locator("text=CHECKING").select_option(index=0)
    logged_in_page.locator("#accountNumber").select_option(index=0)
    logged_in_page.locator("#amount").fill("1000")
    logged_in_page.locator("input[value='Add Account']").click()
    expect(logged_in_page.get_by_text("Account Opened!")).to_be_visible()
    expect(logged_in_page.get_by_text("12345")).to_be_visible()
