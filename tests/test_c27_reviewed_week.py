"""Read-only review inputs and real parser/handoff/resume with synthetic bytes."""

import io
import json
import os
import zipfile
from pathlib import Path

import pytest

from scripts.c27_reviewed_week import run
from src.c27_learning_summary import reviewed_week as api
from src.content_store.models import canonical, fingerprint
from src.model_materials.acquisition import WeekInventory


@pytest.fixture(params=["0", "1"])
def review(tmp_path, request):
    """Week 1 is a generalization fixture, never an actual Week-1 acquisition."""
    week = request.param
    root = tmp_path / "review"
    batch = root / "download-batch-01"
    batch.mkdir(parents=True)
    base = "https://cs50.harvard.edu/python/"
    short = base + "shorts/functions/"
    week_url = base + f"weeks/{week}/"
    text_url = (
        "https://cdn.cs50.net/python/2023/x/shorts/functions/lang/en/functions.txt"
    )
    zip_url = "https://cdn.cs50.net/python/2023/x/shorts/functions/src.zip"
    raw_zip = io.BytesIO()
    with zipfile.ZipFile(raw_zip, "w") as archive:
        archive.writestr("hello.py", 'print("hello")\n')
    contents = {
        "week.html": (
            week_url,
            b"<main><h1>Functions</h1><p>A function returns a value.</p></main>",
        ),
        "short.html": (
            short,
            b"<main><h1>Functions Short</h1><p>Functions may take arguments.</p></main>",
        ),
        "functions.txt": (
            text_url,
            b"A function returns a value.\nThe print function displays text.\n",
        ),
        "functions.zip": (zip_url, raw_zip.getvalue()),
    }

    def row(identity, parent, kind, url=None, fmt="html"):
        return dict(
            course_id="cs50_python",
            week_id=week,
            section_id=week,
            material_id=identity,
            parent_material_id=parent,
            material_type=kind,
            title=identity,
            source_url=url,
            source_format=fmt,
        )

    rows = [
        row("course", None, "course"),
        row("week", "course", "week", week_url),
        row("lecture", "week", "lecture", week_url),
        row("short", "week", "short", short),
        row("lecture-page", "lecture", "page", week_url),
        row("short-page", "short", "page", short),
        row("transcript", "short", "transcript", text_url, "txt"),
        row("code", "short", "source_code", zip_url, "zip"),
        row("lecture-video", "lecture", "video", "https://video.cs50.io/lecture"),
        row("short-video", "short", "video", "https://video.cs50.io/short"),
    ]
    snapshots = [
        dict(url=week_url, path="page.html", sha256=api.sha(contents["week.html"][1]))
    ]
    inventory = WeekInventory(
        schema_version=2,
        course_id="cs50_python",
        week_id=week,
        source_origin="synthetic",
        materials=rows,
        expected_ids=tuple(r["material_id"] for r in rows),
        snapshots=tuple(snapshots),
    )
    for n in (1, 2):
        (root / f"inventory-0{n}.json").write_bytes(
            canonical(inventory.model_dump(mode="json"))
        )
        (root / f"plan-0{n}.json").write_bytes(
            canonical(
                dict(inventory_sha256=fingerprint(inventory.model_dump(mode="json")))
            )
        )
    (root / "snapshots.json").write_bytes(
        canonical(
            dict(
                course_id="cs50_python",
                week_id=week,
                source_origin="synthetic",
                pages=snapshots,
            )
        )
    )
    (root / "page.html").write_bytes(contents["week.html"][1])
    files = []
    for name, (url, raw) in contents.items():
        (batch / name).write_bytes(raw)
        files.append(
            dict(
                filename=name,
                source_url=url,
                bytes=len(raw),
                sha256=api.sha(raw),
                status="DOWNLOADED",
                license="synthetic test input",
            )
        )
    (batch / "download-report.json").write_bytes(
        canonical(
            dict(
                status="COMPLETE",
                files=files,
                total_bytes=sum(e["bytes"] for e in files),
            )
        )
    )
    return root


def input_hashes(root):
    return {
        p.relative_to(root).as_posix(): api.sha(p.read_bytes())
        for p in root.rglob("*")
        if p.is_file()
    }


def test_acquisition_parser_quality_summary_and_cache(review, tmp_path):
    before = input_hashes(review)
    result = run(review, tmp_path / "output", fake_summary=True)
    assert result["evidence_kind"] == "fixture" and not result["full_week_acceptance"]
    assert result["downloads"] == result["llm_calls"] == 0
    assert len(result["summaries"]) == 2
    assert all(s["claims"] > 0 and s["cache_verified"] for s in result["summaries"])
    assert [r["status"] for r in result["materials"]].count("handoff_ready") == 3
    catalog, _, reused = api.process_review(review, tmp_path / "output/processing")
    assert reused
    short = next(u for u in catalog.courses[0].weeks[0].units if u.kind == "short")
    transcript = next(m for m in short.materials if m.material_id == "transcript")
    assert all(
        loc.time_status == "unknown" and loc.start is None and loc.end is None
        for b in transcript.blocks
        for loc in b.locators
    )
    assert all(
        m.verification == "synthetic_test_only"
        for u in catalog.courses[0].weeks[0].units
        for m in u.materials
    )
    assert before == input_hashes(review)


