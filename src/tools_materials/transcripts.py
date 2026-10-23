"""Bounded offline adapter to the integrated official transcript importer.

This lane publishes neither C18 NormalizedDocuments nor Knowledge inputs.
"""

import tempfile
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import Field

from src.job_control.catalog import read_file, safe_path
from src.job_control.models import Contract, Sha, fingerprint
from src.job_control.operations import private
from src.model_lecture.data_resources import LectureDocument
from src.model_materials.materials import MaterialResource
from src.model_transcribe.data_transcribe import TranscriptDocument
from src.tools_lecture.cs50_manifest import COURSE_PATHS
from src.tools_lecture.execute_cs50 import sync_directory, validate_order
from src.tools_materials import batch as api
from src.tools_materials.capacity import MIB, check_capacity
from src.tools_materials.inventory import catalog, official
from src.tools_materials.quality import _json
from src.tools_materials.storage import artifact_root, locked, publish_bytes
from src.tools_transcribe import import_transcript as importer


class TranscriptReceipt(Contract):
    """Only the missing archive binding; existing transcript/lecture models reused."""

    schema_version: Literal[1] = 1
    kind: Literal["c26-offline-transcript"] = "c26-offline-transcript"
    binding: MaterialResource
    lecture: LectureDocument
    batch_sha256: Sha
    approval_sha256: Sha
    importer_sha256: Sha
    raw_sha256: Sha
    raw_bytes: int = Field(strict=True, gt=0, le=MIB)
    transcript_sha256: Sha
    transcript_path: Literal["transcript.json"] = "transcript.json"
    encoding: Literal["utf-8-sig"] = "utf-8-sig"
    preserve_empty_cues: Literal[True] = True


def supported(binding):
    return (
        binding.resource.course_id in COURSE_PATHS
        and official(binding.original_url)
        and len(binding.resource.section_keys) == 1
        and (binding.role, binding.format)
        in {("subtitles", "srt"), ("transcript", "txt")}
        and bool(binding.language and binding.language.strip())
        and len(binding.lecture_ids) == 1
        and binding.source_id != binding.lecture_ids[0]
    )


def revision():
    """Pin the actual importer and timestamp model, not an assumed HEAD version."""
    from src.model_transcribe import data_transcribe

    return fingerprint(
        {
            "importer": api.sha(read_file(Path(importer.__file__))),
            "models": api.sha(read_file(Path(data_transcribe.__file__))),
            "adapter": api.sha(read_file(Path(__file__))),
        }
    )


def checked(batch, limits):
    limits.batch_size(batch)
    if not 1 <= len(batch.materials) <= 2 or not all(map(supported, batch.materials)):
        raise ValueError("Select one or two bound SRT/TXT resources")
    if (
        len({(b.resource.course_id, b.resource.section_keys) for b in batch.materials})
        != 1
    ):
        raise ValueError("Transcript batch must belong to one course and section")
    if limits.reserve_bytes < 5 * 1024**3 or limits.archive_bytes > 64 * MIB:
        raise ValueError(
            "C26 reserve/budget must remain at least 5 GiB / at most 64 MiB"
        )
    # Re-derive graph membership and lecture IDs from hashed discovery snapshots.
    current = api.plan(
        batch.manifest,
        sorted({b.resource.course_id for b in batch.materials}),
        [b.material_id for b in batch.materials],
        synthetic=batch.source_origin == "synthetic",
    )
    if current.materials != batch.materials or current.files != batch.files:
        raise ValueError("Transcript discovery binding changed")


def load_inputs(path):
    data = _json(read_file(private(safe_path(Path(path))), 8192))
    if not isinstance(data, dict) or not 1 <= len(data) <= 2:
        raise ValueError("Explicit source-ID to local-file mapping required")
    result = {}
    for source, name in data.items():
        if not isinstance(name, str) or not Path(name).is_absolute():
            raise ValueError("Explicit absolute input paths required")
        result[source] = safe_path(Path(name))
    return result


def parse(raw, binding, staging, limits):
    """Importer reads a private bounded copy; original bytes never change."""
    check_capacity(staging, limits.archive_bytes, limits.reserve_bytes, len(raw))
    with tempfile.TemporaryDirectory(prefix=".transcript-", dir=staging) as temp:
        path = Path(temp) / ("source." + binding.format)
        publish_bytes(path, raw)
        document = importer.import_transcript(
            path,
            language=binding.language,
            original_url=binding.original_url,
            format=binding.format,
            preserve_empty_cues=True,
        )
    if len(document.segments) > 20000:
        raise ValueError("Transcript segment bound exceeded")
    if binding.format == "srt":
        validate_order(document)  # Allows overlapping intervals, retains empty cues.
    # Stable archive-relative provenance. The raw artifact retains original cue IDs,
    # CRLF, BOM and presentation markup that the established importer normalizes.
    document.source = "source." + binding.format
    document.provenance.source_file = document.source
    return document


