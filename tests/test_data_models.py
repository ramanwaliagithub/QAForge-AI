"""The data rules (framework/data/models.py) and the Faker baseline: bad data is refused, good data passes, a seed reproduces."""
import pytest
from pydantic import ValidationError

from framework.data import FakerSource, Identity

GOOD = dict(first_name="Maria", last_name="O'Neil-Garcia", street="12 Oak Street", city="Santa Fe", state="NM", zip_code="87501",
            phone="5055550123", ssn="123-45-6789")


def test_a_valid_identity_is_accepted_and_untouched():
    assert Identity(**GOOD).model_dump() == GOOD


@pytest.mark.parametrize(("field", "bad"), [
    ("first_name", ""), ("first_name", "R2D2"), ("first_name", "Siobhán"), ("city", "San José"), ("first_name", "x" * 31), ("last_name", "Smith<script>"),
    ("street", "Oak"), ("street", "12345"), ("street", "Oak Street"),
    ("city", "1ville"), ("state", "ca"), ("state", "California"), ("zip_code", "9021"), ("zip_code", "902101"), ("zip_code", "9021a"),
    ("phone", "1055550123"), ("phone", "555-0123"), ("phone", "505555012"),
    ("ssn", "123456789"), ("ssn", "000-12-3456"), ("ssn", "666-12-3456"), ("ssn", "912-12-3456"), ("ssn", "123-00-4567"), ("ssn", "123-45-0000"),
])
def test_each_rule_refuses_what_it_names(field, bad):
    with pytest.raises(ValidationError, match=field):
        Identity(**{**GOOD, field: bad})


def test_padding_and_double_spaces_from_a_model_are_tidied_not_refused():
    assert Identity(**{**GOOD, "first_name": "  Mary   Ann ", "city": "Santa  Fe"}).first_name == "Mary Ann"


def test_unknown_fields_are_refused_so_a_model_cannot_smuggle_extras():
    with pytest.raises(ValidationError, match="extra_forbidden"):
        Identity(**GOOD, nickname="Mo")


def test_faker_gives_the_same_people_for_the_same_seed_and_different_people_for_another():
    assert FakerSource(7).identities(50) == FakerSource(7).identities(50)
    assert FakerSource(7).identities(50) != FakerSource(8).identities(50)


def test_faker_output_is_valid_and_has_no_repeated_names():
    people = FakerSource(3).identities(400)
    assert len(people) == 400 and len({(p.first_name, p.last_name) for p in people}) == 400
