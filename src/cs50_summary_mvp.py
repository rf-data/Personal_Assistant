"""Explicit read-only One-Source HTML summary with a separate current approval."""

import argparse
import fcntl
import json
import os
import stat
import subprocess
import sys
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, Field, field_validator

from scripts import cs50_learning_mvp as mvp
from src.c27_learning_summary.adapter import artifact, source_slices
from src.c27_learning_summary.engine import (
    SummaryRunError,
    bind_section,
    consolidate,
    generate,
    input_snapshot,
    messages_for,
)
from src.c27_learning_summary.llm import FakeLLM
from src.c27_learning_summary.models import (
    Catalog,
    SectionResponse,
    SummaryConfig,
    SummaryResult,
)
from src.c27_learning_summary.store import SummaryStore
from src.content_store.adapters import ImplementationEvidence
from src.content_store.artifacts import explicit_root
from src.content_store.errors import ContentStoreError
from src.content_store.models import ContentBlock, canonical, fingerprint, sha256
from src.content_store.read_models import ContentReadSettings
from src.content_store.reader import ContentReader, ReadFault, private_bytes
from src.job_control.models import Contract, Identifier, Sha
from src.runtime_paths import checked_path
from src.tools_lecture.execute_cs50 import write_state
from src.tools_materials.storage import publish_bytes

ADAPTER_VERSION = "one-source-summary-m1-v1"
ACTIONS = ("read_verified_html", "summarize_fake", "store_private_summary")
Hold = mvp.Hold


class SummaryApproval(Contract):
    schema_version: Literal[1]
    status: Literal["approved"]
    approved_by: Identifier
    evidence_reference: str = Field(min_length=1, max_length=2000, pattern=r"\S")
    valid_until: AwareDatetime
    actions: tuple[str, ...]
    source_id: str
    source_version_id: str
    parsed_version_id: str
    raw_sha256: Sha
    payload_sha256: Sha
    projection_sha256: Sha
    processing_approval_sha256: Sha
    mvp_intent_sha256: Sha
    mvp_state_sha256: Sha
    implementation_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    implementation_sha256: Sha
    adapter_version: Literal["one-source-summary-m1-v1"]
    config: SummaryConfig

    @field_validator("schema_version", mode="before")
    @classmethod
    def explicit_schema(cls, value):
        if type(value) is not int:
            raise ValueError("explicit integer schema_version required")
        return value


def historical_approval(root, intent, actor):
    """Verify historical scope, without treating it as a current code approval."""
    encoded = private_bytes(root / "approval.json", 65536)
    old = mvp.ProcessingApproval.model_validate(mvp._json(encoded))
    mapping = {
        "resource_id": "source_id",
        "material_id": "material_id",
        "original_url": "original_url",
        "source_origin": "source_origin",
        "raw_sha256": "raw_sha256",
        "plan_sha256": "plan_sha256",
        "implementation_revision": "implementation_revision",
        "implementation_sha256": "implementation_sha256",
    }
    if (
        sha256(encoded) != intent["approval_sha256"]
        or old.valid_until <= datetime.now(UTC)
        or old.approved_by != actor.subject
        or old.actions != mvp.ACTIONS
        or old.parser.model_dump(mode="json") != intent["parser"]
        or any(getattr(old, field) != intent[key] for field, key in mapping.items())
    ):
        raise Hold("historical processing approval binding rejected")
    evidence = ImplementationEvidence.model_validate_json(
        mvp._read(root / "implementation.json")
    )
    if (
        evidence.implementation_revision != old.implementation_revision
        or evidence.evidence_reference
        != f"operator approval sha256:{sha256(encoded)}; "
        f"actual Python bytes sha256:{old.implementation_sha256}"
    ):
        raise Hold("historical implementation evidence conflict")


def read_source(root, source_id, parsed_version_id, subject):
    """Caller holds the existing MVP lock. Only stored JSON and raw bytes are read."""
    return _read_verified_source(
        root, source_id, parsed_version_id, subject, phases=("ready",)
    )


