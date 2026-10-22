# Locator quality checklist

Locators are the main source of brittle UI tests. This is the checklist used for the page objects in `framework/pages/`.
It is enforced by `tests/test_locator_quality.py` (see "How it is enforced") and measured by `scripts/locator_audit.py`.

## Preference order

Pick the first one that works and resolves to exactly one element.

| Tier | Locator | Example | Breaks when |
|---|---|---|---|
| 1. semantic | `get_by_role(role, name=...)` | `get_by_role("button", name="Transfer", exact=True)` | the user-visible role or name changes (which is a real change) |
| 1. semantic | `get_by_label`, `get_by_text`, `get_by_placeholder`, `get_by_test_id` | `get_by_label("Amount")` | the visible text changes |
| 2. form `name` attribute | `input[name='username']` | | the server-side field binding changes (rare: it is a contract) |
| 2. hand-written `#id` | `#amount` | | someone renames the id; **never** for generated ids (ParaBank gives the phone field a random UUID id) |
| 3. other CSS | `input[value='Transfer']` | | styling or text changes; prefer a role instead |
| 4. fragile | `.error`, `a[href*='activity.htm']`, `div > p`, `li:nth-child(2)`, XPath | | a refactor, a restyle, or a reordering |

Also avoid position: `.nth(i)`, `.first`, `.last`. If you need "the one containing X", use `filter(has_text=...)` or `filter(has=...)`.

## The checklist

1. **Does a role + accessible name exist?** Look at the accessibility tree, not the HTML (see below). If yes, use it.
2. **Is it unique?** Playwright's strict mode throws if a locator matches more than one element; treat that as information.
   (`p.error` matched 3 elements on an empty transfer: two validation messages plus an internal error.)
3. **Does the name describe what the user sees?** Use the user's words ("Open New Account"), not the implementation.
4. **Buttons and links: use `exact=True`** when one name is a prefix of another ("Transfer" vs "Transfer Funds").
5. **Never use generated values** (UUID ids, `jsessionid` in hrefs, auto-numbered classes).
6. **No position.** No `.nth()`, `.first`, `.last`, `:nth-child`. Scope with a container role or `filter` instead.
7. **No XPath.** There is no case in this app that needs it.
8. **Prefer web-first assertions over manual waits.** `expect(options).not_to_have_count(0)`, not `option.first.wait_for(...)`.
9. **Element has no accessible name?** Use the form `name` attribute or a hand-written id, then add the selector to the
   `ACCEPTED` register in `tests/test_locator_quality.py` **with the reason**, and ask the app team for a label or `data-testid`.
10. **Check the selector is valid CSS.** `#customer.firstName` means id `customer` with class `firstName`; the id has a dot, so use `[id='customer.firstName']`.

## How to find a good locator

- Accessibility snapshot of a region: `page.locator("#rightPanel").aria_snapshot()`; it prints roles and names, which are exactly what `get_by_role` matches.
- Playwright MCP's `browser_snapshot` returns the same tree (with element refs, `f1e34` inside frames).
- Count before you commit: `page.get_by_role(...).count()` should be 1.
- `get_by_text("X")` returns the *smallest element containing the text*, not its container. In ParaBank's
  `<p><b>Your new account number:</b> <a>123</a></p>` it matches the `<b>`, which does not contain the link.
  Use `get_by_role("paragraph").filter(has_text="Your new account number").get_by_role("link")` instead.

## ParaBank's accessibility gaps (why some locators stay non-semantic)

- Form inputs have **no accessible name**: the labels are table cells, not `<label for>`, so `get_by_label` finds nothing.
  Affects login, registration, transfer amount, bill pay, and most forms.
- Dropdowns (`<select>`) have no accessible name either, and several pages have two of them.
- Errors are `<p class="error">`; there is no `role="alert"`, so a screen reader would not announce them.
- Some ids are generated UUIDs (the bill-pay phone field) and links carry `;jsessionid=...`.
- These are accessibility bugs as well as testability bugs; fixing them would let us retire most of the `ACCEPTED` register.

## Result of the Day 12 refactor (`uv run python -m scripts.locator_audit`)

| | Before | After |
|---|---|---|
| Locators in page objects | 23 | 26 |
| Semantic (role/label/text) | 7 | 17 |
| Form `name` attribute | 4 | 4 |
| Hand-written `#id` | 7 | 4 |
| Other CSS | 3 | 0 |
| Fragile (class, href substring, ...) | 2 | 1 (`p.error`, registered exception) |
| Position-dependent (`.nth/.first`) | 2 | 0 |
| Average score (0 = all fragile, 3 = all semantic) | 2.00 | 2.58 |

Changes: table links by `role=link` with a numeric name instead of `href*='activity.htm'`; the open-account result by
heading and by its sentence instead of ids; the Transfer button by role instead of `input[value=...]`; the account-type
dropdown as "the combobox that offers SAVINGS" instead of `#type`; option lookups through `get_by_role("option")`;
manual `wait_for` and `.nth()` replaced with web-first count assertions.

## How it is enforced

`tests/test_locator_quality.py` fails when:
- a non-semantic locator is added without an entry (and reason) in `ACCEPTED`;
- an `ACCEPTED` entry is no longer used (so the register does not rot);
- XPath or position-dependent locators appear in `framework/pages/`;
- the average score drops below `MIN_SCORE` (raise it whenever the score improves, never lower it).
