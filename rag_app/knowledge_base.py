"""The help-center passages the service answers from, and finding the ones closest to a question."""
import json
from dataclasses import dataclass
from pathlib import Path

from framework.llm_client import LLMClient
from framework.similarity import cosine

PASSAGES = Path(__file__).resolve().parent / "knowledge" / "passages.json"


@dataclass(frozen=True)
class Passage:
    """One help-center passage: a stable id (what answers cite), a title and the text."""

    id: str
    title: str
    text: str


def load_passages(path: Path = PASSAGES) -> list[Passage]:
    """Read the passages file; refuses duplicate ids, because a citation must point at exactly one passage."""
    passages = [Passage(**item) for item in json.loads(path.read_text())]
    ids = [p.id for p in passages]
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate passage ids in {path.name}: {sorted({i for i in ids if ids.count(i) > 1})}")
    return passages


class KnowledgeBase:
    """Passages with their embeddings. Embedding happens on first use, so creating the service does not need the model to be up."""

    def __init__(self, client: LLMClient, passages: list[Passage] | None = None):
        self.client = client
        self.passages = passages if passages is not None else load_passages()
        self._vectors: list[list[float]] | None = None

    def search(self, question: str, k: int = 3) -> list[tuple[Passage, float]]:
        """The `k` passages closest to the question with their cosine similarity, best first."""
        if self._vectors is None:
            self._vectors = [self.client.embed(f"{p.title}. {p.text}") for p in self.passages]
        query = self.client.embed(question)
        ranked = sorted(zip(self.passages, (cosine(query, v) for v in self._vectors), strict=True), key=lambda pair: -pair[1])
        return ranked[:k]
