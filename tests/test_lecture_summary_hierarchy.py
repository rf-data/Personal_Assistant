"""Controlled map/reduce responses, original evidence gates, budgets and recovery."""

import json
import socket

import httpx
import pytest

from src.content_store.models import sha256
from src.lecture_summary.exports import render
from src.lecture_summary.hierarchy import HierarchyFailure, bound, payload
from src.lecture_summary.models import (
    Artifact,
    Catalog,
    Formula,
    HierarchyPolicy,
    Lecture,
    SectionDraft,
    Selection,
)
from src.lecture_summary.providers import MockProvider, SummaryProvider
from src.lecture_summary.service import SummaryService
from src.tools_materials.storage import RegisteredStorage


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(
        socket.socket, "connect", lambda *a, **kw: pytest.fail("No real network")
    )


class Counting(MockProvider):
    def __init__(self):
        self.calls = []

    def hierarchical(self, req, result_type):
        self.calls.append(req)
        return super().hierarchical(req, result_type)


@pytest.fixture
def setup(tmp_path):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    (tmp_path / "cache").mkdir()
    storage = RegisteredStorage(
        {
            "source": {"path": str(inputs), "readonly": True},
            "work": {"path": str(tmp_path), "readonly": False},
        }
    )

    def make(
        count=1,
        blocks=8,
        *,
        text="Synthetische Vektoren und Voraussetzungen.",
        provider=None,
        policy=None,
        transcript=True,
    ):
        lectures = []
        for no in range(count):
            name = f"l{no}.json" if transcript else f"l{no}.txt"
            raw = (
                json.dumps(
                    dict(
                        source="synthetic",
                        text=text,
                        segments=[
                            dict(
                                seg_id=i,
                                start=i,
                                end=i + 1,
                                text=f"{text} Abschnitt {i}.",
                            )
                            for i in range(blocks)
                        ],
                    ),
                    ensure_ascii=False,
                ).encode()
                if transcript
                else text.encode()
            )
            (inputs / name).write_bytes(raw)
            artifact = Artifact(
                artifact_id=f"a{no}",
                storage_id="source",
                relative_path=name,
                sha256=sha256(raw),
                format="transcript_json" if transcript else "txt",
                role="derived" if transcript else "original",
                title="Synthetic source",
            )
            lectures.append(
                Lecture(
                    provider_id="synthetic",
                    course_id="example",
                    lecture_id=f"l{no}",
                    title=f"Synthetic lecture {no}",
                    sources=(artifact,),
                )
            )
        selected = Selection(
            provider_id="synthetic",
            course_id="example",
            lecture_ids=tuple(lecture.lecture_id for lecture in lectures),
        )
        model = provider or Counting()
        service = SummaryService(
            Catalog(lectures=tuple(lectures)),
            storage,
            model,
            cache=("work", "cache"),
            hierarchy=policy or HierarchyPolicy(),
        )
        return service, selected, model

    return make, tmp_path


@pytest.mark.parametrize("count", [1, 2, 3])
def test_complete_hierarchy_original_refs_cache_and_visible_coverage(setup, count):
    make, root = setup
    service, selection, model = make(count)
    before = {p: p.read_bytes() for p in (root / "inputs").iterdir()}
    plan = service.preflight(selection)
    result = service.generate(selection)
    assert (
        result.validation_status == "needs_review"
        and result.processing.status == "complete"
    )
    assert len(model.calls) == count + 1 == plan["max_requests"]
    assert len(result.processing.mapped_source_ids) == count * 8
    assert len(result.processing.uncited_source_ids) > 0
    assert all(s.startswith("evidence:") for s in result.processing.final_source_ids)
    assert "Hierarchischer Lauf" in render(result) and "nicht zitiert" in render(
        result, latex=True
    )
    cached = service.generate(selection)
    assert len(model.calls) == count + 1 and cached.content == result.content
    assert (
        cached.processing.requests_this_invocation == 0
        and cached.processing.cached_stages == count + 1
    )
    assert before == {p: p.read_bytes() for p in before}
    assert result.prompt_version == "lecture-hierarchy-de-v1"


def test_default_simple_mode_remains_single_call(setup):
    make, _ = setup
    service, selection, model = make()
    simple = SummaryService(
        service.catalog, service.storage, model, cache=service.cache
    )
    assert simple.strategy == "simple" and simple.preflight(selection) is None
    assert simple.generate(selection).processing is None
    assert not model.calls


