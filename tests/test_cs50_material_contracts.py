import json

import pytest
from pydantic import ValidationError

from src.model_discovery.cs50 import ResourceCandidate
from src.model_materials.materials import (
    MaterialResource,
    NormalizedDocument,
    ParserConfig,
)


def binding():
    r = ResourceCandidate(
        course_id="cs50x",
        role="notes",
        original_url="https://cs50.harvard.edu/x/notes/0/",
        section_keys=("0", "ai"),
    )
    return MaterialResource(
        resource=r,
        original_url=str(r.original_url),
        role="notes",
        format="html",
        lecture_ids=("lecture:checked",),
    )


def test_roundtrip_and_original_identity():
    b = binding()
    d = NormalizedDocument(
        binding=b, raw_sha256="a" * 64, parser=ParserConfig(name="html"), blocks=()
    )
    assert NormalizedDocument.model_validate_json(d.model_dump_json()) == d
    assert b.resource.section_keys == ("0", "ai")
    assert b.source_id == b.resource.resource_id
    assert b.material_id != b.source_id
    assert json.loads(d.model_dump_json())["schema_version"] == 1


@pytest.mark.parametrize(
    "change",
    [{"original_url": "https://example.org/"}, {"language": "en"}, {"role": "slides"}],
)
def test_provenance_conflicts(change):
    with pytest.raises(ValidationError):
        MaterialResource.model_validate(binding().model_dump() | change)
