"""Ask the local LLM to describe user flows from the MCP walkthrough digest: `uv run python -m scripts.mcp_describe_flows`."""
from pathlib import Path

from dotenv import load_dotenv

from framework.llm_client import get_client

load_dotenv()
digest = Path("docs/notes/day10-mcp-walkthrough.md").read_text().split("## Pages", 1)[1]
prompt = (
    "Below is a digest of every page of a web banking app (ParaBank), captured by a browser tool. "
    "Describe the main user flows a customer can perform, one bullet per flow, in plain language. "
    "Only use information present in the digest. If something is unclear from the digest, say so.\n\n" + digest
)
r = get_client().generate(prompt, system="You are a careful QA analyst.", temperature=0.0, num_ctx=8192)
out = Path("docs/notes/day10-llm-flow-summary.md")
out.write_text("# LLM-written flow summary (llama3.1:8b, from the MCP walkthrough digest)\n\n" + r.text.strip() + "\n")
print(r.text)
