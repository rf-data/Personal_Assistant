"""C08 local-only adapter over reviewed parsers. No C16, queues, RAG or downloads.

Production execution remains gated on a reviewed host network/resource sandbox.
Synthetic executions exercise the identical parsing/receipt path offline.
"""

import hashlib
import json
import time
from pathlib import Path

from src.job_control.catalog import read_file
from src.job_control.models import fingerprint
from src.model_materials.materials import NormalizedDocument, ParserConfig
from src.model_transcribe.data_transcribe import TranscriptDocument
from src.tools_materials.capacity import check_capacity
from src.tools_materials.storage import artifact_root, locate, locked, publish_bytes
from src.tools_materials.week_acquisition import (
    CONTAINERS,
    SUCCESS,
    binding,
    verify_row,
)

VERSION = "c26-cs50p-08-v1"
MAX_OUTPUT = 16 * 1024**2


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def revision():
    names = [
        "week_processing.py",
        "parse_html.py",
        "parse_pdf.py",
        "pdf_worker.py",
        "parse_code.py",
        "code_structure.py",
        "code_zip.py",
        "text_validation.py",
    ]
    base = Path(__file__).parent
    files = [base / name for name in names] + [
        base.parent / "tools_transcribe/import_transcript.py",
        base.parent / "model_transcribe/data_transcribe.py",
        base.parent / "model_materials/materials.py",
        base / "source_acquisition.py",
    ]
    return fingerprint(
        {str(p.relative_to(base.parent)): sha(read_file(p)) for p in files}
    )


def required_rows(inventory):
    return [
        r
        for r in inventory.materials
        if r.material_type not in CONTAINERS
        and (
            r.required
            or r.material_id in inventory.expected_ids
            or (r.selected and r.alternative_group)
        )
    ]


def route(row):
    if row.material_type in {"audio", "video", "reference"}:
        return None
    if row.source_format == "zip" and row.material_type == "source_code":
        return "static_zip"
    if row.material_type in {"transcript", "subtitles"} and row.source_format in {
        "txt",
        "srt",
        "vtt",
    }:
        return "transcript"
    if row.source_format in {"html", "pdf"}:
        return row.source_format
    from src.tools_materials.parse_code import LANGUAGES

    if row.source_format in LANGUAGES:
        return "code"
    return None


def config(row):
    name = route(row)
    return (
        ParserConfig(
            name=name,
            version="2" if name in {"html", "pdf"} else "1",
            max_bytes=8 * 1024**2 if name == "pdf" else 2 * 1024**2,
            max_pages=20,
            max_blocks=1000,
            max_images=100,
            timeout=20,
            memory_mb=512,
        )
        if name in {"html", "pdf", "code"}
        else None
    )


def key(row, inventory):
    return fingerprint(
        dict(
            version=VERSION,
            parser_revision=revision(),
            binding=binding(row, inventory).model_dump(mode="json"),
            material_id=row.material_id,
            parent=row.parent_material_id,
            raw_sha256=row.sha256,
            route=route(row),
            config=config(row).model_dump(mode="json") if config(row) else None,
        )
    )


def folder(row, inventory, output):
    return locate(
        Path(output), row.material_id.split(":")[1] + "/" + key(row, inventory)
    )


def _static(raw, fmt):
    import io
    import tokenize

    from src.tools_materials.code_structure import inspect_structure

    result = {"format": fmt, "bytes": len(raw), "sha256": sha(raw)}
    if fmt == "py":
        structure = inspect_structure(raw)
        if structure["status"] != "parsed":
            raise ValueError("Python structure is uncertain: " + structure["status"])
        comments = [
            dict(text=t.string, line=t.start[0])
            for t in tokenize.tokenize(io.BytesIO(raw).readline)
            if t.type == tokenize.COMMENT
        ]
        result.update(structure=structure, comments=comments)
    return result


