"""M2.2a: real publication/Reader/FakeLLM; deliberately no successful FTS gate."""

import json
import socket
import sqlite3
import subprocess
import sys
import time
from contextlib import closing, contextmanager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from scripts import cs50_learning_mvp as mvp
from src import cs50_summary_batch as batch
from src import cs50_summary_mvp as m1
from src import cs50_summary_readiness as readiness
from src.content_store.errors import Unavailable
from src.content_store.models import SourceGrant, canonical
from src.content_store.store import ContentStore
from src.job_control.models import Principal
from src.tools_rag.content_index import ContentIndex
from tests.test_cs50_learning_mvp import HTML, make_case
from tests.test_cs50_summary_batch import invoke
from tests.test_cs50_summary_batch_stress import assert_coverage, source


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*a, **kw):
        raise AssertionError("M2.2a forbids all network access")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


def publish(tmp_path, capsys, monkeypatch, raw=HTML, *, fts_failure=False):
    case = make_case(tmp_path, raw)
    searches = []

    def stop(*a, **kw):
        if fts_failure:
            searches.append(1)
            raise Unavailable("FTS query/database unavailable")
        raise mvp.Hold("synthetic harness stops after complete publication")

    with monkeypatch.context() as setup:
        setup.setattr(
            ContentIndex, "search_lexical" if fts_failure else "initialize", stop
        )
        assert mvp.main(case.argv) == 2
        assert json.loads(capsys.readouterr().err)["status"] == "HOLD"
    state = mvp.load(case.root, "state.json")
    assert state["phase"] == ("index_pending" if fts_failure else "published")
    assert searches == ([1] if fts_failure else [])
    case.common = [
        "--source-root",
        str(case.root),
        "--source-id",
        case.binding.source_id,
        "--parsed-version-id",
        state["parsed_version_id"],
        "--actor",
        "synthetic-operator",
        "--source-contract",
        readiness.CONTRACT,
    ]
    return case


def approve(tmp_path, case, capsys):
    proposed = invoke(["plan", *case.common], capsys)
    assert proposed["status"] == "approval_required"
    assert "approved_by" not in proposed
    plan = batch.BatchPlan.model_validate(proposed["plan"])
    approval = batch.VerifiedBatchApproval(
        schema_version=3,
        status="approved",
        approved_by="synthetic-operator",
        evidence_reference="M2.2a explicitly authorized synthetic fixture only",
        valid_until=datetime.now(UTC) + timedelta(hours=1),
        actions=m1.ACTIONS,
        implementation_revision=proposed["implementation_revision"],
        implementation_sha256=proposed["implementation_sha256"],
        adapter_version=readiness.ADAPTER_VERSION,
        source_contract=readiness.CONTRACT,
        source_verification_sha256=proposed["source_verification_sha256"],
        config=plan.config,
        limits=plan.limits,
        plan=plan,
        **plan.source,
    )
    path = tmp_path / "summary-approval.json"
    path.write_bytes(canonical(approval.model_dump(mode="json")))
    path.chmod(0o600)
    target = tmp_path / "summary"
    return SimpleNamespace(
        case=case,
        plan=plan,
        approval=path,
        target=target,
        argv=[
            "run",
            *case.common,
            "--approval",
            str(path),
            "--output-root",
            str(target),
        ],
    )


@contextmanager
def corrupt_database(case):
    """Fault injection only; restore every trigger to avoid a schema-only failure."""
    with closing(sqlite3.connect(case.root / "store/content.sqlite3")) as db:
        with db:
            triggers = db.execute(
                "SELECT name,sql FROM sqlite_master WHERE type='trigger'"
            ).fetchall()
            for name, _ in triggers:
                db.execute('DROP TRIGGER "' + name + '"')
            yield db
            for _, ddl in triggers:
                db.execute(ddl)
        db.execute("PRAGMA wal_checkpoint(TRUNCATE)")


def sql(case, statement, params=()):
    with corrupt_database(case) as db:
        db.execute(statement, params)


def actor():
    return Principal(
        subject="synthetic-operator", role="operator", courses=("cs50_python",)
    )


def revoke(case):
    # Exercise the real grant API: the summarizing operator is a granted reader.
    owner = actor().model_copy(update={"subject": "synthetic-owner"})
    store = ContentStore(case.root / "store", read_only=False)
    source = store.get_source(case.binding.source_id, actor=owner)
    store.set_source_grants(
        case.binding.source_id,
        (),
        expected_acl_revision=source.acl_revision,
        actor=owner,
    )


