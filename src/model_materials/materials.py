"""Versioned identities and normalized source blocks, never inferred timestamps."""

from pathlib import PurePosixPath
from typing import Literal, Self

from pydantic import Field, field_validator, model_validator

from src.model_discovery.cs50 import (
    DiscoveryModel,
    NonEmpty,
    ResourceCandidate,
    deterministic_id,
)

Sha = str  # validated on fields below
Status = Literal[
    "discovered",
    "selected",
    "downloaded",
    "verified",
    "parsed",
    "normalized",
    "completed",
    "failed",
    "unsupported",
    "blocked",
    "conflict",
]


class MaterialResource(DiscoveryModel):
    schema_version: Literal[1] = 1
    resource: ResourceCandidate
    lecture_ids: tuple[NonEmpty, ...] = ()
    variant_id: str | None = None
    original_url: NonEmpty
    format: NonEmpty
    role: NonEmpty
    language: str | None = None
    source_origin: Literal["official", "synthetic"] = "official"
    license_status: Literal["not_assessed", "reviewed"] = "not_assessed"

    @property
    def source_id(self):
        return self.resource.resource_id

    @property
    def material_id(self):
        return deterministic_id(
            "material", self.source_id, self.variant_id or "", self.original_url
        )

    @model_validator(mode="after")
    def checked_identity(self) -> Self:
        r = self.resource
        if self.variant_id:
            matches = [v for v in r.variants if v.variant_id == self.variant_id]
            if len(matches) != 1 or str(matches[0].original_url) != self.original_url:
                raise ValueError("Variant contradicts discovery binding")
            if self.language != matches[0].language:
                raise ValueError("Variant language contradicts discovery")
        elif self.original_url != str(r.original_url) or self.language != r.language:
            raise ValueError("Material URL/language contradicts discovery")
        if self.role != r.role.value:
            raise ValueError("Material role contradicts discovery")
        if len(set(self.lecture_ids)) != len(self.lecture_ids):
            raise ValueError("Duplicate lecture binding")
        return self


class ParserConfig(DiscoveryModel):
    name: Literal["html", "pdf", "code", "image"]
    version: Literal["1", "2"] = "1"
    max_bytes: int = Field(default=16 * 1024 * 1024, ge=1, le=64 * 1024 * 1024)
    max_pages: int = Field(default=100, ge=1, le=500)
    max_blocks: int = Field(default=20000, ge=1, le=50000)
    max_images: int = Field(default=100, ge=0, le=500)
    timeout: float = Field(default=20, gt=0, le=120, allow_inf_nan=False)
    memory_mb: int = Field(default=1024, ge=256, le=4096)

    @model_validator(mode="after")
    def supported_version(self):
        if self.version == "2" and self.name != "html":
            raise ValueError("Parser v2 is only implemented for HTML")
        return self

    @property
    def config_id(self):
        return deterministic_id("parser", self.model_dump_json())


class Location(DiscoveryModel):
    dom: str | None = None
    page: int | None = Field(default=None, ge=1)
    line_start: int | None = Field(default=None, ge=1)
    line_end: int | None = Field(default=None, ge=1)
    bbox: tuple[float, float, float, float] | None = None

    @model_validator(mode="after")
    def line_order(self):
        if self.line_end is not None and (
            self.line_start is None or self.line_end < self.line_start
        ):
            raise ValueError("Invalid line interval")
        return self


class Block(DiscoveryModel):
    block_id: NonEmpty
    order: int = Field(ge=0)
    type: Literal[
        "heading",
        "paragraph",
        "list",
        "table",
        "code",
        "math",
        "image_reference",
        "link",
        "unknown_block",
    ]
    text: str = ""
    data: dict = Field(default_factory=dict)
    location: Location
    uncertainty: tuple[str, ...] = ()


class ImageArtifact(DiscoveryModel):
    image_id: NonEmpty
    source_location: Location
    original_url: str | None = None
    artifact_path: str | None = None
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    mime_type: str | None = None
    caption: str | None = None
    context: str | None = None

    @field_validator("artifact_path")
    @classmethod
    def portable(cls, value):
        if value is not None:
            p = PurePosixPath(value)
            if (
                p.is_absolute()
                or ".." in p.parts
                or "\\" in value
                or p.as_posix() != value
            ):
                raise ValueError("Image path must be portable and relative")
        return value


class NormalizedDocument(DiscoveryModel):
    schema_version: Literal[1] = 1
    binding: MaterialResource
    raw_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    parser: ParserConfig
    title: str | None = None
    metadata: dict = Field(default_factory=dict)
    blocks: tuple[Block, ...]
    images: tuple[ImageArtifact, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def document_id(self):
        return deterministic_id(
            "material_doc",
            self.binding.material_id,
            self.raw_sha256,
            self.parser.config_id,
        )

    @model_validator(mode="after")
    def block_contract(self):
        if (
            len(self.blocks) > self.parser.max_blocks
            or len(self.images) > self.parser.max_images
        ):
            raise ValueError("Parser output exceeds configured limits")
        for order, block in enumerate(self.blocks):
            if block.order != order or block.block_id != deterministic_id(
                "material_block", self.document_id, str(order)
            ):
                raise ValueError("Invalid block identity/order")
        if len({i.image_id for i in self.images}) != len(self.images):
            raise ValueError("Duplicate image identity")
        image_ids = {i.image_id for i in self.images}
        if any(
            b.type == "image_reference" and b.data.get("image_id") not in image_ids
            for b in self.blocks
        ):
            raise ValueError("Image block references an unknown image artifact")
        return self


class ArtifactReceipt(DiscoveryModel):
    schema_version: Literal[1] = 1
    binding: MaterialResource
    status: Status
    raw_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    mime_type: str | None = None
    origin: Literal["local_import", "http_download"]
    raw_path: Literal["raw/source"] = "raw/source"
    parser: ParserConfig | None = None
    normalized_path: str | None = None
    normalized_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    image_hashes: dict[str, str] = Field(default_factory=dict)
    error: str | None = None
    history: tuple[Status, ...] = ()
