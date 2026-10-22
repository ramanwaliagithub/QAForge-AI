import re

from playwright.sync_api import expect

from framework.pages.base_page import BasePage


class AccountsPage(BasePage):
    path = "/overview.htm"

    @property
    def accounts_table(self):
        return self.page.get_by_role("table")

    @property
    def account_links(self):
        """One link per account in the overview table; an account's link text is its number."""
        return self.accounts_table.get_by_role("link", name=re.compile(r"^\d+$"))

    @property
    def account_type(self):
        """The account-type dropdown: the combobox that offers SAVINGS (the funding dropdown lists numbers)."""
        return self.page.get_by_role("combobox").filter(has=self.page.get_by_role("option", name="SAVINGS"))

    @property
    def funding_account(self):
        return self.page.locator("#fromAccountId")  # no accessible name or label in ParaBank; the id is hand-written

    @property
    def opened_heading(self):
        return self.page.get_by_role("heading", name="Account Opened!")

    @property
    def new_account_link(self):
        """The link carrying the new account number, found through its sentence ("Your new account number: 123")."""
        return self.page.get_by_role("paragraph").filter(has_text="Your new account number").get_by_role("link")

    def open_new_account(self, account_type: str = "SAVINGS"):
        """Open a new account of type CHECKING or SAVINGS; returns its account id."""
        self.page.goto(f"{self.base_url}/openaccount.htm")
        self.account_type.select_option(account_type)
        # The funding-account dropdown is populated asynchronously.
        expect(self.funding_account.locator("option")).not_to_have_count(0)
        self.click(self.page.get_by_role("button", name="Open New Account"))
        expect(self.new_account_link).to_be_visible()
        return self.new_account_link.inner_text()