def _read_verified_source(
    root, source_id, parsed_version_id, subject, *, phases, strict_reader=False
):
    """Shared integrity/Reader checks; callers supply their own readiness contract."""
    intent, state = mvp.load(root, "intent.json"), mvp.load(root, "state.json")
    actor = mvp.actor_for(intent, subject)
    if (
        state["phase"] not in phases
        or source_id != intent["source_id"]
        or parsed_version_id != state["parsed_version_id"]
        or intent["parser"]["name"] != "html"
        or intent["parser"]["version"] != "2"
    ):
        raise Hold("explicit ready HTML source/version required by source contract")
    historical_approval(root, intent, actor)
    store, doc = mvp.verify_persisted(root, intent, state, actor)
    if doc.binding.format != "html" or not doc.binding.lecture_ids:
        raise Hold("HTML with an explicit lecture binding required")
    if (
        doc.binding.source_origin == "official"
        and doc.binding.license_status != "reviewed"
    ):
        raise Hold("real material requires separately reviewed license and approval")
    view = store.get_parsed_document(parsed_version_id, actor=actor)
    projection_bytes = store.read_version_artifact(
        parsed_version_id, "projection", actor=actor
    )
    if sha256(projection_bytes) != view.projection_sha256:
        raise Hold("projection fingerprint conflict")
    blocks = tuple(
        ContentBlock.model_validate(b) for b in json.loads(projection_bytes)["blocks"]
    )
    if len(blocks) != len(doc.blocks) or len({b.block_id for b in blocks}) != len(
        blocks
    ):
        raise Hold("incomplete or duplicate source blocks")
    for block, original in zip(blocks, doc.blocks, strict=True):
        if (
            block.block_id != original.block_id
            or block.order != original.order
            or block.text != original.text
            or block.data != original.data
            or len(block.locators) != 1
            or block.locators[0].raw_artifact_sha256 != intent["raw_sha256"]
            or block.locators[0].origin_pointer != f"/blocks/{original.order}"
            or any(
                getattr(block.locators[0], key) != value
                for key, value in original.location.model_dump().items()
            )
        ):
            raise Hold("original block/locator conflict")
    reader = ContentReader(
        ContentReadSettings(root=root / "store", cursor_key_file=root / "cursor.key")
    )
    seen, cursor = [], None
    while True:
        query = {"limit": "100"}
        if cursor:
            query["cursor"] = cursor
        page = reader.page("blocks", (parsed_version_id,), query, actor)
        for dto in page.items:
            if len(seen) >= len(blocks):
                raise Hold("reader contains unexpected blocks")
            block = blocks[len(seen)]
            if strict_reader and dto.parsed_version_id != parsed_version_id:
                raise Hold("reader parsed version conflict")
            if (
                dto.block_id != block.block_id
                or dto.order != block.order
                or dto.type != block.type
                or dto.aggregation_role != block.aggregation_role
                or dto.text_length != len(block.text)
                or dto.text_sha256 != block.text_sha256
            ):
                raise Hold("reader/projection conflict")
            text, start = "", 0
            while start < len(block.text):
                window = reader.block(
                    parsed_version_id,
                    block.block_id,
                    actor,
                    {"start": str(start), "limit": "16384"},
                )
                if (
                    window.start != start
                    or window.end <= start
                    or window.text_length != len(block.text)
                    or window.text_sha256 != block.text_sha256
                ):
                    raise Hold("incomplete reader text window")
                if strict_reader and (
                    window.parsed_version_id != parsed_version_id
                    or window.block_id != block.block_id
                    or window.end != start + len(window.text)
                    or window.end > len(block.text)
                ):
                    raise Hold("reader text window identity conflict")
                text += window.text
                start = window.end
            if text != block.text:
                raise Hold("reader text conflict")
            structure = reader.block(
                parsed_version_id, block.block_id, actor, {}, structured=True
            )
            if strict_reader:
                from src.content_store.read_views import label
                from src.content_store.read_views import structure as public_structure

                expected_locators = []
                for original in block.locators:
                    expected = original.model_dump(mode="json")
                    expected["dom"] = label(expected["dom"])
                    expected["coordinate_system"] = (
                        label(expected["coordinate_system"]) or "unknown"
                    )
                    expected["chapter_path"] = [
                        p for p in expected["chapter_path"] if label(p) is not None
                    ]
                    expected_locators.append(expected)
                if (
                    structure.parsed_version_id != parsed_version_id
                    or structure.block_id != block.block_id
                    or structure.data != public_structure(block)[0]
                    or any(
                        loc.model_dump(mode="json", exclude={"raw_reference"})
                        != expected
                        or loc.raw_reference.sha256 != intent["raw_sha256"]
                        for loc, expected in zip(
                            structure.locators, expected_locators, strict=True
                        )
                    )
                ):
                    raise Hold("reader complete structure/locator conflict")
            if len(structure.locators) != len(block.locators) or any(
                loc.raw_artifact_sha256 != intent["raw_sha256"]
                or loc.origin_pointer != original.origin_pointer
                or loc.raw_reference.source_id != source_id
                or loc.raw_reference.source_version_id != state["source_version_id"]
                for loc, original in zip(
                    structure.locators, block.locators, strict=True
                )
            ):
                raise Hold("reader source locator conflict")
            seen.append(block.block_id)
        cursor = page.next_cursor
        if not cursor:
            break
        if not page.items or len(seen) >= len(blocks):
            raise Hold("reader pagination conflict")
    if len(seen) != len(blocks):
        raise Hold("reader omitted source blocks")
    identity = dict(
        source_id=source_id,
        source_version_id=state["source_version_id"],
        parsed_version_id=parsed_version_id,
        raw_sha256=intent["raw_sha256"],
        payload_sha256=view.payload_sha256,
        projection_sha256=view.projection_sha256,
        processing_approval_sha256=intent["approval_sha256"],
        mvp_intent_sha256=sha256(mvp._read(root / "intent.json")),
        mvp_state_sha256=sha256(mvp._read(root / "state.json")),
    )
    return identity, blocks, doc


