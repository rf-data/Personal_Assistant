"""Prepare one existing CS50 HTML selection; never downloads or starts a job."""

import argparse
import fcntl
import json
import os
import shutil
import sqlite3
from contextlib import ExitStack, closing
from pathlib import Path

from src.job_control.catalog import read_file, safe_path, verified_files
from src.job_control.controller import authenticate
from src.job_control.models import CatalogEntry, Identity, Job, Settings, fingerprint
from src.job_control.operations import private
from src.model_materials.materials import MaterialResource
from src.tools_materials import batch as api
from src.tools_materials.capacity import CapacityLimits, check_capacity, estimate
from src.tools_materials.download import MaterialDownloader
from src.tools_materials.quality import _json
from src.tools_materials.storage import artifact_root, publish_bytes
from src.workflows.definition import prepare

COURSE = "cs50_python"
SOURCE = "resource:f06e4055b5ef61f0a693c522f1c57880c88edc20c177cfb79fefbffee5b8767a"
URL = "https://cs50.harvard.edu/python/notes/0/"
SNAPSHOTS = {
    "cs50_python/index.html": "228fd09a21987bc55147b7c9660c9f496dda49d234ebc1cb620e58fcb2963efe",
    "cs50_python/week_0.html": "8526668d7cffb93fed9e32f66888dd8b77eed2d643b4527dba0df44a5c6f08e0",
}
MOUNTS = tuple(
    Path("/app") / name for name in ("data", "logs", ".cache", "configuration")
)
SCRIPTS = (
    "cs50_batch.py",
    "cs50_worker.py",
    "cs50_material_quality.py",
    "deployment.py",
    "cs50_materials.py",
    "cs50_workflow.py",
    "worker_image_smoke.py",
)
CODE = Path(api.__file__).resolve().parents[2]
RESERVE = 5 * 1024**3


class Blocked(ValueError):
    pass


def mountpoints():
    """Exact kernel mount entries, including same-filesystem bind mounts."""
    try:
        from src.runtime_paths import mounts
    except ImportError as error:
        raise Blocked("worker_path_policy_update_missing") from error
    try:
        return mounts()
    except (OSError, ValueError, IndexError) as error:
        raise Blocked("kernel_mount_information_unavailable") from error


def location(root, *, policy_required=True):
    root = safe_path(Path(root))
    if root.parent != MOUNTS[0]:
        raise Blocked("new_direct_child_of_data_mount_required")
    mounted = mountpoints()
    for path in MOUNTS:
        safe_path(path)
        if path not in mounted or not path.is_dir():
            raise Blocked("persistent_bind_mount_missing")
        if (
            mounted[path]["filesystem"] not in {"ext4", "xfs", "btrfs"}
            or not mounted[path]["writable"]
        ):
            raise Blocked("persistent_mount_filesystem_not_verified")
    if not os.access(MOUNTS[0], os.W_OK | os.X_OK):
        raise Blocked("data_mount_not_writable")
    # Preserve the actual pipeline's repository/output policy. No alias or bypass.
    if policy_required:
        try:
            artifact_root(root)
            Settings(root=root / "jobs")
        except (ValueError, RuntimeError) as error:
            raise Blocked("repository_output_policy_blocks_mounted_data") from error
    return root


def authorize_paths(root, output):
    """Explicit operator grant for this one subtree and this observed mount."""
    from src.runtime_paths import POLICY_ENV, output_path

    root = location(root, policy_required=False)
    if root.exists():
        raise Blocked("pilot_destination_exists")
    output = safe_path(Path(output))
    if output.parent != MOUNTS[3] or output.exists():
        raise Blocked("new_private_policy_file_in_configuration_mount_required")
    identity = mountpoints()[MOUNTS[0]]
    if any(p != MOUNTS[0] and p.is_relative_to(root) for p in mountpoints()):
        raise Blocked("nested_mount_in_pilot_area")
    document = dict(
        schema_version=1,
        repository=str(CODE),
        roots=[
            dict(
                path=str(root),
                mount_point=str(MOUNTS[0]),
                mount_identity=identity,
                purposes=["material_artifacts"],
                owner_uid=os.geteuid(),
            ),
            dict(
                path=str(root / "jobs"),
                mount_point=str(MOUNTS[0]),
                mount_identity=identity,
                purposes=["job_workspace"],
                owner_uid=os.geteuid(),
            ),
        ],
    )
    publish_bytes(output, (json.dumps(document, sort_keys=True) + "\n").encode())
    previous = os.environ.get(POLICY_ENV)
    try:
        os.environ[POLICY_ENV] = str(output)
        output_path(root, "material_artifacts")
        output_path(root / "jobs", "job_workspace")
    finally:
        if previous is None:
            os.environ.pop(POLICY_ENV, None)
        else:
            os.environ[POLICY_ENV] = previous
    return {
        "status": "path_policy_prepared",
        "worker_uid": os.geteuid(),
        "requires_explicit_policy_environment": True,
    }