def grant_reader(case):
    # Synthetic fixture setup: production has no owner-transfer API. Keep the
    # serialized registration consistent, then grant/revoke via the real API.
    with corrupt_database(case) as db:
        data = json.loads(db.execute("SELECT data FROM sources").fetchone()[0])
        data["owner_subject"] = "synthetic-owner"
        db.execute(
            "UPDATE sources SET owner=?,data=?",
            ("synthetic-owner", canonical(data).decode()),
        )
    owner = actor().model_copy(update={"subject": "synthetic-owner"})
    store = ContentStore(case.root / "store", read_only=False)
    source = store.get_source(case.binding.source_id, actor=owner)
    store.set_source_grants(
        case.binding.source_id,
        (SourceGrant(subject="synthetic-operator"),),
        expected_acl_revision=source.acl_revision,
        actor=owner,
    )


def test_published_without_index_is_explicit_and_fail_closed(
    tmp_path, capsys, monkeypatch
):
    case = publish(tmp_path, capsys, monkeypatch)
    assert not (case.root / "index").exists()
    from src.tools_rag import content_fts

    def forbidden(*a, **kw):
        raise AssertionError("this proof must never reach an FTS build or query")

    monkeypatch.setattr(content_fts, "build_database", forbidden)
    monkeypatch.setattr(content_fts, "search_database", forbidden)
    before = mvp.inventory(case.root)
    with pytest.raises(m1.Hold, match="ready"):
        m1.read_source(
            case.root,
            case.binding.source_id,
            mvp.load(case.root, "state.json")["parsed_version_id"],
            "synthetic-operator",
        )
    test = approve(tmp_path, case, capsys)
    report = invoke(test.argv, capsys)
    assert report["coverage"]["complete_input"]
    assert mvp.inventory(case.root) == before
    assert mvp.load(case.root, "state.json")["phase"] == "published"
    assert (
        mvp.main(
            ["status", "--output-root", str(case.root), "--actor", "synthetic-operator"]
        )
        == 0
    )
    capsys.readouterr()


def test_171_long_lecture_after_failed_fts_complete_handoff(
    tmp_path, capsys, monkeypatch
):
    case = publish(
        tmp_path,
        capsys,
        monkeypatch,
        source([(1200, 1800, 2800)[i % 3] for i in range(166)]),
        fts_failure=True,
    )
    before = mvp.inventory(case.root)

    def forbidden(*a, **kw):
        raise AssertionError(
            "no search, build, publication, download or parsing after handoff"
        )

    from src.tools_materials.download import MaterialDownloader
    from src.tools_materials.processing import MaterialProcessor

    for cls, method in (
        (ContentIndex, "search_lexical"),
        (ContentIndex, "build"),
        (ContentStore, "initialize"),
        (MaterialDownloader, "obtain"),
        (MaterialProcessor, "parse"),
    ):
        monkeypatch.setattr(cls, method, forbidden)
    test = approve(tmp_path, case, capsys)
    pages, calls = [], []
    original_page, original_complete = m1.ContentReader.page, batch.FakeLLM.complete

    def page(*a, **kw):
        result = original_page(*a, **kw)
        pages.append(len(result.items))
        return result

    def complete(*a, **kw):
        calls.append(1)
        return original_complete(*a, **kw)

    monkeypatch.setattr(m1.ContentReader, "page", page)
    monkeypatch.setattr(batch.FakeLLM, "complete", complete)
    started = time.perf_counter()
    report = invoke(test.argv, capsys)
    run_seconds = time.perf_counter() - started
    blocks = tuple(
        m1.ContentBlock.model_validate(b)
        for b in mvp.load(test.target, "evidence.json")["blocks"]
    )
    assert len(blocks) == 171 and len(pages) == 2 and sum(pages) == 171
    assert all(0 < count <= 100 for count in pages)
    source_reader_pages = list(pages)
    refs = assert_coverage(test.plan, report, blocks)
    assert len(calls) == len(refs) == 226
    assert [len(b.refs) for b in test.plan.batches] == [32] * 7 + [2]
    saved = mvp.inventory(test.target)
    monkeypatch.setattr(batch.FakeLLM, "complete", forbidden)
    assert invoke(test.argv, capsys) == report
    child_script = """
import socket, sys
def forbidden(*a, **kw):
    raise AssertionError('No network, FTS or FakeLLM on restart')
socket.socket.connect = socket.socket.connect_ex = forbidden
socket.getaddrinfo = socket.create_connection = forbidden
from src import cs50_summary_batch as batch
from src.tools_rag.content_index import ContentIndex
batch.FakeLLM.complete = forbidden
ContentIndex.search_lexical = ContentIndex.build = forbidden
raise SystemExit(batch.main(sys.argv[1:]))
"""
    child = subprocess.run(
        [sys.executable, "-B", "-c", child_script, *test.argv],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout) == report
    assert mvp.inventory(test.target) == saved
    assert mvp.inventory(case.root) == before
    assert mvp.load(case.root, "state.json")["phase"] == "index_pending"
    for claim in report["claims"]:
        cited = {r.ref_id: r for r in refs}
        assert all(claim["text"] in cited[r].text for r in claim["refs"])
    (tmp_path / "handoff-evidence.json").write_bytes(
        canonical(
            dict(
                blocks=len(blocks),
                reader_pages=source_reader_pages,
                requests=len(calls),
                run_seconds=run_seconds,
                wall_limit_seconds=test.plan.limits.wall_seconds,
                per_batch_wall_limit_seconds=test.plan.config.wall_seconds,
                retries=test.plan.config.retries,
                batch_sizes=[len(b.refs) for b in test.plan.batches],
                coverage=report["coverage"],
                source_phase="index_pending",
                source_unchanged=mvp.inventory(case.root) == before,
                summary_review_status=report["review_status"],
                public_fts_attempts=1,
                public_fts_successes=0,
                fts_fault="injected original Unavailable at public search seam; no native timeout claim",
                cached_result_identical=True,
                guarded_process_restart_identical=True,
            )
        )
    )


