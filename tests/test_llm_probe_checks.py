"""The crude checks and the injected defects used on the sample service: a wrong check would make the Day 25 numbers wrong (one was, see docs/notes/day25.md)."""
import hashlib
from types import SimpleNamespace

import pytest

from framework.llm_client import ScriptedClient
from rag_app.knowledge_base import KnowledgeBase, load_passages
from rag_app.service import NO_ANSWER
from scripts.llm_service_mutants import MUTANTS, MislabelledKB, ReversedKB, build, stale_passages
from scripts.probe_llm_service import QUESTIONS, cited, correct, plain_checks


class WordEmbed(ScriptedClient):
    """Word counts in 128 buckets as embeddings, so retrieval is deterministic without a model."""

    def embed(self, text):
        vector = [0.0] * 128
        for word in text.lower().replace(".", " ").replace("?", " ").split():
            vector[int(hashlib.md5(word.encode()).hexdigest(), 16) % 128] += 1.0
        return vector


def _response(status=200, **body):
    full = {"answer": "ok", "sources": ["open-account"], "model": "m", "latency_ms": 5, **body}
    return SimpleNamespace(status_code=status, json=lambda: full)


KNOWN = {p.id for p in load_passages()}


def test_a_refusal_is_not_accepted_as_an_answer_to_an_answerable_question():
    """The first version of the username check matched \"n't\" and so accepted \"I don't know\" as a correct 'no'."""
    must = next(m for qid, _, _, m, _ in QUESTIONS if qid == "change_username")
    assert not correct(must, NO_ANSWER)
    assert correct(must, "No, your username cannot be changed there.") and correct(must, "You can't change it.")


def test_every_required_pattern_must_match_and_the_refusal_must_be_exact():
    assert correct([r"payee", r"amount"], "Enter the payee and the amount.") and not correct([r"payee", r"amount"], "Enter the payee.")
    assert correct(None, f"  {NO_ANSWER}  ") and not correct(None, "I don't know, sorry.")


def test_citation_check_needs_one_of_the_passages_that_hold_the_answer():
    assert cited({"open-account"}, _response(sources=["x", "open-account"])) and not cited({"open-account"}, _response(sources=["x", "y"]))
    assert cited(set(), _response(sources=[]))


@pytest.mark.parametrize("response", [_response(status=503), _response(sources=[]), _response(sources=["made-up"]), _response(latency_ms=25_000),
                                      _response(answer=""), _response(answer="x" * 601)])
def test_each_plain_check_can_fail(response):
    assert not plain_checks(response, KNOWN)


def test_a_good_response_passes_the_plain_checks():
    assert plain_checks(_response(), KNOWN)


def test_every_question_is_answerable_with_a_source_or_a_refusal_never_both():
    for qid, kind, _, must, sources in QUESTIONS:
        assert (must is None) == (not sources) == (kind != "answerable"), qid
    assert len({q[0] for q in QUESTIONS}) == len(QUESTIONS)


def test_the_expected_source_ids_exist_in_the_knowledge_base():
    wanted = set().union(*(sources for *_, sources in QUESTIONS))
    assert wanted <= KNOWN


def test_reversed_retrieval_returns_the_least_relevant_passages():
    best = KnowledgeBase(WordEmbed()).search("How do I log out of my session?", 1)[0][0].id
    worst = ReversedKB(WordEmbed()).search("How do I log out of my session?", 3)
    assert best == "log-out" and "log-out" not in [p.id for p, _ in worst] and len(worst) == 3


def test_mislabelled_retrieval_keeps_the_text_and_moves_the_id():
    right = KnowledgeBase(WordEmbed()).search("How do I log out of my session?", 1)[0][0]
    wrong = MislabelledKB(WordEmbed()).search("How do I log out of my session?", 1)[0][0]
    assert wrong.text == right.text and wrong.id != right.id and wrong.id in KNOWN


def test_the_stale_fact_changes_one_passage_only():
    old = {p.id: p.text for p in load_passages()}
    new = {p.id: p.text for p in stale_passages()}
    assert [i for i in old if old[i] != new[i]] == ["open-account"] and "$50.00" in new["open-account"] and "$100.00" not in new["open-account"]


def test_every_listed_mutant_can_be_built_and_an_unknown_one_is_refused():
    for name in MUTANTS:
        assert build(name, WordEmbed()) is not None
    with pytest.raises(ValueError, match="unknown mutant"):
        build("no_such_mutant", WordEmbed())
