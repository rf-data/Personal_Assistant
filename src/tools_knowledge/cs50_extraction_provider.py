"""Optional bounded extraction adapters, using the existing prompt and result model."""

import json
import time

import httpx

from src.agent.prompts.prompt_know_extract import build_knowledge_extraction_prompt
from src.model_knowledge.data_knowledge import ChunkKnowledgeResult

ENDPOINT = "https://api.openai.com/v1/chat/completions"


def messages_for(chunk):
    return [
        {"role": "system", "content": build_knowledge_extraction_prompt()},
        {
            "role": "user",
            "content": json.dumps(
                {
                    "target_chunk": chunk.text,
                    "previous_context": chunk.previous_context,
                    "next_context": chunk.next_context,
                    "instruction": "Return only JSON matching this result schema. Do not invent evidence.",
                    "schema": ChunkKnowledgeResult.model_json_schema(),
                },
                ensure_ascii=False,
            ),
        },
    ]


class RequestBudget:
    def __init__(
        self, maximum=1, token_budget=60000, input_limit=28000, output_limit=1200
    ):
        if (
            maximum not in (1, 2)
            or not 1 <= token_budget <= 64000
            or not 1 <= input_limit <= 30000
            or not 1 <= output_limit <= 2000
        ):
            raise ValueError("Invalid request/token limits")
        self.maximum, self.token_budget = maximum, token_budget
        self.input_limit, self.output_limit = input_limit, output_limit
        self.requests = 0
        self.reserved = 0
        self.chunk_attempted = False

    def begin_chunk(self):
        self.chunk_attempted = False

    def claim(self, payload):
        # Conservative UTF-8 byte bound, including generous chat framing overhead.
        bound = len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) + 2048
        if (
            bound > self.input_limit
            or self.reserved + bound + self.output_limit > self.token_budget
        ):
            raise ValueError("Input/total token budget exceeded before request")
        if self.chunk_attempted or self.requests >= self.maximum:
            raise RuntimeError("Request budget exhausted; retries disabled")
        self.requests += 1
        self.chunk_attempted = True
        self.reserved += bound + self.output_limit
        return bound


def validate_response(body):
    choices = body.get("choices", [])
    if len(choices) != 1 or choices[0].get("finish_reason") != "stop":
        raise ValueError("Missing, truncated or refused LLM completion")
    message = choices[0]["message"]
    if message.get("refusal") or not isinstance(message.get("content"), str):
        raise ValueError("LLM refused or omitted JSON content")
    return ChunkKnowledgeResult.model_validate_json(message["content"])


class OpenAIHTTPProvider:
    def __init__(self, *, api_key, model, budget, transport=None):
        if not api_key:
            raise ValueError("Explicit OPENAI_API_KEY is required")
        self.model, self.budget = model, budget
        self.client = httpx.Client(
            transport=transport,
            timeout=20,
            trust_env=False,
            follow_redirects=False,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    def extract(self, chunk, record):
        payload = {
            "model": self.model.removeprefix("openai:"),
            "messages": messages_for(chunk),
            "response_format": {"type": "json_object"},
            "max_completion_tokens": self.budget.output_limit,
            "n": 1,
            "store": False,
        }
        self.budget.begin_chunk()
        record["input_token_upper_bound"] = self.budget.claim(payload)
        started = time.monotonic()
        try:
            response = self.client.post(ENDPOINT, json=payload)
            record["http_status"] = response.status_code
            if response.status_code != 200:
                # Do not persist raw response bodies or credentials.
                raise ValueError(f"LLM HTTP {response.status_code}; no retry")
            body = response.json()
            record["usage"] = body.get("usage")
            record["response_model"] = body.get("model")
            return validate_response(body)
        finally:
            record["runtime_seconds"] = time.monotonic() - started

    def close(self):
        self.client.close()


class MarvinProvider:
    """Default legacy provider, loaded only in an explicitly authorized worker."""

    def __init__(self, *, api_key, model, budget):
        import marvin
        from openai import AsyncOpenAI
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.openai import OpenAIProvider

        self.budget, self.record = budget, None
        owner = self

        class LimitedTransport(httpx.AsyncBaseTransport):
            def __init__(self):
                self.inner = httpx.AsyncHTTPTransport(retries=0)

            async def handle_async_request(self, request):
                if str(request.url) != ENDPOINT or request.method != "POST":
                    raise RuntimeError("Unexpected Marvin API endpoint")
                payload = json.loads(request.content)
                payload["max_completion_tokens"] = budget.output_limit
                payload.pop("max_tokens", None)
                payload["n"] = 1
                payload["store"] = False
                owner.record["input_token_upper_bound"] = budget.claim(payload)
                constrained = httpx.Request(
                    "POST",
                    ENDPOINT,
                    headers=request.headers,
                    content=json.dumps(payload).encode(),
                    extensions=request.extensions,
                )
                # Request body length changed; let HTTPX compute it.
                constrained.headers["Content-Length"] = str(len(constrained.content))
                response = await self.inner.handle_async_request(constrained)
                await response.aread()
                owner.record["http_status"] = response.status_code
                if response.status_code != 200:
                    raise ValueError(f"Marvin HTTP {response.status_code}; no retry")
                owner.record["usage"] = response.json().get("usage")
                owner.record["response_model"] = response.json().get("model")
                return response

            async def aclose(self):
                await self.inner.aclose()

        self.client = AsyncOpenAI(
            api_key=api_key,
            max_retries=0,
            timeout=20,
            http_client=httpx.AsyncClient(
                transport=LimitedTransport(), timeout=20, trust_env=False
            ),
        )
        marvin.defaults.model = OpenAIChatModel(
            model.removeprefix("openai:"),
            provider=OpenAIProvider(openai_client=self.client),
        )
        marvin.defaults.agent.model_settings = {"max_tokens": budget.output_limit}

    def extract(self, chunk, record):
        from src.tools_knowledge.find_knowledge import extract_knowledge

        self.budget.begin_chunk()
        self.record = record
        started = time.monotonic()
        try:
            return ChunkKnowledgeResult.model_validate(
                extract_knowledge(
                    chunk.text, chunk.previous_context, chunk.next_context
                )
            )
        finally:
            record["runtime_seconds"] = time.monotonic() - started

    def close(self):
        import asyncio

        asyncio.run(self.client.close())
