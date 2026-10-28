"""Synthetic end-to-end week acquisition. No DNS, HTTP, C16 or host changes."""

import fcntl
import json
import shutil
import socket
import zipfile
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from scripts.cs50p_week import main
from src.job_control.models import fingerprint
from src.model_materials.acquisition import AcquisitionLimits, SourceGrant, WeekApproval
from src.tools_materials import week_acquisition as api

ROOT = "https://cs50.harvard.edu/python/"
CDN = "https://cdn.cs50.net/python/synthetic/"
WEEK = ROOT + "weeks/0/"
PSET = ROOT + "psets/0/"


def html(title, body):
    return f"<main><h1>{title}</h1>{body}</main>".encode()


def sources(name, text=True, subtitles=True, code=True):
    parts = [
        f'<li>Audio<ul><li><a href="{CDN}{name}.mp3">MP3</a></li></ul></li>',
        f'<li>Video<ul><li><a href="{CDN}{name}.mp4">360p</a></li></ul></li>',
    ]
    if text:
        parts.append(f'<li><a href="{CDN}{name}.txt">Transcript</a></li>')
    if subtitles:
        parts.append(f'<li><a href="{CDN}{name}.srt">Subtitles</a></li>')
    if code:
        parts.append(
            f'<li>Source Code<ul><li><a href="{CDN}{name}.zip">Zip</a></li><li><a href="{CDN}{name}-code.pdf">PDF</a></li></ul></li>'
        )
    return "".join(parts)


def pages(
    *,
    lecture_text=True,
    lecture_subtitles=True,
    missing_short=False,
    missing_task=False,
):
    week_body = (
        f"<ul><li>Lecture<ul>{sources('lecture', lecture_text, lecture_subtitles)}"
        f'<li><a href="{ROOT}notes/0/">Notes</a></li>'
        f'<li>Slides<ul><li><a href="{CDN}slides.pdf">PDF</a></li></ul></li></ul></li>'
        f'<li>Shorts<ol><li><a href="{ROOT}shorts/alpha/">Alpha</a></li>'
        f'<li><a href="{ROOT}shorts/beta/">Beta</a></li>'
        f'<li><a href="{ROOT}shorts/alpha/">Alpha duplicate</a></li></ol></li>'
        f'<li><a href="{PSET}">Problem Set 0</a></li></ul>'
    )
    result = {
        WEEK: html("Week 0 Functions", week_body),
        ROOT + "shorts/alpha/": html(
            "Alpha", f"<ul>{sources('alpha', text=False)}</ul>"
        ),
        ROOT + "shorts/beta/": html(
            "Beta", f"<ul>{sources('beta', subtitles=False, code=False)}</ul>"
        ),
        PSET: html(
            "Problem Set 0",
            '<ul><li><a href="one/">One</a></li><li><a href="two/">Two</a></li></ul>',
        ),
        PSET + "one/": html(
            "One",
            '<p>Task description one, with explicit inputs.</p><a href="https://docs.python.org/">Reference</a>',
        ),
        PSET + "two/": html(
            "Two",
            '<p>Task description two, with starter file.</p><a href="https://cdn.cs50.net/python/synthetic/input.txt">Dataset</a>',
        ),
        ROOT + "notes/0/": html("Notes", "<p>Synthetic lecture notes.</p>"),
    }
    if missing_short:
        del result[ROOT + "shorts/alpha/"]
    if missing_task:
        del result[PSET + "two/"]
    return result


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Real network access forbidden")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    # Explicit synthetic host model; actual host free disk is below the 5 GiB reserve.
    monkeypatch.setattr(
        shutil, "disk_usage", lambda _: SimpleNamespace(free=20 * 1024**3)
    )


def inventory(**kwargs):
    return api.discover(pages(**kwargs), source_origin="synthetic")


