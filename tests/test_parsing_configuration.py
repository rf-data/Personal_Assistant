"""MAINT-03B parsing contracts frozen before consolidating field declarations."""

import importlib
import json
import pickle
import subprocess
import sys

import pytest
import yaml
from pydantic import PydanticUserError, TypeAdapter, ValidationError

from src.core import config_parsing
from tests.parsing_config_support import NAMES, ROOT, contract, legacy_models

BASELINE = json.loads(
    (ROOT / "tests/fixtures/parsing_config/maint03b_contracts.json").read_text()
)


@pytest.fixture(scope="module", params=["legacy", "parsing"])
def family(request):
    return (
        request.param,
        legacy_models() if request.param == "legacy" else config_parsing,
    )


@pytest.mark.parametrize("name", NAMES)
def test_frozen_contract(family, name):
    key, module = family
    model = getattr(module, name)
    assert contract(model) == BASELINE[key][name]
    assert list(model.model_fields) == list(BASELINE[key][name]["fields"])
    assert model().model_dump_json() == json.dumps(
        BASELINE[key][name]["defaults"], ensure_ascii=False, separators=(",", ":")
    )
    assert model.__name__ == model.__qualname__ == name
    assert (
        model.__module__
        == f"src.core.{'config' if key == 'legacy' else 'config_parsing'}"
    )
    assert model.model_validate(model()) is not None
    assert model.model_validate_json(model().model_dump_json()) == model()
    assert model.model_validate(model().model_dump()) == model()
    assert not model().model_dump(exclude_unset=True)
    # No user validators/serializers or aliases in this contract.
    decorators = model.__pydantic_decorators__
    assert not any(
        (
            decorators.validators,
            decorators.field_validators,
            decorators.root_validators,
            decorators.model_validators,
            decorators.field_serializers,
            decorators.model_serializers,
        )
    )


@pytest.mark.parametrize("name", NAMES)
def test_null_missing_extra_and_mutable_defaults(family, name):
    key, module = family
    model = getattr(module, name)
    schema = model.model_json_schema()
    for field, definition in schema["properties"].items():
        allows_null = (
            definition.get("type") == "null"
            or None in definition.get("enum", [])
            or any(part.get("type") == "null" for part in definition.get("anyOf", []))
        )
        if allows_null:
            instance = model.model_validate({field: None})
            assert instance.model_dump(exclude_unset=True) == {field: None}
        else:
            with pytest.raises(ValidationError):
                model.model_validate({field: None})
        assert not model.model_fields[field].is_required()
    if model.model_config.get("extra") == "forbid":
        with pytest.raises(ValidationError, match="extra_forbidden"):
            model.model_validate({"unknown": 1})
    else:
        assert "unknown" not in model.model_validate({"unknown": 1}).model_dump()
    one, two = model(), model()
    for field, value in one.__dict__.items():
        if isinstance(value, list):
            value.append("mutated")
            assert getattr(two, field) == BASELINE[key][name]["defaults"][field]


@pytest.mark.parametrize("name", NAMES)
def test_family_identity_is_preserved(name):
    legacy, parsing = getattr(legacy_models(), name), getattr(config_parsing, name)
    assert legacy is not parsing
    for target, other in ((legacy, parsing), (parsing, legacy)):
        assert not isinstance(other(), target)
        with pytest.raises(ValidationError, match="model_type"):
            target.model_validate(other())


def test_differences_and_lossy_conversion_are_explicit():
    legacy = legacy_models()
    old = legacy.ParseSettings(name_log="kept", name_logfile="retained")
    with pytest.raises(ValidationError, match="extra_forbidden"):
        config_parsing.ParseSettings.model_validate(old.model_dump())
    flags = {"classify_header_footer", "classify_foot_notes", "classify_headings"}
    assert flags <= config_parsing.ParsePDFSettings.model_fields.keys()
    assert not flags & legacy.ParsePDFSettings.model_fields.keys()
    assert (
        legacy.ParsePDFSettings.model_validate(dict.fromkeys(flags, False))
        == legacy.ParsePDFSettings()
    )
    assert all(getattr(config_parsing.ParsePDFSettings(), flag) for flag in flags)
    # Same dump default, different schema/default-factory semantics.
    assert legacy.ParsePDFSettings.model_fields["extraction_model"].default == ""
    assert (
        config_parsing.ParsePDFSettings.model_fields["extraction_model"].default_factory
        is str
    )


