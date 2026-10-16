import pytest
from playwright.sync_api import expect


@pytest.mark.ai
def test_missing_payee_fields_show_validation_messages(logged_in_page, base_url, registered_user):
    logged_in_page.goto(f"{base_url}/billpay.htm")
    logged_in_page.locator("input[name='payee.name']").fill("")
    logged_in_page.locator("input[value='Send Payment']").click()
    expect(logged_in_page.get_by_text("Payee Name: is required")).to_be_visible()
