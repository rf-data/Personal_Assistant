"""Load the real legacy model declarations without importing credential settings.

The optional pydantic-settings/SDK environment is deliberately not emulated.
This is a model contract test, not a full legacy application import smoke.
"""

import ast
import hashlib
import json
from pathlib import Path
from types import ModuleType
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parents[1]
NAMES = (
    "ParseFileSettings",
    "ParseDOCXSettings",
    "ParseHTMLSettings",
    "ParseMDSettings",
    "ParseNotebookSettings",
    "ParsePDFSettings",
    "ParsePlainTextSettings",
    "ParseURLSettings",
    "ParseWikiSettings",
    "GeneralFileSettings",
    "GenDOCXSettings",
    "GenHTMLSettings",
    "GenMDSettings",
    "GenNotebookSettings",
    "GenPDFSettings",
    "GenPlainTextSettings",
    "GenURLSettings",
    "GenWikiSettings",
    "ChunkSettings",
    "GeneralSettings",
    "ParseSettings",
)


def legacy_models():
    path = ROOT / "src/core/config.py"
    tree = ast.parse(path.read_text())
    nodes = [
        node
        for node in tree.body
        if (isinstance(node, ast.ClassDef) and node.name in NAMES)
        or (
            isinstance(node, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id in {"RunSettings", "ParseSettings_all"}
                for t in node.targets
            )
        )
        or (
            isinstance(node, ast.ImportFrom)
            and node.module == "src.core"
            and any(a.name == "_parsing_settings" for a in node.names)
        )
    ]
    module = ModuleType("src.core.config")
    module.__dict__.update(
        BaseModel=BaseModel,
        ConfigDict=ConfigDict,
        Field=Field,
        Annotated=Annotated,
        Literal=Literal,
    )
    exec(
        compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"),
        module.__dict__,
    )
    return module


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def field_contract(model):
    return {
        name: {
            "annotation": str(field.annotation),
            "required": field.is_required(),
            "alias": field.alias,
            "validation_alias": field.validation_alias,
            "serialization_alias": field.serialization_alias,
            "factory": getattr(field.default_factory, "__qualname__", None),
            "default": None if field.default_factory else repr(field.default),
        }
        for name, field in model.model_fields.items()
    }


def contract(model):
    return {
        "defaults": model().model_dump(mode="json"),
        "fields": field_contract(model),
        "validation_schema_sha256": digest(model.model_json_schema(mode="validation")),
        "serialization_schema_sha256": digest(
            model.model_json_schema(mode="serialization")
        ),
        "config": model.model_config,
    }
