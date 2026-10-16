"""Generate pytest files from saved structured test cases.

Usage: uv run python -m scripts.gen_tests [mode] [--no-few-shot]
(mode: none | aria | elements | both; default elements)
"""
import json
import sys

from dotenv import load_dotenv

from ai_testgen.codegen import GENERATED_DIR, CodegenError, generate_test_code, write_test_file
from ai_testgen.grounding import build_context, load_snapshots
from ai_testgen.schema import TestCase
from framework.llm_client import get_client

load_dotenv()
CASES_DIR = GENERATED_DIR.parent / "testcases"

args = [a for a in sys.argv[1:] if not a.startswith("--")]
MODE = args[0] if args else "elements"
FEW_SHOT = "--no-few-shot" not in sys.argv
client = get_client()
for old in GENERATED_DIR.glob("test_*.py"):
    old.unlink()  # regenerate from scratch so results reflect the current prompt

for path in sorted(CASES_DIR.glob("*.json")):
    context = build_context(load_snapshots(path.stem), MODE)
    for i, raw in enumerate(json.loads(path.read_text()), start=1):
        case = TestCase.model_validate(raw)
        try:
            code = generate_test_code(client, case, page_context=context, few_shot=FEW_SHOT)
        except CodegenError as e:
            print(f"{path.stem:15} #{i} CODEGEN-FAILED {case.title}: {e}")
            continue
        out = write_test_file(code, path.stem, i, case)
        print(f"[{MODE}] {path.stem:15} #{i} wrote {out.name}")
