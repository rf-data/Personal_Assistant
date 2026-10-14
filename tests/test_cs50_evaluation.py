"""Source integrity and honest blank review axes, not fabricated gold statements."""

import pytest
from test_cs50_knowledge_input import context as context
from test_cs50_lecture_runner import planned


def test_blank_actual_windows_and_roundtrip(context, tmp_path):
    from src.tools_knowledge.cs50_evaluation import (
        evaluation_counts,
        review_template,
        validate_review_set,
    )

    job = planned(context, tmp_path)
    template = review_template(job, origin="synthetic")
    assert len(template.windows) == 8 and all(not w.reviews for w in template.windows)
    assert validate_review_set(template, job) == template
    assert type(template).model_validate_json(template.model_dump_json()) == template
    counts = evaluation_counts(template)
    assert counts["claims"] == 0 and not counts["quality_established"]
    assert all(a["reviewed"] == 0 for a in counts["axes"].values())


@pytest.mark.parametrize(
    "field",
    ["source_id", "transcript_sha256", "provenance_sha256", "chunk_plan_sha256"],
)
def test_foreign_review_source(context, tmp_path, field):
    from src.tools_knowledge.cs50_evaluation import review_template, validate_review_set

    job = planned(context, tmp_path)
    template = review_template(job, origin="synthetic")
    with pytest.raises(ValueError, match="conflict"):
        validate_review_set(template.model_copy(update={field: "foreign"}), job)


def test_no_unauthored_judgments_or_foreign_cues(context, tmp_path):
    from src.tools_knowledge.cs50_evaluation import (
        ManualReview,
        review_template,
        validate_review_set,
    )

    with pytest.raises(ValueError, match="reviewer"):
        ManualReview(axes={"semantically_supported": True})
    with pytest.raises(ValueError, match="Duplicate"):
        ManualReview(segment_ids=(0, 0))
    job = planned(context, tmp_path)
    template = review_template(job, origin="synthetic")
    window = template.windows[0].model_copy(
        update={"reviews": (ManualReview(claim=None, segment_ids=(99999,)),)}
    )
    with pytest.raises(ValueError, match="review cue"):
        validate_review_set(template.model_copy(update={"windows": (window,)}), job)


def test_changed_cue_text_and_empty_cues_rejected(context, tmp_path):
    from test_cs50_knowledge_input import imported

    from src.tools_knowledge.cs50_evaluation import (
        ManualReview,
        review_template,
        validate_review_set,
    )
    from src.tools_knowledge.run_cs50_lecture import LectureRunConfig, prepare_lecture

    _, input = imported(context, tmp_path)
    job = prepare_lecture(
        context[3], input, workspace=tmp_path, config=LectureRunConfig()
    )
    template = review_template(job, origin="synthetic", indices=[0])
    window = template.windows[0]
    changed = window.cues[0].model_copy(update={"text": "changed"})
    forged = window.model_copy(update={"cues": (changed, *window.cues[1:])})
    with pytest.raises(ValueError, match="original chunk"):
        validate_review_set(template.model_copy(update={"windows": (forged,)}), job)
    empty = window.model_copy(update={"reviews": (ManualReview(segment_ids=(1,)),)})
    with pytest.raises(ValueError, match="review cue"):
        validate_review_set(template.model_copy(update={"windows": (empty,)}), job)
