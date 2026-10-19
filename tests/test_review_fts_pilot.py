"""C2 integration with authored synthetic bytes only; never human real reviews."""

import socket
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.content_store.adapters import import_verified_bundle, verify_material_bundle
from src.content_store.errors import Unavailable
from src.content_store.inventory import InventorySelection
from src.content_store.models import canonical, fingerprint, sha256
from src.content_store.read_models import ContentReadSettings
from src.content_store.store import ContentStore
from src.evaluation_store.models import ReviewGrant, ReviewSettings
from src.evaluation_store.store import EvaluationStore
from src.model_evaluation.content_retrieval import (
    ContentRetrievalEvaluationSet,
    EvaluationConfig,
    QueryResults,
    RetrievalResults,
    dataset_digest,
)
from src.model_evaluation.material_evaluation import (
    CorpusEntry,
    CorpusManifest,
    GoldDataset,
)
from src.tools_evaluation.evaluate_materials import evaluate as evaluate_materials
from src.tools_evaluation.evaluate_retrieval import evaluate_retrieval
from src.tools_rag.content_fts import backend_spec
from src.tools_rag.content_index import ContentIndex, RetrievalFault
from src.tools_rag.content_index_models import IndexSelection
from tests.content_adapter_support import REVISION, material
from tests.content_store_support import OWNER, VIEWER
from tests.review_support import (
    PERMISSIONS,
    api,
    confirm,
    draft,
    gateway,
    initialize,
    mutation,
    region,
)
from tests.test_content_fts import hits, inventory, keyfile

# Independently authored BEFORE any search; not learned from hits/parser output.
LINES = (
    "# 😀 e\u0301\r\n",
    'print("hello")\n',
    "answer = 42\n",
    "x = y + 1\n",
    'print("world")\n',
)
QUESTIONS = (
    ("hello", "hello", (1,)),
    ("world", "world", (4,)),
    ("answer", "answer", (2,)),
    ("print", "print", (1, 4)),
    ("absent", "missingterm", ()),
)
K = 4


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No network in the C2 synthetic pilot")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


@pytest.fixture
def pilot(tmp_path):
    bundle, doc = material(tmp_path, "code", code_raw="".join(LINES).encode())
    assert doc.binding.source_origin == "synthetic"
    content = ContentStore.initialize(tmp_path / "content")
    pv = import_verified_bundle(
        content, verify_material_bundle(bundle), actor=OWNER, request_key="synthetic-c2"
    ).version
    key = keyfile(tmp_path)
    index = ContentIndex.initialize(content, tmp_path / "index", cursor_key_file=key)
    selection = IndexSelection(parsed_version_ids=(pv.parsed_version_id,))
    build = index.build(selection, actor=OWNER)  # No query executed during setup.
    config = dict(
        method="lexical",
        ranking_schema="source_rrf_v1",
        backend_fingerprint=fingerprint(backend_spec()),
        # Public search generation is the existing actor-safe HMAC projection,
        # not the internal generation identifier printed by the build receipt.
        index_generation=index._hmac("index-generation-v1", build.generation_id),
        k=K,
        adapter="c24_search_result_page_v1",
    )
    config["configuration_fingerprint"] = fingerprint(config)
    spec = dict(
        schema_version=1,
        dataset_id="synthetic-review",
        dataset_version="synthetic-c2-five-queries-v1",
        selection=selection.model_dump(mode="json"),
        retrieval=config,
        queries=[dict(schema_version=1, query_id=q, text=t) for q, t, _ in QUESTIONS],
        corpus_reference="Authored synthetic constants; no human real gold",
    )
    EvaluationStore.initialize(tmp_path / "reviews")
    settings = ReviewSettings(
        schema_version=1,
        root=tmp_path / "reviews",
        content=ContentReadSettings(root=content.root, cursor_key_file=key),
        writes_enabled=True,
        grants=(
            ReviewGrant(
                schema_version=1,
                subject=OWNER.subject,
                dataset_id="synthetic-review",
                source_ids=(pv.source_id,),
                permissions=PERMISSIONS,
            ),
        ),
    )
    env = SimpleNamespace(
        app=gateway(settings, tmp_path / "jobs"),
        settings=settings,
        content=content,
        pv=pv,
        index=index,
        selection=selection,
        key=key,
        spec=spec,
        tmp=tmp_path,
        bundle=bundle,
        trace=[],
        blocks=content.list_content_blocks(pv.parsed_version_id, actor=OWNER).items,
    )
    assert tuple(b.text for b in env.blocks) == LINES
    initialize(env)  # Frozen queries are persisted before retrieval/review.
    return env


