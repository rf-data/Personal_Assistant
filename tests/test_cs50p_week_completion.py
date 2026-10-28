"""C08 reproducible offline acquisition -> local processing -> evidence verification."""

import io
import json
import shutil
import socket
import zipfile
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from src.tools_materials import week_acquisition as api
from src.tools_materials import week_processing as processing
from tests.test_cs50p_week_acquisition import CDN, PSET, ROOT, WEEK, grant, html, pages


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Real network forbidden during C08 tests")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(
        shutil, "disk_usage", lambda _: SimpleNamespace(free=20 * 1024**3)
    )


def inventory(supplied=None):
    return api.discover(supplied or pages(), source_origin="synthetic", completion=True)


def package(
    name="hello.py",
    code=b"# comment\nclass Example:\n    def answer(self):\n        return 42\n",
):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr(name, code)
    return stream.getvalue()


def pdf():
    import pymupdf

    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "Synthetic slide with page reference")
    return doc.tobytes()


def responder(calls):
    def reply(request):
        url = str(request.url)
        calls.append(url)
        assert not url.endswith((".mp3", ".mp4"))
        if url.endswith(".zip"):
            data, mime = package(), "application/zip"
        elif url.endswith(".py"):
            data, mime = (
                b'# safe static inspection\ndef hello():\n    return "hello"\n',
                "text/x-python",
            )
        elif url.endswith(".pdf"):
            data, mime = pdf(), "application/pdf"
        elif url.endswith(".srt"):
            data, mime = (
                b"1\n00:00:01,250 --> 00:00:04,500\nSynthetic spoken content with timestamps.\n",
                "text/plain",
            )
        elif url.endswith(".txt"):
            data, mime = (
                b"Synthetic lecture transcript sufficient for content validation.\n",
                "text/plain",
            )
        else:
            data, mime = (
                pages().get(url, html("Notes", "<p>Local notes.</p>")),
                "text/html",
            )
        return httpx.Response(200, content=data, headers={"content-type": mime})

    return reply


def acquire(inv, root, calls, ids=None, handler=None, **kwargs):
    # Keep worst-case admission <=32 MiB even with new ZIPs.
    approval = grant(inv, ids, maximum=1048576)
    return api.acquire(
        inv,
        approval,
        root,
        transport=httpx.MockTransport(handler or responder(calls)),
        offline_test=True,
        **kwargs,
    )


def test_source_discovery_zip_python_and_indexes():
    supplied = pages()
    supplied[WEEK] = supplied[WEEK].replace(b"lecture.zip", b"lecture.py")
    supplied[ROOT + "shorts/alpha/"] += b'<a href="ignored.py">Outside main</a>'
    inv = inventory(supplied)
    code = [r for r in inv.materials if r.material_type == "source_code" and r.required]
    assert {r.source_format for r in code} == {"py", "zip"}
    assert all(not r.manual_action_required for r in code)
    assert all(
        g["eligible"]
        for g in api.plan(inv)["grants"]
        if g["material_id"] in {r.material_id for r in code}
    )


def test_zip_and_python_download_dedupe_reuse_and_resume(tmp_path):
    supplied = pages()
    supplied[PSET + "two/"] = html(
        "Two", f'<a href="{CDN}hello.py">Starter</a><a href="{CDN}hello.py">Again</a>'
    )
    inv, calls, root = inventory(supplied), [], tmp_path / "raw"
    ids = [
        r.material_id
        for r in inv.materials
        if r.material_type == "source_code" and r.required
    ]
    done = acquire(inv, root, calls, ids)
    assert len(calls) == len(ids)
    assert all(
        r.acquisition_status == "VERIFIED"
        for r in done.materials
        if r.material_id in ids
    )
    receipts = {p: p.read_bytes() for p in root.rglob("receipt.v1.json")}
    again = acquire(done, root, calls, ids)
    assert len(calls) == len(ids)
    assert receipts == {p: p.read_bytes() for p in root.rglob("receipt.v1.json")}
    resumed = api.resume_discovery(inventory(supplied), again, root)
    assert all(
        r.receipt_id and r.sha256 for r in resumed.materials if r.material_id in ids
    )
    assert api.completeness(resumed, root)["overall"]["manual_complete"]


