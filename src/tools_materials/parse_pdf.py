"""PyMuPDF text/images in a killable CPU/address-space/page/output bounded worker."""

import base64
import json
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

from src.model_discovery.cs50 import deterministic_id
from src.model_materials.materials import ImageArtifact, ParserConfig
from src.tools_materials.parse_html import build_document, check_input


def run_worker(command, request, timeout):
    with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=output,
            stderr=errors,
            start_new_session=True,
        )
        try:
            process.communicate(json.dumps(request).encode(), timeout=timeout)
        except BaseException:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            raise
        if process.returncode:
            errors.seek(0)
            raise ValueError(
                "Bounded PDF worker failed: "
                + errors.read(2000).decode(errors="replace")
            )
        if output.tell() > 64 * 1024 * 1024:
            raise ValueError("PDF output limit exceeded")
        output.seek(0)
        return json.load(output)


def parse_pdf(binding, raw, config=None):
    config = config or ParserConfig(name="pdf")
    check_input(raw, config, "pdf")
    if not raw.startswith(b"%PDF-"):
        raise ValueError("Expected PDF magic")
    data = run_worker(
        [sys.executable, "-I", str(Path(__file__).with_name("pdf_worker.py"))],
        dict(raw=base64.b64encode(raw).decode(), config=config.model_dump()),
        config.timeout,
    )
    images = []
    for image in data["images"]:
        original = image["image_id"]
        image["image_id"] = deterministic_id(
            "image_ref",
            binding.material_id,
            original,
            __import__("hashlib").sha256(raw).hexdigest(),
        )
        for part in data["parts"]:
            if (
                part["type"] == "image_reference"
                and part["data"].get("image_id") == original
            ):
                part["data"]["image_id"] = image["image_id"]
        images.append(ImageArtifact.model_validate(image))
    return build_document(
        binding,
        raw,
        config,
        data["parts"],
        images=images,
        title=data["metadata"].get("title") or None,
        metadata=dict(**data["metadata"], page_count=data["page_count"]),
        warnings=data["warnings"],
    ), {p: base64.b64decode(c, validate=True) for p, c in data["blobs"].items()}
