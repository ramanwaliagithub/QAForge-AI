"""Turn a structured TestCase into a pytest-playwright test file using an LLM."""
import ast
import json
import re
from pathlib import Path

from ai_testgen.scenarios import load_prompt
from ai_testgen.schema import TestCase
from framework.llm_client import LLMClient
from framework.logging_utils import get_logger

log = get_logger("qaforge.codegen")

PAGES_DIR = Path(__file__).resolve().parent.parent / "framework" / "pages"
GENERATED_DIR = Path(__file__).parent / "generated"

_FENCE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL)


class CodegenError(RuntimeError):
    """The model never produced valid Python within the allowed attempts."""


def page_object_summary() -> str:
    """Class and method signatures of the page objects (not full bodies) to keep the prompt small."""
    lines = []
    for path in sorted(PAGES_DIR.glob("*_page.py")):
        tree = ast.parse(path.read_text())
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            base = f"({', '.join(ast.unparse(b) for b in node.bases)})" if node.bases else ""
            lines.append(f"class {node.name}{base}:")
            doc = ast.get_docstring(node)
            if doc:
                lines.append(f'    """{doc.splitlines()[0]}"""')
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                    prop = any(ast.unparse(d) == "property" for d in item.decorator_list)
                    args = ast.unparse(item.args)
                    lines.append(f"    {'@property ' if prop else ''}def {item.name}({args})")
            lines.append("")
    return "\n".join(lines).strip()


NO_CONTEXT = "(No page snapshot available. Infer locators carefully from the test case.)"


def render_codegen_prompt(case: TestCase, page_context: str = "") -> str:
    return (
        load_prompt("codegen")
        .replace("{page_objects}", page_object_summary())
        .replace("{page_context}", page_context or NO_CONTEXT)
        .replace("{testcase}", json.dumps(case.model_dump(), indent=2))
    )


def extract_code(text: str) -> str:
    m = _FENCE.search(text)
    return (m.group(1) if m else text).strip() + "\n"


def check_code(code: str) -> None:
    """Cheap static checks before we write anything to disk. Raises ValueError with a message for the model."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ValueError(f"SyntaxError: {e.msg} (line {e.lineno})") from e
    tests = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    if len(tests) != 1:
        raise ValueError(f"Expected exactly one test_ function, found {len(tests)}.")
    if "sleep" in code or "wait_for_timeout" in code:
        raise ValueError("Do not use sleep or wait_for_timeout.")
    if not any(isinstance(n, ast.Assert) or (isinstance(n, ast.Call) and ast.unparse(n.func) == "expect")
               for n in ast.walk(tests[0])):
        raise ValueError("The test has no assertion.")


def generate_test_code(
    client: LLMClient, case: TestCase, temperature: float = 0.0, max_retries: int = 2, page_context: str = ""
) -> str:
    base_prompt = render_codegen_prompt(case, page_context)
    prompt, last_error = base_prompt, None
    for attempt in range(max_retries + 1):
        code = extract_code(client.generate(prompt, temperature=temperature).text)
        try:
            check_code(code)
        except ValueError as e:
            last_error = e
            log.warning("invalid_code", extra={"attempt": attempt + 1, "error": str(e)})
            prompt = f"{base_prompt}\n\nYour previous answer was rejected: {e}\nReturn the corrected code only."
            continue
        return code
    raise CodegenError(f"No valid code after {max_retries + 1} attempts: {last_error}")


def slugify(text: str, max_len: int = 40) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:max_len] or "case"


def write_test_file(code: str, story: str, index: int, case: TestCase, out_dir: Path = GENERATED_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"test_{story}_{index:02d}_{slugify(case.title)}.py"
    path.write_text(code)
    return path
