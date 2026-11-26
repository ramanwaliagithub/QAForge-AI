"""The sample service with a scripted model and a crude word-count embedder: its plumbing, not the quality of any real model's answers."""
import hashlib
import json

import pytest
from fastapi.testclient import TestClient

from framework.llm_client import ScriptedClient
from rag_app.knowledge_base import KnowledgeBase, Passage, load_passages
from rag_app.service import NO_ANSWER, create_app


class WordEmbedClient(ScriptedClient):
    """A scripted model whose embeddings are word counts in 128 buckets: texts that share words land close together."""

    def embed(self, text):
        vector = [0.0] * 128
        for word in text.lower().replace(".", " ").replace("?", " ").replace(",", " ").split():
            vector[int(hashlib.md5(word.encode()).hexdigest(), 16) % 128] += 1.0
        return vector


@pytest.fixture
def client_and_app():
    client = WordEmbedClient("You need to deposit at least $100.00.")
    return client, TestClient(create_app(client))


def test_the_real_passages_load_with_unique_ids():
    passages = load_passages()
    assert len(passages) >= 8 and len({p.id for p in passages}) == len(passages)
    assert all(p.title and p.text for p in passages)


def test_duplicate_passage_ids_are_refused(tmp_path):
    path = tmp_path / "p.json"
    path.write_text(json.dumps([{"id": "a", "title": "t", "text": "x"}, {"id": "a", "title": "u", "text": "y"}]))
    with pytest.raises(ValueError, match="duplicate passage ids"):
        load_passages(path)


@pytest.mark.parametrize(("question", "expected_id"), [
    ("How much money do I need to open a savings account?", "open-account"),
    ("How do I pay a bill to a payee?", "bill-pay"),
    ("Can I search transactions by date range?", "find-transactions"),
    ("How do I log out of my session?", "log-out"),
])
def test_retrieval_puts_the_relevant_passage_first(question, expected_id):
    hits = KnowledgeBase(WordEmbedClient()).search(question, k=3)
    assert hits[0][0].id == expected_id and [s for _, s in hits] == sorted((s for _, s in hits), reverse=True)


def test_the_passages_are_embedded_once_not_per_question():
    client = WordEmbedClient()
    calls = []
    original = client.embed
    client.embed = lambda text: (calls.append(text), original(text))[1]
    kb = KnowledgeBase(client, [Passage("a", "A", "alpha"), Passage("b", "B", "beta")])
    kb.search("alpha?")
    kb.search("beta?")
    assert len(calls) == 2 + 2  # two passages once, plus one question each time


def test_ask_returns_the_answer_the_sources_the_model_and_a_latency(client_and_app):
    _, http = client_and_app
    response = http.post("/ask", json={"question": "How much do I need to open a savings account?"})
    body = response.json()
    assert response.status_code == 200 and set(body) == {"answer", "sources", "model", "latency_ms"}
    assert body["answer"] == "You need to deposit at least $100.00." and body["model"] == "scripted"
    assert body["sources"][0] == "open-account" and len(body["sources"]) == 3 and body["latency_ms"] >= 0


def test_the_prompt_shows_the_model_the_retrieved_passages_the_question_and_the_way_out(client_and_app):
    client, http = client_and_app
    http.post("/ask", json={"question": "How much do I need to open a savings account?"})
    prompt = client.prompts[0]
    assert "[open-account]" in prompt and "$100.00" in prompt and "QUESTION: How much do I need to open a savings account?" in prompt
    assert NO_ANSWER in prompt and "ONLY" in prompt


@pytest.mark.parametrize("body", [{}, {"question": ""}, {"question": "x" * 501}, {"question": 5}])
def test_bad_requests_are_refused_before_the_model_is_called(client_and_app, body):
    client, http = client_and_app
    assert http.post("/ask", json=body).status_code == 422 and client.prompts == []


def test_a_model_that_is_down_is_a_503_that_says_so():
    client = WordEmbedClient(exhausted="connection refused")  # no answers left: the first generate raises
    response = TestClient(create_app(client)).post("/ask", json={"question": "How do I log out?"})
    assert response.status_code == 503 and "connection refused" in response.json()["detail"]


def test_the_temperature_comes_from_the_environment_unless_given(monkeypatch):
    monkeypatch.setenv("ASK_TEMPERATURE", "0.2")
    client = WordEmbedClient("a", "b")
    TestClient(create_app(client)).post("/ask", json={"question": "log out?"})
    TestClient(create_app(client, temperature=0.9)).post("/ask", json={"question": "log out?"})
    assert [k["temperature"] for k in client.kwargs] == [0.2, 0.9]