def limits():
    return CapacityLimits(
        reserve_bytes=RESERVE,
        max_materials=1,
        archive_bytes=64 * 1024**2,
        catalog_bytes=128 * 1024**2,
        job_bytes=512 * 1024**2,
    )


def selected(manifest):
    batch = api.plan(manifest, [COURSE], [SOURCE])
    (binding,) = batch.materials
    if (binding.original_url, binding.format, binding.role) != (URL, "html", "notes"):
        raise Blocked("selection_binding_mismatch")
    return batch


def export(snapshot_root, destination):
    """Copy exactly two already-versioned discovery snapshots, not a live page."""
    snapshot_root = safe_path(Path(snapshot_root))
    destination = artifact_root(Path(destination))
    if destination.exists():
        raise Blocked("bundle_destination_exists")
    original = _json(read_file(snapshot_root / "manifest.json"))
    course = next(c for c in original["courses"] if c["course_id"] == COURSE)
    pages = [p for p in course["pages"] if p["file"] in SNAPSHOTS]
    if {p["file"] for p in pages} != SNAPSHOTS.keys():
        raise Blocked("required_discovery_snapshots_missing")
    contents = {}
    for page in pages:
        data = read_file(safe_path(snapshot_root, page["file"]))
        if api.sha(data) != SNAPSHOTS[page["file"]] or page["sha256"] != api.sha(data):
            raise Blocked("versioned_snapshot_hash_mismatch")
        contents[page["file"]] = data
    manifest = dict(original, courses=[dict(course, pages=pages)])
    destination.mkdir(mode=0o700)
    for name, data in contents.items():
        publish_bytes(destination / name, data)
    api.output(destination / "manifest.json", manifest)
    batch = selected(destination / "manifest.json")
    api.output(destination / "binding.json", batch.materials[0].model_dump(mode="json"))
    # Bind the exported helper version to the reviewed deployed runtime.
    publish_bytes(destination / "cs50_pilot.py", Path(__file__).read_bytes())
    api.output(
        destination / "files.json",
        {
            p.relative_to(destination).as_posix(): api.sha(read_file(p))
            for p in destination.rglob("*")
            if p.is_file()
        },
    )
    return {"status": "prepared", "source_id": SOURCE, "downloaded": False}


def bundle(path):
    path = safe_path(Path(path))
    inventory = _json(read_file(path / "files.json"))
    expected = {*SNAPSHOTS, "manifest.json", "binding.json", "cs50_pilot.py"}
    if set(inventory) != expected:
        raise Blocked("bundle_inventory_mismatch")
    for name, digest in inventory.items():
        if api.sha(read_file(safe_path(path, name))) != digest:
            raise Blocked("bundle_hash_mismatch")
    if inventory["cs50_pilot.py"] != api.sha(Path(__file__).read_bytes()):
        raise Blocked("helper_version_does_not_match_bundle")
    batch = selected(path / "manifest.json")
    binding = MaterialResource.model_validate_json(read_file(path / "binding.json"))
    if batch.materials != (binding,):
        raise Blocked("bundle_binding_mismatch")
    return batch


