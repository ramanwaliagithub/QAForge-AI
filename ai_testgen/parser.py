"""Parse and validate LLM output into TestCase objects."""
import json
import re

from pydantic import ValidationError

from ai_testgen.schema import TestCase, TestCaseList


class ParseError(ValueError):
    """The model output could not be turned into valid test cases. The message is safe to feed back to the model."""


_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


def _extract_json(text: str) -> str:
    text = text.strip()
    m = _FENCE.match(text)
    if m:
        return m.group(1)
    # Tolerate chatter around the JSON: take from the first bracket to the last matching one.
    starts = [i for i in (text.find("{"), text.find("[")) if i != -1]
    if not starts:
        raise ParseError("No JSON found in the response.")
    start = min(starts)
    end = max(text.rfind("}"), text.rfind("]"))
    return text[start : end + 1]


def parse_testcases(text: str) -> list[TestCase]:
    try:
        data = json.loads(_extract_json(text))
    except json.JSONDecodeError as e:
        raise ParseError(f"Invalid JSON: {e}") from e
    if isinstance(data, list):  # accept a bare list as well as {"test_cases": [...]}
        data = {"test_cases": data}
    try:
        return TestCaseList.model_validate(data).test_cases
    except ValidationError as e:
        problems = "; ".join(f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in e.errors()[:5])
        raise ParseError(f"JSON does not match the schema: {problems}") from e
