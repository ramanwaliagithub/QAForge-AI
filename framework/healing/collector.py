"""Collect everything a healer needs when a UI test fails, as one JSON file plus a screenshot.

Never raises: a collector that crashes would hide the real test failure, so every capture step is guarded
and problems are recorded in `capture_errors` instead.
"""
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from framework.healing.errors import ErrorInfo, analyze_exception

SCHEMA_VERSION = 1
DEFAULT_DIR = Path("reports/failures")
MAX_ELEMENTS = 300

_ELEMENTS_JS = """(max) => {
  const visible = e => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length);
  const sel = 'a, button, input, select, textarea, label, h1, h2, h3, [role], [onclick]';
  return [...document.querySelectorAll(sel)].slice(0, max).map(e => ({
    tag: e.tagName.toLowerCase(), role: e.getAttribute('role'), type: e.type || null, id: e.id || null,
    name: e.getAttribute('name'), aria_label: e.getAttribute('aria-label'), placeholder: e.getAttribute('placeholder'),
    value: ['submit', 'button'].includes(e.type) ? e.value : null,
    text: ((e.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 60)) || null,
    href: e.tagName === 'A' ? e.getAttribute('href') : null,
    visible: visible(e), disabled: !!e.disabled,
  }));
}"""


@dataclass
class PageState:
    url: str = ""
    title: str = ""
    aria_snapshot: str = ""
    elements: list[dict] = field(default_factory=list)
    html: str = ""
    html_truncated: bool = False
    capture_errors: list[str] = field(default_factory=list)


@dataclass
class FailureContext:
    schema: int
    test_id: str
    collected_at: str
    error: ErrorInfo
    page: PageState
    screenshot: str | None = None  # file name next to the JSON

    def to_dict(self) -> dict:
        return asdict(self)


def slugify(test_id: str, max_len: int = 120) -> str:
    return re.sub(r"[^\w.-]+", "_", test_id).strip("_")[:max_len] or "test"


def _compact(elements: list[dict]) -> list[dict]:
    return [{k: v for k, v in el.items() if v not in (None, "", False) or k in ("visible",)} for el in elements]


def capture_page_state(page, max_html: int = 30_000) -> PageState:
    """Snapshot the live page. Each part is independent, so a crashed page still yields whatever is available."""
    state = PageState()

    def attempt(name, fn):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001: the page may be closed or mid-navigation; record, do not raise
            state.capture_errors.append(f"{name}: {type(e).__name__}: {str(e).splitlines()[0][:160] if str(e) else ''}")
            return None

    state.url = attempt("url", lambda: page.url) or ""
    state.title = attempt("title", lambda: page.title()) or ""
    state.aria_snapshot = attempt("aria_snapshot", lambda: page.locator("body").aria_snapshot()) or ""
    elements = attempt("elements", lambda: page.evaluate(_ELEMENTS_JS, MAX_ELEMENTS))
    state.elements = _compact(elements) if elements else []
    html = attempt("html", lambda: page.content()) or ""
    state.html_truncated = len(html) > max_html
    state.html = html[:max_html]
    return state


def collect_failure_context(page, test_id: str, exc: BaseException, out_dir: Path = DEFAULT_DIR,
                            project_root: Path | None = None) -> Path | None:
    """Write `<slug>.json` and `<slug>.png` for a failed test; returns the JSON path (None if even writing failed)."""
    try:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        slug = slugify(test_id)
        state = capture_page_state(page)

        shot_name = None
        try:
            (out_dir / f"{slug}.png").write_bytes(page.screenshot(full_page=True))
            shot_name = f"{slug}.png"
        except Exception as e:  # noqa: BLE001
            state.capture_errors.append(f"screenshot: {type(e).__name__}")

        ctx = FailureContext(
            schema=SCHEMA_VERSION, test_id=test_id,
            collected_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            error=analyze_exception(exc, project_root), page=state, screenshot=shot_name,
        )
        path = out_dir / f"{slug}.json"
        path.write_text(json.dumps(ctx.to_dict(), indent=2) + "\n")
        return path
    except Exception:  # noqa: BLE001: never let the collector mask the real failure
        return None


def load_failure_context(path: Path) -> FailureContext:
    data = json.loads(Path(path).read_text())
    if data.get("schema") != SCHEMA_VERSION:
        raise ValueError(f"Unsupported failure context schema: {data.get('schema')!r}")
    return FailureContext(
        schema=data["schema"], test_id=data["test_id"], collected_at=data["collected_at"],
        error=ErrorInfo(**data["error"]), page=PageState(**data["page"]), screenshot=data.get("screenshot"),
    )
