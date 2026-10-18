"""Offline, explicit CS50 bundle verification. No Knowledge or inference imports.

Candidates are process-local capabilities referencing immutable byte snapshots,
not serializable approval flags. Publication repeats the gate in store staging.
"""

import os
import stat
import tempfile
import weakref
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

from pydantic import Field, JsonValue

from src.content_store.artifacts import FILE_FLAGS, _open_directory
from src.content_store.errors import ContentStoreError, UnverifiedBinding
from src.content_store.models import (
    MAX_BYTES,
    ContentBlock,
    ContentLocator,
    ParserConfiguration,
    RawArtifact,
    RawManifest,
    SourceRegistration,
    canonical,
    sha256,
)
from src.job_control.models import Contract, Sha
from src.model_discovery.cs50 import deterministic_id
from src.model_materials.materials import NormalizedDocument
from src.tools_lecture.adapt_cs50 import CS50AdapterPlan
from src.tools_lecture.execute_cs50 import CS50Executor, validate_document
from src.tools_lecture.material_handoff import prepare_material_handoff
from src.tools_materials.quality import _json


class MaterialBundle(Contract):
    workspace: Path
    raw_path: Path
    normalized_path: Path
    receipt_path: Path
    plan_path: Path
    implementation_path: Path
    prior_quality_path: Path | None = None


class SRTBundle(Contract):
    workspace: Path
    raw_path: Path
    transcript_path: Path
    receipt_path: Path
    plan_path: Path
    implementation_path: Path
    source_id: str
    # SRT has no original source_origin field; the caller must declare it.
    source_origin: Literal["official", "synthetic"]


class ImplementationEvidence(Contract):
    schema_version: Literal[1] = 1
    implementation_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    parser_name: str
    parser_version: str
    parameters: dict[str, JsonValue]
    source_id: str
    binding_id: str
    raw_sha256: Sha
    payload_sha256: Sha
    receipt_sha256: Sha
    evidence_reference: str = Field(min_length=1, max_length=2000)


class VerifiedPublicationCandidate:
    """Opaque local capability. Only verify_*_bundle can issue one."""

    __slots__ = ("__weakref__",)

    def __new__(cls, token=None):
        if token is not _TOKEN:
            raise UnverifiedBinding("adapter-issued candidate required")
        return super().__new__(cls)


_TOKEN = object()
_issued = weakref.WeakKeyDictionary()


@dataclass(frozen=True)
class _Frozen:
    kind: str
    files: tuple[tuple[str, bytes], ...]
    paths: tuple[tuple[str, str], ...]
    source_id: str = ""
    source_origin: str = "synthetic"


@dataclass(frozen=True)
class _Verified:
    registration: SourceRegistration
    variant_key: str
    binding: bytes
    manifest: RawManifest
    raw: bytes
    payload: bytes
    config: ParserConfiguration
    representation: str
    original_document_id: str | None
    quality_status: str
    projection: bytes
    blocks: tuple[ContentBlock, ...]
    artifacts: tuple[tuple[str, bytes, str], ...]
    transcript: bool = False


def _relative(path, root):
    path = Path(path)
    if not path.is_absolute():
        path = root / path
    if ".." in path.parts or not path.is_relative_to(root) or path == root:
        raise UnverifiedBinding("explicit bundle path outside workspace")
    relative = path.relative_to(root).as_posix()
    if relative.split("/")[0] == ".content-inputs":
        raise UnverifiedBinding("reserved snapshot namespace")
    return relative


