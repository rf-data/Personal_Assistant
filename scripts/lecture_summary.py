"""C27 local setup, read-only inventory and CLI generation. Never starts jobs."""

import argparse
import json
from pathlib import Path

from src.content_store.models import fingerprint, sha256
from src.lecture_summary.exports import filename, render
from src.lecture_summary.inventory import inventory
from src.lecture_summary.local import load_service
from src.lecture_summary.models import Artifact, Catalog, Lecture, Options, Selection
from src.runtime_paths import checked_path, output_path
from src.tools_materials.storage import RegisteredStorage


def register(workspace, root, relative, provider, course, lecture, title, format):
    """Explicit one-file binding, no guessed lecture IDs or edits to originals."""
    workspace = output_path(checked_path(workspace), "material_artifacts")
    workspace.mkdir(mode=0o700, parents=False, exist_ok=True)
    storage = RegisteredStorage({"source": {"path": str(root), "readonly": True}})
    raw = storage.read("source", relative)
    artifact = Artifact(
        artifact_id="lecture-artifact:"
        + fingerprint([provider, course, lecture, relative]),
        storage_id="source",
        relative_path=relative,
        sha256=sha256(raw),
        title=title,
        format=format,
        role="derived"
        if format in {"knowledge_json", "document_json", "transcript_json"}
        else "original",
    )
    catalog = Catalog(
        lectures=(
            Lecture(
                provider_id=provider,
                course_id=course,
                lecture_id=lecture,
                title=title,
                sources=(artifact,),
            ),
        )
    )
    output = RegisteredStorage({"output": {"path": str(workspace), "readonly": False}})
    output.create("output", "catalog.json", catalog.model_dump_json(indent=2).encode())
    config = {
        "schema_version": 1,
        "catalog": "catalog.json",
        "model": "mock-extractive-v1",
        "allow_source_upload": False,
        "storage_roots": {"source": {"path": str(root), "readonly": True}},
    }
    output.create("output", "summary.json", json.dumps(config, indent=2).encode())
    return workspace / "summary.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    inv = subs.add_parser("inventory")
    inv.add_argument("--root", type=Path, required=True)
    inv.add_argument("--max-entries", type=int, default=4000)
    reg = subs.add_parser("register")
    for key in ("workspace", "root"):
        reg.add_argument("--" + key, type=Path, required=True)
    for key in ("relative", "provider", "course", "lecture", "title"):
        reg.add_argument("--" + key, required=True)
    reg.add_argument(
        "--format",
        choices=("txt", "md", "transcript_json", "document_json", "knowledge_json"),
        required=True,
    )
    gen = subs.add_parser("generate")
    gen.add_argument("--config", type=Path, required=True)
    gen.add_argument("--provider", required=True)
    gen.add_argument("--course", required=True)
    gen.add_argument("--lecture", action="append", required=True)
    gen.add_argument("--detail", choices=("compact", "detailed"), default="compact")
    gen.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "inventory":
        print(
            json.dumps(
                inventory(args.root, max_entries=args.max_entries),
                indent=2,
                ensure_ascii=False,
            )
        )
    elif args.command == "register":
        print(
            register(
                args.workspace,
                args.root,
                args.relative,
                args.provider,
                args.course,
                args.lecture,
                args.title,
                args.format,
            )
        )
    else:
        service = load_service(args.config)
        try:
            result = service.generate(
                Selection(
                    provider_id=args.provider,
                    course_id=args.course,
                    lecture_ids=tuple(args.lecture),
                    options=Options(detail=args.detail),
                )
            )
            if result.validation_status == "failed":
                raise ValueError(
                    "Quality gate failed: " + "; ".join(result.validation_messages)
                )
            output = RegisteredStorage(
                {"export": {"path": str(args.output), "readonly": False}}
            )
            for extension in ("md", "tex"):
                output.create(
                    "export",
                    filename(result, extension),
                    render(result, latex=extension == "tex").encode(),
                )
            output.create(
                "export",
                filename(result, "json"),
                result.model_dump_json(indent=2).encode(),
            )
            print(result.validation_status, result.summary_id)
        finally:
            if hasattr(service.provider, "close"):
                service.provider.close()


if __name__ == "__main__":
    main()
