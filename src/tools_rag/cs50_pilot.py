"""Read-only pilot inventory; reuse source bindings and the original timed chunker.

This is an operator review report, never an executable IngestionPlan or an
authorization to send transcript text to a remote service.
"""

import importlib.metadata
import math
import re
from pathlib import Path

from src.tools_knowledge.cs50_checkpoint import fingerprint


def source_inventory(adapter, *, workspace, course=None, section=None, all_six=False):
    from src.core.config_knowledge import KnowledgeSettings
    from src.tools_knowledge.bind_cs50_transcript import (
        bind_cs50_knowledge_input,
        build_cs50_knowledge_chunks,
        load_knowledge_transcript,
    )
    from src.tools_lecture.execute_cs50 import digest, safe_path
    from src.tools_rag.cs50_ingestion import selected_bindings

    workspace = Path(workspace).absolute()
    entries = []
    for binding in selected_bindings(
        adapter, course=course, section=section, all_six=all_six
    ):
        entry = {
            key: getattr(binding, key)
            for key in (
                "course_id",
                "section_key",
                "lecture_id",
                "resource_id",
                "source_id",
                "media_id",
                "language",
                "transcript_url",
            )
        }
        entry.update(import_status="unverified", warnings=[], artifacts={})
        try:
            # Read only the adapter's named artifacts. No recursive directory scan,
            # source adoption, download, receipt repair or receipt reconstruction.
            for key, reference in (
                ("raw", binding.raw_srt_path),
                ("transcript", binding.transcript_json_path),
                ("receipt", binding.raw_srt_path.parent / "execution.v1.json"),
            ):
                target = safe_path(
                    workspace,
                    reference if reference.is_absolute() else workspace / reference,
                )
                entry["artifacts"][key] = {
                    "reference": target.relative_to(workspace).as_posix(),
                    "present": target.is_file(),
                    "bytes": target.stat().st_size if target.is_file() else None,
                    "sha256": digest(target) if target.is_file() else None,
                }
            input = bind_cs50_knowledge_input(adapter, binding, workspace=workspace)
            document = load_knowledge_transcript(adapter, input, workspace=workspace)
            chunks = build_cs50_knowledge_chunks(
                adapter, input, KnowledgeSettings(), workspace=workspace
            )
            ids = [segment.seg_id for segment in document.segments]
            times = [(s.start, s.end) for s in document.segments]
            if not times or any(
                not math.isfinite(a) or not math.isfinite(b) or a < 0 or b <= a
                for a, b in times
            ):
                raise ValueError("Pilot requires real, positive, finite cue times")
            if len(ids) != len(set(ids)):
                raise ValueError("Duplicate original segment identity")
            entry.update(
                import_status="validated",
                format="srt",
                raw_sha256=input.raw_sha256,
                transcript_sha256=input.transcript_sha256,
                binding_sha256=fingerprint(binding.model_dump(mode="json")),
                provenance_sha256=fingerprint(
                    document.provenance.model_dump(mode="json")
                ),
                segment_count=len(ids),
                segment_ids=ids,
                original_srt_cue_numbers="not_retained_by_normalized_model",
                start=min(a for a, _ in times),
                end=max(b for _, b in times),
                timed_chunks=len(chunks),
                embedding_units=None,
            )
            if any(not s.text.strip() for s in document.segments):
                entry["warnings"].append("empty_cues_excluded_by_existing_chunker")
            if any(a[1] > b[0] for a, b in zip(times, times[1:], strict=False)):
                entry["warnings"].append("overlapping_source_cue_times")
        except (OSError, ValueError) as error:
            # Errors from existing binders may contain absolute paths or input
            # content. Publish only the exception class and a fixed reason code.
            entry["error_class"] = type(error).__name__
            entry["warnings"].append("source_binding_or_timing_validation_failed")
        entries.append(entry)
    report = {
        "schema_version": 1,
        "kind": "cs50_pilot_source_inventory",
        "read_only": True,
        "scope_is_upload_approval": False,
        "adapter_plan_sha256": fingerprint(adapter.model_dump(mode="json")),
        "sources": entries,
        "validated_sources": sum(e["import_status"] == "validated" for e in entries),
    }
    return report | {"report_sha256": fingerprint(report)}


