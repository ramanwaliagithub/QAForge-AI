import subprocess
from pathlib import Path

import pytest

from framework.healing.patching import PatchRefused, apply_plan, check_clean, locate, plan_patch

PAGE = '''class TransferPage:
    @property
    def amount(self):
        return self.page.locator("#amt")

    @property
    def submit(self):
        return self.page.get_by_role("button", name="Transfer Money", exact=True)

    def field(self, name):
        return self.page.locator(f"input[name='{name}']")
'''


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "pages").mkdir()
    (tmp_path / "pages" / "transfer.py").write_text(PAGE)
    return tmp_path


def plan(repo, old, new):
    return plan_patch(old, new, roots=("pages",), repo_root=repo)


def test_plan_changes_exactly_one_line_and_shows_a_diff(repo):
    p = plan(repo, 'locator("#amt")', 'locator("#amount")')
    assert (p.file, p.line) == ("pages/transfer.py", 4)
    assert p.old_line.strip() == 'return self.page.locator("#amt")' and p.new_line.strip() == 'return self.page.locator("#amount")'
    assert '-        return self.page.locator("#amt")' in p.diff and '+        return self.page.locator("#amount")' in p.diff
    assert p.new_content.count("\n") == PAGE.count("\n"), "no lines added or removed"
    assert (repo / "pages" / "transfer.py").read_text() == PAGE, "planning must not write"


def test_role_locator_is_patched_too(repo):
    p = plan(repo, 'get_by_role("button", name="Transfer Money", exact=True)', 'get_by_role("button", name="Transfer", exact=True)')
    assert p.line == 8 and 'name="Transfer", exact=True' in p.new_line


@pytest.mark.parametrize("old, code", [
    ('locator("#not-there")', "no_match"),
    ("locator(\"input[name='customer.firstName']\")", "no_match"),  # built from an f-string at run time
    ("", "incomplete"),
])
def test_refuses_when_there_is_no_literal_match(repo, old, code):
    with pytest.raises(PatchRefused) as e:
        plan(repo, old, 'locator("#x")')
    assert e.value.code == code


def test_refuses_an_ambiguous_match(repo):
    (repo / "pages" / "other.py").write_text('class O:\n    x = self.page.locator("#amt")\n')
    with pytest.raises(PatchRefused) as e:
        plan(repo, 'locator("#amt")', 'locator("#amount")')
    assert e.value.code == "ambiguous" and "pages/other.py:2" in str(e.value) and "pages/transfer.py:4" in str(e.value)


def test_refuses_when_the_locator_is_on_one_line_twice(repo):
    (repo / "pages" / "twice.py").write_text('x = (self.page.locator("#q"), self.page.locator("#q"))\n')
    with pytest.raises(PatchRefused) as e:
        plan(repo, 'locator("#q")', 'locator("#r")')
    assert e.value.code == "multiple_on_line"


def test_a_replacement_that_breaks_the_syntax_is_refused(repo):
    with pytest.raises(PatchRefused) as e:
        plan(repo, 'locator("#amt")', 'locator("#amount"')  # unbalanced parenthesis
    assert e.value.code == "syntax_error"


def test_single_quoted_source_is_matched_and_keeps_its_quote_style(repo):
    (repo / "pages" / "single.py").write_text("class S:\n    a = self.page.locator('#old')\n")
    p = plan(repo, 'locator("#old")', 'locator("#new")')
    assert p.new_line.strip() == "a = self.page.locator('#new')"


def test_locate_reports_every_literal_hit(repo):
    hits = locate('locator("#amt")', roots=("pages",), repo_root=repo)
    assert [(h["file"], h["line"]) for h in hits] == [("pages/transfer.py", 4)]


def test_apply_writes_the_planned_content_atomically_and_leaves_no_temp_files(repo):
    p = plan(repo, 'locator("#amt")', 'locator("#amount")')
    apply_plan(p, repo)
    assert (repo / "pages" / "transfer.py").read_text() == p.new_content
    assert [f.name for f in (repo / "pages").iterdir()] == ["transfer.py"]


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args], check=True, capture_output=True)


def test_dirty_files_and_non_repos_are_refused(repo):
    with pytest.raises(PatchRefused) as e:
        check_clean("pages/transfer.py", repo)  # not a git repository at all
    assert e.value.code == "not_a_git_repo"
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    check_clean("pages/transfer.py", repo)  # clean: fine
    (repo / "pages" / "transfer.py").write_text(PAGE + "# local edit\n")
    with pytest.raises(PatchRefused) as e:
        check_clean("pages/transfer.py", repo)
    assert e.value.code == "dirty"