def initialize(source_bundle, root, subject, token_file):
    root = location(root)
    if root.exists():
        raise Blocked("pilot_destination_exists")
    source_bundle = safe_path(Path(source_bundle))
    batch = bundle(source_bundle)
    token_file = private(Path(token_file))
    token = read_file(token_file, 257).decode().strip()
    if (
        not 32 <= len(token) <= 256
        or not token.isascii()
        or any(c.isspace() for c in token)
    ):
        raise Blocked("private_operator_token_invalid")
    identity = Identity(
        subject=subject,
        role="operator",
        courses=(COURSE,),
        token_sha256=api.sha(token.encode()),
    )
    authenticate(
        Settings(root=root / "jobs", identities=(identity,)), "Bearer " + token
    )
    policy = limits()
    if (
        shutil.disk_usage(root.parent).free
        < estimate(batch, policy)["required_free_before_new_batch_bytes"]
    ):
        raise Blocked("insufficient_capacity_including_reserve")
    root.mkdir(mode=0o700)  # Exclusive; failures leave evidence, never retry in place.
    for name in ("inputs", "archive", "jobs", "reports"):
        (root / name).mkdir(mode=0o700)
    for name in (*batch.files, "binding.json"):
        publish_bytes(root / "inputs" / name, read_file(source_bundle / name))
    api.output(root / "limits.json", policy.model_dump(mode="json"))
    api.output(root / "identity.json", identity.model_dump(mode="json"))
    publish_bytes(root / "operator.token", token.encode() + b"\n")
    b = batch.materials[0]
    # Intentionally incomplete operator form; existing SourceApproval rejects it.
    request = dict(
        material_id=b.material_id,
        source_id=b.source_id,
        course_id=COURSE,
        original_url=URL,
        download=False,
        process=False,
        expected_sha256=None,
    )
    for name in (
        "approval",
        "usage",
        "license_review",
        "robots_review",
        "retention",
        "revocation",
    ):
        request[name + "_reference"] = ""
    api.output(
        root / "approvals.json",
        {"schema_version": 1, "sources": [request], "min_interval_seconds": 2.0},
    )
    return {"status": "awaiting_operator_approval", "source_id": SOURCE}


def inputs(root):
    root = location(root)
    try:
        private(root, directory=True)
    except (OSError, ValueError) as error:
        raise Blocked("pilot_root_missing_or_nonprivate") from error
    for name in ("inputs", "archive", "jobs", "reports"):
        try:
            private(root / name, directory=True)
        except (OSError, ValueError) as error:
            raise Blocked("required_private_" + name + "_directory_missing") from error
    from src.tools_materials.capacity import load_limits

    try:
        policy = load_limits(root / "limits.json")
    except (OSError, ValueError) as error:
        raise Blocked("limits_missing_or_invalid") from error
    if policy != limits():
        raise Blocked("single_html_pilot_limits_changed")
    try:
        batch = selected(root / "inputs/manifest.json")
        declared = MaterialResource.model_validate_json(
            read_file(private(root / "inputs/binding.json"))
        )
    except (OSError, ValueError) as error:
        raise Blocked("discovery_manifest_or_binding_invalid") from error
    if batch.materials != (declared,):
        raise Blocked("source_binding_changed")
    if (root / "batch.json").exists() and api.load_batch(root / "batch.json") != batch:
        raise Blocked("batch_binding_changed")
    try:
        identity = Identity.model_validate_json(
            read_file(private(root / "identity.json"))
        )
    except (OSError, ValueError) as error:
        raise Blocked("identity_missing_or_invalid") from error
    if identity.role != "operator" or identity.courses != (COURSE,):
        raise Blocked("operator_course_grant_required")
    try:
        token = read_file(private(root / "operator.token"), 257).decode().strip()
    except (OSError, ValueError) as error:
        raise Blocked("operator_token_missing_or_invalid") from error
    if api.sha(token.encode()) != identity.token_sha256:
        raise Blocked("operator_token_binding_mismatch")
    return root, policy, batch, identity


def grants(root, batch):
    try:
        approvals = api.load_approvals(root / "approvals.json")
        for step in ("download", "process"):
            api.approval(batch.materials[0], approvals, step)
    except (OSError, ValueError) as error:
        raise Blocked("explicit_source_download_process_approval_missing") from error
    return approvals


def archive_check(root, batch, approvals):
    binding = api.reviewed(batch.materials[0])
    downloader = MaterialDownloader(root / "archive", max_bytes=batch.max_bytes)
    raw, receipt_path = downloader.paths(binding)
    data = read_file(private(raw), batch.max_bytes)
    private(receipt_path)
    receipt = downloader.validate(binding)
    if (
        receipt.origin != "http_download"
        or receipt.status not in {"verified", "completed"}
        or receipt.mime_type not in {"text/html", "application/xhtml+xml"}
        or api.sha(data) != receipt.raw_sha256
    ):
        raise Blocked("verified_bounded_http_html_receipt_required")
    grant = api.approval(binding, approvals, "download")
    if grant.expected_sha256 and receipt.raw_sha256 != grant.expected_sha256:
        raise Blocked("expected_raw_hash_mismatch")
    return {
        "status": "verified",
        "bytes": len(data),
        "raw_sha256": receipt.raw_sha256,
        "receipt_sha256": api.sha(read_file(receipt_path)),
        "origin": receipt.origin,
    }