@pytest.mark.parametrize(
    "bad", ["missing", "unsupported", "oversize", "corrupt", "slip", "symlink", "bomb"]
)
def test_source_failures_are_explicit_and_never_fulfill(tmp_path, bad):
    supplied = pages()
    if bad == "missing":
        supplied[WEEK] = (
            supplied[WEEK]
            .replace(
                b'<a href="' + (CDN + "lecture.zip").encode() + b'">Zip</a>',
                b"Zip (href missing)",
            )
            .replace(
                b'<a href="' + (CDN + "lecture-code.pdf").encode() + b'">PDF</a>',
                b"PDF (href missing)",
            )
        )
    if bad == "unsupported":
        supplied[WEEK] = (
            supplied[WEEK]
            .replace(b"lecture.zip", b"lecture.exe")
            .replace(b"lecture-code.pdf", b"lecture-code.exe")
        )
    inv, root = inventory(supplied), tmp_path / "raw"
    row = next(
        r for r in inv.materials if r.material_type == "source_code" and r.required
    )
    if bad in {"missing", "unsupported"}:
        assert row.acquisition_status in {"MISSING", "MANUAL_PENDING"}
        assert not any(
            g["eligible"]
            for g in api.plan(inv)["grants"]
            if g["material_id"] == row.material_id
        )
        assert api.completeness(inv)["status"] == "HOLD"
        return
    raw = package()
    if bad == "oversize":
        raw = b"x" * (1048576 + 1)
    elif bad == "corrupt":
        raw = raw.replace(b"return 42", b"return 43")
    elif bad == "slip":
        raw = package("../escape.py")
    elif bad == "symlink":
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as z:
            entry = zipfile.ZipInfo("link.py")
            entry.external_attr = 0o120777 << 16
            z.writestr(entry, "target")
        raw = stream.getvalue()
    elif bad == "bomb":
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("huge.py", "x" * 1048576)
        raw = stream.getvalue()
    done = acquire(
        inv,
        root,
        [],
        [row.material_id],
        handler=lambda _: httpx.Response(
            200, content=raw, headers={"content-type": "application/zip"}
        ),
    )
    failed = next(r for r in done.materials if r.material_id == row.material_id)
    assert failed.acquisition_status == "FAILED"
    assert not (root / row.expected_local_path).exists()
    assert api.completeness(done, root)["status"] == "HOLD"


@pytest.mark.parametrize(
    "body", [b"", b"WEBVTT\n\n", b"1\n00:00:00,000 --> 00:00:01,000\n"]
)
def test_empty_or_broken_subtitles_fall_back_per_short(tmp_path, body):
    inv = inventory()
    row = next(
        r for r in inv.materials if r.material_type == "subtitles" and r.selected
    )
    done = acquire(
        inv,
        tmp_path / "raw",
        [],
        [row.material_id],
        handler=lambda _: httpx.Response(
            200, content=body, headers={"content-type": "text/plain"}
        ),
    )
    chosen = next(
        r
        for r in done.materials
        if r.selected and r.alternative_group == row.alternative_group
    )
    assert chosen.material_type == "audio"
    assert not next(
        g for g in api.plan(done)["grants"] if g["material_id"] == chosen.material_id
    )["eligible"]
    assert api.completeness(done)["status"] == "HOLD"


def test_e2e_download_then_processing_and_second_identical_run(tmp_path):
    inv, calls, root, output = inventory(), [], tmp_path / "raw", tmp_path / "processed"
    done = acquire(inv, root, calls)
    report = api.completeness(done, root)
    assert report["overall"]["acquisition_complete"]
    assert report["overall"]["manual_complete"]
    assert not report["overall"]["processing_complete"]
    assert report["status"] == "HOLD"
    before = {p: p.read_bytes() for p in root.rglob("receipt.v1.json")}
    result = processing.process(done, root, output, offline_test=True)
    assert all(r["status"] == "COMPLETED" for r in result["materials"]), result
    complete = api.completeness(done, root, output)
    assert complete["status"] == "FULLY_COMPLETE", complete
    assert complete["c26_status"] == "HOLD"
    assert all(s["processing_complete"] for s in complete["sections"].values())
    assert before == {p: p.read_bytes() for p in root.rglob("receipt.v1.json")}
    again = acquire(done, root, calls)
    repeated = processing.process(again, root, output, offline_test=True)
    assert all(r["reused"] for r in repeated["materials"])
    assert len(calls) == len(set(calls))
    results = [json.loads(p.read_bytes()) for p in output.rglob("result.json")]
    html_doc = next(
        r
        for r in results
        if r["kind"] == "normalized_document"
        and r["document"]["parser"]["name"] == "html"
    )
    assert html_doc["source_url"] and html_doc["raw_sha256"] and html_doc["section_id"]
    assert any(b["location"]["dom"] for b in html_doc["document"]["blocks"])
    pdf_doc = next(
        r
        for r in results
        if r["kind"] == "normalized_document"
        and r["document"]["parser"]["name"] == "pdf"
    )
    assert any(b["location"]["page"] == 1 for b in pdf_doc["document"]["blocks"])
    timed = next(
        r
        for r in results
        if r["kind"] == "transcript" and r["source_url"].endswith(".srt")
    )
    assert timed["document"]["segments"][0]["start"] == 1.25
    assert timed["document"]["segments"][0]["end"] == 4.5
    code = next(r for r in results if r["kind"] == "source_archive")
    member = code["members"][0]
    assert member["name"] == "hello.py"
    assert {e["kind"] for e in member["static"]["structure"]["entries"]} == {
        "ClassDef",
        "FunctionDef",
    }
    assert member["static"]["comments"]
    assert not list(root.rglob("hello.py"))