def lecture(binding, digest):
    return LectureDocument(
        title=binding.resource.title,
        source_url=binding.original_url,
        lecture_no=binding.resource.section_keys[0],
        lecture_blocks=list(binding.resource.section_keys),
        file_type=binding.format,
        local_path=Path("source." + binding.format),
        content_hash=digest,
        downloaded=False,  # Local import makes no HTTP-download claim.
    )


def verify(folder, binding, batch_digest, grant, parser_digest, staging, limits):
    if not (folder / "receipt.json").exists():
        raise ValueError("Incomplete publication; no automatic adoption or repair")
    receipt_bytes = read_file(private(folder / "receipt.json"))
    receipt = TranscriptReceipt.model_validate(_json(receipt_bytes))
    if receipt_bytes != (receipt.model_dump_json(indent=2) + "\n").encode():
        raise ValueError("Transcript receipt bytes changed")
    expected = dict(
        binding=binding,
        batch_sha256=batch_digest,
        approval_sha256=fingerprint(grant.model_dump(mode="json")),
        importer_sha256=parser_digest,
        raw_sha256=grant.expected_sha256,
    )
    if any(getattr(receipt, key) != value for key, value in expected.items()):
        raise ValueError("Transcript receipt binding changed")
    raw = read_file(private(folder / ("source." + binding.format)), MIB)
    payload = read_file(private(folder / "transcript.json"))
    if (
        api.sha(raw) != receipt.raw_sha256
        or len(raw) != receipt.raw_bytes
        or api.sha(payload) != receipt.transcript_sha256
        or receipt.lecture != lecture(binding, receipt.raw_sha256)
    ):
        raise ValueError("Transcript archive hash/lecture mismatch")
    document = TranscriptDocument.model_validate(_json(payload))
    expected_document = parse(raw, binding, staging, limits)
    expected_document.provenance.acquired_at = document.provenance.acquired_at
    if expected_document != document:
        raise ValueError("Transcript contradicts raw source")
    return receipt, document


