## llm_helper.py
# imports
import os
import hashlib
import json
import re
from pathlib import Path
from datetime import datetime

from openai import OpenAI
import marvin
from pydantic_ai import Agent

import src.utils.path_helper as ph
from src.core.config import folder_env_vars, agentic_env_vars
from src.core.memory import app_session
from src.llm.data_llm import LLMUsage, LLMProvider

from src.utils.dict_helper import save_dict


def log_openai_usage(usage, model: str, fn_name: str) -> LLMUsage:
    now = datetime.now().isoformat()

    usage = LLMUsage(
        provider=LLMProvider.OPENAI,
        model=model,
        fn_name=fn_name,
        timestamp=now,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        total_tokens=usage.total_tokens,
        cached_tokens=(usage.input_tokens_details.cached_tokens),
        reasoning_tokens=(usage.output_tokens_details.reasoning_tokens),
    )

    save_dict(
        data={now: usage.model_dump(mode="json")},
        path=folder_env_vars.log_dir / "llm_usage.json",
        mode="a",
    )

    return usage


def log_anthropic_usage(
    data: dict,
    model: str,
    fn_name: str,
) -> LLMUsage:

    now = datetime.now().isoformat()

    usage = data.get("usage") or {}

    input_tokens = usage.get(
        "input_tokens",
        0,
    )

    output_tokens = usage.get(
        "output_tokens",
        0,
    )

    cache_read_tokens = usage.get(
        "cache_read_input_tokens",
        0,
    )

    cache_creation_tokens = usage.get(
        "cache_creation_input_tokens",
        0,
    )

    output_details = usage.get("output_tokens_details") or {}

    reasoning_tokens = output_details.get(
        "thinking_tokens",
        0,
    )

    llm_usage = LLMUsage(
        provider=LLMProvider.ANTHROPIC,
        model=model,
        fn_name=fn_name,
        timestamp=now,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=(
            input_tokens + output_tokens
            # + cache_read_tokens
            # + cache_creation_tokens
        ),
        cached_tokens=cache_read_tokens,
        cache_creation_tokens=cache_creation_tokens,
        reasoning_tokens=reasoning_tokens,
        # Claude Code gives cost directly when available.
        total_cost_usd=data.get("total_cost_usd"),
        session_id=data.get("session_id"),
    )

    save_dict(
        data={now: llm_usage.model_dump(mode="json")},
        path=(folder_env_vars.log_dir / "llm_usage.json"),
        mode="a",
    )

    return llm_usage


def configure_marvin(
    context,
    # model: str = "openai:gpt-4o-mini",
) -> None:

    api_key = agentic_env_vars.openai_api_key

    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment.")

    os.environ["OPENAI_API_KEY"] = api_key

    llm_model = getattr(context, "llm_model", None)

    llm_context = getattr(context, "llm_context", None)
    extract_model = getattr(llm_context, "extraction_model", None)

    marvin.defaults.model = extract_model or llm_model

    Agent.instrument_all()

    return


def get_openai_client() -> OpenAI:
    # if not hasattr(_thread_local, "client"):
    client = OpenAI()
    return client


def _make_cache_key(report_text: str, prompt: str, namespace: str) -> str:
    h = hashlib.sha256()
    h.update(prompt.encode("utf-8"))
    h.update(report_text.encode("utf-8"))
    h.update(namespace.encode("utf-8"))
    return h.hexdigest()


def _load_from_cache(key: str, cache_dir: Path = None):
    logger = app_session.logger

    if not cache_dir:
        folder = folder_env_vars.cache_dir
        cache_dir = Path(f"{folder}")

    fn = cache_dir / f"{key}.json"
    ph.ensure_dir(fn)

    if fn.exists():
        with open(fn) as f:
            logger.info("Loading cached json: %s", ph.shorten_path(fn))
            return json.load(f)

    return None


def _save_to_cache(key: str, data: dict, cache_dir: Path = None):
    logger = app_session.logger

    if not cache_dir:
        cache_dir = Path(folder_env_vars.cache_dir)

    fn = cache_dir / f"{key}.json"
    ph.ensure_dir(fn)

    with open(fn, "w") as f:
        logger.info("Saving LLM response as cached json: %s", ph.shorten_path(fn))
        json.dump(data, f, indent=2)


def _clean_llm_output(text: str) -> str:
    text = text.strip()

    # remove ```json ... ```
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```", "", text)
    text = re.sub(r"```$", "", text)

    # if text.startswith("```"):
    #     text = text.split("```")[1]  # nimmt den mittleren Teil

    return text.strip()


def build_llm_aggregation_input(docs, agg):
    payload = []

    for i, doc in enumerate(docs, start=1):
        payload.append(
            {
                "document_id": i,
                "title": doc.title,
                "category": doc.category,
                "summary": doc.summary,
                "key_entities": doc.key_entities,
                "key_findings": doc.key_findings,
                "methods": doc.methods,
                "main_topics": getattr(doc, "main_topics", []),
                "mechanisms": getattr(doc, "mechanisms", []),
                "outcomes": getattr(doc, "outcomes", []),
                "missing_fields": getattr(doc, "missing_fields", []),
                "review_flags": getattr(doc, "review_flags", []),
                "quality_assessment": getattr(doc, "quality_assessment", None),
                "confidence": doc.confidence,
            }
        )

    response = {"documents": payload, "pre_aggregation": agg.model_dump()}

    return json.dumps(response, indent=2, ensure_ascii=False)


# def cached_single(texts: str) -> dict:
#     key = make_cache_key(texts,
#                         prompt,
#                         namespace)
#     cached = load_from_cache(key)
#     if cached is not None:
#         return cached

#     result = single_escalation_by_llm(
#                                     text=texts,
#                                     prompt=prompt,
#                                     scheme=scheme,
#                                     allowed_values=allowed_values,
#                                 )

#     save_to_cache(key, result)

#     return result

#     return cached_single
