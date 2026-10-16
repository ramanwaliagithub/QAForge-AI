import pytest
from playwright.sync_api import expect


@pytest.mark.ai
def test_account_with_insufficient_funds_is_selected(logged_in_page, base_url, registered_user):
    logged_in_page.goto(f"{base_url}/paybills.htm")
    logged_in_page.locator("#account").select_option(index=0)  # Select account with insufficient funds
    logged_in_page.locator("#payee").fill("Test Payee")
    logged_in_page.locator("#accountNumber").fill("1234567890")
    logged_in_page.locator("#amount").fill("1000")  # Amount greater than account balance
    logged_in_page.locator("input[value='Pay with this transfert']").click()
    expect(logged_in_page.get_by_text("Insufficient funds")).to_be_visible()
