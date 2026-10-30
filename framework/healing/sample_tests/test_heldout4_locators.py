"""HELD-OUT SET 4: written on Day 17, after the suggester stopped changing, for the final Phase 2 measurement.
Cases, ground truth and sample capture are committed BEFORE the model is run on them. Do not tune on these.
Generate with:  uv run python -m scripts.make_failure_samples heldout4
"""
from framework.pages import AccountsPage, LoginPage, RegisterPage, TransferPage


class StreetFieldRenamed(RegisterPage):
    """Registration: customer.address.street became customer.address.line1."""

    FIELDS = {**RegisterPage.FIELDS, "street": "customer.address.line1"}


class SsnFieldRenamed(RegisterPage):
    """Registration: customer.ssn became customer.taxId."""

    FIELDS = {**RegisterPage.FIELDS, "ssn": "customer.taxId"}


class ZipFieldRenamed(RegisterPage):
    """Registration: customer.address.zipCode became customer.address.postalCode."""

    FIELDS = {**RegisterPage.FIELDS, "zip_code": "customer.address.postalCode"}


class LoginButtonShortened(LoginPage):
    """Copy change: the login button reads "Login" instead of "Log In"."""

    @property
    def submit(self):
        return self.page.get_by_role("button", name="Login", exact=True)


class FromAccountRenamed(TransferPage):
    """Transfer: the source dropdown id changed from #fromAccountId to #sourceAccountId."""

    @property
    def from_account(self):
        return self.page.locator("#sourceAccountId")


class TransferButtonRenamed(TransferPage):
    """Copy change: the transfer button now reads "Send"."""

    @property
    def submit_button(self):
        return self.page.get_by_role("button", name="Send", exact=True)


class OpenAccountButtonRenamed(AccountsPage):
    """Copy change: the open-account button now reads "Create Account"."""

    def open_new_account(self, account_type: str = "SAVINGS"):
        self.page.goto(f"{self.base_url}/openaccount.htm")
        self.select_option(self.account_type, account_type)
        self.click(self.page.get_by_role("button", name="Create Account"))


USER = dict(first_name="Qa", last_name="Forge", street="1 St", city="C", state="CA", zip_code="90210",
            phone="555", ssn="123-45-6789", username="u", password="Passw0rd!")


def test_heldout4_street_field_renamed(page, base_url):
    StreetFieldRenamed(page, base_url).open().register(**USER)


def test_heldout4_ssn_field_renamed(page, base_url):
    SsnFieldRenamed(page, base_url).open().register(**USER)


def test_heldout4_zip_field_renamed(page, base_url):
    ZipFieldRenamed(page, base_url).open().register(**USER)


def test_heldout4_login_button_shortened(page, base_url):
    LoginButtonShortened(page, base_url).open().login("someone", "Passw0rd!")


def test_heldout4_from_account_renamed(new_customer_page, base_url):
    FromAccountRenamed(new_customer_page, base_url).open().transfer("10")


def test_heldout4_transfer_button_renamed(new_customer_page, base_url):
    TransferButtonRenamed(new_customer_page, base_url).open().transfer("10")


def test_heldout4_open_account_button_renamed(logged_in_page, base_url):
    OpenAccountButtonRenamed(logged_in_page, base_url).open_new_account("SAVINGS")
