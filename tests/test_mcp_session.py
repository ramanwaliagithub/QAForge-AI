import pytest

from ai_testgen.mcp_session import find_ref, list_elements, summarize_snapshot

SNAP = """### Page
- Page URL: http://localhost:8080/parabank/openaccount.htm
- Page Title: ParaBank | Open Account
### Snapshot
```yaml
- generic [ref=e1]:
  - heading "Open New Account" [level=1] [ref=e7]
  - paragraph [ref=e8]: What type of Account would you like to open?
  - link "Register" [ref=e43] [cursor=pointer]:
    - /url: register.htm
  - link "Log Out" [ref=e44] [cursor=pointer]
  - textbox [ref=e50]
  - textbox [ref=e51]
  - combobox [ref=e52]:
    - option "CHECKING" [selected]
  - button "Open New Account" [ref=e53]
```"""


def test_list_elements_only_includes_elements_with_refs():
    els = list_elements(SNAP)
    assert {"role": "link", "name": "Register", "ref": "e43"} in els
    assert all(e["ref"].startswith("e") for e in els)
    assert not any(e["role"] == "option" for e in els)  # options carry no ref


def test_find_ref_by_name_case_insensitive_and_by_order():
    assert find_ref(SNAP, "link", "register") == "e43"
    assert find_ref(SNAP, "textbox", nth=1) == "e51"


def test_find_ref_missing_raises():
    with pytest.raises(LookupError):
        find_ref(SNAP, "link", "Transfer Funds")


def test_summarize_snapshot():
    s = summarize_snapshot(SNAP)
    assert s["url"].endswith("openaccount.htm") and s["title"] == "ParaBank | Open Account"
    assert s["headings"] == ["Open New Account"] and s["textboxes"] == 2 and s["comboboxes"] == 1
    assert s["buttons"] == ["Open New Account"] and s["text"] == ["What type of Account would you like to open?"]


def test_frame_prefixed_refs_and_active_attribute():
    snap = '- textbox [active] [ref=f1e34]\n- paragraph [ref=f1e40]: Hello\n- link "Register" [ref=f1e43] [cursor=pointer]'
    assert find_ref(snap, "textbox") == "f1e34"
    assert find_ref(snap, "link", "Register") == "f1e43"
    assert summarize_snapshot(snap)["text"] == ["Hello"]
