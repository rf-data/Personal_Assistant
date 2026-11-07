"""Own synthetic HTML through real material, bundle, store and FTS/reader APIs."""

import json
import os
import socket
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import cs50_learning_mvp as mvp
from src.content_store.models import canonical, sha256
from src.content_store.store import ContentStore
from src.model_discovery.cs50 import (
    CourseDiscovery,
    Provenance,
    ResourceCandidate,
    SectionDiscovery,
)
from src.model_materials.materials import MaterialPlan, MaterialResource, ParserConfig

# Gold is authored before parsing/searching, independently of any returned hit.
PASSAGES = (
    "A variable stores a value under a chosen name.",
    "The input function returns text entered by the learner.",
    "A loop repeats instructions while its condition remains true.",
)
QUERIES = ("variable", "input", "loop")
HTML = (
    "<!doctype html><html><head><title>Own synthetic CS50P exercise</title></head>"
    "<body><main><h1>Own learning example</h1>"
    + "".join(f"<p>{p}</p>" for p in PASSAGES)
    + "<pre><code>name = input('Name: ')\nprint(name)</code></pre>"
    "</main></body></html>"
).encode()


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)


def make_case(tmp_path, raw=HTML, config=None):
    inputs = tmp_path / "own-inputs"
    inputs.mkdir(mode=0o700)
    url = "https://cs50.harvard.edu/python/synthetic-prompt20/notes.html"
    lecture = ResourceCandidate(
        course_id="cs50_python",
        role="lecture_video",
        original_url="https://cs50.harvard.edu/python/synthetic-prompt20/lecture/",
        section_keys=("synthetic",),
    )
    resource = ResourceCandidate(
        course_id="cs50_python",
        role="notes",
        original_url=url,
        section_keys=("synthetic",),
        provenance=(
            Provenance(
                original_url=url,
                fixture_file="own.html",
                locator="Own synthetic bytes; URL is an identity only, never fetched",
            ),
        ),
    )
    binding = MaterialResource(
        resource=resource,
        original_url=url,
        format="html",
        role="notes",
        lecture_ids=(lecture.resource_id,),
        source_origin="synthetic",
    )
    plan = MaterialPlan(
        courses=(
            CourseDiscovery(
                course_id="cs50_python",
                original_url="https://cs50.harvard.edu/python/",
                sections=(
                    SectionDiscovery(
                        course_id="cs50_python",
                        key="synthetic",
                        original_url="https://cs50.harvard.edu/python/synthetic-prompt20/",
                    ),
                ),
                resources=(lecture, resource),
            ),
        ),
        materials=(binding,),
    )
    source = inputs / "own.html"
    source.write_bytes(raw)
    plan_path = inputs / "plan.json"
    plan_path.write_bytes(canonical(plan.model_dump(mode="json")))
    revision, code_hash = mvp.implementation_identity()
    approval = mvp.ProcessingApproval(
        schema_version=1,
        status="approved",
        approved_by="synthetic-operator",
        evidence_reference="Prompt 20 authorizes own synthetic test material only",
        valid_until=datetime.now(UTC) + timedelta(hours=1),
        resource_id=binding.source_id,
        material_id=binding.material_id,
        original_url=url,
        source_origin="synthetic",
        raw_sha256=sha256(raw),
        plan_sha256=sha256(plan_path.read_bytes()),
        parser=config or ParserConfig(name="html", version="2"),
        implementation_revision=revision,
        implementation_sha256=code_hash,
        actions=mvp.ACTIONS,
        retrieval_tasks=tuple(
            mvp.RetrievalTask(query=q, expected_passage=p)
            for q, p in zip(QUERIES, PASSAGES, strict=True)
        ),
    )
    approval_path = inputs / "approval.json"
    approval_path.write_bytes(canonical(approval.model_dump(mode="json")))
    approval_path.chmod(0o600)
    root = tmp_path / "new-private-mvp"
    return SimpleNamespace(
        root=root,
        source=source,
        plan=plan_path,
        approval=approval_path,
        binding=binding,
        argv=[
            "run",
            "--output-root",
            str(root),
            "--actor",
            "synthetic-operator",
            "--input",
            str(source),
            "--plan",
            str(plan_path),
            "--material",
            binding.material_id,
            "--approval",
            str(approval_path),
            "--query",
            "input",
        ],
    )


