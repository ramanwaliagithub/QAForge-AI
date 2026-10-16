"""Structured test case schema. The LLM must return JSON that validates against these models."""
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TestCase(BaseModel):
    __test__ = False  # not a pytest class, despite the name

    title: str = Field(min_length=3)
    type: Literal["happy", "negative", "edge"] = "happy"
    priority: Literal["high", "medium", "low"] = "medium"
    preconditions: str = ""
    steps: list[str] = Field(min_length=1)
    expected: str = Field(min_length=1)

    @field_validator("type", "priority", mode="before")
    @classmethod
    def _lowercase(cls, v):
        # Models often return "Happy" or "HIGH"; normalise rather than fail.
        return v.strip().lower() if isinstance(v, str) else v


class TestCaseList(BaseModel):
    __test__ = False

    test_cases: list[TestCase] = Field(min_length=1)
