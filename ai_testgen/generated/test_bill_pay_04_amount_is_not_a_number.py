import pytest
from playwright.sync_api import expect

from framework.pages import BasePage


@pytest.mark.ai
def test_amount_is_not_a_number(page, base_url, registered_user, login_page, logged_in_page):
    logged_in_page.goto(f"{base_url}/billpay.htm")
    page.locator('input[name="payee.name"]').fill(registered_user['first_name'])
    page.locator('input[name="payee.address.street"]').fill(registered_user['first_name'])
    page.locator('input[name="payee.address.city"]').fill(registered_user['first_name'])
    page.locator('input[name="payee.address.state"]').fill(registered_user['first_name'])
    page.locator('input[name="payee.address.zipCode"]').fill(registered_user['first_name'])
    page.locator('input[name="payee.phoneNumber"]').fill(registered_user['first_name'])
    page.locator('input[name="payee.accountNumber"]').fill(registered_user['first_name'])
    page.locator('input[name="verifyAccount"]').fill(registered_user['first_name'])
    page.locator('input[name="amount"]').fill('abc')  # non-numeric value
    select = page.locator('select[name="fromAccountId"]')
    select.select_option(index=0)
    page.locator('input[value="Send Payment"]').click()
    error_message = logged_in_page.get_by_text('Error message is shown')
    expect(error_message).to_be_visible()