def test_processing_failure_cannot_destroy_successful_acquisition(tmp_path):
    inv, root, output = inventory(), tmp_path / "raw", tmp_path / "processed"

    def invalid_pdf(req):
        if str(req.url).endswith(".pdf"):
            return httpx.Response(
                200,
                content=b"%PDF-this is corrupt",
                headers={"content-type": "application/pdf"},
            )
        return responder([])(req)

    done = acquire(inv, root, [], handler=invalid_pdf)
    assert api.completeness(done, root)["overall"]["acquisition_complete"]
    result = processing.process(done, root, output, offline_test=True)
    assert any(r["status"] == "FAILED" for r in result["materials"])
    report = api.completeness(done, root, output)
    assert report["overall"]["acquisition_complete"]
    assert not report["overall"]["processing_complete"]
    assert report["status"] == "HOLD"


def test_static_python_is_never_executed(tmp_path):
    marker = tmp_path / "MUST_NOT_EXIST"
    raw = f'from pathlib import Path\nPath({str(marker)!r}).write_text("executed")\n# comment\ndef f():\n    pass\n'.encode()
    result = processing._static(raw, "py")
    assert result["structure"]["status"] == "parsed"
    assert not marker.exists()


def test_production_execution_gate_and_forged_statuses(tmp_path):
    inv = inventory()
    with pytest.raises(PermissionError, match="isolation"):
        processing.process(inv, tmp_path / "raw", tmp_path / "processed")
    with pytest.raises(PermissionError):
        processing.process(
            inv.model_copy(update={"source_origin": "official"}),
            tmp_path / "raw",
            tmp_path / "processed",
            offline_test=True,
        )
    forged = inv.model_copy(
        update={
            "materials": tuple(
                r.model_copy(update={"acquisition_status": "VERIFIED"})
                if r.required and r.material_type not in api.CONTAINERS
                else r
                for r in inv.materials
            )
        }
    )
    assert (
        api.completeness(forged, tmp_path / "raw", tmp_path / "processed")["status"]
        == "HOLD"
    )


def test_processing_output_tampering_detected(tmp_path):
    done = acquire(inventory(), tmp_path / "raw", [])
    processing.process(
        done, tmp_path / "raw", tmp_path / "processed", offline_test=True
    )
    target = next((tmp_path / "processed").rglob("result.json"))
    target.write_bytes(b"{}")
    report = api.completeness(done, tmp_path / "raw", tmp_path / "processed")
    assert report["status"] == "HOLD"
    assert report["overall"]["processing_missing"]


def test_problem_set_material_tree_and_reference_fragments():
    supplied = pages()
    supplied[PSET + "one/"] = html(
        "One",
        f'<pre><code>def starter():\n    pass</code></pre><a href="{CDN}starter.py">Starter</a><a href="{CDN}data.csv">Data</a><a href="https://docs.python.org/3/#input">Reference</a>',
    )
    inv = inventory(supplied)
    task = next(
        r
        for r in inv.materials
        if r.material_type == "task" and r.source_url.endswith("one/")
    )
    children = [r for r in inv.materials if r.parent_material_id == task.material_id]
    assert {r.material_type for r in children} == {
        "page",
        "source_code",
        "attachment",
        "reference",
    }
    assert any(r.metadata.get("original_href", "").endswith("#input") for r in children)


def test_shared_source_url_reuses_receipt_across_different_owners(tmp_path):
    supplied = pages()
    supplied[PSET + "one/"] = html("One", f'<a href="{CDN}shared.py">First label</a>')
    supplied[PSET + "two/"] = html(
        "Two", f'<a href="{CDN}shared.py">Different label</a>'
    )
    inv, root, calls = inventory(supplied), tmp_path / "raw", []
    ids = [r.material_id for r in inv.materials if r.source_url == CDN + "shared.py"]
    done = acquire(inv, root, calls, ids)
    sources = [r for r in done.materials if r.material_id in ids]
    assert len(sources) == 2 and len(calls) == 1
    assert all(r.acquisition_status == "VERIFIED" for r in sources)
    assert sources[0].receipt_id == sources[1].receipt_id
    assert sources[0].parent_material_id != sources[1].parent_material_id