def embedding_environment(*, cache=None, revision=None):
    """Inspect package metadata/cache names without importing models or networking.

    Cache presence is a prerequisite only; LocalEmbedder remains the authority for
    tokenizer, dimension and real inference validation. Never infer a revision
    from a mutable refs/main pointer.
    """
    if revision is not None and not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("An immutable 40-character model revision is required")
    packages = {}
    for name in ("qdrant-client", "sentence-transformers", "torch", "tiktoken"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    cache = Path(cache) if cache is not None else Path.home() / ".cache/huggingface/hub"
    snapshots = cache / "models--intfloat--multilingual-e5-base" / "snapshots"
    revisions = (
        sorted(
            p.name
            for p in snapshots.iterdir()
            if p.is_dir()
            and not p.is_symlink()
            and re.fullmatch(r"[0-9a-f]{40}", p.name)
        )
        if snapshots.is_dir()
        else []
    )
    blockers = []
    if packages["qdrant-client"] is None:
        blockers.append("qdrant_client_unavailable")
    if packages["sentence-transformers"] is None:
        blockers.append("sentence_transformers_unavailable")
    if revision is None:
        blockers.append("immutable_model_revision_not_selected")
    elif revision not in revisions:
        blockers.append("selected_model_revision_not_cached")
    return {
        "schema_version": 1,
        "kind": "cs50_embedding_prerequisites",
        "model": "intfloat/multilingual-e5-base",
        "revision": revision,
        "cached_revision_names": revisions,
        "packages": packages,
        "blockers": blockers,
        "weights_integrity_verified": False,
        "real_inference_executed": False,
        "downloads_performed": False,
    }


def candidate_inventory(paths, *, workspace):
    """Inspect explicitly named local SRT candidates, without adopting a binding.

    A valid SRT located outside the adapter's expected location is still unbound.
    TXT is never assigned invented timestamps; .srt.txt must contain real SRT.
    """
    from src.tools_lecture.execute_cs50 import digest, safe_path, validate_order
    from src.tools_transcribe.import_transcript import import_srt

    if len(paths) > 16:
        raise ValueError("At most 16 explicit pilot candidates")
    root = Path(workspace).absolute()
    results = []
    for path in paths:
        target = safe_path(root, Path(path).absolute())
        entry = {
            "reference": target.relative_to(root).as_posix(),
            "import_status": "unbound_candidate",
            "upload_approved": False,
            "provenance_verified": False,
            "language": None,
        }
        try:
            size = target.stat().st_size
            if not target.is_file() or size > 8 * 1024 * 1024:
                raise ValueError("Expected a bounded regular local SRT file")
            entry.update(bytes=size, sha256=digest(target))
            if not target.name.endswith((".srt", ".srt.txt")):
                raise ValueError(
                    "Only explicit SRT candidates; no timeless TXT fallback"
                )
            # The existing importer requires metadata even for syntax inspection.
            # These sentinels are not provenance and never leave this function.
            document = import_srt(
                target,
                language="und",
                original_url="https://example.invalid/unbound-candidate",
                preserve_empty_cues=True,
            )
            validate_order(document)
            entry.update(
                format="srt",
                segment_ids=[s.seg_id for s in document.segments],
                segment_count=len(document.segments),
                start=min(s.start for s in document.segments),
                end=max(s.end for s in document.segments),
            )
        except (OSError, ValueError) as error:
            entry.update(
                error_class=type(error).__name__, import_status="invalid_candidate"
            )
        results.append(entry)
    return results


def pilot_review(inventory, environment, *, candidates=()):
    """Portable, text-free selection for approval; never fabricate token counts."""
    selected = [s for s in inventory["sources"] if s["import_status"] == "validated"]
    blockers = list(environment["blockers"])
    if len(selected) != 1 or len(inventory["sources"]) != 1:
        blockers.append("pilot_one_requires_exactly_one_validated_lecture")
    blockers.extend(
        ("real_embedding_and_ingestion_plan_not_created", "phase_b_not_authorized")
    )
    report = {
        "schema_version": 1,
        "kind": "cs50_pilot_approval_review",
        "status": "blocked",
        "inventory_sha256": inventory["report_sha256"],
        "selected_sources": selected,
        "unbound_candidates": list(candidates),
        "unverified_sources": [
            s for s in inventory["sources"] if s["import_status"] != "validated"
        ],
        "embedding_environment": environment,
        "ingestion_plan": None,
        "remote_payload_policy": {
            "requires_explicit_approval": True,
            "includes_text": ["text", "original_chunk_text"],
            "includes_original_files": False,
            "includes_local_absolute_paths": False,
        },
        "blockers": blockers,
        "phase_b": {"status": "blocked", "approval_received": False},
    }
    return report | {"report_sha256": fingerprint(report)}
