import pytest
from playwright.sync_api import expect


@pytest.mark.ai
def test_missing_payee_fields_show_validation_messages(logged_in_page, base_url, registered_user):
    logged_in_page.goto(f"{base_url}/paybills.htm")
    logged_in_page.locator("#payeeName").fill("")
    logged_in_page.locator("input[value='Add Payee']").click()
    expect(logged_in_page.get_by_text("Payee name is required.")).to_be_visible()
