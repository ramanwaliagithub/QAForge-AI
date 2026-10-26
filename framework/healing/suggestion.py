"""A locator suggestion as data, a safe way to turn it into a Playwright locator, and checks that reject bad ones.

The model never writes code that we run: it fills in fields, we validate them and build the locator ourselves.
"""
import json
import re
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, model_validator

from framework.healing.errors import ErrorInfo
from framework.locator_audit import classify_css

_INTENT = re.compile(r"\.(fill|click|select_option|check|uncheck|type|press|hover)\(")
_NOT_TEXT_INPUT_TYPES = {"submit", "button", "checkbox", "radio", "image", "reset", "file"}


class LocatorSuggestion(BaseModel):
    strategy: Literal["role", "label", "text", "placeholder", "css"]
    role: str | None = None
    name: str | None = None      # accessible name for role locators
    exact: bool = False
    text: str | None = None      # for label / text / placeholder
    css: str | None = None       # only for elements with no accessible name; keep it to an id or a name attribute
    reason: str = ""
    confidence: float = Field(0.5, ge=0, le=1)

    @model_validator(mode="after")
    def _fields_match_strategy(self):
        if self.strategy == "role" and not self.role:
            raise ValueError("strategy 'role' needs a role")
        if self.strategy in ("label", "text", "placeholder") and not self.text:
            raise ValueError(f"strategy '{self.strategy}' needs text")
        if self.strategy == "css":
            if not self.css:
                raise ValueError("strategy 'css' needs css")
            if self.css.lstrip().startswith(("//", "xpath=", "(//", "nth=", "js=")):
                raise ValueError("XPath, nth and js selectors are not allowed")
        return self


class SuggestionParseError(ValueError):
    """The model output could not be turned into a LocatorSuggestion. The message is safe to show the model."""


def parse_suggestion(text: str) -> LocatorSuggestion:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise SuggestionParseError("No JSON object in the response.")
    try:
        return LocatorSuggestion.model_validate(json.loads(text[start : end + 1]))
    except json.JSONDecodeError as e:
        raise SuggestionParseError(f"Invalid JSON: {e}") from e
    except ValidationError as e:
        problems = "; ".join(f"{'.'.join(map(str, x['loc'])) or 'suggestion'}: {x['msg']}" for x in e.errors()[:4])
        raise SuggestionParseError(f"Suggestion does not match the schema: {problems}") from e


def render_locator(s: LocatorSuggestion, prefix: str = "") -> str:
    """Python source for the locator, e.g. `get_by_role("button", name="Transfer", exact=True)`."""
    q = json.dumps
    if s.strategy == "role":
        parts = [q(s.role)] + ([f"name={q(s.name)}"] if s.name else []) + (["exact=True"] if s.exact else [])
        return f"{prefix}get_by_role({', '.join(parts)})"
    if s.strategy == "css":
        return f"{prefix}locator({q(s.css)})"
    call = {"label": "get_by_label", "text": "get_by_text", "placeholder": "get_by_placeholder"}[s.strategy]
    return f"{prefix}{call}({q(s.text)}{', exact=True' if s.exact else ''})"


def build_locator(page, s: LocatorSuggestion):
    if s.strategy == "role":
        kwargs = {"name": s.name} if s.name else {}
        return page.get_by_role(s.role, exact=s.exact, **kwargs)
    if s.strategy == "css":
        return page.locator(s.css)
    return {"label": page.get_by_label, "text": page.get_by_text, "placeholder": page.get_by_placeholder}[s.strategy](
        s.text, exact=s.exact)


def intended_action(error: ErrorInfo) -> str | None:
    """What the test was trying to do with the locator, read from the failing source lines (innermost first)."""
    for frame in reversed(error.frames):
        m = _INTENT.search(frame["code"])
        if m:
            return m.group(1)
    return error.action


@dataclass
class Validation:
    ok: bool
    count: int
    reason: str
    element: dict | None = None


_DESCRIBE_JS = """e => ({tag: e.tagName.toLowerCase(), type: e.type || null, id: e.id || null,
  name: e.getAttribute('name'), value: e.getAttribute('value'),
  text: (e.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 60) || null})"""


def validate_suggestion(page, s: LocatorSuggestion, failed_locator: str | None = None, action: str | None = None) -> Validation:
    """Check a suggestion against the captured DOM loaded in `page`. Rejects: unchanged, fragile, zero or many matches,
    or an element the intended action cannot work on."""
    if failed_locator and _normalise(render_locator(s)) == _normalise(failed_locator):
        return Validation(False, -1, "Same locator as the one that failed.")
    if s.strategy == "css" and classify_css(s.css) == "fragile":
        return Validation(False, -1, f"CSS selector {s.css!r} is fragile (class, structure, position or XPath); "
                                      "use role/label/text, or an id or name attribute.")
    try:
        loc = build_locator(page, s)
        count = loc.count()
    except Exception as e:  # noqa: BLE001: an invalid role or selector from the model
        return Validation(False, -1, f"Locator is invalid: {str(e).splitlines()[0][:140]}")
    if count == 0:
        return Validation(False, 0, "Matches no element on the page.")
    if count > 1:
        return Validation(False, count, f"Matches {count} elements; it must match exactly one. Be more specific.")
    element = loc.evaluate(_DESCRIBE_JS)
    problem = _incompatible(action, element)
    if problem:
        return Validation(False, 1, problem, element)
    return Validation(True, 1, "Matches exactly one element.", element)


def action_compatible(action: str | None, el: dict) -> bool:
    """Can `action` work on this element description ({tag, type, ...})? Used to narrow candidates before prompting."""
    el = {"tag": el.get("tag"), "type": el.get("type")}
    if action == "click":
        return el["tag"] in ("button", "a") or (el["tag"] == "input" and el["type"] in ("submit", "button", "image", "reset", "checkbox", "radio"))
    return _incompatible(action, el) is None


def _incompatible(action: str | None, el: dict) -> str | None:
    if action in ("fill", "type", "press") and not (
            el["tag"] == "textarea" or (el["tag"] == "input" and (el["type"] or "text") not in _NOT_TEXT_INPUT_TYPES)):
        return f"The test fills text but this is a <{el['tag']}> ({el['type']}); pick the text input."
    if action == "select_option" and el["tag"] != "select":
        return f"The test selects an option but this is a <{el['tag']}>; pick the <select> dropdown."
    if action in ("check", "uncheck") and not (el["tag"] == "input" and el["type"] in ("checkbox", "radio")):
        return f"The test checks a box but this is a <{el['tag']}>."
    return None


def _normalise(source: str) -> str:
    return re.sub(r"[\s'\"]", "", source)
