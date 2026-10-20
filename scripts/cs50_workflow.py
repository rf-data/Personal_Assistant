"""Explicit local workflow planning/control/export; execution always uses C16."""

import argparse
import json
import time
from pathlib import Path

from src.job_control.catalog import read_file, safe_path
from src.job_control.controller import Controller, authenticate
from src.job_control.models import TERMINAL, fingerprint, load_settings
from src.tools_materials.storage import publish_bytes
from src.workflows.service import inspect, markdown, submit


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("plan", "preview", "execute", "resume", "status", "report", "cancel"),
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--source-ref", required=True)
    parser.add_argument("--workflow-id")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args(argv)
    settings = load_settings(args.config)
    actor = authenticate(
        settings,
        "Bearer "
        + read_file(safe_path(args.token_file.absolute()), 257).decode().strip(),
    )
    workflow_id = (
        args.workflow_id
        or "wf_"
        + fingerprint(dict(subject=actor.subject, source_ref=args.source_ref))[:32]
    )
    if args.command in {"execute", "resume", "cancel"}:
        if not args.confirm:
            raise ValueError("Explicit --confirm required")
        if args.command == "cancel":
            _report, _prepared, job = inspect(
                settings, actor, args.source_ref, workflow_id
            )
            if job is None:
                raise ValueError("No workflow job to cancel")
            job = Controller(settings).cancel(actor, job.job_id)
        else:
            job = submit(
                settings,
                actor,
                args.source_ref,
                workflow_id,
                resume=args.command == "resume",
            )
        if args.wait:
            until = time.monotonic() + 100
            controller = Controller(settings)
            while job.status not in TERMINAL:
                if time.monotonic() > until:
                    raise RuntimeError("Wait limit; existing job remains authoritative")
                time.sleep(0.1)
                job = controller.get(actor, job.job_id)
        if not args.wait:
            print(job.model_dump_json())
            return 0
    report, _prepared, _job = inspect(settings, actor, args.source_ref, workflow_id)
    targets = [p.absolute() for p in (args.json_output, args.markdown_output) if p]
    if len(set(targets)) != len(targets):
        raise ValueError("Report output paths must be distinct")
    for path in targets:
        safe_path(path.parent, path)
        if (
            path.exists()
            or path.is_relative_to(settings.root)
            or any(path.is_relative_to(e.root) for e in settings.catalog.values())
        ):
            raise ValueError(
                "Report output must be new and outside input/job workspaces"
            )
    raw = (report.model_dump_json(indent=2) + "\n").encode()
    if args.json_output:
        publish_bytes(args.json_output.absolute(), raw)
    if args.markdown_output:
        publish_bytes(args.markdown_output.absolute(), markdown(report).encode())
    print(raw.decode(), end="")
    return (
        1 if report.status in {"failed", "blocked", "interrupted", "cancelled"} else 0
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, RuntimeError, KeyError) as error:
        print(
            json.dumps(
                dict(
                    schema_version=1,
                    error=type(error).__name__,
                    message="Workflow request rejected; inspect configuration, grants and reports",
                )
            )
        )
        raise SystemExit(2) from None
