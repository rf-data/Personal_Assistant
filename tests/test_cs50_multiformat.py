"""Real integrated importer, synthetic raw inputs, immutable local archive; offline."""

import json
import os
import socket
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import cs50_batch as cli
from scripts.cs50_workflow_demo import inputs as demo_inputs
from src.model_transcribe.data_transcribe import TranscriptDocument
from src.tools_materials import batch as api
from src.tools_materials import transcripts as lane
from src.tools_materials.capacity import MIB, CapacityLimits


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("Real network forbidden")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


@pytest.fixture
def env(tmp_path, monkeypatch):
    os.umask(0o077)
    tmp_path.chmod(0o700)
    # Capacity is modeled, production's five-GiB reserve stays unchanged.
    monkeypatch.setattr(
        "shutil.disk_usage", lambda _: SimpleNamespace(free=100 * 1024**3)
    )
    snapshots = tmp_path / "discovery"
    demo_inputs(snapshots)
    page = snapshots / "cs50_python/week0.html"
    text = page.read_text().replace(
        "</ul></li></ul></main>",
        '<li>Subtitles<ul><li><a href="https://cdn.cs50.net/python/2022/x/lectures/0/lang/en/lecture0.srt">SRT</a></li></ul></li>'
        '<li>Transcript<ul><li><a href="https://cdn.cs50.net/python/2022/x/lectures/0/lang/en/lecture0.txt">TXT</a></li></ul></li>'
        "</ul></li></ul></main>",
    )
    page.write_text(text)
    manifest = snapshots / "manifest.json"
    data = json.loads(manifest.read_text())
    for p in data["courses"][0]["pages"]:
        p["sha256"] = api.sha((snapshots / p["file"]).read_bytes())
    manifest.write_text(json.dumps(data))
    bindings = [
        b
        for b in api.make_plan(manifest).materials
        if b.role in {"subtitles", "transcript"}
    ]
    assert {b.format for b in bindings} == {"srt", "txt"}
    batch = api.plan(
        manifest, ["cs50_python"], [b.source_id for b in bindings], synthetic=True
    )
    payloads = {
        "srt": b"17\r\n00:00:01,000 --> 00:00:03,500\r\nFirst\r\nline\r\n\r\n42\r\n00:00:02,000 --> 00:00:04,000\r\n\r\n43\r\n00:00:03,000 --> 00:00:05,000\r\nThird\r\n",
        "txt": "\ufeff  héllo 😀 e\u0301\r\n\tcode()\r\n\r\nSecond paragraph.\r\n".encode(),
    }
    inputs = {}
    grants = []
    for b in batch.materials:
        path = tmp_path / ("original." + b.format)
        path.write_bytes(payloads[b.format])
        inputs[b.source_id] = path
        refs = {
            n: "synthetic-operator-evidence"
            for n in api.SourceApproval.model_fields
            if n.endswith("_reference")
        }
        grants.append(
            api.SourceApproval(
                material_id=b.material_id,
                source_id=b.source_id,
                course_id=b.resource.course_id,
                original_url=b.original_url,
                process=True,
                download=False,
                expected_sha256=api.sha(payloads[b.format]),
                **refs,
            )
        )
    return SimpleNamespace(
        batch=batch,
        manifest=manifest,
        inputs=inputs,
        payloads=payloads,
        approvals=api.Approvals(sources=tuple(grants)),
        root=tmp_path / "new-transcript-archive",
        limits=CapacityLimits(
            reserve_bytes=5 * 1024**3, archive_bytes=64 * MIB, max_materials=2
        ),
    )


def run(env, action="import", **kwargs):
    return lane.run(
        env.batch,
        env.root,
        kwargs.pop("approvals", env.approvals),
        kwargs.pop("inputs", env.inputs),
        action=action,
        limits=kwargs.pop("limits", env.limits),
        **kwargs,
    )


def folder(env, fmt):
    b = next(b for b in env.batch.materials if b.format == fmt)
    return env.root / b.material_id.split(":")[-1]


def snapshot(root):
    return {
        str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }


def test_preview_has_no_source_reads_or_output(env, monkeypatch):
    original = lane.read_file

    def read(path, *args):
        assert Path(path) not in env.inputs.values()
        return original(path, *args)

    monkeypatch.setattr(lane, "read_file", read)
    result = run(env, "preview")
    assert result["status_counts"] == {"selected": 2}
    assert all(not r["download_approved"] for r in result["materials"])
    assert not env.root.exists()


def test_preview_missing_input_is_not_ready(env):
    next(iter(env.inputs.values())).unlink()
    assert run(env, "preview")["status_counts"] == {"missing": 1, "selected": 1}
    assert not env.root.exists()


def test_srt_txt_roundtrip_provenance_raw_bytes_lecture_and_idempotency(env):
    originals = {k: p.read_bytes() for k, p in env.inputs.items()}
    result = run(env)
    assert result["processed_materials"] == 2 and not result["full_week_coverage"]
    assert result["network_requests"] == 0 and not result["c18_publication"]
    assert all(not r["reused"] for r in result["materials"])
    before = snapshot(env.root)
    assert all(r["reused"] for r in run(env)["materials"])
    assert snapshot(env.root) == before
    assert {k: p.read_bytes() for k, p in env.inputs.items()} == originals
    for fmt in ("srt", "txt"):
        directory = folder(env, fmt)
        receipt = lane.TranscriptReceipt.model_validate_json(
            (directory / "receipt.json").read_bytes()
        )
        document = TranscriptDocument.model_validate_json(
            (directory / "transcript.json").read_bytes()
        )
        assert (directory / ("source." + fmt)).read_bytes() == env.payloads[fmt]
        assert receipt.binding.source_id != receipt.binding.lecture_ids[0]
        assert receipt.lecture.source_url == receipt.binding.original_url
        assert receipt.lecture.file_type == document.provenance.media_format == fmt
        assert document.provenance.language == document.language == "en"
        assert document.provenance.source_file == document.source == "source." + fmt
        assert (
            receipt.raw_sha256
            == receipt.lecture.content_hash
            == api.sha(env.payloads[fmt])
        )
        assert str(env.root) not in (directory / "transcript.json").read_text()
        if fmt == "srt":
            assert len(document.segments) == 3 and document.segments[1].text == ""
            assert document.segments[0].end > document.segments[1].start
            assert document.segments[0].text == "First\nline" and document.duration == 5
        else:
            assert document.text == env.payloads[fmt].decode("utf-8-sig").replace(
                "\r\n", "\n"
            )
            assert document.duration is None and all(
                s.start is s.end is None for s in document.segments
            )
            with pytest.raises(ValueError):
                document.require_timestamps()
    assert run(env, "report", inputs={})["status_counts"] == {"processed": 2}


@pytest.mark.parametrize(
    "problem",
    [
        "approval",
        "process",
        "hash",
        "url",
        "course",
        "input_missing",
        "invalid_srt",
        "oversize",
    ],
)
def test_partial_failure_and_explicit_repeat(env, problem):
    b = env.batch.materials[0]
    path = env.inputs[b.source_id]
    if problem == "approval":
        env.approvals = api.Approvals(sources=env.approvals.sources[1:])
    elif problem in {"process", "hash", "url", "course"}:
        update = (
            {"process": False}
            if problem == "process"
            else {"expected_sha256": None}
            if problem == "hash"
            else {"original_url": "https://example.org/wrong"}
            if problem == "url"
            else {"course_id": "cs50x"}
        )
        env.approvals = api.Approvals(
            sources=(
                env.approvals.sources[0].model_copy(update=update),
                *env.approvals.sources[1:],
            )
        )
    elif problem == "input_missing":
        path.unlink()
    else:
        raw = b"x" * (MIB + 1) if problem == "oversize" else b"not a subtitle"
        path.write_bytes(raw)
        env.approvals = api.Approvals(
            sources=(
                env.approvals.sources[0].model_copy(
                    update={"expected_sha256": api.sha(raw)}
                ),
                *env.approvals.sources[1:],
            )
        )
    result = run(env)
    assert result["processed_materials"] == 1
    assert result["materials"][0]["status"] in {"blocked", "missing"}
    assert result["materials"][1]["status"] == "processed"
    assert "error_class" in result["materials"][0]
    assert not folder(env, b.format).exists()