def run(batch, root, approvals, inputs, *, action, limits):
    """Explicit preview/import/report. Serial, immutable receipts, no network/queue.

    Interrupted publications without a complete receipt stay blocked. They require
    diagnosis and a separately authorized new root, never guessed repair/adoption.
    """
    if action not in {"preview", "import", "report"}:
        raise ValueError("Unknown transcript action")
    checked(batch, limits)
    root = artifact_root(Path(root))
    private(root.parent, directory=True)
    if action != "report" and set(inputs) != {b.source_id for b in batch.materials}:
        raise ValueError("Input selection must exactly match the transcript batch")
    for path in inputs.values():
        if not path.is_absolute() or safe_path(path).is_relative_to(root):
            raise ValueError("Original input must be outside transcript output")
    batch_digest = fingerprint(batch.model_dump(mode="json"))
    parser_digest = revision()
    rows = []

    def process():
        for binding in batch.materials:
            published = False
            row = dict(
                material_id=binding.material_id,
                source_id=binding.source_id,
                lecture_ids=list(binding.lecture_ids),
                language=binding.language,
                format=binding.format,
                source_origin=batch.source_origin,
                status="blocked",
                execution_supported=False,
                knowledge_fact_verified=False,
                human_quality="not_evaluated",
            )
            stage = "approval"
            try:
                grant = api.approval(binding, approvals, "process")
                if grant.expected_sha256 is None:
                    raise PermissionError("Expected original hash required")
                row["download_approved"] = grant.download
                if action == "preview":
                    exists = inputs[binding.source_id].is_file()
                    row.update(
                        status="selected" if exists else "missing",
                        input_exists=exists,
                    )
                else:
                    stage = "capacity"
                    check_capacity(root, limits.archive_bytes, limits.reserve_bytes)
                    folder = root / binding.material_id.split(":")[-1]
                    if action == "import":
                        stage = "original_input"
                        raw = read_file(
                            safe_path(inputs[binding.source_id]), batch.max_bytes
                        )
                        if api.sha(raw) != grant.expected_sha256:
                            raise ValueError("Original transcript hash mismatch")
                    if action == "import" and not folder.exists():
                        stage = "importer"
                        document = parse(raw, binding, root, limits)
                        payload = (document.model_dump_json(indent=2) + "\n").encode()
                        if len(payload) > 8 * MIB:
                            raise ValueError(
                                "Normalized transcript size bound exceeded"
                            )
                        receipt = TranscriptReceipt(
                            binding=binding,
                            lecture=lecture(binding, api.sha(raw)),
                            batch_sha256=batch_digest,
                            approval_sha256=fingerprint(grant.model_dump(mode="json")),
                            importer_sha256=parser_digest,
                            raw_sha256=api.sha(raw),
                            raw_bytes=len(raw),
                            transcript_sha256=api.sha(payload),
                        )
                        receipt_bytes = (
                            receipt.model_dump_json(indent=2) + "\n"
                        ).encode()
                        check_capacity(
                            root,
                            limits.archive_bytes,
                            limits.reserve_bytes,
                            len(raw) + len(payload) + len(receipt_bytes),
                        )
                        stage = "publication"
                        folder.mkdir(mode=0o700)
                        sync_directory(root)
                        publish_bytes(folder / ("source." + binding.format), raw)
                        publish_bytes(folder / "transcript.json", payload)
                        publish_bytes(folder / "receipt.json", receipt_bytes)
                        published = True
                    stage = "archive_verification"
                    private(folder, directory=True)
                    receipt, document = verify(
                        folder,
                        binding,
                        batch_digest,
                        grant,
                        parser_digest,
                        root,
                        limits,
                    )
                    row.update(
                        status="processed",
                        raw_sha256=receipt.raw_sha256,
                        transcript_sha256=receipt.transcript_sha256,
                        segments=len(document.segments),
                        timestamps="unknown"
                        if binding.format == "txt"
                        else "source_cues",
                        reused=not published,
                    )
            except (ValueError, OSError, RuntimeError) as error:
                # No source text, private paths or exception message in reports.
                row.update(error_class=type(error).__name__, error_stage=stage)
                if isinstance(error, FileNotFoundError):
                    row["status"] = "missing"
            rows.append(row)

    if action == "preview":
        process()
    else:
        new = False
        if action == "import" and not root.exists():
            root.mkdir(mode=0o700)
            new = True
        private(root, directory=True)
        with locked(root):
            marker = root / "batch.sha256"
            if new:
                publish_bytes(marker, (batch_digest + "\n").encode())
            if read_file(private(marker), 100).decode().strip() != batch_digest:
                raise ValueError("Existing transcript root belongs to another batch")
            process()
    return dict(
        schema_version=1,
        action=action,
        batch_sha256=batch_digest,
        importer_sha256=parser_digest,
        materials=rows,
        status_counts=dict(sorted(Counter(r["status"] for r in rows).items())),
        selected_materials=len(rows),
        processed_materials=sum(r["status"] == "processed" for r in rows),
        full_week_coverage=False,
        c18_publication=False,
        network_requests=0,
        coverage={
            "scope": "explicit_transcript_selection_only",
            "other_week_materials": "not_processed_by_this_lane",
            "missing_materials": sum(r["status"] == "missing" for r in rows),
        },
    )


def week_inventory(manifest):
    """Existing bounded snapshot inventory; raw references never become source IDs."""
    data = catalog(manifest)
    bindings = api.make_plan(manifest).materials
    by_url = {
        b.original_url: b for b in bindings if b.resource.course_id == "cs50_python"
    }
    rows = []
    for original in data["references"]:
        if (
            original["course_id"] != "cs50_python"
            or "0" not in original["section_keys"]
        ):
            continue
        row = dict(original)
        binding = by_url.get(row["original_url"])
        if binding and supported(binding):
            adapter = "offline_official_transcript"
        elif binding and api.supported(binding):
            adapter = "existing_c18_material"
        else:
            adapter = "excluded_unbound_or_unsupported"
        row.update(
            adapter=adapter,
            processing_status="not_processed",
            availability="reference_only",
            live_reachability="not_checked",
        )
        rows.append(row)
    from src.tools_lecture.cs50_manifest import load_fixture_manifest

    snapshots = [
        dict(file=p.file, url=str(p.url), sha256=p.sha256)
        for c in load_fixture_manifest(manifest).courses
        if c.course_id == "cs50_python"
        for p in c.pages
        if str(p.url) in {r["original_url"] for r in rows}
        or str(p.url) == str(c.source_url)
        or str(p.url).startswith("https://cs50.harvard.edu/python/psets/0/")
    ]
    for row in rows:
        matches = [p for p in snapshots if p["url"] == row["original_url"]]
        row["local_snapshots"] = matches
        if matches:
            row["availability"] = "versioned_html_snapshot"
    return dict(
        schema_version=1,
        coverage="versioned_week0_snapshot_references_only",
        full_week_coverage=False,
        references=rows,
        local_snapshots=snapshots,
        counts=dict(sorted(Counter(r["reference_kind"] for r in rows).items())),
        missing="Raw SRT/TXT/PDF/ZIP/Python/media not supplied to this inventory; private stores not searched",
    )
