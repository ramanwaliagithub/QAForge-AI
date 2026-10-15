import pytest
from playwright.sync_api import expect

@pytest.mark.ai
def test_successful_payment(logged_in_page, base_url, registered_user):
    logged_in_page.wait_for_url('account')
    logged_in_page.click(page.locator('text="Bill Pay"'))
    logged_in_page.wait_for_url('billpay.htm')
    logged_in_page.fill(page.locator('input[name="payee.name"]'), 'Test Payee')
    logged_in_page.fill(page.locator('input[name="payee.address.street"]'), '123 Main St')
    logged_in_page.fill(page.locator('input[name="payee.address.city"]'), 'Anytown')
    logged_in_page.fill(page.locator('input[name="payee.address.state"]'), 'CA')
    logged_in_page.fill(page.locator('input[name="payee.address.zipCode"]'), '12345')
    logged_in_page.fill(page.locator('input[name="payee.phoneNumber"]'), '1234567890')
    logged_in_page.fill(page.locator('input[name="payee.accountNumber"]'), '1234567890')
    logged_in_page.fill(page.locator('input[name="verifyAccount"]'), '1234567890')
    logged_in_page.fill(page.locator('input[name="amount"]'), '100.00')
    logged_in_page.locator('select[name="fromAccountId"]').select_option(registered_user['account_number'])
    logged_in_page.click(page.locator('input[value="Send Payment"]'))
    expect(logged_in_page.locator('text="Bill Payment Complete"')).to_be_visible()
    expect(logged_in_page.locator('text="Test Payee"')).to_be_visible()
    expect(logged_in_page.locator('text="100.00"')).to_be_visible()
    expect(logged_in_page.locator('text="1234567890"')).to_be_visible()
