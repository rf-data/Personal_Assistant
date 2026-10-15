"""Read-only material input mapping. No transcript collection/Knowledge changes."""

from typing import Literal

from pydantic import Field, model_validator

from src.model_discovery.cs50 import DiscoveryModel, deterministic_id
from src.model_materials.materials import (
    Block,
    MaterialResource,
    NormalizedDocument,
    ParserConfig,
)


class MaterialCollection(DiscoveryModel):
    schema_version: Literal[1] = 1
    name: Literal["cs50_material_blocks_v1"] = "cs50_material_blocks_v1"
    execution_supported: Literal[False] = False
    embedding_config: dict | None = (
        None  # Must be fully bound before any future vector upload.
    )


class MaterialUnit(DiscoveryModel):
    schema_version: Literal[1] = 1
    collection: Literal["cs50_material_blocks_v1"] = "cs50_material_blocks_v1"
    unit_id: str
    document_id: str
    binding: MaterialResource
    raw_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    parser: ParserConfig
    block: Block
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)
    text: str
    knowledge_fact_verified: Literal[False] = False

    @model_validator(mode="after")
    def checked_window(self):
        expected_doc = deterministic_id(
            "material_doc",
            self.binding.material_id,
            self.raw_sha256,
            self.parser.config_id,
        )
        expected_unit = deterministic_id(
            "material_unit",
            expected_doc,
            self.block.block_id,
            str(self.char_start),
            str(self.char_end),
        )
        if (
            self.document_id != expected_doc
            or self.unit_id != expected_unit
            or self.block.block_id
            != deterministic_id("material_block", expected_doc, str(self.block.order))
            or not self.char_start < self.char_end <= len(self.block.text)
            or self.text != self.block.text[self.char_start : self.char_end]
            or self.block.type
            not in {"heading", "paragraph", "list", "table", "code", "link"}
        ):
            raise ValueError("Material window contradicts original block/binding")
        return self


def map_material(document, *, max_chars=2000):
    """Exact character windows within a source block, never inferred timed Evidence.

    Math/image/unknown blocks remain references in NormalizedDocument and cannot
    silently become verified Knowledge facts. Empty tables still retain structure.
    """
    document = NormalizedDocument.model_validate_json(document.model_dump_json())
    if not 1 <= max_chars <= 10000:
        raise ValueError("Invalid bounded block window size")
    units = []
    for block in document.blocks:
        if block.type not in {"heading", "paragraph", "list", "table", "code", "link"}:
            continue
        text = block.text
        if not text and block.type == "table":
            # Structured tables need a separate explicit serializer/evaluation before embedding.
            continue
        for start in range(0, len(text), max_chars):
            end = min(start + max_chars, len(text))
            units.append(
                MaterialUnit(
                    unit_id=deterministic_id(
                        "material_unit",
                        document.document_id,
                        block.block_id,
                        str(start),
                        str(end),
                    ),
                    document_id=document.document_id,
                    binding=document.binding,
                    raw_sha256=document.raw_sha256,
                    parser=document.parser,
                    block=block,
                    char_start=start,
                    char_end=end,
                    text=text[start:end],
                )
            )
    return tuple(units)
