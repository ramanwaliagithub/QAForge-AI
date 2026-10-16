import pytest
from playwright.sync_api import expect


@pytest.mark.ai
def test_transfer_money_between_own_accounts(logged_in_page, base_url, registered_user):
    logged_in_page.goto(f"{base_url}/transfer.htm")
    logged_in_page.locator("#amount").fill("50")
    logged_in_page.locator("#fromAccountId").select_option(index=0)
    logged_in_page.locator("#toAccountId").select_option(index=1)
    logged_in_page.locator("input[value='Transfer']").click()
    expect(logged_in_page.get_by_text("Transfer Complete!")).to_be_visible()
    amount = logged_in_page.locator("#amount").text_content()
    from_account = logged_in_page.locator("#fromAccountId").text_content()
    to_account = logged_in_page.locator("#toAccountId").text_content()
    expect(f"Transfer Complete! {amount} from {from_account} to {to_account}").to_be_visible()
