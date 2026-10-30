"""Ask an LLM for a replacement locator, validate it against the captured page, retry with feedback."""
import re
from dataclasses import dataclass, field
from pathlib import Path

from framework.healing.collector import FailureContext
from framework.healing.suggestion import (
    action_compatible, failed_role, repair_dotted_id, LocatorSuggestion, SuggestionParseError, Validation, intended_action, parse_suggestion, render_locator,
    validate_suggestion,
)
from framework.llm_client import LLMClient
from framework.logging_utils import get_logger

log = get_logger("qaforge.healing")
PROMPT_PATH = Path(__file__).parent / "prompts" / "suggest_locator.md"
MAX_ELEMENTS = 80


@dataclass
class Attempt:
    """One model answer and what became of it: the parsed suggestion and its validation, or why it was rejected."""

    suggestion: LocatorSuggestion | None
    source: str | None            # rendered locator, e.g. get_by_role("button", name="Transfer")
    validation: Validation | None
    error: str | None = None      # parse error, when the model's answer was not usable
    rejected_because: str | None = None
    repaired_from: str | None = None   # what the model wrote before a mechanical repair (e.g. a dotted id)


@dataclass
class HealResult:
    """Outcome of `suggest_locator`: whether a valid suggestion was found, and every attempt made on the way."""

    healed: bool
    attempts: list[Attempt] = field(default_factory=list)

    @property
    def suggestion(self) -> LocatorSuggestion | None:
        return self.attempts[-1].suggestion if self.healed else None

    @property
    def source(self) -> str | None:
        return self.attempts[-1].source if self.healed else None

    @property
    def element(self) -> dict | None:
        return self.attempts[-1].validation.element if self.healed else None


def should_attempt(ctx: FailureContext, allow_maybe: bool = False) -> bool:
    """Guard rail: heal only failures where the locator is the problem. A failed assertion on a found element may be a
    real product bug; "healing" it would hide the bug, and DOM validation cannot tell the difference."""
    return ctx.error.heal_hint == "locator" or (allow_maybe and ctx.error.heal_hint == "maybe")


_BUTTON_INPUTS = {"submit", "button", "reset", "image"}
_SIMPLE_ID = re.compile(r"[A-Za-z_][\w-]*")
_GENERATED_ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-")  # ParaBank gives some fields a random uuid id


def implicit_role(el: dict) -> str | None:
    """ARIA role an element has by default (what Playwright's get_by_role matches)."""
    tag, typ = el.get("tag"), el.get("type") or ""
    if el.get("role"):
        return el["role"]
    if tag == "a":
        return "link"
    if tag == "button" or (tag == "input" and typ in _BUTTON_INPUTS):
        return "button"
    if tag == "select":
        return "combobox"
    if tag == "textarea" or (tag == "input" and typ not in _BUTTON_INPUTS | {"checkbox", "radio", "hidden"}):
        return "textbox"
    if tag == "input" and typ in ("checkbox", "radio"):
        return typ
    if tag in ("h1", "h2", "h3"):
        return "heading"
    return None


def accessible_name(el: dict) -> str | None:
    """Approximation of the accessible name from what the collector captured (no label association is captured)."""
    role = implicit_role(el)
    if el.get("aria_label"):
        return el["aria_label"]
    if role in ("textbox", "combobox"):
        return el.get("placeholder")  # form controls get their name from a label or placeholder; ParaBank has neither
    return el.get("value") if (role == "button" and el.get("value")) else el.get("text")


def css_hint(el: dict) -> str | None:
    """A valid CSS selector for a control with no accessible name: its id, else its name attribute.
    (An id with a dot, like `customer.firstName`, must be `[id='customer.firstName']`: `#a.b` means id a + class b.)"""
    if el.get("id") and not _GENERATED_ID.match(el["id"]):
        return f"#{el['id']}" if _SIMPLE_ID.fullmatch(el["id"]) else f"[id='{el['id']}']"
    if el.get("name"):
        return f"{el['tag']}[name='{el['name']}']"
    return None


