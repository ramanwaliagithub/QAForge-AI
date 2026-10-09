"""Swappable LLM client. Tests and tooling depend on `LLMClient`, not on a vendor SDK."""
import os
import time
from dataclasses import dataclass
from typing import Protocol

from framework.logging_utils import get_logger

log = get_logger("qaforge.llm")


@dataclass
class LLMResponse:
    text: str
    model: str
    latency_s: float
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class LLMClient(Protocol):
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

            client = ollama.Client(host=host or os.getenv("OLLAMA_HOST", "http://localhost:11434"))
        self._client = client

    def generate(self, prompt, *, system=None, temperature=0.0, json_mode=False, num_ctx=None) -> LLMResponse:
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


def get_client() -> LLMClient:
    """Factory: pick the backend from LLM_PROVIDER (only `ollama` for now)."""
    provider = os.getenv("LLM_PROVIDER", "ollama")
    if provider == "ollama":
        return OllamaClient()
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
