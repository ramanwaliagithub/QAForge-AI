import pytest

from ai_testgen.codegen import (
    CodegenError, check_code, extract_code, generate_test_code, page_object_summary, render_codegen_prompt, slugify,
    write_test_file,
)
from ai_testgen.schema import TestCase
from framework.llm_client import LLMResponse

CASE = TestCase(title="Open account", steps=["open page"], expected="Account Opened!")
GOOD = (
    "import pytest\nfrom playwright.sync_api import expect\n\n\n@pytest.mark.ai\n"
    "def test_x(page):\n    expect(page).to_have_title('x')\n"
)


def test_extract_code_strips_fences():
    assert extract_code(f"Sure!\n```python\n{GOOD}```\nDone") == GOOD
    assert extract_code(GOOD) == GOOD


def test_check_code_accepts_good():
    check_code(GOOD)


@pytest.mark.parametrize(
    "code, fragment",
    [
        ("def test_x(:\n", "SyntaxError"),
        ("def helper():\n    pass\n", "exactly one"),
        ("def test_a(page):\n    assert 1\ndef test_b(page):\n    assert 1\n", "exactly one"),
        ("import time\ndef test_x(page):\n    time.sleep(1)\n    assert 1\n", "sleep"),
        ("def test_x(page):\n    page.goto('x')\n", "no assertion"),
        ("def test_x(logged_in_page):\n    assert page.title()\n", "Undefined name.*page"),
    ],
)
def test_check_code_rejects(code, fragment):
    with pytest.raises(ValueError, match=fragment):
        check_code(code)


def test_page_object_summary_lists_real_api():
    summary = page_object_summary()
    assert "class LoginPage(BasePage)" in summary
    assert "def open_new_account(self, account_type: str='SAVINGS')" in summary or "def open_new_account" in summary
    assert "def _" not in summary


def test_prompt_contains_case_and_page_objects():
    prompt = render_codegen_prompt(CASE)
    assert "Account Opened!" in prompt and "class AccountsPage" in prompt
    assert "{testcase}" not in prompt and "{page_objects}" not in prompt


class Scripted:
    def __init__(self, *outs):
        self.outs, self.prompts = list(outs), []

    def generate(self, prompt, **kw):
        self.prompts.append(prompt)
        return LLMResponse(self.outs.pop(0), "fake", 0.0)


def test_generate_retries_with_error_feedback():
    client = Scripted("def test_x(:\n", f"```python\n{GOOD}```")
    assert generate_test_code(client, CASE) == GOOD
    assert "SyntaxError" in client.prompts[1]


def test_generate_gives_up():
    with pytest.raises(CodegenError):
        generate_test_code(Scripted("bad", "bad"), CASE, max_retries=1)


def test_write_test_file_names_by_story_index_and_title(tmp_path):
    path = write_test_file(GOOD, "open_account", 3, CASE, out_dir=tmp_path)
    assert path.name == "test_open_account_03_open_account.py"
    assert path.read_text() == GOOD
    assert slugify("A very / odd title!!") == "a_very_odd_title"


def test_prompt_includes_page_context_or_fallback():
    assert "selector: #amount" in render_codegen_prompt(CASE, "selector: #amount")
    assert "No page snapshot available" in render_codegen_prompt(CASE)
    assert "{page_context}" not in render_codegen_prompt(CASE)


def test_generate_passes_page_context_into_prompt():
    client = Scripted(GOOD)
    generate_test_code(client, CASE, page_context="CTX-MARKER")
    assert "CTX-MARKER" in client.prompts[0]
