"""PyMuPDF text/images in a killable CPU/address-space/page/output bounded worker."""

import base64
import json
import os
import signal
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

from src.model_discovery.cs50 import deterministic_id
from src.model_materials.materials import ImageArtifact, ParserConfig
from src.tools_materials.parse_html import build_document, check_input

_JOB_SCOPE = ContextVar("material_worker_job_scope", default=False)


@contextmanager
def job_worker_scope():
    """Trusted C16 entry only: keep workers inside the guardian-owned group.

    No persisted PID, request parameter or inherited environment selects this.
    The guardian is the subreaper and owns descendant cleanup confirmation.
    """
    token = _JOB_SCOPE.set(True)
    try:
        yield
    finally:
        _JOB_SCOPE.reset(token)


def run_worker(command, request, timeout):
    managed = _JOB_SCOPE.get()
    bootstrap = None
    if managed:
        from src.job_control.guardian import arm_parent_death

        parent = os.getpid()

        # Same bootstrap race check as the guardian, with an uncatchable signal.
        # C16's adapter is single-threaded at this fork boundary.
        def bootstrap():
            arm_parent_death(parent, signal.SIGKILL)

    with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=output,
            stderr=errors,
            start_new_session=not managed,
            preexec_fn=bootstrap,
        )
        try:
            process.communicate(json.dumps(request).encode(), timeout=timeout)
        except BaseException:
            try:
                if managed:
                    process.kill()  # Direct unreaped child, never the adapter's group.
                else:
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
    config = config or ParserConfig(name="pdf", version="2")
    check_input(raw, config, "pdf")
    if config.version != "2":
        raise ValueError("PDF parser v1 is read-only; use v2 in a new workspace")
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