def annotate(env, task_id, number, query=None, grade=None):
    task = dict(
        schema_version=1,
        task_id=task_id,
        kind="retrieval" if query else "parsing",
        assignee=OWNER.subject,
        region=region(env, env.blocks[number], LINES[number], 0),
        query_id=query,
        corpus_entry_id=None if query else "synthetic-code-entry",
    )
    head = api(env, "POST", "/tasks", mutation(task=task))
    fields = {} if query else dict(quality="correct", expected_content=LINES[number])
    head = api(
        env,
        "POST",
        f"/tasks/{task_id}/draft",
        draft(head["revision"], grade=grade, **fields),
    )
    return confirm(env, task_id, head)


def review_all(env):
    for number in range(len(LINES)):
        annotate(env, f"parsing-{number}", number)
    for query, _, relevant in QUESTIONS:
        ids = []
        for number in range(len(LINES)):
            task_id = f"{query}-{number}"
            annotate(env, task_id, number, query, 3 if number in relevant else 0)
            ids.append(task_id)
        api(
            env,
            "POST",
            "/pool",
            mutation(
                query_id=query,
                reviewed_task_ids=ids,
                coverage_note="All five synthetic original lines",
                evidence_reference="synthetic-c2-authored-coverage",
            ),
        )


def export(env, name="gold"):
    api(env, "POST", f"/exports/{name}", mutation())
    data = api(env, "GET", f"/exports/{name}")
    return ContentRetrievalEvaluationSet.model_validate(data["retrieval"]), data


def search(env, dataset):
    # Actual local FTS5 API, fixed k and actor/source/course scope; no canned hits.
    outputs = []
    for q in dataset.queries:
        page = hits(
            env.index,
            q.text,
            actor=OWNER,
            course_id="cs50_python",
            source_ids=(env.pv.source_id,),
            limit=K,
        )
        assert page.index_generation == dataset.retrieval.index_generation
        assert page.next_cursor is None and len(page.items) <= K
        for hit in page.items:
            b = next(b for b in env.blocks if b.block_id == hit.block_id)
            assert hit.source_id == env.pv.source_id
            assert hit.source_version_id == env.pv.source_version_id
            assert hit.parsed_version_id == env.pv.parsed_version_id
            assert hit.anchor.text_sha256 == b.text_sha256
            assert hit.excerpt.text == b.text[hit.excerpt.start : hit.excerpt.end]
            assert tuple(
                x.model_dump(mode="json", exclude={"raw_reference"})
                for x in hit.locators
            ) == tuple(x.model_dump(mode="json") for x in b.locators)
            for locator in hit.locators:
                assert locator.raw_reference.source_id == env.pv.source_id
                assert (
                    locator.raw_reference.source_version_id == env.pv.source_version_id
                )
                assert locator.raw_reference.sha256 == b.locators[0].raw_artifact_sha256
        outputs.append(
            QueryResults(
                query_id=q.query_id,
                query_sha256=sha256(q.text.encode()),
                scope_sha256=fingerprint(q.scope.model_dump(mode="json")),
                configuration=dataset.retrieval,
                page=page,
            )
        )
    return RetrievalResults(
        schema_version=1, dataset_sha256=dataset_digest(dataset), queries=tuple(outputs)
    )


def evaluate(env, results, name="report", status=200):
    return api(
        env,
        "POST",
        f"/reports/{name}",
        mutation(export_id="gold", results=results.model_dump(mode="json")),
        status=status,
    )


