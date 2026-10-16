"""Generate scenarios for every story at several temperatures: `uv run python -m scripts.gen_scenarios`."""
from dotenv import load_dotenv

from ai_testgen.scenarios import STORIES_DIR, OUTPUTS_DIR, count_scenarios, generate_scenarios, load_story
from framework.llm_client import get_client

load_dotenv()
TEMPERATURES = (0.0, 0.8)

client = get_client()
OUTPUTS_DIR.mkdir(exist_ok=True)
for path in sorted(STORIES_DIR.glob("*.md")):
    story = load_story(path)
    for temp in TEMPERATURES:
        r = generate_scenarios(client, story, temperature=temp)
        out = OUTPUTS_DIR / f"{story.name}_t{temp}.md"
        out.write_text(r.text.strip() + "\n")
        print(f"{story.name:15} T={temp}  scenarios={count_scenarios(r.text):2}  {r.latency_s:5.1f}s  -> {out}")
