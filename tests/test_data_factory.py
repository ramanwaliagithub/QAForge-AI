"""The seeded factory: reproducible from a seed, unique where uniqueness matters, exact where money is concerned."""
import re
from decimal import Decimal

import pytest

from framework.data import DataFactory, Identity
from framework.pages.register_page import RegisterPage


def test_the_same_seed_gives_the_same_customers_credentials_included():
    assert DataFactory(seed=11).customers(20) == DataFactory(seed=11).customers(20)


def test_a_different_seed_gives_different_people_and_different_usernames():
    one, other = DataFactory(seed=11).customers(20), DataFactory(seed=12).customers(20)
    assert {c.username for c in one}.isdisjoint({c.username for c in other})
    assert [c.first_name for c in one] != [c.first_name for c in other]


def test_without_a_seed_one_is_chosen_and_kept_so_the_run_can_be_replayed():
    factory = DataFactory()
    assert isinstance(factory.seed, int) and DataFactory(seed=factory.seed).customers(5) == factory.customers(5)


def test_usernames_are_unique_and_shaped_for_the_form():
    names = [c.username for c in DataFactory(seed=1).customers(1000)]
    assert len(set(names)) == 1000 and all(re.fullmatch(r"qaforge_[0-9a-f]{10}", n) for n in names)


def test_passwords_have_every_character_class():
    for customer in DataFactory(seed=2).customers(100):
        assert re.search(r"[a-z]", customer.password) and re.search(r"[A-Z]", customer.password)
        assert re.search(r"\d", customer.password) and "!" in customer.password and len(customer.password) == 12


def test_a_customer_fits_the_registration_form_exactly():
    assert set(DataFactory(seed=3).customer().register_kwargs()) == set(RegisterPage.FIELDS)


@pytest.mark.parametrize(("low", "high"), [("1.00", "100.00"), ("0.01", "0.05"), ("250.00", "250.00"), ("100.00", "500.00")])
def test_amounts_stay_inside_the_range_with_two_decimals(low, high):
    factory = DataFactory(seed=4)
    for _ in range(200):
        amount = factory.amount(low, high)
        assert re.fullmatch(r"\d+\.\d{2}", amount) and Decimal(low) <= Decimal(amount) <= Decimal(high)


def test_amounts_repeat_for_a_seed():
    assert [DataFactory(seed=5).amount() for _ in range(3)] == [DataFactory(seed=5).amount() for _ in range(3)]


class _Repeating:
    """A source that returns the same identity every time, like a model stuck in a rut."""

    name = "repeating"

    def identities(self, n):
        return [Identity(first_name="Ann", last_name="Lee", street="1 Main Street", city="Reno", state="NV", zip_code="89501",
                         phone="7755550100", ssn="123-45-6789")] * n


def test_a_source_that_repeats_itself_cannot_make_usernames_collide():
    customers = DataFactory(seed=6, source=_Repeating()).customers(50)
    assert len({c.username for c in customers}) == 50 and len({c.first_name for c in customers}) == 1
