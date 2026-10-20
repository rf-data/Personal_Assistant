"""Visual observations layered on existing material/location/image contracts."""

import math
from typing import Literal

from pydantic import Field, model_validator

from src.model_discovery.cs50 import DiscoveryModel, NonEmpty
from src.model_materials.materials import (
    ImageArtifact,
    Location,
    MaterialResource,
    ParserConfig,
)


class InventoryLimits(DiscoveryModel):
    max_bytes: int = Field(default=16 * 1024 * 1024, ge=1, le=64 * 1024 * 1024)
    max_pages: int = Field(default=100, ge=1, le=500)
    max_assets: int = Field(default=2000, ge=1, le=10000)
    max_paths: int = Field(default=4000, ge=1, le=20000)
    max_operations: int = Field(default=20000, ge=1, le=100000)
    max_image_pixels: int = Field(default=40_000_000, ge=1, le=200_000_000)
    timeout: float = Field(default=20, gt=0, le=120, allow_inf_nan=False)
    memory_mb: int = Field(default=1024, ge=256, le=4096)
    grouping_gap: float = Field(default=2, ge=0, le=20, allow_inf_nan=False)


class VisualWarning(DiscoveryModel):
    code: NonEmpty
    message: NonEmpty
    severity: Literal["warning", "error"] = "warning"


class VisualAsset(DiscoveryModel):
    asset_id: NonEmpty
    document_id: NonEmpty
    material_id: NonEmpty
    asset_type: Literal[
        "raster_image",
        "vector_graphics_candidate",
        "inline_svg",
        "external_image_reference",
        "unknown_visual",
    ]
    location: Location
    original_reference: str | None = None
    # Preserve the original normalized record, including declared (not observed) hash.
    image: ImageArtifact | None = None
    image_aliases: tuple[ImageArtifact, ...] = ()
    block_ids: tuple[str, ...] = ()
    artifact_status: Literal[
        "not_declared",
        "missing",
        "verified",
        "unverified",
        "hash_mismatch",
        "unsafe",
        "limit_exceeded",
    ] = "not_declared"
    observed_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    extraction_status: Literal[
        "available", "reference_only", "unsupported", "uncertain"
    ]
    review_status: Literal["requires_visual_review", "uncertain"] = (
        "requires_visual_review"
    )
    context: dict = Field(default_factory=dict)
    warnings: tuple[VisualWarning, ...] = ()

    @model_validator(mode="after")
    def geometry_and_bytes(self):
        bbox = self.location.bbox
        if bbox and (
            not all(math.isfinite(v) for v in bbox)
            or bbox[0] > bbox[2]
            or bbox[1] > bbox[3]
        ):
            raise ValueError("Invalid visual bounding box")
        if self.image and self.location != self.image.source_location:
            raise ValueError("Asset/image source positions differ")
        if any(alias.source_location != self.location for alias in self.image_aliases):
            raise ValueError("Image aliases must reference the same physical position")
        if self.extraction_status == "available" and (
            self.artifact_status != "verified" or self.observed_sha256 is None
        ):
            raise ValueError("Available requires verified local artifact bytes")
        return self


class VisualInventory(DiscoveryModel):
    schema_version: Literal[1] = 1
    inventory_version: Literal["visual_inventory_v1"] = "visual_inventory_v1"
    document_id: NonEmpty
    binding: MaterialResource
    parser: ParserConfig
    raw_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    observed_raw_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    normalized_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    inputs: dict[str, str]
    limits: InventoryLimits
    raw_scan: Literal["complete", "not_supplied", "failed", "unsupported"]
    scan_backend: dict[str, str] = Field(default_factory=dict)
    binding_verification: Literal["declared", "plan_verified", "conflict"] = "declared"
    assets: tuple[VisualAsset, ...]
    warnings: tuple[VisualWarning, ...]
    counts: dict[str, int]
    by_type: dict[str, int]
    by_page: dict[str, int]
    report_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def identities(self):
        if len({a.asset_id for a in self.assets}) != len(self.assets):
            raise ValueError("Duplicate visual occurrence identity")
        if any(
            a.document_id != self.document_id
            or a.material_id != self.binding.material_id
            for a in self.assets
        ):
            raise ValueError("Foreign visual asset")
        return self
