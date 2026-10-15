import pytest
from playwright.sync_api import expect

@pytest.mark.ai
def test_account_with_insufficient_funds_is_selected(page, base_url, registered_user, login_page, logged_in_page):
    logged_in_page.goto(f"{base_url}/billpay.htm")
    page.locator('input[name="payee.name"]').fill("Test Payee")
    page.locator('input[name="payee.address.street"]').fill("123 Main St")
    page.locator('input[name="payee.address.city"]').fill("Anytown")
    page.locator('input[name="payee.address.state"]').fill("CA")
    page.locator('input[name="payee.address.zipCode"]').fill("12345")
    page.locator('input[name="payee.phoneNumber"]').fill("1234567890")
    page.locator('input[name="payee.accountNumber"]').fill("123456789")
    page.locator('input[name="verifyAccount"]').fill("123456789")
    page.locator('input[name="amount"]').fill("1000.00")
    select = page.locator('select[name="fromAccountId"]')
    select.select_option(index=0)  # Select the first account
    page.locator('input[value="Send Payment"]').click()
    error_message = logged_in_page.get_by_text("Error: Insufficient funds in account")
    expect(error_message).to_be_visible()
