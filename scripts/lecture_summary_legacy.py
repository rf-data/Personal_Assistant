"""C27-B private read-only inventory and explicit catalog candidate preparation."""

import argparse
import json
import os
import sys
from pathlib import Path

from src.content_store.models import sha256
from src.lecture_summary.legacy import LegacyEntry, LegacyManifest, candidate, recognize
from src.lecture_summary.legacy_inventory import scan
from src.lecture_summary.local import load_service
from src.runtime_paths import checked_path, output_path
from src.tools_materials.storage import RegisteredStorage


def read_json(path):
    reader = RegisteredStorage({"config": {"path": str(path.parent), "readonly": True}})
    return reader.read("config", path.name)


def workspace(path):
    path = output_path(checked_path(path), "material_artifacts")
    path.mkdir(mode=0o700, parents=False, exist_ok=False)
    return RegisteredStorage({"output": {"path": str(path), "readonly": False}})


def publish(output, name, obj):
    output.create("output", name, (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    inv = sub.add_parser("inventory")
    inv.add_argument("--root", type=Path, required=True)
    inv.add_argument("--storage-id", default="source")
    inv.add_argument("--output", type=Path, required=True)
    cat = sub.add_parser("catalog")
    cat.add_argument("--roots", type=Path, required=True, help="JSON registered roots mapping")
    cat.add_argument("--manifest", type=Path, required=True)
    cat.add_argument("--output", type=Path, required=True)
    man = sub.add_parser("manifest", help="Reuse an existing explicit offline C27 registration")
    man.add_argument("--config", type=Path, required=True)
    man.add_argument("--output", type=Path, required=True, help="New private manifest directory")
    man.add_argument("--knowledge-for", help="Explicit lecture ID with exactly one transcript")
    man.add_argument("--knowledge", help="Relative knowledge locator in the same registered root")
    args = parser.parse_args()
    if args.command == "inventory":
        storage = RegisteredStorage({args.storage_id: {"path": str(args.root), "readonly": True}})
        output = workspace(args.output)
        # Anchored exclusive streaming publication; partial reports remain inspectable.
        with output.parent("output", "inventory.jsonl", write=True) as (parent, name):
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600,
                         dir_fd=parent)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                def emit(obj):
                    stream.write(json.dumps(obj, ensure_ascii=False) + "\n")

                def progress(obj):
                    stream.flush()
                    print(json.dumps(dict(event="progress", **obj)), file=sys.stderr, flush=True)

                report = scan(storage, args.storage_id, emit, progress=progress)
                stream.flush()
                os.fsync(stream.fileno())
            os.fsync(parent)
        publish(output, "inventory_summary.json", report)
        print(json.dumps({k: report[k] for k in ("complete", "files", "issues", "metadata_complete")}))
        return 0 if report["complete"] else 2
    if args.command == "manifest":
        service = load_service(args.config, offline_only=True)
        if any(not grant[1] for grant in service.storage.roots.values()):
            # Existing local caches may be writable, but never become input grants.
            input_ids = {a.storage_id for l in service.catalog.lectures for a in l.sources}
            if any(not service.storage.roots[k][1] for k in input_ids):
                raise ValueError("Legacy input root is not read-only")
        entries = []
        bindings = [(l, a) for l in service.catalog.lectures for a in l.sources]
        parent_index = {(l.provider_id, l.course_id, l.lecture_id, a.artifact_id): str(i)
                        for i, (l, a) in enumerate(bindings)}
        for lecture in service.catalog.lectures:
            for artifact in lecture.sources:
                if not artifact.format.endswith("_json"):
                    raise ValueError("Only the three supported JSON source schemas qualify")
                entries.append(LegacyEntry(key=str(len(entries)), storage_id=artifact.storage_id,
                    locator=artifact.relative_path, expected_sha256=artifact.sha256,
                    provider_id=lecture.provider_id, course_id=lecture.course_id,
                    lecture_ids=(lecture.lecture_id,), title=artifact.title,
                    parent_keys=tuple(parent_index[(lecture.provider_id, lecture.course_id,
                        lecture.lecture_id, key)] for key in artifact.parent_artifact_ids),
                    identity_evidence="explicit_registration"))
        if bool(args.knowledge) != bool(args.knowledge_for):
            raise ValueError("Knowledge requires an explicit parent lecture and locator")
        if args.knowledge:
            parents = [e for e in entries if e.lecture_ids == (args.knowledge_for,)
                       and next(a.format for l in service.catalog.lectures for a in l.sources
                                if a.storage_id == e.storage_id and a.relative_path == e.locator)
                       == "transcript_json"]
            if len(parents) != 1:
                raise ValueError("Knowledge parent lecture ambiguous or missing")
            parent = parents[0]
            raw = service.storage.read(parent.storage_id, args.knowledge)
            if recognize(raw)[0] != "knowledge_json":
                raise ValueError("Explicit knowledge locator must contain TranscriptKnowledgeDocument")
            entries.append(LegacyEntry(key="knowledge", storage_id=parent.storage_id,
                locator=args.knowledge, expected_sha256=sha256(raw), provider_id=parent.provider_id,
                course_id=parent.course_id, lecture_ids=parent.lecture_ids, title=parent.title + " – Knowledge",
                parent_keys=(parent.key,), identity_evidence="explicit_registration"))
        manifest = LegacyManifest(entries=tuple(entries))
        input_ids = {e.storage_id for e in entries}
        roots = {key: {"path": str(service.storage.roots[key][0]), "readonly": True} for key in input_ids}
        output = workspace(args.output)
        publish(output, "manifest.json", manifest.model_dump(mode="json"))
        publish(output, "roots.json", roots)
        print("Explicit manifest prepared; candidate validation still required")
        return 0
    roots = json.loads(read_json(args.roots))
    storage = RegisteredStorage(roots)
    if any(not grant[1] for grant in storage.roots.values()):
        raise ValueError("Legacy input roots must explicitly be read-only")
    manifest = LegacyManifest.model_validate_json(read_json(args.manifest))
    catalog, report = candidate(storage, manifest)
    output = workspace(args.output)
    publish(output, "catalog_review.json", report)
    if catalog:
        output.create("output", "catalog.json", catalog.model_dump_json(indent=2).encode())
        publish(output, "summary.json", dict(schema_version=1, catalog="catalog.json",
            storage_roots=roots, model="mock-extractive-v1", allow_source_upload=False))
    print(json.dumps(dict(accepted=len(report["accepted"]), review=len(report["review"]),
                         candidate_available=catalog is not None, registered=False)))
    return 0 if catalog else 2


if __name__ == "__main__":
    raise SystemExit(main())
