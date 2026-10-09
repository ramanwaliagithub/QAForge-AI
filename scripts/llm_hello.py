"""Smoke-check the local model and compare temperatures: `uv run python scripts/llm_hello.py`."""
from dotenv import load_dotenv

from framework.llm_client import get_client

load_dotenv()

client = get_client()
system = "You are a concise QA engineer."
prompt = "Name one negative test for a bank login form, in one sentence."

for temp in (0.0, 1.0):
    for i in range(2):
        r = client.generate(prompt, system=system, temperature=temp)
        print(f"[T={temp} run{i + 1}] {r.text.strip()}  ({r.latency_s:.1f}s, {r.completion_tokens} tok)")

print("embedding dims:", len(client.embed("login form")))