@pytest.mark.parametrize(
    "change",
    [
        {"status": "rejected"},
        {"approved_by": "other"},
        {"actions": []},
        {"valid_until": "2020-01-01T00:00:00Z"},
        {"schema_version": True},
        {"raw_sha256": "0" * 64},
        {"implementation_sha256": "0" * 64},
        {"source_verification_sha256": "0" * 64},
        {"schema_version": 2},
    ],
)
def test_bad_summary_approval_no_dispatch(tmp_path, capsys, monkeypatch, change):
    case = publish(tmp_path, capsys, monkeypatch)
    test = approve(tmp_path, case, capsys)
    data = json.loads(test.approval.read_bytes())
    data.update(change)
    test.approval.write_bytes(canonical(data))
    monkeypatch.setattr(
        batch.FakeLLM, "complete", lambda *a, **k: pytest.fail("dispatch")
    )
    invoke(test.argv, capsys, expected=2)
    assert not test.target.exists()


@pytest.mark.parametrize(
    "change",
    [
        {"status": "rejected"},
        {"approved_by": "other"},
        {"actions": []},
        {"valid_until": "2020-01-01T00:00:00Z"},
        {"raw_sha256": "0" * 64},
        {"parser": {"name": "html", "version": "1"}},
    ],
)
def test_bad_processing_approval(tmp_path, capsys, monkeypatch, change):
    case = publish(tmp_path, capsys, monkeypatch)
    data = mvp.load(case.root, "approval.json")
    data.update(change)
    (case.root / "approval.json").write_bytes(canonical(data))
    invoke(["plan", *case.common], capsys, expected=2)


@pytest.mark.parametrize(
    "kind",
    [
        "raw",
        "payload",
        "projection",
        "missing_block",
        "locator",
        "phase",
        "unpublished",
        "unverified",
        "missing_quality",
        "parsed_version",
        "acl",
        "official",
    ],
)
def test_invalid_publication_no_approval(tmp_path, capsys, monkeypatch, kind):
    case = publish(tmp_path, capsys, monkeypatch)
    state = mvp.load(case.root, "state.json")
    vid = state["parsed_version_id"]
    if kind in {"raw", "payload", "projection"}:
        store = ContentStore(case.root / "store")
        view = store.get_parsed_document(vid, actor=actor())
        digest = (
            mvp.load(case.root, "intent.json")["raw_sha256"]
            if kind == "raw"
            else getattr(view, kind + "_sha256")
        )
        path = case.root / "store/blobs/sha256" / digest[:2] / digest
        path.write_bytes(path.read_bytes() + b" ")
    elif kind == "missing_block":
        sql(
            case,
            "DELETE FROM content_blocks WHERE rowid=(SELECT min(rowid) FROM content_blocks)",
        )
    elif kind == "locator":
        with corrupt_database(case) as db:
            key, data = db.execute(
                "SELECT id,data FROM content_blocks LIMIT 1"
            ).fetchone()
            data = json.loads(data)
            data["locators"][0]["origin_pointer"] = "/blocks/999"
            db.execute(
                "UPDATE content_blocks SET data=? WHERE id=?",
                (canonical(data).decode(), key),
            )
    elif kind == "phase":
        state["phase"] = "publication_pending"
        (case.root / "state.json").write_bytes(canonical(state))
    elif kind == "unpublished":
        sql(case, "UPDATE parsed_versions SET state='quarantined'")
    elif kind == "unverified":
        sql(case, "UPDATE source_versions SET state='quarantined'")
    elif kind == "missing_quality":
        sql(case, "DELETE FROM artifact_references WHERE role='quality'")
    elif kind == "parsed_version":
        state["parsed_version_id"] = "missing-version"
        (case.root / "state.json").write_bytes(canonical(state))
    elif kind == "acl":
        grant_reader(case)
        revoke(case)
    elif kind == "official":
        intent = mvp.load(case.root, "intent.json")
        intent["source_origin"] = "official"
        (case.root / "intent.json").write_bytes(canonical(intent))
    invoke(["plan", *case.common], capsys, expected=2)
    assert not list(tmp_path.glob("summary*"))


