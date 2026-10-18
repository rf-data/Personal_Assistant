"""Small deterministic DTO/redaction/cursor contracts without a server."""

import base64
import json
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.content_store.models import (
    ContentBlock,
    ContentLocator,
    RawArtifact,
    RawManifest,
)
from src.content_store.read_models import ContentReadSettings, TextWindow
from src.content_store.read_views import locators, public_url, structure, warnings
from src.content_store.reader import ContentReader, Cursor, ReadFault


@pytest.mark.parametrize(
    "url",
    [
        "file:///home/private/file",
        "javascript:alert(1)",
        "https://user:secret@example.com/",
        "https://example.com/?token=secret",
        "https://[invalid",
        "/private/file",
    ],
)
def test_unsafe_provenance_urls_are_null(url):
    assert public_url(url) is None


def test_public_url_and_unknown_time_locator_projection():
    assert (
        public_url("https://cs50.harvard.edu/python/")
        == "https://cs50.harvard.edu/python/"
    )
    ref = RawArtifact(sha256="a" * 64, size_bytes=10, mime_type="text/plain")
    version = SimpleNamespace(
        source_id="resource:example",
        source_version_id="source:example",
        manifest=RawManifest(artifacts=(ref,)),
    )
    original = ContentLocator(
        raw_artifact_sha256=ref.sha256,
        origin_pointer="/blocks/0",
        time_status="unknown",
        chapter_path=("Chapter 1", "/home/private/file"),
        dom="/private/internal",
        coordinate_system="/private/unknown",
    )
    block = ContentBlock(
        block_id="block:example",
        order=0,
        type="paragraph",
        original_type="paragraph",
        payload_pointer="/blocks/0",
        text="example",
        locators=(original,),
    )
    projected = locators(block, version)[0]
    assert (
        projected.time_status == "unknown" and projected.start is projected.end is None
    )
    assert projected.chapter_path == ("Chapter 1",) and projected.dom is None
    assert projected.coordinate_system == "unknown"
    assert projected.raw_reference.source_id == version.source_id


@pytest.mark.parametrize(
    "kind,data,expected",
    [
        (
            "table",
            {
                "rows": [["literal /home/path", None, "∑"]],
                "private_file": "/private/secret",
            },
            {"rows": [["literal /home/path", None, "∑"]]},
        ),
        (
            "formula",
            {"latex": r"x^2+y^2=z^2", "source_markup": "<script>bad</script>"},
            {"latex": r"x^2+y^2=z^2"},
        ),
        (
            "image_reference",
            {
                "image_id": "image:abc",
                "artifact_path": "/private/picture",
                "source_reference": "file:///secret",
            },
            {"image_id": "image:abc"},
        ),
        (
            "code",
            {
                "language": "python",
                "source_path": "/private/code.py",
                "code_view": "print('é')\r\n",
            },
            {"language": "python", "code_view": "print('é')\r\n"},
        ),
    ],
)
def test_structure_allowlist_keeps_content_not_private_metadata(kind, data, expected):
    block = SimpleNamespace(type=kind, data=data)
    view, redacted = structure(block)
    assert view == expected and redacted


def test_dtos_reject_schema_extra_fields_and_ambiguous_times(tmp_path):
    with pytest.raises(ValidationError):
        ContentReadSettings(
            root=tmp_path / "content",
            cursor_key_file=tmp_path / "key",
            schema_version=2,
        )
    with pytest.raises(ValidationError):
        ContentReadSettings(
            root=tmp_path / "content", cursor_key_file=tmp_path / "content/key"
        )
    value = dict(
        parsed_version_id="version:1",
        block_id="block:1",
        start=0,
        end=0,
        text_length=0,
        text_sha256="a" * 64,
        text="",
    )
    assert TextWindow(**value).schema_version == 1
    with pytest.raises(ValidationError):
        TextWindow(**value, schema_version=2)
    with pytest.raises(ValidationError):
        TextWindow(**value, private_path="/private")
    with pytest.raises(ValidationError):
        ContentLocator(
            raw_artifact_sha256="a" * 64,
            origin_pointer="/blocks/0",
            time_status="unknown",
            start=0,
            end=1,
        )


def test_cursor_binds_hidden_revisions_and_has_no_keys_or_tokens():
    reader = object.__new__(ContentReader)
    reader.key = b"synthetic-cursor-contract-key!!123"
    snapshot = reader._snapshot((3, 17))
    cursor = Cursor(
        actor="a" * 64,
        request="b" * 64,
        snapshot=snapshot,
        acl_revision=2,
        last=("resource:example",),
    )
    token = reader._encode_cursor(cursor)
    assert reader._decode_cursor(token) == cursor
    decoded = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))[:-32]
    fields = json.loads(decoded)
    assert "max_publication_seq" not in fields and "collection_revision" not in fields
    assert reader.key not in decoded and "token" not in fields
    assert snapshot != reader._snapshot((4, 17)) and snapshot != reader._snapshot(
        (3, 18)
    )
    with pytest.raises(ReadFault):
        reader._decode_cursor(token[:-1] + ("A" if token[-1] != "A" else "B"))


def test_quality_warnings_exclude_messages_and_are_block_scoped():
    quality = {
        "inputs": {"raw": "/private/raw"},
        "findings": [
            dict(
                code="page_coverage",
                severity="warning",
                category="semantic_review",
                block_id="block:1",
                message="/private/source",
            ),
            dict(
                code="other",
                severity="warning",
                category="technical",
                block_id="block:2",
            ),
        ],
    }
    view = warnings(quality, "block:1")
    assert (
        len(view) == 1 and view[0].code == "page_coverage" and view[0].occurrences == 1
    )
    assert "private" not in view[0].model_dump_json()