@pytest.mark.parametrize(
    "policy",
    [
        HierarchyPolicy(total_token_limit=1),
        HierarchyPolicy(reduce_input_limit=4000),
        HierarchyPolicy(section_input_limit=4000),
        HierarchyPolicy(max_calls=2),
        HierarchyPolicy(max_sections=1),
        HierarchyPolicy(input_microusd_per_million=1000000, max_cost_microusd=1),
    ],
)
def test_preflight_rejects_all_budget_failures_without_dispatch(setup, policy):
    make, root = setup
    service, selection, model = make(2, policy=policy)
    with pytest.raises(ValueError):
        service.generate(selection)
    assert model.calls == [] and not list((root / "cache").iterdir())


@pytest.mark.parametrize(
    "policy",
    [
        dict(total_token_limit=64001),
        dict(section_input_limit=30001),
        dict(section_output_limit=2001),
        dict(max_calls=8),
        dict(max_sections=7),
    ],
)
def test_policy_cannot_raise_existing_or_strategy_hard_ceilings(policy):
    with pytest.raises(ValueError):
        HierarchyPolicy(**policy)


def test_live_requires_explicit_cost_assumptions_before_any_call(setup):
    make, _ = setup
    model = Counting()
    model.offline = False
    service, selection, _ = make(provider=model)
    with pytest.raises(ValueError, match="price assumptions"):
        service.generate(selection)
    assert not model.calls


def test_missing_source_and_existing_collection_ceiling_remain_fail_closed(setup):
    make, root = setup
    service, selection, model = make()
    (root / "inputs/l0.json").rename(root / "inputs/unavailable.json")
    with pytest.raises(FileNotFoundError):
        service.generate(selection)
    assert not model.calls
    service, selection, model = make(blocks=161)
    with pytest.raises(ValueError, match="context limit"):
        service.generate(selection)
    assert not model.calls
    service, selection, model = make(blocks=6, text="x" * 5000)
    with pytest.raises(ValueError, match="context limit"):
        service.generate(selection)
    assert not model.calls


def test_full_160_blocks_are_processed_without_input_sampling(setup):
    make, _ = setup
    service, selection, _ = make(blocks=160, text="Synthetic.")
    result = service.generate(selection)
    assert len(result.processing.mapped_source_ids) == len(result.evidence) == 160
    assert result.processing.uncited_source_ids  # Explicitly disclosed Mock sampling.
    assert (
        result.processing.final_section_ids == result.processing.completed_section_ids
    )


def test_deterministic_natural_source_order_independent_of_selection_order(setup):
    make, _ = setup
    service, selection, model = make(2, blocks=12)
    result = service.generate(
        selection.model_copy(
            update={"lecture_ids": tuple(reversed(selection.lecture_ids))}
        )
    )
    messages = [json.loads(r["messages"][1]["content"]) for r in model.calls[:-1]]
    assert [m["sources"][0]["lecture_id"] for m in messages] == ["l0", "l1"]
    assert [s["text"].rsplit(" ", 1)[1] for s in messages[0]["sources"]] == [
        f"{i}." for i in range(12)
    ]
    assert len(result.processing.completed_section_ids) == 2


def test_interruption_between_stages_resumes_validated_prefix(setup):
    make, _ = setup
    service, selection, model = make(2)
    with pytest.raises(HierarchyFailure) as failure:
        service.generate(selection, cancelled=lambda: len(model.calls) == 1)
    report = failure.value.report
    assert report.status == "incomplete" and len(report.completed_section_ids) == 1
    assert report.requests_reserved == 1 and not report.final_source_ids
    result = service.generate(selection)
    assert result.processing.status == "complete" and len(model.calls) == 3
    assert result.processing.requests_reserved == 3


def test_failed_unknown_attempt_is_never_retried_on_resume(setup):
    make, _ = setup

    class Fail(Counting):
        def hierarchical(self, req, result_type):
            if len(self.calls) == 1:
                self.calls.append(req)
                raise ValueError("Synthetic partial failure")
            return super().hierarchical(req, result_type)

    service, selection, model = make(2, provider=Fail())
    with pytest.raises(HierarchyFailure) as error:
        service.generate(selection)
    assert len(error.value.report.completed_section_ids) == 1
    with pytest.raises(HierarchyFailure, match="retry forbidden"):
        service.generate(selection)
    assert len(model.calls) == 2


