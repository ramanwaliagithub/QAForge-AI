from framework.pages.base_page import BasePage


class AccountsPage(BasePage):
    path = "/overview.htm"

    @property
    def accounts_table(self):
        return self.page.locator("#accountTable")

    @property
    def account_links(self):
        return self.accounts_table.locator("a[href*='activity.htm']")

    def open_new_account(self, account_type: str = "SAVINGS"):
        """Open a new account of type CHECKING or SAVINGS; returns its account id."""
        self.page.goto(f"{self.base_url}/openaccount.htm")
        self.page.locator("#type").select_option(account_type)
        # The funding-account dropdown is populated asynchronously.
        self.page.locator("#fromAccountId option").first.wait_for(state="attached")
        self.click(self.page.get_by_role("button", name="Open New Account"))
        new_id = self.page.locator("#newAccountId")
        new_id.wait_for()
        return new_id.inner_text()

    @property
    def open_account_result(self):
        return self.page.locator("#openAccountResult")