def grant(inv, ids=None, *, maximum=None, transfer=None):
    candidates = [
        r
        for r in api.plan(inv)["grants"]
        if r["eligible"] and (ids is None or r["material_id"] in ids)
    ]
    grants = tuple(
        SourceGrant(
            material_id=r["material_id"],
            source_url=r["source_url"],
            source_format=r["source_format"],
            max_bytes=maximum or r["max_bytes"],
            license_reviewed=True,
        )
        for r in candidates
    )
    return WeekApproval(
        inventory_sha256=fingerprint(inv.model_dump(mode="json")),
        source_origin="synthetic",
        reviewed_by="Synthetic test operator",
        review_reference="offline-only",
        transfer_bytes=transfer or inv.limits.transfer_bytes,
        grants=grants,
    )


def handler(calls, *, bad=None):
    def respond(request):
        url = str(request.url)
        calls.append(url)
        assert not url.endswith((".mp3", ".mp4", ".zip"))
        if bad:
            return bad(request)
        if url.endswith(".srt"):
            return httpx.Response(
                200,
                content=b"1\n00:00:00,000 --> 00:00:02,000\nSynthetic spoken content from a short.\n",
                headers={"content-type": "text/plain"},
            )
        if url.endswith(".txt"):
            return httpx.Response(
                200,
                content=b"Synthetic official language content for a lecture or assignment.\n",
                headers={"content-type": "text/plain"},
            )
        if url.endswith(".pdf"):
            return httpx.Response(
                200,
                content=b"%PDF-synthetic bytes; never parsed",
                headers={"content-type": "application/pdf"},
            )
        return httpx.Response(
            200,
            content=pages().get(url, html("Notes", "<p>Synthetic notes.</p>")),
            headers={"content-type": "text/html"},
        )

    return respond


def run(inv, root, calls, ids=None, **kwargs):
    return api.acquire(
        inv,
        grant(inv, ids),
        root,
        transport=httpx.MockTransport(handler(calls)),
        offline_test=True,
        **kwargs,
    )


def test_full_week_receipts_manual_import_reuse_and_reports(tmp_path):
    inv = inventory()
    report = api.completeness(inv)
    assert report["counts"] == {"lecture": 1, "short": 2, "task": 2}
    assert report["overall"]["discovery_complete"]
    assert not report["overall"]["acquisition_complete"]
    assert not report["overall"]["manual_complete"]
    assert inv.processing_enabled is False
    calls, root = [], tmp_path / "archive"
    saved = []
    done = run(inv, root, calls, checkpoint=saved.append)
    assert saved
    report = api.completeness(done, root)
    assert report["overall"]["acquisition_complete"], report
    assert report["status"] == "HOLD"
    assert len(calls) == len(
        set(calls)
    )  # duplicate lecture/week page uses the same verified receipt
    again = run(done, root, calls)
    assert [(r.sha256, r.file_size) for r in again.materials] == [
        (r.sha256, r.file_size) for r in done.materials
    ]
    assert len(calls) == len(set(calls))
    source = tmp_path / "manual.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("hello.py", "print('synthetic')")
    for row in done.materials:
        if row.manual_action_required:
            done = api.import_manual(
                done,
                row.material_id,
                source,
                api.sha(source.read_bytes()),
                root,
                provenance="Operator obtained synthetic test package",
            )
    report = api.completeness(done, root)
    assert report["status"] == "HOLD", report
    assert not report["overall"]["processing_complete"]
    assert report["c26_status"] == "HOLD"
    assert all(s["acquisition_complete"] for s in report["sections"].values())
    manual = next(r for r in done.materials if r.manual_action_required)
    raw = root / manual.expected_local_path
    before = raw.read_bytes()
    with pytest.raises(ValueError):
        api.import_manual(
            done, manual.material_id, source, "0" * 64, root, provenance="Wrong hash"
        )
    assert raw.read_bytes() == before
    raw.write_bytes(b"corrupted")
    assert api.completeness(done, root)["status"] == "HOLD"


