"""The deterministic baseline: identities from Faker, seeded, so the same seed always gives the same people."""
from faker import Faker

from framework.data.models import Identity


class FakerSource:
    """Identity source backed by Faker (en_US). Same seed, same identities, in the same order."""

    name = "faker"

    def __init__(self, seed: int):
        self._fake = Faker("en_US")
        self._fake.seed_instance(seed)

    def identities(self, n: int) -> list[Identity]:
        """`n` identities. Faker's raw output is passed through the same validation as any other source, never trusted."""
        made: list[Identity] = []
        seen: set[tuple[str, str]] = set()
        while len(made) < n:
            identity = Identity(
                first_name=self._fake.first_name().replace(".", ""),
                last_name=self._fake.last_name(),
                street=self._fake.street_address()[:50],
                city=self._fake.city(),
                state=self._fake.state_abbr(include_territories=False, include_freely_associated_states=False),
                zip_code=self._fake.numerify("#####"),
                phone=self._fake.random_element("23456789") + self._fake.numerify("#########"),
                ssn=self._fake.ssn(),
            )
            key = (identity.first_name, identity.last_name)
            if key not in seen:
                seen.add(key)
                made.append(identity)
        return made