def parse(row, inventory, archive):
    """Read only verified bounded bytes; returned data is never executed."""
    raw_path = locate(Path(archive), row.expected_local_path)
    raw = read_file(raw_path, inventory.limits.ceiling(row))
    b, selected, cfg = binding(row, inventory), route(row), config(row)
    blobs = {}
    if selected in {"html", "pdf", "code"}:
        if selected == "html":
            from src.tools_materials.parse_html import parse_html as parser
        elif selected == "pdf":
            from src.tools_materials.parse_pdf import parse_pdf as parser
        else:
            from src.tools_materials.parse_code import parse_code as parser
        document, blobs = parser(b, raw, cfg)
        if not any(
            block.text.strip() or block.type == "image_reference"
            for block in document.blocks
        ):
            raise ValueError("Parser produced no usable content")
        payload = dict(
            kind="normalized_document", document=document.model_dump(mode="json")
        )
        if selected == "code":
            payload["static"] = _static(raw, row.source_format)
    elif selected == "transcript":
        from src.tools_transcribe.import_transcript import import_transcript

        document = import_transcript(
            raw_path,
            language=b.language or "en",
            original_url=b.original_url,
            format=b.format,
        )
        document.source = row.expected_local_path
        document.provenance.source_file = row.expected_local_path
        payload = dict(kind="transcript", document=document.model_dump(mode="json"))
    elif selected == "static_zip":
        from src.tools_materials.code_zip import inspect_zip
        from src.tools_materials.parse_code import LANGUAGES, parse_code

        members, supported = [], 0
        for metadata, content in inspect_zip(raw):
            entry = dict(metadata)
            if content is not None:
                fmt = Path(metadata["name"]).suffix.lstrip(".").lower()
                # Preserve all member metadata; unsupported executable/nested content blocks success.
                if (
                    metadata["status"] not in {"candidate_python", "excluded_type"}
                    or fmt not in LANGUAGES
                ):
                    raise ValueError("ZIP member requires review: " + metadata["name"])
                member_binding = b.model_copy(update={"format": fmt})
                doc, _ = parse_code(
                    member_binding,
                    content,
                    ParserConfig(name="code", max_bytes=1048576),
                )
                doc = doc.model_copy(
                    update={
                        "metadata": {
                            **doc.metadata,
                            "source_path": metadata["name"],
                            "archive_url": row.source_url,
                        }
                    }
                )
                entry.update(
                    document=doc.model_dump(mode="json"), static=_static(content, fmt)
                )
                supported += 1
            members.append(entry)
        if not supported:
            raise ValueError("ZIP contains no supported source members")
        payload = dict(kind="source_archive", members=members, extracted_to_disk=False)
    else:
        raise ValueError("No reviewed isolated processing route")
    payload.update(
        version=VERSION,
        material_id=row.material_id,
        parent_material_id=row.parent_material_id,
        section_id=row.section_id,
        source_url=row.source_url,
        raw_sha256=row.sha256,
        acquisition_strategy=row.acquisition_strategy,
        related_material_ids=[
            r.material_id
            for r in inventory.materials
            if r.parent_material_id == row.parent_material_id
        ],
    )
    return payload, blobs


def inspect(row, inventory, archive, output):
    """Never trust status labels, malformed records or output existence alone."""
    try:
        return _inspect(row, inventory, archive, output)
    except (TypeError, KeyError, AttributeError) as error:
        raise ValueError("Malformed processing evidence") from error


def _inspect(row, inventory, archive, output):
    checked = verify_row(row, inventory, Path(archive))
    if (checked.sha256, checked.file_size, checked.receipt_id) != (
        row.sha256,
        row.file_size,
        row.receipt_id,
    ):
        raise ValueError("Processing raw evidence differs from inventory")
    root = folder(row, inventory, output)
    from src.tools_materials.quality import _json

    receipt = _json(read_file(locate(root, "receipt.json"), 65536))
    if (receipt.get("key"), receipt.get("version"), receipt.get("raw_sha256")) != (
        key(row, inventory),
        VERSION,
        row.sha256,
    ):
        raise ValueError("Processing receipt binding mismatch")
    if receipt.get("status") != "COMPLETED":
        raise ValueError(receipt.get("reason", "Processing incomplete"))
    for name, digest in receipt["outputs"].items():
        if sha(read_file(locate(root, name), MAX_OUTPUT)) != digest:
            raise ValueError("Processing artifact hash mismatch")
    if "result.json" not in receipt["outputs"]:
        raise ValueError("Processing result missing")
    result = _json(read_file(locate(root, "result.json"), MAX_OUTPUT))
    if (
        result["material_id"],
        result["raw_sha256"],
        result["source_url"],
        result["version"],
    ) != (row.material_id, row.sha256, row.source_url, VERSION):
        raise ValueError("Processing result provenance mismatch")
    if result["kind"] == "normalized_document":
        document = NormalizedDocument.model_validate(result["document"])
        if (
            document.raw_sha256 != row.sha256
            or document.binding != binding(row, inventory)
            or document.parser != config(row)
        ):
            raise ValueError("Normalized provenance mismatch")
    elif result["kind"] == "transcript":
        document = TranscriptDocument.model_validate(result["document"])
        if (
            not document.text.strip()
            or not document.segments
            or str(document.provenance.source_url) != row.source_url
        ):
            raise ValueError("Transcript result invalid")
    elif result["kind"] == "source_archive" and route(row) == "static_zip":
        from src.tools_materials.code_zip import inspect_zip

        actual = inspect_zip(
            read_file(
                locate(Path(archive), row.expected_local_path),
                inventory.limits.ceiling(row),
            )
        )
        if len(actual) != len(result.get("members", [])):
            raise ValueError("Source archive processing membership mismatch")
        for (metadata, content), member in zip(actual, result["members"], strict=True):
            if any(member.get(k) != v for k, v in metadata.items()):
                raise ValueError("Source member provenance mismatch")
            if content is not None:
                document = NormalizedDocument.model_validate(member["document"])
                if (
                    document.raw_sha256 != sha(content)
                    or document.binding.original_url != row.source_url
                ):
                    raise ValueError("Source member raw hash mismatch")
    else:
        raise ValueError("Unsupported or empty processing output")
    return receipt


