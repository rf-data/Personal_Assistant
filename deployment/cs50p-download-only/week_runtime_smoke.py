#!/usr/bin/env python3
"""Synthetic week download/reuse without pytest or non-frozen runtime imports."""

import argparse
import importlib.abc
import json
import os
import shutil
import socket
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace


class RuntimeOnly(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {
            "pymupdf",
            "fitz",
            "pydantic_settings",
            "returns",
            "typer",
            "yaml",
            "pytest",
            "tenacity",
            "dotenv",
        } or fullname in {
            "scripts.cs50_worker",
            "src.job_control.controller",
            "src.job_control.native_admission",
        }:
            raise AssertionError("Non-download-runtime import: " + fullname)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source))
    sys.meta_path.insert(0, RuntimeOnly())

    def forbidden(*_args, **_kwargs):
        raise AssertionError("Real network access forbidden")

    socket.getaddrinfo = socket.socket.connect = forbidden
    import httpx

    from src.job_control.models import fingerprint
    from src.model_materials.acquisition import SourceGrant, WeekApproval
    from src.tools_materials import week_acquisition as api
    from src.tools_materials.https_transport import PublicHTTPSTransport

    transport = PublicHTTPSTransport()
    transport.close()
    week = "https://cs50.harvard.edu/python/weeks/0/"
    pset = "https://cs50.harvard.edu/python/psets/0/"
    raw = (
        f'<main><h1>Week 0</h1><ul><li>Lecture<ul><li><a href="https://cdn.cs50.net/python/synthetic.txt">Transcript</a></li></ul></li><li><a href="{pset}">Problem Set 0</a></li></ul></main>'
    ).encode()
    inventory = api.discover(
        {
            week: raw,
            pset: b'<main><h1>Problem Set 0</h1><a href="one/">Task One</a></main>',
            pset
            + "one/": b"<main><h1>Task One</h1><p>Synthetic task description</p></main>",
        },
        source_origin="synthetic",
    )
    requests = []

    def respond(request):
        requests.append(str(request.url))
        text = str(request.url).endswith(".txt")
        return httpx.Response(
            200,
            content=b"Synthetic transcript language content for a lecture."
            if text
            else b"<main><h1>Synthetic page</h1></main>",
            headers={"content-type": "text/plain" if text else "text/html"},
        )

    def approve(inv):
        grants = [
            SourceGrant(
                **{
                    key: row[key]
                    for key in (
                        "material_id",
                        "source_url",
                        "source_format",
                        "max_bytes",
                        "purpose",
                    )
                },
                license_reviewed=True,
            )
            for row in api.plan(inv)["grants"]
            if row["eligible"]
        ]
        return WeekApproval(
            inventory_sha256=fingerprint(inv.model_dump(mode="json")),
            source_origin="synthetic",
            reviewed_by="OFFLINE TEST ONLY",
            review_reference="SYNTHETIC MOCK ONLY",
            transfer_bytes=inv.limits.transfer_bytes,
            grants=tuple(grants),
        )

    original_disk, previous_umask = shutil.disk_usage, os.umask(0o077)
    try:
        # Synthetic host model; never lower the production 5 GiB reserve.
        shutil.disk_usage = lambda _: SimpleNamespace(free=20 * 1024**3)
        with tempfile.TemporaryDirectory(prefix="cs50p07-smoke-") as name:
            archive = Path(name) / "archive"
            done = api.acquire(
                inventory,
                approve(inventory),
                archive,
                transport=httpx.MockTransport(respond),
                offline_test=True,
            )
            count = len(requests)
            reused = api.acquire(
                done,
                approve(done),
                archive,
                transport=httpx.MockTransport(respond),
                offline_test=True,
            )
            report = api.completeness(reused, archive)
            assert report["status"] == "FULLY_COMPLETE", report
            assert len(requests) == count
            print(
                json.dumps(
                    dict(
                        status="CHECKED",
                        synthetic=True,
                        transfers=count,
                        reused=True,
                        processing_enabled=False,
                        c26_status="HOLD",
                        frozen_install_proven=False,
                    )
                )
            )
    finally:
        shutil.disk_usage = original_disk
        os.umask(previous_umask)


if __name__ == "__main__":
    main()
