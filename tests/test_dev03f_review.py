"""Synthetic, private offline exports; no real human decisions are manufactured."""

import copy
import os
from collections import Counter

import pymupdf
import pytest

from scripts.acceptance import dev03f_review as review
from src.content_store.errors import IntegrityError
from src.content_store.models import canonical, fingerprint, sha256
from src.model_evaluation.material_evaluation import GoldDataset


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_bytes(canonical(data) + b"\n")
    path.chmod(0o600)


def seal(path):
    save(
        path / "manifest.json",
        dict(
            schema_version=1,
            inventory_digest=review.DIGEST,
            files={
                p.relative_to(path).as_posix(): sha256(p.read_bytes())
                for p in path.rglob("*")
                if p.is_file() and p.name != "manifest.json"
            },
        ),
    )


@pytest.fixture
def exported(tmp_path, monkeypatch):
    inputs = tmp_path / "inputs"
    run = tmp_path / "run"
    output = tmp_path / "private"
    for folder in (inputs, run, output):
        folder.mkdir(mode=0o700)
    entries, summaries = [], []
    for n in range(4):
        name = f"synthetic_{n}.pdf"
        doc = pymupdf.open()
        for _ in range(2):
            page = doc.new_page()
            page.insert_text((50, 80), "SYNTHETIC ORIGINAL; no real gold")
        raw = doc.tobytes()
        doc.close()
        (inputs / name).write_bytes(raw)
        entries.append(
            dict(
                file_name=name,
                source_id=f"synthetic_source_{n}",
                raw_artifact=dict(sha256=sha256(raw), size_bytes=len(raw)),
            )
        )
        location = dict(page=1, bbox=[40.0, 50.0, 400.0, 100.0])
        parts = [
            dict(type="math", text=f"SYNTHETIC prediction {i}", location=location)
            for i in range(8)
        ] + [
            dict(
                type="paragraph", text="SYNTHETIC ordinary control", location=location
            ),
            dict(
                type="paragraph",
                text="1. SYNTHETIC structure <script>x</script>",
                location=location,
            ),
            dict(type="paragraph", text="2. SYNTHETIC structure", location=location),
        ]
        pdf = dict(parts=parts)
        visual = dict(
            observations=[dict(location=location, tag="vector") for _ in range(4)]
        )
        candidates = [
            dict(
                candidate_id=f"synthetic_candidate_{n}_{i}",
                kind="formula" if i < 8 else "structure",
                locator=dict(origin_pointer=f"/parts/{i}", **location),
                extracted_result=p["text"],
                hypothesis="synthetic hypothesis",
                syntax_status="syntax_valid" if i == 0 else "not_evaluable",
            )
            for i, p in enumerate(parts)
            if i != 8
        ]
        summary = dict(
            source_id=entries[-1]["source_id"],
            original_sha256=sha256(raw),
            pdf_observations_sha256=fingerprint(pdf),
            visual_observations_sha256=fingerprint(visual),
        )
        summaries.append(summary)
        folder = run / name.removesuffix(".pdf")
        save(folder / "analysis.json", dict(**summary, candidates=candidates))
        save(folder / "pdf/response.json", pdf)
        save(folder / "visual/response.json", visual)
    report = dict(documents=summaries)
    save(run / "report.json", dict(report=report, sha256=fingerprint(report)))
    save(
        run / "execution.json",
        dict(
            implementation_revision="a" * 40,
            pdf_worker_sha256="b" * 64,
            visual_worker_sha256="c" * 64,
        ),
    )
    seal(run)
    monkeypatch.setattr(review, "source_inventory", lambda: entries)
    monkeypatch.setattr(review, "RUN_DIGEST", fingerprint(report))
    package_path, package = review.prepare(run, inputs, output)
    return package_path, package, run, inputs, output


def response(exported):
    path, _package, _run, _inputs, output = exported
    data = review.read(path / "responses.blank.json")
    row = data["responses"][0]
    row.update(
        confirm=True,
        original_reviewed_independently=True,
        annotation=dict(
            schema_version=1,
            mode="independent_original",
            quality="correct",
            expected_content="SYNTHETIC HUMAN TEST MARKER, not real gold",
            error_categories=[],
            comment="SYNTHETIC attestation for contract testing only",
        ),
        formula_decision="exact_match",
        reviewed_at="2026-10-20T13:00:00+02:00",
        evidence_reference="synthetic-test-evidence",
    )
    answer = output / "answers-test.json"
    save(answer, data)
    return data, answer


