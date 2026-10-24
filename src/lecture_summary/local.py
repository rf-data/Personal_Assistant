"""Trusted local configuration; no API listener or production job activation."""

import json
import os
from pathlib import Path

from src.lecture_summary.models import Catalog
from src.lecture_summary.providers import MockProvider, SummaryProvider
from src.lecture_summary.service import SummaryService
from src.tools_materials.storage import RegisteredStorage


def load_service(config_path, *, offline_only=False):
    path = Path(config_path)
    config_reader = RegisteredStorage(
        {"config": {"path": str(path.parent), "readonly": True}}
    )
    config = json.loads(config_reader.read("config", path.name, maximum=65536))
    if not isinstance(config, dict) or set(config) - {
        "schema_version",
        "catalog",
        "storage_roots",
        "model",
        "allow_source_upload",
        "cache",
    }:
        raise ValueError("Unknown summary configuration field")
    if not {
        "schema_version",
        "catalog",
        "storage_roots",
    } <= config.keys() or not isinstance(config["catalog"], str):
        raise ValueError("Missing required summary configuration fields")
    if not isinstance(config.get("model", "mock-extractive-v1"), str):
        raise ValueError("Model must be an explicit string")
    if not isinstance(config.get("allow_source_upload", False), bool):
        raise ValueError("Source upload permission must be an explicit boolean")
    if type(config.get("schema_version")) is not int or config["schema_version"] != 1:
        raise ValueError("Unsupported summary configuration")
    if offline_only and config.get("model", "mock-extractive-v1") != "mock-extractive-v1":
        raise ValueError("Preflight requires the unchanged mock configuration")
    # Catalog belongs to this trusted config directory, not a widget-provided path.
    catalog = Catalog.model_validate_json(
        config_reader.read("config", config["catalog"])
    )
    storage = RegisteredStorage(config["storage_roots"])
    model = config.get("model", "mock-extractive-v1")
    if model == "mock-extractive-v1":
        provider = MockProvider()
    else:
        provider = SummaryProvider(
            model=model,
            api_key=os.environ.get("OPENAI_API_KEY", ""),
            allow_source_upload=config.get("allow_source_upload") is True,
        )
    cache = config.get("cache")
    if cache is not None and (
        not isinstance(cache, list)
        or len(cache) != 2
        or any(not isinstance(v, str) for v in cache)
    ):
        raise ValueError(
            "Cache must be [registered_storage_id, existing_relative_directory]"
        )
    return SummaryService(catalog, storage, provider, cache=cache)
