## data_llm.py
# import
from datetime import datetime

# from typing import Literal
from pydantic import BaseModel
from enum import StrEnum


class LLMProvider(StrEnum):
    OPENAI = "openAI"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class LLMUsage(BaseModel):
    provider: LLMProvider
    model: str  # =model
    fn_name: str
    timestamp: str | datetime

    input_tokens: int
    output_tokens: int
    total_tokens: int

    cached_tokens: int = 0  # bei 'anthopic' == 'cache_read_tokens'
    cache_creation_tokens: int = 0

    reasoning_tokens: int = 0

    total_cost_usd: float | None = None
    session_id: str | None = None
