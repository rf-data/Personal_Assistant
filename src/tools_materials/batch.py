"""Explicit CS50 archive-to-C18 handoff. C16 remains the only execution queue."""

import shutil
import time
from pathlib import Path
from typing import Literal

import httpx
from pydantic import Field, model_validator

from src.job_control.catalog import read_file, safe_path, verified_files
from src.job_control.controller import Controller, authenticate
from src.job_control.models import CatalogEntry, Contract, Sha, fingerprint
from src.job_control.operations import fence, preflight, private
from src.model_materials.materials import ArtifactReceipt, MaterialResource
from src.tools_materials.download import MaterialDownloader
from src.tools_materials.processing import make_plan, parser_for
from src.tools_materials.quality import _json
from src.tools_materials.storage import artifact_root, publish_bytes
from src.workflows.definition import prepare
from src.workflows.models import Definition
from src.workflows.service import inspect, submit


class Batch(Contract):
    schema_version: Literal[1] = 1
    manifest: Path
    files: dict[str, Sha] = Field(min_length=1, max_length=120)
    materials: tuple[MaterialResource, ...] = Field(min_length=1, max_length=32)
    source_origin: Literal["official", "synthetic"] = "official"
    max_bytes: int = Field(default=1048576, strict=True, ge=1, le=1048576)

    @model_validator(mode="after")
    def identities(self):
        if not self.manifest.is_absolute() or ".." in self.manifest.parts:
            raise ValueError("Explicit snapshot manifest required")
        if len({b.material_id for b in self.materials}) != len(self.materials):
            raise ValueError("Duplicate selected material")
        for name in self.files:
            safe_path(self.manifest.parent, name)
        return self


class SourceApproval(Contract):
    """Operator declaration, not an alternative backend identity/capability."""

    material_id: str = Field(min_length=1, max_length=200)
    source_id: str = Field(min_length=1, max_length=200)
    course_id: str = Field(min_length=1, max_length=100)
    original_url: str = Field(min_length=1, max_length=2000)
    approval_reference: str = Field(min_length=1, max_length=2000)
    usage_reference: str = Field(min_length=1, max_length=2000)
    license_review_reference: str = Field(min_length=1, max_length=2000)
    robots_review_reference: str = Field(min_length=1, max_length=2000)
    retention_reference: str = Field(min_length=1, max_length=2000)
    revocation_reference: str = Field(min_length=1, max_length=2000)
    download: bool = Field(default=False, strict=True)
    process: bool = Field(default=False, strict=True)
    expected_sha256: Sha | None = None

    @model_validator(mode="after")
    def concrete_references(self):
        if any(
            not value.strip()
            for name, value in self.model_dump().items()
            if name.endswith("_reference")
        ):
            raise ValueError("Nonblank operator evidence required")
        return self


class Approvals(Contract):
    schema_version: Literal[1] = 1
    sources: tuple[SourceApproval, ...] = Field(default=(), max_length=32)
    min_interval_seconds: float = Field(default=2.0, ge=1, le=60, allow_inf_nan=False)

    @model_validator(mode="after")
    def unique(self):
        if len({s.material_id for s in self.sources}) != len(self.sources):
            raise ValueError("Duplicate source approvals")
        return self


def sha(raw):
    import hashlib

    return hashlib.sha256(raw).hexdigest()


def output(path, value):
    from src.content_store.models import canonical

    path = artifact_root(Path(path))
    private(path.parent, directory=True)
    publish_bytes(path, canonical(value) + b"\n")


def plan(manifest, courses, resources=(), *, synthetic=False):
    if not courses or len(set(courses)) != len(courses):
        raise ValueError("Explicit unique course selection required")
    manifest = safe_path(Path(manifest))
    raw = read_file(manifest)
    data = _json(raw)
    known = {c["course_id"] for c in data["courses"]}
    if set(courses) - known:
        raise ValueError("Unknown selected course")
    origin = "synthetic" if synthetic else "official"
    bindings = tuple(
        b.model_copy(update=dict(source_origin=origin))
        for b in make_plan(manifest).materials
        if b.resource.course_id in courses
        and (not resources or b.source_id in resources or b.material_id in resources)
    )
    if resources and set(resources) - {
        key for b in bindings for key in (b.source_id, b.material_id)
    }:
        raise ValueError("Unknown/out-of-course selected resource")
    files = {manifest.name: sha(raw)}
    for course in data["courses"]:
        for page in course["pages"]:
            content = read_file(safe_path(manifest.parent, page["file"]))
            if page.get("sha256") and sha(content) != page["sha256"]:
                raise ValueError("Discovery snapshot hash mismatch")
            files[page["file"]] = sha(content)
    return Batch(
        manifest=manifest, files=files, materials=bindings, source_origin=origin
    )


