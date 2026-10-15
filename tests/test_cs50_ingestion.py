from contextlib import closing

import pytest
from qdrant_client import QdrantClient
from test_cs50_knowledge_input import context as context
from test_cs50_knowledge_input import imported
from test_cs50_lecture_runner import body

from src.model_discovery.cs50_index import EmbeddingConfig
from src.tools_rag.cs50_embeddings import FakeEmbedder
from src.tools_rag.cs50_ingestion import (
    IngestionPlan,
    UploadState,
    build_ingestion_plan,
    embed_plan,
    selected_bindings,
    upsert_plan,
)


@pytest.fixture
def index_case(context, tmp_path):
    from src.core.config_knowledge import KnowledgeSettings

    _, _, _, adapter = context
    workspace = tmp_path / "sources"
    workspace.mkdir()
    _, input = imported(context, workspace, body=body(20))
    engine = FakeEmbedder(EmbeddingConfig.fake(max_tokens=64))
    plan = build_ingestion_plan(
        adapter,
        [input],
        KnowledgeSettings(),
        engine,
        workspace=workspace,
        course="cs50_python",
        section="0",
        source_origin="synthetic",
    )
    vectors = embed_plan(
        plan,
        adapter,
        engine,
        workspace=workspace,
        destination=tmp_path / "vectors.json",
    )
    return adapter, workspace, input, engine, plan, vectors


def test_plan_vectors_roundtrip_dry_run_and_repeat(index_case, tmp_path):
    adapter, workspace, input, engine, plan, vectors = index_case
    assert IngestionPlan.model_validate_json(plan.model_dump_json()) == plan
    assert len(plan.units) > 2
    again = embed_plan(
        plan,
        adapter,
        engine,
        workspace=workspace,
        destination=tmp_path / "vectors.json",
    )
    assert again == vectors
    with closing(QdrantClient(":memory:")) as client:
        preview = upsert_plan(
            client,
            plan,
            vectors,
            adapter,
            workspace=workspace,
            state_root=tmp_path / "state",
        )
        assert preview["dry_run"] and not client.get_collections().collections
        done = upsert_plan(
            client,
            plan,
            vectors,
            adapter,
            workspace=workspace,
            state_root=tmp_path / "state",
            execute=True,
            allow_create=True,
            batch_size=2,
        )
        assert done.status == "done" and done.verified_points == len(plan.units)
        assert (
            upsert_plan(
                client,
                plan,
                vectors,
                adapter,
                workspace=workspace,
                state_root=tmp_path / "state",
                execute=True,
            )
            == done
        )
        assert client.count(plan.collection.name).count == len(plan.units)


def test_interruption_after_actual_write_resume(index_case, tmp_path, monkeypatch):
    adapter, workspace, _, _, plan, vectors = index_case
    with closing(QdrantClient(":memory:")) as client:
        real = client.upsert
        calls = []

        def lost_ack(*args, **kwargs):
            result = real(*args, **kwargs)
            calls.append(result)
            if len(calls) == 1:
                raise TimeoutError("Simulated lost acknowledgement")
            return result

        monkeypatch.setattr(client, "upsert", lost_ack)
        with pytest.raises(TimeoutError):
            upsert_plan(
                client,
                plan,
                vectors,
                adapter,
                workspace=workspace,
                state_root=tmp_path / "state",
                execute=True,
                allow_create=True,
                batch_size=2,
            )
        receipt = tmp_path / "state" / plan.collection.name / (plan.plan_id + ".json")
        assert UploadState.model_validate_json(receipt.read_bytes()).status == "failed"
        assert client.count(plan.collection.name).count == 2
        done = upsert_plan(
            client,
            plan,
            vectors,
            adapter,
            workspace=workspace,
            state_root=tmp_path / "state",
            execute=True,
            batch_size=2,
        )
        assert done.status == "done"
        assert client.count(plan.collection.name).count == len(plan.units)


def test_payload_corruption_never_adopted(index_case, tmp_path):
    adapter, workspace, _, _, plan, vectors = index_case
    with closing(QdrantClient(":memory:")) as client:
        upsert_plan(
            client,
            plan,
            vectors,
            adapter,
            workspace=workspace,
            state_root=tmp_path / "state",
            execute=True,
            allow_create=True,
        )
        client.set_payload(
            plan.collection.name,
            {"source_id": "foreign"},
            points=[plan.units[0].point_id],
        )
        with pytest.raises(ValueError, match="Foreign"):
            upsert_plan(
                client,
                plan,
                vectors,
                adapter,
                workspace=workspace,
                state_root=tmp_path / "state",
                execute=True,
            )


