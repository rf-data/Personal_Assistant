"""Only declared, hashed operator inputs. No browser filesystem traversal."""

import hashlib
import json
import os
from pathlib import Path

from src.job_control.models import Preview, fingerprint
from src.job_control.registry import process_for

MAX_FILE = 8 * 1024 * 1024
MAX_TOTAL = 32 * 1024 * 1024


def safe_path(root, relative=None):
    root = Path(root).absolute()
    path = root if relative is None else root / relative
    if ".." in path.parts or not path.is_relative_to(root):
        raise ValueError("Path outside approved directory")
    for item in (path, *path.parents):
        if item.is_symlink():
            raise ValueError("Symlink paths are forbidden")
    return path


def read_file(path, limit=MAX_FILE):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        import stat

        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError("Input must be a regular file")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            data = stream.read(limit + 1)
        if len(data) > limit:
            raise ValueError("Input size limit")
        return data
    finally:
        os.close(fd)


def verified_files(entry):
    total = 0
    values = {}
    for relative, expected in entry.files.items():
        data = read_file(safe_path(entry.root, relative))
        total += len(data)
        if total > MAX_TOTAL or hashlib.sha256(data).hexdigest() != expected:
            raise ValueError("Input hash or total size limit")
        values[relative] = data
    if entry.kind in {"manifest", "workflow_bundle"}:
        manifest = json.loads(values[entry.roles["manifest"]])
        parent = Path(entry.roles["manifest"]).parent
        for course in manifest["courses"]:
            for page in course["pages"]:
                name = (parent / page["file"]).as_posix()
                if name not in values:
                    raise ValueError("Manifest references an undeclared input")
    return values


def prepare_indexes(settings):
    """Read-only startup preflight, outside every HTTP request lifecycle."""
    from src.tools_materials.processing import make_plan

    indexes = {}
    for ref, entry in settings.catalog.items():
        if entry.kind not in {"manifest", "workflow_bundle"}:
            continue
        try:
            verified_files(entry)
            if entry.kind == "workflow_bundle":
                from src.workflows.definition import catalog_plan

                indexes[ref] = catalog_plan(entry)
            else:
                indexes[ref] = make_plan(safe_path(entry.root, entry.roles["manifest"]))
        except (ValueError, OSError, KeyError):
            # Only this input becomes unavailable; never advertise a fabricated plan.
            continue
    return indexes


def resolve_preview(settings, request, actor, indexes):
    process = process_for(request.process_id)
    if process.process_id == "cs50_offline_workflow" and not settings.workflows_enabled:
        raise PermissionError("Workflows require explicit operator configuration")
    if process.process_id == "material_parsing" and not settings.pdf_enabled:
        raise PermissionError("PDF jobs require explicit operator configuration")
    if process.process_id == "content_index_build" and not settings.index_jobs_enabled:
        raise PermissionError("Index jobs require explicit operator configuration")
    if process.process_id == "content_import" and not settings.import_jobs_enabled:
        raise PermissionError("Imports require explicit operator configuration")
    params = process.model.model_validate(request.parameters).model_dump(mode="json")
    course = params["course_id"]
    if course not in actor.courses:
        raise PermissionError("Course scope denied")
    ref = params.get("source_ref", params.get("material_ref"))
    entry = settings.catalog.get(ref)
    if (
        entry is None
        or entry.kind != process.input_kind
        or course not in entry.course_ids
    ):
        if process.process_id in {"content_index_build", "content_import"}:
            raise PermissionError("Index input unavailable")
        raise ValueError("Approved input reference/scope missing")
    values = verified_files(entry)
    if process.process_id == "content_import":
        from src.content_store.errors import ContentStoreError, Forbidden, NotFound
        from src.job_control.import_jobs import prepare
        from src.job_control.store import Unavailable

        try:
            prepare(entry, actor, settings.root, params)
        except (Forbidden, NotFound):
            raise PermissionError("Import input unavailable") from None
        except ContentStoreError as error:
            from src.content_store.errors import Conflict as ContentConflict
            from src.job_control.store import Conflict

            if isinstance(error, ContentConflict):
                raise Conflict("Import state changed") from None
            raise Unavailable("Import input verification unavailable") from None
    elif process.process_id == "content_index_build":
        from src.content_store.errors import ContentStoreError, Forbidden, NotFound
        from src.job_control.index_jobs import prepare
        from src.job_control.store import Unavailable

        try:
            prepare(entry, course, actor, settings.root, params["resume_of"])
        except (Forbidden, NotFound):
            raise PermissionError("Index input unavailable") from None
        except ContentStoreError:
            raise Unavailable("Index input verification unavailable") from None
    elif process.process_id == "material_planning":
        plan = indexes.get(ref)
        if plan is None:
            raise ValueError(
                "Approved planning index unavailable; recheck configuration"
            )
        rows = plan.select(
            course=course, section=params["section"], resource=params["resource_id"]
        )
        if len(rows) > 100:
            raise ValueError("Selection exceeds 100 materials")
    elif process.process_id == "cs50_offline_workflow":
        from src.workflows.definition import prepare

        prepared = prepare(entry, plan=indexes.get(ref))
        if prepared.definition.course_id != course:
            raise ValueError("Workflow course contradicts requested scope")
    elif process.process_id == "material_parsing":
        from src.job_control.pdf_adapter import prepare

        prepare(entry, course, values)
    else:
        from src.model_materials.materials import NormalizedDocument

        doc = NormalizedDocument.model_validate_json(values[entry.roles["normalized"]])
        if doc.binding.resource.course_id != course:
            raise ValueError("Material course contradicts requested scope")
    binding = dict(
        process_id=process.process_id,
        parameters=params,
        input_ref=ref,
        input_contract=entry.model_dump(mode="json"),
    )
    return Preview(
        preview_id=fingerprint(binding),
        process_id=process.process_id,
        parameters=params,
        input_refs=(ref,),
        expected_artifacts=(process.artifact_kind,),
    ), entry


def snapshot(entry, directory):
    """Copy approved bytes once. Existing destinations are never overwritten."""
    directory = safe_path(directory)
    directory.mkdir(mode=0o700)
    for relative, data in verified_files(entry).items():
        path = safe_path(directory, relative)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with path.open("xb") as stream:
            stream.write(data)
        path.chmod(0o400)
