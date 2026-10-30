"""Small explicit legacy compatibility boundary; no discovery, moves or inference."""

import json
import math
from pathlib import PurePosixPath
from typing import Literal

from pydantic import Field

from src.content_store.models import Name, fingerprint, sha256
from src.job_control.models import Contract, Identifier, Sha
from src.lecture_summary.models import Artifact, Catalog, Lecture
from src.lecture_summary.sources import source_blocks
from src.model_knowledge.data_knowledge import TranscriptKnowledgeDocument
from src.model_materials.materials import NormalizedDocument
from src.model_transcribe.data_transcribe import TranscriptDocument


class LegacyEntry(Contract):
    """Trusted registration instructions, never derived from lecture text."""

    key: Name
    storage_id: Identifier
    locator: str = Field(min_length=1, max_length=2000)
    expected_sha256: Sha
    provider_id: Name | None = None
    course_id: Name | None = None
    lecture_ids: tuple[Name, ...] = Field(default=(), max_length=3)
    title: Name
    identity_evidence: Literal["explicit_registration", "native_metadata"] = "native_metadata"
    parent_keys: tuple[Name, ...] = Field(default=(), max_length=4)


class LegacyManifest(Contract):
    schema_version: Literal[1] = 1
    entries: tuple[LegacyEntry, ...] = Field(min_length=1, max_length=128)


def relative_locator(storage, storage_id, locator):
    """Translate old absolute paths only within that *explicitly named* root.

    No implicit root search, prefix substitution, resolve(), mkdir or fallback.
    The existing resolver still checks ancestors, links, mounts and permissions.
    """
    path = PurePosixPath(locator)
    if path.is_absolute():
        if path.as_posix() != locator:
            raise ValueError("Noncanonical historical path")
        root = storage.roots[storage_id][0]
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            raise ValueError("Historical path outside explicitly registered legacy root") from None
    else:
        relative = locator
    storage.path(storage_id, relative)
    return relative


def recognize(raw):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Ambiguous duplicate JSON key")
            result[key] = value
        return result

    obj = json.loads(raw, object_pairs_hook=unique_keys)
    if not isinstance(obj, dict):
        raise ValueError("Unsupported legacy JSON: object required")
    schemas = [("transcript_json", TranscriptDocument, {"source", "text", "segments"}),
               ("document_json", NormalizedDocument, {"binding", "raw_sha256", "blocks"}),
               ("knowledge_json", TranscriptKnowledgeDocument, {"chunks", "visual_candidates"})]
    matching = [(kind, model) for kind, model, fields in schemas if fields <= obj.keys()]
    if len(matching) != 1:
        raise ValueError("Unsupported or ambiguous legacy schema (Docling/RawDocument not normalized)")
    kind, model = matching[0]
    document = model.model_validate_json(raw)
    if kind == "knowledge_json":
        chunk_ids = [c.analysis.chunk_id for c in document.chunks]
        if len(set(chunk_ids)) != len(chunk_ids):
            raise ValueError("Ambiguous duplicate knowledge chunk ID")
        for chunk in document.chunks:
            if chunk.extraction:
                if chunk.extraction.chunk_id != chunk.analysis.chunk_id:
                    raise ValueError("Contradictory knowledge chunk IDs")
                for ids in ([s.statement_id for s in chunk.extraction.statements],
                            [f.expression_id for f in chunk.extraction.formulas]):
                    if len(set(ids)) != len(ids):
                        raise ValueError("Ambiguous duplicate knowledge item ID")
    return kind, document, obj


