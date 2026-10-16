import pytest
from playwright.sync_api import expect


@pytest.mark.ai
def test_bill_payment_service_form_is_displayed(logged_in_page, base_url, registered_user):
    logged_in_page.goto(f"{base_url}/billpay.htm")
    expect(logged_in_page.get_by_text("Payee Name:")).to_be_visible()
    expect(logged_in_page.get_by_text("Address:")).to_be_visible()
    expect(logged_in_page.get_by_text("City:")).to_be_visible()
    expect(logged_in_page.get_by_text("State:")).to_be_visible()
    expect(logged_in_page.get_by_text("Zip Code:")).to_be_visible()
    expect(logged_in_page.get_by_text("Phone #:")).to_be_visible()
    expect(logged_in_page.get_by_text("Account #:")).to_be_visible()
    expect(logged_in_page.get_by_text("Verify Account #:")).to_be_visible()
    expect(logged_in_page.get_by_text("Amount: $")).to_be_visible()
    expect(logged_in_page.get_by_role("button", name="Send Payment")).to_be_visible()
    select = logged_in_page.locator("select[name='fromAccountId']")
    expect(select).to_have_value(0)
    expect(select).to_have_option(index=0)
    expect(select).to_have_option(index=1)