def change_approval(case, **changes):
    value = json.loads(case.approval.read_bytes())
    value.update(changes)
    case.approval.write_bytes(canonical(value))


def invoke(argv, capsys, expected=0):
    assert mvp.main(argv) == expected
    output = capsys.readouterr()
    return json.loads(output.out if expected == 0 else output.err)


def observation(case, operation="status"):
    return [operation, "--output-root", str(case.root), "--actor", "synthetic-operator"]


def test_synthetic_pipeline_persistence_idempotency_and_provenance(tmp_path, capsys):
    case = make_case(tmp_path)
    inputs = {p: p.read_bytes() for p in (case.source, case.plan, case.approval)}
    first = invoke(case.argv, capsys)
    assert first["technical_status"] == "TECHNICAL PASS"
    assert first["real_source_status"] == "BLOCKED" and first["mvp_status"] == "PENDING"
    assert first["raw_bytes_verified"] and not first["reused_publication"]
    assert all(t["rank"] <= 5 for t in first["retrieval_acceptance"])
    assert first["publication"]["record_count"] >= 3
    assert first["publication"]["generation_id"].startswith(
        "content_index_generation_v1:"
    )
    before = mvp.inventory(case.root)
    second = invoke(case.argv, capsys)
    assert second["reused_publication"]
    assert first["publication"] == second["publication"]
    assert first["searches"] == second["searches"]
    assert mvp.inventory(case.root) == before
    status = invoke(observation(case), capsys)
    assert len(status["sources"]) == len(status["versions"]) == 1
    assert len(status["versions"][0]["parsed"]["items"]) == 1
    assert status["recovery"] == []
    actor = mvp.actor_for(first["intent"], "synthetic-operator")
    store = ContentStore(case.root / "store")
    vid = first["publication"]["parsed_version_id"]
    assert (
        store.read_raw_artifact(case.binding.source_id, sha256(HTML), actor=actor)
        == HTML
    )
    document = json.loads(store.read_parsed_payload(vid, actor=actor))
    assert document["parser"]["version"] == "2"
    for result in first["searches"]:
        for resolved in result["results"]:
            hit, block = resolved["hit"], resolved["source_block"]
            assert hit["source_id"] == case.binding.source_id
            assert hit["parsed_version_id"] == block["parsed_version_id"] == vid
            assert block["text"] == hit["excerpt"]["text"]
            assert resolved["original_location"]["dom"]
            assert resolved["source_structure"]["locators"][0]["origin_pointer"]
    assert all(p.read_bytes() == data for p, data in inputs.items())
    assert mvp.inventory(case.root) == before


def test_separate_process_restart_and_lost_final_response(
    tmp_path, capsys, monkeypatch
):
    case = make_case(tmp_path)
    original = mvp.report

    def lost(*args, **kwargs):
        original(*args, **kwargs)
        raise OSError("simulated final response loss")

    monkeypatch.setattr(mvp, "report", lost)
    invoke(case.argv, capsys, 2)
    assert mvp.load(case.root, "state.json")["phase"] == "ready"
    before = mvp.inventory(case.root)
    command = [sys.executable, "-m", "scripts.cs50_learning_mvp"]
    # A fresh process can search and then safely repeat without publication/indexing.
    for argv in [observation(case, "search") + ["--query", "variable"], case.argv]:
        completed = subprocess.run(
            command + argv,
            cwd=mvp.REPO,
            capture_output=True,
            text=True,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
            timeout=30,
        )
        assert completed.returncode == 0, completed.stderr
        result = json.loads(completed.stdout)
        assert all(task["passed"] for task in result["retrieval_acceptance"])
        assert result["publication"] == mvp.load(case.root, "state.json")
    assert mvp.inventory(case.root) == before


