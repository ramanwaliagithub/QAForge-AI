"""Draft a bug report from a saved test failure, and check the draft against the evidence it was given.

A model is good at turning a stack of Playwright log into steps, expected and actual. It is also happy to invent a message the page never
showed (9 of 14 failing generated tests in Phase 2 asserted such text), so every quote in a draft is checked against the failure itself
and a draft with an unfounded quote is sent back once with the quote named. A text model cannot see the screenshot; it is given the page's
accessibility text instead, and the report says so.
"""
import ast
import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, field_validator

from framework.healing.collector import FailureContext
from framework.llm_client import LLMClient
from framework.logging_utils import get_logger

log = get_logger("qaforge.bugreport")

CLASSES = ("app_bug", "test_bug", "ui_change", "environment", "unclear")
MAX_PAGE_TEXT = 1200
MAX_SOURCE = 1800

PROMPT = """You are a QA engineer triaging one failed automated UI test of the ParaBank banking website. Write ONE bug report from the facts below.
Use only these facts. Do not invent page text, messages, numbers or steps that are not in them. If the facts do not show what the page did, say so in `actual`.

{brief}

Decide `classification` from the facts:
  app_bug      the page behaved wrongly for a user (a check that should refuse did not, a wrong value is shown)
  test_bug     the test expects something the page never promised (invented text, a wrong locator, a missing fixture)
  ui_change    the element the test looks for was renamed or moved
  environment  the app or browser was unavailable or slow
  unclear      the facts do not decide it
Return JSON only, with exactly these keys:
{{"title": "short, specific, no test name", "classification": "<one of the five>", "severity": "critical|major|minor|trivial",
  "summary": "two sentences at most", "steps_to_reproduce": ["numbered user steps, taken from the test"], "expected": "what should happen",
  "actual": "what happened, from the error", "evidence": ["exact short quotes copied from the facts above"], "suspected_cause": "one sentence, or empty",
  "next_action": "one sentence: who should do what"}}{feedback}"""


class BugReport(BaseModel):
    """A drafted bug report. `evidence` quotes must be copied from the failure; `classification` is the model's triage call."""

    title: str = Field(min_length=8, max_length=140)
    classification: Literal["app_bug", "test_bug", "ui_change", "environment", "unclear"]
    severity: Literal["critical", "major", "minor", "trivial"] = "minor"
    summary: str = Field(min_length=1)
    steps_to_reproduce: list[str] = Field(min_length=1)
    expected: str = Field(min_length=1)
    actual: str = Field(min_length=1)
    evidence: list[str] = Field(default_factory=list)
    suspected_cause: str = ""
    next_action: str = Field(min_length=1)

    @field_validator("classification", "severity", mode="before")
    @classmethod
    def _lowercase(cls, value: object) -> object:
        return value.strip().lower().replace(" ", "_") if isinstance(value, str) else value


class DraftError(RuntimeError):
    """The model never produced a valid, grounded draft within the allowed attempts."""


def visible_text(aria_snapshot: str, limit: int = MAX_PAGE_TEXT) -> str:
    """The words a user would read, taken from an accessibility snapshot: quoted names and `text:` lines, in page order, without repeats."""
    seen: dict[str, None] = {}
    for line in aria_snapshot.splitlines():
        for match in re.finditer(r'"([^"]+)"|text: (.+)$', line):
            seen.setdefault((match.group(1) or match.group(2)).strip(), None)
    text = " | ".join(seen)
    return text[:limit] + (" ..." if len(text) > limit else "")


def read_test_source(test_id: str, root: Path = Path(".")) -> str:
    """The source of the test function named by a pytest id (`path::name`), or a note that it is not available any more."""
    path, _, name = test_id.partition("::")
    file = root / path
    if not file.is_file():
        return "(test source not available)"
    source = file.read_text()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            code = ast.get_source_segment(source, node) or ""
            return code[:MAX_SOURCE] + ("\n# ... cut" if len(code) > MAX_SOURCE else "")
    return "(test source not available)"


def build_brief(ctx: FailureContext, source: str) -> str:
    """The facts a draft may use, as plain text: the failing test, the error, what the page showed, and the test code."""
    error = ctx.error
    return "\n".join([
        f"TEST: {ctx.test_id}",
        f"ERROR TYPE: {error.type.rsplit('.', 1)[-1]}",
        f"ERROR MESSAGE:\n{error.message}",
        f"LOCATOR WAITED FOR: {error.locator or 'n/a'}",
        f"ACTION: {error.action or 'n/a'}",
        f"PAGE: {ctx.page.title} ({ctx.page.url})",
        f"TEXT THE PAGE SHOWED (from its accessibility snapshot; the screenshot is not visible to you): {visible_text(ctx.page.aria_snapshot)}",
        f"TEST CODE:\n{source}",
    ])


def ungrounded(report: BugReport, brief: str) -> list[str]:
    """Evidence quotes that do not occur in the brief, ignoring case and runs of whitespace: the invented ones."""
    norm = " ".join(brief.lower().split())
    return [quote for quote in report.evidence if " ".join(quote.lower().split()) not in norm]


def draft_bug_report(client: LLMClient, ctx: FailureContext, source: str, temperature: float = 0.0, max_attempts: int = 3) -> tuple[BugReport, dict]:
    """Draft a report for one failure. Returns the report and `{"attempts": n, "dropped_quotes": [...]}`.

    Invalid JSON or an invalid report is retried with the problem named. A quote that is not in the failure is retried too; if it is still
    there on the last attempt it is dropped from the evidence and listed, never silently kept.
    """
    brief = build_brief(ctx, source)
    feedback = ""
    report = None
    for attempt in range(1, max_attempts + 1):
        response = client.generate(PROMPT.format(brief=brief, feedback=feedback), temperature=temperature, json_mode=True)
        try:
            report = BugReport(**json.loads(response.text))
        except (json.JSONDecodeError, ValidationError, TypeError) as error:
            feedback = f"\n\nYour previous answer was rejected: {str(error)[:300]}\nReturn corrected JSON only."
            log.warning("bug_draft_invalid", extra={"attempt": attempt, "error": str(error)[:200]})
            report = None
            continue
        invented = ungrounded(report, brief)
        if not invented:
            return report, {"attempts": attempt, "dropped_quotes": []}
        feedback = f"\n\nThese evidence quotes are not in the facts, remove or replace them: {invented}"
        log.warning("bug_draft_ungrounded", extra={"attempt": attempt, "quotes": invented})
    if report is None:
        raise DraftError(f"no valid bug report after {max_attempts} attempts for {ctx.test_id}")
    dropped = ungrounded(report, brief)
    report.evidence = [quote for quote in report.evidence if quote not in dropped]
    return report, {"attempts": max_attempts, "dropped_quotes": dropped}
