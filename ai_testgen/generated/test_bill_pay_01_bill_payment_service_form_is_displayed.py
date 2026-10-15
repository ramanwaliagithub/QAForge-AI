import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_bill_payment_form(logged_in_page, base_url, registered_user):
    logged_in_page.goto(f"{base_url}/billpay.htm")

    # Verify that the form contains fields for payee name, address, city, state, zip, phone, account number (entered twice), amount, and a 'from' account
    page = logged_in_page
    payee_name = page.locator("input[name='payee.name']")
    expect(payee_name).to_be_visible()

    address_street = page.locator("input[name='payee.address.street']")
    expect(address_street).to_be_visible()

    city = page.locator("input[name='payee.address.city']")
    expect(city).to_be_visible()

    state = page.locator("input[name='payee.address.state']")
    expect(state).to_be_visible()

    zip_code = page.locator("input[name='payee.address.zipCode']")
    expect(zip_code).to_be_visible()

    phone_number = page.locator("input[name='payee.phoneNumber']")
    expect(phone_number).to_be_visible()

    account_number = page.locator("input[name='payee.accountNumber']")
    expect(account_number).to_be_visible()

    verify_account = page.locator("input[name='verifyAccount']")
    expect(verify_account).to_be_visible()

    amount = page.locator("input[name='amount']")
    expect(amount).to_be_visible()

    from_account = page.locator("select[name='fromAccountId']")
    expect(from_account).to_be_visible()

    send_payment = page.locator("input[value='Send Payment']")
    expect(send_payment).to_be_visible()

    # Fill in the form with test data
    page.fill(payee_name, "Test Payee")
    page.fill(address_street, "123 Main St")
    page.fill(city, "Anytown")
    page.fill(state, "CA")
    page.fill(zip_code, "12345")
    page.fill(phone_number, "123-456-7890")
    page.fill(account_number, "123456789")
    page.fill(verify_account, "123456789")
    page.fill(amount, "100.00")

    # Select the 'from' account
    from_account.select_option(index=0)

    # Click the 'Send Payment' button
    page.click(send_payment)

    # Verify that the form is displayed with all required fields
    expect(page.locator("text=The form is displayed with all required fields")).to_be_visible()
