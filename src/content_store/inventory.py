"""Read-only evaluation of an explicit bundle list using the existing B gates."""

from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from src.content_store.adapters import (
    MaterialBundle,
    SRTBundle,
    _capture,
    _json_bytes,
    _read,
    _verify_frozen,
)
from src.content_store.errors import (
    Conflict,
    ContentStoreError,
    InvalidInput,
    UnverifiedBinding,
)
from src.content_store.models import (
    ParsedDocumentVersion,
    ParserConfiguration,
    canonical,
    checked_actor,
    sha256,
    snapshot,
)
from src.content_store.publication import _known_source_version, _source_version
from src.job_control.models import Contract, Identifier, Sha
from src.model_discovery.cs50 import CourseId
from src.model_materials.materials import ArtifactReceipt
from src.tools_lecture.adapt_cs50 import CS50AdapterPlan


class InventorySelection(Contract):
    schema_version: Literal[1] = 1
    entry_id: Identifier
    kind: Literal["material", "srt"]
    source_id: str = Field(min_length=1, max_length=500)
    course_id: CourseId
    expected_implementation_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    bundle: MaterialBundle | SRTBundle

    @model_validator(mode="after")
    def typed_bundle(self):
        expected = MaterialBundle if self.kind == "material" else SRTBundle
        if type(self.bundle) is not expected or not self.bundle.workspace.is_absolute():
            raise ValueError("Explicit absolute workspace and matching bundle required")
        return self


