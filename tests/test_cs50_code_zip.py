"""Synthetic offline integration through the actual material gate and handoff."""

import io
import json
import socket
import stat
import struct
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import cs50_batch as cli
from scripts.cs50_workflow_demo import inputs as demo_inputs
from src.model_materials.materials import NormalizedDocument
from src.tools_lecture.material_handoff import LectureMaterialHandoff
from src.tools_materials import batch as api
from src.tools_materials import code_import as lane
from src.tools_materials import code_structure, code_zip
from src.tools_materials.capacity import MIB, CapacityLimits
from src.tools_materials.processing import make_plan, parser_for

INDEX = "https://cdn.cs50.net/python/2022/x/lectures/0/src0/"


def zipped(entries, *, compression=zipfile.ZIP_DEFLATED):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=compression) as archive:
        for name, content in entries:
            archive.writestr(name, content)
    return out.getvalue()


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("Network forbidden")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


@pytest.fixture
def env(tmp_path, monkeypatch, private_umask):
    tmp_path.chmod(0o700)
    monkeypatch.setattr(
        "shutil.disk_usage", lambda _: SimpleNamespace(free=100 * 1024**3)
    )
    snapshots = tmp_path / "discovery"
    demo_inputs(snapshots)
    week = snapshots / "cs50_python/week0.html"
    week.write_text(
        week.read_text().replace(
            '<a href="/python/2022/src0/hello.py">hello.py</a>',
            f'<a href="{INDEX}">Code</a></li><li><a href="{INDEX[:-1]}.zip">ZIP</a>',
        )
    )
    index = snapshots / "cs50_python/code.html"
    index.write_text(
        "<main>"
        + "".join(
            f'<a href="hello{i}.py{view}">{i}</a>'
            for i in range(3)
            for view in ("", "?download", "?view", "?highlight")
        )
        + "</main>"
    )
    manifest = snapshots / "manifest.json"
    data = json.loads(manifest.read_bytes())
    data["courses"][0]["pages"].append(
        dict(file="cs50_python/code.html", url=INDEX, role="source_code_index")
    )
    for page in data["courses"][0]["pages"]:
        page["sha256"] = api.sha((snapshots / page["file"]).read_bytes())
    manifest.write_text(json.dumps(data))
    plan = make_plan(manifest, include_code_indexes=True)
    code = sorted(
        [b for b in plan.materials if b.format == "py"], key=lambda b: b.original_url
    )
    archive = next(b for b in plan.materials if b.format == "zip")
    assert len(code) == 3
    payloads = [
        (
            '\ufeff"""😀 e\u0301"""\r\nimport math as m\r\nfrom os import path\r\nclass C:\r\n\t"""class doc"""\r\n\tdef f(self):\r\n\t\t"""func doc"""\r\n\t\treturn "héllo"\r\n'
        ).encode(),
        b"def f():\n    return 2\n",
        b'raise RuntimeError("MUST NEVER EXECUTE")\n',
    ]
    raw_zip = zipped(
        [(f"src/hello{i}.py", raw) for i, raw in enumerate(payloads[:2])]
        + [
            ("README.md", b"synthetic README"),
            ("nested.zip", b"not extracted"),
            ("other.py", b"x=1\n"),
        ]
    )
    raw_by_id = {b.source_id: raw for b, raw in zip(code, payloads, strict=True)}
    raw_by_id[archive.source_id] = raw_zip
    grants = []
    refs = {
        n: "synthetic-evidence"
        for n in api.SourceApproval.model_fields
        if n.endswith("_reference")
    }
    for b in [archive, *code]:
        grants.append(
            api.SourceApproval(
                material_id=b.material_id,
                source_id=b.source_id,
                original_url=b.original_url,
                course_id="cs50_python",
                expected_sha256=api.sha(raw_by_id[b.source_id]),
                process=True,
                download=False,
                **refs,
            )
        )
    batch = api.plan(
        manifest,
        ["cs50_python"],
        [b.source_id for b in [archive, *code]],
        synthetic=True,
        include_code_indexes=True,
    )
    zip_path, py_path = tmp_path / "source.zip", tmp_path / "hello2.py"
    zip_path.write_bytes(raw_zip)
    py_path.write_bytes(payloads[2])
    return SimpleNamespace(
        batch=batch,
        manifest=manifest,
        code=code,
        archive=archive,
        raw_by_id=raw_by_id,
        approvals=api.Approvals(sources=tuple(grants)),
        inputs={
            archive.source_id: lane.LocalSource(
                path=zip_path,
                members={
                    "src/hello0.py": code[0].source_id,
                    "src/hello1.py": code[1].source_id,
                },
            ),
            code[2].source_id: lane.LocalSource(path=py_path),
        },
        root=tmp_path / "new-code-archive",
        limits=CapacityLimits(
            reserve_bytes=5 * 1024**3, archive_bytes=64 * MIB, max_materials=8
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


def snapshot(root):
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file()
    }


def test_preview_no_original_reads_or_writes(env, monkeypatch):
    original = lane.read_file

    def checked(path, *args):
        assert Path(path) not in {i.path for i in env.inputs.values()}
        return original(path, *args)

    monkeypatch.setattr(lane, "read_file", checked)
    assert run(env, "preview")["status_counts"] == {"selected": 2}
    assert not env.root.exists()


def test_full_roundtrip_lossless_gate_handoff_archive_relations_resume(env):
    originals = {key: item.path.read_bytes() for key, item in env.inputs.items()}
    result = run(env)
    assert result["processed_materials"] == 4, result
    assert result["status_counts"] == {"processed": 2}
    assert not result["full_week_coverage"] and result["network_requests"] == 0
    before = snapshot(env.root)
    assert all(row["reused"] for row in run(env)["materials"])
    assert snapshot(env.root) == before
    assert originals == {
        key: item.path.read_bytes() for key, item in env.inputs.items()
    }
    reports = [
        json.loads(raw)["receipt"]
        for name, raw in before.items()
        if name.endswith("import.v1.json")
    ]
    archive = next(r for r in reports if r["binding"]["format"] == "zip")
    assert {m["status"] for m in archive["members"]} == {
        "selected",
        "excluded_type",
        "excluded_not_selected",
    }
    for member in archive["members"]:
        if member["status"] == "selected":
            assert member["archive_source_id"] == env.archive.source_id
            assert member["archive_sha256"] == api.sha(originals[env.archive.source_id])
            assert member["sha256"] == api.sha(env.raw_by_id[member["source_id"]])
    for name, raw in before.items():
        if name.endswith("normalized.v1.json"):
            doc = NormalizedDocument.model_validate_json(raw)
            assert "".join(b.text for b in doc.blocks) == env.raw_by_id[
                doc.binding.source_id
            ].decode("utf-8-sig")
            assert [b.location.line_start for b in doc.blocks] == list(
                range(1, len(doc.blocks) + 1)
            )
            assert len(doc.binding.lecture_ids) == 1
        if name.endswith("handoff.v1.json"):
            handoff = LectureMaterialHandoff.model_validate_json(raw)
            assert (
                not handoff.execution_supported and not handoff.knowledge_fact_verified
            )
            assert len(handoff.aggregation_units) == len(handoff.document.blocks)
            assert not handoff.excluded_blocks
        assert str(env.root).encode() not in raw
    for item in env.inputs.values():
        item.path.unlink()
    assert run(env, "report")["processed_materials"] == 4


def test_ast_structure_isolated_no_execution_order_docstrings(env):
    raw = env.raw_by_id[env.code[0].source_id]
    result = code_structure.inspect_structure(raw)
    assert result["status"] == "parsed", result
    assert [e["kind"] for e in result["entries"]] == [
        "Import",
        "ImportFrom",
        "ClassDef",
        "FunctionDef",
    ]
    assert result["entries"][-1]["line_start"] == 6
    assert result["entries"][-1]["docstring"] == "func doc"
    sentinel = env.root.parent / "must-not-exist"
    malicious = f'from pathlib import Path\nPath({str(sentinel)!r}).write_text("executed")\nraise RuntimeError()\n'.encode()
    assert code_structure.inspect_structure(malicious)["status"] == "parsed"
    assert not sentinel.exists()
    assert (
        code_structure.inspect_structure(b"def broken(:\n")["status"] == "syntax_error"
    )
    assert code_structure.inspect_structure(b"x=1\n" * 6000)["status"] == "undetermined"


@pytest.mark.parametrize(
    "problem",
    [
        "approval",
        "process",
        "hash",
        "url",
        "child_hash",
        "missing",
        "zip_corrupt",
        "oversize",
    ],
)
def test_partial_failures_repeat_and_current_grants(env, problem):
    key = env.archive.source_id
    grant_index = next(
        i for i, g in enumerate(env.approvals.sources) if g.source_id == key
    )
    grants = list(env.approvals.sources)
    if problem == "approval":
        grants.pop(grant_index)
    elif problem in {"process", "hash", "url", "child_hash"}:
        if problem == "child_hash":
            grant_index = next(
                i for i, g in enumerate(grants) if g.source_id == env.code[0].source_id
            )
        update = (
            {"process": False}
            if problem == "process"
            else {"original_url": "https://example.org/wrong"}
            if problem == "url"
            else {"expected_sha256": "0" * 64}
        )
        grants[grant_index] = grants[grant_index].model_copy(update=update)
    else:
        path = env.inputs[key].path
        if problem == "missing":
            path.unlink()
        else:
            raw = b"not zip" if problem == "zip_corrupt" else b"X" * (MIB + 1)
            path.write_bytes(raw)
            grants[grant_index] = grants[grant_index].model_copy(
                update={"expected_sha256": api.sha(raw)}
            )
    changed = api.Approvals(sources=tuple(grants))
    result = run(env, approvals=changed)
    assert result["processed_materials"] == 1, result
    assert result["materials"][0]["status"] in {"blocked", "missing"}
    assert not (env.root / env.archive.material_id.split(":")[-1]).exists()
    if problem in {"approval", "process", "hash", "url", "child_hash"}:
        assert run(env)["processed_materials"] == 4


@pytest.mark.parametrize(
    "target",
    [
        "raw/source",
        "import.v1.json",
        "normalized.v1.json",
        "handoff.v1.json",
        "structure.v1.json",
    ],
)
def test_tampered_receipts_raw_outputs_block_without_overwrite(env, target):
    assert run(env)["processed_materials"] == 4
    folder = env.root / env.archive.material_id.split(":")[-1]
    path = (
        folder / target
        if "/" in target or target == "import.v1.json"
        else next(folder.rglob(target))
    )
    path.write_bytes(path.read_bytes() + b" ")
    before = snapshot(env.root)
    assert run(env)["processed_materials"] == 1
    assert snapshot(env.root) == before


def test_interruption_no_adoption_and_partial_resume(env, monkeypatch):
    original = lane.publish_bytes

    def crash(path, data):
        if path.name == "import.v1.json":
            raise OSError("synthetic interrupted publication")
        return original(path, data)

    with monkeypatch.context() as patch:
        patch.setattr(lane, "publish_bytes", crash)
        assert run(env)["processed_materials"] == 0
    before = snapshot(env.root)
    assert run(env)["processed_materials"] == 0
    assert snapshot(env.root) == before


def test_selection_lecture_snapshot_implementation_and_permissions(env, monkeypatch):
    bad = env.batch.model_copy(
        update={
            "materials": tuple(
                b.model_copy(update={"lecture_ids": ()}) for b in env.batch.materials
            )
        }
    )
    with pytest.raises(ValueError):
        lane.run(
            bad, env.root, env.approvals, env.inputs, action="import", limits=env.limits
        )
    assert run(env)["processed_materials"] == 4
    before = snapshot(env.root)
    assert run(env, "report", approvals=api.Approvals())["processed_materials"] == 0
    with monkeypatch.context() as patch:
        patch.setattr(lane, "revision", lambda: "0" * 64)
        assert run(env)["processed_materials"] == 0
    assert snapshot(env.root) == before
    receipt = next(env.root.rglob("import.v1.json"))
    receipt.chmod(0o644)
    assert run(env)["processed_materials"] < 4


@pytest.mark.parametrize(
    "name",
    [
        "../escape.py",
        "/absolute.py",
        "a/../../b.py",
        "a\\b.py",
        "C:/evil.py",
        "./evil.py",
        "a//b.py",
        "a\x00b.py",
    ],
)
def test_zip_unsafe_paths(name):
    # zipfile truncates embedded NUL when writing; mutate bytes to test readers.
    if "\x00" in name:
        raw = zipped([("a_b.py", b"x=1\n")]).replace(b"a_b.py", b"a\x00b.py")
    else:
        raw = zipped([(name, b"x=1\n")])
    with pytest.raises((ValueError, zipfile.BadZipFile)):
        code_zip.inspect_zip(raw)


@pytest.mark.parametrize(
    "mode", [stat.S_IFLNK | 0o777, stat.S_IFIFO | 0o600, stat.S_IFCHR | 0o600]
)
def test_zip_symlinks_specialfiles(mode):
    info = zipfile.ZipInfo("evil.py")
    info.create_system = 3
    info.external_attr = mode << 16
    with pytest.raises(ValueError):
        code_zip.inspect_zip(zipped([(info, b"target")]))


@pytest.mark.parametrize(
    "entries",
    [
        [("same.py", b"a"), ("same.py", b"b")],
        [("Same.py", b"a"), ("same.py", b"b")],
        [("e\u0301.py", b"a"), ("é.py", b"b")],
        [("file", b"a"), ("file/child.py", b"b")],
        [(f"f{i}.py", b"x=1\n") for i in range(65)],
        [("bomb.py", b"x" * MIB)],
        [("oversized.py", b"x" * (MIB + 1))],
    ],
)
def test_zip_collisions_counts_bombs_and_sizes(entries):
    with pytest.raises(ValueError):
        code_zip.inspect_zip(zipped(entries))


def test_zip_crc_encryption_truncated_and_nested_type():
    raw = zipped([("ok.py", b"x=1\n")], compression=zipfile.ZIP_STORED)
    with pytest.raises(zipfile.BadZipFile):
        code_zip.inspect_zip(raw.replace(b"x=1\n", b"x=2\n"))
    compressed = bytearray(zipped([("ok.py", b"x=1\n")]))
    name_length, extra_length = struct.unpack_from("<2H", compressed, 26)
    compressed[30 + name_length + extra_length] = 7  # Reserved deflate block type.
    with pytest.raises(ValueError):
        code_zip.inspect_zip(bytes(compressed))
    bad = bytearray(raw)
    for signature, offset in ((b"PK\x03\x04", 6), (b"PK\x01\x02", 8)):
        pos = raw.index(signature) + offset
        struct.pack_into("<H", bad, pos, 1)
    for data in (bytes(bad), raw[:-1], b"notzip"):
        with pytest.raises((ValueError, zipfile.BadZipFile)):
            code_zip.inspect_zip(data)
    result = code_zip.inspect_zip(
        zipped([("inner.zip", raw), ("binary.py", b"\x00bad"), ("bad.py", b"\xff")])
    )
    assert [m[0]["status"] for m in result] == [
        "excluded_type",
        "excluded_binary_or_empty",
        "excluded_encoding",
    ]


def test_capacity_existing_root_lock_input_symlink_and_size(env, monkeypatch):
    with pytest.raises(ValueError):
        run(env, limits=CapacityLimits())
    with monkeypatch.context() as patch:
        patch.setattr("shutil.disk_usage", lambda _: SimpleNamespace(free=4 * 1024**3))
        assert run(env)["processed_materials"] == 0
    assert run(env)["processed_materials"] == 4
    import fcntl

    with (env.root / ".materials.lock").open("r+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            run(env)
    item = env.inputs[env.archive.source_id]
    link = item.path.with_name("link.zip")
    link.symlink_to(item.path)
    env.inputs[env.archive.source_id] = item.model_copy(update={"path": link})
    with pytest.raises(ValueError):
        run(env)


def test_cli_typed_inputs_hashes_no_overwrite(env, tmp_path, capsys):
    data = {
        "batch": dict(
            batch=env.batch.model_dump(mode="json"),
            sha256=api.fingerprint(env.batch.model_dump(mode="json")),
        ),
        "limits": env.limits.model_dump(mode="json"),
        "approvals": env.approvals.model_dump(mode="json"),
        "inputs": {
            key: value.model_dump(mode="json") for key, value in env.inputs.items()
        },
    }
    for name, value in data.items():
        (tmp_path / (name + ".json")).write_text(json.dumps(value))
    argv = ["code", "preview", "--archive", str(env.root)]
    for name in data:
        argv += ["--" + name, str(tmp_path / (name + ".json"))]
    assert cli.main(argv) == 0
    capsys.readouterr()
    argv[1] = "import"
    assert cli.main(argv) == 2
    capsys.readouterr()
    target = tmp_path / "report.json"
    assert cli.main([*argv, "--confirm", "--output", str(target)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert json.loads(target.read_bytes()) == result
    before = target.read_bytes()
    assert cli.main([*argv, "--confirm", "--output", str(target)]) == 2
    assert target.read_bytes() == before


def test_opt_in_discovery_original_identities_views_and_batch(env, tmp_path):
    legacy = make_plan(env.manifest)
    extended = make_plan(env.manifest, include_code_indexes=True)
    assert extended.materials[: len(legacy.materials)] == legacy.materials
    assert not any(b.format == "py" for b in legacy.materials)
    assert len([b for b in extended.materials if b.format == "py"]) == 3
    for b in env.code:
        assert b.resource.parent_resource_id in {x.source_id for x in legacy.materials}
    assert parser_for(env.archive)[0] is None  # No silent C18 ZIP promotion.
    from src.tools_materials.code_discovery import inventory

    rows = inventory(env.manifest)["references"]
    variants = [r for r in rows if "?" in r["reference"]["original_url"]]
    assert len(variants) == 9 and all(r["binding"] is None for r in variants)
    assert all(r["content_equivalence"] == "not_checked" for r in rows)
    batch_path = tmp_path / "batch.json"
    batch_path.write_bytes(
        lane.json_bytes(
            dict(
                batch=env.batch.model_dump(mode="json"),
                sha256=api.fingerprint(env.batch.model_dump(mode="json")),
            )
        )
    )
    assert api.load_batch(batch_path) == env.batch


@pytest.mark.parametrize("raw", [b"\xff", b"a\x00b", b"   ", b"x" * (MIB + 1)])
def test_invalid_standalone_python_retains_original_and_blocks(env, raw):
    key = env.code[2].source_id
    env.inputs[key].path.write_bytes(raw)
    grants = tuple(
        g.model_copy(update={"expected_sha256": api.sha(raw)})
        if g.source_id == key
        else g
        for g in env.approvals.sources
    )
    result = run(env, approvals=api.Approvals(sources=grants))
    assert result["processed_materials"] == 3
    assert env.inputs[key].path.read_bytes() == raw
    assert not (env.root / env.code[2].material_id.split(":")[-1]).exists()


def test_zip_total_budget_executable_mode_and_empty_directories():
    import random

    pattern = random.Random(42).randbytes(16384)
    raw = zipped([(f"f{i}.py", pattern * 64) for i in range(9)])
    assert len(raw) < MIB
    with pytest.raises(ValueError, match="total size"):
        code_zip.inspect_zip(raw)
    info = zipfile.ZipInfo("executable.py")
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | 0o755) << 16
    result = code_zip.inspect_zip(
        zipped([(info, b"print('no execution')\n"), ("empty/", b"")])
    )
    assert [m[0]["status"] for m in result] == [
        "excluded_executable_mode",
        "excluded_directory",
    ]


@pytest.mark.parametrize(
    "problem",
    [
        "missing_child",
        "duplicate",
        "missing_member",
        "other_lecture",
        "unexpected_directory",
        "existing_root",
    ],
)
def test_explicit_selection_conflicts(env, problem):
    key = env.archive.source_id
    item = env.inputs[key]
    if problem == "existing_root":
        env.root.mkdir(mode=0o700)
        with pytest.raises(FileNotFoundError):
            run(env)
    elif problem == "unexpected_directory":
        assert run(env)["processed_materials"] == 4
        (env.root / env.archive.material_id.split(":")[-1] / "unknown").mkdir(
            mode=0o700
        )
        assert run(env)["processed_materials"] == 1
    elif problem == "missing_member":
        env.inputs[key] = item.model_copy(
            update={
                "members": {
                    "not-there.py": env.code[0].source_id,
                    "src/hello1.py": env.code[1].source_id,
                }
            }
        )
        assert run(env)["processed_materials"] == 1
    else:
        if problem == "missing_child":
            env.inputs[key] = item.model_copy(
                update={"members": {"src/hello0.py": "unknown-source"}}
            )
        elif problem == "duplicate":
            env.inputs[env.code[0].source_id] = lane.LocalSource(path=item.path)
        else:
            env.batch = env.batch.model_copy(
                update={
                    "materials": tuple(
                        b.model_copy(update={"lecture_ids": ("wrong",)})
                        if b.source_id == env.code[0].source_id
                        else b
                        for b in env.batch.materials
                    )
                }
            )
        with pytest.raises(ValueError):
            run(env)


def test_syntax_error_and_worker_failure_are_not_execution(env, monkeypatch):
    monkeypatch.setattr(
        code_structure.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=9, stdout=b""),
    )
    assert (
        code_structure.inspect_structure(b"raise Exception()\n")["status"]
        == "undetermined"
    )
    result = run(env)
    assert result["processed_materials"] == 4
    assert not result["execution_supported"]


def test_zip64_and_unsupported_compression_refused():
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as archive:
        with archive.open("source.py", "w", force_zip64=True) as stream:
            stream.write(b"x=1\n")
    with pytest.raises(ValueError):
        code_zip.inspect_zip(out.getvalue())
    with pytest.raises(ValueError):
        code_zip.inspect_zip(
            zipped([("source.py", b"x=1\n")], compression=zipfile.ZIP_BZIP2)
        )


def test_versioned_week_zero_metadata_inventory():
    from src.tools_materials.code_discovery import inventory

    manifest = (
        Path(__file__).resolve().parents[1] / "docs/course_sources/cs50/manifest.json"
    )
    rows = inventory(manifest)["references"]
    assert len(rows) == 98
    direct = {
        r["source_id"]: r["binding"]
        for r in rows
        if r["binding"] and r["binding"]["format"] == "py"
    }
    assert len(direct) == 24
    assert {b["resource"]["title"] for b in direct.values()} == {
        f"{base}{i}.py" for base in ("calculator", "hello") for i in range(12)
    }
    assert sum("?" in r["reference"]["original_url"] for r in rows) == 72
    assert all(
        r["source_id"] is None for r in rows if "?" in r["reference"]["original_url"]
    )
    assert {tuple(b["lecture_ids"]) for b in direct.values()} == {
        ("resource:4305fcd17cb0d9c50cfdd5e2718461e8369cb883189de96bda796f04cc800192",)
    }