def test_prepared_counts_independence_and_pending_gold(exported):
    path, package, run, inputs, _output = exported
    cases = package["package"]["cases"]
    assert Counter(c["kind"] for c in cases) == dict(
        formula=20, structure=10, visual=10
    )
    assert Counter(c["selection_criterion"] for c in cases) == dict(
        systematic_control=12, candidate=28
    )
    assert len({c["review_id"] for c in cases}) == 40
    assert all(
        c["visual_observation"]["tag"] == "vector"
        for c in cases
        if c["kind"] == "visual"
    )
    assert all(
        c["source_version_id"] is None and c["parsed_version_id"] is None for c in cases
    )
    gold = GoldDataset.model_validate(review.read(path / "pending_gold.v1.json"))
    assert len(gold.references) == 40
    assert all(
        r.reference_status == "pending_review" and r.expected_content is None
        for r in gold.references
    )
    assert all(
        not row["confirm"] and row["annotation"] is None
        for row in review.read(path / "responses.blank.json")["responses"]
    )
    queries = review.read(path / "query_worksheet.json")["queries"]
    assert len(queries) == 20
    assert all(q["text"] is None and not q["pool_complete"] for q in queries)
    original = (path / "originals.html").read_text()
    compared = (path / "comparison.html").read_text()
    assert "SYNTHETIC prediction" not in original
    assert "synthetic hypothesis" not in original
    assert "<script>" not in compared
    assert "&lt;script&gt;" in compared
    assert "Content-Security-Policy" in original
    assert len(list(path.glob("original-*.png"))) == 40
    review.verify_manifest(path)
    review.verify_manifest(run)
    assert len(list(inputs.iterdir())) == 4
    assert path.stat().st_mode & 0o777 == 0o700
    assert all(p.stat().st_mode & 0o777 == 0o600 for p in path.iterdir())


def test_capture_is_explicit_immutable_and_not_c23_gold(exported):
    path, package, _run, _inputs, output = exported
    data, answer = response(exported)
    with pytest.raises(PermissionError):
        review.capture(path, answer, output / "revision-1.json")
    snapshot = review.capture(path, answer, output / "revision-1.json", attest=True)
    assert len(snapshot["reviews"]) == 1
    assert snapshot["confirmed_c23_gold"] == 0
    assert snapshot["quality_rate"] is None
    assert snapshot["reviews"][0]["review"]["status"] == "confirmed"
    gold = GoldDataset.model_validate(snapshot["gold"])
    assert all(r.reference_status == "pending_review" for r in gold.references)
    with pytest.raises(FileExistsError):
        review.capture(path, answer, output / "revision-1.json", attest=True)
    previous = review.read(output / "revision-1.json")
    assert fingerprint(previous["snapshot"]) == previous["sha256"]
    data["previous_sha256"] = previous["sha256"]
    data["responses"][0]["annotation"]["quality"] = "partial"
    data["responses"][0]["formula_decision"] = "incomplete"
    save(answer, data)
    revision = review.capture(
        path,
        answer,
        output / "revision-2.json",
        output / "revision-1.json",
        attest=True,
    )
    assert revision["previous_sha256"] == previous["sha256"]
    assert revision["reviews"][0]["annotation"]["quality"] == "partial"
    assert review.read(output / "revision-1.json") == previous
    assert package["sha256"] == review.read(path / "package.json")["sha256"]


@pytest.mark.parametrize(
    "change",
    [
        lambda d: d.update(schema_version=True),
        lambda d: d.update(package_sha256="f" * 64),
        lambda d: d.update(previous_sha256="f" * 64),
        lambda d: d["responses"][0].update(review_id="unknown"),
        lambda d: d["responses"].append(copy.deepcopy(d["responses"][0])),
        lambda d: d["responses"][0].update(confirm="true"),
        lambda d: d["responses"][0].update(original_reviewed_independently=False),
        lambda d: d["responses"][0]["annotation"].update(mode="assisted"),
        lambda d: d["responses"][0]["annotation"].update(expected_content=None),
        lambda d: d["responses"][0]["annotation"].update(quality="incorrect"),
        lambda d: d["responses"][0].update(
            formula_decision="mathematically_equivalent"
        ),
        lambda d: d["responses"][0].update(reviewed_at="2026-10-20T13:00:00"),
        lambda d: d["responses"][0].update(evidence_reference=None),
        lambda d: d["responses"][0].update(reviewer="someone_else"),
    ],
)
def test_bad_review_never_publishes(exported, change):
    path, _package, _run, _inputs, output = exported
    data, answer = response(exported)
    change(data)
    save(answer, data)
    destination = output / "must-not-exist.json"
    with pytest.raises((ValueError, TypeError)):
        review.capture(path, answer, destination, attest=True)
    assert not destination.exists()


