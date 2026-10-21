"""Reusable ParaBank flows driven through a Playwright MCP session (registration, accounts, reading results)."""
import re

from ai_testgen.mcp_session import find_ref, result_text

CHROME_TEXT = ("Experience the difference", "Welcome ", "© Parasoft", "Username", "Password")


class McpActionError(RuntimeError):
    """The MCP server reported an error for a tool call."""


async def act(session, tool: str, args: dict) -> str:
    """Call a tool, then return a fresh snapshot of the page (the server only returns a file path after actions)."""
    res = result_text(await session.call_tool(tool, args))
    if res.lstrip().startswith("### Error"):
        raise McpActionError(f"{tool} {args}: {res[:300]}")
    return result_text(await session.call_tool("browser_snapshot", {}))


async def goto(session, url: str, settle_s: float = 1.0) -> str:
    """Navigate and wait briefly: ParaBank fills its account dropdowns asynchronously."""
    await act(session, "browser_navigate", {"url": url})
    await session.call_tool("browser_wait_for", {"time": settle_s})
    return result_text(await session.call_tool("browser_snapshot", {}))


def account_options(snapshot: str) -> list[str]:
    """Account ids offered in the page's dropdowns (all-numeric options), de-duplicated, in order."""
    seen = []
    for m in re.finditer(r'- option "(\d+)"', snapshot):
        if m.group(1) not in seen:
            seen.append(m.group(1))
    return seen


def page_texts(snapshot: str) -> list[str]:
    """Meaningful visible text of the content area: headings, paragraphs and error spans, without page chrome."""
    texts = []
    for m in re.finditer(r'- (?:heading "([^"]+)"|paragraph(?: \[ref=\w*?e\d+\])?: (.+)|text: (.+)|cell "([^"]+)")', snapshot):
        t = next(g for g in m.groups() if g).strip().strip('"')
        if t and re.search(r"\w", t) and not any(t.startswith(c) for c in CHROME_TEXT) and t not in ("Account Services", "Customer Login", "Latest News"):
            texts.append(t)
    return texts


REGISTER_FIELDS = ["First Name", "Last Name", "Address", "City", "State", "Zip Code", "Phone #", "SSN",
                   "Username", "Password", "Confirm"]


async def register(session, base_url: str, username: str, password: str = "Passw0rd!") -> str:
    """Register a customer through the UI (and so log in). Returns the snapshot after registration."""
    snap = await goto(session, f"{base_url}/index.htm", settle_s=0.2)
    snap = await act(session, "browser_click", {"target": find_ref(snap, "link", "Register")})
    values = ["Mcp", "Tester", "1 Test Street", "Testville", "CA", "90210", "5550100", "123-45-6789", username, password, password]
    # two login textboxes come first on the page, then the 11 registration fields
    fields = [{"name": n, "type": "textbox", "target": find_ref(snap, "textbox", nth=i + 2), "value": v}
              for i, (n, v) in enumerate(zip(REGISTER_FIELDS, values))]
    snap = await act(session, "browser_fill_form", {"fields": fields})
    return await act(session, "browser_click", {"target": find_ref(snap, "button", "Register")})


async def open_account(session, base_url: str, account_type: str = "SAVINGS") -> list[str]:
    """Open an extra account; returns the account ids now offered by the dropdowns."""
    snap = await goto(session, f"{base_url}/openaccount.htm")
    combos = [find_ref(snap, "combobox", nth=0)]
    await act(session, "browser_select_option", {"target": combos[0], "values": [account_type]})
    snap = await goto(session, f"{base_url}/openaccount.htm")
    await act(session, "browser_click", {"target": find_ref(snap, "button", "Open New Account")})
    await session.call_tool("browser_wait_for", {"time": 1})
    return account_options(await goto(session, f"{base_url}/transfer.htm"))