@pytest.mark.parametrize(
    "change",
    [
        {"status": "revoked"},
        {"raw_sha256": "0" * 64},
        {"material_id": "foreign"},
        {"resource_id": "foreign"},
        {"original_url": "https://cs50.harvard.edu/python/other/"},
        {"implementation_revision": "0" * 40},
        {"implementation_sha256": "0" * 64},
        {"plan_sha256": "0" * 64},
        {"actions": ["parse"]},
        {"source_origin": "official"},
        {"approved_by": "another-operator"},
        {"valid_until": "2020-01-01T00:00:00Z"},
        {"schema_version": True},
        {"evidence_reference": " "},
    ],
)
def test_invalid_approval_prevents_any_output(tmp_path, capsys, change):
    case = make_case(tmp_path)
    change_approval(case, **change)
    assert invoke(case.argv, capsys, 2)["status"] == "HOLD"
    assert not case.root.exists()


def test_missing_approval_and_rawhash_conflict(tmp_path, capsys):
    case = make_case(tmp_path)
    without = case.argv[: case.argv.index("--approval")]
    invoke(without, capsys, 2)
    assert not case.root.exists()
    case.source.write_bytes(HTML + b"changed")
    invoke(case.argv, capsys, 2)
    assert not case.root.exists()
    case.source.write_bytes(HTML)
    invoke(case.argv, capsys)
    before = mvp.inventory(case.root)
    case.source.write_bytes(HTML + b"changed")
    invoke(case.argv, capsys, 2)
    change_approval(case, raw_sha256=sha256(case.source.read_bytes()))
    invoke(case.argv, capsys, 2)
    assert mvp.inventory(case.root) == before


def test_changed_approved_bytes_require_new_root(tmp_path, capsys):
    case = make_case(tmp_path)
    first = invoke(case.argv, capsys)
    before = mvp.inventory(case.root)
    changed = HTML.replace(b"</main>", b"<p>Own additional exercise.</p></main>")
    case.source.write_bytes(changed)
    change_approval(case, raw_sha256=sha256(changed))
    new_root = tmp_path / "explicit-new-byte-generation"
    argv = case.argv.copy()
    argv[argv.index("--output-root") + 1] = str(new_root)
    second = invoke(argv, capsys)
    assert (
        first["publication"]["parsed_version_id"]
        != second["publication"]["parsed_version_id"]
    )
    assert second["intent"]["raw_sha256"] == sha256(changed)
    assert mvp.inventory(case.root) == before


@pytest.mark.parametrize(
    "raw,config",
    [
        (b"<html><main></main></html>", None),
        (HTML, ParserConfig(name="html", version="2", max_blocks=1)),
    ],
)
def test_parser_failure_never_publishes(tmp_path, capsys, raw, config):
    case = make_case(tmp_path, raw, config)
    invoke(case.argv, capsys, 2)
    assert mvp.load(case.root, "state.json")["phase"] == "preparing"
    assert not (case.root / "store").exists()
    before = mvp.inventory(case.root)
    invoke(case.argv, capsys, 2)
    assert mvp.inventory(case.root) == before


def test_quality_gate_rejects_incomplete_lecture_binding(tmp_path, capsys):
    case = make_case(tmp_path)
    plan = json.loads(case.plan.read_bytes())
    plan["courses"][0]["resources"] = [plan["materials"][0]["resource"]]
    plan["materials"][0]["lecture_ids"] = []
    case.plan.write_bytes(canonical(plan))
    change_approval(case, plan_sha256=sha256(case.plan.read_bytes()))
    rejected = invoke(case.argv, capsys, 2)
    assert "quality/handoff" in rejected["reason"]
    assert not (case.root / "store").exists()


