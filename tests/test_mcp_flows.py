from ai_testgen.mcp_flows import account_options, page_texts

SNAP = """- heading "Transfer Funds" [level=1] [ref=e7]
- combobox [ref=e9]:
  - option "13677" [selected]
  - option "13788"
- combobox [ref=e10]:
  - option "13677" [selected]
  - option "13788"
- paragraph [ref=e11]: Experience the difference
- paragraph [ref=e12]: Welcome Mcp Tester
- heading "Account Services" [level=2] [ref=e13]
- heading "Error!" [level=1] [ref=e14]
- paragraph [ref=e15]: An internal error has occurred and has been logged.
- text: "Amount: $"
- cell "|"
- paragraph [ref=e16]: |
"""


def test_account_options_dedupes_and_ignores_non_numeric():
    assert account_options(SNAP) == ["13677", "13788"]
    assert account_options('- option "CHECKING"') == []


def test_page_texts_drops_chrome():
    assert page_texts(SNAP) == ["Transfer Funds", "Error!", "An internal error has occurred and has been logged.", "Amount: $"]
