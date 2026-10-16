"""Page context for grounding generated tests in the real UI.

Two views of a page are captured with Playwright:
- `aria`: the accessibility snapshot (roles and accessible names).
- `elements`: a compact list of interactive elements with exact CSS selectors. Needed because ParaBank's
  inputs have no accessible names, so the aria view alone cannot yield a working locator.
"""
import json
import re
from pathlib import Path

from playwright.sync_api import Page

SNAPSHOTS_DIR = Path(__file__).parent / "snapshots"

# Which ParaBank screens each story exercises.
STORY_PAGES = {
    "transfer_funds": ["transfer.htm"],
    "bill_pay": ["billpay.htm"],
    "open_account": ["openaccount.htm"],
}

_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-")

_ELEMENTS_JS = """() => [...document.querySelectorAll(
    '#rightPanel input, #rightPanel select, #rightPanel button, #rightPanel textarea, #rightPanel a')].map(e => ({
  tag: e.tagName.toLowerCase(), type: e.type || null, id: e.id || null, name: e.getAttribute('name'),
  value: e.tagName === 'INPUT' && ['submit', 'button'].includes(e.type) ? e.value : null,
  text: ['A', 'BUTTON'].includes(e.tagName) ? e.textContent.trim().slice(0, 40) : null,
  label: (e.closest('tr')?.querySelector('td')?.textContent || '').trim().slice(0, 40),
  options: e.tagName === 'SELECT' ? [...e.options].map(o => o.text).slice(0, 5) : null }))"""


def capture_page(page: Page, base_url: str, path: str) -> dict:
    """Open `path` (the page must already be logged in) and return both snapshot views."""
    page.goto(f"{base_url.rstrip('/')}/{path}")
    page.locator("#rightPanel").wait_for()
    selects = page.locator("#rightPanel select")
    for i in range(selects.count()):  # dropdowns are filled asynchronously
        selects.nth(i).locator("option").first.wait_for(state="attached")
    return {
        "path": path,
        "aria": page.locator("#rightPanel").aria_snapshot(),
        "elements": page.evaluate(_ELEMENTS_JS),
    }


def selector_for(el: dict) -> str | None:
    """Best stable CSS selector for an element, or None if nothing stable exists."""
    if el.get("id") and not _UUID.match(el["id"]):
        # `#a.b` would mean id "a" with class "b", so use an attribute selector for ids with special characters.
        return f"#{el['id']}" if re.fullmatch(r"[A-Za-z_][\w-]*", el["id"]) else f"[id='{el['id']}']"
    if el.get("name"):
        return f"{el['tag']}[name='{el['name']}']"
    if el.get("value"):
        return f"{el['tag']}[value='{el['value']}']"
    if el.get("text"):
        return f"{el['tag']}:has-text('{el['text']}')"
    return None


def format_elements(elements: list[dict]) -> str:
    lines = []
    for el in elements:
        selector = selector_for(el)
        if not selector:
            continue
        kind = el.get("type") or el["tag"]
        parts = [f"- {el['tag']}[{kind}]", f"selector: {selector}"]
        if el.get("label"):
            parts.append(f"label: {el['label']!r}")
        if el.get("options"):
            numeric = all(o.isdigit() for o in el["options"])  # account ids differ per user; don't let the model hardcode them
            parts.append("options: account ids (vary per user, never hardcode)" if numeric else f"options: {el['options']}")
        lines.append("  ".join(parts))
    return "\n".join(lines)


def estimate_tokens(text: str) -> int:
    """Rough estimate (about 4 characters per token); good enough for budgeting."""
    return (len(text) + 3) // 4


_NOISE = re.compile(r"^\s*- (?:row|rowgroup|cell)(?: \"[^\"]*\")?:?\s*$")


def trim_to_tokens(text: str, max_tokens: int = 2000) -> str:
    """Drop structural noise (bare rows/cells), then cut at a line boundary to fit the budget."""
    lines = [ln for ln in text.splitlines() if ln.strip() and not _NOISE.match(ln)]
    kept, used = [], 0
    for ln in lines:
        cost = estimate_tokens(ln) + 1
        if used + cost > max_tokens:
            kept.append("... (truncated)")
            break
        kept.append(ln)
        used += cost
    return "\n".join(kept)


def build_context(snapshots: list[dict], mode: str = "elements", max_tokens: int = 2000) -> str:
    """Render snapshots into prompt text. mode: none | aria | elements | both."""
    if mode == "none" or not snapshots:
        return ""
    per_page = max_tokens // len(snapshots)
    blocks = []
    for snap in snapshots:
        parts = [f"### Screen: {snap['path']}  (navigate with: logged_in_page.goto(f\"{{base_url}}/{snap['path']}\"))"]
        if mode in ("aria", "both"):
            parts.append("Accessibility snapshot:\n" + trim_to_tokens(snap["aria"], per_page // (2 if mode == "both" else 1)))
        if mode in ("elements", "both"):
            parts.append("Interactive elements (use these exact selectors):\n"
                         + trim_to_tokens(format_elements(snap["elements"]), per_page // (2 if mode == "both" else 1)))
        blocks.append("\n".join(parts))
    return "\n\n".join(blocks)


def save_snapshot(snap: dict, out_dir: Path = SNAPSHOTS_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{Path(snap['path']).stem}.json"
    path.write_text(json.dumps(snap, indent=2) + "\n")
    return path


def load_snapshots(story: str, snap_dir: Path = SNAPSHOTS_DIR) -> list[dict]:
    return [json.loads((snap_dir / f"{Path(p).stem}.json").read_text()) for p in STORY_PAGES.get(story, [])]
