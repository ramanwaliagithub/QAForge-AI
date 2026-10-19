"""Thin client for the Playwright MCP server (`@playwright/mcp`) over stdio, using the MCP Python SDK."""
import re
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PLAYWRIGHT_MCP_ARGS = ["-y", "@playwright/mcp@latest", "--headless", "--isolated"]


@asynccontextmanager
async def playwright_mcp(extra_args: list[str] | None = None):
    """Start the server, initialise a session and yield it. The server process stops when the block exits."""
    params = StdioServerParameters(command="npx", args=PLAYWRIGHT_MCP_ARGS + (extra_args or []))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


def result_text(result) -> str:
    """Flatten a CallToolResult into plain text (images are noted, not inlined)."""
    parts = []
    for item in result.content:
        parts.append(item.text if getattr(item, "type", "") == "text" else f"[{item.type} content omitted]")
    return "\n".join(parts)


_REF = re.compile(r'^\s*- (?P<role>[\w-]+)(?: "(?P<name>[^"]*)")?(?P<attrs>(?: \[[^\]]*\])*)')
_REF_ID = re.compile(r"\[ref=(e\d+)\]")


def list_elements(snapshot: str) -> list[dict]:
    """Parse an MCP YAML snapshot into [{role, name, ref}] for every element that has a ref, in page order."""
    out = []
    for line in snapshot.splitlines():
        m = _REF.match(line)
        ref = _REF_ID.search(line)
        if m and ref:
            out.append({"role": m["role"], "name": m["name"] or "", "ref": ref.group(1)})
    return out


def find_ref(snapshot: str, role: str, name: str | None = None, nth: int = 0) -> str:
    """Ref of the nth element with `role` (and, if given, an accessible name containing `name`, case-insensitive)."""
    hits = [e for e in list_elements(snapshot)
            if e["role"] == role and (name is None or name.lower() in e["name"].lower())]
    if len(hits) <= nth:
        raise LookupError(f"No {role} {name!r} (#{nth}) in snapshot; found {len(hits)}")
    return hits[nth]["ref"]


def summarize_snapshot(snapshot: str) -> dict:
    """Short digest of a page: URL, title, headings, visible control counts, button names, plain text lines."""
    elements = list_elements(snapshot)
    url = re.search(r"- Page URL: (\S+)", snapshot)
    title = re.search(r"- Page Title: (.+)", snapshot)
    texts = [m.group(1).strip() for m in re.finditer(r"- paragraph(?: \[ref=e\d+\])?: (.+)", snapshot)]
    return {
        "url": url.group(1) if url else "",
        "title": title.group(1).strip() if title else "",
        "headings": [e["name"] for e in elements if e["role"] == "heading"],
        "textboxes": sum(e["role"] == "textbox" for e in elements),
        "comboboxes": sum(e["role"] == "combobox" for e in elements),
        "buttons": [e["name"] for e in elements if e["role"] == "button" and e["name"]],
        "text": texts[:6],
    }
