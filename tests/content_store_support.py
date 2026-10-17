"""Own small synthetic bytes; never use course originals, settings or external APIs."""

import io

from src.content_store._testing import (
    SyntheticPayload,
    initialize_synthetic_store,
    register_synthetic_version,
)
from src.content_store.models import (
    ContentBlock,
    ContentLocator,
    ParserConfiguration,
    RawArtifact,
    RawManifest,
    SourceRegistration,
    sha256,
)
from src.job_control.models import Principal

OWNER = Principal(subject="owner", role="operator", courses=("cs50_python",))
VIEWER = Principal(subject="viewer", role="viewer", courses=("cs50_python",))
OTHER = Principal(subject="other", role="operator", courses=("cs50_python",))
RAW = b"Synthetic original\r\n  preserve bytes\n"


def registration(key="sample", *, course="cs50_python"):
    return SourceRegistration(
        identity_namespace="synthetic:c23-02a",
        external_identity=key,
        course_id=course,
        source_type="synthetic",
        source_origin="synthetic",
    )


def raw(store, source_id, data=RAW, *, actor=OWNER):
    return store.store_raw_artifact(
        source_id,
        io.BytesIO(data),
        expected_sha256=sha256(data),
        expected_size=len(data),
        mime_type="text/plain",
        actor=actor,
    )


def config(**updates):
    return ParserConfiguration(
        **(
            {
                "parser_name": "synthetic",
                "parser_version": "1",
                "parameters": {"preserve_whitespace": True, "encoding": "utf-8"},
                "implementation_revision": "synthetic-fixture-revision-1",
                "payload_schema": "SyntheticPayload:1",
                "adapter_version": "synthetic_fixture_v1",
            }
            | updates
        )
    )


def payload(raw_sha, *, text="  Ä\u0308 + − x²\r\n\t untouched  "):
    blocks = []
    for index, kind in enumerate(
        ("heading", "paragraph", "code", "formula", "image_reference")
    ):
        locator = ContentLocator(
            raw_artifact_sha256=raw_sha,
            origin_pointer=f"/blocks/{index}",
            page=1,
            bbox=(1, 2, 100, 22),
            coordinate_system="synthetic_points",
            chapter_path=("Kapitel 1",),
            time_status="known" if index == 1 else "unknown",
            start=1.25 if index == 1 else None,
            end=3.5 if index == 1 else None,
        )
        blocks.append(
            ContentBlock(
                block_id=f"synthetic-block:{index}",
                order=index,
                type=kind,
                original_type="math" if kind == "formula" else kind,
                payload_pointer=f"/blocks/{index}",
                text=text if index == 1 else kind,
                data={"availability": "reference_only"}
                if kind == "image_reference"
                else {},
                aggregation_role="non_text_reference"
                if kind == "image_reference"
                else "primary",
                locators=(locator,),
            )
        )
    return (
        SyntheticPayload(blocks=tuple(blocks)).model_dump_json(indent=2) + "\n"
    ).encode()


def seeded(tmp_path):
    store = initialize_synthetic_store(tmp_path / "content")
    source = store.register_source(registration(), actor=OWNER)
    reference = raw(store, source.source_id)
    manifest = RawManifest(artifacts=(RawArtifact(**reference.model_dump()),))
    version = register_synthetic_version(store, source.source_id, manifest, actor=OWNER)
    return store, source, reference, version
