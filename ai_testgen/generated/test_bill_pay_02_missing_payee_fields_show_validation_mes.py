import pytest
from playwright.sync_api import expect

@pytest.mark.ai
def test_missing_payee_fields_show_validation_messages(logged_in_page, base_url):
    logged_in_page.wait_for_url('billpay.htm')
    page = logged_in_page
    page.locator('input[name="payee.name"]').fill('')
    page.locator('input[name="payee.address.street"]').fill('123 Main St')
    page.locator('input[name="payee.address.city"]').fill('Anytown')
    page.locator('input[name="payee.address.state"]').fill('CA')
    page.locator('input[name="payee.address.zipCode"]').fill('12345')
    page.locator('input[name="payee.phoneNumber"]').fill('1234567890')
    page.locator('input[name="payee.accountNumber"]').fill('123456789')
    page.locator('input[name="verifyAccount"]').fill('123456789')
    page.locator('input[name="amount"]').fill('100.00')
    select = page.locator('select[name="fromAccountId"]')
    select.select_option(registered_user['account_number'])
    page.locator('input[value="Send Payment"]').click()
    expect(page.locator('input[name="payee.name"]').get_attribute('validationMessage')).to_contain_text('Please enter payee name')
    expect(page.locator('input[name="payee.address.street"]').get_attribute('validationMessage')).to_not_contain_text('Please enter payee name')
