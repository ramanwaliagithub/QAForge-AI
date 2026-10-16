import pytest
from playwright.sync_api import expect


@pytest.mark.ai
def test_amount_is_not_a_number(logged_in_page, base_url, registered_user):
    logged_in_page.goto(f"{base_url}/billpay.htm")
    logged_in_page.locator("input[name='payee.name']").fill("Test Payee")
    logged_in_page.locator("input[name='payee.address.street']").fill("123 Main St")
    logged_in_page.locator("input[name='payee.address.city']").fill("Anytown")
    logged_in_page.locator("input[name='payee.address.state']").fill("CA")
    logged_in_page.locator("input[name='payee.address.zipCode']").fill("12345")
    logged_in_page.locator("input[name='payee.phoneNumber']").fill("1234567890")
    logged_in_page.locator("input[name='payee.accountNumber']").fill("1234567890")
    logged_in_page.locator("input[name='verifyAccount']").fill("1234567890")
    logged_in_page.locator("input[name='amount']").fill("abc")  # non-numeric value
    logged_in_page.locator("select[name='fromAccountId']").select_option(index=0)
    logged_in_page.locator("input[value='Send Payment']").click()
    expect(logged_in_page.get_by_text("Invalid amount")).to_be_visible()
