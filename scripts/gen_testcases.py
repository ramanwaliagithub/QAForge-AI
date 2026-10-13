"""Generate structured test cases per story and save JSON: `uv run python -m scripts.gen_testcases`."""
import json

from dotenv import load_dotenv

from ai_testgen.scenarios import STORIES_DIR, load_story
from ai_testgen.structured import GenerationError, generate_testcases
from framework.llm_client import get_client

load_dotenv()
OUT = STORIES_DIR.parent / "testcases"
OUT.mkdir(exist_ok=True)

client = get_client()
for path in sorted(STORIES_DIR.glob("*.md")):
    story = load_story(path)
    try:
        cases = generate_testcases(client, story, temperature=0.0)
    except GenerationError as e:
        print(f"{story.name:15} FAILED: {e}")
        continue
    (OUT / f"{story.name}.json").write_text(json.dumps([c.model_dump() for c in cases], indent=2) + "\n")
    kinds = ",".join(c.type for c in cases)
    print(f"{story.name:15} ok  {len(cases)} cases ({kinds})")