@pytest.mark.parametrize(
    "text,subtitles,selected",
    [(True, True, "transcript"), (False, True, "subtitles"), (False, False, "audio")],
)
def test_lecture_fallback_priority(text, subtitles, selected):
    inv = inventory(lecture_text=text, lecture_subtitles=subtitles)
    lecture = next(r for r in inv.materials if r.material_type == "lecture")
    alternatives = [
        r for r in inv.materials if r.alternative_group == lecture.material_id
    ]
    assert [r.material_type for r in alternatives if r.selected] == [selected]
    assert not any(r.required for r in alternatives)
    if selected == "audio":
        assert not any(
            g["eligible"]
            for g in api.plan(inv)["grants"]
            if g["source_format"] in {"mp3", "mp4"}
        )


def test_shorts_fallback_independent_and_not_masked_by_lecture(tmp_path):
    inv = inventory()
    chosen = {
        next(
            r for r in inv.materials if r.material_id == s.parent_material_id
        ).title: s.material_type
        for s in inv.materials
        if s.alternative_group and s.selected
    }
    assert chosen["Alpha"] == "subtitles"
    assert chosen["Beta"] == "transcript"
    lecture_text = next(
        r
        for r in inv.materials
        if r.material_type == "transcript" and "lecture" in (r.source_url or "")
    )
    done = run(inv, tmp_path / "archive", [], [lecture_text.material_id])
    report = api.completeness(done, tmp_path / "archive")
    shorts = [s for s in report["sections"].values() if s["material_type"] == "short"]
    assert all(not s["acquisition_complete"] for s in shorts)


@pytest.mark.parametrize("case", ["missing_task", "missing_short"])
def test_missing_detail_is_explicit(case):
    inv = inventory(**{case: True})
    report = api.completeness(inv)
    assert report["overall"]["discovery_missing"]
    assert any(r.acquisition_status == "MISSING" for r in inv.materials)
    assert not report["overall"]["discovery_complete"]


def test_deleted_single_task_detected_by_expectation_ledger():
    inv = inventory()
    task = next(r for r in inv.materials if r.material_type == "task")
    removed = {
        r.material_id for r in inv.materials if r.parent_material_id == task.material_id
    } | {task.material_id}
    damaged = inv.model_copy(
        update={
            "materials": tuple(r for r in inv.materials if r.material_id not in removed)
        }
    )
    report = api.completeness(damaged)
    assert task.material_id in report["overall"]["missing_expected_ids"]
    assert report["status"] == "HOLD"


@pytest.mark.parametrize(
    "failure",
    [
        "http",
        "redirect",
        "dns",
        "tls",
        "oversize",
        "mime",
        "html_text",
        "empty",
        "subtitle",
    ],
)
def test_failed_transfers_do_not_publish_or_fulfill(tmp_path, failure):
    inv = inventory()
    row = next(
        r
        for r in inv.materials
        if r.material_type == ("subtitles" if failure == "subtitle" else "transcript")
        and r.selected
    )

    def bad(request):
        if failure in {"dns", "tls"}:
            raise httpx.ConnectError("Synthetic DNS/TLS failure", request=request)
        if failure == "http":
            return httpx.Response(404)
        if failure == "redirect":
            return httpx.Response(302, headers={"location": "http://127.0.0.1/secret"})
        body = {
            "oversize": b"x" * 200,
            "mime": b"text",
            "html_text": b"<!doctype html><html>Error</html>",
            "empty": b"",
            "subtitle": b"Broken subtitle without timing",
        }.get(failure, b"")
        return httpx.Response(
            200,
            content=body,
            headers={
                "content-type": "application/json"
                if failure == "mime"
                else "text/plain"
            },
        )

    root = tmp_path / "archive"
    done = api.acquire(
        inv,
        grant(inv, [row.material_id], maximum=100),
        root,
        transport=httpx.MockTransport(bad),
        offline_test=True,
    )
    result = next(r for r in done.materials if r.material_id == row.material_id)
    assert result.acquisition_status == "FAILED", result
    assert not (root / row.expected_local_path).exists()
    assert not list(root.rglob(".download-*"))
    assert not api.completeness(done, root)["overall"]["acquisition_complete"]
    assert any(
        r.selected and r.acquisition_priority > row.acquisition_priority
        for r in done.materials
        if r.alternative_group == row.alternative_group
    )


