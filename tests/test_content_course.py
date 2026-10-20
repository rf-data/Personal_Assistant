"""Additive course contracts and actual synthetic ACL/FTS persistence roundtrip."""

import json
from typing import get_args

import pytest
from pydantic import TypeAdapter, ValidationError

from src.content_store._testing import (
    initialize_synthetic_store,
    publish_synthetic,
    register_synthetic_version,
    synthetic_content_index,
)
from src.content_store.errors import Forbidden
from src.content_store.models import (
    RawArtifact,
    RawManifest,
    SourceGrant,
    SourceRegistration,
)
from src.content_store.read_models import ContentReadSettings, SourceDTO
from src.content_store.reader import ContentReader
from src.content_store.store import ContentStore
from src.evaluation_store.models import DatasetBinding
from src.job_control.models import PlanningParams, Principal
from src.model_course import ContentCourseId
from src.model_discovery.cs50 import CourseId, deterministic_id
from src.model_evaluation.material_evaluation import CorpusEntry
from src.tools_rag.content_index_models import IndexSelection
from tests.content_store_support import config, payload, raw, registration

COURSE = "loviscach_mathe_1"


@pytest.mark.parametrize("course", get_args(CourseId))
def test_legacy_identity_and_serialization_unchanged(course):
    source = registration(course=course)
    body = source.model_dump(mode="json")
    assert body["course_id"] == course
    assert type(source).model_validate_json(source.model_dump_json()) == source
    assert source.resolved_id == deterministic_id(
        "content_source_v1", "synthetic:c23-02a", "sample"
    )
    assert Principal(subject="legacy", role="viewer", courses=(course,)).courses == (
        course,
    )


def test_explicit_addition_does_not_open_discovery_or_arbitrary_course_names():
    assert get_args(ContentCourseId) == (*get_args(CourseId), COURSE)
    TypeAdapter(ContentCourseId).validate_python(COURSE)
    for value in ("unknown_course", "../course", "*", "", 123):
        with pytest.raises(ValidationError):
            TypeAdapter(ContentCourseId).validate_python(value)
    with pytest.raises(ValidationError):
        TypeAdapter(CourseId).validate_python(COURSE)
    with pytest.raises(ValidationError):
        PlanningParams(source_ref="approved", course_id=COURSE)
    with pytest.raises(ValidationError, match="CS50 namespace"):
        SourceRegistration(
            identity_namespace="cs50",
            external_identity="resource:test",
            source_id="resource:test",
            course_id=COURSE,
            source_type="material",
            source_origin="official",
        )
    entry = CorpusEntry(
        entry_id="inventory",
        origin="real",
        course_id=COURSE,
        format="pdf",
        root_key="explicit",
        permission="inventory_only",
        permission_reference="test",
    )
    assert CorpusEntry.model_validate_json(entry.model_dump_json()) == entry
    # Nested C24/B1 binding schemas inherit the same explicit enum, no new role.
    assert COURSE in json.dumps(DatasetBinding.model_json_schema())
    assert COURSE in json.dumps(SourceDTO.model_json_schema())


def test_authorized_reader_course_filter_and_redacted_dto(tmp_path):
    owner = Principal(subject="owner", role="operator", courses=(COURSE,))
    old = Principal(subject="owner", role="operator", courses=("cs50_python",))
    store = ContentStore.initialize(tmp_path / "content")
    source = store.register_source(registration(course=COURSE), actor=owner)
    key = tmp_path / "key"
    key.write_bytes(bytes(range(32)))
    key.chmod(0o600)
    reader = ContentReader(ContentReadSettings(root=store.root, cursor_key_file=key))
    page = reader.page("sources", (), {"course_id": COURSE}, owner)
    assert len(page.items) == 1 and page.items[0].source_id == source.source_id
    assert page.items[0].course_id == COURSE
    assert reader.page("sources", (), {"course_id": COURSE}, old).items == ()


def test_real_synthetic_store_index_acl_and_reopen(tmp_path):
    owner = Principal(subject="owner", role="operator", courses=(COURSE,))
    viewer = Principal(subject="viewer", role="viewer", courses=(COURSE,))
    old_scope = Principal(subject="owner", role="operator", courses=("cs50_python",))
    store = initialize_synthetic_store(tmp_path / "content")
    source = store.register_source(registration(course=COURSE), actor=owner)
    ref = raw(store, source.source_id, actor=owner)
    version = register_synthetic_version(
        store,
        source.source_id,
        RawManifest(artifacts=(RawArtifact(**ref.model_dump()),)),
        actor=owner,
    )
    published = publish_synthetic(
        store,
        version.source_version_id,
        payload(ref.sha256),
        config(),
        actor=owner,
    ).version
    key = tmp_path / "key"
    key.write_bytes(bytes(range(32)))
    key.chmod(0o600)
    index = synthetic_content_index(
        store,
        tmp_path / "index",
        cursor_key_file=key,
        initialize=True,
    )
    index.build(
        IndexSelection(parsed_version_ids=(published.parsed_version_id,)), actor=owner
    )
    with index.search_lexical("untouched", course_id=COURSE, actor=owner) as page:
        assert page.items and all(h.source_id == source.source_id for h in page.items)
    with pytest.raises(Forbidden):
        store.get_source(source.source_id, actor=old_scope)
    with index.search_lexical("untouched", course_id=COURSE, actor=old_scope) as page:
        assert not page.items
    with index.search_lexical("untouched", course_id=COURSE, actor=viewer) as page:
        assert not page.items
    store.set_source_grants(
        source.source_id,
        (SourceGrant(subject=viewer.subject),),
        expected_acl_revision=0,
        actor=owner,
    )
    with index.search_lexical("untouched", course_id=COURSE, actor=viewer) as page:
        assert page.items
    store.set_source_grants(source.source_id, (), expected_acl_revision=1, actor=owner)
    with index.search_lexical("untouched", course_id=COURSE, actor=viewer) as page:
        assert not page.items
    reopened = ContentStore(store.root)
    assert reopened.get_source(source.source_id, actor=owner).course_id == COURSE
    assert reopened.read_raw_artifact(source.source_id, ref.sha256, actor=owner)
    assert reopened.read_parsed_payload(
        published.parsed_version_id, actor=owner
    ) == payload(ref.sha256)
