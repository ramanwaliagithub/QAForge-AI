import re

from playwright.sync_api import expect

from framework.pages.base_page import BasePage


class TransferPage(BasePage):
    path = "/transfer.htm"

    @property
    def amount(self):
        return self.page.locator("#amount")

    @property
    def from_account(self):
        return self.page.locator("#fromAccountId")

    @property
    def to_account(self):
        return self.page.locator("#toAccountId")

    @property
    def submit_button(self):
        return self.page.get_by_role("button", name="Transfer", exact=True)

    @property
    def success_heading(self):
        return self.page.get_by_role("heading", name="Transfer Complete!")

    @property
    def error_heading(self):
        return self.page.get_by_role("heading", name="Error!")

    @property
    def result_heading(self):
        """Whichever result the page shows after submitting: success or error."""
        return self.page.get_by_role("heading", name=re.compile(r"Transfer Complete!|Error!"))

    def open(self, accounts: int = 1):
        """Open the page and wait until the dropdowns list `accounts` accounts (they load asynchronously)."""
        super().open()
        expect(self.to_account.get_by_role("option")).to_have_count(accounts)
        return self

    def transfer(self, amount: str, from_index: int = 0, to_index: int = 0):
        """Fill the form, submit and wait for the result heading. Assertions stay in the tests."""
        if amount:
            self.fill(self.amount, amount)
        self.select_option(self.from_account, index=from_index)
        self.select_option(self.to_account, index=to_index)
        self.click(self.submit_button)
        self.result_heading.wait_for()
        return self
