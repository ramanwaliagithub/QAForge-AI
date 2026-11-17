"""A reviewed, committed set of identities: the way to use model-written data in tests that must repeat.

Generate once with the model, read the result, commit the file; tests then read it like any fixture. Same data every run, no model call,
no new rule failures, and a diff when somebody changes it.
"""
import json
from pathlib import Path

from framework.data.models import Identity


def save_identities(path: Path, identities: list[Identity]) -> None:
    """Write identities as a JSON list, one object per item, stable key order, ending in a newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([i.model_dump() for i in identities], indent=2, ensure_ascii=False) + "\n")


class FrozenSource:
    """Identity source that reads a file written by `save_identities`; every item is validated again on load."""

    name = "frozen"

    def __init__(self, path: Path):
        self.path = path
        self._all = [Identity(**item) for item in json.loads(path.read_text())]

    def identities(self, n: int) -> list[Identity]:
        """The first `n` identities of the file. Asking for more than the file holds is an error, not a silent repeat."""
        if n > len(self._all):
            raise ValueError(f"{self.path.name} holds {len(self._all)} identities, {n} asked for")
        return self._all[:n]
