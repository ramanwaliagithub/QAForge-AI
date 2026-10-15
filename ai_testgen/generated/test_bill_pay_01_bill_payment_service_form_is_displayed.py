import pytest
from playwright.sync_api import expect

@pytest.mark.ai
def test_bill_payment_form(logged_in_page, base_url):
    logged_in_page.wait_for_url('billpay.htm')
    page = logged_in_page

    # Verify that the form contains fields for payee name, address, city, state, zip, phone, account number (entered twice), amount, and a 'from' account
    expect(page.locator('input[name="payee.name"]').get_attribute('value')).to_be_empty()
    expect(page.locator('input[name="payee.address.street"]').get_attribute('value')).to_be_empty()
    expect(page.locator('input[name="payee.address.city"]').get_attribute('value')).to_be_empty()
    expect(page.locator('input[name="payee.address.state"]').get_attribute('value')).to_be_empty()
    expect(page.locator('input[name="payee.address.zipCode"]').get_attribute('value')).to_be_empty()
    expect(page.locator('input[name="payee.phoneNumber"]').get_attribute('value')).to_be_empty()
    expect(page.locator('input[name="payee.accountNumber"]').get_attribute('value')).to_be_empty()
    expect(page.locator('input[name="verifyAccount"]').get_attribute('value')).to_be_empty()
    expect(page.locator('input[name="amount"]').get_attribute('value')).to_be_empty()
    expect(page.locator('select[name="fromAccountId"]').get_attribute('value')).to_be_empty()

    # Verify that the 'from' account dropdown contains all account IDs
    accounts = logged_in_page.accounts_table
    account_ids = [account.get_attribute('id') for account in accounts]
    expect(page.locator('select[name="fromAccountId"]').options()).to_have_length(len(account_ids))
    for account_id in account_ids:
        expect(page.locator('select[name="fromAccountId"]').option(account_id)).to_be_visible()