@pytest.mark.parametrize(
    "mutation",
    [
        "raw",
        "snapshot",
        "plan_pair",
        "inventory_pair",
        "total",
        "duplicate",
        "traversal",
        "scope",
        "canonical",
        "snapshot_coverage",
    ],
)
def test_reject_invalid_review_before_processing(review, tmp_path, mutation):
    batch = review / "download-batch-01"
    report = json.loads((batch / "download-report.json").read_bytes())
    if mutation == "raw":
        (batch / "functions.txt").write_text("changed")
    elif mutation == "snapshot":
        (review / "page.html").write_text("changed")
    elif mutation == "plan_pair":
        (review / "plan-01.json").write_text("{}")
    elif mutation == "inventory_pair":
        (review / "inventory-01.json").write_text("{}")
    elif mutation == "total":
        report["total_bytes"] += 1
    elif mutation == "duplicate":
        report["files"].append(report["files"][0])
    elif mutation == "traversal":
        report["files"][0]["filename"] = "../page.html"
    elif mutation == "scope":
        p = review / "snapshots.json"
        data = json.loads(p.read_bytes())
        data["week_id"] = "other"
        p.write_bytes(canonical(data))
    elif mutation == "canonical":
        for n in (1, 2):
            (review / f"plan-0{n}.json").write_bytes(
                canonical(dict(inventory_sha256="0" * 64))
            )
    elif mutation == "snapshot_coverage":
        data = json.loads((review / "inventory-02.json").read_bytes())
        data["snapshots"].append(
            dict(url="https://cs50.harvard.edu/python/extra/", sha256="a" * 64)
        )
        inventory = WeekInventory.model_validate(data)
        for n in (1, 2):
            (review / f"inventory-0{n}.json").write_bytes(canonical(data))
            (review / f"plan-0{n}.json").write_bytes(
                canonical(
                    dict(
                        inventory_sha256=fingerprint(inventory.model_dump(mode="json"))
                    )
                )
            )
    (batch / "download-report.json").write_bytes(canonical(report))
    with pytest.raises(ValueError):
        api.process_review(review, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_reject_symlink(review, tmp_path):
    path = review / "download-batch-01/functions.txt"
    path.unlink()
    path.symlink_to(review / "page.html")
    with pytest.raises(ValueError, match="Symlink"):
        api.verify_review(review)


def test_no_output_inside_inputs(review):
    before = input_hashes(review)
    with pytest.raises(ValueError, match="disjoint"):
        api.process_review(review, review / "output")
    assert input_hashes(review) == before


def test_reuse_rejects_tampered_output(review, tmp_path):
    output = tmp_path / "out"
    api.process_review(review, output)
    path = next(output.glob("*/catalog.json"))
    path.write_text("{}")
    with pytest.raises(ValueError, match="output hash"):
        api.process_review(review, output)


def test_resume_after_interrupted_publication(review, tmp_path, monkeypatch):
    original = api.publish_bytes

    def interrupted(path, data):
        if path.name == "catalog.json":
            raise KeyboardInterrupt()
        return original(path, data)

    with monkeypatch.context() as scoped:
        scoped.setattr(api, "publish_bytes", interrupted)
        with pytest.raises(KeyboardInterrupt):
            api.process_review(review, tmp_path / "out")
    before = input_hashes(tmp_path / "out")
    _, _, reused = api.process_review(review, tmp_path / "out")
    assert not reused
    after = input_hashes(tmp_path / "out")
    assert all(after[n] == v for n, v in before.items())
    assert api.process_review(review, tmp_path / "out")[2]


def test_revision_invalidates_processing(review, tmp_path, monkeypatch):
    api.process_review(review, tmp_path / "out")
    monkeypatch.setattr(api, "revision", lambda: "a" * 64)
    assert not api.process_review(review, tmp_path / "out")[2]
    assert len(list((tmp_path / "out").glob("*/receipt.json"))) == 2


@pytest.mark.external_integration
def test_real_penguin_week0_read_only(tmp_path):
    path = os.environ.get("C27_WEEK0_REVIEW_ROOT")
    if not path:
        pytest.skip("Explicit local review directory required")
    root = Path(path)
    before = input_hashes(root)
    selected = [
        row.material_id
        for row, _, _ in api.verify_review(root)[2]
        if row.material_type == "transcript"
    ]
    result = run(
        root, tmp_path / "real-week0", fake_summary=True, material_ids=selected
    )
    assert result["evidence_kind"] == "real_local_raw"
    assert len(result["materials"]) == 4 and not result["full_week_acceptance"]
    successful = [s for s in result["summaries"] if s["state"] != "blocked"]
    assert successful and all(s["cache_verified"] for s in successful)
    assert before == input_hashes(root)


def test_explicit_summary_selection(review, tmp_path):
    result = run(
        review, tmp_path / "out", fake_summary=True, material_ids=["transcript"]
    )
    assert len(result["summaries"]) == 1
    assert result["summaries"][0]["selected_material_ids"] == ["transcript"]
    assert len(result["materials"]) == 4
    with pytest.raises(ValueError, match="unique processed"):
        run(review, tmp_path / "out", fake_summary=True, material_ids=["foreign"])


def test_fake_long_definition_preserves_excerpt_with_bounded_topic():
    from src.c27_learning_summary.llm import FakeLLM
    from src.c27_learning_summary.models import SectionResponse, SummaryConfig

    text = "An introductory sentence. " * 12 + "This is a function."
    reply = FakeLLM().complete(
        [{"content": json.dumps({"excerpt": {"text": text, "ref_id": "a" * 64}})}],
        config=SummaryConfig(),
        timeout=20,
    )
    claim = SectionResponse.model_validate_json(reply.raw).claims[0]
    assert claim.text == text and len(claim.topic) == 200
