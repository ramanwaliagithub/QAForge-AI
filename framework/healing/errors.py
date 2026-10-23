"""Turn a test failure into structured facts: what kind of failure, which locator, which source lines.

The classification feeds the healing guard rail: only failures where a *locator* is the problem may be healed.
A failed assertion on a found element is a possible product bug and must never be "healed" away.
"""
import re
import traceback
from dataclasses import dataclass, field
from pathlib import Path

_ANSI = re.compile(r"\x1b\[[0-9;]*m")
_LOCATOR_EXPR = re.compile(r"^\s*-\s*waiting for ((?:locator|get_by_\w+|frame_locator)\(.*)$", re.M)
_ACTION = re.compile(r"^(?:\w+\.)?(?P<cls>Locator|Page|Frame)\.(?P<action>\w+): ", re.M)
_TIMEOUT = re.compile(r"Timeout (\d+)ms exceeded")
_EXPECT = re.compile(r'Expect "(\w+)"')

# What may a healer do about each kind?
#   locator: the locator is the problem (heal candidate)   maybe: could be a locator or a product change   no: never heal
KIND_HINT = {
    "locator_not_found": "locator",       # waited for the locator, nothing matched
    "strict_mode_violation": "locator",   # matched several elements; needs to be more specific
    "assertion_element_missing": "maybe",  # expect() on an element that does not exist: renamed, or removed on purpose?
    "not_actionable": "maybe",            # matched, but wrong element type or not enabled/visible
    "assertion": "no",                    # element found, value differs: a possible product bug
    "timeout_other": "no",                # navigation / url / load waits
    "other": "no",
}


@dataclass
class ErrorInfo:
    type: str                  # e.g. "playwright._impl._errors.TimeoutError"
    message: str               # cleaned, without the aria snapshot Playwright appends to expect() failures
    kind: str                  # a KIND_HINT key
    heal_hint: str             # locator | maybe | no
    locator: str | None = None  # the locator expression Playwright was waiting for
    action: str | None = None   # "click", "fill", or the expect matcher such as "to_be_visible"
    timeout_ms: int | None = None
    frames: list[dict] = field(default_factory=list)  # project source frames, innermost last
    raised_in: str = "other"   # page_object | test | other: where the innermost project frame is


def clean_message(text: str, max_chars: int = 1500) -> str:
    text = _ANSI.sub("", text)
    text = text.split("\nAria snapshot:")[0]  # the page snapshot is captured separately
    return text.strip()[:max_chars]


def classify_message(exc_type: str, message: str) -> tuple[str, str | None, str | None, int | None]:
    """Return (kind, locator, action, timeout_ms) from an exception type name and its (cleaned) message."""
    loc = _LOCATOR_EXPR.search(message)
    locator = loc.group(1).strip() if loc else None
    timeout = _TIMEOUT.search(message)
    timeout_ms = int(timeout.group(1)) if timeout else None
    expect = _EXPECT.search(message)
    act = _ACTION.search(message)
    action = expect.group(1) if expect else (act.group("action") if act else None)

    if "strict mode violation" in message:
        kind = "strict_mode_violation"
    elif expect or (exc_type.endswith("AssertionError") and message.startswith("Locator expected")):
        kind = "assertion_element_missing" if "element(s) not found" in message else "assertion"
    elif exc_type.endswith("AssertionError"):
        kind = "assertion"
    elif "locator resolved to" in message:
        kind = "not_actionable"  # Playwright found the element but could not act on it
    elif locator and ("Timeout" in message or exc_type.endswith("TimeoutError")):
        kind = "locator_not_found"
    elif exc_type.endswith("TimeoutError"):
        kind = "timeout_other"
    else:
        kind = "other"
    return kind, locator, action, timeout_ms


def project_frames(tb, root: Path | None = None, limit: int = 8) -> list[dict]:
    """Stack frames that are in this repository (not site-packages / .venv), innermost last."""
    root = (root or Path.cwd()).resolve()
    out = []
    for fs in traceback.extract_tb(tb):
        p = Path(fs.filename).resolve()
        if ".venv" in p.parts or "site-packages" in p.parts:
            continue
        try:
            rel = p.relative_to(root)
        except ValueError:
            continue
        out.append({"file": str(rel), "line": fs.lineno, "function": fs.name, "code": (fs.line or "").strip()})
    return out[-limit:]


def raised_in(frames: list[dict]) -> str:
    """Where the failure surfaced. In a page object the locator definition is nearby; in a test it is an assertion."""
    if not frames:
        return "other"
    inner = frames[-1]["file"].replace("\\", "/")
    if inner.startswith("framework/pages/"):
        return "page_object"
    return "test" if inner.startswith("tests/") or inner.startswith("ai_testgen/generated/") else "other"


def analyze_exception(exc: BaseException, root: Path | None = None) -> ErrorInfo:
    exc_type = f"{type(exc).__module__}.{type(exc).__qualname__}"
    message = clean_message(str(exc))
    kind, locator, action, timeout_ms = classify_message(exc_type, message)
    frames = project_frames(exc.__traceback__, root)
    return ErrorInfo(type=exc_type, message=message, kind=kind, heal_hint=KIND_HINT[kind], locator=locator,
                     action=action, timeout_ms=timeout_ms, frames=frames, raised_in=raised_in(frames))
