"""Controlled C16 imports of operator-pinned existing C23 bundles."""

from typing import Literal

from pydantic import Field, TypeAdapter, model_validator

from src.content_store.inventory import InventorySelection
from src.content_store.models import Name
from src.content_store.read_models import ContentReadSettings
from src.job_control.models import Contract, Identifier, Preview, Sha


class ContentImportPlan(Contract):
    schema_version: Literal[1]
    content: ContentReadSettings
    selection: InventorySelection
    allowed_subjects: tuple[Identifier, ...] = Field(min_length=1, max_length=32)

    @model_validator(mode="after")
    def bounded(self):
        TypeAdapter(Name).validate_python(self.selection.source_id)
        if len(set(self.allowed_subjects)) != len(self.allowed_subjects):
            raise ValueError("unique import subjects required")
        return self


class ImportInfo(Contract):
    schema_version: Literal[1] = 1
    input_ref: Identifier
    source_id: Name
    course_id: str
    adapter: Literal["material", "srt"]
    parser_config_id: Name
    parser_name: Name
    parser_version: Name
    implementation_revision: str
    source_version_id: Name
    parsed_version_id: Name
    raw_sha256: Sha
    payload_sha256: Sha
    state_sha256: Sha
    existing_parsed_version_id: Name | None
    can_import: bool
    operator_decision: Literal["content_recovery_required"] | None
    max_file_bytes: Literal[8388608] = 8388608
    max_bundle_bytes: Literal[33554432] = 33554432


class ImportPreview(Contract):
    schema_version: Literal[1] = 1
    plan: ImportInfo
    preview: Preview | None
    request_key: Identifier


class ImportReceipt(Contract):
    schema_version: Literal[1] = 1
    job_id: Identifier
    source_id: Name
    source_version_id: Name
    parsed_version_id: Name
    raw_sha256: Sha
    payload_sha256: Sha
    created: bool
    parsed_route: str
    index_inputs_route: Literal["/v1/content/index/inputs"] = "/v1/content/index/inputs"