def test_blank_reviews_and_symlink_inputs_rejected(exported):
    path, _package, _run, _inputs, output = exported
    blank = output / "blank.json"
    save(blank, review.read(path / "responses.blank.json"))
    with pytest.raises(ValueError, match="No explicit"):
        review.capture(path, blank, output / "none.json", attest=True)
    link = output / "link.json"
    link.symlink_to(blank)
    with pytest.raises(OSError):
        review.capture(path, link, output / "none.json", attest=True)
    assert not (output / "none.json").exists()


def test_integrity_no_overwrite_and_changed_original(exported):
    path, _package, run, inputs, output = exported
    with pytest.raises(FileExistsError):
        review.write(path, "originals.html", b"overwrite")
    with pytest.raises(ValueError):
        review.write(path, "../outside", b"escape")
    original = next(inputs.iterdir())
    original.write_bytes(b"changed")
    with pytest.raises(ValueError, match="Original"):
        review.prepare(run, inputs, output)
    (path / "original-00.png").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="integrity"):
        review.verify_manifest(path)


def test_parent_revision_must_match_exact_case_binding(exported):
    path, _package, _run, _inputs, output = exported
    data, answer = response(exported)
    previous_path = output / "revision-1.json"
    review.capture(path, answer, previous_path, attest=True)
    previous = review.read(previous_path)
    previous["snapshot"]["reviews"][0]["binding"]["original_sha256"] = "f" * 64
    previous["sha256"] = fingerprint(previous["snapshot"])
    save(previous_path, previous)
    data["previous_sha256"] = previous["sha256"]
    save(answer, data)
    with pytest.raises(ValueError, match="binding"):
        review.capture(
            path, answer, output / "revision-2.json", previous_path, attest=True
        )


def test_manifest_traversal_and_private_modes(exported):
    path, _package, _run, _inputs, _output = exported
    manifest = review.read(path / "manifest.json")
    manifest["files"]["../escape"] = "f" * 64
    save(path / "manifest.json", manifest)
    with pytest.raises(ValueError, match="Relative"):
        review.verify_manifest(path)
    path.chmod(0o755)
    with pytest.raises(IntegrityError):
        review.private_dir(path)
    path.chmod(0o700)
    assert os.getuid() == path.stat().st_uid


def test_repeat_export_has_same_bound_selection_and_digest(exported):
    path, package, run, inputs, output = exported
    second_path, second_package = review.prepare(run, inputs, output)
    assert second_path != path
    assert package == second_package
    assert review.read(path / "manifest.json") == review.read(
        second_path / "manifest.json"
    )


def test_candidate_cannot_replace_actual_worker_text(exported):
    _path, _package, run, inputs, output = exported
    analysis_path = next(run.glob("*/analysis.json"))
    analysis = review.read(analysis_path)
    analysis["candidates"][0]["extracted_result"] = "invented prediction"
    save(analysis_path, analysis)
    seal(run)
    with pytest.raises(ValueError, match="Candidate differs"):
        review.prepare(run, inputs, output)


def test_unknown_formula_requires_explicit_undetermined(exported):
    path, _package, _run, _inputs, output = exported
    data, answer = response(exported)
    data["responses"][0]["annotation"].update(
        quality="undetermined", expected_content=None
    )
    data["responses"][0]["formula_decision"] = "not_evaluable"
    save(answer, data)
    snapshot = review.capture(path, answer, output / "unknown.json", attest=True)
    assert snapshot["reviews"][0]["annotation"]["quality"] == "undetermined"
    assert snapshot["quality_rate"] is None


def test_justified_equivalence_stays_human_and_provenance_pending(exported):
    path, _package, _run, _inputs, output = exported
    data, answer = response(exported)
    data["responses"][0].update(
        formula_decision="mathematically_equivalent",
        latex_reference="x+x",
        equivalence_reason="SYNTHETIC TEST: distribute the coefficient two",
    )
    save(answer, data)
    snapshot = review.capture(path, answer, output / "equivalent.json", attest=True)
    assert snapshot["reviews"][0]["formula_decision"] == "mathematically_equivalent"
    assert snapshot["confirmed_c23_gold"] == 0


def test_capture_output_cannot_modify_package(exported):
    path, _package, _run, _inputs, _output = exported
    _data, answer = response(exported)
    with pytest.raises(ValueError, match="sibling revision"):
        review.capture(path, answer, path / "new.json", attest=True)
    assert not (path / "new.json").exists()
