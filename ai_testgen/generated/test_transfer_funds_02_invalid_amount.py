import pytest
from playwright.sync_api import expect


@pytest.mark.ai
def test_invalid_amount(logged_in_page, base_url, registered_user):
    logged_in_page.goto(f"{base_url}/transfer.htm")
    logged_in_page.locator("#amount").fill("-50")
    logged_in_page.locator("#fromAccountId").select_option(index=0)
    logged_in_page.locator("#toAccountId").select_option(index=1)
    logged_in_page.locator("input[value='Transfer']").click()
    expect(logged_in_page.get_by_text("Invalid amount")).to_be_visible()
