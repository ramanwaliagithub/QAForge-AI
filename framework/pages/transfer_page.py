import re

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
        return self.page.locator("input[value='Transfer']")

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
        """Open the page and wait until the account dropdowns are filled (they load asynchronously)."""
        super().open()
        self.to_account.locator("option").nth(accounts - 1).wait_for(state="attached")
        return self

    def transfer(self, amount: str, from_index: int = 0, to_index: int = 0):
        """Fill the form, submit and wait for the result heading. Assertions stay in the tests."""
        if amount:
            self.fill(self.amount, amount)
        self.from_account.select_option(index=from_index)
        self.to_account.select_option(index=to_index)
        self.click(self.submit_button)
        self.result_heading.wait_for()
        return self
