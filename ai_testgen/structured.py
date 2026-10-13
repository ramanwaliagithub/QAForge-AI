"""Generate structured test cases from a story, retrying when the model returns invalid JSON."""
from ai_testgen.parser import ParseError, parse_testcases
from ai_testgen.scenarios import Story, load_prompt, render_prompt
from ai_testgen.schema import TestCase
from framework.llm_client import LLMClient
from framework.logging_utils import get_logger

log = get_logger("qaforge.testgen")


class GenerationError(RuntimeError):
    """The model never produced valid test cases within the allowed attempts."""


def generate_testcases(
    client: LLMClient, story: Story, temperature: float = 0.0, max_retries: int = 2
) -> list[TestCase]:
    base_prompt = render_prompt(load_prompt("testcase_json"), story)
    prompt = base_prompt
    last_error = None
    for attempt in range(max_retries + 1):
        response = client.generate(prompt, temperature=temperature, json_mode=True)
        try:
            cases = parse_testcases(response.text)
        except ParseError as e:
            last_error = e
            log.warning("invalid_output", extra={"attempt": attempt + 1, "error": str(e)})
            # Tell the model what was wrong; a bare retry at T=0 would return the same output.
            prompt = (
                f"{base_prompt}\n\nYour previous answer was rejected: {e}\n"
                "Return corrected JSON only, in the exact shape described above."
            )
            continue
        log.info("testcases_ok", extra={"story": story.name, "attempt": attempt + 1, "count": len(cases)})
        return cases
    raise GenerationError(f"No valid test cases after {max_retries + 1} attempts: {last_error}")