def load_batch(path):
    data = _json(read_file(safe_path(Path(path))))
    batch = Batch.model_validate(data["batch"])
    if data["sha256"] != fingerprint(batch.model_dump(mode="json")):
        raise ValueError("Batch digest mismatch")
    for name, digest in batch.files.items():
        if sha(read_file(safe_path(batch.manifest.parent, name))) != digest:
            raise ValueError("Snapshot bytes changed")
    current = plan(
        batch.manifest,
        sorted({b.resource.course_id for b in batch.materials}),
        [b.material_id for b in batch.materials],
        synthetic=batch.source_origin == "synthetic",
    )
    if current.materials != batch.materials or current.files != batch.files:
        raise ValueError("Snapshot/selection binding changed")
    return batch


def load_approvals(path):
    return Approvals.model_validate(_json(read_file(private(Path(path)))))


def approval(binding, approvals, step):
    matches = [a for a in approvals.sources if a.material_id == binding.material_id]
    if len(matches) != 1:
        raise PermissionError("Explicit per-source approval missing")
    item = matches[0]
    if (item.source_id, item.course_id, item.original_url) != (
        binding.source_id,
        binding.resource.course_id,
        binding.original_url,
    ) or not getattr(item, step):
        raise PermissionError("Source/URL/course/step not approved")
    return item


def supported(binding):
    config, _status, _reason = parser_for(binding)
    return config is not None and config.name in {"html", "pdf", "code"}


def reviewed(binding):
    return binding.model_copy(update=dict(license_status="reviewed"))


def obtain(
    batch,
    archive,
    approvals,
    *,
    execute=False,
    retry_failed=False,
    transport=None,
    sleep=time.sleep,
):
    """Serial existing downloader; no automatic retries or second job store."""
    archive = artifact_root(Path(archive))
    if execute:
        private(archive, directory=True)
        if (
            shutil.disk_usage(archive).free
            < 512 * 1024**2 + len(batch.materials) * batch.max_bytes
        ):
            raise ValueError("Download capacity reserve")
    downloader = MaterialDownloader(
        archive, max_bytes=batch.max_bytes, retries=0, transport=transport
    )
    rows, transfers = [], 0
    for binding in batch.materials:
        row = dict(
            material_id=binding.material_id,
            source_id=binding.source_id,
            course_id=binding.resource.course_id,
            original_url=binding.original_url,
        )
        try:
            if not supported(binding):
                row.update(status="unsupported", reason="not_in_c18_material_contract")
            elif not execute:
                row.update(status="selected", execute=False)
            else:
                grant = approval(binding, approvals, "download")
                b = reviewed(binding)
                raw, receipt_path = downloader.paths(b)
                if receipt_path.exists():
                    old = ArtifactReceipt.model_validate_json(read_file(receipt_path))
                    if old.status in {"failed", "conflict"} and not retry_failed:
                        raise PermissionError(
                            "Failed attempt requires explicit retry decision"
                        )
                reusable = receipt_path.exists() and raw.exists()
                if transfers and not reusable:
                    sleep(approvals.min_interval_seconds)
                transfers += not reusable
                receipt = downloader.obtain(b, execute=True, license_reviewed=True)
                if (
                    grant.expected_sha256
                    and receipt.raw_sha256 != grant.expected_sha256
                ):
                    raise ValueError("Expected raw hash mismatch")
                row.update(
                    status="verified",
                    raw_sha256=receipt.raw_sha256,
                    receipt_sha256=sha(read_file(receipt_path)),
                    reused=reusable,
                )
        except (ValueError, OSError, RuntimeError, httpx.HTTPError) as error:
            row.update(
                status="blocked" if isinstance(error, PermissionError) else "failed",
                error_class=type(error).__name__,
            )
        rows.append(row)
    return dict(
        schema_version=1,
        batch_sha256=fingerprint(batch.model_dump(mode="json")),
        execution_requested=execute,
        materials=rows,
    )


