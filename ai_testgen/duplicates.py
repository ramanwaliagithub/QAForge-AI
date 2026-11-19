"""Find a bug report that is probably a duplicate of an earlier one, by comparing embeddings of what the reports say.

The text embedded is the report's content (title, expected, actual), never the test name or the locator: two different tests can show one
bug, and two tests that fail the same way for different reasons are not duplicates. The threshold is a measured number, not a default
(docs/notes/day23.md): below it a report is new, at or above it a person is told which earlier report to look at. Nothing is merged or closed.
"""
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from ai_testgen.bug_report import BugReport
from framework.llm_client import LLMClient

THRESHOLD = 0.85


@dataclass
class Match:
    """The earlier report a new one most resembles, and how much."""

    id: str
    similarity: float


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two vectors; 0.0 when either has no length (an empty embedding resembles nothing)."""
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return sum(x * y for x, y in zip(a, b, strict=True)) / norm if norm else 0.0


def embedding_text(report: BugReport) -> str:
    """What is embedded for a report: the three fields that say what is wrong."""
    return f"{report.title}. Expected: {report.expected} Actual: {report.actual}"


class DuplicateIndex:
    """Earlier reports with their vectors, kept in a JSON file so that a later run can compare against an earlier one."""

    def __init__(self, embed_model: str, path: Path | None = None):
        self.embed_model = embed_model
        self.path = path
        self.records: list[dict] = []
        if path and path.is_file():
            data = json.loads(path.read_text())
            if data["embed_model"] != embed_model:
                raise ValueError(f"{path.name} was built with {data['embed_model']!r}, not {embed_model!r}: vectors of different models cannot be compared")
            self.records = data["records"]

    def nearest(self, vector: list[float], exclude: str | None = None) -> Match | None:
        """The most similar stored report (leaving out `exclude`, a report's own earlier entry), or None when the index is empty."""
        scored = [Match(r["id"], cosine(vector, r["vector"])) for r in self.records if r["id"] != exclude]
        return max(scored, key=lambda m: m.similarity) if scored else None

    def check_and_add(self, client: LLMClient, report_id: str, report: BugReport, threshold: float = THRESHOLD) -> Match | None:
        """Embed the report, return the earlier report it duplicates (similarity at or above `threshold`) or None, and store it either way.

        A report with the same id replaces its old entry, so rerunning a failure does not make it a duplicate of itself.
        """
        vector = client.embed(embedding_text(report))
        nearest = self.nearest(vector, exclude=report_id)
        self.records = [r for r in self.records if r["id"] != report_id] + [{"id": report_id, "vector": vector}]
        return nearest if nearest and nearest.similarity >= threshold else None

    def save(self) -> None:
        """Write the index next to the reports (needs a path)."""
        if self.path is None:
            raise ValueError("this index has no path")
        self.path.write_text(json.dumps({"embed_model": self.embed_model, "records": self.records}) + "\n")


def as_dict(match: Match | None) -> dict | None:
    """A match as the plain dict the markdown renderer and the JSON index take."""
    return asdict(match) if match else None
