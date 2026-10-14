import pytest
from test_cs50_ingestion import context as context
from test_cs50_ingestion import index_case as index_case

from src.tools_rag.cs50_retrieval_evaluation import (
    create_evaluation_template,
    ranking_metrics,
    reviewed_metrics,
)


def test_source_windows_are_real_cues_not_invented_gold(index_case):
    adapter, workspace, input, _, _, _ = index_case
    specs = [
        {
            "question": f"Synthetic infrastructure query {i}",
            "topic": "test only",
            "segment_ids": [0],
        }
        for i in range(10)
    ]
    template = create_evaluation_template(
        adapter,
        input,
        workspace=workspace,
        specifications=specs,
        source_origin="synthetic",
    )
    assert all(
        q.start == 0 and q.end == 5 and not q.relevance_reviewed
        for q in template.questions
    )
    assert type(template).model_validate_json(template.model_dump_json()) == template
    specs[0]["segment_ids"] = [99999]
    with pytest.raises(ValueError, match="actual"):
        create_evaluation_template(
            adapter,
            input,
            workspace=workspace,
            specifications=specs,
            source_origin="synthetic",
        )


def test_fake_scores_are_never_real_quality_metrics(index_case):
    adapter, workspace, input, _, plan, _ = index_case
    specs = [
        {
            "question": f"Technical test query {i}",
            "topic": "test only",
            "segment_ids": [0],
        }
        for i in range(10)
    ]
    template = create_evaluation_template(
        adapter,
        input,
        workspace=workspace,
        specifications=specs,
        source_origin="synthetic",
    )
    with pytest.raises(ValueError, match="Fake"):
        reviewed_metrics(template, [], {}, plan)


def test_ranking_arithmetic_toy_units_only():
    # This is arithmetic coverage, not an invented transcript gold set/benchmark.
    assert ranking_metrics([{1, 2}, {3}], [[2, 4], [0, 3]], k=2) == {
        "recall_at_k": 0.75,
        "mrr_at_k": 0.75,
    }
    with pytest.raises(ValueError):
        ranking_metrics([set()], [[]], k=5)
