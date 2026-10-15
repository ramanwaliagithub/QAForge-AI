import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage, LoginPage


@pytest.mark.ai
def test_account_with_insufficient_funds_is_selected(login_page, base_url, registered_user):
    login_page.login(registered_user['username'], registered_user['password'])
    logged_in_page = LoginPage(login_page, base_url)
    logged_in_page.wait_for_url('account')
    accounts = AccountsPage(logged_in_page, base_url)
    accounts.open_new_account('SAVINGS')  # Create a new savings account
    accounts.open_new_account('CHECKING')  # Create a new checking account with insufficient funds
    logged_in_page.wait_for_url('billpay.htm')
    page = logged_in_page.page
    page.locator('input[name="payee.name"]').fill('Test Payee')
    page.locator('input[name="payee.address.street"]').fill('123 Main St')
    page.locator('input[name="payee.address.city"]').fill('Anytown')
    page.locator('input[name="payee.address.state"]').fill('CA')
    page.locator('input[name="payee.address.zipCode"]').fill('12345')
    page.locator('input[name="payee.phoneNumber"]').fill('1234567890')
    page.locator('input[name="payee.accountNumber"]').fill('1234567890')
    page.locator('input[name="verifyAccount"]').fill('1234567890')
    page.locator('input[name="amount"]').fill('1000.00')
    select = page.locator('select[name="fromAccountId"]')
    select.select_option(registered_user['username'])  # Select the account with insufficient funds
    page.locator('input[value="Send Payment"]').click()
    expect(page.locator('text=Insufficient funds')).to_be_visible()