def test_corrupt_intermediate_cache_is_rejected_without_model_repair(setup):
    make, root = setup
    service, selection, model = make()
    service.generate(selection)
    cache = next((root / "cache").glob("hs-*.json"))
    cache.write_bytes(b"{")
    with pytest.raises(HierarchyFailure):
        service.generate(selection)
    assert len(model.calls) == 2


def test_cache_invalidation_for_source_version_options_and_model(setup):
    make, root = setup
    service, selection, model = make()
    first = service.generate(selection)
    detail = selection.model_copy(
        update={"options": selection.options.model_copy(update={"detail": "detailed"})}
    )
    assert (
        service.generate(detail).summary_id != first.summary_id
        and len(model.calls) == 4
    )
    model.model = "mock-controlled-other"
    assert (
        service.generate(selection).summary_id != first.summary_id
        and len(model.calls) == 6
    )
    (root / "inputs/l0.json").write_bytes(b"changed")
    with pytest.raises(ValueError, match="version changed"):
        service.generate(selection)
    assert len(model.calls) == 6


def test_cached_result_model_metadata_must_match_its_versioned_key(setup):
    make, root = setup
    service, selection, model = make()
    service.generate(selection)
    path = next((root / "cache").glob("hs-*.json"))
    record = json.loads(path.read_bytes())
    record["model"] = "different-model"
    path.write_text(json.dumps(record))
    with pytest.raises(HierarchyFailure, match="cache identity/model/prompt mismatch"):
        service.generate(selection)
    assert len(model.calls) == 2


def test_final_request_overflow_stops_without_silent_reduction(setup):
    make, _ = setup
    service, selection, model = make()
    floor = bound(payload("consolidate", [], selection, model.model, 2000))
    service.hierarchy = HierarchyPolicy(reduce_input_limit=floor + 10)
    with pytest.raises(HierarchyFailure, match="reserved request size") as error:
        service.generate(selection)
    assert len(model.calls) == 1 and len(error.value.report.completed_section_ids) == 1


def test_unknown_alias_and_oversized_partial_fail_before_consolidation(setup):
    make, _ = setup

    class Bad(Counting):
        def hierarchical(self, req, result_type):
            result = super().hierarchical(req, result_type)
            return result.model_copy(
                update={
                    "claims": (
                        result.claims[0].model_copy(update={"source_ids": ("Q999",)}),
                    )
                }
            )

    service, selection, model = make(provider=Bad())
    with pytest.raises(HierarchyFailure, match="alias"):
        service.generate(selection)
    assert len(model.calls) == 1


def test_oversized_partial_is_not_cached_or_consolidated(setup):
    make, root = setup

    class TooLarge(Counting):
        def hierarchical(self, req, result_type):
            result = super().hierarchical(req, result_type)
            return result.model_copy(update={"notices": ("x" * 3000,)})

    service, selection, model = make(provider=TooLarge())
    with pytest.raises(HierarchyFailure, match="byte limit"):
        service.generate(selection)
    assert len(model.calls) == 1 and not list((root / "cache").glob("hs-*.json"))


def test_concurrent_exclusive_reservation_prevents_duplicate_dispatch(
    setup, monkeypatch
):
    make, root = setup
    service, selection, model = make()
    original = service.storage.create

    def race(storage_id, name, data):
        if "/ha-" in name:
            original(storage_id, name, data)  # Synthetic other invocation won.
        return original(storage_id, name, data)

    monkeypatch.setattr(service.storage, "create", race)
    with pytest.raises(HierarchyFailure, match="concurrently reserved"):
        service.generate(selection)
    assert not model.calls


def test_readonly_cache_and_cancellation_before_collection_do_not_dispatch(setup):
    make, _ = setup
    service, selection, model = make()
    with pytest.raises(InterruptedError):
        service.generate(selection, cancelled=lambda: True)
    service.cache = ("source", "cache")
    with pytest.raises(PermissionError):
        service.generate(selection)
    assert not model.calls


def test_omitted_sections_are_explicitly_reported(setup):
    make, _ = setup

    class Omit(Counting):
        def hierarchical(self, req, result_type):
            draft = super().hierarchical(req, result_type)
            if result_type is SectionDraft:
                return draft
            topic = draft.topics[0].model_copy(
                update={"explanations": draft.topics[0].explanations[:1]}
            )
            return draft.model_copy(update={"topics": (topic,)})

    service, selection, _ = make(
        blocks=100,
        text="Synthetic context and notation." * 2,
        provider=Omit(),
        policy=HierarchyPolicy(section_input_limit=18000),
    )
    result = service.generate(selection)
    assert len(result.processing.section_ids) > 1
    assert result.processing.omitted_section_ids
    assert "Abschnitte ohne Quellenzitat" in render(result)


