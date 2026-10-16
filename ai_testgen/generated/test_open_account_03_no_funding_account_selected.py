import pytest
from playwright.sync_api import expect


@pytest.mark.ai
def test_no_funding_account_selected(logged_in_page, base_url, registered_user):
    logged_in_page.goto(f"{base_url}/openaccount.htm")
    logged_in_page.locator("input[value='Open New Account']").click()
    logged_in_page.locator("#type").select_option(index=0)
    logged_in_page.locator("#fromAccountId").select_option(index=-1)  # Select no option
    logged_in_page.locator("#amount").fill("1000")
    logged_in_page.locator("input[value='Open New Account']").click()
    expect(logged_in_page.get_by_text("No funding account selected")).to_be_visible()
