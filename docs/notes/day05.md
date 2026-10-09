# Day 05
- Ollama installed with Homebrew; run `ollama serve` (or `brew services start ollama`). Models: `llama3.1:8b` (4.9 GB, Q4_K_M) and `nomic-embed-text` (274 MB, 768-dim embeddings). Machine: 24 GB RAM, plenty for 8B.
- **Temperature:** 0 gave the identical sentence twice (near-deterministic, good for tests and evals); 1.0 gave different wording and structure each run. Use low temperature when asserting, higher only to explore variety.
- **System prompt:** sets role and style ("concise QA engineer") and is sent as a separate `system` message; the user prompt carries the task. Small models follow it loosely, so keep it short and specific.
- **Context window:** llama3.1 supports 131072 tokens, but Ollama runs with a much smaller default `num_ctx` to save memory, and silently truncates long prompts. `LLMClient.generate(num_ctx=...)` lets us raise it; watch for this when feeding DOM snapshots on Day 9.
- First call took 5.4s (model load), later calls 0.4-0.8s. Ignore the first call when measuring latency.
- `framework/llm_client.py`: `LLMClient` protocol + `OllamaClient` + `get_client()` (switch with `LLM_PROVIDER`). Unit tests use a fake client so CI doesn't need Ollama.
- `scripts/` run as modules: `uv run python -m scripts.llm_hello`, since `framework` is not an installed package.
