import pytest
from playwright.sync_api import expect

from framework.pages import BasePage


@pytest.mark.ai
def test_missing_payee_fields_show_validation_messages(
    logged_in_page, base_url, registered_user
):
    logged_in_page.goto(f"{base_url}/billpay.htm")
    page = logged_in_page

    # Leave a required payee field blank
    page.fill(page.locator("input[name='payee.name']"), "")

    # Submit the form
    page.locator("input[value='Send Payment']").click()

    # Assert error message is shown next to the blank field
    error_message_locator = page.get_by_text("Error: Payee Name is required")
    expect(error_message_locator).to_be_visible()
