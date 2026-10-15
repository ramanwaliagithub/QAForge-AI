import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage, BasePage


@pytest.mark.ai
def test_amount_is_not_a_number(logged_in_page, base_url):
    logged_in_page.wait_for_url('billpay.htm')
    logged_in_page.fill(page.locator('input[name="payee.name"]'), 'Test Payee')
    logged_in_page.fill(page.locator('input[name="payee.address.street"]'), '123 Main St')
    logged_in_page.fill(page.locator('input[name="payee.address.city"]'), 'Anytown')
    logged_in_page.fill(page.locator('input[name="payee.address.state"]'), 'CA')
    logged_in_page.fill(page.locator('input[name="payee.address.zipCode"]'), '12345')
    logged_in_page.fill(page.locator('input[name="payee.phoneNumber"]'), '1234567890')
    logged_in_page.fill(page.locator('input[name="payee.accountNumber"]'), '1234567890')
    logged_in_page.fill(page.locator('input[name="verifyAccount"]'), '1234567890')
    logged_in_page.fill(page.locator('input[name="amount"]'), 'abc')  # non-numeric value
    logged_in_page.fill(page.locator('select[name="fromAccountId"]'), '1234567890')  # select an account
    logged_in_page.click(page.locator('input[value="Send Payment"]'))
    expect(logged_in_page.error_message).to_contain_text('Invalid amount')
