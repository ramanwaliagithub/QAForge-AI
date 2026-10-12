"""Turn a user story into Given/When/Then test scenarios with an LLM."""
from dataclasses import dataclass
from pathlib import Path

from framework.llm_client import LLMClient, LLMResponse

PROMPTS_DIR = Path(__file__).parent / "prompts"
STORIES_DIR = Path(__file__).parent / "stories"


@dataclass
class Story:
    name: str
    story: str
    criteria: str


def load_story(path: Path) -> Story:
    """Parse a story file: `# Title`, one story paragraph, then `## Acceptance criteria`."""
    text = path.read_text()
    head, _, criteria = text.partition("## Acceptance criteria")
    lines = [ln for ln in head.splitlines() if ln.strip() and not ln.startswith("#")]
    return Story(name=path.stem, story=" ".join(lines).strip(), criteria=criteria.strip())


def load_prompt(name: str = "scenario_generation") -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text()


def render_prompt(template: str, story: Story) -> str:
    # str.replace, not str.format: prompts may contain literal braces.
    return template.replace("{story}", story.story).replace("{criteria}", story.criteria)


def generate_scenarios(client: LLMClient, story: Story, temperature: float = 0.0) -> LLMResponse:
    return client.generate(render_prompt(load_prompt(), story), temperature=temperature)


def count_scenarios(text: str) -> int:
    return sum(1 for ln in text.splitlines() if ln.strip().lower().startswith("scenario:"))