@pytest.mark.parametrize("target", ["source.srt", "transcript.json", "receipt.json"])
def test_tampered_archive_never_overwritten_or_repaired(env, target):
    run(env)
    path = folder(env, "srt") / target
    path.write_bytes(path.read_bytes() + b" ")
    before = snapshot(env.root)
    result = run(env)
    assert result["processed_materials"] == 1
    assert snapshot(env.root) == before


def test_interrupted_publication_blocks_instead_of_adoption(env):
    run(env)
    (folder(env, "srt") / "receipt.json").unlink()
    before = snapshot(env.root)
    assert run(env)["status_counts"] == {"blocked": 1, "processed": 1}
    assert snapshot(env.root) == before


def test_existing_root_and_different_batch_are_not_adopted(env):
    env.root.mkdir(mode=0o700)
    with pytest.raises(FileNotFoundError):
        run(env)
    assert not (env.root / "batch.sha256").exists()


def test_explicit_retry_after_missing_input_and_changed_hash(env):
    b = env.batch.materials[0]
    path = env.inputs[b.source_id]
    raw = path.read_bytes()
    path.unlink()
    assert run(env)["status_counts"] == {"missing": 1, "processed": 1}
    path.write_bytes(raw)
    assert run(env)["status_counts"] == {"processed": 2}
    before = snapshot(env.root)
    path.write_bytes(raw + b"changed")
    assert run(env)["status_counts"] == {"blocked": 1, "processed": 1}
    assert snapshot(env.root) == before
    assert run(env, "report", inputs={})["processed_materials"] == 2


def test_foreign_lecture_unknown_format_and_changed_discovery_rejected(env):
    binding = env.batch.materials[0].model_copy(
        update={"lecture_ids": ("foreign-lecture",)}
    )
    batch = env.batch.model_copy(
        update={"materials": (binding, *env.batch.materials[1:])}
    )
    with pytest.raises(ValueError, match="binding changed"):
        lane.run(
            batch,
            env.root,
            env.approvals,
            env.inputs,
            action="import",
            limits=env.limits,
        )
    assert not env.root.exists()
    binding = binding.model_copy(update={"format": "vtt"})
    assert not lane.supported(binding)
    for url in (
        "http://cdn.cs50.net/test.srt",
        "https://example.org/test.srt",
        "https://cdn.cs50.net/test.srt?query",
    ):
        assert not lane.supported(
            env.batch.materials[0].model_copy(update={"original_url": url})
        )
    page = env.manifest.parent / "cs50_python/week0.html"
    page.write_bytes(page.read_bytes() + b" ")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        run(env)


def test_revoked_approval_and_changed_importer_block_reuse(env, monkeypatch):
    run(env)
    before = snapshot(env.root)
    assert run(env, "report", inputs={}, approvals=api.Approvals())[
        "status_counts"
    ] == {"blocked": 2}
    monkeypatch.setattr(lane, "revision", lambda: "0" * 64)
    assert run(env)["status_counts"] == {"blocked": 2}
    assert snapshot(env.root) == before