@pytest.mark.parametrize("after", [False, True])
def test_publication_failure_or_lost_response_holds_without_retry(
    tmp_path, capsys, monkeypatch, after
):
    case = make_case(tmp_path)
    original = ContentStore.publish_parsed_document

    def fail(self, *args, **kwargs):
        if after:
            original(self, *args, **kwargs)
        raise OSError("simulated publication boundary failure")

    monkeypatch.setattr(ContentStore, "publish_parsed_document", fail)
    invoke(case.argv, capsys, 2)
    assert mvp.load(case.root, "state.json")["phase"] == "publication_pending"
    assert not (case.root / "index").exists()
    before = mvp.inventory(case.root)
    invoke(case.argv, capsys, 2)
    assert mvp.inventory(case.root) == before
    status = invoke(observation(case), capsys)
    assert status["publication"]["phase"] == "publication_pending"
    assert len(status["versions"][0]["parsed"]["items"]) == int(after)
    invoke(observation(case, "search") + ["--query", "input"], capsys, 2)
    assert mvp.inventory(case.root) == before


def test_failure_before_index_activation_retains_publication(
    tmp_path, capsys, monkeypatch
):
    from src.tools_rag.content_index_files import IndexFiles

    case = make_case(tmp_path)

    def failed(*args, **kwargs):
        raise OSError("simulated failure before index publication")

    monkeypatch.setattr(IndexFiles, "publish", failed)
    invoke(case.argv, capsys, 2)
    state = mvp.load(case.root, "state.json")
    assert state["phase"] == "index_pending" and state["parsed_version_id"]
    assert not (case.root / "index/active.json").exists()
    before = mvp.inventory(case.root)
    invoke(case.argv, capsys, 2)
    status = invoke(observation(case), capsys)
    assert len(status["versions"][0]["parsed"]["items"]) == 1
    assert status["builds"][0]["state"] == "failed"
    assert mvp.inventory(case.root) == before


def test_foreign_existing_data_and_unsafe_paths_are_preserved(tmp_path, capsys):
    case = make_case(tmp_path)
    case.root.mkdir(mode=0o700)
    foreign = case.root / "valuable.sqlite3"
    foreign.write_bytes(b"pre-existing user data")
    before = foreign.read_bytes()
    invoke(case.argv, capsys, 2)
    assert foreign.read_bytes() == before
    # A real pre-existing store is also never adopted, including its private files.
    store = ContentStore.initialize(tmp_path / "pre-existing-store")
    saved = mvp.inventory(store.root)
    other = case.argv.copy()
    other[other.index("--output-root") + 1] = str(store.root)
    invoke(other, capsys, 2)
    assert mvp.inventory(store.root) == saved
    for root in [Path("relative"), mvp.REPO / "forbidden-output"]:
        other[other.index("--output-root") + 1] = str(root)
        invoke(other, capsys, 2)
    link = tmp_path / "output-link"
    link.symlink_to(case.root, target_is_directory=True)
    other[other.index("--output-root") + 1] = str(link)
    invoke(other, capsys, 2)
    assert foreign.read_bytes() == before


def test_unknown_entries_unsafe_approval_and_actor_conflict(tmp_path, capsys):
    case = make_case(tmp_path)
    case.approval.chmod(0o644)
    invoke(case.argv, capsys, 2)
    assert not case.root.exists()
    case.approval.chmod(0o600)
    invoke(case.argv, capsys)
    changed_actor = observation(case)
    changed_actor[-1] = "other-operator"
    invoke(changed_actor, capsys, 2)
    unknown = case.root / "unrelated"
    unknown.write_bytes(b"retain this")
    invoke(case.argv, capsys, 2)
    assert unknown.read_bytes() == b"retain this"