class InventoryRequest(Contract):
    schema_version: Literal[1] = 1
    entries: tuple[InventorySelection, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def unique_entries(self):
        if len({e.entry_id for e in self.entries}) != len(self.entries):
            raise ValueError("Duplicate inventory entry")
        return self


class InventoryResult(Contract):
    entry_id: Identifier
    source_id: str
    course_id: CourseId
    kind: Literal["material", "srt"]
    expected_implementation_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    supplied_paths: dict[str, str]
    expected_original_paths: dict[str, str]
    hashes: dict[str, Sha]
    parser: ParserConfiguration | None = None
    section_keys: tuple[str, ...] = ()
    lecture_ids: tuple[str, ...] = ()
    source_version_id: str | None = None
    existing_parsed_version_id: str | None = None
    validation_status: Literal["verified", "blocked"]
    issues: tuple[str, ...] = ()
    manual_approvals: tuple[Literal["D06", "D07"], ...] = ()


class InventoryBody(Contract):
    schema_version: Literal[1] = 1
    kind: Literal["cs50-content-inventory-v1"] = "cs50-content-inventory-v1"
    entries: tuple[InventoryResult, ...]


class InventoryReport(Contract):
    report: InventoryBody
    sha256: Sha

    @model_validator(mode="after")
    def digest(self):
        if sha256(canonical(self.report.model_dump(mode="json"))) != self.sha256:
            raise ValueError("Inventory report digest mismatch")
        return self


def _paths(selection):
    bundle = selection.bundle
    return {
        field.removesuffix("_path"): str(
            value if value.is_absolute() else bundle.workspace / value
        )
        for field in type(bundle).model_fields
        if field.endswith("_path") and (value := getattr(bundle, field)) is not None
    }


def _binding_details(files, paths, selection):
    """Report claimed canonical paths; only the subsequent gate verifies them."""
    root = selection.bundle.workspace
    if selection.kind == "material":
        receipt = ArtifactReceipt.model_validate(_json_bytes(files[paths["receipt"]]))
        binding = receipt.binding
        directory = binding.material_id.split(":")[1]
        expected = {
            "raw": str(root / directory / receipt.raw_path),
            "payload": str(root / receipt.normalized_path),
            "receipt": str(root / directory / "receipt.v1.json"),
        }
        return expected, binding.resource.section_keys, binding.lecture_ids
    plan = CS50AdapterPlan.model_validate(_json_bytes(files[paths["plan"]]))
    bindings = [
        b
        for c in plan.courses
        for b in c.bindings
        if b.source_id == selection.source_id
    ]
    if len(bindings) != 1:
        raise UnverifiedBinding("one explicit source binding required")
    binding = bindings[0]
    return (
        {
            "raw": str(root / binding.raw_srt_path),
            "payload": str(root / binding.transcript_json_path),
            "receipt": str(root / binding.raw_srt_path.parent / "execution.v1.json"),
        },
        (binding.section_key,),
        (binding.lecture_id,),
    )


def _existing(store, verified, actor):
    """Import readiness, not a latest-version selector; no register/reserve/stage."""
    expected = _source_version(verified)
    with store._maintenance(), store._connection() as db:
        row = db.execute(
            "SELECT id FROM sources WHERE id=?", (expected.source_id,)
        ).fetchone()
        if row is None:
            return None
        source = store._authorize(db, expected.source_id, actor, write=True)
        if source.registration != verified.registration:
            raise Conflict("inventory source identity conflict")
        if db.execute(
            "SELECT 1 FROM source_versions WHERE id=?", (expected.source_version_id,)
        ).fetchone():
            _known_source_version(store, db, verified)
        slot = _json_bytes(verified.projection)["slot_id"]
        row = db.execute(
            "SELECT data FROM parsed_versions WHERE slot_id=?", (slot,)
        ).fetchone()
        if row is None:
            return None
        version = ParsedDocumentVersion.model_validate_json(row[0])
        store._parsed(db, version.parsed_version_id, actor)
        if version.payload.sha256 != sha256(
            verified.payload
        ) or version.projection.sha256 != sha256(verified.projection):
            raise Conflict("inventory imports same slot with different bytes")
        return version.parsed_version_id


def inventory(request: InventoryRequest, *, actor, store=None) -> InventoryReport:
    """No input/store changes. Scratch snapshots are private and automatically removed."""
    if type(request) is not InventoryRequest:
        raise InvalidInput("typed v1 inventory request required")
    request = snapshot(request)
    actor = checked_actor(actor)
    if actor.role != "operator" or (store is not None and not store.read_only):
        raise InvalidInput("operator and read-only inventory handle required")
    results = []
    for entry in request.entries:
        supplied = _paths(entry)
        values = dict(
            entry_id=entry.entry_id,
            source_id=entry.source_id,
            course_id=entry.course_id,
            kind=entry.kind,
            expected_implementation_revision=entry.expected_implementation_revision,
            supplied_paths=supplied,
            expected_original_paths={},
            hashes={},
            validation_status="blocked",
        )
        # Every non-synthetic selection remains subject to separate real-data release.
        values["manual_approvals"] = ("D06", "D07")
        try:
            if entry.course_id not in actor.courses:
                from src.content_store.errors import Forbidden

                raise Forbidden("inventory course outside actor scope")
            frozen = _capture(entry.bundle, entry.kind)
            files, paths = dict(frozen.files), dict(frozen.paths)
            values["hashes"] = {
                role: sha256(files[path]) for role, path in paths.items()
            }
            expected, sections, lectures = _binding_details(files, paths, entry)
            values.update(
                expected_original_paths=expected,
                section_keys=sections,
                lecture_ids=lectures,
            )
            verified = _verify_frozen(frozen)
            values["parser"] = verified.config
            if (
                verified.registration.resolved_id != entry.source_id
                or verified.registration.course_id != entry.course_id
                or verified.config.implementation_revision
                != entry.expected_implementation_revision
            ):
                raise UnverifiedBinding(
                    "inventory selection contradicts verified bundle"
                )
            values["source_version_id"] = _source_version(verified).source_version_id
            if store is not None:
                values["existing_parsed_version_id"] = _existing(store, verified, actor)
            values["manual_approvals"] = (
                ()
                if verified.registration.source_origin == "synthetic"
                else ("D06", "D07")
            )
            values["validation_status"] = "verified"
        except ContentStoreError as error:
            values["issues"] = (error.code,)
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            RecursionError,
        ):
            values["issues"] = ("unverified_binding",)
        if not values["hashes"] and values["issues"] == ("unverified_binding",):
            # Individually observed explicit inputs of an incomplete bundle are
            # diagnostic only. They never issue a candidate or pass a gate.
            files, paths, total = {}, {}, 0
            for role, path in supplied.items():
                role = "payload" if role in {"normalized", "transcript"} else role
                try:
                    data = _read(Path(path))
                    total += len(data)
                    if total > 256 * 1024 * 1024:
                        break
                    files[role] = data
                    paths[role] = role
                    values["hashes"][role] = sha256(data)
                except (OSError, ContentStoreError):
                    continue
            try:
                expected, sections, lectures = _binding_details(files, paths, entry)
                values.update(
                    expected_original_paths=expected,
                    section_keys=sections,
                    lecture_ids=lectures,
                )
            except (
                OSError,
                ValueError,
                TypeError,
                KeyError,
                RecursionError,
                ContentStoreError,
            ):
                pass
        results.append(InventoryResult(**values))
    body = InventoryBody(entries=tuple(results))
    return InventoryReport(
        report=body, sha256=sha256(canonical(body.model_dump(mode="json")))
    )


def report_bytes(report: InventoryReport) -> bytes:
    return canonical(report.model_dump(mode="json")) + b"\n"


def output_path(path, request, *, store_root=None):
    """Reports cannot land inside selected workspaces, inputs, or a ContentStore."""
    path = Path(path).absolute()
    from src.tools_lecture.execute_cs50 import safe_path

    safe_path(path.parent, path)
    for entry in request.entries:
        if (
            path.is_relative_to(entry.bundle.workspace)
            or str(path) in _paths(entry).values()
        ):
            raise InvalidInput("report overlaps inventory input")
    if store_root is not None and path.is_relative_to(store_root):
        raise InvalidInput("report overlaps content store")
    return path
