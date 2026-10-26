"""HELD-OUT SET 2: written after set 1 had been used to diagnose the suggester, so it is the unbiased one.
Do not tune the prompt on these. Generate with:  uv run python -m scripts.make_failure_samples heldout2
"""
from framework.pages import LoginPage, RegisterPage, TransferPage


class PasswordInputRenamed(LoginPage):
    """Login form: the password field's name attribute changed to `pass`."""

    @property
    def password(self):
        return self.page.locator("input[name='pass']")


class RegisterButtonRenamed(RegisterPage):
    """Registration: the submit button now reads "Sign Up"."""

    def register(self, **values):
        for key, field in self.FIELDS.items():
            self.fill(self.page.locator(f"input[name='{field}']"), values[key])
        self.fill(self.page.locator("input[name='repeatedPassword']"), values["password"])
        self.click(self.page.get_by_role("button", name="Sign Up", exact=True))
        return self


class StateFieldRenamed(RegisterPage):
    """Registration: customer.address.state became customer.address.region."""

    FIELDS = {**RegisterPage.FIELDS, "state": "customer.address.region"}


class ToAccountIdRenamed(TransferPage):
    """Transfer: the destination dropdown id changed from #toAccountId to #destinationAccount."""

    @property
    def to_account(self):
        return self.page.locator("#destinationAccount")


USER = dict(first_name="Qa", last_name="Forge", street="1 St", city="C", state="CA", zip_code="90210",
            phone="555", ssn="123-45-6789", username="u", password="Passw0rd!")


def test_heldout2_password_renamed(page, base_url):
    PasswordInputRenamed(page, base_url).open().login("someone", "Passw0rd!")


def test_heldout2_register_button_renamed(page, base_url):
    RegisterButtonRenamed(page, base_url).open().register(**USER)


def test_heldout2_state_field_renamed(page, base_url):
    StateFieldRenamed(page, base_url).open().register(**USER)


def test_heldout2_to_account_id_renamed(new_customer_page, base_url):
    ToAccountIdRenamed(new_customer_page, base_url).open().transfer("10")