def test_more_than_100_blocks_resolve_through_existing_reader(tmp_path, capsys):
    raw = HTML.replace(b"</main>", b"<p>extra paragraph</p>" * 110 + b"</main>")
    case = make_case(tmp_path, raw)
    result = invoke(case.argv, capsys)
    assert result["publication"]["record_count"] > 100
    assert all(t["passed"] for t in result["retrieval_acceptance"])


def test_retrieval_mismatch_is_failure_with_real_empty_results(tmp_path, capsys):
    case = make_case(tmp_path)
    approval = json.loads(case.approval.read_bytes())
    approval["retrieval_tasks"][0]["query"] = "wordnotpresentanywhere"
    case.approval.write_bytes(canonical(approval))
    assert mvp.main(case.argv) == 2
    result = json.loads(capsys.readouterr().out)
    assert (
        result["status"] == "retrieval_failed" and result["technical_status"] == "FAIL"
    )
    assert result["searches"][0]["results"] == []
    assert result["retrieval_acceptance"][0]["rank"] is None


def test_cli_argument_validation(tmp_path, capsys):
    with pytest.raises(SystemExit) as error:
        mvp.main(["run"])
    assert error.value.code == 2
    capsys.readouterr()
    case = make_case(tmp_path)
    invoke(case.argv + ["--query", " "], capsys, 2)
    invoke(case.argv + ["--query", "x" * 65], capsys, 2)
    assert not case.root.exists()
    invoke(case.argv, capsys)
    invoke(observation(case, "search"), capsys, 2)
    invoke(observation(case) + ["--input", str(case.source)], capsys, 2)
    invoke(observation(case) + ["--query", "input"], capsys, 2)


@pytest.mark.parametrize(
    "target", ["input.html", "plan.json", "approval.json", "implementation.json"]
)
def test_corrupted_saved_closure_never_reports_success(tmp_path, capsys, target):
    case = make_case(tmp_path)
    invoke(case.argv, capsys)
    (case.root / target).write_bytes(b"corrupted own fixture")
    before = mvp.inventory(case.root)
    invoke(observation(case, "search") + ["--query", "input"], capsys, 2)
    assert mvp.inventory(case.root) == before


def test_expired_saved_approval_blocks_retrieval(tmp_path, capsys, monkeypatch):
    case = make_case(tmp_path)
    invoke(case.argv, capsys)

    class FutureClock:
        @staticmethod
        def now(tz):
            return datetime.now(tz) + timedelta(days=1)

    monkeypatch.setattr(mvp, "datetime", FutureClock)
    before = mvp.inventory(case.root)
    invoke(observation(case, "search") + ["--query", "input"], capsys, 2)
    assert mvp.inventory(case.root) == before


def test_search_current_implementation_is_read_only(tmp_path, capsys):
    case = make_case(tmp_path)
    first = invoke(case.argv, capsys)
    before = mvp.inventory(case.root)
    result = invoke(observation(case, "search") + ["--query", "input"], capsys)
    assert result["technical_status"] == "TECHNICAL PASS"
    assert result["publication"] == first["publication"]
    assert mvp.inventory(case.root) == before
    status = invoke(observation(case), capsys)
    assert status["retrieval_authorization"] == {"status": "current"}
    assert status["technical_status"] == "NOT_ASSESSED"
    assert mvp.inventory(case.root) == before


