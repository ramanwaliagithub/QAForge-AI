"""Find where a locator is defined in the page objects, so a human (or the Day 16 apply step) knows which line to change."""
from pathlib import Path


def find_definitions(locator_expr: str | None, roots: tuple[str, ...] = ("framework/pages",), limit: int = 5) -> list[dict]:
    """Lines whose source contains the locator expression Playwright logged, e.g. `locator("#amt")`.

    Textual search on purpose: it finds literal selectors, and finds nothing for built ones (f-strings), which is
    honest: the caller must then look at the call site.
    """
    if not locator_expr:
        return []
    hits = []
    for root in roots:
        for path in sorted(Path(root).rglob("*.py")):
            for n, line in enumerate(path.read_text().splitlines(), start=1):
                if locator_expr in line:
                    hits.append({"file": str(path), "line": n, "text": line.strip()})
    return hits[:limit]
