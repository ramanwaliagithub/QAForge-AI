import json

import pytest

from ai_testgen.edge_cases import (
    EdgeCaseError, classify_outcome, expects_rejection, parse_edge_cases, propose_edge_cases,
)
from framework.llm_client import LLMResponse

CASE = {"title": "Negative amount", "amount": "-5", "from_index": 0, "to_index": 1, "expected": "The transfer is rejected"}


def test_parse_edge_cases_object_list_and_chatter():
    assert parse_edge_cases(json.dumps({"edge_cases": [CASE]}))[0].amount == "-5"
    assert len(parse_edge_cases("Sure! " + json.dumps({"edge_cases": [CASE, CASE]}))) == 2


@pytest.mark.parametrize("text", ["no json", '{"edge_cases": []}', '{"edge_cases": [{"title": "x"}]}',
                                  json.dumps({"edge_cases": [{**CASE, "from_index": 5}]})])
def test_parse_edge_cases_rejects_bad_output(text):
    with pytest.raises(EdgeCaseError):
        parse_edge_cases(text)


class Scripted:
    def __init__(self, *outs):
        self.outs, self.prompts = list(outs), []

    def generate(self, prompt, **kw):
        self.prompts.append(prompt)
        return LLMResponse(self.outs.pop(0), "fake", 0.0)


def test_propose_retries_with_feedback_and_truncates_to_n():
    client = Scripted("garbage", json.dumps({"edge_cases": [CASE] * 7}))
    cases = propose_edge_cases(client, "SNAP", n=5)
    assert len(cases) == 5 and "rejected" in client.prompts[1] and "SNAP" in client.prompts[0]


@pytest.mark.parametrize("expected, rejects", [
    ("The transfer is rejected with an error message", True),
    ("The transfer should not be allowed", True),
    ("The app should show a validation error", True),
    ("The transfer is accepted and balances update", False),
    ("The transfer should be successful", False),
])
def test_expects_rejection(expected, rejects):
    assert expects_rejection(expected) is rejects


def test_classify_outcome():
    assert classify_outcome(["Transfer Complete!", "$5 has been transferred"]) == "accepted"
    assert classify_outcome(["Error!", "An internal error has occurred"]) == "rejected"
    assert classify_outcome(["Amount: $"]) == "other"
