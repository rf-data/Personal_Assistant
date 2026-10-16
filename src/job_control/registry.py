"""Only two reviewed fixed entry points. No command/path parameters."""

from dataclasses import dataclass

from src.job_control.models import PlanningParams, QualityParams


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


def process_for(process_id):
    if process_id not in REGISTRY:
        raise ValueError("Process is not enabled")
    return REGISTRY[process_id]


def registry_document():
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
            for p in REGISTRY.values()
        ],
        "disabled_processes": list(DISABLED),
    }
