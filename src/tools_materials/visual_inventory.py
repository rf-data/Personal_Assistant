"""Read-only material visual inventory; no parser, image download or inference."""

import base64
import hashlib
import json
import math
import re
import stat
import subprocess
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from src.model_discovery.cs50 import deterministic_id
from src.model_materials.materials import (
    ArtifactReceipt,
    Location,
    MaterialPlan,
    NormalizedDocument,
)
from src.model_materials.visual_inventory import (
    InventoryLimits,
    VisualAsset,
    VisualInventory,
    VisualWarning,
)
from src.tools_lecture.cs50_manifest import _unique_json_keys
from src.tools_lecture.execute_cs50 import safe_path


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode()


def strict_json(raw):
    def reject(value):
        raise ValueError(f"Non-finite JSON number: {value}")

    def finite(value):
        result = float(value)
        return result if math.isfinite(result) else reject(value)

    return json.loads(
        raw,
        object_pairs_hook=_unique_json_keys,
        parse_constant=reject,
        parse_float=finite,
    )


def read_bounded(root, path, limit):
    path = safe_path(root, path)
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError("Only regular local input/artifact files are supported")
    with path.open("rb") as stream:
        value = stream.read(limit + 1)
    if len(value) > limit:
        raise ValueError("Local file byte limit exceeded")
    return value


def warning(code, message, *, error=False):
    return VisualWarning(
        code=code, message=message, severity="error" if error else "warning"
    )


def reference_warnings(reference, base_url):
    if not reference or not reference.strip():
        return "unsupported", [
            warning(
                "missing_image_source",
                "Missing/empty image source; no reference inferred",
            )
        ]
    if (
        reference != reference.strip()
        or any(ord(c) < 32 for c in reference)
        or "\\" in reference
    ):
        return "unsupported", [
            warning(
                "unsafe_reference",
                "Control characters, backslash or surrounding whitespace in image reference",
            )
        ]
    if reference.startswith("data:") and not re.fullmatch(
        r"data:image/(?:png|jpeg|gif|webp);base64,[A-Za-z0-9+/=\s]+", reference
    ):
        return "unsupported", [
            warning(
                "unsupported_inline_encoding",
                "Unsupported/malformed inline data reference; never decoded",
            )
        ]
    if reference == "inline:raster" or reference.startswith("data:"):
        return "reference_only", [
            warning(
                "inline_reference_only",
                "Inline source retained; inventory does not decode or publish image bytes",
            )
        ]
    try:
        target = urlsplit(urljoin(base_url, reference))
        if (
            target.scheme not in {"https", "http"}
            or not target.hostname
            or target.username is not None
            or target.password is not None
        ):
            raise ValueError("Disallowed image URL")
    except ValueError:
        return "unsupported", [
            warning(
                "unsafe_reference",
                "Non-HTTP(S), credential-bearing or invalid image reference; never dereferenced",
            )
        ]
    return "reference_only", []


def nearby(left, right):
    return (
        left is not None
        and right is not None
        and len(left) == len(right)
        and all(abs(a - b) <= 0.01 for a, b in zip(left, right, strict=True))
    )


