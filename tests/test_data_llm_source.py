"""The model-backed and file-backed sources, with a scripted client (no model is called): bad output is dropped, counted and fed back."""
import json

import pytest

from framework.data import DataFactory, DataGenerationError, FakerSource, FrozenSource, LLMSource, save_identities
from framework.llm_client import LLMResponse

GOOD = dict(first_name="Maria", last_name="Lopez", street="12 Oak Street", city="Santa Fe", state="NM", zip_code="87501",
            phone="5055550123", ssn="123-45-6789")


class Scripted:
    """Returns the given answers in order and remembers every prompt."""

    def __init__(self, *answers):
        self.answers, self.prompts = list(answers), []

    def generate(self, prompt, *, system=None, temperature=0.0, json_mode=False, num_ctx=None):
        self.prompts.append(prompt)
        answer = self.answers.pop(0)
        return LLMResponse(text=answer if isinstance(answer, str) else json.dumps(answer), model="scripted", latency_s=0.5)

    def embed(self, text):
        return [0.0]


def _letters(i):  # distinct, letters-only names
    return "".join(chr(ord("a") + int(d)) for d in str(i)).capitalize()


def _people(count, start=0, **changes):
    return [{**GOOD, "first_name": _letters(start + i) + "ann", "last_name": _letters(start + i) + "son", **changes} for i in range(count)]


def test_valid_answers_are_returned_as_identities():
    got = LLMSource(Scripted({"identities": _people(3)})).identities(3)
    assert [p.first_name for p in got] == ["Aann", "Bann", "Cann"]


def test_a_bare_list_or_another_key_name_is_accepted():
    assert len(LLMSource(Scripted(_people(2))).identities(2)) == 2
    assert len(LLMSource(Scripted({"customers": _people(2)})).identities(2)) == 2


def test_bad_items_are_dropped_counted_and_the_shortfall_is_asked_for_again_with_the_reasons():
    client = Scripted({"identities": [*_people(2, 0), *_people(2, 5, phone="505-555-0123")]}, {"identities": _people(2, 10)})
    source = LLMSource(client)
    assert len(source.identities(4)) == 4
    assert source.stats.calls == 2 and source.stats.rejected == {"phone": 2}
    assert "phone" in client.prompts[1] and "505-555-0123" in client.prompts[1]  # the second prompt names what was wrong
    assert "Invent 4 different" in client.prompts[1]  # shortfall of 2, plus a margin of 2


def test_duplicate_names_are_dropped_and_counted():
    source = LLMSource(Scripted({"identities": _people(2) + _people(2)}, {"identities": _people(2, 4)}))
    assert len(source.identities(4)) == 4 and source.stats.duplicates == 2


def test_not_json_and_non_objects_do_not_crash_and_are_retried():
    client = Scripted("Sure! Here are your customers:", {"identities": ["nope", 7]}, {"identities": _people(2)})
    assert len(LLMSource(client).identities(2)) == 2
    assert "not valid JSON" in client.prompts[1] and "not an object" in client.prompts[2]


def test_it_gives_up_with_an_error_that_says_how_far_it_got():
    source = LLMSource(Scripted(*[{"identities": _people(1, 0, state="Ohio")}] * 3), max_attempts=3)
    with pytest.raises(DataGenerationError, match=r"only 0 of 2 valid identities after 3 attempts"):
        source.identities(2)
    assert source.stats.rejected["state"] == 3


def test_model_data_goes_through_the_factory_with_credentials_the_model_cannot_touch():
    customers = DataFactory(seed=9, source=LLMSource(Scripted({"identities": _people(30)}))).customers(30)
    assert len({c.username for c in customers}) == 30 and all(c.username.startswith("qaforge_") for c in customers)


def test_a_frozen_file_round_trips_and_repeats(tmp_path):
    path = tmp_path / "ids.json"
    people = FakerSource(1).identities(10)
    save_identities(path, people)
    assert FrozenSource(path).identities(10) == people and FrozenSource(path).identities(3) == people[:3]
    assert path.read_text().endswith("\n")


def test_asking_a_frozen_file_for_more_than_it_holds_is_an_error_not_a_repeat(tmp_path):
    path = tmp_path / "ids.json"
    save_identities(path, FakerSource(1).identities(2))
    with pytest.raises(ValueError, match="holds 2 identities, 3 asked for"):
        FrozenSource(path).identities(3)


def test_a_frozen_file_that_breaks_the_rules_is_refused_on_load(tmp_path):
    path = tmp_path / "ids.json"
    path.write_text(json.dumps([{**GOOD, "zip_code": "9021"}]))
    with pytest.raises(ValueError, match="zip_code"):
        FrozenSource(path)