def _read(path):
    """Bounded regular-file snapshot; open every component without following links."""
    path = Path(path).absolute()
    if ".." in path.parts:
        raise UnverifiedBinding("bundle path traversal")
    directory = _open_directory(path.parent)
    try:
        fd = os.open(path.name, FILE_FLAGS, dir_fd=directory)
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_BYTES:
                raise UnverifiedBinding("bounded regular bundle file required")
            data = stream.read(MAX_BYTES + 1)
            after = os.fstat(stream.fileno())
            if (
                len(data) > MAX_BYTES
                or len(data) != before.st_size
                or (before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                != (after.st_size, after.st_mtime_ns, after.st_ctime_ns)
            ):
                raise UnverifiedBinding("bundle changed while freezing")
            return data
    finally:
        os.close(directory)


def _json_bytes(data):
    value = _json(data)
    canonical(value)
    return value


def _capture(bundle, kind):
    root = bundle.workspace.absolute()
    paths, files = {}, {}

    def take(relative, path):
        if relative in files or len(files) >= 506:
            raise UnverifiedBinding("bundle input collision or count limit")
        data = _read(path)
        if sum(map(len, files.values())) + len(data) > 256 * 1024 * 1024:
            raise UnverifiedBinding("bundle snapshot budget exceeded")
        files[relative] = data

    for field, key in (
        ("raw_path", "raw"),
        ("normalized_path" if kind == "material" else "transcript_path", "payload"),
        ("receipt_path", "receipt"),
    ):
        relative = _relative(getattr(bundle, field), root)
        paths[key] = relative
        take(relative, root / relative)
    for field, key in (
        ("plan_path", "plan"),
        ("implementation_path", "implementation"),
        ("prior_quality_path", "prior_quality"),
    ):
        path = getattr(bundle, field, None)
        if path is not None:
            path = path if path.is_absolute() else root / path
            paths[key] = f".content-inputs/{key}.json"
            take(paths[key], path)
    if kind == "material":
        doc = NormalizedDocument.model_validate(_json_bytes(files[paths["payload"]]))
        for image in doc.images:
            if image.artifact_path is not None:
                relative = _relative(
                    root / Path(paths["payload"]).parent / image.artifact_path, root
                )
                take(relative, root / relative)
    return _Frozen(
        kind=kind,
        files=tuple(sorted(files.items())),
        paths=tuple(sorted(paths.items())),
        source_id=getattr(bundle, "source_id", ""),
        source_origin=getattr(bundle, "source_origin", "synthetic"),
    )


def _evidence(
    root,
    paths,
    *,
    source,
    binding_id,
    raw,
    payload,
    receipt,
    name,
    version,
    parameters,
    schema,
    adapter,
):
    evidence = ImplementationEvidence.model_validate(
        _json_bytes((root / paths["implementation"]).read_bytes())
    )
    expected = dict(
        source_id=source,
        binding_id=binding_id,
        raw_sha256=sha256(raw),
        payload_sha256=sha256(payload),
        receipt_sha256=sha256(receipt),
        parser_name=name,
        parser_version=version,
        parameters=parameters,
    )
    if any(getattr(evidence, k) != v for k, v in expected.items()):
        raise UnverifiedBinding("implementation evidence contradicts bundle")
    return ParserConfiguration(
        parser_name=name,
        parser_version=version,
        parameters=parameters,
        implementation_revision=evidence.implementation_revision,
        payload_schema=schema,
        adapter_version=adapter,
    )


def _material(root, paths):
    review = prepare_material_handoff(
        workspace=root,
        raw_path=root / paths["raw"],
        normalized_path=root / paths["payload"],
        receipt_path=root / paths["receipt"],
        plan_path=root / paths["plan"],
    )
    if not review.report.passed or review.handoff is None:
        raise UnverifiedBinding("material quality gate rejected frozen bundle")
    handoff = review.handoff
    doc, binding = handoff.document, handoff.document.binding
    raw, payload, receipt = (
        (root / paths[k]).read_bytes() for k in ("raw", "payload", "receipt")
    )
    if len(raw) > doc.parser.max_bytes:
        raise UnverifiedBinding("material exceeds recorded parser byte limit")
    config = _evidence(
        root,
        paths,
        source=binding.source_id,
        binding_id=binding.material_id,
        raw=raw,
        payload=payload,
        receipt=receipt,
        name=doc.parser.name,
        version=doc.parser.version,
        parameters=doc.parser.model_dump(mode="json"),
        schema="NormalizedDocument:1",
        adapter="cs50_material_content_v1",
    )
    active = {u.block.block_id for u in handoff.aggregation_units}
    blocks = []
    for b in doc.blocks:
        excluded = handoff.excluded_blocks.get(b.block_id)
        role = (
            "primary"
            if b.block_id in active
            else (
                "reference_projection"
                if excluded
                in {
                    "table_of_contents",
                    "reference_projection",
                    "geometric_table_projection",
                }
                else "structure"
                if excluded == "list_structure"
                else "non_text_reference"
            )
        )
        blocks.append(
            ContentBlock(
                block_id=b.block_id,
                order=b.order,
                type="formula" if b.type == "math" else b.type,
                original_type=b.type,
                payload_pointer=f"/blocks/{b.order}",
                text=b.text,
                data=b.data,
                aggregation_role=role,
                locators=(
                    ContentLocator(
                        raw_artifact_sha256=doc.raw_sha256,
                        origin_pointer=f"/blocks/{b.order}",
                        **b.location.model_dump(),
                        time_status="not_applicable",
                    ),
                ),
            )
        )
    projection = canonical(
        dict(
            schema_version=1,
            adapter_version=config.adapter_version,
            document_id=doc.document_id,
            blocks=[b.model_dump(mode="json") for b in blocks],
            aggregation_units=[
                u.model_dump(mode="json") for u in handoff.aggregation_units
            ],
            excluded_blocks=handoff.excluded_blocks,
            alternative_views=handoff.alternative_views,
        )
    )
    report = review.report.model_dump(mode="json")
    report["inputs"] = {
        "normalized": paths["payload"],
        "receipt": paths["receipt"],
        "raw": paths["raw"],
        "plan": paths["plan"],
        "workspace": ".",
    }
    artifacts = [
        (k, (root / paths[k]).read_bytes(), "application/json")
        for k in ("receipt", "plan", "implementation")
    ]
    artifacts += [
        ("quality", canonical(report), "application/json"),
        ("handoff", canonical(handoff.model_dump(mode="json")), "application/json"),
    ]
    if "prior_quality" in paths:
        artifacts.append(
            (
                "prior_quality",
                (root / paths["prior_quality"]).read_bytes(),
                "application/json",
            )
        )
    for image in doc.images:
        if image.artifact_path:
            artifacts.append(
                (
                    f"image:{image.image_id}",
                    (root / paths["payload"])
                    .parent.joinpath(image.artifact_path)
                    .read_bytes(),
                    image.mime_type or "application/octet-stream",
                )
            )
    return _Verified(
        registration=SourceRegistration(
            identity_namespace="cs50",
            external_identity=binding.source_id,
            source_id=binding.source_id,
            course_id=binding.resource.course_id,
            source_type="material",
            source_origin=binding.source_origin,
            original_url=binding.original_url,
        ),
        variant_key=binding.variant_id or "default",
        binding=canonical(binding.model_dump(mode="json")),
        manifest=RawManifest(
            artifacts=(
                RawArtifact(
                    sha256=sha256(raw),
                    size_bytes=len(raw),
                    mime_type=handoff.receipt.mime_type or "application/octet-stream",
                ),
            )
        ),
        raw=raw,
        payload=payload,
        config=config,
        representation=f"material:{binding.material_id}",
        original_document_id=doc.document_id,
        quality_status=review.report.status,
        projection=projection,
        blocks=tuple(blocks),
        artifacts=tuple(artifacts),
    )


def _srt(root, paths, frozen):
    plan = CS50AdapterPlan.model_validate(
        _json_bytes((root / paths["plan"]).read_bytes())
    )
    executor = CS50Executor(plan, workspace=root)  # constructor only; no run/download
    binding = executor.bindings.get(frozen.source_id)
    if binding is None or binding.source_id != binding.resource_id:
        raise UnverifiedBinding("SRT source absent from checked plan")
    if binding.raw_srt_path.is_absolute() or binding.transcript_json_path.is_absolute():
        raise UnverifiedBinding(
            "absolute historical SRT binding requires separate migration"
        )
    if (
        paths["raw"] != binding.raw_srt_path.as_posix()
        or paths["payload"] != binding.transcript_json_path.as_posix()
        or paths["receipt"]
        != (binding.raw_srt_path.parent / "execution.v1.json").as_posix()
    ):
        raise UnverifiedBinding("SRT paths contradict original binding")
    receipt = _json_bytes((root / paths["receipt"]).read_bytes())
    if (
        set(receipt) != {"schema_version", "binding", "actions"}
        or receipt["schema_version"] != 1
        or receipt["binding"] != binding.model_dump(mode="json")
    ):
        raise UnverifiedBinding("SRT receipt identity mismatch")
    tasks = [t for t in executor.tasks.values() if t.resource_id == binding.resource_id]
    if len(tasks) != 2 or set(receipt["actions"]) != {t.task_id for t in tasks}:
        raise UnverifiedBinding("exactly two bound SRT tasks required")
    raw, payload, receipt_bytes = (
        (root / paths[k]).read_bytes() for k in ("raw", "payload", "receipt")
    )
    actions = {}
    for task in tasks:
        action = task.task.actions[0].value
        record = receipt["actions"][task.task_id]
        expected = dict(
            status="done",
            action=action,
            sha256=sha256(raw if action == "download" else payload),
        )
        if action == "parse_subtitle":
            expected["input_sha256"] = sha256(raw)
        if record != expected or action in actions:
            raise UnverifiedBinding("SRT task or input/output hash mismatch")
        actions[action] = record
    if set(actions) != {"download", "parse_subtitle"}:
        raise UnverifiedBinding("unsupported SRT actions")
    # Strict JSON check precedes existing Pydantic/reparse validation.
    _json_bytes((root / paths["payload"]).read_bytes())
    document = validate_document(root / paths["payload"], binding, root / paths["raw"])
    config = _evidence(
        root,
        paths,
        source=binding.source_id,
        binding_id=binding.source_id,
        raw=raw,
        payload=payload,
        receipt=receipt_bytes,
        name="srt",
        version="1",
        parameters=dict(
            encoding="utf-8-sig",
            media_format="srt",
            language=binding.language,
            preserve_empty_cues=True,
        ),
        schema="TranscriptDocument:legacy-unversioned",
        adapter="cs50_srt_content_v1",
    )
    blocks = tuple(
        ContentBlock(
            # Projection keeps original cue identity; final persisted ID binds parsed version.
            block_id=f"cue:{s.seg_id}",
            order=i,
            type="paragraph",
            original_type="srt_cue",
            payload_pointer=f"/segments/{i}",
            text=s.text,
            data=dict(seg_id=s.seg_id, language=document.language),
            locators=(
                ContentLocator(
                    raw_artifact_sha256=sha256(raw),
                    origin_pointer=f"/segments/{i}",
                    original_segment_id=s.seg_id,
                    time_status="known",
                    start=s.start,
                    end=s.end,
                ),
            ),
        )
        for i, s in enumerate(document.segments)
    )
    if len({b.block_id for b in blocks}) != len(blocks):
        raise UnverifiedBinding("duplicate SRT cue IDs")
    projection = canonical(
        dict(
            schema_version=1,
            adapter_version=config.adapter_version,
            source_id=binding.source_id,
            blocks=[b.model_dump(mode="json") for b in blocks],
            aggregation_units=[
                dict(order=b.order, payload_pointer=b.payload_pointer, text=b.text)
                for b in blocks
            ],
        )
    )
    return _Verified(
        registration=SourceRegistration(
            identity_namespace="cs50",
            external_identity=binding.source_id,
            source_id=binding.source_id,
            course_id=binding.course_id,
            source_type="transcript",
            source_origin=frozen.source_origin,
            original_url=binding.transcript_url,
        ),
        variant_key=binding.language,
        binding=canonical(binding.model_dump(mode="json")),
        manifest=RawManifest(
            artifacts=(
                RawArtifact(
                    sha256=sha256(raw),
                    size_bytes=len(raw),
                    mime_type="application/x-subrip",
                ),
            )
        ),
        raw=raw,
        payload=payload,
        config=config,
        representation=f"transcript:srt:{binding.resource_id}",
        original_document_id=None,
        quality_status="passed",
        projection=projection,
        blocks=blocks,
        artifacts=tuple(
            (k, (root / paths[k]).read_bytes(), "application/json")
            for k in ("receipt", "plan", "implementation")
        )
        + (
            (
                "quality",
                canonical(
                    dict(
                        schema_version=1,
                        validator_version="cs50_srt_content_v1",
                        status="passed",
                        raw_sha256=sha256(raw),
                        payload_sha256=sha256(payload),
                        segment_count=len(blocks),
                    )
                ),
                "application/json",
            ),
        ),
        transcript=True,
    )


def _verify_frozen(frozen, *, staging_parent=None):
    try:
        with tempfile.TemporaryDirectory(
            prefix="content-bundle-", dir=staging_parent
        ) as temporary:
            root = Path(temporary)
            for relative, data in frozen.files:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                for parent in path.parents:
                    if parent == root:
                        break
                    parent.chmod(0o700)
                with path.open("xb") as output:
                    output.write(data)
                path.chmod(0o400)
            paths = dict(frozen.paths)
            verified = (
                _material(root, paths)
                if frozen.kind == "material"
                else _srt(root, paths, frozen)
            )
            projection = _json_bytes(verified.projection)
            source_id = verified.registration.resolved_id
            source_version_id = deterministic_id(
                "content_source_version_v1",
                source_id,
                verified.variant_key,
                verified.manifest.digest,
            )
            document_id = deterministic_id(
                "content_document_v1", source_id, verified.representation
            )
            projection["slot_id"] = deterministic_id(
                "content_slot_v1",
                source_version_id,
                document_id,
                verified.config.config_id,
            )
            projection["binding_sha256"] = sha256(verified.binding)
            return replace(verified, projection=canonical(projection))
    except ContentStoreError:
        raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError):
        raise UnverifiedBinding("invalid or incomplete frozen bundle") from None