def inventory(
    normalized_path,
    *,
    input_root,
    raw_path=None,
    artifact_root=None,
    receipt_path=None,
    plan_path=None,
    limits=None,
):
    limits = limits or InventoryLimits()
    root = Path(input_root).absolute()
    normalized_path = safe_path(root, Path(normalized_path).absolute())
    artifact_root = (
        Path(artifact_root).absolute() if artifact_root else normalized_path.parent
    )
    safe_path(root, artifact_root / ".visual-path-check")
    encoded = read_bounded(root, normalized_path, limits.max_bytes)
    value = strict_json(encoded)
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != 1
        or not isinstance(value.get("binding"), dict)
        or value["binding"].get("schema_version") != 1
        or not isinstance(value.get("parser"), dict)
        or "version" not in value["parser"]
    ):
        raise ValueError(
            "Explicit normalized/binding schema_version and parser.version required"
        )
    document = NormalizedDocument.model_validate_json(encoded, strict=True)
    if len(document.images) > limits.max_assets:
        raise ValueError("Normalized visual occurrence limit exceeded")
    inputs = {"normalized": str(normalized_path), "artifact_root": str(artifact_root)}
    warnings, assets = [], []
    observed_raw = None
    observations = []
    raw_scan = "not_supplied"
    backend = {}
    binding_verification = "declared"
    if plan_path:
        plan_path = safe_path(root, Path(plan_path).absolute())
        inputs["plan"] = str(plan_path)
        try:
            plan = MaterialPlan.model_validate(
                strict_json(read_bounded(root, plan_path, limits.max_bytes))
            )
            matches = [
                b
                for b in plan.materials
                if b.material_id == document.binding.material_id
            ]
            if matches != [document.binding]:
                raise ValueError(
                    "Material/course/lecture binding contradicts validated discovery graph"
                )
            binding_verification = "plan_verified"
        except (OSError, ValueError) as error:
            binding_verification = "conflict"
            warnings.append(warning("binding_conflict", str(error), error=True))
    else:
        warnings.append(
            warning(
                "binding_not_independently_verified",
                "Course/section/lecture mapping preserved from normalized binding; no discovery plan supplied",
            )
        )
    if receipt_path:
        receipt_path = safe_path(root, Path(receipt_path).absolute())
        inputs["receipt"] = str(receipt_path)
        try:
            receipt = ArtifactReceipt.model_validate(
                strict_json(read_bounded(root, receipt_path, limits.max_bytes))
            )
            if receipt.status != "completed":
                raise ValueError("Material receipt is not completed")
            if (
                receipt.binding != document.binding
                or receipt.parser != document.parser
                or receipt.raw_sha256 != document.raw_sha256
                or receipt.normalized_sha256 != sha(encoded)
            ):
                raise ValueError(
                    "Receipt metadata/hashes contradict normalized document"
                )
            expected_images = {
                i.artifact_path: i.sha256 for i in document.images if i.artifact_path
            }
            if receipt.image_hashes != expected_images:
                raise ValueError(
                    "Receipt image manifest contradicts normalized document"
                )
            if (
                receipt.normalized_path
                and safe_path(root, root / receipt.normalized_path) != normalized_path
            ):
                raise ValueError(
                    "Receipt normalized path contradicts explicit input root/path"
                )
        except (OSError, ValueError) as error:
            warnings.append(warning("receipt_conflict", str(error), error=True))
    if raw_path:
        raw_path = safe_path(root, Path(raw_path).absolute())
        inputs["raw"] = str(raw_path)
        try:
            raw = read_bounded(root, raw_path, limits.max_bytes)
            observed_raw = sha(raw)
            if observed_raw != document.raw_sha256:
                raise ValueError("Raw SHA-256 contradicts normalized source")
            if document.parser.name not in {"html", "pdf"}:
                raw_scan = "unsupported"
                warnings.append(
                    warning(
                        "unsupported_source", "Raw visual scan supports HTML/PDF only"
                    )
                )
            else:
                from src.tools_materials.parse_pdf import run_worker

                data = run_worker(
                    [
                        sys.executable,
                        "-I",
                        str(Path(__file__).with_name("visual_worker.py")),
                    ],
                    dict(
                        raw=base64.b64encode(raw).decode(),
                        kind=document.parser.name,
                        limits=limits.model_dump(),
                    ),
                    limits.timeout,
                )
                observations = data["observations"]
                backend = data["backend"]
                if (
                    document.parser.name == "pdf"
                    and document.metadata.get("page_count") != data["page_count"]
                ):
                    warnings.append(
                        warning(
                            "page_count_conflict",
                            "PDF page count missing or inconsistent in normalized metadata",
                            error=True,
                        )
                    )
                raw_scan = "complete"
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            raw_scan = "failed"
            warnings.append(warning("raw_scan_failed", str(error), error=True))
    else:
        warnings.append(
            warning(
                "raw_not_supplied",
                "Inventory limited to normalized images; SVG, missing-src and PDF vectors not inspected",
            )
        )
    if not document.binding.lecture_ids:
        warnings.append(
            warning(
                "lecture_binding_absent", "No lecture binding supplied; none inferred"
            )
        )
    for text in document.warnings:
        warnings.append(warning("parser_warning", text))
    # A shared artifact may be used by many distinct occurrences. Read once, but
    # compare each occurrence's independently declared hash against actual bytes.
    cache, spent, consumed = {}, 0, set()
    for image in document.images:
        own = []
        observed = None
        artifact_status = "not_declared"
        extraction_status = "reference_only"
        blocks = tuple(
            b.block_id
            for b in document.blocks
            if b.type == "image_reference" and b.data.get("image_id") == image.image_id
        )
        if not blocks:
            own.append(
                warning(
                    "unreferenced_image",
                    "Normalized image has no image_reference block",
                )
            )
        source_reference = next(
            (
                b.data.get("source_reference")
                for b in document.blocks
                if b.block_id in blocks
            ),
            image.original_url,
        )
        match = None
        for index, observation in enumerate(observations):
            if index in consumed:
                continue
            location = observation["location"]
            same_dom = (
                observation["tag"] == "img"
                and image.source_location.dom
                and location.get("dom") == image.source_location.dom
            )
            same_pdf = (
                observation["tag"] == "pdf_image"
                and location.get("page") == image.source_location.page
                and nearby(location.get("bbox"), image.source_location.bbox)
            )
            if same_dom or same_pdf:
                match = observation
                consumed.add(index)
                source_reference = match.get("reference") or source_reference
                break
        if raw_scan == "complete" and match is None and document.parser.name == "pdf":
            # PDF-v2 can enumerate the same xref repeatedly and then emit all its
            # rectangles for every resource entry. Only alias when a verified raw
            # occurrence already exists AND the complete normalized record agrees.
            alias_found = False
            for asset_index, previous in enumerate(assets):
                if (
                    previous.image
                    and previous.context.get("raw_occurrence_token")
                    and previous.image.model_dump(exclude={"image_id"})
                    == image.model_dump(exclude={"image_id"})
                ):
                    assets[asset_index] = previous.model_copy(
                        update=dict(
                            image_aliases=(*previous.image_aliases, image),
                            block_ids=(*previous.block_ids, *blocks),
                            warnings=(
                                *previous.warnings,
                                warning(
                                    "duplicate_normalized_image_reference",
                                    "Verified PDF occurrence has duplicate normalized records; all original image/block identities retained as aliases",
                                ),
                            ),
                        )
                    )
                    if any(
                        b.location != image.source_location
                        for b in document.blocks
                        if b.block_id in blocks
                    ):
                        assets[asset_index] = assets[asset_index].model_copy(
                            update=dict(
                                review_status="uncertain",
                                warnings=(
                                    *assets[asset_index].warnings,
                                    warning(
                                        "image_location_conflict",
                                        "Aliased image block location contradicts its image record",
                                        error=True,
                                    ),
                                ),
                            )
                        )
                    alias_found = True
                    break
            if alias_found:
                continue
        if raw_scan == "complete" and match is None:
            own.append(
                warning(
                    "source_position_unmatched",
                    "Normalized image position absent from raw visual observations",
                    error=True,
                )
            )
        if match and document.parser.name == "html":
            _, reference_issues = reference_warnings(
                match.get("reference"), document.binding.original_url
            )
            own.extend(reference_issues)
            if (
                image.original_url
                and match.get("reference")
                and not str(match["reference"]).startswith("data:")
                and urljoin(document.binding.original_url, match["reference"])
                != image.original_url
            ):
                own.append(
                    warning(
                        "image_reference_conflict",
                        "Normalized image URL contradicts original DOM reference",
                        error=True,
                    )
                )
        for block in document.blocks:
            if block.block_id in blocks and block.location != image.source_location:
                own.append(
                    warning(
                        "image_location_conflict",
                        "Image block location contradicts its image record",
                        error=True,
                    )
                )
        if image.artifact_path:
            try:
                local = safe_path(artifact_root, artifact_root / image.artifact_path)
                if image.artifact_path not in cache:
                    content = read_bounded(
                        artifact_root, local, limits.max_bytes - spent
                    )
                    if not content:
                        raise ValueError("Empty local image artifact")
                    spent += len(content)
                    cache[image.artifact_path] = sha(content)
                observed = cache[image.artifact_path]
                artifact_status = (
                    "verified"
                    if image.sha256 == observed
                    else "hash_mismatch"
                    if image.sha256
                    else "unverified"
                )
                extraction_status = (
                    "available" if artifact_status == "verified" else "uncertain"
                )
                if artifact_status != "verified":
                    own.append(
                        warning(
                            "artifact_hash_unverified",
                            "Observed bytes do not match a declared image hash",
                            error=True,
                        )
                    )
            except FileNotFoundError:
                artifact_status = "missing"
                own.append(
                    warning(
                        "missing_image_bytes",
                        "Declared local image artifact is missing; reference retained",
                    )
                )
            except (OSError, ValueError) as error:
                artifact_status = (
                    "limit_exceeded" if "limit" in str(error) else "unsafe"
                )
                extraction_status = "uncertain"
                own.append(warning("artifact_unavailable", str(error), error=True))
        elif source_reference:
            extraction_status, issues = reference_warnings(
                source_reference, document.binding.original_url
            )
            own.extend(issues)
        else:
            own.append(
                warning(
                    "missing_image_bytes",
                    "Normalized image has neither local bytes nor a resolvable original source",
                )
            )
        context = dict(match.get("context", {})) if match else {}
        if match:
            context["raw_occurrence_token"] = match["token"]
        if match and match.get("caption"):
            context["caption"] = match["caption"]
        assets.append(
            VisualAsset(
                asset_id=deterministic_id(
                    "visual_asset", document.document_id, "image:" + image.image_id
                ),
                document_id=document.document_id,
                material_id=document.binding.material_id,
                asset_type="raster_image"
                if image.artifact_path or document.parser.name == "pdf"
                else "external_image_reference",
                location=image.source_location,
                original_reference=source_reference,
                image=image,
                block_ids=blocks,
                artifact_status=artifact_status,
                observed_sha256=observed,
                extraction_status=extraction_status,
                review_status="uncertain"
                if any(w.severity == "error" for w in own)
                else "requires_visual_review",
                context=context,
                warnings=tuple(own),
            )
        )
    for index, observation in enumerate(observations):
        if index in consumed:
            continue
        if len(assets) >= limits.max_assets:
            raw_scan = "failed"
            warnings.append(
                warning(
                    "asset_limit_exceeded",
                    "Combined normalized/raw occurrence limit exceeded; raw coverage incomplete",
                    error=True,
                )
            )
            break
        tag, context = observation["tag"], observation["context"]
        own = [
            warning(
                "not_in_normalized_images",
                "Raw-source visual observation supplements the unchanged normalized document",
            )
        ]
        extraction_status = "reference_only"
        if tag == "pdf_vectors":
            kind = "vector_graphics_candidate"
            own.append(
                warning(
                    "geometric_candidate_only",
                    "Spatially grouped drawing paths; no diagram/math/decorative semantics determined",
                )
            )
        elif tag == "svg":
            kind = "inline_svg"
            own.append(
                warning(
                    "svg_not_rendered",
                    "Inline SVG markup position retained; no rasterization or standalone artifact created",
                )
            )
            for reference in context.get("svg_references", ()):
                _, issues = (
                    reference_warnings(reference, document.binding.original_url)
                    if not reference.startswith("#")
                    else (None, [])
                )
                own.extend(issues)
            if context.get("active_svg"):
                own.append(
                    warning(
                        "active_svg_not_executed",
                        "SVG contains script/foreignObject; neither executed nor rendered",
                    )
                )
        elif tag == "pdf_image":
            kind = "raster_image"
            own.append(
                warning(
                    "missing_image_bytes",
                    "PDF image occurrence has no normalized artifact; inventory performs no extraction",
                )
            )
        else:
            kind = (
                "external_image_reference"
                if observation.get("reference")
                else "unknown_visual"
            )
            extraction_status, issues = reference_warnings(
                observation.get("reference"), document.binding.original_url
            )
            own.extend(issues)
            if context.get("srcset"):
                own.append(
                    warning(
                        "srcset_not_selected",
                        "Responsive image selection is not evaluated; original srcset retained",
                    )
                )
        location = Location.model_validate(observation["location"])
        assets.append(
            VisualAsset(
                asset_id=deterministic_id(
                    "visual_asset", document.document_id, observation["token"]
                ),
                document_id=document.document_id,
                material_id=document.binding.material_id,
                asset_type=kind,
                location=location,
                original_reference=observation.get("reference"),
                extraction_status=extraction_status,
                review_status="requires_visual_review",
                context=context,
                warnings=tuple(own),
            )
        )
    for idx, asset in enumerate(assets):
        extra = []
        width, height = asset.context.get("width", 0), asset.context.get("height", 0)
        if width * height > limits.max_image_pixels:
            extra.append(
                warning(
                    "image_pixel_limit",
                    "Declared image dimensions exceed review limit; no pixels decoded",
                )
            )
        bounds, bbox = asset.context.get("page_bounds"), asset.location.bbox
        if (
            bbox
            and bounds
            and (
                bbox[0] < bounds[0]
                or bbox[1] < bounds[1]
                or bbox[2] > bounds[2]
                or bbox[3] > bounds[3]
            )
        ):
            extra.append(
                warning(
                    "outside_page_bounds",
                    "Source geometry extends beyond page; preserved without clipping",
                )
            )
        if not asset.location.dom and asset.location.page is None:
            extra.append(
                warning(
                    "missing_source_position",
                    "Neither DOM nor page location available",
                    error=True,
                )
            )
        if extra:
            assets[idx] = asset.model_copy(
                update=dict(warnings=(*asset.warnings, *extra))
            )
    all_warnings = [*warnings, *(w for a in assets for w in a.warnings)]
    counts = dict(
        assets=len(assets),
        normalized_image_aliases=sum(len(a.image_aliases) for a in assets),
        available_artifacts=sum(a.artifact_status == "verified" for a in assets),
        unique_artifacts=len(
            {
                a.image.artifact_path
                for a in assets
                if a.image and a.artifact_status == "verified"
            }
        ),
        reference_only=sum(a.extraction_status == "reference_only" for a in assets),
        review_candidates=len(assets),
        warnings=sum(w.severity == "warning" for w in all_warnings),
        errors=sum(w.severity == "error" for w in all_warnings),
    )
    payload = dict(
        schema_version=1,
        inventory_version="visual_inventory_v1",
        document_id=document.document_id,
        binding=document.binding.model_dump(mode="json"),
        parser=document.parser.model_dump(mode="json"),
        raw_sha256=document.raw_sha256,
        observed_raw_sha256=observed_raw,
        normalized_sha256=sha(encoded),
        inputs=inputs,
        limits=limits.model_dump(mode="json"),
        raw_scan=raw_scan,
        scan_backend=backend,
        binding_verification=binding_verification,
        assets=[a.model_dump(mode="json") for a in assets],
        warnings=[w.model_dump(mode="json") for w in warnings],
        counts=counts,
        by_type=dict(Counter(a.asset_type for a in assets)),
        by_page=dict(
            Counter(
                str(a.location.page) if a.location.page else "dom_or_unknown"
                for a in assets
            )
        ),
    )
    return VisualInventory(**payload, report_sha256=sha(json_bytes(payload)))


