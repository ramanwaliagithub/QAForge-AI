"""What ParaBank's registration form takes from generated data: the limits behind the rules in framework/data/models.py."""
import pytest
from playwright.sync_api import expect

from framework.pages import RegisterPage


def _register(page, base_url, customer):
    RegisterPage(page, base_url).open().register(**customer.register_kwargs())


def test_a_name_with_an_apostrophe_and_a_hyphen_registers_and_is_shown_as_given(page, base_url, data_factory):
    customer = data_factory.customer().model_copy(update={"first_name": "Mary", "last_name": "O'Neil-Smith"})
    _register(page, base_url, customer)
    expect(page.get_by_text("Welcome Mary O'Neil-Smith")).to_be_visible()


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="ParaBank bug: HTTP 400 'Character decoding failed' for a non-ASCII name such as Siobhán")
def test_a_name_with_an_accent_registers(page, base_url, data_factory):
    customer = data_factory.customer().model_copy(update={"first_name": "Siobhán"})  # model_copy skips validation, on purpose
    _register(page, base_url, customer)
    expect(page.get_by_role("link", name="Log Out")).to_be_visible()


def test_generated_customers_from_the_factory_register(page, base_url, data_factory):
    customer = data_factory.customer()
    _register(page, base_url, customer)
    expect(page.get_by_text(f"Welcome {customer.first_name} {customer.last_name}")).to_be_visible()