def catalog_for(identity, blocks, doc):
    binding = doc.binding
    # The source is selected explicitly; a shared material does not select other lectures.
    lecture_id = binding.lecture_ids[0]
    week_id = (
        binding.resource.section_keys[0] if binding.resource.section_keys else "single"
    )
    processing = artifact(
        blocks,
        artifact_id=binding.material_id,
        parser_version=f"html-{doc.parser.version}",
        last_run=identity["parsed_version_id"],
    )
    material = dict(
        material_id=binding.material_id,
        source_id=binding.source_id,
        source_path="verified-content-store",
        resource=dict(
            resource_type="document",
            file_type="html",
            content_hash=doc.raw_sha256,
            title="Explicit verified HTML",
            source_url=binding.original_url,
        ),
        available=True,
        verification="synthetic_test_only"
        if binding.source_origin == "synthetic"
        else "operator_verified",
        processing_status="completed",
        artifact=processing,
        blocks=blocks,
    )
    catalog = Catalog.model_validate(
        dict(
            origin="synthetic"
            if binding.source_origin == "synthetic"
            else "operator_reviewed_local",
            courses=[
                dict(
                    course_id=binding.resource.course_id,
                    course_title="One selected source",
                    provider="cs50",
                    source_url=None,
                    weeks=[
                        dict(
                            section_id=week_id,
                            units=[
                                dict(
                                    section_id=lecture_id,
                                    title="One selected HTML source",
                                    materials=[material],
                                )
                            ],
                        )
                    ],
                )
            ],
        )
    )
    return (
        catalog,
        (binding.resource.course_id, week_id, lecture_id),
        (binding.material_id,),
    )


def check_approval(approval, identity, subject):
    revision, code_hash = mvp.implementation_identity()
    if (
        approval.valid_until <= datetime.now(UTC)
        or approval.approved_by != subject
        or approval.actions != ACTIONS
        or approval.implementation_revision != revision
        or approval.implementation_sha256 != code_hash
        or any(getattr(approval, key) != value for key, value in identity.items())
        or approval.config.provider != "fake"
        or approval.config.retries != 0
    ):
        raise Hold("current summary approval scope/code/version rejected")


