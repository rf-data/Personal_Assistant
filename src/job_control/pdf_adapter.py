"""Approved receipt workspace -> private PDF-v2 workspace, using existing runners."""

import hashlib
from pathlib import PurePosixPath

from src.job_control.catalog import safe_path, verified_files
from src.model_materials.materials import ArtifactReceipt, ParserConfig
from src.tools_materials.processing import MaterialProcessor, parser_for
from src.tools_materials.storage import publish_bytes, save_model

PDF_CONFIG = ParserConfig(
    name="pdf",
    version="2",
    max_bytes=1024 * 1024,
    max_pages=20,
    max_blocks=2000,
    max_images=20,
    timeout=10,
    memory_mb=512,
)


def prepare(entry, course, files=None):
    """Read-only validation; the catalog must include every receipt artifact."""
    files = verified_files(entry) if files is None else files
    receipt = ArtifactReceipt.model_validate_json(files[entry.roles["receipt"]])
    binding = receipt.binding
    mid = binding.material_id.split(":")[1]
    selected, _, _ = parser_for(binding)
    if (
        selected is None
        or selected.name != "pdf"
        or selected.version != "2"
        or binding.resource.course_id != course
        or course not in entry.course_ids
        or entry.roles
        != {"raw": f"{mid}/raw/source", "receipt": f"{mid}/receipt.v1.json"}
        or receipt.raw_sha256 != hashlib.sha256(files[entry.roles["raw"]]).hexdigest()
        or not files[entry.roles["raw"]].startswith(b"%PDF-")
        or len(files[entry.roles["raw"]]) > PDF_CONFIG.max_bytes
    ):
        raise ValueError("Approved PDF-v2 binding/raw receipt mismatch")
    expected = set(entry.roles.values())
    if receipt.status == "completed":
        if not receipt.normalized_path:
            raise ValueError("Completed receipt requires normalized artifact")
        expected.add(receipt.normalized_path)
        expected.update(
            str(PurePosixPath(receipt.normalized_path).parent / name)
            for name in receipt.image_hashes
        )
    elif receipt.status != "verified" or receipt.parser is not None:
        raise ValueError("Only verified inputs or complete validated outputs accepted")
    if expected != set(files):
        raise ValueError("PDF bundle must declare exactly the receipt artifacts")
    processor = MaterialProcessor(entry.root)
    # Existing inspectors verify hashes, schema, parser config and image provenance.
    if receipt.status == "completed":
        processor.inspect(binding, PDF_CONFIG)
    else:
        processor.downloader.validate(binding)
    return receipt


def run(entry, job, results, output):
    files = verified_files(entry)
    receipt = prepare(entry, job.parameters["course_id"], files)
    workspace = results / "materials"
    for name, data in files.items():
        publish_bytes(safe_path(workspace, name), data)
    completed = MaterialProcessor(workspace).parse(
        receipt.binding, execute=True, config=PDF_CONFIG
    )
    save_model(output, completed)
