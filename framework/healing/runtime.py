"""Opt-in self-healing at run time.

A page-object action (click, fill, select_option) that fails because its locator is wrong asks the active `Healer` for
a replacement, retries the action ONCE with it, and records everything as a `HealEvent`. Rules that make this safe:

- Off unless a healer is active (`--heal`). With no healer, failures propagate exactly as before.
- Guard rail: only failures classified as locator problems are healed. Assertions in tests never reach this code, and
  anything else (element found but not actionable, navigation timeouts, ...) is skipped.
- The suggestion is validated against the LIVE page (exactly one match, right kind of element), then verified by the
  retry succeeding. A failed retry re-raises the ORIGINAL error.
- Nothing is written to source. The only output is the event log (reports/healing.json, written by the pytest plugin).
- Bounded: one retry per action, a few heals per test, and the model's answers are cached per (page, locator, action).
"""
import contextlib
import time
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from urllib.parse import urlparse

from framework.healing.collector import FailureContext, capture_page_state
from framework.healing.definitions import find_definitions
from framework.healing.errors import analyze_exception, stack_frames
from framework.healing.suggester import suggest_locator
from framework.healing.suggestion import (
    LocatorSuggestion, build_locator, failed_role, render_locator, validate_suggestion,
)
from framework.logging_utils import get_logger

log = get_logger("qaforge.healing")


@dataclass
class HealConfig:
    max_attempts: int = 3           # LLM attempts per heal (each rejection is fed back)
    max_heals_per_test: int = 3     # stops a badly broken page from costing a model call per action
    allow_maybe: bool = False       # also try failures whose cause is ambiguous (not_actionable, preconditions)
    temperature: float = 0.0


@dataclass
class HealEvent:
    test_id: str
    time: str
    action: str
    page_url: str
    failed_locator: str | None
    kind: str
    heal_hint: str
    outcome: str = "pending"        # healed | retry_failed | no_suggestion | skipped_guard | budget_exhausted | error
    suggestion: str | None = None   # e.g. get_by_role("button", name="Transfer", exact=True)
    strategy: str | None = None
    reason: str = ""
    confidence: float | None = None
    attempts: int = 0
    from_cache: bool = False
    repaired_from: str | None = None
    rejections: list[str] = field(default_factory=list)
    element: dict | None = None
    verified: bool = False          # the retried action succeeded with the suggestion
    definitions: list[dict] = field(default_factory=list)   # where the failed locator is defined in source
    caller_frames: list[dict] = field(default_factory=list)
    error_message: str = ""
    seconds: float = 0.0
    status: str = "proposed"        # proposed | approved | rejected: for the review step (Day 16); never set here


@dataclass
class Proposal:
    locator: object                 # a Playwright Locator for the healed element
    suggestion: LocatorSuggestion
    event: HealEvent


class Healer:
    def __init__(self, client_factory, config: HealConfig | None = None):
        self._client_factory, self._client = client_factory, None
        self.config = config or HealConfig()
        self.events: list[HealEvent] = []
        self.test_id = ""
        self._heals_in_test = 0
        self._cache: dict[tuple, LocatorSuggestion] = {}

    @property
    def client(self):
        if self._client is None:  # created on first use: a run with --heal but no locator failures never needs the model
            self._client = self._client_factory()
        return self._client

    def begin_test(self, test_id: str) -> None:
        self.test_id, self._heals_in_test = test_id, 0

    def _allowed(self, hint: str) -> bool:
        return hint == "locator" or (self.config.allow_maybe and hint == "maybe")

    def heal(self, page, action: str, locator, exc: BaseException) -> Proposal | None:
        """Called by a page-object action that just failed with `exc`. Returns a Proposal to retry with, or None."""
        started = time.perf_counter()
        info = analyze_exception(exc)
        event = HealEvent(
            test_id=self.test_id, time=datetime.now(timezone.utc).isoformat(timespec="seconds"), action=action,
            page_url=_safe(lambda: page.url, ""), failed_locator=info.locator, kind=info.kind, heal_hint=info.heal_hint,
            definitions=find_definitions(info.locator), caller_frames=stack_frames(), error_message=info.message[:400],
        )
        self.events.append(event)
        try:
            return self._heal(page, action, info, event)
        except Exception as e:  # noqa: BLE001: healing must never turn a test failure into a different failure
            event.outcome, event.error_message = "error", f"{type(e).__name__}: {str(e)[:300]}"
            log.warning("heal_error", extra={"test": self.test_id, "error": event.error_message})
            return None
        finally:
            event.seconds = round(time.perf_counter() - started, 2)

    def _heal(self, page, action, info, event) -> Proposal | None:
        if not self._allowed(info.heal_hint):
            event.outcome = "skipped_guard"
            return None
        if self._heals_in_test >= self.config.max_heals_per_test:
            event.outcome = "budget_exhausted"
            return None
        self._heals_in_test += 1

        role = failed_role(info.locator)
        key = (_url_path(page), info.locator, action)
        cached = self._cache.get(key)
        if cached is not None:
            check = validate_suggestion(page, cached, info.locator, action, role=role)
            if check.ok:
                event.from_cache = True
                return self._proposal(page, cached, check.element, event)

        ctx = FailureContext(schema=1, test_id=self.test_id, collected_at=event.time,
                             error=replace(info, frames=event.caller_frames), page=capture_page_state(page))
        result = suggest_locator(self.client, ctx, page, max_attempts=self.config.max_attempts,
                                 temperature=self.config.temperature, action=action)
        event.attempts = len(result.attempts)
        event.rejections = [a.rejected_because for a in result.attempts if a.rejected_because]
        if not result.healed:
            event.outcome = "no_suggestion"
            return None
        self._cache[key] = result.suggestion
        event.repaired_from = result.attempts[-1].repaired_from
        return self._proposal(page, result.suggestion, result.element, event)

    def _proposal(self, page, suggestion: LocatorSuggestion, element: dict | None, event: HealEvent) -> Proposal:
        event.suggestion, event.strategy = render_locator(suggestion), suggestion.strategy
        event.reason, event.confidence, event.element = suggestion.reason, suggestion.confidence, element
        return Proposal(locator=build_locator(page, suggestion), suggestion=suggestion, event=event)

    def confirm(self, proposal: Proposal, ok: bool) -> None:
        """The caller retried the action with the proposal: record whether that worked."""
        proposal.event.verified = ok
        proposal.event.outcome = "healed" if ok else "retry_failed"
        log.info("heal_result", extra={"test": self.test_id, "outcome": proposal.event.outcome,
                                       "locator": proposal.event.suggestion})


def _safe(fn, default):
    try:
        return fn()
    except Exception:  # noqa: BLE001
        return default


def _url_path(page) -> str:
    return urlparse(_safe(lambda: page.url, "")).path


_current: Healer | None = None


def current() -> Healer | None:
    return _current


@contextlib.contextmanager
def use(healer: Healer | None):
    """Make `healer` the active one for the duration of a test (None switches healing off)."""
    global _current
    previous, _current = _current, healer
    try:
        yield healer
    finally:
        _current = previous


def event_dicts(healer: Healer) -> list[dict]:
    return [asdict(e) for e in healer.events]