def checked_refs(refs, blocks, config):
    """Independently prove that slicing did not silently omit source text."""
    expected, whitespace = [], []
    for block in blocks:
        if block.aggregation_role != "primary" or not block.text.strip():
            continue
        for start in range(0, len(block.text), config.chunk_chars):
            text = block.text[start : start + config.chunk_chars]
            item = (block.block_id, start, start + len(text), text)
            if text.strip():
                expected.append(item)
            else:
                whitespace.append(
                    dict(block_id=block.block_id, start=start, end=start + len(text))
                )
    observed = [(r.block_id, r.offset_start, r.offset_end, r.text) for r in refs]
    if (
        not expected
        or observed != expected
        or len({r.ref_id for r in refs}) != len(refs)
    ):
        raise Hold("source slices omit, duplicate or truncate eligible content")
    return whitespace


def checked_result(result, refs, config, engine_key):
    if (
        result.refs != refs
        or len(result.sections) != len(refs)
        or result.config != config
        or result.cache_key != engine_key
    ):
        raise Hold("summary evidence coverage conflict")
    for section, ref in zip(result.sections, refs, strict=True):
        response = SectionResponse(
            claims=[c.model_dump(exclude={"claim_id"}) for c in section.claims],
            uncertainties=section.uncertainties,
        )
        if section != bind_section(response, ref):
            raise Hold("summary section evidence rejected")
    claims, issues = consolidate(result.sections)
    if (
        not claims
        or result.claims != claims
        or issues
        or result.state != "ready_for_review"
    ):
        raise Hold("summary claims require attention; no accepted result")


