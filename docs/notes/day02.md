# Day 02
- Own `browser`/`page` fixtures in `tests/conftest.py` (sync Playwright) with `--headed` and `--slowmo` options; no pytest-playwright plugin yet, to keep control and avoid fixture-name clashes.
- Headless vs headed: same results; headed is ~1s slower and only useful for debugging.
- ParaBank quirk: a bad login on the public demo shows "An internal error has occurred" (and lands on overview.htm), not "could not be verified". Test asserts the `p.error` element only; don't trust exact wording or URL on this shared demo.
- Fixtures are per-test contexts (isolated cookies) on one session-wide browser.
