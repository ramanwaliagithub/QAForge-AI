"""Fixtures for tests that call the real service with the real local model (marked `eval`, opt-in: `uv run pytest -m eval`)."""
import pytest
from fastapi.testclient import TestClient

from framework.llm_client import get_client
from rag_app.service import create_app


@pytest.fixture(scope="session")
def ask():
    """`ask(question)` -> the HTTP response of the real service backed by the local model; skips when the model server is not reachable."""
    client = get_client()
    try:
        client.embed("ping")
    except Exception as error:  # no Ollama: these tests cannot say anything about the service
        pytest.skip(f"local model not reachable: {error}")
    http = TestClient(create_app(client))
    return lambda question: http.post("/ask", json={"question": question})
