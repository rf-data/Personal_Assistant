"""Deliberate metadata allowlists. Internal payloads remain byte-identical."""

import re
from collections import Counter
from urllib.parse import quote, urlsplit

from src.content_store.models import ContentBlock, canonical, sha256
from src.content_store.read_models import BlockDTO, LocatorDTO, RawDTO, WarningDTO


def route(*parts):
    return "/v1/content/" + "/".join(quote(str(p), safe="") for p in parts)


def public_url(value):
    if not isinstance(value, str) or not value:
        return None
    try:
        url = urlsplit(value)
    except ValueError:
        return None
    if (
        url.scheme not in {"http", "https"}
        or not url.hostname
        or url.username
        or url.password
        or url.query
        or url.fragment
        or any(ord(c) < 32 for c in value)
        or len(value) > 4096
    ):
        return None
    return value


def label(value):
    if not isinstance(value, str) or len(value) > 2000:
        return None
    if re.search(
        r"(?:^[/\\~]|file:|[A-Za-z]:\\|/(?:home|tmp|private|var|etc)/|[\x00-\x1f])",
        value,
    ):
        return None
    return value


def raw_view(version, ref):
    return RawDTO(
        source_id=version.source_id,
        source_version_id=version.source_version_id,
        role=ref.role,
        ordinal=ref.ordinal,
        sha256=ref.sha256,
        size_bytes=ref.size_bytes,
        download_route=route(
            "sources",
            version.source_id,
            "versions",
            version.source_version_id,
            "raw",
            ref.role,
            ref.ordinal,
        ),
    )


def locators(block, version):
    refs = {r.sha256: raw_view(version, r) for r in version.manifest.artifacts}
    output = []
    for locator in block.locators:
        value = locator.model_dump(mode="json")
        value["dom"] = label(value["dom"])
        value["coordinate_system"] = label(value["coordinate_system"]) or "unknown"
        value["chapter_path"] = [
            p for p in value["chapter_path"] if label(p) is not None
        ]
        # B adapters generate these pointers, never host paths.
        if not re.fullmatch(r"/(?:blocks|segments)/\d+", value["origin_pointer"]):
            value["origin_pointer"] = block.payload_pointer
        output.append(
            LocatorDTO(**value, raw_reference=refs[locator.raw_artifact_sha256])
        )
    return tuple(output)


def block_view(block: ContentBlock, parsed, version, quality):
    locations = locators(block, version)
    external = (
        len(canonical([p.model_dump(mode="json") for p in locations])) > 32 * 1024
    )
    base = ("parsed", parsed.parsed_version_id, "blocks", block.block_id)
    return BlockDTO(
        parsed_version_id=parsed.parsed_version_id,
        block_id=block.block_id,
        order=block.order,
        type=block.type,
        original_type=label(block.original_type) or "unknown",
        aggregation_role=block.aggregation_role,
        quality_status=parsed.quality_status,
        warnings=warnings(quality, block.block_id),
        text=block.text if len(block.text) <= 2048 else None,
        text_length=len(block.text),
        text_sha256=block.text_sha256,
        text_route=route(*base, "text"),
        structure_route=route(*base, "structure"),
        locators=None if external else locations,
        locators_in_structure=external,
    )


def structure(block):
    source, result = block.data, {}
    boxes = source.get("line_bboxes")
    if isinstance(boxes, list) and all(
        isinstance(b, list) and len(b) == 4 and all(type(n) in (float, int) for n in b)
        for b in boxes
    ):
        result["line_bboxes"] = boxes
    classification = source.get("classification")
    if (
        isinstance(classification, dict)
        and classification.get("strategy") == "python_math_v2"
    ):
        result["classification"] = {"strategy": "python_math_v2"}
        if isinstance(classification.get("signals"), list) and all(
            isinstance(s, str) and re.fullmatch(r"[a-z_]{1,64}", s)
            for s in classification["signals"]
        ):
            result["classification"]["signals"] = classification["signals"]
        for key in ("monospace_ratio", "python_syntax_valid"):
            if type(classification.get(key)) in (float, int, bool):
                result["classification"][key] = classification[key]
    # Text-bearing values here are content, not arbitrary metadata containers.
    if block.type == "table" and isinstance(source.get("rows"), list):
        rows = source["rows"]
        if all(
            isinstance(row, list)
            and all(cell is None or isinstance(cell, (str, int, float)) for cell in row)
            for row in rows
        ):
            result["rows"] = rows
    if block.type == "code":
        for key in ("language", "line_number_strategy"):
            if (
                key in source
                and isinstance(source[key], str)
                and re.fullmatch(r"[A-Za-z0-9_+.-]{1,100}", source[key])
            ):
                result[key] = source[key]
        if isinstance(source.get("code_view"), str):
            result["code_view"] = source["code_view"]
        lines = source.get("line_numbers")
        if isinstance(lines, list) and all(
            isinstance(v, dict)
            and set(v) == {"line_index", "number", "prefix"}
            and type(v["line_index"]) is int
            and type(v["number"]) is int
            and isinstance(v["prefix"], str)
            and re.fullmatch(r"[ \t]*\d+[ \t]+", v["prefix"])
            for v in lines
        ):
            result["line_numbers"] = lines
    if block.type == "formula" and isinstance(source.get("latex"), str):
        result["latex"] = source["latex"]
    if block.type == "image_reference" and label(source.get("image_id")):
        result["image_id"] = source["image_id"]
    if block.type == "heading" and type(source.get("level")) is int:
        result["level"] = source["level"]
    if block.type == "list":
        for key in ("ordered", "reversed"):
            if type(source.get(key)) is bool:
                result[key] = source[key]
        if source.get("start") is None or isinstance(source.get("start"), (int, str)):
            if source.get("start") is None or str(source["start"]).isdigit():
                result["start"] = source.get("start")
    if source.get("content_role") == "table_of_contents":
        result["content_role"] = "table_of_contents"
    if block.type == "link":
        for key in ("url", "href"):
            if public_url(source.get(key)):
                result[key] = source[key]
    return result, result != source


def warnings(value, block_id=None):
    counts = Counter(
        (f.get("code"), f.get("severity"), f.get("category"))
        for f in value.get("findings", [])
        if isinstance(f, dict)
        and (block_id is None or f.get("block_id") in {None, block_id})
        and re.fullmatch(r"[a-z][a-z0-9_]{0,95}", str(f.get("code")))
        and f.get("severity") in {"warning", "info"}
        and f.get("category") in {"technical", "semantic_review"}
    )
    return tuple(
        WarningDTO(code=k[0], severity=k[1], category=k[2], occurrences=n)
        for k, n in sorted(counts.items())
    )


def structure_hash(data, locations):
    return sha256(
        canonical(
            dict(data=data, locators=[p.model_dump(mode="json") for p in locations])
        )
    )
