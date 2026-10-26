"""HELD-OUT SET 3: written after sets 1 and 2 had been used to diagnose and fix the suggester. The unbiased one.
Do not tune the prompt on these. Generate with:  uv run python -m scripts.make_failure_samples heldout3
"""
from framework.pages import AccountsPage, LoginPage, RegisterPage


class LoginButtonRenamed(LoginPage):
    """Login form: the button now reads "Sign In"."""

    @property
    def submit(self):
        return self.page.get_by_role("button", name="Sign In", exact=True)


class LastNameFieldRenamed(RegisterPage):
    """Registration: customer.lastName became customer.surname."""

    FIELDS = {**RegisterPage.FIELDS, "last_name": "customer.surname"}


class PhoneFieldRenamed(RegisterPage):
    """Registration: customer.phoneNumber became customer.mobile."""

    FIELDS = {**RegisterPage.FIELDS, "phone": "customer.mobile"}


class FundingAccountRenamed(AccountsPage):
    """Open account: the funding dropdown id changed from #fromAccountId to #sourceAccount."""

    @property
    def funding_account(self):
        return self.page.locator("#sourceAccount")


USER = dict(first_name="Qa", last_name="Forge", street="1 St", city="C", state="CA", zip_code="90210",
            phone="555", ssn="123-45-6789", username="u", password="Passw0rd!")


def test_heldout3_login_button_renamed(page, base_url):
    LoginButtonRenamed(page, base_url).open().login("someone", "Passw0rd!")


def test_heldout3_last_name_field_renamed(page, base_url):
    LastNameFieldRenamed(page, base_url).open().register(**USER)


def test_heldout3_phone_field_renamed(page, base_url):
    PhoneFieldRenamed(page, base_url).open().register(**USER)


def test_heldout3_funding_account_renamed(logged_in_page, base_url):
    FundingAccountRenamed(logged_in_page, base_url).open_new_account("SAVINGS")