def format_elements(elements: list[dict], limit: int = MAX_ELEMENTS, action: str | None = None,
                    role: str | None = None) -> str:
    """Candidates a locator could target, described like the accessibility tree: role and accessible name, plus a
    ready-made CSS selector when there is no accessible name. With an `action`, only elements it can work on are listed."""
    lines = []
    for el in elements:
        if not el.get("visible", True) or (action and not action_compatible(action, el)):
            continue
        el_role, name = implicit_role(el), accessible_name(el)
        if not el_role or (role and el_role != role):
            continue
        if name:
            line = f"- {el_role} name={name!r}"
        elif css_hint(el):
            line = f"- {el_role}, NO accessible name; css={css_hint(el)}"
        else:
            continue  # nothing to identify it by
        if line not in lines:  # footer links repeat the header ones
            lines.append(line)
    return "\n".join(lines[:limit])


def format_frames(frames: list[dict], limit: int = 4) -> str:
    return "\n".join(f"  - {f['file']}:{f['line']}  {f['code']}" for f in frames[-limit:]) or "  (none)"


def build_prompt(ctx: FailureContext, action: str | None = None) -> str:
    """Fill the prompt template: the failed locator, the intended action, source frames, page title and url, and the
    candidate elements that action can work on.
    """
    e = ctx.error
    action = action or intended_action(e)
    return (PROMPT_PATH.read_text()
            .replace("{locator}", e.locator or "(unknown)")
            .replace("{action}", action or "(unknown)")
            .replace("{frames}", format_frames(e.frames))
            .replace("{title}", ctx.page.title).replace("{url}", ctx.page.url)
            .replace("{elements}", format_elements(ctx.page.elements, action=action, role=failed_role(e.locator))))


def suggest_locator(client: LLMClient, ctx: FailureContext, page, max_attempts: int = 3, temperature: float = 0.0,
                    action: str | None = None) -> HealResult:
    """`page` holds the DOM to validate against: the captured one (see open_snapshot) or the live page.
    `action` overrides the intent read from the failing source lines. Rejections are fed back for the next attempt."""
    action = action or intended_action(ctx.error)
    base_prompt, prompt = build_prompt(ctx, action), build_prompt(ctx, action)
    result = HealResult(healed=False)
    tried: list[str] = []
    for n in range(1, max_attempts + 1):
        reply = client.generate(prompt, temperature=temperature, json_mode=True, num_ctx=8192).text
        try:
            suggestion = parse_suggestion(reply)
        except SuggestionParseError as e:
            result.attempts.append(Attempt(None, None, None, error=str(e), rejected_because=str(e)))
            prompt = f"{base_prompt}\n\nYour previous answer was rejected: {e}\nAnswer with corrected JSON only."
            continue
        original = render_locator(suggestion)
        suggestion = repair_dotted_id(suggestion, ctx.page.elements)
        source = render_locator(suggestion)
        repaired_from = original if source != original else None
        validation = validate_suggestion(page, suggestion, ctx.error.locator, action, role=failed_role(ctx.error.locator))
        if validation.ok:
            result.attempts.append(Attempt(suggestion, source, validation, repaired_from=repaired_from))
            result.healed = True
            log.info("heal_suggested", extra={"test": ctx.test_id, "locator": source, "attempt": n})
            return result
        result.attempts.append(Attempt(suggestion, source, validation, rejected_because=validation.reason,
                                       repaired_from=repaired_from))
        tried.append(source)
        prompt = (f"{base_prompt}\n\nYour previous suggestion {source} was rejected: {validation.reason}\n"
                  f"Already rejected, do not repeat: {'; '.join(tried)}\n"
                  "Choose one of the candidates listed above and answer with different JSON only.")
    return result


def open_snapshot(browser, ctx: FailureContext):
    """Load the captured DOM as a static page (JS off, offline) so counts reflect exactly what was captured."""
    context = browser.new_context(java_script_enabled=False, offline=True)
    page = context.new_page()
    page.set_content(ctx.page.html)
    return context, page
