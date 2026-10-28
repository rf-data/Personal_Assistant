"""Bounded CS50P download admission over the existing batch CLI/pipeline.

systemd owns process lifetime; C16 remains the only processing job engine.
"""

import argparse
import fcntl
import json
import os
import signal
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote, urlsplit

from src.job_control.catalog import read_file
from src.job_control.operations import private
from src.tools_materials import batch as api
from src.tools_materials.capacity import TransferBudget, load_limits
from src.tools_materials.https_transport import PublicHTTPSTransport


def admit(batch, limits, approvals):
    if (
        len(batch.materials) > 3
        or limits.max_materials > 3
        or limits.reserve_bytes < 5 * 1024**3
        or limits.archive_bytes > 64 * 1024**2
        or limits.job_bytes > 512 * 1024**2
    ):
        raise ValueError("Explicit small-host limits required")
    for binding in batch.materials:
        url = urlsplit(binding.original_url)
        path = unquote(url.path)
        if (
            binding.resource.course_id != "cs50_python"
            or binding.format not in {"html", "pdf"}
            or not api.supported(binding)
            or url.fragment
            or url.query
            or url.username
            or url.password
            or url.scheme != "https"
            or url.port not in (None, 443)
            or url.hostname not in {"cs50.harvard.edu", "cdn.cs50.net"}
            or not path.startswith("/python/")
            or any(p in {".", ".."} for p in path.split("/"))
            or "\\" in path
            or "%" in path
        ):
            raise PermissionError("CS50P HTML/PDF source admission failed")
        api.approval(binding, approvals, "download")
        api.approval(binding, approvals, "process")


def download(args, *, transport=None):
    batch = api.load_batch(args.batch)
    limits, approvals = load_limits(args.limits), api.load_approvals(args.approvals)
    admit(batch, limits, approvals)
    archive = private(args.archive, directory=True)
    reports = private(args.reports, directory=True)
    if (
        reports == archive
        or reports.is_relative_to(archive)
        or archive.is_relative_to(reports)
    ):
        raise ValueError("Separate report/archive roots required")
    if not args.confirm:
        return api.obtain(batch, archive, approvals, limits=limits), 0
    fd = os.open(
        archive / ".mvp-download.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600
    )
    report = dict(
        schema_version=1,
        started_at=datetime.now(UTC).isoformat(),
        status="running",
        batch_sha256=api.fingerprint(batch.model_dump(mode="json")),
        sources=[
            dict(
                material_id=b.material_id,
                source_id=b.source_id,
                original_url=b.original_url,
            )
            for b in batch.materials
        ],
    )
    code, started = 2, time.monotonic()
    try:
        private(archive / ".mvp-download.lock")
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Unknown partial bytes are evidence. Never remove or adopt them.
        if any(archive.rglob(".download-*")):
            raise ValueError("Partial files require operator investigation")
        downloader = api.MaterialDownloader(archive)
        for binding in batch.materials:
            _raw, receipt = downloader.paths(api.reviewed(binding))
            if receipt.exists():
                old = api.ArtifactReceipt.model_validate_json(read_file(receipt))
                if (
                    old.status in {"selected", "failed", "conflict"}
                    and not args.retry_failed
                ):
                    raise PermissionError(
                        "Interrupted/failed attempt requires --retry-failed"
                    )
        result = api.obtain(
            batch,
            archive,
            approvals,
            execute=True,
            retry_failed=args.retry_failed,
            transport=TransferBudget(transport or PublicHTTPSTransport()),
            limits=limits,
            retries=1,
        )
        for row in result["materials"]:
            if row["status"] == "verified":
                binding = next(
                    b for b in batch.materials if b.material_id == row["material_id"]
                )
                row["bytes"] = downloader.paths(binding)[0].stat().st_size
        report.update(result)
        code = int(any(r["status"] != "verified" for r in result["materials"]))
        report["status"] = "failed" if code else "completed"
    except (KeyboardInterrupt, InterruptedError):
        report["status"], code = "interrupted", 130
    except (ValueError, OSError, RuntimeError) as error:
        report.update(status="blocked", error_class=type(error).__name__)
    finally:
        try:
            report.update(
                finished_at=datetime.now(UTC).isoformat(),
                elapsed_seconds=round(time.monotonic() - started, 3),
            )
            api.output(
                reports / ("download-" + uuid.uuid4().hex + ".json"),
                report,
                limits=limits,
            )
        finally:
            os.close(fd)
    return report, code


def main(argv=None):
    root_parser = argparse.ArgumentParser(description=__doc__)
    sub = root_parser.add_subparsers(dest="command", required=True)
    worker = sub.add_parser("worker")
    worker.add_argument("--config", type=Path, required=True)
    worker.add_argument("--limits", type=Path, required=True)
    parser = sub.add_parser("download")
    for name in ("batch", "archive", "approvals", "limits", "reports"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")
    args = root_parser.parse_args(argv)
    os.umask(0o077)
    if os.geteuid() == 0:
        print('{"status":"blocked","reason":"nonprivileged_user_required"}')
        return 2
    if args.command == "worker":
        try:
            check_worker(args.config, args.limits)
            from scripts.cs50_worker import main as serve

            return serve(["--config", str(args.config), "--limits", str(args.limits)])
        except (ValueError, OSError, RuntimeError) as error:
            print(json.dumps(dict(status="blocked", error_class=type(error).__name__)))
            return 2

    def interrupted(_signum, _frame):
        raise KeyboardInterrupt

    previous = signal.signal(signal.SIGTERM, interrupted)
    try:
        report, code = download(args)
        print(json.dumps(report, ensure_ascii=False))
        return code
    except (ValueError, OSError, RuntimeError, KeyError) as error:
        print(json.dumps(dict(status="blocked", error_class=type(error).__name__)))
        return 2
    finally:
        signal.signal(signal.SIGTERM, previous)


def check_worker(config, limits_path):
    from src.job_control.operations import preflight

    limits = load_limits(limits_path)
    settings = preflight(config, min_free_bytes=limits.reserve_bytes)
    if (
        not settings.deployment_gate_required
        or settings.deployment_gate_protocol != "c26-gate-v2"
        or not settings.execution_enabled
        or not settings.workflows_enabled
        or settings.max_parallel != 1
        or settings.index_jobs_enabled
        or settings.import_jobs_enabled
        or settings.max_queued != 1
        or len(settings.catalog) > 3
        or any(
            entry.kind != "workflow_bundle" or entry.course_ids != ("cs50_python",)
            for entry in settings.catalog.values()
        )
        or limits.reserve_bytes < 5 * 1024**3
        or limits.job_bytes > 512 * 1024**2
    ):
        raise PermissionError(
            "Existing execution/admission gates and small-host limits required"
        )
    return settings


if __name__ == "__main__":
    raise SystemExit(main())