def test_five_query_fts_reviews_export_report_restart(pilot):
    env = pilot
    before, raw_before = inventory(env.content.root), inventory(env.bundle.workspace)
    review_all(env)
    dataset, exported = export(env)
    assert dataset.origin == "synthetic" and dataset.corpus_complete
    assert len(dataset.judgments) == 25 and len(dataset.pools) == 5
    parsing = GoldDataset.model_validate(exported["parsing"])
    assert len(parsing.references) == 5
    assert {r.expected_content for r in parsing.references} == set(LINES)
    corpus = CorpusManifest(
        schema_version=1,
        dataset_version=parsing.dataset_version,
        entries=(
            CorpusEntry(
                entry_id="synthetic-code-entry",
                origin="synthetic",
                course_id="cs50_python",
                source_id=env.pv.source_id,
                format="code",
                root_key="fixture",
                permission="evaluation",
                permission_reference="Synthetic C2 test bytes only",
                selection=InventorySelection(
                    entry_id="synthetic-code-entry",
                    kind="material",
                    source_id=env.pv.source_id,
                    course_id="cs50_python",
                    expected_implementation_revision=REVISION,
                    bundle=env.bundle,
                ),
            ),
        ),
    )
    material_report = evaluate_materials(
        corpus,
        parsing,
        roots={"fixture": env.bundle.workspace},
        actor=OWNER,
        store=ContentStore(env.content.root, read_only=True),
    )
    assert len(material_report.report["results"]) == 5
    assert all(x["status"] == "passed" for x in material_report.report["results"])
    results = search(env, dataset)
    report = evaluate(env, results)
    standalone = evaluate_retrieval(
        dataset, results, evaluation_config=EvaluationConfig(schema_version=1)
    )
    assert report["value"]["report"]["digest"] == standalone.digest
    body = standalone.report
    assert body.query_count == 5 and body.evaluable_queries == 5
    assert body.precision_at_k.denominator == 5
    assert (
        body.recall_at_k.denominator
        == body.mrr_at_k.denominator
        == body.ndcg_at_k.denominator
        == 4
    )
    assert body.recall_at_k.value == body.mrr_at_k.value == body.ndcg_at_k.value == 1
    absent = next(q for q in body.queries if q.query_key == fingerprint("absent"))
    assert absent.recall_at_k.value is None
    assert (
        body.real_acceptance == "blocked" and body.live_authorization == "not_checked"
    )
    # Exact result bytes/digest survive reopening. No rebuild or migration on replay.
    snapshot = canonical(results.model_dump(mode="json"))
    env.index = ContentIndex(
        ContentStore(env.content.root), env.index.root, cursor_key_file=env.key
    )
    env.app = gateway(env.settings, env.tmp / "jobs")
    assert canonical(search(env, dataset).model_dump(mode="json")) == snapshot
    assert api(env, "GET", "/exports/gold") == exported
    assert api(env, "GET", "/reports/report")["value"] == report["value"]
    assert evaluate(env, results) == report  # Same idempotent intent.
    # Different request cannot overwrite the existing immutable report.
    api(
        env,
        "POST",
        "/reports/report",
        {
            **mutation(
                key="different",
                export_id="gold",
                results=results.model_dump(mode="json"),
            ),
            "reason": "Changed",
        },
        status=409,
    )
    history = api(env, "GET", "/tasks/hello-1/revisions")["items"]
    assert [x["value"]["status"] for x in history] == [
        "pending",
        "in_review",
        "confirmed",
    ]
    assert all(
        fingerprint({k: v for k, v in x.items() if k != "revision"}) == x["revision"]
        for x in history
    )
    assert inventory(env.content.root) == before
    assert inventory(env.bundle.workspace) == raw_before
    # Actual frozen run evidence, private/temporary only. No report reproduction
    # performs a hidden build or import, and output bytes cannot be overwritten.
    output = env.tmp / "snapshots"
    output.mkdir(mode=0o700)
    files = {
        "corpus.json": corpus.model_dump(mode="json"),
        "gold.json": exported,
        "results.json": results.model_dump(mode="json"),
        "report.json": standalone.model_dump(mode="json"),
        "parsing-report.json": material_report.model_dump(mode="json"),
        "query-plan.json": env.spec,
    }
    digests = {}
    for name, value in files.items():
        raw = canonical(value)
        with (output / name).open("xb") as handle:
            handle.write(raw)
        (output / name).chmod(0o600)
        digests[name] = sha256(raw)
    with (output / "manifest.json").open("xb") as handle:
        handle.write(
            canonical(dict(schema_version=1, origin="synthetic", files=digests))
        )
    assert all(
        sha256((output / name).read_bytes()) == digest
        for name, digest in digests.items()
    )
    with pytest.raises(FileExistsError):
        (output / "report.json").open("xb")


def test_incomplete_review_pool_never_becomes_negative_gold(pilot):
    annotate(pilot, "hello-1", 1, "hello", 3)
    dataset, _ = export(pilot)
    assert len(dataset.judgments) == 1 and not dataset.pools
    report = evaluate(pilot, search(pilot, dataset))["value"]["report"]["report"]
    assert report["evaluable_queries"] == 0
    assert report["recall_at_k"]["value"] is None
    assert report["recall_at_k"]["denominator"] == 0


def test_contradictory_original_gold_blocks_export(pilot):
    annotate(pilot, "positive", 1, "hello", 3)
    annotate(pilot, "contradiction", 1, "hello", 0)
    # Existing B1 returns unavailable for an invalid assembled gold export.
    api(pilot, "POST", "/exports/conflicting", mutation(), status=503)
    api(pilot, "GET", "/exports/conflicting", status=409)