def candidate(storage, manifest):
    """Return a candidate and audit report; rejected entries never enter catalog.

    Only explicit, fingerprinted bindings or complete native identities qualify.
    No filename matching. Derived knowledge requires an explicit validated parent.
    Nothing is installed into an application; callers publish a private candidate.
    """
    manifest = LegacyManifest.model_validate_json(manifest.model_dump_json())
    keys = [e.key for e in manifest.entries]
    if len(keys) != len(set(keys)):
        raise ValueError("Ambiguous duplicate manifest key")
    prepared, review, records = {}, [], []
    for entry in manifest.entries:
        try:
            relative = relative_locator(storage, entry.storage_id, entry.locator)
            raw = storage.read(entry.storage_id, relative)
            if sha256(raw) != entry.expected_sha256:
                raise ValueError("Source fingerprint changed")
            kind, doc, native = recognize(raw)
            provider = native.get("provider_id")
            course = native.get("course_id")
            lecture_ids = (native["lecture_id"],) if native.get("lecture_id") else ()
            native_id = native.get("source_id")
            document_id = None
            source_url = None
            if kind == "document_json":
                course = doc.binding.resource.course_id
                lecture_ids = doc.binding.lecture_ids
                native_id, document_id = doc.binding.source_id, doc.document_id
                source_url = doc.binding.original_url
            for declared, actual in ((entry.provider_id, provider), (entry.course_id, course)):
                if declared is not None and actual is not None and declared != actual:
                    raise ValueError("Contradictory native identity")
            if entry.lecture_ids and lecture_ids and set(entry.lecture_ids) != set(lecture_ids):
                raise ValueError("Contradictory native lecture identity")
            if entry.identity_evidence == "explicit_registration":
                provider = entry.provider_id or provider
                course = entry.course_id or course
                lecture_ids = entry.lecture_ids or lecture_ids
            if not provider or not course or not lecture_ids or len(set(lecture_ids)) != len(lecture_ids):
                raise ValueError("Missing or ambiguous identity; explicit registration required")
            if native_id is not None and (not isinstance(native_id, str) or not 1 <= len(native_id) <= 200):
                raise ValueError("Invalid native source identity")
            for lecture_id in lecture_ids:
                Lecture(provider_id=provider, course_id=course, lecture_id=lecture_id,
                        title=entry.title, sources=())
            artifact = Artifact(
                artifact_id="lecture-artifact:" + fingerprint(
                    ["legacy-v1", provider, course, kind, native_id or entry.expected_sha256]),
                storage_id=entry.storage_id, relative_path=relative,
                sha256=entry.expected_sha256, format=kind, role="derived", title=entry.title,
                source_url=source_url,
            )
            usable = False
            for text, _, _ in source_blocks(artifact, raw):
                usable = usable or bool(text.strip())
            if not usable:
                raise ValueError("No supported text blocks")
            prepared[entry.key] = dict(entry=entry, artifact=artifact, doc=doc,
                native=native, provider=provider, course=course, lectures=tuple(lecture_ids),
                native_id=native_id, document_id=document_id)
        except (OSError, ValueError, KeyError, TypeError, RecursionError) as error:
            if isinstance(error, OSError) and error.errno == 28:
                raise
            review.append(dict(key=entry.key, reason=type(error).__name__, detail=str(error)[:500]))

    # A repeated native identity with different versions is ambiguous: reject both.
    versions = {}
    for p in prepared.values():
        versions.setdefault(p["artifact"].artifact_id, set()).add(p["artifact"].sha256)
    rejected = {key for key, p in prepared.items() if len(versions[p["artifact"].artifact_id]) > 1}
    for key in rejected:
        review.append(dict(key=key, reason="conflicting_native_versions"))

    # Parent chain is deliberately limited to knowledge -> transcript or document.
    for key, p in prepared.items():
        if key in rejected:
            continue
        try:
            entry, artifact = p["entry"], p["artifact"]
            parents = [prepared[k] for k in entry.parent_keys if k not in rejected]
            if len(parents) != len(entry.parent_keys):
                raise ValueError("Unavailable or ambiguous parent")
            if artifact.format == "knowledge_json" and not parents:
                raise ValueError("Knowledge parent missing; no filename-only inference")
            for parent in parents:
                if parent["artifact"].format not in {"transcript_json", "document_json"}:
                    raise ValueError("Unsupported parent chain")
                if (parent["provider"], parent["course"], parent["lectures"]) != (
                        p["provider"], p["course"], p["lectures"]):
                    raise ValueError("Parent identity mismatch")
                if artifact.format == "knowledge_json":
                    if parent["artifact"].format != "transcript_json":
                        raise ValueError("Transcript knowledge requires transcript parent")
                    if p["native_id"] and parent["native_id"] and p["native_id"] != parent["native_id"]:
                        raise ValueError("Parent source identity mismatch")
                    knowledge_provenance = p["doc"].transcript_provenance
                    transcript_provenance = parent["doc"].provenance
                    if knowledge_provenance and transcript_provenance:
                        for field in ("source_url", "source_file", "media_id", "language"):
                            declared, original = (getattr(knowledge_provenance, field),
                                                  getattr(transcript_provenance, field))
                            if declared is not None and original is not None and declared != original:
                                raise ValueError("Parent transcript provenance mismatch")
                    if (p["doc"].language and parent["doc"].language
                            and p["doc"].language != parent["doc"].language):
                        raise ValueError("Parent transcript language mismatch")
                    segments = {s.seg_id: s for s in parent["doc"].segments}
                    for chunk in p["doc"].chunks:
                        if chunk.extraction:
                            for claim in [*chunk.extraction.statements, *chunk.extraction.formulas]:
                                if not claim.segment_ids or any(s not in segments for s in claim.segment_ids):
                                    raise ValueError("Knowledge references unknown parent segments")
                                referenced = [segments[s] for s in claim.segment_ids]
                                if (not math.isfinite(claim.start) or not math.isfinite(claim.end)
                                        or claim.start < 0 or claim.end < claim.start):
                                    raise ValueError("Invalid knowledge time interval")
                                if any(s.start is None for s in referenced):
                                    raise ValueError("Knowledge asserts time for untimed parent")
                                if (claim.start < min(s.start for s in referenced) - 0.001
                                        or claim.end > max(s.end for s in referenced) + 0.001):
                                    raise ValueError("Knowledge time outside parent segments")
            p["artifact"] = artifact.model_copy(update={
                "parent_artifact_ids": tuple(v["artifact"].artifact_id for v in parents)})
        except (KeyError, ValueError) as error:
            rejected.add(key)
            review.append(dict(key=key, reason="invalid_parent", detail=str(error)))

    lectures, seen = {}, set()
    for key, p in prepared.items():
        if key in rejected:
            continue
        artifact = p["artifact"]
        accepted = False
        for lecture_id in p["lectures"]:
            identity = (p["provider"], p["course"], lecture_id)
            duplicate = (*identity, artifact.format, artifact.sha256)
            if duplicate in seen:
                review.append(dict(key=key, reason="duplicate_content", lecture_id=lecture_id))
                continue
            seen.add(duplicate)
            lecture = lectures.setdefault(identity, dict(provider_id=p["provider"],
                course_id=p["course"], lecture_id=lecture_id, title=p["entry"].title, sources=[]))
            lecture["sources"].append(artifact)
            accepted = True
        if accepted:
            records.append(dict(key=key, artifact=artifact.model_dump(mode="json"),
                provider_id=p["provider"], course_id=p["course"], lecture_ids=p["lectures"],
                identity_evidence=p["entry"].identity_evidence,
                native_source_id=p["native_id"], native_document_id=p["document_id"],
                original_artifact_sha256=p["doc"].raw_sha256 if artifact.format == "document_json" else None,
                resource_role=p["doc"].binding.role if artifact.format == "document_json" else None,
                provenance=p["native"].get("provenance") or p["native"].get("transcript_provenance"),
                historical_source_reference=p["native"].get("source"),
                parent_keys=p["entry"].parent_keys,
                warnings=["derived_not_independent_evidence"] if artifact.format == "knowledge_json" else []))
    catalog = Catalog(lectures=tuple(Lecture(**v) for v in lectures.values())) if lectures else None
    return catalog, dict(schema_version=1, registered=False, accepted=records, review=review,
                        all_manifest_entries_accepted=not review,
                        scope="explicit_manifest_only_not_whole_inventory")
