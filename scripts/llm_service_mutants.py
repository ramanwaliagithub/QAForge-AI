"""Break the sample service on purpose, seven ways, and see which of the plain checks and the crude fact check notice.

    uv run python -m scripts.llm_service_mutants [--repeats=3] [--out=reports/day25]

The seven are regressions real LLM applications suffer: retrieval that returns the worst passages, a prompt that no longer says "only", a stale fact in the
knowledge base, a very high temperature, no context at all, a model that always refuses, and citations that point at the wrong passage. The same
questions and the same checks as scripts/probe_llm_service.py are run against each. Writes <out>/mutants.json.
"""
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from framework.llm_client import LLMClient, get_client
from rag_app.knowledge_base import KnowledgeBase, Passage, load_passages
from rag_app.service import NO_ANSWER, PROMPT, create_app
from scripts.flags import parse_flags
from scripts.probe_llm_service import QUESTIONS, cited, correct, plain_checks

ROOT = Path(__file__).resolve().parent.parent


class ReversedKB(KnowledgeBase):
    """Retrieval that hands back the least relevant passages instead of the most relevant."""

    def search(self, question: str, k: int = 3) -> list[tuple[Passage, float]]:
        """The k worst-ranked passages."""
        return super().search(question, k=len(self.passages))[::-1][:k]


class MislabelledKB(KnowledgeBase):
    """Right passages, wrong ids: every citation points at the neighbouring passage."""

    def search(self, question: str, k: int = 3) -> list[tuple[Passage, float]]:
        """The right passages, each carrying the id of the next passage in the file."""
        ids = [p.id for p in self.passages]
        shifted = {p.id: ids[(i + 1) % len(ids)] for i, p in enumerate(self.passages)}
        return [(replace(p, id=shifted[p.id]), score) for p, score in super().search(question, k)]


def stale_passages() -> list[Passage]:
    """The knowledge base with one fact out of date: the minimum opening deposit is $50.00, not $100.00."""
    return [replace(p, text=p.text.replace("$100.00", "$50.00")) if p.id == "open-account" else p for p in load_passages()]


def build(name: str, client: LLMClient) -> TestClient:
    """The service with one defect injected (`baseline` has none)."""
    if name == "retrieval_reversed":
        return TestClient(create_app(client, ReversedKB(client)))
    if name == "no_grounding_instruction":
        loose = PROMPT.replace("using ONLY the passages below", "using the passages below if they help").replace(
            "If the passages do not contain the answer, reply exactly: {no_answer}\n", "")
        return TestClient(create_app(client, prompt=loose))
    if name == "stale_fact":
        return TestClient(create_app(client, KnowledgeBase(client, stale_passages())))
    if name == "high_temperature":
        return TestClient(create_app(client, temperature=1.8))
    if name == "no_context":
        return TestClient(create_app(client, prompt=PROMPT.replace("{passages}", "(no passages available)")))
    if name == "always_refuses":
        refusing = PROMPT.replace("Answer the customer's question using ONLY the passages below.", "Whatever the question, reply exactly: {no_answer}")
        return TestClient(create_app(client, prompt=refusing + "\nREMINDER: whatever the question, reply exactly: {no_answer}"))
    if name == "wrong_citations":
        return TestClient(create_app(client, MislabelledKB(client)))
    if name == "baseline":
        return TestClient(create_app(client))
    raise ValueError(f"unknown mutant {name!r}")


MUTANTS = ["baseline", "retrieval_reversed", "no_grounding_instruction", "stale_fact", "high_temperature", "no_context", "always_refuses", "wrong_citations"]


def run(name: str, client: LLMClient, repeats: int) -> dict[str, Any]:
    """Ask every probe question `repeats` times of one variant; count plain-check passes and correct answers, in total and per kind."""
    http = build(name, client)
    known = {p.id for p in load_passages()}
    per_kind: dict[str, list[int]] = {}
    plain = right = total = cite_ok = cite_total = 0
    wrong: list[str] = []
    for qid, kind, question, must, expected_sources in QUESTIONS:
        for _ in range(repeats):
            response = http.post("/ask", json={"question": question})
            answer = response.json().get("answer", "") if response.status_code == 200 else ""
            ok_plain, ok_fact = plain_checks(response, known), correct(must, answer)
            plain, right, total = plain + ok_plain, right + ok_fact, total + 1
            bucket = per_kind.setdefault(kind, [0, 0])
            bucket[0] += ok_fact
            bucket[1] += 1
            if expected_sources:
                cite_total += 1
                cite_ok += cited(expected_sources, response)
            if not ok_fact and len(wrong) < 3:
                wrong.append(f"{qid}: {answer[:110]}")
    return {"mutant": name, "calls": total, "plain_checks_passed": plain, "correct": right, "cited_the_right_passage": f"{cite_ok}/{cite_total}",
            "correct_by_kind": {k: f"{a}/{b}" for k, (a, b) in per_kind.items()}, "examples_of_wrong_answers": wrong}


def main(argv: list[str]) -> None:
    """Run every variant, print one line each and write <out>/mutants.json."""
    flags, _ = parse_flags(argv, __doc__)
    repeats = int(flags.get("repeats", 3))
    out = ROOT / flags.get("out", "reports/day25")
    client = get_client()
    rows = []
    for name in MUTANTS:
        row = run(name, client, repeats)
        rows.append(row)
        print(f"{name:26} plain {row['plain_checks_passed']}/{row['calls']}  correct {row['correct']}/{row['calls']}  cited {row['cited_the_right_passage']}  {row['correct_by_kind']}", flush=True)
    out.mkdir(parents=True, exist_ok=True)
    (out / "mutants.json").write_text(json.dumps({"repeats": repeats, "no_answer_sentence": NO_ANSWER, "rows": rows}, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
    sys.exit(0)