def test_missing_sources_and_changed_artifacts(index_case, tmp_path):
    from src.core.config_knowledge import KnowledgeSettings

    adapter, workspace, input, engine, plan, vectors = index_case
    with pytest.raises(ValueError, match="Missing validated"):
        build_ingestion_plan(
            adapter,
            [input],
            KnowledgeSettings(),
            engine,
            workspace=workspace,
            course="cs50_python",
        )
    assert len(selected_bindings(adapter, all_six=True)) == 50
    input.raw_srt_path.write_text("changed")
    with pytest.raises(ValueError, match="hash conflict"):
        embed_plan(plan, adapter, engine, workspace=workspace)


def test_stale_plan_and_invalid_receipt(index_case, tmp_path):
    from src.core.config_knowledge import KnowledgeSettings

    adapter, workspace, input, engine, plan, vectors = index_case
    with closing(QdrantClient(":memory:")) as client:
        upsert_plan(
            client,
            plan,
            vectors,
            adapter,
            workspace=workspace,
            state_root=tmp_path / "state",
            execute=True,
            allow_create=True,
        )
        changed = build_ingestion_plan(
            adapter,
            [input],
            KnowledgeSettings(target_duration=20),
            engine,
            workspace=workspace,
            course="cs50_python",
            section="0",
        )
        changed_vectors = embed_plan(changed, adapter, engine, workspace=workspace)
        with pytest.raises(ValueError, match="Stale"):
            upsert_plan(
                client,
                changed,
                changed_vectors,
                adapter,
                workspace=workspace,
                state_root=tmp_path / "other",
                execute=True,
            )
        receipt = tmp_path / "state" / plan.collection.name / (plan.plan_id + ".json")
        receipt.write_text("{broken")
        with pytest.raises(ValueError):
            upsert_plan(
                client,
                plan,
                vectors,
                adapter,
                workspace=workspace,
                state_root=tmp_path / "state",
                execute=True,
            )


def test_outputs_cannot_touch_sources(index_case, tmp_path):
    adapter, workspace, input, engine, plan, _ = index_case
    with pytest.raises(ValueError, match="separate"):
        embed_plan(
            plan,
            adapter,
            engine,
            workspace=workspace,
            destination=input.raw_srt_path.parent / "vectors.json",
        )


def test_ack_without_points_is_not_complete(index_case, tmp_path, monkeypatch):
    adapter, workspace, _, _, plan, vectors = index_case
    with closing(QdrantClient(":memory:")) as client:
        monkeypatch.setattr(client, "upsert", lambda *a, **kw: None)
        with pytest.raises(ValueError, match="expected points missing"):
            upsert_plan(
                client,
                plan,
                vectors,
                adapter,
                workspace=workspace,
                state_root=tmp_path / "state",
                execute=True,
                allow_create=True,
            )
        receipt = tmp_path / "state" / plan.collection.name / (plan.plan_id + ".json")
        assert UploadState.model_validate_json(receipt.read_bytes()).status == "failed"


def test_replaced_source_in_same_lecture_cannot_leave_old_points(index_case, tmp_path):
    from qdrant_client.models import PointStruct

    adapter, workspace, _, _, plan, vectors = index_case
    with closing(QdrantClient(":memory:")) as client:
        upsert_plan(
            client,
            plan,
            vectors,
            adapter,
            workspace=workspace,
            state_root=tmp_path / "state",
            execute=True,
            allow_create=True,
        )
        old = plan.units[0].model_copy(
            update={"source_id": "prior-source", "resource_id": "prior-resource"}
        )
        client.upsert(
            plan.collection.name,
            points=[
                PointStruct(
                    id=old.point_id,
                    vector=list(vectors.vectors[0]),
                    payload=old.model_dump(mode="json"),
                )
            ],
            wait=True,
        )
        with pytest.raises(ValueError, match="Replaced source"):
            upsert_plan(
                client,
                plan,
                vectors,
                adapter,
                workspace=workspace,
                state_root=tmp_path / "state",
                execute=True,
            )


def test_missing_declared_version_not_filled_by_pydantic_defaults(index_case, tmp_path):
    adapter, workspace, _, _, plan, vectors = index_case
    with closing(QdrantClient(":memory:")) as client:
        upsert_plan(
            client,
            plan,
            vectors,
            adapter,
            workspace=workspace,
            state_root=tmp_path / "state",
            execute=True,
            allow_create=True,
        )
        client.delete_payload(
            plan.collection.name,
            ["ingestion_schema_version"],
            points=[plan.units[0].point_id],
        )
        with pytest.raises(ValueError, match="explicit required"):
            upsert_plan(
                client,
                plan,
                vectors,
                adapter,
                workspace=workspace,
                state_root=tmp_path / "state",
                execute=True,
            )