def test_size_and_transfer_admission_then_midstream_budget(tmp_path):
    inv = inventory()
    row = next(
        r for r in inv.materials if r.material_type == "transcript" and r.selected
    )
    approval = grant(inv, [row.material_id], maximum=100, transfer=99)
    with pytest.raises(ValueError, match="worst-case"):
        api.acquire(
            inv,
            approval,
            tmp_path / "archive",
            transport=httpx.MockTransport(handler([])),
            offline_test=True,
        )
    from scripts.cs50p_mvp import TransferBudget

    budget = TransferBudget(
        httpx.MockTransport(lambda req: httpx.Response(200, content=b"x" * 100)), 10
    )
    with (
        httpx.Client(transport=budget) as client,
        pytest.raises(ValueError, match="transfer budget"),
    ):
        client.get(row.source_url)


def test_interruption_checkpoint_resume_and_explicit_retry(tmp_path):
    inv, root, checkpoints = inventory(), tmp_path / "archive", []
    count = 0

    def interrupt(request):
        nonlocal count
        count += 1
        if count == 2:
            raise KeyboardInterrupt
        return handler([])(request)

    with pytest.raises(KeyboardInterrupt):
        api.acquire(
            inv,
            grant(inv),
            root,
            transport=httpx.MockTransport(interrupt),
            offline_test=True,
            checkpoint=checkpoints.append,
        )
    assert checkpoints
    # A receipt for the interrupted source remains selected; no byte adoption.
    recovered = run(checkpoints[-1], root, [], retry_failed=True)
    assert api.completeness(recovered, root)["overall"]["acquisition_complete"]