@pytest.mark.parametrize("kind", ["missing", "window", "locator", "version"])
def test_incomplete_or_wrong_reader(tmp_path, capsys, monkeypatch, kind):
    case = publish(tmp_path, capsys, monkeypatch)
    if kind == "missing":
        original = m1.ContentReader.page

        def page(*a, **kw):
            value = original(*a, **kw)
            return value.model_copy(update={"items": value.items[:-1]})

        monkeypatch.setattr(m1.ContentReader, "page", page)
    else:
        original = m1.ContentReader.block

        def block(*a, **kw):
            value = original(*a, **kw)
            if kind == "window" and not kw.get("structured"):
                return value.model_copy(update={"text": value.text[:-1]})
            if kind == "locator" and kw.get("structured"):
                loc = value.locators[0].model_copy(update={"dom": "wrong-dom"})
                return value.model_copy(update={"locators": (loc,)})
            if kind == "version":
                return value.model_copy(update={"parsed_version_id": "other-version"})
            return value

        monkeypatch.setattr(m1.ContentReader, "block", block)
    invoke(["plan", *case.common], capsys, expected=2)


@pytest.mark.parametrize(
    "kind", ["acl", "raw", "state", "approval", "implementation", "historical_expiry"]
)
def test_change_after_first_reply_stops_next_dispatch(
    tmp_path, capsys, monkeypatch, kind
):
    case = publish(tmp_path, capsys, monkeypatch)
    if kind == "acl":
        grant_reader(case)
    test = approve(tmp_path, case, capsys)
    complete = batch.FakeLLM.complete
    calls = []

    def mutate(*a, **kw):
        result = complete(*a, **kw)
        calls.append(1)
        if kind == "acl":
            revoke(case)
        elif kind == "raw":
            (case.root / "input.html").write_bytes(b"changed")
        elif kind == "state":
            state = mvp.load(case.root, "state.json")
            state["source_version_id"] = "other"
            (case.root / "state.json").write_bytes(canonical(state))
        elif kind == "approval":
            test.approval.write_bytes(test.approval.read_bytes() + b" ")
        elif kind == "implementation":
            monkeypatch.setattr(
                mvp, "implementation_identity", lambda: ("a" * 40, "b" * 64)
            )
        elif kind == "historical_expiry":
            data = mvp.load(case.root, "approval.json")
            data["valid_until"] = "2020-01-01T00:00:00Z"
            (case.root / "approval.json").write_bytes(canonical(data))
        return result

    monkeypatch.setattr(batch.FakeLLM, "complete", mutate)
    invoke(test.argv, capsys, expected=2)
    assert calls == [1]
    assert mvp.load(test.target, "state.json")["phase"] == "HOLD"
    assert not (test.target / "summary.json").exists()


def test_source_change_during_final_publication_invalidates_ready(
    tmp_path, capsys, monkeypatch
):
    case = publish(tmp_path, capsys, monkeypatch)
    test = approve(tmp_path, case, capsys)
    publish_bytes = batch.publish_bytes

    def mutate(path, data):
        result = publish_bytes(path, data)
        if path.name == "manifest.json":
            (case.root / "input.html").write_bytes(b"changed during final write")
        return result

    monkeypatch.setattr(batch, "publish_bytes", mutate)
    invoke(test.argv, capsys, expected=2)
    assert mvp.load(test.target, "state.json")["phase"] == "HOLD"
    invoke(test.argv, capsys, expected=2)
