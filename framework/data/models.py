"""The shape of test data and the rules it must follow, whoever produced it (Faker, a model, a file).

The rules are ours, not ParaBank's: ParaBank accepts nearly any text in these fields, so a field that "works" there says little. Rules are
strict enough that a source of data cannot quietly hand a test something a real form would reject (a 4-digit zip, a long state name).
"""
import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

NAME = re.compile(r"^[^\W\d_]+(?:[ '\-][^\W\d_]+)*$")  # letters, with single spaces, apostrophes or hyphens inside
CITY = NAME
SSN = re.compile(r"^(?!000|666|9)\d{3}-(?!00)\d{2}-(?!0000)\d{4}$")  # the format the form expects, and a number the SSA never issues is refused


def _clean(value: object) -> object:
    return " ".join(value.split()) if isinstance(value, str) else value


class Identity(BaseModel):
    """Who the customer is: the eight fields a model or Faker can plausibly invent. Names the registration form's keyword arguments."""

    model_config = ConfigDict(extra="forbid")

    first_name: Annotated[str, StringConstraints(min_length=1, max_length=30)]
    last_name: Annotated[str, StringConstraints(min_length=1, max_length=30)]
    street: Annotated[str, StringConstraints(min_length=5, max_length=50)]
    city: Annotated[str, StringConstraints(min_length=2, max_length=30)]
    state: Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}$")]
    zip_code: Annotated[str, StringConstraints(pattern=r"^\d{5}$")]
    phone: Annotated[str, StringConstraints(pattern=r"^[2-9]\d{9}$")]
    ssn: str

    @field_validator("first_name", "last_name", "street", "city", "state", "zip_code", "phone", "ssn", mode="before")
    @classmethod
    def _tidy(cls, value: object) -> object:
        return _clean(value)  # a model pads and double-spaces; that is noise, not a finding

    @field_validator("first_name", "last_name", "city")
    @classmethod
    def _letters_only(cls, value: str) -> str:
        if not NAME.match(value):
            raise ValueError(f"{value!r} is not a name: letters, with single spaces, apostrophes or hyphens inside")
        return value

    @field_validator("street")
    @classmethod
    def _street_has_number_and_word(cls, value: str) -> str:
        if not (re.search(r"\d", value) and re.search(r"[^\W\d_]{2}", value)):
            raise ValueError(f"{value!r} is not a street address: needs a number and a name")
        return value

    @field_validator("ssn")
    @classmethod
    def _ssn_format(cls, value: str) -> str:
        if not SSN.match(value):
            raise ValueError(f"{value!r} is not an SSN of the form 123-45-6789 (no 000, 666 or 9xx area, no 00 group, no 0000 serial)")
        return value


class Customer(Identity):
    """An identity plus the credentials the factory owns: a username unique to this run and a password."""

    username: Annotated[str, StringConstraints(pattern=r"^[a-z0-9_]{6,30}$")]
    password: Annotated[str, StringConstraints(min_length=8, max_length=30)]

    def register_kwargs(self) -> dict[str, str]:
        """The keyword arguments `RegisterPage.register` takes."""
        return self.model_dump()
