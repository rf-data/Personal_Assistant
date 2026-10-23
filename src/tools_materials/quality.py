"""Read-only offline checks of exact artifact bytes and existing CS50 contracts.

No parsers, downloaders, task runners or SDKs are instantiated. Untrusted JSON
failures become findings. Schema defaults never stand in for declared versions.
"""

import hashlib
import json
import math
import re
from pathlib import Path

from pydantic import ValidationError

from src.model_discovery.cs50 import deterministic_id
from src.model_materials.materials import (
    ArtifactReceipt,
    Location,
    MaterialPlan,
    NormalizedDocument,
)
from src.model_materials.quality import MaterialFinding, MaterialQualityReport
from src.tools_lecture.cs50_manifest import _unique_json_keys
from src.tools_materials.storage import locate


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _json(raw):
    def reject_constant(value):
        raise ValueError(f"Non-finite JSON number: {value}")

    def finite_float(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError(f"Non-finite JSON number: {value}")
        return result

    return json.loads(
        raw,
        object_pairs_hook=_unique_json_keys,
        parse_constant=reject_constant,
        parse_float=finite_float,
    )


class _Audit:
    def __init__(self):
        self.findings = []

    def add(
        self,
        code,
        message,
        *,
        severity="error",
        category="technical",
        input="normalized",
        field=None,
        block=None,
        location=None,
        image_id=None,
    ):
        self.findings.append(
            MaterialFinding(
                code=code,
                severity=severity,
                category=category,
                message=message,
                input=input,
                field=field,
                block_id=block.block_id if block else None,
                block_order=block.order if block else None,
                location=block.location if block else location,
                image_id=image_id,
            )
        )

    def load(self, path, model, input, observed):
        try:
            raw = Path(path).read_bytes()
            observed[input] = _sha(raw)
            data = _json(raw)
            if not isinstance(data, dict):
                raise ValueError("Expected a JSON object")
            # These defaults support legacy readers, but are not evidence of a version.
            for field in ("schema_version",):
                if field not in data:
                    self.add(
                        "version_missing",
                        "Explicit schema_version is required",
                        input=input,
                        field=field,
                    )
            if input in {"normalized", "receipt"}:
                binding = data.get("binding")
                if isinstance(binding, dict) and "schema_version" not in binding:
                    self.add(
                        "version_missing",
                        "Explicit material binding schema_version is required",
                        input=input,
                        field="binding.schema_version",
                    )
                config = data.get("parser")
                if not isinstance(config, dict) or "version" not in config:
                    self.add(
                        "version_missing",
                        "Explicit parser.version is required",
                        input=input,
                        field="parser.version",
                    )
            if input == "normalized":
                self.block_identities(data)
            return model.model_validate_json(raw, strict=True)
        except ValidationError as exc:
            for error in exc.errors(
                include_url=False, include_context=False, include_input=False
            ):
                loc = error["loc"]
                location = None
                block_id = None
                order = None
                if (
                    input == "normalized"
                    and len(loc) > 1
                    and loc[0] == "blocks"
                    and type(loc[1]) is int
                ):
                    blocks = data.get("blocks", [])
                    if (
                        isinstance(blocks, list)
                        and loc[1] < len(blocks)
                        and isinstance(blocks[loc[1]], dict)
                    ):
                        b = blocks[loc[1]]
                        block_id = (
                            b.get("block_id")
                            if isinstance(b.get("block_id"), str)
                            else None
                        )
                        order = loc[1]
                        try:
                            location = Location.model_validate(b.get("location"))
                        except ValidationError:
                            pass
                self.findings.append(
                    MaterialFinding(
                        code="schema_invalid",
                        severity="error",
                        category="technical",
                        message=error["msg"],
                        input=input,
                        field=".".join(map(str, loc)) or "$",
                        block_id=block_id,
                        block_order=order,
                        location=location,
                    )
                )
        except (OSError, UnicodeError, ValueError, TypeError, RecursionError) as exc:
            self.add("input_invalid", str(exc), input=input)
        return None

    def block_identities(self, data):
        # Diagnose exact offending blocks even when the existing model's root
        # identity validator subsequently rejects the entire document.
        try:
            shell = NormalizedDocument.model_validate(
                {**data, "blocks": [], "images": []}
            )
        except (ValueError, TypeError):
            return
        blocks = data.get("blocks")
        if not isinstance(blocks, list):
            return
        seen = set()
        for index, block in enumerate(blocks):
            if not isinstance(block, dict):
                continue
            identity = block.get("block_id")
            if not isinstance(identity, str):
                continue
            if (
                identity in seen
                or block.get("order") != index
                or identity
                != deterministic_id("material_block", shell.document_id, str(index))
            ):
                try:
                    location = Location.model_validate(block.get("location"))
                except ValueError:
                    location = None
                self.findings.append(
                    MaterialFinding(
                        code="block_identity",
                        severity="error",
                        category="technical",
                        message="Block identity/order contradicts document or repeats another block",
                        input="normalized",
                        field=f"blocks.{index}",
                        block_id=identity,
                        block_order=index,
                        location=location,
                    )
                )
            seen.add(identity)


def _geometry(audit, location, doc, *, block=None, image_id=None):
    kwargs = dict(block=block, location=location, image_id=image_id)
    if doc.parser.name == "html" and (
        not location.dom or not location.dom.startswith("/")
    ):
        audit.add("dom_missing", "HTML source needs an absolute DOM locator", **kwargs)
    if doc.parser.name == "pdf":
        count = doc.metadata.get("page_count")
        if location.page is None or (type(count) is int and location.page > count):
            audit.add(
                "page_invalid",
                "PDF source page is missing or outside page_count",
                **kwargs,
            )
        if location.bbox is None:
            audit.add(
                "bbox_missing",
                "PDF source has no bounding box",
                severity="warning",
                **kwargs,
            )
    if location.bbox is not None:
        x0, y0, x1, y1 = location.bbox
        if not all(math.isfinite(x) for x in location.bbox) or x0 > x1 or y0 > y1:
            audit.add(
                "bbox_invalid", "Non-finite or inverted source bounding box", **kwargs
            )


def _structure(audit, doc):
    if not doc.title or not doc.title.strip():
        audit.add(
            "title_missing",
            "Document title is absent",
            severity="warning",
            field="title",
        )
    if not doc.metadata:
        audit.add(
            "metadata_missing",
            "No document metadata was supplied",
            severity="warning",
            field="metadata",
        )
    if not doc.blocks:
        audit.add("blocks_empty", "Document has no source blocks", field="blocks")
    if not doc.binding.resource.provenance:
        audit.add(
            "provenance_missing",
            "Discovery source provenance is absent",
            field="binding.resource.provenance",
        )
    if doc.parser.name in {"html", "pdf"} and doc.parser.version != "2":
        audit.add(
            "parser_legacy",
            "Legacy parser is readable but requires separate review; C10 handoff requires v2",
            field="parser.version",
        )
    expected_parser = (
        "pdf"
        if doc.binding.format == "pdf"
        else "html"
        if doc.binding.format == "html" and doc.binding.role != "source_code"
        else None
    )
    if expected_parser and doc.parser.name != expected_parser:
        audit.add(
            "parser_conflict",
            "Parser kind contradicts material format",
            field="parser.name",
        )
    # Unknown publisher metadata is retained. Only explicit identity claims are compared.
    identities = dict(
        course_id=doc.binding.resource.course_id,
        resource_id=doc.binding.source_id,
        material_id=doc.binding.material_id,
        document_id=doc.document_id,
    )
    for key, expected in identities.items():
        if key in doc.metadata and doc.metadata[key] != expected:
            audit.add(
                "metadata_conflict",
                f"Metadata {key} contradicts source binding",
                field=f"metadata.{key}",
            )
    if "section_keys" in doc.metadata and doc.metadata["section_keys"] != list(
        doc.binding.resource.section_keys
    ):
        audit.add(
            "metadata_conflict",
            "Metadata section_keys contradicts source binding",
            field="metadata.section_keys",
        )
    if "lecture_ids" in doc.metadata and doc.metadata["lecture_ids"] != list(
        doc.binding.lecture_ids
    ):
        audit.add(
            "metadata_conflict",
            "Metadata lecture_ids contradicts source binding",
            field="metadata.lecture_ids",
        )
    lists = {b.location.dom: b for b in doc.blocks if b.type == "list"}
    seen = set()
    last_page = 0
    for index, block in enumerate(doc.blocks):
        if block.block_id in seen or block.order != index:
            audit.add(
                "block_identity",
                "Duplicate block identity or invalid order",
                block=block,
            )
        seen.add(block.block_id)
        _geometry(audit, block.location, doc, block=block)
        if block.location.page is not None:
            if block.location.page < last_page:
                audit.add("page_order", "Block page order goes backwards", block=block)
            last_page = block.location.page
        for message in block.uncertainty:
            audit.add(
                "parser_uncertainty",
                message,
                severity="warning",
                category="semantic_review",
                block=block,
            )
        data = block.data
        if doc.parser.name == "pdf" and block.type in {
            "heading",
            "paragraph",
            "code",
            "math",
        }:
            _pdf_text(audit, block)
        if "reference_only" in data and type(data["reference_only"]) is not bool:
            audit.add(
                "projection_invalid", "reference_only must be boolean", block=block
            )
        if "content_role" in data and data["content_role"] != "table_of_contents":
            audit.add(
                "projection_invalid",
                "Unknown content role cannot be safely aggregated",
                block=block,
            )
        if block.type == "link" and (
            data.get("reference_only") is not True
            or not isinstance(data.get("original_url"), str)
            or not data["original_url"]
        ):
            audit.add(
                "link_projection_invalid",
                "Link needs reference_only=true and its original URL",
                block=block,
            )
        if (
            data.get("reference_only") is True
            or data.get("content_role") == "table_of_contents"
        ):
            audit.add(
                "reference_projection",
                "Reference projection retained and excluded from text aggregation",
                severity="info",
                block=block,
            )
        if block.type == "list":
            items = data.get("item_doms")
            if (
                block.text
                or type(data.get("ordered")) is not bool
                or not isinstance(items, list)
                or any(
                    not isinstance(p, str)
                    or not p.startswith((block.location.dom or "") + "/li[")
                    for p in items
                )
                or len(items) != len(set(items))
            ):
                audit.add(
                    "list_invalid",
                    "List must be structural with unique direct item DOM references",
                    block=block,
                )
        contexts = data.get("list_context", [])
        if not isinstance(contexts, list):
            audit.add(
                "list_context_invalid", "list_context must be a list", block=block
            )
        else:
            for item in contexts:
                if not isinstance(item, dict):
                    audit.add(
                        "list_context_invalid", "Invalid list item context", block=block
                    )
                    continue
                parent = (
                    lists.get(item.get("list_dom"))
                    if isinstance(item.get("list_dom"), str)
                    else None
                )
                item_index = item.get("item_index")
                doms = parent.data.get("item_doms") if parent else None
                if (
                    parent is None
                    or not isinstance(doms, list)
                    or type(item_index) is not int
                    or not 0 <= item_index < len(doms)
                    or doms[item_index] != item.get("item_dom")
                    or type(item.get("ordered")) is not bool
                    or item["ordered"] != parent.data.get("ordered")
                    or not (block.location.dom or "").startswith(
                        str(item.get("item_dom"))
                    )
                ):
                    audit.add(
                        "list_context_invalid",
                        "List item context does not resolve to its source list/item",
                        block=block,
                    )
                elif (
                    parent.data.get("content_role") == "table_of_contents"
                    and data.get("content_role") != "table_of_contents"
                ):
                    audit.add(
                        "toc_projection_invalid",
                        "TOC child lost its projection marker",
                        block=block,
                    )
        spans = data.get("inline_code", [])
        if not isinstance(spans, list):
            audit.add(
                "inline_code_invalid",
                "Inline code references must be a list",
                block=block,
            )
        else:
            previous = 0
            for span in spans:
                if (
                    not isinstance(span, dict)
                    or type(span.get("start")) is not int
                    or type(span.get("end")) is not int
                    or not previous <= span["start"] <= span["end"] <= len(block.text)
                    or block.text[span["start"] : span["end"]] != span.get("text")
                ):
                    audit.add(
                        "inline_code_invalid",
                        "Inline code is not an exact ordered character window",
                        block=block,
                    )
                else:
                    previous = span["end"]
        if (
            "code_view" in data
            or "line_numbers" in data
            or "line_number_strategy" in data
        ):
            _code_view(audit, doc, block)
        if block.type in {"math", "unknown_block"}:
            audit.add(
                "semantic_review",
                "Source notation/classification needs human review",
                severity="warning",
                category="semantic_review",
                block=block,
            )
        if doc.parser.name == "pdf" and block.type == "table":
            audit.add(
                "table_overlap",
                "Geometric table may project existing text; excluded from aggregation",
                severity="warning",
                category="semantic_review",
                block=block,
            )
    if doc.parser.name == "pdf":
        count = doc.metadata.get("page_count")
        if type(count) is not int or not 1 <= count <= doc.parser.max_pages:
            audit.add(
                "page_count_invalid",
                "PDF metadata needs a bounded positive integer page_count",
                field="metadata.page_count",
            )
        else:
            pages = {b.location.page for b in doc.blocks}
            for page in range(1, count + 1):
                if page not in pages:
                    audit.add(
                        "page_uncovered",
                        "No normalized block covers this page; blank/image-only/lost content is unresolved",
                        severity="warning",
                        category="semantic_review",
                        location=Location(page=page),
                    )
    for message in doc.warnings:
        match = re.match(r"Page ([0-9]{1,6}):", message)
        audit.add(
            "parser_warning",
            message,
            severity="warning",
            category="semantic_review",
            location=Location(page=int(match[1]))
            if match and int(match[1]) > 0
            else None,
        )


def _pdf_text(audit, block):
    data = block.data
    classification = data.get("classification")
    valid = isinstance(classification, dict)
    if valid:
        signals = classification.get("signals")
        ratio = classification.get("monospace_ratio")
        valid = (
            classification.get("strategy") == "python_math_v2"
            and isinstance(signals, list)
            and all(isinstance(s, str) for s in signals)
            and signals == sorted(set(signals))
            and type(ratio) in {int, float}
            and 0 <= ratio <= 1
            and type(classification.get("python_syntax_valid")) is bool
        )
    if not valid:
        audit.add(
            "classification_invalid",
            "PDF-v2 text needs its structured classification evidence",
            block=block,
        )
    boxes = data.get("line_bboxes")
    if (
        not isinstance(boxes, list)
        or len(boxes) != len(block.text.split("\n"))
        or any(
            not isinstance(box, list)
            or len(box) != 4
            or any(type(x) not in {int, float} for x in box)
            or box[0] > box[2]
            or box[1] > box[3]
            for box in boxes
        )
    ):
        audit.add(
            "line_geometry_invalid",
            "PDF-v2 line geometry must match the original text lines",
            block=block,
        )


def _code_view(audit, doc, block):
    data = block.data
    rows, view = data.get("line_numbers"), data.get("code_view")
    valid = (
        doc.parser.name == "pdf"
        and doc.parser.version == "2"
        and block.type == "code"
        and data.get("line_number_strategy") == "sequential_aligned_two_space_gutter_v1"
        and isinstance(rows, list)
        and len(rows) >= 3
        and isinstance(view, str)
    )
    if valid:
        source, payload = block.text.split("\n"), view.split("\n")
        valid = len(source) == len(payload) == len(rows)
        previous = None
        width = None
        for index, row in enumerate(rows):
            if not valid:
                break
            valid = (
                isinstance(row, dict)
                and type(row.get("line_index")) is int
                and row["line_index"] == index
                and type(row.get("number")) is int
                and isinstance(row.get("prefix"), str)
            )
            if not valid:
                break
            prefix = row["prefix"]
            match = re.fullmatch(r" *([0-9]{1,5})  ", prefix)
            valid = (
                bool(match)
                and int(match[1]) == row["number"]
                and (previous is None or row["number"] == previous + 1)
                and (width is None or len(prefix) == width)
                and prefix + payload[index] == source[index]
            )
            previous, width = row["number"], len(prefix)
    if not valid:
        audit.add(
            "code_view_invalid",
            "Derived code view/line map cannot reconstruct exact numbered source",
            block=block,
        )
    else:
        audit.add(
            "derived_code_view",
            "Reversible code view retained as an alternative, excluded from additional aggregation",
            severity="info",
            block=block,
        )


def _inspect_material(*, normalized_path, receipt_path, raw_path, plan_path, workspace):
    """Internal checked snapshot shared by the report API and handoff adapter."""
    audit = _Audit()
    inputs = {
        "normalized": str(normalized_path),
        "receipt": str(receipt_path),
        "raw": str(raw_path),
        "plan": str(plan_path),
        "workspace": str(workspace),
    }
    observed = {}
    artifacts = {}
    for key in ("normalized", "receipt", "raw"):
        try:
            artifacts[key] = locate(workspace, Path(inputs[key]).absolute())
        except ValueError as exc:
            audit.add("path_invalid", str(exc), input=key)
    doc = (
        audit.load(artifacts["normalized"], NormalizedDocument, "normalized", observed)
        if "normalized" in artifacts
        else None
    )
    receipt = (
        audit.load(artifacts["receipt"], ArtifactReceipt, "receipt", observed)
        if "receipt" in artifacts
        else None
    )
    plan = audit.load(plan_path, MaterialPlan, "plan", observed)
    if "raw" in artifacts:
        try:
            # Existing digest primitive streams raw sources without parsing them.
            from src.tools_lecture.execute_cs50 import digest

            observed["raw"] = digest(artifacts["raw"])
        except OSError as exc:
            audit.add("input_invalid", str(exc), input="raw")
    if doc:
        _structure(audit, doc)
        from src.tools_materials.quality_projection import audit_html_projection

        audit_html_projection(audit, doc)
        if observed.get("raw") != doc.raw_sha256:
            audit.add(
                "raw_hash_mismatch",
                "Raw bytes do not match normalized document raw_sha256",
                input="raw",
            )
        if plan:
            matches = [
                b for b in plan.materials if b.material_id == doc.binding.material_id
            ]
            if matches != [doc.binding]:
                audit.add(
                    "plan_binding_conflict",
                    "Material/course/section/lecture binding contradicts the reviewed plan",
                    input="plan",
                )
            if not doc.binding.resource.section_keys or not doc.binding.lecture_ids:
                audit.add(
                    "lecture_binding_missing",
                    "Material needs explicit sections and logical lecture IDs",
                    field="binding.lecture_ids",
                )
        if receipt:
            if (
                receipt.binding != doc.binding
                or receipt.parser != doc.parser
                or receipt.raw_sha256 != doc.raw_sha256
            ):
                audit.add(
                    "receipt_binding_conflict",
                    "Receipt binding, parser or raw hash contradicts document",
                    input="receipt",
                )
            if receipt.status != "completed" or receipt.error:
                audit.add(
                    "receipt_incomplete",
                    "Receipt must be completed without an error",
                    input="receipt",
                    field="status",
                )
            if (
                not receipt.normalized_sha256
                or receipt.normalized_sha256 != observed.get("normalized")
            ):
                audit.add(
                    "normalized_hash_mismatch",
                    "Exact normalized file bytes do not match receipt hash",
                    input="receipt",
                    field="normalized_sha256",
                )
            directory = doc.binding.material_id.split(":")[1]
            for key, relative in (
                ("normalized", receipt.normalized_path),
                ("raw", f"{directory}/{receipt.raw_path}"),
                ("receipt", f"{directory}/receipt.v1.json"),
            ):
                try:
                    if not relative or locate(workspace, relative) != artifacts.get(
                        key
                    ):
                        raise ValueError(
                            "Explicit input path contradicts receipt/storage binding"
                        )
                except ValueError as exc:
                    audit.add(
                        "receipt_path_conflict", str(exc), input="receipt", field=key
                    )
            expected = {
                i.artifact_path: i.sha256 for i in doc.images if i.artifact_path
            }
            if receipt.image_hashes != expected:
                audit.add(
                    "image_manifest_conflict",
                    "Receipt image hashes contradict normalized image manifest",
                    input="receipt",
                    field="image_hashes",
                )
        referenced = {
            b.data.get("image_id")
            for b in doc.blocks
            if b.type == "image_reference" and isinstance(b.data.get("image_id"), str)
        }
        for image in doc.images:
            _geometry(audit, image.source_location, doc, image_id=image.image_id)
            kwargs = dict(
                input="image", image_id=image.image_id, location=image.source_location
            )
            if image.image_id not in referenced:
                audit.add(
                    "image_unreferenced",
                    "Image artifact has no block reference",
                    severity="warning",
                    **kwargs,
                )
            for block in doc.blocks:
                if (
                    block.type == "image_reference"
                    and block.data.get("image_id") == image.image_id
                    and block.location != image.source_location
                ):
                    audit.add(
                        "image_location_conflict",
                        "Image block and artifact source positions disagree",
                        block=block,
                        input="image",
                        image_id=image.image_id,
                    )
            if not image.artifact_path:
                audit.add(
                    "image_reference_only",
                    "No local image bytes; interpretation remains unverified",
                    severity="warning",
                    category="semantic_review",
                    **kwargs,
                )
                if image.sha256:
                    audit.add(
                        "image_metadata_conflict",
                        "Image hash supplied without an artifact path",
                        **kwargs,
                    )
                continue
            try:
                path = locate(
                    Path(normalized_path).absolute().parent, image.artifact_path
                )
                from src.tools_lecture.execute_cs50 import digest

                if not image.sha256 or digest(path) != image.sha256:
                    audit.add(
                        "image_hash_mismatch",
                        "Local image bytes differ from declared hash",
                        **kwargs,
                    )
            except (OSError, ValueError) as exc:
                audit.add("image_artifact_missing", str(exc), **kwargs)
    errors = any(f.severity == "error" for f in audit.findings)
    warnings = any(f.severity == "warning" for f in audit.findings)
    report = MaterialQualityReport(
        schema_version=2,
        validator_version="cs50_material_quality_v2",
        status="failed" if errors else "passed_with_warnings" if warnings else "passed",
        inputs=inputs,
        observed_sha256=observed,
        document_id=doc.document_id if doc else None,
        material_id=doc.binding.material_id if doc else None,
        resource_id=doc.binding.source_id if doc else None,
        course_id=doc.binding.resource.course_id if doc else None,
        section_keys=doc.binding.resource.section_keys if doc else (),
        lecture_ids=doc.binding.lecture_ids if doc else (),
        findings=tuple(audit.findings),
    )
    return report, doc, receipt, plan


def validate_material(**paths):
    """Return a deterministic MaterialQualityReport; never modify any input."""
    return _inspect_material(**paths)[0]
