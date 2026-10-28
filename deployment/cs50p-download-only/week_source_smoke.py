#!/usr/bin/env python3
"""C08 synthetic ZIP acquisition in a fresh download-only process; no native processing/C16."""

import argparse
import importlib.util
import io
import json
import shutil
import socket
import sys
import tempfile
import zipfile
from pathlib import Path
from types import SimpleNamespace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source))
    spec = importlib.util.spec_from_file_location(
        "download_smoke", Path(__file__).with_name("week_runtime_smoke.py")
    )
    smoke = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(smoke)
    sys.meta_path.insert(0, smoke.RuntimeOnly())

    def forbidden(*args, **kwargs):
        raise AssertionError("Real network forbidden")

    socket.getaddrinfo = socket.socket.connect = forbidden
    shutil.disk_usage = lambda _: SimpleNamespace(free=20 * 1024**3)
    import httpx

    from src.job_control.models import fingerprint
    from src.model_materials.acquisition import SourceGrant, WeekApproval
    from src.tools_materials import week_acquisition as api

    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        z.writestr("example.py", "# Synthetic source\ndef example():\n    return 42\n")
    url = "https://cs50.harvard.edu/python/weeks/0/"
    inventory = api.discover(
        {
            url: b'<main><h1>Week 0</h1><ul><li>Lecture<ul><li>Source Code<ul><li><a href="https://cdn.cs50.net/python/synthetic/src.zip">Zip</a></li></ul></li><li><a href="https://cdn.cs50.net/python/synthetic/t.txt">Transcript</a></li></ul></li></ul></main>'
        },
        source_origin="synthetic",
        completion=True,
    )
    row = next(
        r
        for r in inventory.materials
        if r.material_type == "source_code" and r.required
    )
    calls = []

    def respond(request):
        calls.append(str(request.url))
        return httpx.Response(
            200, content=stream.getvalue(), headers={"content-type": "application/zip"}
        )

    def approve(inv):
        return WeekApproval(
            inventory_sha256=fingerprint(inv.model_dump(mode="json")),
            source_origin="synthetic",
            reviewed_by="offline test",
            review_reference="no production evidence",
            transfer_bytes=1048576,
            grants=(
                SourceGrant(
                    material_id=row.material_id,
                    source_url=row.source_url,
                    source_format="zip",
                    max_bytes=1048576,
                    license_reviewed=True,
                ),
            ),
        )

    with tempfile.TemporaryDirectory(prefix="cs50p08-source-smoke-") as temp:
        done = api.acquire(
            inventory,
            approve(inventory),
            Path(temp) / "raw",
            transport=httpx.MockTransport(respond),
            offline_test=True,
        )
        again = api.acquire(
            done,
            approve(done),
            Path(temp) / "raw",
            transport=httpx.MockTransport(respond),
            offline_test=True,
        )
        verified = next(r for r in again.materials if r.material_id == row.material_id)
        assert verified.acquisition_status == "VERIFIED" and len(calls) == 1
    forbidden_modules = {
        "src.tools_materials.week_processing",
        "src.tools_materials.processing",
        "src.tools_materials.parse_pdf",
        "src.tools_materials.code_structure",
        "src.job_control.controller",
        "scripts.cs50_worker",
        "pymupdf",
        "fitz",
    }
    assert not forbidden_modules.intersection(sys.modules)
    print(
        json.dumps(
            dict(
                status="PASS",
                network="mock-only",
                zip_transfers=len(calls),
                reused=True,
                c16_imported=False,
                processing_imported=False,
                source_origin="synthetic",
            )
        )
    )


if __name__ == "__main__":
    main()