def test_final_invented_source_or_quote_cannot_replace_original_backing(setup):
    make, _ = setup

    class Fabricate(Counting):
        def hierarchical(self, req, result_type):
            result = super().hierarchical(req, result_type)
            if result_type is SectionDraft:
                return result
            first = (
                result.topics[0]
                .explanations[0]
                .model_copy(update={"evidence_quote": "Invented original text"})
            )
            return result.model_copy(
                update={
                    "topics": (
                        result.topics[0].model_copy(update={"explanations": (first,)}),
                    )
                }
            )

    service, selection, _ = make(provider=Fabricate())
    with pytest.raises(HierarchyFailure, match="quote absent"):
        service.generate(selection)


def test_source_change_during_generation_prevents_export(setup):
    make, root = setup

    class Change(Counting):
        def hierarchical(self, req, result_type):
            result = super().hierarchical(req, result_type)
            if result_type is not SectionDraft:
                (root / "inputs/l0.json").write_bytes(b"synthetic concurrent change")
            return result

    service, selection, _ = make(provider=Change())
    with pytest.raises(HierarchyFailure, match="version changed") as error:
        service.generate(selection)
    assert error.value.report.status == "incomplete"


class FormulaMock(Counting):
    def __init__(self, *, verify_final=False):
        super().__init__()
        self.verify_final = verify_final

    def hierarchical(self, req, result_type):
        result = super().hierarchical(req, result_type)
        data = json.loads(req["messages"][1]["content"])
        source = data["sources"][0]
        expression = "x=2" if "x=2" in source["text"] else "x=1"
        formula = Formula(
            text=expression,
            latex=expression,
            notation="x: synthetische Testgröße",
            assumptions="Nur synthetische Testannahme",
            evidence_quote=expression,
            source_ids=(source["source_id"],),
            quality="uncertain",
        )
        if result_type is SectionDraft:
            return result.model_copy(update={"formulas": (formula,)})
        if self.verify_final:
            formula = formula.model_copy(update={"quality": "verified_from_source"})
            return result.model_copy(
                update={
                    "topics": (
                        result.topics[0].model_copy(update={"formulas": (formula,)}),
                    )
                }
            )
        return result


def test_uncertain_formula_cannot_become_verified_even_if_original_is_literal(setup):
    make, _ = setup
    service, selection, _ = make(
        text="x=1", transcript=False, provider=FormulaMock(verify_final=True)
    )
    with pytest.raises(HierarchyFailure, match="cannot verify"):
        service.generate(selection)


def test_transcript_formula_requires_visual_status_at_intermediate_stage(setup):
    make, _ = setup
    service, selection, _ = make(text="x=1", provider=FormulaMock())
    with pytest.raises(HierarchyFailure, match="visual review"):
        service.generate(selection)


def test_visual_requirement_propagates_to_final_formula(setup):
    make, _ = setup

    class Visual(FormulaMock):
        def hierarchical(self, req, result_type):
            result = super().hierarchical(req, result_type)
            if result_type is SectionDraft:
                return result.model_copy(
                    update={
                        "formulas": tuple(
                            f.model_copy(update={"quality": "requires_visual_context"})
                            for f in result.formulas
                        )
                    }
                )
            topic = result.topics[0]
            return result.model_copy(
                update={
                    "topics": (
                        topic.model_copy(
                            update={
                                "formulas": tuple(
                                    f.model_copy(update={"quality": "uncertain"})
                                    for f in topic.formulas
                                )
                            }
                        ),
                    )
                }
            )

    service, selection, _ = make(text="x=1", transcript=False, provider=Visual())
    with pytest.raises(HierarchyFailure, match="preserve.*visual"):
        service.generate(selection)


def test_conflicting_formula_variants_remain_visible_in_both_exports(setup):
    make, root = setup
    service, selection, _ = make(
        2, text="x=1", transcript=False, provider=FormulaMock()
    )
    path = root / "inputs/l1.txt"
    path.write_text("x=2")
    lecture = service.catalog.lectures[1]
    changed = lecture.sources[0].model_copy(
        update={"sha256": sha256(path.read_bytes())}
    )
    service.catalog = Catalog(
        lectures=(
            service.catalog.lectures[0],
            lecture.model_copy(update={"sources": (changed,)}),
        )
    )
    result = service.generate(selection)
    assert len(result.processing.formula_variants) == 2
    for latex in (False, True):
        text = render(result, latex=latex)
        assert "x=1" in text and "x=2" in text and "Formelwiderspruch" in text
        assert "synthetische Testgröße" in text and "Testannahme" in text