def test_index_only_source_files_discovered_from_exact_hrefs():
    supplied = pages()
    supplied[WEEK] = (
        supplied[WEEK]
        .replace(b"lecture.zip", b"index/")
        .replace(b"lecture-code.pdf", b"index/")
    )
    supplied[CDN + "index/"] = (
        b'<html><a href="a.py">A</a><a href="a.py">Duplicate</a><a href="../escape.py">Parent</a></html>'
    )
    inv = inventory(supplied)
    files = [r for r in inv.materials if r.source_url == CDN + "index/a.py"]
    assert len(files) == 1 and files[0].required
    assert not any(r.source_url == CDN + "escape.py" for r in inv.materials)
    assert files[0].discovered_from == (CDN + "index/",)


def test_transcript_failure_falls_back_independently(tmp_path):
    inv = inventory()
    row = next(
        r
        for r in inv.materials
        if r.material_type == "transcript"
        and r.selected
        and r.parent_material_id
        == next(
            c.material_id
            for c in inv.materials
            if c.material_type == "short" and c.title == "Beta"
        )
    )
    done = acquire(
        inv,
        tmp_path / "raw",
        [],
        [row.material_id],
        handler=lambda _: httpx.Response(404),
    )
    chosen = next(
        r
        for r in done.materials
        if r.selected and r.alternative_group == row.alternative_group
    )
    assert chosen.material_type == "audio"
    lecture = next(r for r in done.materials if r.material_type == "lecture")
    assert (
        next(
            r
            for r in done.materials
            if r.selected and r.alternative_group == lecture.material_id
        ).material_type
        == "transcript"
    )


def test_processing_receipt_publication_interruption_can_resume(tmp_path, monkeypatch):
    done = acquire(inventory(), tmp_path / "raw", [])
    original, interrupted = processing.publish_bytes, False

    def publish(path, data):
        nonlocal interrupted
        if path.name == "receipt.json" and not interrupted:
            interrupted = True
            raise KeyboardInterrupt
        original(path, data)

    monkeypatch.setattr(processing, "publish_bytes", publish)
    with pytest.raises(KeyboardInterrupt):
        processing.process(
            done, tmp_path / "raw", tmp_path / "processed", offline_test=True
        )
    monkeypatch.setattr(processing, "publish_bytes", original)
    result = processing.process(
        done, tmp_path / "raw", tmp_path / "processed", offline_test=True
    )
    assert all(r["status"] == "COMPLETED" for r in result["materials"])
    assert (
        api.completeness(done, tmp_path / "raw", tmp_path / "processed")["status"]
        == "FULLY_COMPLETE"
    )


def test_expected_ledger_prevents_required_or_parent_downgrade(tmp_path):
    done = acquire(inventory(), tmp_path / "raw", [])
    row = next(
        r for r in done.materials if r.material_type == "source_code" and r.required
    )
    downgraded = done.model_copy(
        update={
            "materials": tuple(
                r.model_copy(update={"required": False})
                if r.material_id == row.material_id
                else r
                for r in done.materials
            )
        }
    )
    report = api.completeness(downgraded, tmp_path / "raw")
    assert row.material_id in report["overall"]["processing_missing"]
    reparented = done.model_copy(
        update={
            "materials": tuple(
                r.model_copy(
                    update={"parent_material_id": done.materials[0].material_id}
                )
                if r.material_id == row.material_id
                else r
                for r in done.materials
            )
        }
    )
    assert (
        row.material_id
        in api.completeness(reparented, tmp_path / "raw")["overall"][
            "missing_expected_ids"
        ]
    )


