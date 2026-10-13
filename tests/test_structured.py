import json

import pytest

from ai_testgen.scenarios import Story
from ai_testgen.structured import GenerationError, generate_testcases
from framework.llm_client import LLMResponse

CASE = {"title": "Valid transfer", "steps": ["do"], "expected": "done"}
VALID = json.dumps({"test_cases": [CASE]})
STORY = Story("s", "a story", "some criteria")


class ScriptedClient:
    """Returns canned responses in order and records the prompts it was given."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.prompts = []
        self.kwargs = []

    def generate(self, prompt, **kw):
        self.prompts.append(prompt)
        self.kwargs.append(kw)
        return LLMResponse(self.responses.pop(0), "fake", 0.0)


def test_valid_first_try_makes_one_call_in_json_mode():
    client = ScriptedClient(VALID)
    cases = generate_testcases(client, STORY)
    assert len(cases) == 1 and len(client.prompts) == 1
    assert client.kwargs[0]["json_mode"] is True


def test_retries_after_invalid_json_and_feeds_error_back():
    client = ScriptedClient("sorry, here are tests: ...", VALID)
    cases = generate_testcases(client, STORY)
    assert len(cases) == 1 and len(client.prompts) == 2
    assert "rejected" in client.prompts[1] and "No JSON" in client.prompts[1]
    assert "rejected" not in client.prompts[0]


def test_retries_after_schema_violation():
    bad = json.dumps({"test_cases": [{"title": "No steps", "steps": [], "expected": "x"}]})
    client = ScriptedClient(bad, VALID)
    assert len(generate_testcases(client, STORY)) == 1
    assert "steps" in client.prompts[1]


def test_gives_up_after_max_retries():
    client = ScriptedClient("bad", "bad", "bad")
    with pytest.raises(GenerationError):
        generate_testcases(client, STORY, max_retries=2)
    assert len(client.prompts) == 3


def test_zero_retries_means_single_attempt():
    client = ScriptedClient("bad")
    with pytest.raises(GenerationError):
        generate_testcases(client, STORY, max_retries=0)
    assert len(client.prompts) == 1
