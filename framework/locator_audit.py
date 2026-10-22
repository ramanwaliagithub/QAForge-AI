"""Static audit of Playwright locators in page objects, ranked by how resilient they are to UI changes.

Tiers (best to worst):
  semantic   get_by_role / get_by_label / get_by_text / get_by_placeholder / get_by_alt_text / get_by_title / get_by_test_id
             -> what a user sees; survives restyling and DOM restructuring
  name_attr  CSS on a form field `name` attribute, e.g. input[name='username']
             -> the contract with the server's form binding, so it rarely changes
  id         CSS `#id`
             -> stable if the id is hand-written, breaks when ids are generated or renamed
  css        any other CSS selector that is not class/position based
  fragile    class selectors, attribute-substring matches (href*=), structural combinators, nth-child, XPath
             -> tied to styling or page structure
`.nth()`, `.first` and `.last` are reported separately as position-dependent.
"""
import ast
import re
from dataclasses import dataclass
from pathlib import Path

SEMANTIC_CALLS = {"get_by_role", "get_by_label", "get_by_text", "get_by_placeholder", "get_by_alt_text",
                  "get_by_title", "get_by_test_id"}
TIER_SCORE = {"semantic": 3, "name_attr": 2, "id": 2, "css": 1, "fragile": 0}
POSITION_CALLS = {"nth", "first", "last"}

_ID = re.compile(r"^#[\w-]+$")
_NAME_ATTR = re.compile(r"^[a-z]*\[name=X\]$")  # matched after attribute values are masked as X


@dataclass
class Finding:
    file: str
    line: int
    call: str          # locator | get_by_role | ...
    selector: str      # first string argument, "" if dynamic
    tier: str
    position: bool = False  # .nth()/.first/.last used on this chain


def classify_css(selector: str) -> str:
    sel = selector.strip()
    if sel.startswith(("//", "xpath=", "(//")):
        return "fragile"
    # strip attribute values so a "." or ">" inside quotes is not mistaken for syntax
    bare = re.sub(r"=(?:(['\"]).*?\1|[^\]\s'\"]+)", "=X", sel)
    if _ID.match(sel):
        return "id"
    if _NAME_ATTR.match(bare):
        return "name_attr"
    if re.search(r"\[\w+[*^$]=", bare) or ":nth-" in bare or re.search(r"[>+~]", bare) or re.search(r"(^|[\w\]])\.[A-Za-z_-]", bare):
        return "fragile"
    return "css"


def _first_str(node: ast.Call) -> str:
    if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
        return node.args[0].value
    if node.args and isinstance(node.args[0], ast.JoinedStr):  # f-string: keep the literal shape
        return "".join(p.value if isinstance(p, ast.Constant) else "{}" for p in node.args[0].values)
    return ""


def _chain_has_position(node: ast.AST) -> bool:
    """True if any call/attribute along the chain this locator belongs to is .nth()/.first/.last."""
    return any(isinstance(n, ast.Attribute) and n.attr in POSITION_CALLS for n in ast.walk(node))


def audit_source(source: str, filename: str = "<src>") -> list[Finding]:
    findings = []
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        name = node.func.attr
        if name in SEMANTIC_CALLS:
            findings.append(Finding(filename, node.lineno, name, _first_str(node), "semantic"))
        elif name == "locator":
            sel = _first_str(node)
            findings.append(Finding(filename, node.lineno, name, sel, classify_css(sel) if sel else "css"))
    # mark position use per statement line: a chain such as `.locator("option").nth(1)` shares its line
    position_lines = {n.lineno for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr in POSITION_CALLS}
    for f in findings:
        f.position = f.line in position_lines
    return sorted(findings, key=lambda f: f.line)


def audit_paths(paths: list[Path]) -> list[Finding]:
    out = []
    for p in paths:
        out += audit_source(p.read_text(), str(p))
    return out


def score(findings: list[Finding]) -> float:
    """Mean tier score, 0 (all fragile) to 3 (all semantic)."""
    return round(sum(TIER_SCORE[f.tier] for f in findings) / len(findings), 2) if findings else 0.0
