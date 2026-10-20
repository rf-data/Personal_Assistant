"""Two default entries; opt-in PDF and workflow. No command/path parameters."""

from dataclasses import dataclass

from src.job_control.models import (
    ContentImportParams,
    IndexParams,
    PdfParams,
    PlanningParams,
    QualityParams,
    WorkflowParams,
)


@dataclass(frozen=True)
class Process:
    process_id: str
    model: type
    input_kind: str
    artifact_kind: str
    reviewed_runner: str
    timeout_seconds: float = 30
    cpu_seconds: int = 20
    memory_bytes: int = 768 * 1024 * 1024
    file_bytes: int = 8 * 1024 * 1024
    file_descriptors: int = 64
    subprocesses: int = 32


REGISTRY = {
    p.process_id: p
    for p in (
        Process(
            "material_planning",
            PlanningParams,
            "manifest",
            "material_plan",
            "src.tools_materials.processing.make_plan",
        ),
        Process(
            "quality_evaluation",
            QualityParams,
            "material_bundle",
            "quality_report",
            "scripts.cs50_material_quality.main",
        ),
    )
}
DISABLED = (
    "course_discovery",
    "lecture_compilation",
    "material_download",
    "material_parsing",
    "audio_transcription",
    "visual_analysis",
    "visual_enrichment",
    "knowledge_extraction",
    "knowledge_consolidation",
)

WORKFLOW_PROCESS = Process(
    "cs50_offline_workflow",
    WorkflowParams,
    "workflow_bundle",
    "workflow_report",
    "src.workflows.engine.run",
    timeout_seconds=90,
    cpu_seconds=60,
    # Linux NPROC counts all threads of the UID, not just this job's children.
    # Fixed trusted topology still permits only one PDF worker per running job.
    subprocesses=512,
)
PDF_PROCESS = Process(
    "material_parsing",
    PdfParams,
    "pdf_bundle",
    "material_receipt",
    "src.tools_materials.processing.MaterialProcessor.parse (local PDF-v2 only)",
    subprocesses=512,
)
INDEX_PROCESS = Process(
    "content_index_build",
    IndexParams,
    "index_bundle",
    "index_build",
    "src.job_control.index_jobs.run",
    timeout_seconds=180,
    cpu_seconds=120,
    file_bytes=64 * 1024 * 1024,
)


IMPORT_PROCESS = Process(
    "content_import",
    ContentImportParams,
    "content_import_bundle",
    "content_import",
    "src.job_control.import_jobs.run",
    timeout_seconds=180,
    cpu_seconds=120,
    file_bytes=64 * 1024 * 1024,
)


def process_for(process_id):
    if process_id == IMPORT_PROCESS.process_id:
        return IMPORT_PROCESS
    if process_id == INDEX_PROCESS.process_id:
        return INDEX_PROCESS
    if process_id == WORKFLOW_PROCESS.process_id:
        return WORKFLOW_PROCESS
    if process_id == PDF_PROCESS.process_id:
        return PDF_PROCESS
    if process_id not in REGISTRY:
        raise ValueError("Process is not enabled")
    return REGISTRY[process_id]


def registry_document(*, workflows=False, pdf=False, index=False, imports=False):
    return {
        "schema_version": 1,
        "processes": [
            dict(
                process_id=p.process_id,
                parameter_schema=p.model.model_json_schema(),
                actions=["preview", "create", "start", "cancel"],
                execution="offline_python_subprocess",
                timeout_seconds=p.timeout_seconds,
                cpu_seconds=p.cpu_seconds,
                memory_bytes=p.memory_bytes,
                file_bytes=p.file_bytes,
                file_descriptors=p.file_descriptors,
                subprocesses=p.subprocesses,
                max_parallel=1,
                cancellable=True,
                expected_artifacts=[p.artifact_kind],
                required_role="operator",
                runner=p.reviewed_runner,
            )
            for p in (
                *REGISTRY.values(),
                *((WORKFLOW_PROCESS,) if workflows else ()),
                *((PDF_PROCESS,) if pdf else ()),
                *((INDEX_PROCESS,) if index else ()),
                *((IMPORT_PROCESS,) if imports else ()),
            )
        ],
        "disabled_processes": [
            p for p in DISABLED if not (pdf and p == "material_parsing")
        ],
    }