@pytest.mark.parametrize("state", ["quarantined", "tombstoned"])
def test_status_change_blocks_gold_and_fts(pilot, state):
    annotate(pilot, "positive", 1, "hello", 3)
    export(pilot)
    with pilot.content._maintenance(), pilot.content._connection(write=True) as db:
        db.execute(
            "UPDATE parsed_versions SET state=? WHERE id=?",
            (state, pilot.pv.parsed_version_id),
        )
    with pytest.raises(RetrievalFault, match="stale_index"):
        hits(pilot.index, "hello", source_ids=(pilot.pv.source_id,))
    api(pilot, "GET", "/exports/gold", status=404)
    api(pilot, "GET", "/tasks/positive/region", status=404)


def test_content_read_access_is_not_review_access(pilot):
    from src.content_store.models import SourceGrant

    pilot.content.set_source_grants(
        pilot.pv.source_id,
        (SourceGrant(subject=VIEWER.subject),),
        expected_acl_revision=0,
        actor=OWNER,
    )
    assert hits(pilot.index, "hello", actor=VIEWER).items
    api(pilot, "GET", "/tasks", actor=VIEWER, status=404)
    pilot.content.set_source_grants(
        pilot.pv.source_id, (), expected_acl_revision=1, actor=OWNER
    )
    assert not hits(pilot.index, "hello", actor=VIEWER).items


def test_failed_report_commit_rolls_back_and_same_request_retries(pilot, monkeypatch):
    # Complete technical synthetic reviews, not human actions on a real corpus.
    review_all(pilot)
    dataset, _ = export(pilot)
    results = search(pilot, dataset)
    ledger = EvaluationStore(pilot.settings.root)
    with ledger.connection() as db:
        before = db.execute("SELECT count(*) FROM events").fetchone()[0]
    append = EvaluationStore.append
    injected = []

    def fail(cls, db, entity, actor, request, value, binding):
        reply = append(db, entity, actor, request, value, binding)
        if "/evaluate/" in entity:
            assert EvaluationStore.get(db, entity) == reply
            injected.append(reply["revision"])
            raise Unavailable("Synthetic failure after report insert before commit")
        return reply

    with monkeypatch.context() as patch:
        patch.setattr(EvaluationStore, "append", classmethod(fail))
        evaluate(pilot, results, status=503)
    assert len(injected) == 1  # Failure really occurred after the SQL insert.
    ledger = EvaluationStore(pilot.settings.root)
    with ledger.connection() as db:
        assert db.execute("SELECT count(*) FROM events").fetchone()[0] == before
    api(pilot, "GET", "/reports/report", status=404)
    saved = evaluate(pilot, results)
    assert api(pilot, "GET", "/reports/report")["value"] == saved["value"]


def test_readiness_revisions_preserve_real_access_blockers(monkeypatch):
    import json

    root = Path(__file__).resolve().parents[1] / "docs/cs50/evaluation/c24_05c"
    folders = (root, root / "r2", root / "r3")
    names = (
        "manifest.json",
        "corpus_manifest.v1.json",
        "gold_references.v1.json",
        "pilot_readiness.v1.json",
    )
    allowed = {folder / name for folder in folders for name in names}
    read = Path.read_bytes
    opened = []

    def metadata_only(path):
        assert path in allowed, "Original access forbidden in readiness validation"
        opened.append(path)
        return read(path)

    monkeypatch.setattr(Path, "read_bytes", metadata_only)
    snapshots = []
    for folder in folders:
        manifest = json.loads((folder / "manifest.json").read_bytes())
        assert set(manifest["files"]) == set(names) - {"manifest.json"}
        for name, digest in manifest["files"].items():
            assert sha256((folder / name).read_bytes()) == digest
        corpus = CorpusManifest.model_validate_json(
            (folder / "corpus_manifest.v1.json").read_bytes()
        )
        gold = GoldDataset.model_validate_json(
            (folder / "gold_references.v1.json").read_bytes()
        )
        report = json.loads((folder / "pilot_readiness.v1.json").read_bytes())
        assert fingerprint(report["report"]) == report["sha256"]
        assert (
            fingerprint(corpus.model_dump(mode="json"))
            == report["report"]["corpus_digest"]
        )
        assert (
            fingerprint(gold.model_dump(mode="json")) == report["report"]["gold_digest"]
        )
        assert not gold.references and len(corpus.entries) == 11
        assert all(
            e.origin == "real" and e.permission != "evaluation" for e in corpus.entries
        )
        snapshots.append((corpus, report))
    old, current = snapshots[1], snapshots[2]
    assert old[0].entries == current[0].entries
    assert current[1]["report"]["supersedes_sha256"] == old[1]["sha256"]
    report = current[1]["report"]
    assert not any(report["operations"].values())
    assert report["acceptance"]["status"] == "not_evaluable"
    assert report["retrieval_evaluation"]["metrics"] is None
    assert not report["request_authorization"]["original_file_reads_authorized"]
    assert all(s["status"] == "blocked" for s in report["sources"])
    assert set(opened) == allowed
