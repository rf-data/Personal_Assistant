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


class LiteLLMSummaryModel:
    provider = "litellm"

    def __init__(self, model):
        self.model = model

    def complete(self, messages, *, config, timeout):
        from src.llm.model_litellm import LLMClient

        client = LLMClient.bounded(model=self.model, temperature=config.temperature)
        response = client.completion(
            messages=messages,
            response_format={"type": "json_object"},
            max_tokens=config.max_output_tokens,
            timeout=timeout,
            num_retries=0,
        )
        if len(response.choices) != 1 or response.choices[0].finish_reason != "stop":
            raise ValueError("Truncated or refused response")
        message = response.choices[0].message
        if getattr(message, "refusal", None) or not isinstance(message.content, str):
            raise ValueError("Missing or refused content")
        usage = getattr(response, "usage", None)
        known = {}
        for name, field_name in (
            ("input_tokens", "prompt_tokens"),
            ("output_tokens", "completion_tokens"),
        ):
            value = (
                usage.get(field_name)
                if isinstance(usage, dict)
                else getattr(usage, field_name, None)
            )
            if type(value) is int and value >= 0:
                known[name] = value
        return Reply(
            message.content,
            known,
        )
