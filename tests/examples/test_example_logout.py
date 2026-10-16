import pytest
from playwright.sync_api import expect


@pytest.mark.ai
def test_logout_returns_to_login_form(login_page, registered_user):
    login_page.login(registered_user["username"], registered_user["password"])
    expect(login_page.logout_link).to_be_visible()
    login_page.logout()
    expect(login_page.submit).to_be_visible()
