"""pytest integration for opt-in self-healing: the `--heal` flag, the per-test runtime and the report.

    uv run pytest --heal                      # heal locator failures at run time; propose, never edit source
    uv run pytest --heal -W error::framework.healing.plugin.HealedLocatorWarning   # make any heal fail the test (CI)

Each test that only passed because a locator was healed raises a HealedLocatorWarning (shown in pytest's warnings
summary), so a heal is never a silent pass. All proposals are written to reports/healing.json (override: HEAL_REPORT).
Source files are never modified.
"""
import json
import os
import warnings
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import allure
import pytest

from framework.healing import runtime
from framework.healing.runtime import HealConfig, Healer
from framework.llm_client import get_client

DEFAULT_REPORT = "reports/healing.json"


class HealedLocatorWarning(UserWarning):
    """A test passed only because a locator was healed at run time. The page object still needs fixing."""


def pytest_addoption(parser):
    group = parser.getgroup("self-healing")
    group.addoption("--heal", action="store_true", default=False,
                    help="heal locator failures at run time (retry once with an LLM-proposed locator; never edits source)")
    group.addoption("--heal-allow-maybe", action="store_true", default=False,
                    help="also try failures whose cause is ambiguous (element found but not actionable, ...)")
    group.addoption("--heal-max-per-test", type=int, default=3, help="healing attempts allowed per test (default 3)")


def _enabled(config) -> bool:
    return bool(config.getoption("--heal"))


def pytest_configure(config):
    config.addinivalue_line("filterwarnings", "default::framework.healing.plugin.HealedLocatorWarning")
    config._worker_heal_events = []  # events handed over by xdist workers (controller only)
    config._healer = None
    if _enabled(config):
        config._healer = Healer(get_client, HealConfig(
            allow_maybe=config.getoption("--heal-allow-maybe"), max_heals_per_test=config.getoption("--heal-max-per-test")))


@pytest.fixture(autouse=True)
def _self_healing(request):
    healer = request.config._healer
    if healer is None:
        yield
        return
    healer.begin_test(request.node.nodeid)
    start = len(healer.events)
    with runtime.use(healer):
        yield
    mine = healer.events[start:]  # reruns of the same test each get their own events
    if not mine:
        return
    allure.attach(json.dumps([asdict(e) for e in mine], indent=2), name="healing", attachment_type=allure.attachment_type.JSON)
    for e in mine:
        if e.outcome == "healed":
            where = f"{e.definitions[0]['file']}:{e.definitions[0]['line']}" if e.definitions else "a page object"
            warnings.warn(HealedLocatorWarning(
                f"healed {e.failed_locator} -> {e.suggestion} (defined in {where}); fix the page object, "
                "this test only passed because of the heal"), stacklevel=1)


def _all_events(config) -> list[dict]:
    own = [asdict(e) for e in config._healer.events] if config._healer else []
    return own + config._worker_heal_events


def summarize(events: list[dict]) -> dict:
    out: dict[str, int] = {}
    for e in events:
        out[e["outcome"]] = out.get(e["outcome"], 0) + 1
    return {"events": len(events), **dict(sorted(out.items()))}


def write_report(events: list[dict], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": os.getenv("OLLAMA_MODEL", "llama3.1:8b") if os.getenv("LLM_PROVIDER", "ollama") == "ollama" else os.getenv("LLM_PROVIDER"),
        "note": "Proposals only: no source file was changed. Review each, then fix the page object by hand.",
        "summary": summarize(events), "events": events,
    }, indent=2) + "\n")
    return path


def pytest_sessionfinish(session, exitstatus):
    config = session.config
    if config._healer is None:
        return
    if hasattr(config, "workerinput"):  # xdist worker: hand the events to the controller, which writes the report
        config.workeroutput["heal_events"] = [asdict(e) for e in config._healer.events]
        return
    write_report(_all_events(config), os.getenv("HEAL_REPORT", DEFAULT_REPORT))


@pytest.hookimpl(optionalhook=True)
def pytest_testnodedown(node, error):
    node.config._worker_heal_events.extend(getattr(node, "workeroutput", {}).get("heal_events", []))


def pytest_terminal_summary(terminalreporter, config):
    if config._healer is None:
        return
    events = _all_events(config)
    terminalreporter.section("self-healing")
    if not events:
        terminalreporter.write_line("no locator failures needed healing")
    s = summarize(events)
    if events:
        terminalreporter.write_line("  ".join(f"{k}={v}" for k, v in s.items()))
    for e in events:
        if e["outcome"] == "healed":
            terminalreporter.write_line(f"  healed  {e['failed_locator']}  ->  {e['suggestion']}   [{e['test_id']}]")
        elif e["outcome"] not in ("skipped_guard",):
            terminalreporter.write_line(f"  {e['outcome']}  {e['failed_locator']}   [{e['test_id']}]")
    terminalreporter.write_line(f"proposals only; no source file was changed. Report: {os.getenv('HEAL_REPORT', DEFAULT_REPORT)}")
