"""Checked read-only lecture material references. Never create ResourceTasks.

LectureResource has no stable source/block IDs; KnowledgeEvidence requires times.
Keep the existing NormalizedDocument and MaterialUnit until a non-temporal
consumer can preserve these references. A passing report is an observation,
not permission to run extraction and not proof of source semantics.
"""

from typing import Literal

from pydantic import Field, model_serializer, model_validator

from src.model_discovery.cs50 import DiscoveryModel
from src.model_materials.materials import ArtifactReceipt, NormalizedDocument
from src.model_materials.quality import MaterialQualityReport
from src.tools_materials.html_projection import UnresolvedReference, link_owners
from src.tools_materials.mapping import (
    MaterialUnit,
    aggregation_exclusions,
    map_material,
)
from src.tools_materials.quality import _inspect_material


def _units(document, version=2):
    excluded = aggregation_exclusions(document)
    return tuple(
        u
        for u in map_material(document, projection_version=version)
        if u.block.block_id not in excluded
    )


def _unresolved(document):
    if document.parser.name != "html" or document.parser.version != "2":
        return ()
    excluded = aggregation_exclusions(document)
    blocks = [b for b in document.blocks if b.block_id not in excluded and b.text]
    return link_owners(document, blocks)[1]


class LectureMaterialHandoff(DiscoveryModel):
    schema_version: Literal[1, 2] = 1
    adapter_version: Literal["cs50_lecture_material_v1", "cs50_lecture_material_v2"] = (
        "cs50_lecture_material_v1"
    )
    execution_supported: Literal[False] = False
    knowledge_fact_verified: Literal[False] = False
    course_id: str
    section_keys: tuple[str, ...]
    lecture_ids: tuple[str, ...]
    normalized_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    plan_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    document: NormalizedDocument
    receipt: ArtifactReceipt
    aggregation_units: tuple[MaterialUnit, ...]
    unresolved_references: tuple[UnresolvedReference, ...] = ()
    excluded_blocks: dict[str, str]
    # Paths below refer to views within document.blocks, never extra content units.
    alternative_views: tuple[str, ...]

    @model_serializer(mode="wrap")
    def versioned_payload(self, handler):
        payload = handler(self)
        if self.schema_version == 1:
            payload.pop("unresolved_references", None)
        return payload

    @model_validator(mode="after")
    def check_references(self):
        b = self.document.binding
        views = tuple(
            f"blocks.{block.order}.data.code_view"
            for block in self.document.blocks
            if "code_view" in block.data
        )
        if (
            self.adapter_version != f"cs50_lecture_material_v{self.schema_version}"
            or self.unresolved_references
            != (_unresolved(self.document) if self.schema_version == 2 else ())
            or self.course_id != b.resource.course_id
            or self.section_keys != b.resource.section_keys
            or self.lecture_ids != b.lecture_ids
            or self.receipt.binding != b
            or self.receipt.normalized_sha256 != self.normalized_sha256
            or self.receipt.parser != self.document.parser
            or self.receipt.raw_sha256 != self.document.raw_sha256
            or self.receipt.status != "completed"
            or self.aggregation_units != _units(self.document, self.schema_version)
            or self.excluded_blocks != aggregation_exclusions(self.document)
            or self.alternative_views != views
        ):
            raise ValueError(
                "Handoff contradicts source binding, receipt or canonical aggregation"
            )
        if self.schema_version == 2:
            from src.tools_materials.quality import _Audit
            from src.tools_materials.quality_projection import audit_html_projection

            audit = _Audit()
            audit_html_projection(
                audit, self.document, self.aggregation_units, self.unresolved_references
            )
            if any(f.severity == "error" for f in audit.findings):
                raise ValueError("Handoff projection failed technical integrity checks")
        return self


class MaterialReview(DiscoveryModel):
    schema_version: Literal[1] = 1
    report: MaterialQualityReport
    handoff: LectureMaterialHandoff | None = None

    @model_validator(mode="after")
    def gate(self):
        if self.report.passed != (self.handoff is not None):
            raise ValueError("Only a passing gate may expose a lecture handoff")
        if self.handoff and (
            self.handoff.document.document_id != self.report.document_id
            or self.handoff.document.binding.material_id != self.report.material_id
            or self.handoff.document.binding.source_id != self.report.resource_id
            or self.handoff.course_id != self.report.course_id
            or self.handoff.section_keys != self.report.section_keys
            or self.handoff.lecture_ids != self.report.lecture_ids
            or self.handoff.normalized_sha256
            != self.report.observed_sha256.get("normalized")
            or self.handoff.plan_sha256 != self.report.observed_sha256.get("plan")
        ):
            raise ValueError("Handoff does not match quality report snapshot")
        return self


def prepare_material_handoff(**paths):
    """Recheck local artifacts and graph, returning report plus optional handoff.

    Serialized reports/handoffs are snapshots. Consumers must call this function
    again against their explicit paths before using artifacts at a later time.
    """
    report, document, receipt, _plan = _inspect_material(**paths)
    if not report.passed:
        return MaterialReview(report=report)
    binding = document.binding
    handoff = LectureMaterialHandoff(
        schema_version=2,
        adapter_version="cs50_lecture_material_v2",
        unresolved_references=_unresolved(document),
        course_id=binding.resource.course_id,
        section_keys=binding.resource.section_keys,
        lecture_ids=binding.lecture_ids,
        normalized_sha256=report.observed_sha256["normalized"],
        plan_sha256=report.observed_sha256["plan"],
        document=document,
        receipt=receipt,
        aggregation_units=_units(document),
        excluded_blocks=aggregation_exclusions(document),
        alternative_views=tuple(
            f"blocks.{b.order}.data.code_view"
            for b in document.blocks
            if "code_view" in b.data
        ),
    )
    return MaterialReview(report=report, handoff=handoff)