def seal(batch, archive, destination, approvals):
    """New immutable C16 input bundles, including the original HTTP receipts."""
    archive = private(artifact_root(Path(archive)), directory=True)
    destination = artifact_root(Path(destination))
    private(destination.parent, directory=True)
    if (
        destination == archive
        or destination.is_relative_to(archive)
        or archive.is_relative_to(destination)
    ):
        raise ValueError("Separate catalog and archive roots required")
    if destination == batch.manifest.parent or destination.is_relative_to(
        batch.manifest.parent
    ):
        raise ValueError("Separate snapshot and output roots required")
    if (
        shutil.disk_usage(destination.parent).free
        < 512 * 1024**2
        + sum(
            len(read_file(safe_path(batch.manifest.parent, name)))
            for name in batch.files
        )
        * len(batch.materials)
        + len(batch.materials) * batch.max_bytes
    ):
        raise ValueError("Catalog capacity reserve")
    destination.mkdir(mode=0o700)
    downloader = MaterialDownloader(archive, max_bytes=batch.max_bytes)
    catalog, rows = {}, []
    for binding in batch.materials:
        row = dict(
            material_id=binding.material_id, course_id=binding.resource.course_id
        )
        try:
            if not supported(binding):
                row.update(status="unsupported", reason="not_in_c18_material_contract")
                rows.append(row)
                continue
            grant = approval(binding, approvals, "process")
            b = reviewed(binding)
            receipt = downloader.validate(b)
            raw_path, receipt_path = downloader.paths(b)
            raw = read_file(raw_path, batch.max_bytes)
            receipt_bytes = read_file(receipt_path)
            if (
                sha(raw) != receipt.raw_sha256
                or ArtifactReceipt.model_validate_json(receipt_bytes) != receipt
            ):
                raise ValueError("Archive changed during handoff")
            if grant.expected_sha256 and sha(raw) != grant.expected_sha256:
                raise ValueError("Expected raw hash mismatch")
            ref = "c26_" + fingerprint([binding.material_id, sha(raw)])[:40]
            root = destination / ref
            root.mkdir(mode=0o700)
            for name in batch.files:
                path = root / "discovery" / name
                path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                data = read_file(safe_path(batch.manifest.parent, name))
                if sha(data) != batch.files[name]:
                    raise ValueError("Snapshot changed during handoff")
                publish_bytes(path, data)
                path.chmod(0o600)
            publish_bytes(root / "raw.source", raw)
            publish_bytes(root / "download_receipt.v1.json", receipt_bytes)
            output(root / "approval.json", grant.model_dump(mode="json"))
            definition = Definition(
                course_id=binding.resource.course_id,
                sources={binding.source_id: "raw.source"},
                source_origin=batch.source_origin,
                max_bytes=batch.max_bytes,
            )
            output(root / "workflow.json", definition.model_dump(mode="json"))
            entry = CatalogEntry(
                kind="workflow_bundle",
                root=root,
                files={
                    p.relative_to(root).as_posix(): sha(read_file(p))
                    for p in root.rglob("*")
                    if p.is_file()
                },
                roles=dict(
                    manifest="discovery/" + batch.manifest.name,
                    workflow="workflow.json",
                ),
                course_ids=(binding.resource.course_id,),
            )
            prepare(
                entry
            )  # Existing discovery, parser, graph and full hash validation.
            catalog[ref] = entry.model_dump(mode="json")
            row.update(status="sealed", source_ref=ref, raw_sha256=receipt.raw_sha256)
        except (ValueError, OSError, RuntimeError) as error:
            row.update(
                status="blocked" if isinstance(error, PermissionError) else "failed",
                error_class=type(error).__name__,
            )
        rows.append(row)
    result = dict(
        schema_version=1,
        batch_sha256=fingerprint(batch.model_dump(mode="json")),
        catalog=catalog,
        materials=rows,
    )
    result["sha256"] = fingerprint(result)
    output(
        destination / "catalog.json", result
    )  # Last: partial directory is not a published catalog.
    return result


def control(config, token_file, catalog_file, action, refs=(), *, confirm=False):
    """One explicit bounded submission/report, never runs its own executor."""
    settings = preflight(Path(config))
    with fence(settings.root):
        return _control(
            settings, token_file, catalog_file, action, refs, confirm=confirm
        )


def _control(settings, token_file, catalog_file, action, refs, *, confirm):
    if action not in {"preview", "execute", "resume", "cancel", "report"}:
        raise ValueError("Unknown C18 action")
    writing = action in {"execute", "resume", "cancel"}
    if writing and (not confirm or not 1 <= len(refs) <= 8):
        raise ValueError("Explicit confirmation and one to eight source refs required")
    actor = authenticate(
        settings, "Bearer " + read_file(private(Path(token_file)), 257).decode().strip()
    )
    document = _json(read_file(private(Path(catalog_file))))
    if document.get("sha256") != fingerprint(
        {k: v for k, v in document.items() if k != "sha256"}
    ):
        raise ValueError("Catalog publication digest mismatch")
    selected = tuple(refs) or tuple(document["catalog"])
    if len(set(selected)) != len(selected) or len(selected) > 32:
        raise ValueError("Bounded unique source refs required")
    for ref in selected:
        entry = CatalogEntry.model_validate(document["catalog"][ref])
        if entry != settings.catalog.get(ref) or not set(entry.course_ids).issubset(
            actor.courses
        ):
            raise PermissionError("Current C16 catalog/course approval required")
        verified_files(entry)
    workflows = []
    for ref in selected:
        if action in {"execute", "resume"}:
            submit(settings, actor, ref, ref, resume=action == "resume")
        report, _prepared, job = inspect(settings, actor, ref, ref)
        if action == "cancel":
            if job is None:
                raise ValueError("No C16 job to cancel")
            Controller(settings).cancel(actor, job.job_id)
            report, _prepared, job = inspect(settings, actor, ref, ref)
        workflows.append(
            dict(
                source_ref=ref,
                job=job.model_dump(mode="json") if job else None,
                report=report.model_dump(mode="json"),
            )
        )
    return dict(
        schema_version=1,
        batch_sha256=document["batch_sha256"],
        materials=[
            row
            for row in document["materials"]
            if row["course_id"] in actor.courses
            and (not row.get("source_ref") or row["source_ref"] in selected)
        ],
        workflows=workflows,
    )
