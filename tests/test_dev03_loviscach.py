"""Synthetic technical checks; never open the authorized real exam originals."""

import base64
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.acceptance import dev03_loviscach as run
from src.content_store.models import sha256
from src.model_materials.materials import ParserConfig


def entry(raw=b"synthetic"):
    return dict(
        file_name="synthetic.pdf",
        source_id="synthetic-source",
        page_count=2,
        raw_artifact=dict(sha256=sha256(raw), size_bytes=len(raw)),
    )


def test_actual_integrated_worker_repeat_resources_and_no_overwrite(tmp_path):
    root = run.private_directory(tmp_path / "private")
    fixture = Path("tests/fixtures/visual_inventory/source.pdf.b64")
    request = dict(
        raw=base64.b64encode(base64.b64decode(fixture.read_bytes())).decode(),
        config=ParserConfig(name="pdf", version="2").model_dump(),
    )
    first = run.worker(root, root / "first", "pdf_worker.py", request, 20)
    second = run.worker(root, root / "second", "pdf_worker.py", request, 20)
    assert first == second and first["page_count"] == 2
    assert json.loads((root / "first/resources.json").read_bytes())["max_rss_kib"] > 0
    for p in root.rglob("*"):
        assert stat.S_IMODE(p.stat().st_mode) == (0o700 if p.is_dir() else 0o600)
    before = (root / "first/response.json").read_bytes()
    with pytest.raises(FileExistsError):
        run.worker(root, root / "first", "pdf_worker.py", request, 20)
    assert (root / "first/response.json").read_bytes() == before


def test_worker_audit_blocks_network(tmp_path):
    source = tmp_path / "synthetic_probe.py"
    source.write_text("import socket\nsocket.socket()\n")
    result = subprocess.run(
        [sys.executable, "-I", "-c", run.BOOTSTRAP, str(source)], capture_output=True
    )
    assert result.returncode != 0 and b"Network disabled" in result.stderr


def test_observations_are_candidates_not_independent_gold():
    location = dict(page=1, bbox=[1, 2, 80, 20])
    parts = [
        dict(type="math", text="x^2+1=0", location=location, uncertainty=[]),
        dict(
            type="heading",
            text="1. Synthetic task",
            location=location,
            uncertainty=["heuristic"],
        ),
    ]
    data = dict(parts=parts, images=[], warnings=[], page_count=2)
    visual = dict(observations=[], page_count=2)
    value = run.analyze(entry(), data, visual)
    assert value == run.analyze(entry(), data, visual)
    assert value["formula_candidates"] == 1 and value["syntax"] == {"syntax_valid": 1}
    assert value["quality_rate"] is None and value["quality_denominator"] == 0
    assert value["page_coverage"] == {"1": 2, "2": 0}
    assert all(
        c["independent_reference"] is None and c["reviewed_by"] is None
        for c in value["candidates"]
    )
    assert len({c["candidate_id"] for c in value["candidates"]}) == len(
        value["candidates"]
    )


def test_private_writes_limits_and_symlink_inputs(tmp_path, monkeypatch):
    root = run.private_directory(tmp_path / "private")
    run.write(root, root / "keep", b"unchanged")
    with pytest.raises(FileExistsError):
        run.write(root, root / "keep", b"overwrite")
    assert (root / "keep").read_bytes() == b"unchanged"
    (tmp_path / "original").write_bytes(b"synthetic")
    (tmp_path / "synthetic.pdf").symlink_to(tmp_path / "original")
    with pytest.raises(ValueError, match="Symlink"):
        run.read_original(tmp_path, entry())
    monkeypatch.setattr(run, "MAX_OUTPUT", 1)
    with pytest.raises(OSError):
        run.write(root, root / "large", b"xx")
    assert not (root / "large").exists()


def test_hash_mismatch_rejected_before_original_processing(tmp_path):
    (tmp_path / "synthetic.pdf").write_bytes(b"modified")
    with pytest.raises(ValueError, match="identity"):
        run.read_original(tmp_path, entry())


def test_review_limits_diversity_and_unicode_offsets():
    summaries = []
    for n in range(4):
        e = entry()
        e["source_id"] += str(n)
        e["file_name"] = f"synthetic-{n}.pdf"
        candidates = [
            run.candidate(
                e,
                kind,
                f"/parts/{i}",
                dict(page=1, bbox=[1, 2, 80, 20]),
                "😀e\u0301\r\n  x^2",
                "requires_review",
            )
            for kind in ("formula", "structure", "visual")
            for i in range(25)
        ]
        summaries.append(dict(candidates=candidates))
    selected = run.select_candidates(summaries)
    assert [
        sum(c["kind"] == k for c in selected)
        for k in ("formula", "structure", "visual")
    ] == [20, 10, 10]
    assert len({c["file_name"] for c in selected if c["kind"] == "formula"}) == 4
    assert all(c["extracted_result"] == "😀e\u0301\r\n  x^2" for c in selected)


def test_real_local_crop_and_inert_escaped_comparison(tmp_path):
    import pymupdf

    with pymupdf.open() as document:
        page = document.new_page()
        page.insert_text((20, 40), "Synthetic original")
        raw = document.tobytes()
    e = entry(raw)
    e["page_count"] = 1
    (tmp_path / e["file_name"]).write_bytes(raw)
    c = run.candidate(
        e,
        "structure",
        "/parts/0",
        dict(page=1, bbox=[10, 15, 200, 60]),
        '<script>alert("synthetic")</script>\r\n\t',
        "requires_review",
    )
    root = run.private_directory(tmp_path / "private")
    selected = run.review_package(root, tmp_path, [e], [dict(candidates=[c])])
    assert selected == {"structure": 1}
    html = (root / "review/index.html").read_text()
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert "Content-Security-Policy" in html and "https://" not in html
    assert (root / "review/region-00.png").read_bytes().startswith(b"\x89PNG")
    assert os.stat(root / "review/candidates.json").st_mode & 0o777 == 0o600
