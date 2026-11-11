"""Presentation must preserve full provenance while disclosing bounded Mock sampling."""

import json
import socket

import pytest

from scripts.lecture_summary import registered_lecture
from src.lecture_summary.exports import cited_source_ids, render, tex_evidence
from src.lecture_summary.models import Catalog, Options, Selection
from src.lecture_summary.providers import MockProvider
from src.lecture_summary.service import SummaryService
from src.tools_materials.storage import RegisteredStorage


@pytest.fixture
def summary_factory(tmp_path, monkeypatch):
    monkeypatch.setattr(
        socket.socket, "connect", lambda *a, **kw: pytest.fail("No network")
    )
    path = tmp_path / "synthetic.json"
    path.write_text(
        json.dumps(
            {
                "source": "synthetic",
                "text": "Synthetisches Testmaterial.",
                "segments": [
                    {
                        "seg_id": i,
                        "start": i + 0.123456,
                        "end": i + 0.987654,
                        "text": f"Synthetischer Ausschnitt {i}, absichtlich ohne Satzende",
                    }
                    for i in range(25)
                ],
            }
        )
    )
    lecture = registered_lecture(
        tmp_path, path.name, "synthetic", "example", "l1", "Test", "transcript_json"
    )
    service = SummaryService(
        Catalog(lectures=(lecture,)),
        RegisteredStorage({"source": {"path": str(tmp_path), "readonly": True}}),
        MockProvider(),
    )

    def generate(detail="compact"):
        return service.generate(
            Selection(
                provider_id="synthetic",
                course_id="example",
                lecture_ids=("l1",),
                options=Options(detail=detail),
            )
        )

    return generate


@pytest.mark.parametrize("detail,count", [("compact", 2), ("detailed", 4)])
def test_mock_sampling_bibliography_and_full_evidence(summary_factory, detail, count):
    summary = summary_factory(detail)
    before = summary.model_dump_json()
    assert len(summary.evidence) == 25 and len(cited_source_ids(summary)) == count
    for latex in (False, True):
        text = render(summary, latex=latex)
        assert f"{count} von 25" in text
        assert (
            "Demonstrationsausschnitt" in text
            and "möglicherweise unvollständig" in text
        )
        assert "keine vollständige didaktische Synthese" in text
        assert "Q1:" in text and f"Q{count}:" in text and "Q25:" not in text
        assert "Q25:" in render(summary, latex=latex, include_all_evidence=True)
        assert "0.12–0.99 s" in text and "0.123456" not in text
    assert summary.model_dump_json() == before  # Exact values never rounded in JSON.
    assert summary.evidence[0].locator.start == 0.123456


def test_sparse_citations_keep_original_q_labels(summary_factory):
    summary = summary_factory()
    claim = (
        summary.content.topics[0]
        .explanations[0]
        .model_copy(update={"source_ids": (summary.evidence[24].source_id,)})
    )
    # The renderer does not renumber evidence after filtering. Validation remains upstream.
    content = summary.content.model_copy(
        update={
            "learning_objectives": (),
            "takeaways": (),
            "topics": (
                summary.content.topics[0].model_copy(
                    update={"explanations": (claim,), "questions": ()}
                ),
            ),
        }
    )
    text = render(summary.model_copy(update={"content": content}))
    assert "Q25:" in text and "Q1:" not in text


def test_unknown_time_is_not_zero(summary_factory):
    summary = summary_factory()
    first = summary.evidence[0]
    unknown = first.locator.model_copy(
        update={"start": None, "end": None, "time_status": "unknown"}
    )
    summary = summary.model_copy(
        update={
            "evidence": (
                first.model_copy(update={"locator": unknown}),
                *summary.evidence[1:],
            )
        }
    )
    first_entry = render(summary).split("- Q1:")[1].split("- Q2:")[0]
    assert "Zeitstatus unknown" in first_entry and " s; Segment" not in first_entry


def test_tex_long_ids_have_breaks_without_accepting_commands():
    digest = "abcdef0123456789" * 4
    encoded = tex_evidence("evidence:" + digest + r" \input{/etc/passwd} a_b%{x}&")
    assert r"\allowbreak{}" in encoded and digest not in encoded
    assert encoded.replace(r"\allowbreak{}", "").startswith("evidence:" + digest)
    assert r"\input{" not in encoded
    assert r"\textbackslash{}input\{/etc/passwd\}" in encoded
    assert r"a\_b\%\{x\}\&" in encoded
