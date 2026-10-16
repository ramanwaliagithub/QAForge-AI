import pytest
from playwright.sync_api import expect


@pytest.mark.ai
def test_loan_request_is_approved(logged_in_page, base_url):
    logged_in_page.goto(f"{base_url}/requestloan.htm")
    logged_in_page.locator("#amount").fill("1000")
    logged_in_page.locator("#downPayment").fill("100")
    logged_in_page.locator("#fromAccountId").select_option(index=0)
    logged_in_page.locator("input[value='Apply Now']").click()
    expect(logged_in_page.get_by_text("Congratulations, your loan has been approved.")).to_be_visible()
