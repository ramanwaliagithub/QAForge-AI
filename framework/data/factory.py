"""The factory tests use: realistic customers and amounts, reproducible from one seed.

Who a customer is (name, address...) comes from a pluggable source (Faker by default, a model, or a frozen file). What must be unique or exact
(username, password, money) comes from here, from a seeded generator the sources cannot influence: a model that repeats a username must
not be able to break a test run, and a boundary amount must be the amount asked for.
"""
import random
import string
from decimal import Decimal
from typing import Protocol

from framework.data.faker_source import FakerSource
from framework.data.models import Customer, Identity

PASSWORD_ALPHABET = string.ascii_letters + string.digits


class IdentitySource(Protocol):
    """Anything that can invent `n` valid identities: FakerSource, LLMSource, FrozenSource."""

    name: str

    def identities(self, n: int) -> list[Identity]: ...


class DataFactory:
    """Seeded test data. `seed=None` picks a random seed and keeps it in `.seed`: print it, and a failing run can be replayed exactly.

    Usernames are derived from the seed, so two runs with the same seed against a ParaBank that was not reset will meet "already exists";
    use a new seed, or reset the app, to register again.
    """

    def __init__(self, seed: int | None = None, source: IdentitySource | None = None):
        self.seed = random.SystemRandom().getrandbits(31) if seed is None else seed
        self._rng = random.Random(self.seed)
        self.source: IdentitySource = source or FakerSource(self.seed)

    def customers(self, n: int) -> list[Customer]:
        """`n` customers: identities from the source, credentials from the seeded generator (usernames are unique within the factory)."""
        identities = self.source.identities(n)
        return [Customer(**identity.model_dump(), username=self._username(), password=self._password()) for identity in identities]

    def customer(self) -> Customer:
        """One customer. With a model-backed source this is one model call; ask for `customers(n)` when you need several."""
        return self.customers(1)[0]

    def amount(self, low: str = "1.00", high: str = "100.00") -> str:
        """A money amount between `low` and `high` inclusive, as the text a form takes: two decimals, a dot."""
        cents = self._rng.randint(int(Decimal(low) * 100), int(Decimal(high) * 100))
        return f"{Decimal(cents) / 100:.2f}"

    def _username(self) -> str:
        return f"qaforge_{self._rng.getrandbits(40):010x}"

    def _password(self) -> str:
        # a letter, a digit and a symbol are guaranteed; the form has no rule today, but a real one would
        body = [self._rng.choice(string.ascii_lowercase), self._rng.choice(string.ascii_uppercase), self._rng.choice(string.digits), "!"]
        body += [self._rng.choice(PASSWORD_ALPHABET) for _ in range(8)]
        self._rng.shuffle(body)
        return "".join(body)
