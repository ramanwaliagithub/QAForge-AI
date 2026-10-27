"""Ratchet on locator quality in the page objects (see docs/locator-quality-checklist.md).

Every locator must be semantic (role, label, text, ...) unless it is listed here WITH a reason.
New non-semantic locators fail this test until someone writes the reason down, and entries that are no
longer used fail too, so the register cannot rot.
"""
from pathlib import Path

from framework.locator_audit import audit_paths, score

PAGES = sorted(Path("framework/pages").glob("*_page.py"))

# selector -> why no semantic locator is possible. Ask the app team for labels / roles to retire these.
ACCEPTED = {
    "input[name='username']": "login inputs have no accessible name; `name` is the server form-binding contract",
    "input[name='password']": "same as username",
    "input[name='{}']": "registration inputs have no accessible name; the name is the form-binding contract",
    "input[name='repeatedPassword']": "same as the registration fields",
    "#amount": "transfer amount input has no label association; hand-written id",
    "#fromAccountId": "dropdowns have no accessible name; hand-written id, and there are two on some pages",
    "#toAccountId": "same as #fromAccountId",
    "p.error": "ParaBank marks errors only with a CSS class (no role=alert); several can appear at once",
}
MIN_SCORE = 2.5  # current score is 2.58; raise the floor when it improves, never lower it


def _non_semantic():
    return [f for f in audit_paths(PAGES) if f.tier != "semantic"]


def test_every_non_semantic_locator_is_registered_with_a_reason():
    unregistered = [f"{Path(f.file).name}:{f.line} {f.selector!r} ({f.tier})" for f in _non_semantic() if f.selector not in ACCEPTED]
    assert not unregistered, "use get_by_role/label/text, or add to ACCEPTED with a reason:\n" + "\n".join(unregistered)


def test_register_has_no_stale_entries():
    used = {f.selector for f in _non_semantic()}
    assert not (set(ACCEPTED) - used), f"remove unused entries: {sorted(set(ACCEPTED) - used)}"


def test_no_xpath_or_position_dependent_locators_in_page_objects():
    findings = audit_paths(PAGES)
    assert not [f for f in findings if f.selector.startswith(("//", "xpath="))]
    assert not [f for f in findings if f.position], "avoid .nth()/.first/.last; use filter(has_text=...) or an assertion on count"


def test_overall_score_does_not_regress():
    assert score(audit_paths(PAGES)) >= MIN_SCORE


def test_page_objects_act_through_the_basepage_helpers_so_healing_covers_them():
    """`self.click(locator)` / `self.fill(...)` / `self.select_option(...)` can heal a broken locator under --heal; a direct
    `locator.click()` in a page object cannot. Only base_page.py may call Playwright's action methods on a locator."""
    import ast

    actions = {"click", "fill", "select_option", "check", "uncheck", "type", "press", "hover", "dblclick"}
    offenders = []
    for path in PAGES:
        if path.name == "base_page.py":
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in actions
                    and not (isinstance(node.func.value, ast.Name) and node.func.value.id == "self")):
                offenders.append(f"{path.name}:{node.lineno} .{node.func.attr}(...)")
    assert not offenders, "use self.click/self.fill/self.select_option (BasePage) so --heal can cover them:\n" + "\n".join(offenders)
