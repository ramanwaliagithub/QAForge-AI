import pytest
from playwright.sync_api import expect

@pytest.mark.ai
def test_transfer_same_amount_same_account(page, base_url, registered_user, login_page, logged_in_page):
    logged_in_page.goto(f"{base_url}/transfer.htm")
    page.locator("#amount").fill("50")
    logged_in_page.locator("#fromAccountId").select_option(index=0)
    logged_in_page.locator("#toAccountId").select_option(index=0)
    logged_in_page.locator("input[value='Transfer']").click()
    expect(logged_in_page.locator("text=Transfer Complete!")).to_be_visible()
    expect(logged_in_page.locator("text=50")).to_be_visible()
    expect(logged_in_page.locator("text=account id 1")).to_be_visible()
    expect(logged_in_page.locator("text=account id 2")).to_be_visible()
