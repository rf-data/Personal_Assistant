"""Versioned audit output; source documents retain their existing material models."""

from typing import Literal

from pydantic import Field, model_validator

from src.model_discovery.cs50 import DiscoveryModel
from src.model_materials.materials import Location


class MaterialFinding(DiscoveryModel):
    code: str
    severity: Literal["error", "warning", "info"]
    category: Literal["technical", "semantic_review"]
    message: str
    input: Literal["normalized", "receipt", "raw", "plan", "image"]
    field: str | None = None
    block_id: str | None = None
    block_order: int | None = None
    location: Location | None = None
    image_id: str | None = None


class MaterialQualityReport(DiscoveryModel):
    schema_version: Literal[1, 2] = 1
    validator_version: Literal[
        "cs50_material_quality_v1", "cs50_material_quality_v2"
    ] = "cs50_material_quality_v1"
    status: Literal["passed", "passed_with_warnings", "failed"]
    inputs: dict[str, str]
    observed_sha256: dict[str, str] = Field(default_factory=dict)
    document_id: str | None = None
    material_id: str | None = None
    resource_id: str | None = None
    course_id: str | None = None
    section_keys: tuple[str, ...] = ()
    lecture_ids: tuple[str, ...] = ()
    findings: tuple[MaterialFinding, ...]

    @property
    def passed(self):
        return self.status != "failed"

    @model_validator(mode="after")
    def check_status(self):
        if self.validator_version != f"cs50_material_quality_v{self.schema_version}":
            raise ValueError("Quality schema and validator versions differ")
        severities = {f.severity for f in self.findings}
        expected = (
            "failed"
            if "error" in severities
            else "passed_with_warnings"
            if "warning" in severities
            else "passed"
        )
        if self.status != expected:
            raise ValueError("Quality status contradicts findings")
        return self
