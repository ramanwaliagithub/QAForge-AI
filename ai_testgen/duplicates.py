"""Find a bug report that is probably a duplicate of an earlier one, by comparing embeddings of what the reports say.

Two signals, because they fail differently (docs/notes/day23.md). A *fingerprint* (failure kind, locator, shape of the message) says "the same failure":
exact, cheap, and blind to anything phrased differently. An *embedding* of the draft's title, expected and actual says "similar": it ranks well
(AUC 0.93) but no threshold separates duplicates from look-alikes cleanly, so its match is only a pointer for a person. Nothing is merged or closed.
"""
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from ai_testgen.bug_report import BugReport
from framework.healing.collector import FailureContext
from framework.llm_client import LLMClient
from framework.similarity import cosine

SIMILAR_THRESHOLD = 0.75  # fitted on 11 failures: precision 0.75, recall 0.5. The first guess of 0.85 found none of the 6 duplicate pairs


@dataclass
class Match:
    """The earlier report a new one most resembles, and how much."""

    id: str
    similarity: float
    kind: str = "similar"  # "same_failure" (equal fingerprints, similarity 1.0) or "similar" (embedding at or above the threshold)


def embedding_text(report: BugReport) -> str:
    """What is embedded for a report: the three fields that say what is wrong."""
    return f"{report.title}. Expected: {report.expected} Actual: {report.actual}"


def fingerprint(ctx: FailureContext) -> str:
    """What a failure is, apart from which test hit it: its kind, the locator it was waiting for, and the shape of the first line of its message.

    Numbers (timeouts, account ids) and URLs are blanked, so the same failure on another run or another test gives the same text.
    """
    first = next((line for line in ctx.error.message.splitlines() if line.strip()), "")
    shape = re.sub(r"https?://\S+", "<url>", first.lower())
    shape = re.sub(r"\d+", "#", shape)[:90]
    return f"{ctx.error.kind}|{ctx.error.locator or ''}|{shape}"


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

    def check_and_add(self, client: LLMClient, report_id: str, report: BugReport, threshold: float = SIMILAR_THRESHOLD,
                      failure_fingerprint: str | None = None) -> Match | None:
        """Embed the report and return the earlier report it repeats or resembles, or None; store it either way.

        An equal fingerprint wins (kind `same_failure`); otherwise the nearest embedding at or above `threshold` (kind `similar`).
        A report with the same id replaces its old entry, so rerunning a failure does not make it a duplicate of itself.
        """
        vector = client.embed(embedding_text(report))
        others = [r for r in self.records if r["id"] != report_id]
        same = next((r for r in others if failure_fingerprint and r.get("fingerprint") == failure_fingerprint), None)
        nearest = self.nearest(vector, exclude=report_id)
        self.records = [*others, {"id": report_id, "vector": vector, "fingerprint": failure_fingerprint}]
        if same:
            return Match(same["id"], 1.0, "same_failure")
        return nearest if nearest and nearest.similarity >= threshold else None

    def save(self) -> None:
        """Write the index next to the reports (needs a path)."""
        if self.path is None:
            raise ValueError("this index has no path")
        self.path.write_text(json.dumps({"embed_model": self.embed_model, "records": self.records}) + "\n")


def as_dict(match: Match | None) -> dict | None:
    """A match as the plain dict the markdown renderer and the JSON index take."""
    return asdict(match) if match else None
