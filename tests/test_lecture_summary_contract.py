"""Summary contracts against an existing, explicitly synthetic repository source.

No writable fixture is needed. Filesystem/cache tests live in test_lecture_summary.
"""

import json
from pathlib import Path

import httpx
import pytest

from src.content_store.models import sha256
from src.lecture_summary.exports import filename, render
from src.lecture_summary.models import (
    Artifact,
    Catalog,
    Claim,
    Formula,
    Lecture,
    Options,
    Selection,
)
from src.lecture_summary.providers import MockProvider, SummaryProvider
from src.lecture_summary.service import SummaryService
from src.lecture_summary.sources import collect
from src.lecture_summary.validation import validate
from src.tools_materials.storage import RegisteredStorage

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "docs/course_sources/cs50/examples/official_transcript.txt"


def fixture():
    # This tracked file says explicitly that it is a synthetic import example.
    artifact = Artifact(
        artifact_id="synthetic-import-example",
        storage_id="repo",
        relative_path=SOURCE,
        sha256=sha256((ROOT / SOURCE).read_bytes()),
        format="txt",
        title="Synthetisches Importbeispiel",
    )
    catalog = Catalog(
        lectures=tuple(
            Lecture(
                provider_id="synthetic",
                course_id="example",
                lecture_id=f"l{i}",
                title=f"Synthetische Auswahl {i}",
                sources=(artifact,),
            )
            for i in range(1, 4)
        )
    )
    storage = RegisteredStorage({"repo": {"path": str(ROOT), "readonly": True}})
    return catalog, storage


def selected(ids=("l1",), detail="compact"):
    return Selection(
        provider_id="synthetic",
        course_id="example",
        lecture_ids=ids,
        options=Options(detail=detail),
    )


@pytest.mark.parametrize("ids", [("l1",), ("l1", "l2", "l3")])
@pytest.mark.parametrize("detail", ["compact", "detailed"])
def test_actual_pipeline_and_print_exports_without_source_writes(ids, detail):
    catalog, storage = fixture()
    before = (ROOT / SOURCE).read_bytes()
    summary = SummaryService(catalog, storage, MockProvider()).generate(
        selected(ids, detail)
    )
    assert summary.validation_status == "needs_review"
    assert {e.lecture_id for e in summary.evidence} == set(ids)
    assert str(ROOT) not in summary.model_dump_json()
    markdown, latex = render(summary), render(summary, latex=True)
    assert "## Quellenverzeichnis" in markdown and "Café" in markdown
    assert r"\documentclass" in latex and r"\end{document}" in latex
    assert "@@BODY@@" not in latex
    assert all(filename(summary, ext).endswith("." + ext) for ext in ("md", "tex"))
    assert (ROOT / SOURCE).read_bytes() == before


@pytest.mark.parametrize(
    "change,reason",
    [
        ({"lecture_ids": ()}, "at least"),
        ({"lecture_ids": ("l1", "l2", "l3", "l4")}, "at most"),
        ({"lecture_ids": ("l1", "l1")}, "distinct"),
    ],
)
def test_selection_contract(change, reason):
    values = selected().model_dump()
    values.update(change)
    with pytest.raises(ValueError):
        Selection.model_validate(values)


def test_missing_lecture_fails_before_model_dispatch():
    catalog, storage = fixture()
    with pytest.raises(ValueError, match="Unknown"):
        SummaryService(catalog, storage, MockProvider()).generate(selected(("absent",)))


@pytest.mark.parametrize(
    "claim",
    [
        Claim(text="Invented reference", source_ids=("invented",)),
        Claim(text="Missing source", source_ids=()),
        Claim(
            text="External material",
            source_ids=(),
            kind="external",
            quality="unsupported",
        ),
    ],
)
def test_quality_gate_rejects_unbound_or_external_claims(claim):
    catalog, storage = fixture()
    evidence, _ = collect(catalog, selected(), storage)
    draft = (
        MockProvider()
        .generate(evidence, selected())
        .model_copy(update={"takeaways": (claim,)})
    )
    assert validate(draft, evidence, selected())[0] == "failed"


def test_literal_quotes_and_verified_formula_cannot_be_fabricated():
    catalog, storage = fixture()
    evidence, _ = collect(catalog, selected(), storage)
    draft = MockProvider().generate(evidence, selected())
    fake = Formula(
        text="x=42",
        latex="x=42",
        notation="x",
        assumptions="Keine",
        source_ids=(evidence[0].source_id,),
        evidence_quote="x=42",
        quality="verified_from_source",
    )
    changed = draft.model_copy(
        update={"topics": (draft.topics[0].model_copy(update={"formulas": (fake,)}),)}
    )
    status, messages = validate(changed, evidence, selected())
    assert status == "failed" and any("quote absent" in m for m in messages)


@pytest.mark.parametrize(
    "body",
    [
        None,
        [],
        {},
        {"choices": [{}]},
        {"choices": [{"finish_reason": "length"}]},
        {"choices": [{"finish_reason": "stop", "message": {}}]},
        {"choices": [{"finish_reason": "stop", "message": {"content": "{}"}}]},
    ],
)
def test_incomplete_provider_responses_are_rejected_once(body):
    catalog, storage = fixture()
    evidence, _ = collect(catalog, selected(), storage)
    provider = SummaryProvider(
        api_key="synthetic",
        model="test-model",
        allow_source_upload=True,
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=body)),
    )
    try:
        with pytest.raises(ValueError):
            provider.generate(evidence, selected())
        assert provider.budget.requests == 1
    finally:
        provider.close()


def test_http_mock_structured_generation_and_no_retry():
    catalog, storage = fixture()
    evidence, _ = collect(catalog, selected(), storage)
    draft = MockProvider().generate(evidence, selected())
    calls = []

    def handle(request):
        payload = json.loads(request.content)
        calls.append(payload)
        assert payload["store"] is False
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": draft.model_dump_json()},
                    }
                ]
            },
        )

    provider = SummaryProvider(
        api_key="synthetic",
        model="test-model",
        allow_source_upload=True,
        transport=httpx.MockTransport(handle),
    )
    try:
        result = SummaryService(catalog, storage, provider).generate(selected())
        assert result.validation_status == "needs_review"
        with pytest.raises(RuntimeError):
            provider.generate(evidence, selected())
        assert len(calls) == 1
    finally:
        provider.close()


def test_upload_requires_explicit_configuration_and_timeout_is_sanitized():
    with pytest.raises(PermissionError):
        SummaryProvider(api_key="synthetic", model="test-model")
    catalog, storage = fixture()
    evidence, _ = collect(catalog, selected(), storage)

    def timeout(request):
        raise httpx.ReadTimeout("private diagnostic must not escape")

    provider = SummaryProvider(
        api_key="synthetic",
        model="test-model",
        allow_source_upload=True,
        transport=httpx.MockTransport(timeout),
    )
    try:
        with pytest.raises(ValueError, match="timed out") as error:
            provider.generate(evidence, selected())
        assert "private diagnostic" not in str(error.value)
    finally:
        provider.close()
