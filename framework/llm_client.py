"""Swappable LLM client. Tests and tooling depend on `LLMClient`, not on a vendor SDK."""
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from framework.logging_utils import get_logger

log = get_logger("qaforge.llm")


@dataclass
class LLMResponse:
    """A model answer with its latency and, when the provider reports them, token counts."""

    text: str
    model: str
    latency_s: float
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class LLMClient(Protocol):
    """What the rest of the code needs from a model: `generate` and `embed`. Implemented by OllamaClient and ReplayClient."""

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.0,
        json_mode: bool = False,
        num_ctx: int | None = None,
    ) -> LLMResponse: ...

    def embed(self, text: str) -> list[float]: ...


class OllamaClient:
    """Local models via Ollama. Defaults come from env (see .env.example)."""

    def __init__(self, model: str | None = None, embed_model: str | None = None, host: str | None = None, client=None):
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        self.embed_model = embed_model or os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        if client is None:
            import ollama

            # a timeout so a hung model cannot hang a test run (healing calls the model from inside tests)
            client = ollama.Client(host=host or os.getenv("OLLAMA_HOST", "http://localhost:11434"),
                                   timeout=float(os.getenv("OLLAMA_TIMEOUT_S", "120")))
        self._client = client

    def generate(self, prompt, *, system=None, temperature=0.0, json_mode=False, num_ctx=None) -> LLMResponse:
        """One chat turn with the local Ollama model (`json_mode` asks for JSON). Raises if the server is down or times out."""
        messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        options = {"temperature": temperature}
        if num_ctx:
            options["num_ctx"] = num_ctx
        start = time.perf_counter()
        resp = self._client.chat(
            model=self.model, messages=messages, options=options, format="json" if json_mode else None
        )
        latency = time.perf_counter() - start
        log.info("llm_call", extra={"model": self.model, "temperature": temperature, "latency_s": round(latency, 2)})
        return LLMResponse(
            text=resp["message"]["content"],
            model=self.model,
            latency_s=latency,
            prompt_tokens=resp.get("prompt_eval_count"),
            completion_tokens=resp.get("eval_count"),
        )

    def embed(self, text: str) -> list[float]:
        return list(self._client.embeddings(model=self.embed_model, prompt=text)["embedding"])


class ReplayClient:
    """Deterministic stand-in for a model: replays canned answers from a JSON file (a list of strings).

    For tests and CI where the model must not be called. Answers are returned in order; running out is an error,
    so a test notices when the code under test makes more calls than expected.
    """

    def __init__(self, path: str | None = None):
        self.path = path or os.environ["LLM_REPLAY_FILE"]
        self.replies: list[str] = json.loads(Path(self.path).read_text())
        self.calls = 0

    def generate(self, prompt, *, system=None, temperature=0.0, json_mode=False, num_ctx=None) -> LLMResponse:
        if self.calls >= len(self.replies):
            raise RuntimeError(f"ReplayClient exhausted after {self.calls} calls ({self.path})")
        text = self.replies[self.calls]
        self.calls += 1
        return LLMResponse(text=text if isinstance(text, str) else json.dumps(text), model="replay", latency_s=0.0)

    def embed(self, text: str) -> list[float]:
        return [0.0]


def get_client() -> LLMClient:
    """Factory: pick the backend from LLM_PROVIDER: `ollama` (default) or `replay` (canned answers, for tests)."""
    provider = os.getenv("LLM_PROVIDER", "ollama")
    if provider == "ollama":
        return OllamaClient()
    if provider == "replay":
        return ReplayClient()
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
