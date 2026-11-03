"""Page object for ParaBank's Bill Pay screen (/billpay.htm)."""

from playwright.sync_api import Locator, expect

from framework.pages.base_page import BasePage


class BillPayPage(BasePage):
    """Pay a bill from one of the customer's accounts.

    Validation is client-side: all 13 error spans are in the DOM from the start (hidden), and "Send Payment" reveals the
    ones that apply. A valid payment replaces the form with a confirmation on the same URL. Assertions stay in the tests.
    """

    path = "/billpay.htm"

    # keyword name -> form `name` attribute; the inputs have no accessible name, so the `name` binding is the locator
    FIELDS: dict[str, str] = {
        "payee_name": "payee.name",
        "address": "payee.address.street",
        "city": "payee.address.city",
        "state": "payee.address.state",
        "zip_code": "payee.address.zipCode",
        "phone": "payee.phoneNumber",
        "account": "payee.accountNumber",
        "verify_account": "verifyAccount",
        "amount": "amount",
    }

    @property
    def heading(self) -> Locator:
        """The form's heading, "Bill Payment Service" (hidden once the confirmation replaces the form)."""
        return self.page.get_by_role("heading", name="Bill Payment Service")

    @property
    def submit_button(self) -> Locator:
        return self.page.get_by_role("button", name="Send Payment", exact=True)

    @property
    def result_heading(self) -> Locator:
        return self.page.get_by_role("heading", name="Bill Payment Complete")

    @property
    def result_message(self) -> Locator:
        """The paragraph "Bill Payment to {payee} in the amount of ${amount} from account {account} was successful."."""
        return self.page.get_by_role("paragraph").filter(has_text="Bill Payment to")

    @property
    def from_account(self) -> Locator:
        """The From account dropdown. It has no accessible name and no id; its form `name` is the stable handle."""
        return self.page.locator("select[name='fromAccountId']")

    def field(self, name: str) -> Locator:
        """One of the nine text inputs, by its FIELDS keyword name (e.g. "payee_name")."""
        return self.page.locator(f"input[name='{self.FIELDS[name]}']")

    def field_error(self, message_id: str) -> Locator:
        """ONE validation message, by the part of its id after `validationModel-` (e.g. "verifyAccount-mismatch").

        Matched by id, because the visible texts repeat ("Account number is required." is shown for both account and verify
        account), so a text locator matches two elements. Each id is hand-written and unique on the page.
        """
        return self.page.locator(f"#validationModel-{message_id}")

    def open(self) -> "BillPayPage":
        """Open the page and wait until the form is usable: the From dropdown loads its accounts asynchronously."""
        super().open()
        expect(self.from_account.get_by_role("option")).not_to_have_count(0)
        return self

    def fill_payment(self, **values: str) -> "BillPayPage":
        """Fill the given fields (keys are the FIELDS names); omitted fields stay empty. The From account is left as is."""
        unknown = set(values) - set(self.FIELDS)
        if unknown:
            raise ValueError(f"unknown bill pay field(s) {sorted(unknown)}; expected some of {sorted(self.FIELDS)}")
        for name, value in values.items():
            self.fill(self.field(name), value)
        return self

    def submit(self) -> "BillPayPage":
        """Click "Send Payment". Nothing is waited for: invalid input shows messages, valid input shows the confirmation."""
        self.click(self.submit_button)
        return self

    def pay(self, **values: str) -> "BillPayPage":
        """Fill the given fields and submit."""
        return self.fill_payment(**values).submit()
