"""No lecture completion from partial, corrupt, unbound or unknown outputs."""

import json

import pytest
from test_cs50_knowledge_input import context as context
from test_cs50_lecture_runner import fake_factory, planned


def test_complete_and_irrelevant(context, tmp_path):
    from src.tools_knowledge.complete_cs50_lecture import complete_lecture
    from src.tools_knowledge.run_cs50_lecture import lecture_budget, run_lecture

    job = planned(context, tmp_path, cues=20)
    budget = lecture_budget([job], tmp_path / "budget")
    run_lecture(job, tmp_path / "job", budget, indices=[0])
    with pytest.raises(ValueError, match="incomplete"):
        complete_lecture(job, tmp_path / "job", budget)
    run_lecture(job, tmp_path / "job", budget)
    marker, values = complete_lecture(job, tmp_path / "job", budget)
    assert marker.phase == "done" and values["coverage"]["complete"]
    assert len(values["extraction"]["chunks"]) == len(job.chunks)
    assert all(r["extraction"] is None for r in values["extraction"]["chunks"])
    assert values["consolidated"]["statements"] == []
    assert complete_lecture(job, tmp_path / "job", budget) == (marker, values)
    assert type(marker).model_validate_json(marker.model_dump_json()) == marker


@pytest.mark.parametrize("artifact", ["extraction", "coverage", "marker"])
def test_corrupt_completion(context, tmp_path, artifact):
    from src.tools_knowledge.complete_cs50_lecture import FILES, complete_lecture
    from src.tools_knowledge.run_cs50_lecture import lecture_budget, run_lecture

    job = planned(context, tmp_path, cues=20)
    budget = lecture_budget([job], tmp_path / "budget")
    run_lecture(job, tmp_path / "job", budget, provider_factory=fake_factory([]))
    complete_lecture(job, tmp_path / "job", budget)
    path = (
        (tmp_path / "job" / "completion.v1.json")
        if artifact == "marker"
        else tmp_path / "job" / "completion" / FILES[artifact]
    )
    path.write_text("{corrupt")
    with pytest.raises(ValueError):
        complete_lecture(job, tmp_path / "job", budget)
    assert path.read_text() == "{corrupt"


def test_complete_publication_crash_recovery(context, tmp_path, monkeypatch):
    from src.tools_knowledge import complete_cs50_lecture as complete
    from src.tools_knowledge.run_cs50_lecture import lecture_budget, run_lecture

    job = planned(context, tmp_path, cues=20)
    budget = lecture_budget([job], tmp_path / "budget")
    run_lecture(job, tmp_path / "job", budget, provider_factory=fake_factory([]))
    publish = complete.atomic_json

    def crash(path, value, **kw):
        if path.name == "completion.v1.json":
            raise RuntimeError("before final marker")
        return publish(path, value, **kw)

    with monkeypatch.context() as patch:
        patch.setattr(complete, "atomic_json", crash)
        with pytest.raises(RuntimeError):
            complete.complete_lecture(job, tmp_path / "job", budget)
    marker, values = complete.complete_lecture(job, tmp_path / "job", budget)
    assert (
        marker.phase == "done"
        and values["consolidated"]["source_id"] == job.input.source_id
    )
    assert (
        values["coverage"]["expected_chunks"] == values["coverage"]["processed_chunks"]
    )


def test_foreign_chunk_receipt(context, tmp_path):
    from src.tools_knowledge.complete_cs50_lecture import complete_lecture
    from src.tools_knowledge.run_cs50_lecture import lecture_budget, run_lecture

    job = planned(context, tmp_path, cues=20)
    budget = lecture_budget([job], tmp_path / "budget")
    run_lecture(job, tmp_path / "job", budget)
    path = tmp_path / "job" / "checkpoint" / "checkpoint.v1.json"
    receipt = json.loads(path.read_text())
    receipt["chunks"]["foreign"] = receipt["chunks"][job.chunks[0].chunk_id]
    path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="checkpoint JSON/schema"):
        complete_lecture(job, tmp_path / "job", budget)
