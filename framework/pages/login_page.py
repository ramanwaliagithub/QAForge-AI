from framework.pages.base_page import BasePage


class LoginPage(BasePage):
    path = "/index.htm"

    @property
    def username(self):
        return self.page.locator("input[name='username']")

    @property
    def password(self):
        return self.page.locator("input[name='password']")

    @property
    def submit(self):
        return self.page.get_by_role("button", name="Log In")

    @property
    def logout_link(self):
        return self.page.get_by_role("link", name="Log Out")

    def login(self, username: str, password: str):
        self.fill(self.username, username)
        self.fill(self.password, password)
        self.click(self.submit)
        return self

    def logout(self):
        self.click(self.logout_link)
        return self