@pytest.mark.parametrize("kind", ["audio", "video"])
def test_media_candidate_never_bypasses_source_grants(tmp_path, kind):
    inv = inventory()
    lecture = next(r for r in inv.materials if r.material_type == "lecture")
    inv = inv.model_copy(
        update={
            "materials": tuple(
                r.model_copy(update={"acquisition_status": "BLOCKED"})
                if r.alternative_group == lecture.material_id
                and r.acquisition_priority < api.CONTENT[kind]
                else r
                for r in inv.materials
            )
        }
    )
    inv = api.select_fallbacks(inv)
    chosen = next(
        r
        for r in inv.materials
        if r.alternative_group == lecture.material_id and r.selected
    )
    assert chosen.material_type == kind
    from src.model_materials.acquisition import SourceGrant

    approval = grant(inv, []).model_copy(
        update={
            "grants": (
                SourceGrant(
                    material_id=chosen.material_id,
                    source_url=chosen.source_url,
                    source_format=chosen.source_format,
                    max_bytes=100,
                    license_reviewed=True,
                ),
            )
        }
    )
    with pytest.raises(PermissionError, match="media"):
        api.acquire(
            inv,
            approval,
            tmp_path / "raw",
            transport=httpx.MockTransport(
                lambda _: pytest.fail("No media transfer allowed")
            ),
            offline_test=True,
        )


def test_single_python_processing_and_vtt_times(tmp_path):
    supplied = pages()
    supplied[PSET + "one/"] = html("One", f'<a href="{CDN}starter.py">Starter code</a>')
    supplied[ROOT + "shorts/alpha/"] = supplied[ROOT + "shorts/alpha/"].replace(
        b"alpha.srt", b"alpha.vtt"
    )
    inv = inventory(supplied)

    def response(req):
        if str(req.url).endswith(".vtt"):
            return httpx.Response(
                200,
                content=b"WEBVTT\n\n00:01.000 --> 00:03.500\nSynthetic subtitle text preserves timing.\n",
                headers={"content-type": "text/vtt"},
            )
        return responder([])(req)

    done = acquire(inv, tmp_path / "raw", [], handler=response)
    result = processing.process(
        done, tmp_path / "raw", tmp_path / "processed", offline_test=True
    )
    assert all(r["status"] == "COMPLETED" for r in result["materials"]), result
    results = [
        json.loads(p.read_bytes())
        for p in (tmp_path / "processed").rglob("result.json")
    ]
    code = next(r for r in results if r["source_url"].endswith(".py"))
    assert code["document"]["metadata"]["programming_language"] == "python"
    assert code["static"]["structure"]["entries"][0]["name"] == "hello"
    vtt = next(r for r in results if r["source_url"].endswith(".vtt"))
    assert vtt["document"]["segments"][0]["end"] == 3.5


def test_genuinely_unresolved_source_can_use_explicit_manual_export(tmp_path):
    supplied = pages()
    supplied[WEEK] = (
        supplied[WEEK]
        .replace(b"lecture.zip", b"unsupported.exe")
        .replace(b"lecture-code.pdf", b"unsupported.exe")
    )
    inv = inventory(supplied)
    row = next(
        r for r in inv.materials if r.material_type == "source_code" and r.required
    )
    manual = api.manual_fallback(
        inv,
        row.material_id,
        source_format="zip",
        filename="reviewed.zip",
        provenance="Operator reviewed local export after unsupported official offer",
    )
    selected = next(r for r in manual.materials if r.material_id == row.material_id)
    assert selected.metadata["source_url_is_context"]
    assert selected.source_url == WEEK
    assert not next(
        g for g in api.plan(manual)["grants"] if g["material_id"] == row.material_id
    )["eligible"]
    assert row.material_id in api.completeness(manual)["overall"]["manual_pending"]
    source = tmp_path / "reviewed.zip"
    source.write_bytes(package())
    done = api.import_manual(
        manual,
        row.material_id,
        source,
        api.sha(source.read_bytes()),
        tmp_path / "raw",
        provenance="Manually reviewed synthetic export",
    )
    assert api.completeness(done, tmp_path / "raw")["overall"]["manual_complete"]
    assert (
        next(
            r for r in done.materials if r.material_id == row.material_id
        ).acquisition_status
        == "MANUAL_VERIFIED"
    )


def test_malformed_processing_receipt_is_a_finding_not_success(tmp_path):
    done = acquire(inventory(), tmp_path / "raw", [])
    processing.process(
        done, tmp_path / "raw", tmp_path / "processed", offline_test=True
    )
    receipt = next((tmp_path / "processed").rglob("receipt.json"))
    receipt.write_bytes(b"[]")
    report = api.completeness(done, tmp_path / "raw", tmp_path / "processed")
    assert report["status"] == "HOLD"
    assert not report["overall"]["processing_complete"]


@pytest.mark.parametrize("script", ["week_runtime_smoke.py", "week_source_smoke.py"])
def test_fresh_download_only_process_has_no_c16_or_processing_import(script):
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            str(root / "deployment/cs50p-download-only" / script),
            "--source",
            str(root),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["reused"]
