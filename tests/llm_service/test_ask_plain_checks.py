"""The five checks anyone would write first for /ask: status, schema, latency, a non-empty answer, bad input refused.

They all pass. `docs/notes/day25.md` and reports/day25/ show why that is not the same as the service being right.
"""
import pytest

from rag_app.knowledge_base import load_passages
from rag_app.service import AskResponse

pytestmark = pytest.mark.eval
QUESTION = "How much do I need to deposit to open a savings account?"
LATENCY_BUDGET_MS = 20_000


def test_a_valid_question_gets_status_200(ask):
    assert ask(QUESTION).status_code == 200


def test_the_response_matches_the_schema_and_cites_known_passages(ask):
    body = AskResponse(**ask(QUESTION).json())
    assert body.sources and set(body.sources) <= {p.id for p in load_passages()}


def test_the_answer_arrives_within_the_latency_budget(ask):
    assert ask(QUESTION).json()["latency_ms"] < LATENCY_BUDGET_MS


def test_the_answer_is_not_empty_and_not_absurdly_long(ask):
    answer = ask(QUESTION).json()["answer"]
    assert 1 <= len(answer) <= 600


def test_an_empty_question_is_refused(ask):
    assert ask("").status_code == 422
