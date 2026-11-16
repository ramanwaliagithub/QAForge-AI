"""Identities written by a language model, held to the same rules as any other source.

A model is good at what a generator is bad at: names, streets and cities that look like a real mix of people. It is bad at what a rule
needs: it writes a 4-digit zip, a state spelled out, a phone number with a 1 in front. So nothing a model returns reaches a test unchecked:
every item is validated one by one, bad items are dropped (and counted), and the model is asked again for the shortfall with the reasons.
"""
import json
from collections import Counter
from dataclasses import dataclass, field

from pydantic import ValidationError

from framework.data.models import Identity
from framework.llm_client import LLMClient
from framework.logging_utils import get_logger

log = get_logger("qaforge.data")

PROMPT = """Invent {n} different, realistic United States customers for testing a banking website.
Return JSON only: {{"identities": [ ... ]}} where every item has exactly these string fields:
  first_name, last_name  letters only (a space, hyphen or apostrophe inside is fine), at most 30 characters
  street                 a street address with a number, 5 to 50 characters, for example "418 Maple Avenue"
  city                   a real US city, letters only
  state                  the two-letter capital abbreviation, for example "OH"
  zip_code               exactly 5 digits
  phone                  exactly 10 digits, no punctuation, the first digit 2 to 9
  ssn                    the form 123-45-6789, a made-up number that does not start with 000, 666 or 9, with group 00 or serial 0000 never used
Make the people differ from each other: mix origins, include some hyphenated or apostrophe names, different states. No field may be empty.{feedback}"""


class DataGenerationError(RuntimeError):
    """The model could not produce enough valid identities within the allowed attempts."""


@dataclass
class LLMStats:
    """What a generation cost and what the rules threw away: the numbers behind 'is the model worth it here'."""

    calls: int = 0
    seconds: float = 0.0
    items_returned: int = 0
    rejected: Counter = field(default_factory=Counter)  # first words of each rule failure -> how often
    duplicates: int = 0


class LLMSource:
    """Identity source backed by a model. Not reproducible: the same prompt gives different people; freeze a result to reuse it."""

    name = "llm"

    def __init__(self, client: LLMClient, temperature: float = 0.7, max_attempts: int = 4):
        self.client = client
        self.temperature = temperature
        self.max_attempts = max_attempts
        self.stats = LLMStats()

    def identities(self, n: int) -> list[Identity]:
        """Exactly `n` valid, distinct identities, or DataGenerationError. Each retry asks only for the shortfall and names what was wrong."""
        made: list[Identity] = []
        seen: set[tuple[str, str]] = set()
        feedback = ""
        for attempt in range(1, self.max_attempts + 1):
            wanted = n - len(made)
            response = self.client.generate(PROMPT.format(n=wanted + 2, feedback=feedback), temperature=self.temperature, json_mode=True)
            self.stats.calls += 1
            self.stats.seconds += response.latency_s
            problems: list[str] = []
            for item in self._items(response.text, problems):
                self.stats.items_returned += 1
                try:
                    identity = Identity(**item) if isinstance(item, dict) else None
                except (ValidationError, TypeError) as error:
                    reason = self._reason(error)
                    self.stats.rejected[reason.split(":")[0]] += 1
                    problems.append(reason)
                    continue
                if identity is None:
                    problems.append(f"item {item!r} is not an object")
                    continue
                key = (identity.first_name.lower(), identity.last_name.lower())
                if key in seen:
                    self.stats.duplicates += 1
                    continue
                seen.add(key)
                made.append(identity)
                if len(made) == n:
                    return made
            log.warning("llm_data_shortfall", extra={"attempt": attempt, "have": len(made), "want": n, "problems": problems[:3]})
            feedback = "\n\nYour previous answer had these problems, avoid them: " + "; ".join(dict.fromkeys(problems))[:600] if problems else ""
        raise DataGenerationError(f"only {len(made)} of {n} valid identities after {self.max_attempts} attempts")

    @staticmethod
    def _items(text: str, problems: list[str]) -> list:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as error:
            problems.append(f"the answer was not valid JSON ({error.msg})")
            return []
        if isinstance(data, dict):  # {"identities": [...]}, or whatever single list the model chose to name
            data = data.get("identities") or next((v for v in data.values() if isinstance(v, list)), [])
        if not isinstance(data, list):
            problems.append("the answer was not a list of identities")
            return []
        return data

    @staticmethod
    def _reason(error: Exception) -> str:
        if isinstance(error, ValidationError):
            first = error.errors()[0]
            return f"{'.'.join(str(p) for p in first['loc'])}: {first['msg']} (got {first.get('input')!r})"
        return f"unusable item: {error}"