def test_http_adapter_reuses_transport_budget_and_decodes_both_schemas(setup):
    make, _ = setup
    controlled = MockProvider()
    calls = []

    def respond(request):
        req = json.loads(request.content)
        calls.append(req)
        stage = json.loads(req["messages"][1]["content"])["stage"]
        from src.lecture_summary.models import Draft

        result = controlled.hierarchical(
            req, SectionDraft if stage == "section" else Draft
        )
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": result.model_dump_json()},
                    }
                ]
            },
        )

    provider = SummaryProvider(
        api_key="synthetic",
        model="synthetic-http",
        allow_source_upload=True,
        transport=httpx.MockTransport(respond),
    )
    try:
        policy = HierarchyPolicy(
            input_microusd_per_million=1000000,
            output_microusd_per_million=4000000,
            max_cost_microusd=1000000,
        )
        service, selection, _ = make(provider=provider, policy=policy)
        result = service.generate(selection)
        assert len(calls) == 2 and result.processing.status == "complete"
        assert all(
            bound(c) <= 30000 and c["max_completion_tokens"] <= 2000 for c in calls
        )
        assert result.processing.cost_upper_bound_microusd <= policy.max_cost_microusd
    finally:
        provider.close()


def test_unknown_transcript_times_keep_original_locators_without_timed_chunking(setup):
    make, root = setup
    service, selection, _ = make()
    path = root / "inputs/l0.json"
    raw = json.loads(path.read_bytes())
    for segment in raw["segments"]:
        segment.update(start=None, end=None)
    path.write_text(json.dumps(raw))
    lecture = service.catalog.lectures[0]
    source = lecture.sources[0].model_copy(update={"sha256": sha256(path.read_bytes())})
    service.catalog = Catalog(
        lectures=(lecture.model_copy(update={"sources": (source,)}),)
    )
    result = service.generate(selection)
    assert all(
        e.locator.time_status == "unknown" and e.locator.start is None
        for e in result.evidence
    )
    assert [e.locator.original_segment_id for e in result.evidence] == list(range(8))


def test_versioned_offline_setup_and_three_case_demo_are_reproducible(
    tmp_path, monkeypatch
):
    from scripts.lecture_summary_acceptance import SOURCES
    from scripts.lecture_summary_acceptance import prepare as prepare_single
    from scripts.lecture_summary_hierarchy import demo, prepare
    from src.lecture_summary.local import load_service

    inputs = tmp_path / "originals"
    folder = inputs / "loviscach/mathe_1/transcripts"
    folder.mkdir(parents=True)
    for lecture, stem, _ in SOURCES:
        (folder / f"{lecture}_{stem}.json").write_text(
            json.dumps(
                dict(
                    source="synthetic",
                    text="Explicitly synthetic source.",
                    segments=[
                        dict(
                            seg_id=0,
                            start=0,
                            end=1,
                            text="Explicitly synthetic source.",
                        )
                    ],
                )
            )
        )
    baseline = prepare_single(inputs, tmp_path / "baseline")
    monkeypatch.setattr(
        httpx, "Client", lambda **kw: pytest.fail("No HTTP client in offline demo")
    )
    config = prepare(baseline, tmp_path / "hierarchy")
    assert load_service(config, offline_only=True).strategy == "hierarchical"
    assert (
        load_service(config.parent / "summary.simple.json", offline_only=True).strategy
        == "simple"
    )
    report = demo(config, tmp_path / "exports", "controlled-label")
    assert report["paid_api_calls"] == 0 and report["all_source_fingerprints_unchanged"]
    assert set(report["cases"]) == {"text", "formulas", "group"}
    assert len(list((tmp_path / "exports").glob("*/*.tex"))) == 6
    assert all(
        case["hierarchy_processing"]["status"] == "complete"
        for case in report["cases"].values()
    )
    repeated = demo(config, tmp_path / "exports-cached", "controlled-label")
    assert all(
        not case["actual_mock_dispatches"] for case in repeated["cases"].values()
    )
    with pytest.raises(FileExistsError):
        prepare(baseline, config.parent)