def _candidate(candidate, *, staging_parent=None):
    if type(candidate) is not VerifiedPublicationCandidate or candidate not in _issued:
        raise UnverifiedBinding("adapter-issued candidate required")
    frozen = _issued[candidate]
    if staging_parent is None:
        return _verify_frozen(frozen)
    from src.content_store.artifacts import _Artifacts
    from src.content_store.limits import staging_budget

    with staging_budget(
        _Artifacts(staging_parent.parent), sum(len(data) for _, data in frozen.files)
    ):
        return _verify_frozen(frozen, staging_parent=staging_parent)


def _issue(bundle, expected, kind):
    if type(bundle) is not expected:
        raise UnverifiedBinding("typed explicit bundle required")
    try:
        bundle = expected.model_validate_json(bundle.model_dump_json())
        frozen = _capture(bundle, kind)
        _verify_frozen(frozen)
    except ContentStoreError:
        raise
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        raise UnverifiedBinding("invalid or incomplete explicit bundle") from None
    candidate = VerifiedPublicationCandidate(_TOKEN)
    _issued[candidate] = frozen
    return candidate


def verify_material_bundle(bundle: MaterialBundle) -> VerifiedPublicationCandidate:
    return _issue(bundle, MaterialBundle, "material")


def verify_srt_bundle(bundle: SRTBundle) -> VerifiedPublicationCandidate:
    return _issue(bundle, SRTBundle, "srt")


def import_verified_bundle(
    store, candidate, *, actor, request_key, raw_retry=None, binding_retry=None
):
    """Persist independently valid raw/source records, then atomic parsed publication."""
    import io

    from src.content_store.errors import Forbidden
    from src.content_store.models import checked_actor

    actor = checked_actor(actor)
    if store.read_only:
        raise Forbidden("read-only content handle")
    with store._maintenance():
        verified = _candidate(candidate, staging_parent=store.root / "staging")
        source = store.register_source(verified.registration, actor=actor)
        ref = verified.manifest.artifacts[0]
        store.store_raw_artifact(
            source.source_id,
            io.BytesIO(verified.raw),
            expected_sha256=ref.sha256,
            expected_size=ref.size_bytes,
            mime_type=ref.mime_type,
            actor=actor,
            retry=raw_retry,
        )
        version = store.register_source_version(
            source.source_id,
            verified.manifest,
            variant_key=verified.variant_key,
            binding=candidate,
            actor=actor,
            retry=binding_retry,
        )
        return store.publish_parsed_document(
            version.source_version_id, candidate, actor=actor, request_key=request_key
        )
