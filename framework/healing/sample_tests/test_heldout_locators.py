"""HELD-OUT broken locators: written after the suggester prompt was tuned on test_broken_locators.py, on other pages and
page objects, to check the prompt is not just fitted to the first samples. Never edit the prompt while looking at these.

Generate with:  uv run python -m scripts.make_failure_samples heldout
"""
from framework.pages import AccountsPage, LoginPage, RegisterPage


class UsernameInputRenamed(LoginPage):
    """Login form: the username field's name attribute changed to `user`."""

    @property
    def username(self):
        return self.page.locator("input[name='user']")


class LogoutLinkRenamed(LoginPage):
    """Copy change: the logout link now reads "Sign Out"."""

    @property
    def logout_link(self):
        return self.page.get_by_role("link", name="Sign Out", exact=True)


class AccountTypeDropdownChanged(AccountsPage):
    """The account-type dropdown no longer offers SAVINGS under that name."""

    @property
    def account_type(self):
        return self.page.get_by_role("combobox").filter(has=self.page.get_by_role("option", name="SAVER"))


class FirstNameFieldRenamed(RegisterPage):
    """Registration: customer.firstName became customer.givenName."""

    FIELDS = {**RegisterPage.FIELDS, "first_name": "customer.givenName"}


USER = dict(first_name="Qa", last_name="Forge", street="1 St", city="C", state="CA", zip_code="90210",
            phone="555", ssn="123-45-6789", username="u", password="Passw0rd!")


def test_heldout_username_renamed(page, base_url):
    UsernameInputRenamed(page, base_url).open().login("someone", "Passw0rd!")


def test_heldout_logout_link_renamed(logged_in_page, base_url):
    LogoutLinkRenamed(logged_in_page, base_url).logout()


def test_heldout_account_type_dropdown(logged_in_page, base_url):
    AccountTypeDropdownChanged(logged_in_page, base_url).open_new_account("SAVINGS")


def test_heldout_first_name_field_renamed(page, base_url):
    FirstNameFieldRenamed(page, base_url).open().register(**USER)