def catalog(root, batch, approvals):
    try:
        document = _json(read_file(private(root / "catalog/catalog.json")))
    except (OSError, ValueError) as error:
        raise Blocked("sealed_catalog_missing_or_invalid") from error
    if document.get("sha256") != fingerprint(
        {k: v for k, v in document.items() if k != "sha256"}
    ):
        raise Blocked("catalog_digest_mismatch")
    if (
        document["batch_sha256"] != fingerprint(batch.model_dump(mode="json"))
        or len(document["catalog"]) != 1
    ):
        raise Blocked("single_batch_catalog_required")
    downloader = MaterialDownloader(root / "archive", max_bytes=batch.max_bytes)
    b = api.reviewed(batch.materials[0])
    archive_check(root, batch, approvals)
    ref, raw_entry = next(iter(document["catalog"].items()))
    entry = CatalogEntry.model_validate(raw_entry)
    if (
        entry.root != root / "catalog" / ref
        or entry.course_ids != (COURSE,)
        or entry.kind != "workflow_bundle"
    ):
        raise Blocked("catalog_scope_or_root_mismatch")
    files = verified_files(entry)
    raw, http_receipt = downloader.paths(b)
    if files["raw.source"] != read_file(raw, batch.max_bytes) or files[
        "download_receipt.v1.json"
    ] != read_file(http_receipt):
        raise Blocked("catalog_archive_bytes_differ")
    prepared = prepare(entry)
    if (
        len(prepared.bindings) != 1
        or next(iter(prepared.bindings.values())) != batch.materials[0]
    ):
        raise Blocked("catalog_source_binding_mismatch")
    return document


def controller(root, document, identity):
    return Settings(
        root=root / "jobs",
        catalog=document["catalog"],
        identities=(identity,),
        execution_enabled=True,
        workflows_enabled=True,
        max_parallel=1,
        max_queued=1,
        max_jobs=3,
        worker_ttl=10,
    )


def configure(root):
    root, _policy, batch, identity = inputs(root)
    if (root / "jobs/jobs.sqlite3").exists():
        raise Blocked("existing_job_database_must_not_be_adopted")
    idle(root / "jobs")
    document = catalog(root, batch, grants(root, batch))
    settings = controller(root, document, identity)
    api.output(root / "controller.json", settings.model_dump(mode="json"))
    return {"status": "configured", "source_ref": next(iter(settings.catalog))}


def idle(root):
    """Read-only stopped-worker inspection, never Store(), recovery or lock creation."""
    if (root / "quarantine").exists():
        raise Blocked("job_quarantine_requires_operator_investigation")
    with ExitStack() as stack:
        for name in (".operations.lock", "worker.lock", ".bootstrap.lock"):
            path = root / name
            if not path.exists():
                continue
            stream = stack.enter_context(private(path).open("rb"))
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise Blocked("worker_or_operation_active") from error
        db = root / "jobs.sqlite3"
        if not db.exists():
            if list(root.iterdir()):
                raise Blocked("unknown_jobroot_contents")
            return []
        if any(
            not (root / name).is_file()
            for name in (".operations.lock", "worker.lock", ".bootstrap.lock")
        ):
            raise Blocked("existing_database_lock_evidence_missing")
        for suffix in ("-wal", "-journal"):
            path = root / (db.name + suffix)
            if path.exists() and private(path).stat().st_size:
                raise Blocked("database_requires_separate_investigation")
        private(db)
        with closing(
            sqlite3.connect(db.as_uri() + "?mode=ro&immutable=1", uri=True)
        ) as connection:
            if connection.execute("PRAGMA user_version").fetchone() != (1,):
                raise Blocked("unknown_job_database_version")
            if {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            } != {"jobs", "events", "worker"}:
                raise Blocked("unknown_job_database_schema")
            jobs = [
                Job.model_validate_json(data)
                for (data,) in connection.execute("SELECT data FROM jobs LIMIT 4")
            ]
            if len(jobs) > 3:
                raise Blocked("pilot_job_history_limit_exceeded")
            for job in jobs:
                if job.status in {"queued", "running", "cancel_requested"}:
                    raise Blocked("existing_job_requires_explicit_status_or_resume")
            return jobs


