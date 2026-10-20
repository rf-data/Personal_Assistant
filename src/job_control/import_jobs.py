"""Pinned byte snapshots -> real C23 candidate -> existing ContentStore publication."""

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

from src.content_store.adapters import (
    MaterialBundle,
    _candidate,
    import_verified_bundle,
    verify_material_bundle,
    verify_srt_bundle,
)
from src.content_store.errors import (
    Conflict,
    Forbidden,
    UnverifiedBinding,
)
from src.content_store.inventory import _existing
from src.content_store.models import ParsedDocument, canonical, fingerprint, sha256
from src.content_store.publication import _source_version
from src.content_store.read_views import route
from src.content_store.store import ContentStore
from src.job_control.catalog import read_file, safe_path, verified_files
from src.job_control.import_models import ContentImportPlan, ImportInfo, ImportReceipt
from src.job_control.models import Principal
from src.model_discovery.cs50 import deterministic_id
from src.tools_materials.quality import _json

PROCESS = "content_import"


def plan(entry, job_root):
    relative = entry.roles["import"]
    raw = read_file(safe_path(entry.root, relative))
    if sha256(raw) != entry.files[relative]:
        raise UnverifiedBinding("import plan changed")
    spec = ContentImportPlan.model_validate(_json(raw))
    if entry.kind != "content_import_bundle" or entry.course_ids != (
        spec.selection.course_id,
    ):
        raise UnverifiedBinding("import catalog scope")
    for target in (spec.content.root, spec.content.cursor_key_file, job_root):
        if target.is_relative_to(entry.root) or entry.root.is_relative_to(target):
            raise UnverifiedBinding(
                "separate approved, content, key and job roots required"
            )
    workspace = spec.selection.bundle.workspace
    if not workspace.is_relative_to(entry.root):
        raise UnverifiedBinding("bundle workspace outside approved root")
    for name in type(spec.selection.bundle).model_fields:
        value = getattr(spec.selection.bundle, name)
        if name.endswith("_path") and value is not None:
            p = value if value.is_absolute() else workspace / value
            if not p.is_relative_to(entry.root) or ".." in p.parts:
                raise UnverifiedBinding("bundle input outside approved root")
            relative = p.relative_to(entry.root).as_posix()
            if relative not in entry.files:
                raise UnverifiedBinding("bundle role not declared")
    return spec


def authorize(spec, actor, db, *, job_owner=None):
    if (
        actor.role != "operator"
        or actor.subject not in spec.allowed_subjects
        or spec.selection.course_id not in actor.courses
        or job_owner is not None
        and actor.subject != job_owner
    ):
        raise Forbidden("import permission required")
    source_id = spec.selection.source_id
    if db.execute("SELECT 1 FROM sources WHERE id=?", (source_id,)).fetchone():
        ContentStore._authorize(db, source_id, actor, write=True)


def authorize_job(store, job, actor):
    spec = plan(store.entry(job.job_id), store.root)
    with ContentStore(spec.content.root)._connection() as db:
        authorize(spec, actor, db, job_owner=job.initiated_by)


def state(spec, db, actor):
    authorize(spec, actor, db)
    sid = spec.selection.source_id
    data = {
        table: [
            tuple(row)
            for row in db.execute(
                "SELECT id,state"
                + (",acl_revision" if table == "sources" else "")
                + f" FROM {table} WHERE "
                + ("id" if table == "sources" else "source_id")
                + "=? ORDER BY id",
                (sid,),
            ).fetchall()
        ]
        for table in (
            "sources",
            "source_versions",
            "parsed_versions",
            "processing_runs",
        )
    }
    active = any(
        row[1] in {"preparing", "prepared", "blocked"}
        for row in data["processing_runs"]
    )
    return fingerprint(data), active


def mapped_bundle(spec, original_root, new_root):
    bundle = spec.selection.bundle
    values = {}
    for name in type(bundle).model_fields:
        value = getattr(bundle, name)
        if name == "workspace":
            value = new_root / value.relative_to(original_root)
        elif name.endswith("_path") and value is not None:
            original = value if value.is_absolute() else bundle.workspace / value
            value = new_root / original.relative_to(original_root)
        values[name] = value
    return type(bundle)(**values)


