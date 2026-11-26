"""Entry point: `uv run uvicorn rag_app.main:app --port 8001` serves the assistant with the local Ollama model."""
from framework.llm_client import get_client
from rag_app.service import create_app

app = create_app(get_client())
