"""Evidence for the unversioned alias defect; no invented discriminator tags.

Legacy declarations use the existing MAINT-04 AST harness, not an SDK import.
These are characterization tests, not a claim that RunSettings works.
"""

import json

import pytest
import yaml
from pydantic import PydanticUserError, TypeAdapter, ValidationError

from src.core import config_parsing
from tests.parsing_config_support import ROOT, legacy_models

VARIANTS = (
    "ParseHTMLSettings",
    "ParseNotebookSettings",
    "ParseMDSettings",
    "ParsePDFSettings",
    "ParsePlainTextSettings",
    "ParseURLSettings",
    "ParseWikiSettings",
    "ChunkSettings",
)


@pytest.fixture(scope="module", params=["legacy", "parsing"])
def family(request):
    return legacy_models() if request.param == "legacy" else config_parsing


def test_alias_cannot_construct_validator_or_serializer(family):
    # This fails before payload/tag lookup, even if a caller supplies meta_type.
    with pytest.raises(PydanticUserError) as error:
        TypeAdapter(family.RunSettings)
    assert error.value.code == "discriminator-no-field"
    assert "ParseHTMLSettings" in str(error.value) and "meta_type" in str(error.value)


@pytest.mark.parametrize("name", VARIANTS)
def test_untagged_variant_defaults_and_serialization_stay_valid(family, name):
    model = getattr(family, name)
    assert "meta_type" not in model.model_fields
    value = model.model_validate({})
    assert "meta_type" not in value.model_dump(mode="json")
    assert model.model_validate_json(value.model_dump_json()) == value


def test_legacy_payload_is_ambiguous_between_nominal_variants(family):
    payload = dict(save=["txt"], assemble=["md"], scrape_images=False)
    models = [
        family.ParseMDSettings,
        family.ParsePlainTextSettings,
        family.ParseURLSettings,
    ]
    values = [m.model_validate_json(json.dumps(payload)) for m in models]
    assert len({type(v) for v in values}) == 3
    assert all(v.model_dump(mode="json") == payload for v in values)
    # HTML and notebook parser strings do not identify their family either.
    assert (
        family.ParseHTMLSettings.model_validate({"parser": "synthetic"}).parser
        == family.ParseNotebookSettings.model_validate({"parser": "synthetic"}).parser
    )


def test_invented_tag_would_currently_be_discarded_or_rejected(family):
    value = family.ParseMDSettings.model_validate({"meta_type": "unrecognized"})
    assert "meta_type" not in value.model_dump()
    with pytest.raises(ValidationError) as error:
        family.ChunkSettings.model_validate({"meta_type": "chunk"})
    assert error.value.errors()[0]["type"] == "extra_forbidden"


def test_existing_invalid_variant_payloads_remain_invalid(family):
    for model, payload in (
        (family.ParsePDFSettings, {"assemble": ["unsupported"]}),
        (family.ParseWikiSettings, {"language": "unsupported"}),
        (family.ChunkSettings, {"transformer_model": "unsupported"}),
    ):
        with pytest.raises(ValidationError) as error:
            model.model_validate(payload)
        assert error.value.errors()[0]["type"] == "literal_error"


@pytest.mark.parametrize("name", ["cfg_parsing", "streamlit_run"])
def test_stored_yaml_uses_explicit_aggregate_without_discriminator(family, name):
    data = yaml.safe_load((ROOT / "configuration" / f"{name}.yaml").read_text())
    assert "meta_type" not in data
    if family is config_parsing and name == "streamlit_run":
        with pytest.raises(ValidationError, match="name_log"):
            family.ParseSettings.model_validate(data)
    else:
        value = family.ParseSettings.model_validate(data)
        assert (
            family.ParseSettings.model_validate_json(value.model_dump_json()) == value
        )