@contextmanager
def verified(entry, spec):
    # Only declared hash-checked bytes are installed. Gates can never follow a
    # changing original payload to an undeclared file during preview/dispatch.
    values = verified_files(entry)
    with tempfile.TemporaryDirectory(prefix="content-import-inputs-") as root:
        target = Path(root)
        for relative, data in values.items():
            path = target / relative
            path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(data)
            path.chmod(0o600)
        bundle = mapped_bundle(spec, entry.root, target)
        candidate = (
            verify_material_bundle(bundle)
            if isinstance(bundle, MaterialBundle)
            else verify_srt_bundle(bundle)
        )
        detail = _candidate(candidate)
        selected = spec.selection
        if (
            detail.registration.resolved_id != selected.source_id
            or detail.registration.course_id != selected.course_id
            or detail.config.implementation_revision
            != selected.expected_implementation_revision
        ):
            raise UnverifiedBinding("import selection contradicts gate")
        # No real-source release contract has been authorized for this MVP.
        if detail.registration.source_origin != "synthetic":
            raise Forbidden("real source release required")
        yield candidate, detail


def inspect(entry, spec, actor, input_ref):
    store = ContentStore(spec.content.root)
    with store._maintenance(), store._connection() as db:
        authorize(spec, actor, db)
    with verified(entry, spec) as (_, detail):
        existing = _existing(store, detail, actor)
        sv = _source_version(detail)
        stream = ParsedDocument(
            source_id=sv.source_id, representation_key=detail.representation
        )
        slot = deterministic_id(
            "content_slot_v1",
            sv.source_version_id,
            stream.parsed_document_id,
            detail.config.config_id,
        )
        parsed = deterministic_id(
            "content_version_v1",
            slot,
            sha256(detail.payload),
            sha256(detail.projection),
        )
        with store._maintenance(), store._connection() as db:
            digest, active = state(spec, db, actor)
        return ImportInfo(
            input_ref=input_ref,
            source_id=sv.source_id,
            course_id=spec.selection.course_id,
            adapter=spec.selection.kind,
            parser_config_id=detail.config.config_id,
            parser_name=detail.config.parser_name,
            parser_version=detail.config.parser_version,
            implementation_revision=detail.config.implementation_revision,
            source_version_id=sv.source_version_id,
            parsed_version_id=parsed,
            raw_sha256=sha256(detail.raw),
            payload_sha256=sha256(detail.payload),
            state_sha256=digest,
            existing_parsed_version_id=existing,
            can_import=not active,
            operator_decision="content_recovery_required" if active else None,
        )


def prepare(entry, actor, job_root, params):
    spec = plan(entry, job_root)
    info = inspect(entry, spec, actor, params["source_ref"])
    if not info.can_import or info.state_sha256 != params["state_sha256"]:
        raise Conflict("import state changed or recovery required")
    return info


def run(store, job, entry, output):
    # Stored spec keeps original approved roots. Only its bundle paths are remapped
    # into the already pinned C16 input snapshot; provenance bytes stay untouched.
    original = store.entry(job.job_id)
    spec = plan(original, store.root)
    actor = Principal(
        subject=job.initiated_by,
        role="operator",
        courses=(job.parameters["course_id"],),
    )
    current = ContentStore(spec.content.root, read_only=False)
    with current._maintenance(), current._connection() as db:
        digest, active = state(spec, db, actor)
        if active or digest != job.parameters["state_sha256"]:
            raise Conflict("import state changed before publication")
    pinned = spec.model_copy(
        update={
            "selection": spec.selection.model_copy(
                update={"bundle": mapped_bundle(spec, original.root, entry.root)}
            )
        }
    )
    with verified(entry, pinned) as (candidate, detail):
        with current._maintenance(), current._connection() as db:
            digest, active = state(spec, db, actor)
            if active or digest != job.parameters["state_sha256"]:
                raise Conflict("import state changed during verification")
        result = import_verified_bundle(
            current, candidate, actor=actor, request_key="import_" + job.job_id
        )
    version = result.version
    receipt = ImportReceipt(
        job_id=job.job_id,
        source_id=version.source_id,
        source_version_id=version.source_version_id,
        parsed_version_id=version.parsed_version_id,
        raw_sha256=sha256(detail.raw),
        payload_sha256=version.payload.sha256,
        created=result.created,
        parsed_route=route("parsed", version.parsed_version_id),
    )
    with output.open("xb") as stream:
        stream.write(canonical(receipt.model_dump(mode="json")))
        stream.flush()
        os.fsync(stream.fileno())
    output.chmod(0o600)
