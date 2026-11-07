"""Small replaceable summary adapters over the existing LLMClient boundary."""

import json
import re
from dataclasses import dataclass, field
from typing import Protocol

from src.c27_learning_summary.models import SectionResponse


@dataclass
class Reply:
    raw: str
    usage: dict[str, int] = field(default_factory=dict)


class SummaryModel(Protocol):
    model: str
    provider: str

    def complete(self, messages: list[dict], *, config, timeout: float) -> Reply: ...


class FakeLLM:
    model = "fake-extractive-v1"
    provider = "fake"

    def __init__(self):
        self.calls = 0

    def complete(self, messages, *, config, timeout):
        self.calls += 1
        excerpt = json.loads(messages[-1]["content"])["excerpt"]
        text = excerpt["text"]
        category = (
            "code"
            if text.startswith(("print(", "def "))
            else ("definition" if " is " in text else "key_point")
        )
        if text.startswith("Learning objective:"):
            category = "learning_objective"
        elif text.startswith("Explanation:"):
            category = "explanation"
        elif "=" in text and re.fullmatch(r"[\d\s+*/=().-]+", text):
            category = "formula"
        response = SectionResponse(
            claims=[
                dict(
                    category=category,
                    text=text,
                    refs=[excerpt["ref_id"]],
                    topic=text.split(" is ")[0][:200]
                    if category == "definition"
                    else "",
                )
            ]
        )
        return Reply(
            response.model_dump_json(), {"input_tokens": 0, "output_tokens": 0}
        )
