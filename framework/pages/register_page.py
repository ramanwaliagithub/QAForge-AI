from framework.pages.base_page import BasePage


class RegisterPage(BasePage):
    path = "/register.htm"

    FIELDS = {
        "first_name": "customer.firstName",
        "last_name": "customer.lastName",
        "street": "customer.address.street",
        "city": "customer.address.city",
        "state": "customer.address.state",
        "zip_code": "customer.address.zipCode",
        "phone": "customer.phoneNumber",
        "ssn": "customer.ssn",
        "username": "customer.username",
        "password": "customer.password",
    }

    def register(self, **values: str):
        """Fill the registration form; `values` keys are the FIELDS names."""
        for key, field in self.FIELDS.items():
            self.fill(self.page.locator(f"input[name='{field}']"), values[key])
        self.fill(self.page.locator("input[name='repeatedPassword']"), values["password"])
        self.click(self.page.get_by_role("button", name="Register"))
        return self