def markdown(report):
    def escape(value):
        # Reports may contain untrusted captions/URLs; never emit their markup.
        return (
            str(value)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("|", "&#124;")
            .replace("\n", " ")
            .replace("\r", " ")
        )

    lines = [
        "# Visual inventory v1",
        "",
        f"Document: {report.document_id}",
        f"Course: {report.binding.resource.course_id}; lectures: {escape(', '.join(report.binding.lecture_ids) or '(unbound)')}",
        f"Material: {report.binding.material_id}",
        f"Raw SHA-256: {report.raw_sha256}",
        f"Raw scan: {report.raw_scan}; assets: {len(report.assets)}; verified local occurrences: {report.counts['available_artifacts']}; reference only: {report.counts['reference_only']}; possible review cases: {report.counts['review_candidates']}",
        "",
        "Technical observations only; no OCR, diagram interpretation or mathematical verification.",
        "",
        "| Type | Count |",
        "| --- | ---: |",
        *[f"| {kind} | {count} |" for kind, count in sorted(report.by_type.items())],
        "",
        "| Page | Count |",
        "| --- | ---: |",
        *[f"| {page} | {count} |" for page, count in sorted(report.by_page.items())],
        "",
        "| Asset | Position | Type | Extraction | Artifact |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines.extend(
        f"| {a.asset_id} | {escape(a.location.model_dump(exclude_none=True))} | {a.asset_type} | {a.extraction_status} | {a.artifact_status} |"
        for a in report.assets[:50]
    )
    if len(report.assets) > 50:
        lines.append(
            "Additional assets omitted from Markdown; full inventory is in JSON."
        )
    lines.extend(["", "## Findings", ""])
    findings = [
        f"- {w.severity} {w.code}: {escape(w.message)}" for w in report.warnings
    ]
    for asset in report.assets:
        findings.extend(
            f"- {asset.asset_id} {escape(asset.location.model_dump(exclude_none=True))}: {w.severity} {w.code}: {escape(w.message)}"
            for w in asset.warnings
        )
    lines.extend(findings[:50])
    if len(findings) > 50:
        lines.append(
            "Additional findings omitted from Markdown; all findings remain in JSON."
        )
    return "\n".join(lines) + "\n"