def test_lock_contention_and_insufficient_file_permissions_fail_closed(
    env, monkeypatch
):
    import fcntl

    run(env)
    with (env.root / ".materials.lock").open("r+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            run(env)
    (folder(env, "srt") / "receipt.json").chmod(0o644)
    assert run(env)["processed_materials"] == 1


def test_invalid_nul_srt_and_nonmonotonic_cues(env):
    binding = next(b for b in env.batch.materials if b.format == "srt")
    env.root.mkdir(mode=0o700)
    for raw in (
        b"\x00",
        b"1\n00:00:02,000 --> 00:00:03,000\na\n\n2\n00:00:01,000 --> 00:00:04,000\nb\n",
    ):
        with pytest.raises(ValueError):
            lane.parse(raw, binding, env.root, env.limits)
    assert not list(env.root.iterdir())


@pytest.mark.parametrize(
    "contents", ["[]", '{"source":"relative.srt"}', '{"source":3}', "{}"]
)
def test_invalid_explicit_input_mapping(env, contents, tmp_path):
    path = tmp_path / "bad-inputs.json"
    path.write_text(contents)
    with pytest.raises(ValueError):
        lane.load_inputs(path)


@pytest.mark.parametrize("problem", ["symlink", "parent_symlink", "traversal", "fifo"])
def test_unsafe_inputs_rejected(env, problem, tmp_path):
    b = env.batch.materials[0]
    path = env.inputs[b.source_id]
    if problem == "symlink":
        alternate = tmp_path / "link.srt"
        alternate.symlink_to(path)
    elif problem == "parent_symlink":
        link = tmp_path / "linked"
        link.symlink_to(tmp_path, target_is_directory=True)
        alternate = link / path.name
    elif problem == "traversal":
        alternate = tmp_path / "missing" / ".." / path.name
    else:
        alternate = tmp_path / "fifo.srt"
        os.mkfifo(alternate, 0o600)
    env.inputs[b.source_id] = alternate
    if problem == "fifo":
        assert run(env)["processed_materials"] == 1
    else:
        with pytest.raises(ValueError):
            run(env)
    assert not alternate.is_file() if problem == "fifo" else True


def test_limits_hash_conflict_and_snapshot_binding(env, monkeypatch):
    with pytest.raises(ValueError, match="reserve"):
        run(env, limits=CapacityLimits())
    with pytest.raises(ValueError):
        run(env, limits=env.limits.model_copy(update={"max_materials": 1}))
    monkeypatch.setattr(
        "shutil.disk_usage", lambda _: SimpleNamespace(free=4 * 1024**3)
    )
    assert run(env)["processed_materials"] == 0
    assert not any(env.root.glob("*/receipt.json"))


def test_cli_preview_confirmation_report_output_and_hashes(env, tmp_path, capsys):
    files = {
        "batch.json": {
            "batch": env.batch.model_dump(mode="json"),
            "sha256": api.fingerprint(env.batch.model_dump(mode="json")),
        },
        "limits.json": env.limits.model_dump(mode="json"),
        "approvals.json": env.approvals.model_dump(mode="json"),
        "inputs.json": {s: str(p) for s, p in env.inputs.items()},
    }
    for name, data in files.items():
        (tmp_path / name).write_text(json.dumps(data))
    argv = ["transcripts", "preview", "--archive", str(env.root)]
    for name in ("batch", "limits", "approvals", "inputs"):
        argv += ["--" + name, str(tmp_path / (name + ".json"))]
    assert cli.main(argv) == 0
    capsys.readouterr()
    argv[1] = "import"
    assert cli.main(argv) == 2
    capsys.readouterr()
    output = tmp_path / "report.json"
    assert cli.main([*argv, "--confirm", "--output", str(output)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert json.loads(output.read_text()) == result
    digest = api.sha(output.read_bytes())
    assert cli.main([*argv, "--confirm", "--output", str(output)]) == 2
    assert api.sha(output.read_bytes()) == digest


def test_versioned_inventory_binding_counts_no_transcript_content():
    manifest = (
        Path(__file__).resolve().parents[1] / "docs/course_sources/cs50/manifest.json"
    )
    report = lane.week_inventory(manifest)
    candidates = [r for r in report["references"] if r["reference_kind"] == "candidate"]
    assert len(candidates) == 16 and not report["full_week_coverage"]
    assert sum(r["adapter"] == "offline_official_transcript" for r in candidates) == 2
    assert sum(r["adapter"] == "existing_c18_material" for r in candidates) == 5
    assert any(
        r["format"] == "py" and r["adapter"].startswith("excluded")
        for r in report["references"]
    )
    assert all(r["processing_status"] == "not_processed" for r in report["references"])
    assert not any(
        r["availability"] == "versioned_html_snapshot"
        for r in candidates
        if r["format"] in {"srt", "txt"}
    )
