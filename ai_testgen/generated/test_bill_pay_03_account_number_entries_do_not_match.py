import pytest
from playwright.sync_api import expect


@pytest.mark.ai
def test_account_number_entries_do_not_match(logged_in_page, base_url, registered_user):
    logged_in_page.goto(f"{base_url}/billpay.htm")
    logged_in_page.locator("input[name='payee.accountNumber']").fill("1234567890")
    logged_in_page.locator("input[name='verifyAccount']").fill("9876543210")
    logged_in_page.locator("input[value='Send Payment']").click()
    expect(logged_in_page.get_by_text("Account numbers do not match")).to_be_visible()
