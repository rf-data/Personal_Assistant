"""Read-only verification of explicitly named evidence; never scans archives."""

from src.job_control.catalog import read_file, safe_path
from src.job_control.models import fingerprint
from src.job_control.operations import private
from src.model_materials.materials import ArtifactReceipt
from src.model_transcribe.data_transcribe import TranscriptDocument
from src.tools_lecture.material_handoff import prepare_material_handoff
from src.tools_materials import batch as api
from src.tools_materials import transcripts
from src.tools_materials.capacity import MIB
from src.tools_materials.processing import parser_for
from src.tools_materials.quality import _json
from src.tools_materials.storage import locate


def verify(binding, ref, grant, media_limits):
    root = safe_path(ref.workspace)
    if not root.is_absolute():
        raise ValueError("Absolute evidence root required")
    private(root, directory=True)
    if grant.expected_sha256 is None:
        raise PermissionError("Pinned raw hash required for local evidence")
    result = dict(
        verified=True,
        raw_sha256=grant.expected_sha256,
        provenance="hash_bound_local_input",
        technical_quality="not_checked",
        language=binding.language,
        times="unknown",
        processed=False,
        visual_evidence_available=False,
    )
    key = binding.material_id.split(":")[-1]
    if ref.kind == "media":
        if not ref.relative_path or binding.role not in {"audio", "lecture_video"}:
            raise ValueError("Explicit audio/video path required")
        maximum = (
            media_limits.audio_bytes
            if binding.role == "audio"
            else media_limits.video_bytes
        )
        raw = read_file(private(locate(root, ref.relative_path)), maximum)
        if api.sha(raw) != grant.expected_sha256 or not raw:
            raise ValueError("Local media hash mismatch")
        return dict(result, bytes=len(raw), adapter="local_media_reference_only")
    if ref.receipt_sha256 is None:
        raise PermissionError("Pinned existing receipt required")
    if ref.kind == "transcript":
        if ref.batch is None or not transcripts.supported(binding):
            raise ValueError("Existing B5 receipt/binding required")
        batch = api.load_batch(safe_path(ref.batch))
        if binding not in batch.materials:
            raise ValueError("Transcript batch binding mismatch")
        folder = locate(root, key)
        raw_receipt = read_file(private(locate(folder, "receipt.json")), MIB)
        receipt = transcripts.TranscriptReceipt.model_validate(_json(raw_receipt))
        if (
            receipt.binding != binding
            or receipt.batch_sha256 != fingerprint(batch.model_dump(mode="json"))
            or receipt.approval_sha256 != fingerprint(grant.model_dump(mode="json"))
            or receipt.importer_sha256 != transcripts.revision()
            or receipt.lecture != transcripts.lecture(binding, grant.expected_sha256)
        ):
            raise ValueError("Transcript receipt/provenance changed")
        raw = read_file(private(locate(folder, "source." + binding.format)), MIB)
        payload = read_file(private(locate(folder, "transcript.json")), 8 * MIB)
        if (
            api.sha(payload) != receipt.transcript_sha256
            or len(raw) != receipt.raw_bytes
        ):
            raise ValueError("Transcript payload changed")
        document = TranscriptDocument.model_validate(_json(payload))
        if (
            document.language != binding.language
            or not document.provenance
            or document.provenance.source_url != binding.original_url
            or document.provenance.media_format != binding.format
            or document.provenance.language != binding.language
            or receipt.raw_sha256 != grant.expected_sha256
        ):
            raise ValueError("Transcript metadata changed")
        result.update(
            adapter="existing_official_transcript",
            processed=True,
            provenance="pinned_b5_receipt",
            times="source_cues" if binding.format == "srt" else "unknown",
            duration_seconds=document.duration,
            parser_revision=receipt.importer_sha256,
        )
    else:
        if ref.plan is None or parser_for(binding)[0] is None:
            raise ValueError("Existing MaterialPlan required")
        receipt_path = locate(root, f"{key}/receipt.v1.json")
        raw_receipt = read_file(private(receipt_path), MIB)
        receipt = ArtifactReceipt.model_validate(_json(raw_receipt))
        if receipt.binding != binding or receipt.raw_sha256 != grant.expected_sha256:
            raise ValueError("Material receipt binding changed")
        raw_path = locate(root, f"{key}/{receipt.raw_path}")
        raw = read_file(private(raw_path), MIB)
        if not receipt.normalized_path:
            raise ValueError("Missing normalized artifact")
        normalized_path = private(locate(root, receipt.normalized_path))
        review = prepare_material_handoff(
            workspace=root,
            normalized_path=normalized_path,
            receipt_path=receipt_path,
            raw_path=raw_path,
            plan_path=safe_path(ref.plan),
        )
        if review.handoff is None:
            raise ValueError("Existing material gate rejected artifacts")
        result.update(
            adapter="existing_material_handoff",
            processed=True,
            provenance="pinned_material_receipt",
            technical_quality=review.report.status,
            parser_revision=receipt.parser.config_id,
            visual_evidence_available=any(
                i.artifact_path and i.sha256 for i in review.handoff.document.images
            ),
        )
    if (
        api.sha(raw_receipt) != ref.receipt_sha256
        or api.sha(raw) != grant.expected_sha256
    ):
        raise ValueError("Pinned raw/receipt hash changed")
    return result