@pytest.mark.parametrize("component", ["revision", "fingerprint", "unavailable"])
def test_search_changed_implementation_holds_but_status_remains_readable(
    tmp_path, capsys, monkeypatch, component
):
    case = make_case(tmp_path)
    first = invoke(case.argv, capsys)
    revision, code_hash = mvp.implementation_identity()

    def changed_identity():
        if component == "unavailable":
            raise OSError("synthetic identity lookup failure")
        return (
            "0" * 40 if component == "revision" else revision,
            "0" * 64 if component == "fingerprint" else code_hash,
        )

    def forbidden_retrieve(*args, **kwargs):
        pytest.fail("rejected search reached retrieval")

    monkeypatch.setattr(mvp, "implementation_identity", changed_identity)
    monkeypatch.setattr(mvp, "retrieve", forbidden_retrieve)
    before = mvp.inventory(case.root)
    result = invoke(observation(case, "search") + ["--query", "input"], capsys, 2)
    assert result["status"] == "HOLD" and result["success"] is False
    if component != "unavailable":
        assert "current implementation" in result["reason"]
    status = invoke(observation(case), capsys)
    assert status["status"] == "observed"
    assert status["technical_status"] == "NOT_ASSESSED"
    assert status["retrieval_authorization"]["status"] == "HOLD"
    assert status["intent"] == first["intent"]
    assert status["publication"] == first["publication"]
    assert len(status["versions"][0]["parsed"]["items"]) == 1
    assert mvp.inventory(case.root) == before


@pytest.mark.parametrize(
    "defect",
    [
        "missing_approval_revision",
        "missing_approval_fingerprint",
        "missing_intent_revision",
        "missing_intent_fingerprint",
        "intent_revision_mismatch",
        "intent_fingerprint_mismatch",
        "revoked",
        "wrong_actions",
        "wrong_actor",
        "expired",
    ],
)
def test_search_invalid_saved_binding_preserves_all_data(
    tmp_path, capsys, monkeypatch, defect
):
    case = make_case(tmp_path)
    invoke(case.argv, capsys)
    approval = mvp.load(case.root, "approval.json")
    intent = mvp.load(case.root, "intent.json")
    if defect.startswith("missing_approval_"):
        field = defect.removeprefix("missing_approval_")
        approval.pop(
            "implementation_" + ("sha256" if field == "fingerprint" else field)
        )
    elif defect.startswith("missing_intent_"):
        field = defect.removeprefix("missing_intent_")
        intent.pop("implementation_" + ("sha256" if field == "fingerprint" else field))
    elif defect == "intent_revision_mismatch":
        intent["implementation_revision"] = "0" * 40
    elif defect == "intent_fingerprint_mismatch":
        intent["implementation_sha256"] = "0" * 64
    elif defect == "revoked":
        approval["status"] = "revoked"
    elif defect == "wrong_actions":
        approval["actions"] = ["retrieve"]
    elif defect == "wrong_actor":
        approval["approved_by"] = "other-operator"
    else:
        approval["valid_until"] = "2020-01-01T00:00:00Z"
    # Deliberately malformed synthetic closure, with a matching saved bytehash,
    # exercises schema/authorization checks beyond the existing tamper hash gate.
    data = canonical(approval)
    (case.root / "approval.json").write_bytes(data)
    intent["approval_sha256"] = sha256(data)
    (case.root / "intent.json").write_bytes(canonical(intent))

    def forbidden_retrieve(*args, **kwargs):
        pytest.fail("invalid approval reached retrieval")

    monkeypatch.setattr(mvp, "retrieve", forbidden_retrieve)
    before = mvp.inventory(case.root)
    result = invoke(observation(case, "search") + ["--query", "input"], capsys, 2)
    assert result["status"] == "HOLD" and result["success"] is False
    status = invoke(observation(case), capsys)
    assert status["status"] == "observed"
    assert status["technical_status"] == "NOT_ASSESSED"
    assert status["retrieval_authorization"]["status"] == "HOLD"
    assert mvp.inventory(case.root) == before


@pytest.mark.parametrize("change", ["duplicate_query", "blank_passage"])
def test_invalid_predeclared_retrieval_tasks_are_rejected(tmp_path, capsys, change):
    case = make_case(tmp_path)
    value = json.loads(case.approval.read_bytes())
    if change == "duplicate_query":
        value["retrieval_tasks"][1]["query"] = "  VARIABLE  "
    else:
        value["retrieval_tasks"][1]["expected_passage"] = " "
    case.approval.write_bytes(canonical(value))
    invoke(case.argv, capsys, 2)
    assert not case.root.exists()