def test_forged_approval_synthetic_production_and_media_rejected(tmp_path):
    inv = inventory()
    with pytest.raises(PermissionError, match="Production"):
        api.acquire(inv, grant(inv), tmp_path / "archive")
    with pytest.raises(PermissionError, match="bind"):
        api.acquire(
            inv,
            grant(inv).model_copy(update={"inventory_sha256": "0" * 64}),
            tmp_path / "archive",
            offline_test=True,
            transport=httpx.MockTransport(handler([])),
        )
    media = next(r for r in inv.materials if r.material_type == "audio")
    approval = grant(inv).model_copy(
        update={
            "grants": (
                SourceGrant(
                    material_id=media.material_id,
                    source_url=media.source_url,
                    source_format="mp3",
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
            tmp_path / "archive",
            offline_test=True,
            transport=httpx.MockTransport(handler([])),
        )


def test_lock_unknown_partial_and_no_overwrite(tmp_path):
    inv, root = inventory(), tmp_path / "archive"
    root.mkdir(mode=0o700)
    with (root / ".mvp-download.lock").open("w") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            run(inv, root, [])
    partial = root / ".download-unknown"
    partial.write_bytes(b"evidence")
    with pytest.raises(ValueError, match="partial"):
        run(inv, root, [])
    assert partial.read_bytes() == b"evidence"


def test_real_disk_reserve_is_not_lowered(tmp_path, monkeypatch):
    monkeypatch.setattr(
        shutil, "disk_usage", lambda _: SimpleNamespace(free=4 * 1024**3)
    )
    with pytest.raises(ValueError, match="reserve"):
        run(inventory(), tmp_path / "archive", [])
    with pytest.raises(ValueError):
        AcquisitionLimits(reserve_bytes=1)
    with pytest.raises(ValueError):
        AcquisitionLimits(transfer_bytes=64 * 1024**2)


@pytest.mark.parametrize(
    "url",
    [
        "http://cs50.harvard.edu/python/",
        "https://127.0.0.1/",
        "https://cs50.harvard.edu:444/python/",
        "https://user:pass@cs50.harvard.edu/python/",
        "https://cs50.harvard.edu/python/%252e%252e/secret",
        "https://cs50.harvard.edu/python/a?token=x",
    ],
)
def test_ssrf_url_admission(url):
    with pytest.raises((ValueError, PermissionError)):
        api.checked_url(url)


def test_cli_discovery_plan_report_and_exclusive_output(tmp_path):
    config = {
        "course_id": "cs50_python",
        "week_id": "0",
        "source_origin": "synthetic",
        "pages": [],
    }
    for i, (url, raw) in enumerate(pages().items()):
        path = tmp_path / f"page-{i}.html"
        path.write_bytes(raw)
        config["pages"].append(dict(url=url, path=path.name, sha256=api.sha(raw)))
    snapshots = tmp_path / "snapshots.json"
    snapshots.write_text(json.dumps(config))
    target = tmp_path / "inventory.json"
    assert (
        main(["discover", "--snapshots", str(snapshots), "--output", str(target)]) == 0
    )
    assert (
        main(["discover", "--snapshots", str(snapshots), "--output", str(target)]) == 2
    )
    for command in ("plan", "manual-list"):
        assert (
            main(
                [
                    command,
                    "--inventory",
                    str(target),
                    "--output",
                    str(tmp_path / (command + ".json")),
                ]
            )
            == 0
        )
    assert (
        main(
            [
                "report",
                "--inventory",
                str(target),
                "--archive",
                str(tmp_path / "archive"),
                "--output",
                str(tmp_path / "report.json"),
            ]
        )
        == 0
    )
    assert not (tmp_path / "archive").exists()


def test_no_worker_import_or_call_in_download_only_modules():
    import ast

    for name in (
        "src/tools_materials/week_acquisition.py",
        "scripts/cs50p_week.py",
        "src/tools_materials/text_validation.py",
    ):
        tree = ast.parse(Path(name).read_text())
        imports = [
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        ]
        assert not any(
            x in imports
            for x in (
                "scripts.cs50_worker",
                "src.job_control.controller",
                "src.job_control.native_admission",
            )
        )
        assert (
            "processing_enabled=False"
            in Path("src/tools_materials/week_acquisition.py").read_text()
        )


def test_approved_discovery_and_rediscovery_adds_missing_short_and_task(tmp_path):
    initial_pages = {WEEK: pages()[WEEK]}
    inv = api.discover(initial_pages, source_origin="synthetic")
    page_ids = [r.material_id for r in inv.materials if r.material_type == "page"]
    approval = grant(inv, page_ids)
    approval = approval.model_copy(
        update={
            "grants": tuple(
                g.model_copy(update={"purpose": "discovery"}) for g in approval.grants
            )
        }
    )
    calls = []
    root = tmp_path / "archive"
    done = api.acquire(
        inv,
        approval,
        root,
        purpose="discovery",
        transport=httpx.MockTransport(handler(calls)),
        offline_test=True,
    )
    config = {
        "course_id": "cs50_python",
        "week_id": "0",
        "source_origin": "synthetic",
        "pages": [{"url": WEEK, "path": "week.html", "sha256": api.sha(pages()[WEEK])}],
    }
    (tmp_path / "week.html").write_bytes(pages()[WEEK])
    (tmp_path / "snapshots.json").write_text(json.dumps(config))
    (tmp_path / "previous.json").write_text(done.model_dump_json())
    target = tmp_path / "expanded.json"
    assert (
        main(
            [
                "discover",
                "--snapshots",
                str(tmp_path / "snapshots.json"),
                "--previous-inventory",
                str(tmp_path / "previous.json"),
                "--archive",
                str(root),
                "--output",
                str(target),
            ]
        )
        == 0
    )
    expanded = json.loads(target.read_text())
    assert sum(r["material_type"] == "task" for r in expanded["materials"]) == 2
    assert all(not url.endswith((".mp3", ".mp4")) for url in calls)


def test_explicit_retry_preserves_failed_source_and_then_validates(tmp_path):
    inv = inventory()
    row = next(
        r for r in inv.materials if r.material_type == "transcript" and r.selected
    )
    root = tmp_path / "archive"
    failed = api.acquire(
        inv,
        grant(inv, [row.material_id]),
        root,
        transport=httpx.MockTransport(lambda _: httpx.Response(404)),
        offline_test=True,
    )
    with pytest.raises(PermissionError, match="retry"):
        run(failed, root, [], [row.material_id])
    recovered = run(failed, root, [], [row.material_id], retry_failed=True)
    assert (
        next(
            r for r in recovered.materials if r.material_id == row.material_id
        ).acquisition_status
        == "VERIFIED"
    )


def test_dns_pinning_rejects_private_and_mixed_answers(monkeypatch):
    from src.tools_materials.https_transport import public_addresses

    for addresses in (["127.0.0.1"], ["93.184.216.34", "10.0.0.2"], ["::1"]):
        monkeypatch.setattr(
            socket,
            "getaddrinfo",
            lambda *a, addresses=addresses, **k: [
                (
                    socket.AF_INET6 if ":" in value else socket.AF_INET,
                    socket.SOCK_STREAM,
                    0,
                    "",
                    (value, 443),
                )
                for value in addresses
            ],
        )
        with pytest.raises(ValueError, match="Nonpublic"):
            public_addresses("cs50.harvard.edu")


@pytest.mark.parametrize("kind", ["notes", "slides"])
def test_missing_required_notes_or_slides_is_not_hidden(kind):
    inv = inventory()
    row = next(r for r in inv.materials if r.material_type == kind and r.required)
    damaged = inv.model_copy(
        update={
            "materials": tuple(
                r for r in inv.materials if r.material_id != row.material_id
            )
        }
    )
    report = api.completeness(damaged)
    assert row.material_id in report["overall"]["missing_expected_ids"]
    lecture = next(
        s for s in report["sections"].values() if s["material_type"] == "lecture"
    )
    assert not lecture["discovery_complete"]


def test_external_only_slides_and_unverified_success_labels_block_completion():
    supplied = pages()
    supplied[WEEK] = supplied[WEEK].replace(
        (CDN + "slides.pdf").encode(),
        b"https://docs.google.com/presentation/d/example/",
    )
    inv = api.discover(supplied, source_origin="synthetic")
    slide = next(r for r in inv.materials if r.material_type == "slides" and r.required)
    assert slide.acquisition_status == "BLOCKED"
    assert not api.completeness(inv)["overall"]["discovery_complete"]
    forged = inv.model_copy(
        update={
            "materials": tuple(
                r.model_copy(update={"acquisition_status": "VERIFIED"})
                if r.material_type == "transcript"
                else r
                for r in inv.materials
            )
        }
    )
    assert api.completeness(forged)["integrity_failures"]
    assert api.completeness(forged)["status"] == "HOLD"


def test_csv_attachment_requires_individual_approval(tmp_path):
    supplied = pages()
    supplied[PSET + "two/"] = html(
        "Two", '<a href="' + CDN + 'required.csv">Data CSV</a>'
    )
    inv = api.discover(supplied, source_origin="synthetic")
    row = next(
        r
        for r in inv.materials
        if r.material_type == "attachment" and r.source_format == "csv"
    )
    assert row.required
    result = api.acquire(
        inv,
        grant(inv, [row.material_id]),
        tmp_path / "archive",
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200, content=b"a,b\n1,2\n", headers={"content-type": "text/csv"}
            )
        ),
        offline_test=True,
    )
    assert (
        next(
            r for r in result.materials if r.material_id == row.material_id
        ).acquisition_status
        == "VERIFIED"
    )


def test_reused_file_still_respects_new_grant_size(tmp_path):
    inv = inventory()
    row = next(
        r for r in inv.materials if r.material_type == "transcript" and r.selected
    )
    root, calls = tmp_path / "archive", []
    done = run(inv, root, calls, [row.material_id])
    limited = api.acquire(
        done,
        grant(done, [row.material_id], maximum=10),
        root,
        transport=httpx.MockTransport(
            lambda _: pytest.fail("Verified file should be reused")
        ),
        offline_test=True,
    )
    result = next(r for r in limited.materials if r.material_id == row.material_id)
    assert result.acquisition_status == "FAILED"
    assert "approved size" in result.error_reason
    assert (root / row.expected_local_path).exists()
