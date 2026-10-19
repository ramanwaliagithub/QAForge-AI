"""Thin client for the Playwright MCP server (`@playwright/mcp`) over stdio, using the MCP Python SDK."""
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