def plan(inventory):
    return dict(
        version=VERSION,
        parser_revision=revision(),
        c16_enabled=False,
        production_execution="BLOCKED: host network/resource isolation and installation gates require review",
        materials=[
            dict(
                material_id=r.material_id,
                route=route(r),
                status="PENDING"
                if r.acquisition_status in SUCCESS and route(r)
                else "BLOCKED",
                next_action="Review isolated local processing"
                if route(r)
                else "Provide reviewed offline adapter",
            )
            for r in required_rows(inventory)
        ],
    )


def process(inventory, archive, output, *, offline_test=False):
    if not offline_test or inventory.source_origin != "synthetic":
        raise PermissionError(
            "BLOCKED: production processing requires separately reviewed host isolation gate"
        )
    archive, output = artifact_root(archive), artifact_root(output)
    if (
        archive == output
        or archive.is_relative_to(output)
        or output.is_relative_to(archive)
    ):
        raise ValueError("Separate acquisition and processing roots required")
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    records, started = [], time.monotonic()
    with locked(output):
        for row in required_rows(inventory):
            record = dict(material_id=row.material_id, status="FAILED", reason=None)
            try:
                if time.monotonic() - started > inventory.limits.wall_seconds:
                    raise ValueError("Processing wall budget exceeded")
                if row.acquisition_status not in SUCCESS:
                    raise ValueError("Verified acquisition required before processing")
                checked = verify_row(row, inventory, archive)
                if (checked.sha256, checked.file_size, checked.receipt_id) != (
                    row.sha256,
                    row.file_size,
                    row.receipt_id,
                ):
                    raise ValueError("Raw inventory/receipt mismatch")
                target = folder(row, inventory, output)
                if locate(target, "receipt.json").exists():
                    inspect(row, inventory, archive, output)
                    record.update(status="COMPLETED", reused=True)
                else:
                    result, blobs = parse(row, inventory, archive)
                    data = (
                        json.dumps(result, indent=2, ensure_ascii=False) + "\n"
                    ).encode()
                    outputs = {**blobs, "result.json": data}
                    required = sum(len(b) for b in outputs.values())
                    if required > MAX_OUTPUT:
                        raise ValueError("Processing output budget exceeded")
                    check_capacity(
                        output,
                        inventory.limits.report_bytes,
                        inventory.limits.reserve_bytes,
                        required + 65536,
                    )
                    hashes = {name: sha(data) for name, data in outputs.items()}
                    # Resume after publication interruption: validate every existing byte, never overwrite.
                    for name, data in outputs.items():
                        path = locate(target, name)
                        if path.exists():
                            if sha(read_file(path, MAX_OUTPUT)) != hashes[name]:
                                raise ValueError(
                                    "Existing processing artifact conflicts"
                                )
                        else:
                            publish_bytes(path, data)
                    receipt = dict(
                        version=VERSION,
                        key=key(row, inventory),
                        raw_sha256=row.sha256,
                        parser_revision=revision(),
                        status="COMPLETED",
                        outputs=hashes,
                    )
                    publish_bytes(
                        locate(target, "receipt.json"),
                        (json.dumps(receipt, indent=2) + "\n").encode(),
                    )
                    inspect(row, inventory, archive, output)
                    record.update(status="COMPLETED", reused=False)
            except (ValueError, OSError, RuntimeError, KeyError) as error:
                record["reason"] = f"{type(error).__name__}: {error}"
            records.append(record)
    return dict(
        version=VERSION, materials=records, c26_status="HOLD", c16_enabled=False
    )