@contextmanager
def summary_root(path):
    create = not path.exists()
    if create:
        path.mkdir(mode=0o700)
        publish_bytes(path / ".m1.lock", b"")
    info = path.stat()
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.getuid()
        or info.st_mode & 0o077
    ):
        raise Hold("private owned summary root required")
    fd = os.open(path / ".m1.lock", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        mvp.inventory(path)
        yield create


def run(args):
    source_root = checked_path(explicit_root(args.source_root))
    target = checked_path(explicit_root(args.output_root))
    approval_path = checked_path(args.approval)
    if (
        source_root.is_relative_to(target)
        or target.is_relative_to(source_root)
        or approval_path.is_relative_to(target)
        or approval_path.is_relative_to(source_root)
    ):
        raise Hold("source, approval and new summary root must be isolated")
    approval_bytes = private_bytes(approval_path, 65536)
    approval = SummaryApproval.model_validate(mvp._json(approval_bytes))
    with mvp.output_root(source_root) as (_, before):
        identity, blocks, doc = read_source(
            source_root, args.source_id, args.parsed_version_id, args.actor
        )
        check_approval(approval, identity, args.actor)
        catalog, scope, selected = catalog_for(identity, blocks, doc)
        unit = catalog.courses[0].weeks[0].units[0]
        try:
            refs = source_slices(*scope, unit.materials, approval.config)
        except ValueError as error:
            raise Hold(
                "complete source exceeds supported slicing limits; no truncation"
            ) from error
        whitespace = checked_refs(refs, blocks, approval.config)
        engine_key = fingerprint(
            input_snapshot(catalog, unit, *scope, selected, approval.config)
        )
        if not refs or any(
            len(
                json.dumps(
                    messages_for(ref, approval.config), ensure_ascii=False
                ).encode()
            )
            > approval.config.max_input_bytes
            for ref in refs
        ):
            raise Hold("complete source exceeds supported context; no truncation")
        evidence = dict(
            identity=identity,
            blocks=[b.model_dump(mode="json") for b in blocks],
            refs=[
                dict(
                    ref_id=ref.ref_id,
                    block_id=ref.block_id,
                    parsed_version_id=args.parsed_version_id,
                    offset_start=ref.offset_start,
                    offset_end=ref.offset_end,
                    original_locators=[
                        loc.model_dump(mode="json")
                        for loc in next(
                            b for b in blocks if b.block_id == ref.block_id
                        ).locators
                    ],
                )
                for ref in refs
            ],
            excluded_blocks=[
                dict(
                    block_id=b.block_id,
                    reason="blank_text" if not b.text.strip() else b.aggregation_role,
                )
                for b in blocks
                if b.aggregation_role != "primary" or not b.text.strip()
            ],
        )
        evidence["whitespace_only_slices"] = whitespace
        intent = dict(
            adapter_version=ADAPTER_VERSION,
            identity=identity,
            summary_approval_sha256=sha256(approval_bytes),
            implementation_revision=approval.implementation_revision,
            implementation_sha256=approval.implementation_sha256,
            config=approval.config.model_dump(mode="json"),
            evidence_sha256=fingerprint(evidence),
        )
        with summary_root(target) as create:
            if not create:
                manifest = mvp.load(target, "manifest.json")
                observed = mvp.inventory(target)
                observed.pop("manifest.json")
                if observed != manifest or mvp.load(target, "intent.json") != intent:
                    raise Hold(
                        "summary root incomplete, changed or belongs to another intent"
                    )
                report = mvp.load(target, "summary.json")
                result = SummaryResult.model_validate(report["summary"])
                checked_result(result, refs, approval.config, engine_key)
                if mvp.load(target, "evidence.json") != evidence:
                    raise Hold("cached original evidence conflict")
                if mvp.inventory(source_root) != before:
                    raise Hold("source changed during cache verification")
                check_approval(approval, identity, args.actor)
                return report
            publish_bytes(target / "approval.json", approval_bytes)
            publish_bytes(target / "intent.json", canonical(intent))
            publish_bytes(target / "evidence.json", canonical(evidence))
            write_state(target / "state.json", {"phase": "pending"})
            outcome = generate(
                SummaryStore(target / "engine"),
                catalog,
                *scope,
                selected,
                approval.config,
                FakeLLM(),
            )
            result = outcome.result
            checked_result(result, refs, approval.config, engine_key)
            if read_source(
                source_root, args.source_id, args.parsed_version_id, args.actor
            ) != (identity, blocks, doc):
                raise Hold("source changed during summary generation")
            check_approval(approval, identity, args.actor)
            if mvp.inventory(source_root) != before:
                raise Hold("original MVP changed; summary retained as incomplete")
            cited = {r for claim in result.claims for r in claim.refs}
            report = dict(
                schema_version=1,
                status="completed",
                review_status="unreviewed",
                provider="fake",
                cache_identity=fingerprint(intent),
                source=identity,
                summary=result.model_dump(mode="json"),
                evidence_sha256=fingerprint(evidence),
                coverage=dict(
                    total_blocks=len(blocks),
                    eligible_blocks=len({r.block_id for r in refs}),
                    input_refs=len(refs),
                    processed_refs=len(result.sections),
                    cited_refs=len(cited),
                    uncited_refs=sorted({r.ref_id for r in refs} - cited),
                    excluded_blocks=evidence["excluded_blocks"],
                    whitespace_only_slices=whitespace,
                    complete_input=True,
                ),
                warnings=list(result.warnings)
                + [
                    "FakeLLM produces mechanical excerpts, not a semantic lecture summary.",
                    "Human review required; no subject-matter acceptance or real-source approval.",
                ],
            )
            publish_bytes(target / "summary.json", canonical(report))
            write_state(
                target / "state.json",
                {"phase": "ready", "cache_identity": fingerprint(intent)},
            )
            publish_bytes(target / "manifest.json", canonical(mvp.inventory(target)))
            return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--parsed-version-id", required=True)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--actor", required=True)
    args = parser.parse_args(argv)
    previous = os.umask(0o077)
    try:
        print(json.dumps(run(args), ensure_ascii=False))
        return 0
    except (
        ContentStoreError,
        ReadFault,
        SummaryRunError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        subprocess.SubprocessError,
        RuntimeError,
    ) as error:
        print(
            json.dumps(
                dict(
                    status="HOLD",
                    success=False,
                    reason=str(error)
                    if isinstance(error, Hold)
                    else type(error).__name__,
                    recovery="retain roots; no automatic retry, parsing or recovery",
                )
            ),
            file=sys.stderr,
        )
        return 2
    finally:
        os.umask(previous)


if __name__ == "__main__":
    raise SystemExit(main())
