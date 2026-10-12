from ai_testgen.scenarios import STORIES_DIR, Story, count_scenarios, generate_scenarios, load_prompt, load_story, render_prompt
from framework.llm_client import LLMResponse


def test_load_story_splits_story_and_criteria():
    s = load_story(STORIES_DIR / "transfer_funds.md")
    assert s.name == "transfer_funds"
    assert s.story.startswith("As a logged-in customer")
    assert "Transfer Complete!" in s.criteria
    assert "## Acceptance" not in s.story


def test_render_prompt_fills_placeholders():
    out = render_prompt(load_prompt(), Story("x", "STORY-TEXT", "CRITERIA-TEXT"))
    assert "STORY-TEXT" in out and "CRITERIA-TEXT" in out
    assert "{story}" not in out and "{criteria}" not in out


def test_all_stories_load():
    stories = [load_story(p) for p in STORIES_DIR.glob("*.md")]
    assert len(stories) >= 3
    assert all(s.story and s.criteria for s in stories)


def test_count_scenarios():
    assert count_scenarios("Scenario: a\nGiven x\n\nscenario: b\nGiven y") == 2


class FakeClient:
    def generate(self, prompt, *, temperature=0.0, **kw):
        self.prompt, self.temperature = prompt, temperature
        return LLMResponse("Scenario: t", "fake", 0.0)


def test_generate_scenarios_passes_prompt_and_temperature():
    fake = FakeClient()
    r = generate_scenarios(fake, Story("x", "S", "C"), temperature=0.8)
    assert r.text == "Scenario: t"
    assert fake.temperature == 0.8 and "S" in fake.prompt