def preflight(root, phase):
    root, policy, batch, identity = inputs(root)
    approvals = grants(root, batch)
    for name in SCRIPTS:
        if not (CODE / "scripts" / name).is_file():
            raise Blocked("runtime_script_missing")
    required = estimate(batch, policy)["required_free_before_new_batch_bytes"]
    if shutil.disk_usage(root).free < required:
        raise Blocked("insufficient_capacity_including_reserve")
    for name, maximum in (
        ("archive", policy.archive_bytes),
        ("jobs", policy.job_bytes),
        ("reports", policy.report_bytes),
    ):
        check_capacity(root / name, maximum, policy.reserve_bytes)
    jobs = idle(root / "jobs")
    archive = {"status": "not_downloaded"}
    if phase == "plan":
        if (root / "batch.json").exists() or (root / "catalog").exists():
            raise Blocked("planning_output_already_exists")
    else:
        if not (root / "batch.json").exists():
            raise Blocked("planned_batch_missing")
        if phase == "download" and (root / "catalog").exists():
            raise Blocked("catalog_already_published_use_processing_checks")
        if phase == "download":
            downloader = MaterialDownloader(root / "archive", max_bytes=batch.max_bytes)
            binding = api.reviewed(batch.materials[0])
            raw, receipt = downloader.paths(binding)
            if raw.exists() or receipt.exists():
                try:
                    archive = archive_check(root, batch, approvals)
                except (ValueError, OSError) as error:
                    raise Blocked("archive_requires_explicit_investigation") from error
        if phase == "process":
            document = catalog(root, batch, approvals)
            archive = archive_check(root, batch, approvals)
            expected = controller(root, document, identity)
            try:
                actual = Settings.model_validate_json(
                    read_file(private(root / "controller.json"))
                )
            except (OSError, ValueError) as error:
                raise Blocked("controller_configuration_missing_or_invalid") from error
            if actual != expected:
                raise Blocked("controller_catalog_or_identity_changed")
            for job in jobs:
                if (
                    job.initiated_by != identity.subject
                    or job.process_id != "cs50_offline_workflow"
                    or tuple(job.input_refs) != tuple(actual.catalog)
                    or job.parameters.get("course_id") != COURSE
                ):
                    raise Blocked("foreign_job_in_pilot_database")
            authenticate(
                actual,
                "Bearer "
                + read_file(private(root / "operator.token"), 257).decode().strip(),
            )
    return {
        "status": "ready",
        "phase": phase,
        "source_id": SOURCE,
        "reserve_bytes": policy.reserve_bytes,
        "max_raw_bytes": batch.max_bytes,
        "archive": archive,
        "scope": "preflight_only_no_download_or_job",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("export")
    p.add_argument("--snapshots", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("init")
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--subject", required=True)
    p.add_argument("--token-file", type=Path, required=True)
    p.add_argument("--confirm-setup", action="store_true", required=True)
    p = sub.add_parser("authorize-paths")
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--confirm-setup", action="store_true", required=True)
    for command in ("configure", "preflight"):
        p = sub.add_parser(command)
        p.add_argument("--root", type=Path, required=True)
        if command == "preflight":
            p.add_argument(
                "--phase", choices=("plan", "download", "process"), required=True
            )
        else:
            p.add_argument("--confirm-setup", action="store_true", required=True)
    args = parser.parse_args(argv)
    os.umask(0o077)
    try:
        if args.command == "export":
            result = export(args.snapshots, args.output)
        elif args.command == "authorize-paths":
            result = authorize_paths(args.root, args.output)
        elif args.command == "init":
            result = initialize(args.bundle, args.root, args.subject, args.token_file)
        elif args.command == "configure":
            result = configure(args.root)
        else:
            result = preflight(args.root, args.phase)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (
        OSError,
        ValueError,
        RuntimeError,
        KeyError,
        StopIteration,
        sqlite3.Error,
    ) as error:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason": str(error)
                    if isinstance(error, Blocked)
                    else "invalid_or_unavailable_pilot_input",
                }
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
