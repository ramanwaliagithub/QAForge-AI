import pytest
from playwright.sync_api import expect


@pytest.mark.ai
def test_successful_payment_shows_confirmation(logged_in_page, base_url, registered_user):
    logged_in_page.goto(f"{base_url}/billpay.htm")
    logged_in_page.locator("input[name='payee.name']").fill("Payee Name")
    logged_in_page.locator("input[name='payee.address.street']").fill("Address")
    logged_in_page.locator("input[name='payee.address.city']").fill("City")
    logged_in_page.locator("input[name='payee.address.state']").fill("State")
    logged_in_page.locator("input[name='payee.address.zipCode']").fill("Zip Code")
    logged_in_page.locator("input[name='payee.phoneNumber']").fill("Phone #")
    logged_in_page.locator("input[name='payee.accountNumber']").fill("Account #")
    logged_in_page.locator("input[name='verifyAccount']").fill("Verify Account #")
    logged_in_page.locator("input[name='amount']").fill("100")
    logged_in_page.locator("select[name='fromAccountId']").select_option(index=0)
    logged_in_page.locator("input[value='Send Payment']").click()
    expect(logged_in_page.get_by_text("Bill Payment Complete with payee name, amount, and from-account is displayed")).to_be_visible()