def test_inheritance_and_nested_identity(family):
    _, module = family
    for name in NAMES:
        if name.startswith("Parse") and name not in {
            "ParseFileSettings",
            "ParseSettings",
        }:
            assert issubclass(getattr(module, name), module.ParseFileSettings)
        if name.startswith("Gen") and name not in {
            "GeneralFileSettings",
            "GeneralSettings",
        }:
            assert issubclass(getattr(module, name), module.GeneralFileSettings)
    for root in (module.ParseSettings, module.GeneralSettings):
        for field in (
            "docx",
            "html",
            "json_nb",
            "md",
            "pdf",
            "plain_text",
            "url",
            "wiki",
        ):
            value = getattr(root(), field)
            assert type(value) is root.model_fields[field].annotation
            assert type(value).__module__ == module.__name__
        one, two = root(), root()
        one.pdf.__dict__[next(iter(type(one.pdf).model_fields))].append("mutation")
        assert one.pdf != two.pdf


def test_coercion_literals_errors_and_assignment(family):
    _, module = family
    assert module.ParseFileSettings(
        scrape_images="false", save=(True, "md")
    ).model_dump() == {
        "save": [True, "md"],
        "assemble": None,
        "scrape_images": False,
    }
    assert module.ParseSettings(file_id="7", page_range=["2", "1"]).page_range == [2, 1]
    assert module.ParseWikiSettings(page_id=["3"], max_retries="-1").max_retries == -1
    assert module.GenPDFSettings(width_thresh="0.45").width_thresh == 0.45
    for model, payload in (
        (module.ParseFileSettings, {"save": ["pdf"]}),
        (module.ParseDOCXSettings, {"tbl_text_mode": "wide"}),
        (module.ParseWikiSettings, {"language": "fr"}),
        (module.ChunkSettings, {"transformer_model": "unknown"}),
        (module.ParseSettings, {"page_range": "1-3"}),
    ):
        with pytest.raises(ValidationError):
            model.model_validate(payload)
    # Assignment validation remains disabled on settings.
    settings = module.ParseSettings()
    settings.file_id = "historically-unvalidated"
    assert settings.file_id == "historically-unvalidated"


@pytest.mark.parametrize(
    "file", ["cfg_parsing", "streamlit_run", "cfg_general", "streamlit_general"]
)
def test_tracked_historical_yaml(family, file):
    key, module = family
    data = yaml.safe_load((ROOT / "configuration" / f"{file}.yaml").read_text())
    model = module.GeneralSettings if "general" in file else module.ParseSettings
    if key == "parsing" and file == "streamlit_run":
        with pytest.raises(ValidationError, match="name_log"):
            model.model_validate(data)
    else:
        loaded = model.model_validate(data)
        assert model.model_validate_json(loaded.model_dump_json()) == loaded
        if file == "cfg_parsing":
            assert (getattr(loaded.pdf, "classify_header_footer", None) is False) == (
                key == "parsing"
            )
            assert not hasattr(loaded.wiki, "article_to_parse")


def test_stored_json_payloads(family):
    key, module = family
    payloads = json.loads(
        (ROOT / "tests/fixtures/parsing_config/legacy_payloads.json").read_text()
    )
    for item in payloads:
        model = getattr(module, item["model"])
        if key in item.get("reject", []):
            with pytest.raises(ValidationError):
                model.model_validate_json(json.dumps(item["payload"]))
        else:
            value = model.model_validate_json(json.dumps(item["payload"]))
            assert model.model_validate_json(value.model_dump_json()) == value


def test_broken_discriminated_alias_stays_visible(family):
    _, module = family
    with pytest.raises(PydanticUserError, match="meta_type"):
        TypeAdapter(module.RunSettings)


def test_parsing_import_is_sdk_and_settings_free(tmp_path):
    code = """
import importlib.abc, sys
class Guard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, *args):
        if fullname in {"src.core.config", "src.core.memory", "pydantic_settings", "tiktoken", "docling"}:
            raise AssertionError(fullname)
sys.meta_path.insert(0, Guard())
sys.path.insert(0, sys.argv[1])
from src.core.config_parsing import ParseSettings
assert ParseSettings().pdf.classify_headings is True
"""
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", code, str(ROOT)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert importlib.import_module("src.core.config_parsing") is config_parsing


@pytest.mark.parametrize("name", NAMES)
def test_public_parsing_pickle_identity(name):
    model = getattr(config_parsing, name)
    restored = pickle.loads(pickle.dumps(model()))
    assert type(restored) is model
    assert restored == model()
