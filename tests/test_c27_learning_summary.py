"""Offline contracts and acceptance; deterministic adapters only."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from scripts.lecture_summary_offline import run
from src.c27_learning_summary.adapter import (
    load_catalog,
    source_slices,
    transcript_blocks,
    validate_input,
)
from src.c27_learning_summary.engine import (
    SummaryRunError,
    bind_section,
    consolidate,
    generate,
)
from src.c27_learning_summary.export import markdown, visible_claims
from src.c27_learning_summary.llm import FakeLLM, LiteLLMSummaryModel, Reply
from src.c27_learning_summary.models import (
    Catalog,
    ClaimReview,
    Review,
    SectionResponse,
    SummaryConfig,
)
from src.c27_learning_summary.store import SummaryStore
from src.content_store.models import fingerprint
from src.model_transcribe.data_transcribe import TranscriptDocument, TranscriptSegment

FIXTURE = Path("tests/fixtures/lecture_summary/catalog.json")
SCOPE = ("synthetic_cs50p", "0", "lecture-0")
SELECTED = ["transcript", "notes", "code"]


@pytest.fixture
def catalog():
    return load_catalog(FIXTURE)


@pytest.fixture
def store(tmp_path):
    return SummaryStore(tmp_path / "store")


def generate_demo(store, catalog, model=None, config=None, **kwargs):
    return generate(
        store,
        catalog,
        *SCOPE,
        SELECTED,
        config or SummaryConfig(),
        model or FakeLLM(),
        **kwargs,
    )


def mutate(catalog, fn):
    data = catalog.model_dump(mode="json")
    material = data["courses"][0]["weeks"][0]["units"][0]["materials"][1]
    fn(material)
    if material["artifact"]:
        material["artifact"]["payload_sha256"] = fingerprint(material["blocks"])
    return Catalog.model_validate(data)


def test_navigation_missing_and_provenance(catalog):
    _, c, w, u, materials, warnings = validate_input(catalog, *SCOPE, SELECTED)
    assert c.course_id == SCOPE[0] and w.section_id == "0" and u.kind == "lecture"
    assert c.weeks[0].units[1].kind == "short"
    assert any("slides" in warning for warning in warnings)
    refs = source_slices(*SCOPE, materials, SummaryConfig())
    assert len(refs) == 7
    assert len({r.ref_id for r in refs}) == 7
    assert all(
        r.course_id == SCOPE[0] and r.parser_version and r.artifact_id and r.source_path
        for r in refs
    )
    assert any(r.locators[0].page == 1 for r in refs)
    assert any(r.locators[0].start == 5 for r in refs)
    assert any(r.locators[0].line_start == 1 for r in refs)


@pytest.mark.parametrize("selected", [[], ["slides"], ["foreign"], ["notes", "notes"]])
def test_invalid_selection(catalog, selected):
    with pytest.raises(ValueError):
        validate_input(catalog, *SCOPE, selected)


def test_unverified_and_unprocessed_blocked(catalog, store):
    for change in (
        lambda m: m.update(verification="unverified"),
        lambda m: m.update(processing_status="pending"),
    ):
        with pytest.raises(ValueError):
            generate_demo(store, mutate(catalog, change))
    assert not store.history()


def test_integrity_rejects_hash_locator_and_duplicate(catalog):
    for change in (
        lambda m: m.update(artifact={**m["artifact"], "payload_sha256": "0" * 64}),
        lambda m: m["blocks"][0]["locators"][0].update(raw_artifact_sha256="0" * 64),
        lambda m: m["blocks"].append(m["blocks"][0]),
    ):
        data = catalog.model_dump(mode="json")
        change(data["courses"][0]["weeks"][0]["units"][0]["materials"][1])
        with pytest.raises(ValueError):
            Catalog.model_validate(data)


def test_duplicate_course_and_unit(catalog):
    data = catalog.model_dump(mode="json")
    data["courses"].append(data["courses"][0])
    with pytest.raises(ValueError):
        Catalog.model_validate(data)


def test_transcript_unknown_time_and_duplicate_ids():
    segment = TranscriptSegment(seg_id=3, start=None, end=None, text="Unlocated text")
    doc = TranscriptDocument(source="local", text=segment.text, segments=[segment])
    blocks = transcript_blocks(doc, raw_sha256="a" * 64)
    assert blocks[0].locators[0].time_status == "unknown"
    assert blocks[0].locators[0].original_segment_id == 3
    with pytest.raises(ValueError):
        transcript_blocks(
            doc.model_copy(update={"segments": [segment, segment]}), raw_sha256="a" * 64
        )


def test_multiple_sections_dedup_cache_and_force(store, catalog):
    model = FakeLLM()
    first = generate_demo(store, catalog, model)
    assert first.result.state == "ready_for_review"
    assert len(first.result.sections) == model.calls == 7
    assert len(first.result.claims) == 6
    assert any(len(c.refs) == 2 for c in first.result.claims)
    again = generate_demo(store, catalog, model)
    assert again.from_cache and model.calls == 7
    assert again.result.run_id == first.result.run_id
    new = generate_demo(store, catalog, model, force=True)
    assert not new.from_cache and new.result.run_id != first.result.run_id
    assert store.result(first.result.run_id) == first.result


@pytest.mark.parametrize(
    "change",
    [
        lambda m: m["blocks"][0].update(text="Changed notes source."),
        lambda m: m["artifact"].update(parser_version="synthetic-2"),
        lambda m: m.update(verification="operator_verified"),
    ],
)
def test_material_cache_invalidation(store, catalog, change):
    before = generate_demo(store, catalog)
    after = generate_demo(store, mutate(catalog, change))
    assert not after.from_cache and before.result.cache_key != after.result.cache_key


@pytest.mark.parametrize(
    "changes",
    [
        {"prompt_version": "v2"},
        {"prompt": "Different instruction"},
        {"summary_type": "notes"},
        {"temperature": 0.5},
        {"chunk_chars": 300},
        {"input_usd_per_million": 2.0},
    ],
)
def test_config_cache_invalidation(store, catalog, changes):
    first = generate_demo(store, catalog)
    second = generate_demo(store, catalog, config=SummaryConfig(**changes))
    assert first.result.cache_key != second.result.cache_key and not second.from_cache


def test_selection_and_transcript_cache_invalidation(store, catalog):
    first = generate_demo(store, catalog)
    second = generate(store, catalog, *SCOPE, ["notes"], SummaryConfig(), FakeLLM())
    assert first.result.cache_key != second.result.cache_key
    data = catalog.model_dump(mode="json")
    material = data["courses"][0]["weeks"][0]["units"][0]["materials"][0]
    material["blocks"][0]["text"] = "Changed transcript"
    material["artifact"]["payload_sha256"] = fingerprint(material["blocks"])
    third = generate_demo(store, Catalog.model_validate(data))
    assert third.result.cache_key != first.result.cache_key


def ref_for(catalog, text=None):
    _, _, _, _, materials, _ = validate_input(catalog, *SCOPE, SELECTED)
    ref = source_slices(*SCOPE, materials, SummaryConfig())[0]
    return ref.model_copy(update={"text": text}) if text else ref


@pytest.mark.parametrize(
    "category,text,refs,reason",
    [
        ("key_point", "Invented claim", None, "unsupported_claim"),
        ("formula", "x = (", None, "invalid_or_unsupported_formula"),
        ("code", "print(", None, "invalid_python_code"),
        ("key_point", "Exact", ["0" * 64], "foreign_source"),
    ],
)
def test_reject_unsupported_formula_code_foreign_refs(
    catalog, category, text, refs, reason
):
    ref = ref_for(catalog, text if text != "Invented claim" else "Original")
    section = bind_section(
        SectionResponse(
            claims=[dict(category=category, text=text, refs=refs or [ref.ref_id])]
        ),
        ref,
    )
    assert not section.claims and any(reason in r for r in section.rejected)


def test_missing_references_schema():
    for claim in (
        {"category": "key_point", "text": "x"},
        {"category": "key_point", "text": "x", "refs": []},
    ):
        with pytest.raises(ValueError):
            SectionResponse(claims=[claim])


def test_conflicts_preserved(catalog):
    sections = []
    for text in (
        "A variable is a name.",
        "A variable is not a name.",
        "A variable is a container.",
    ):
        ref = ref_for(catalog, text)
        sections.append(
            bind_section(
                SectionResponse(
                    claims=[
                        dict(
                            category="definition",
                            text=text,
                            topic="variable",
                            refs=[ref.ref_id],
                        )
                    ]
                ),
                ref,
            )
        )
    claims, warnings = consolidate(sections)
    assert len(claims) == 3 and any("contradiction" in w for w in warnings)


class BrokenLLM(FakeLLM):
    def complete(self, *args, **kwargs):
        self.calls += 1
        if self.calls == 2:
            raise RuntimeError("SECRET_MUST_NOT_BE_SAVED")
        self.calls -= 1
        return super().complete(*args, **kwargs)


def test_failure_partial_and_secret_redaction(store, catalog):
    with pytest.raises(SummaryRunError) as caught:
        generate_demo(store, catalog, BrokenLLM())
    state = store.state(caught.value.run_id)
    assert state["status"] == "failed" and state["completed_sections"] == 1
    assert (
        len(list((store.run_path(caught.value.run_id) / "sections").glob("*.json")))
        == 1
    )
    assert not any(
        "SECRET_MUST_NOT_BE_SAVED" in p.read_text() for p in store.root.rglob("*.json")
    )
    assert not generate_demo(store, catalog).from_cache


def test_interruption_and_crash_recovery(store, catalog):
    class Interrupt(FakeLLM):
        def complete(self, *args, **kwargs):
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        generate_demo(store, catalog, Interrupt())
    assert store.history()[0]["status"] == "interrupted"
    stale = store.begin("0" * 64, {})
    with store.exclusive():
        assert store.state(stale)["status"] == "interrupted"


def test_duplicate_start_locked(store, catalog):
    with store.exclusive():
        with pytest.raises(RuntimeError, match="already running"):
            generate_demo(store, catalog)
    assert not store.history()


def test_limits_before_dispatch(store, catalog):
    backend = FakeLLM()
    with pytest.raises(ValueError, match="Chunk limit"):
        generate_demo(store, catalog, backend, SummaryConfig(max_chunks=1))
    assert backend.calls == 0 and not store.history()
    with pytest.raises(ValueError, match="identity"):
        generate_demo(store, catalog, LiteLLMSummaryModel("other"))


def test_timeout(store, catalog, monkeypatch):
    ticks = iter([0, 0, 200])
    monkeypatch.setattr(
        "src.c27_learning_summary.engine.time.monotonic", lambda: next(ticks)
    )
    with pytest.raises(SummaryRunError):
        generate_demo(store, catalog)
    assert store.history()[0]["status"] == "failed"


def test_retry_bounded_and_usage(store, catalog):
    class Retry(FakeLLM):
        failed = False

        def complete(self, *args, **kwargs):
            if not self.failed:
                self.failed = True
                return Reply("not JSON", {"input_tokens": 10, "output_tokens": 2})
            return super().complete(*args, **kwargs)

    outcome = generate_demo(
        store,
        catalog,
        Retry(),
        SummaryConfig(retries=1, input_usd_per_million=1, output_usd_per_million=2),
    )
    assert outcome.result.usage["calls"] == 8
    assert outcome.result.estimated_cost_usd == 14 / 1_000_000
    assert (
        len(list((store.run_path(outcome.result.run_id) / "raw").glob("*.json"))) == 9
    )


def test_review_append_only_integrity_and_export(store, catalog):
    result = generate_demo(store, catalog).result
    original = (store.run_path(result.run_id) / "result.json").read_bytes()
    with pytest.raises(ValueError, match="Approval"):
        store.save_review(
            Review(run_id=result.run_id, decision="approved", reviewer="tester")
        )
    claims = [ClaimReview(claim_id=c.claim_id, rating="correct") for c in result.claims]
    store.save_review(
        Review(
            run_id=result.run_id, decision="approved", reviewer="tester", claims=claims
        )
    )
    store.save_review(
        Review(
            run_id=result.run_id,
            decision="rejected",
            reviewer="tester",
            comment="Recheck",
        )
    )
    assert len(store.reviews(result.run_id)) == 2
    assert original == (store.run_path(result.run_id) / "result.json").read_bytes()
    exported = json.loads(store.export_json(result.run_id))
    assert exported["reviews"][0]["review"]["decision"] == "approved"
    md = markdown(result, store.reviews(result.run_id))
    assert "#source-1" in md and "SHA-256" in md and "segment=" in md and "lines=" in md
    assert "Decision: rejected" in md
    with pytest.raises(ValueError):
        store.run_path("../escape")
    path = store.run_path(result.run_id) / "result.json"
    path.write_bytes(original + b" ")
    with pytest.raises(ValueError, match="integrity"):
        store.result(result.run_id)


@pytest.mark.parametrize(
    "kind", ["overview", "structured", "notes", "glossary", "code"]
)
def test_output_formats(store, catalog, kind):
    result = generate_demo(
        store, catalog, config=SummaryConfig(summary_type=kind)
    ).result
    assert visible_claims(result)
    assert "Sources" in markdown(result)


def test_existing_llm_abstraction_without_sdk_network(monkeypatch):
    import sys
    from types import SimpleNamespace

    from src.llm.model_litellm import LLMClient

    calls = []
    completion = SimpleNamespace(
        choices=[
            SimpleNamespace(
                finish_reason="stop", message=SimpleNamespace(content='{"claims": []}')
            )
        ],
        usage=SimpleNamespace(prompt_tokens=3, completion_tokens=2),
    )
    monkeypatch.setitem(
        sys.modules,
        "litellm",
        SimpleNamespace(completion=lambda **kwargs: calls.append(kwargs) or completion),
    )
    config = SummaryConfig(provider="litellm", model="local/test")
    reply = LiteLLMSummaryModel(config.model).complete([], config=config, timeout=3)
    assert reply.usage == {"input_tokens": 3, "output_tokens": 2}
    assert calls[0]["num_retries"] == 0 and calls[0]["timeout"] == 3
    assert LLMClient.bounded(model="local/test").context is None


def test_legacy_llm_constructor_callbacks_cache_and_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import sys
    from types import SimpleNamespace
    from typing import Any

    from src.llm.model_litellm import LLMClient

    providers: list[str] = []
    dispatches: list[dict[str, Any]] = []
    cache_requests: list[dict[str, Any]] = []
    logger = object()

    def dispatch(**kwargs: Any) -> str:
        dispatches.append(kwargs)
        return "dispatched"

    def from_provider(name: str) -> str:
        providers.append(name)
        return "client"

    def cache_key(**kwargs: Any) -> str:
        cache_requests.append(kwargs)
        return "key"

    sdk = SimpleNamespace(completion=dispatch)
    monkeypatch.setitem(sys.modules, "litellm", sdk)
    monkeypatch.setitem(
        sys.modules,
        "instructor",
        SimpleNamespace(from_provider=from_provider),
    )
    monkeypatch.setitem(
        sys.modules,
        "src.core.logger",
        SimpleNamespace(create_logger=lambda **kwargs: logger),
    )
    cached: dict[str, str | None] = {"value": "cached"}
    monkeypatch.setitem(
        sys.modules,
        "src.utils.general_helper",
        SimpleNamespace(
            make_cache_key=cache_key,
            load_from_cache=lambda **kwargs: cached["value"],
        ),
    )
    context = SimpleNamespace(
        model="legacy/test",
        temperature=0.25,
        response_model=str,
        name_logger="r12-logger",
        name_logfile="r12-logfile",
        callbacks=["local-stub"],
    )
    client = LLMClient(context)
    messages = [{"role": "user", "content": "Synthetic request"}]
    assert providers == ["litellm/legacy/test"]
    assert client.logger is logger and client.response_model is str
    assert sdk.success_callback == context.callbacks
    assert client.completion(messages, timeout=2) == "cached"
    assert cache_requests == [{"message": messages, "model": "legacy/test"}]
    assert dispatches == []
    cached["value"] = None
    assert client.completion(messages, timeout=2) == "dispatched"
    assert dispatches == [
        dict(model="legacy/test", messages=messages, temperature=0.25, timeout=2)
    ]
    # Bounded callers retain the same dispatch interface and bypass legacy cache.
    assert LLMClient.bounded(model="bounded/test").completion(messages) == "dispatched"
    assert len(cache_requests) == 2
    assert dispatches[-1] == dict(
        model="bounded/test", messages=messages, temperature=0
    )


def test_offline_end_to_end(tmp_path):
    report = run(tmp_path)
    assert report["cache_reused"] and report["review"] == "approved"
    assert report["sections"] == 7
    assert (tmp_path / "summary.md").exists() and (tmp_path / "summary.json").exists()


@pytest.mark.parametrize("kind", ["html", "pdf", "code"])
def test_existing_processed_material_handoff(tmp_path, kind):
    from src.c27_learning_summary.adapter import material_handoff_blocks
    from src.tools_lecture.material_handoff import prepare_material_handoff
    from tests.content_adapter_support import material

    bundle, document = material(tmp_path, kind)
    review = prepare_material_handoff(
        workspace=bundle.workspace,
        raw_path=bundle.raw_path,
        normalized_path=bundle.normalized_path,
        receipt_path=bundle.receipt_path,
        plan_path=bundle.plan_path,
    )
    blocks = material_handoff_blocks(review)
    assert [b.block_id for b in blocks] == [b.block_id for b in document.blocks]
    assert all(b.locators[0].raw_artifact_sha256 == document.raw_sha256 for b in blocks)
    assert any(b.aggregation_role == "primary" for b in blocks)
    bundle.raw_path.write_bytes(b"changed raw source")
    rejected = prepare_material_handoff(
        workspace=bundle.workspace,
        raw_path=bundle.raw_path,
        normalized_path=bundle.normalized_path,
        receipt_path=bundle.receipt_path,
        plan_path=bundle.plan_path,
    )
    with pytest.raises(ValueError, match="quality gate"):
        material_handoff_blocks(rejected)


def test_invalid_output_never_approved_or_reused(store, catalog):
    class Unsupported(FakeLLM):
        def complete(self, messages, **kwargs):
            ref = json.loads(messages[-1]["content"])["excerpt"]
            return Reply(
                json.dumps(
                    {
                        "claims": [
                            {
                                "category": "key_point",
                                "text": "Invented unsupported knowledge",
                                "refs": [ref["ref_id"]],
                            }
                        ]
                    }
                )
            )

    first = generate_demo(store, catalog, Unsupported()).result
    assert first.state == "needs_attention" and not first.claims
    second = generate_demo(store, catalog, Unsupported())
    assert not second.from_cache
    with pytest.raises(ValueError, match="Approval"):
        store.save_review(
            Review(run_id=first.run_id, decision="approved", reviewer="tester")
        )


def test_serialized_input_byte_limit(store, catalog):
    model = FakeLLM()
    with pytest.raises(ValueError, match="input size"):
        generate_demo(
            store,
            catalog,
            model,
            SummaryConfig(prompt="字" * 4000, max_input_bytes=8000),
        )
    assert model.calls == 0 and not store.history()


def test_nonprimary_blocks_and_chunk_offsets(catalog):
    altered = mutate(
        catalog, lambda m: m["blocks"][0].update(aggregation_role="structure")
    )
    _, _, _, _, mats, _ = validate_input(altered, *SCOPE, SELECTED)
    refs = source_slices(*SCOPE, mats, SummaryConfig())
    assert not any(r.block_id == "notes:0" for r in refs)
    long = mutate(
        catalog, lambda m: m["blocks"][0].update(text="Local source text. " * 12)
    )
    _, _, _, _, mats, _ = validate_input(long, *SCOPE, SELECTED)
    refs = source_slices(*SCOPE, mats, SummaryConfig(chunk_chars=64))
    slices = [r for r in refs if r.block_id == "notes:0"]
    assert len(slices) > 1 and slices[1].offset_start == 64
    assert "".join(r.text for r in slices) == "Local source text. " * 12


@pytest.mark.parametrize(
    "rating,recheck", [("questionable", False), ("false", False), ("correct", True)]
)
def test_questionable_false_and_recheck_prevent_approval(
    store, catalog, rating, recheck
):
    result = generate_demo(store, catalog).result
    reviews = [
        ClaimReview(claim_id=c.claim_id, rating="correct") for c in result.claims
    ]
    reviews[0] = ClaimReview(
        claim_id=result.claims[0].claim_id,
        rating=rating,
        recheck=recheck,
        comment="Review evidence",
    )
    store.save_review(
        Review(
            run_id=result.run_id, decision="draft", reviewer="tester", claims=reviews
        )
    )
    with pytest.raises(ValueError, match="Approval"):
        store.save_review(
            Review(
                run_id=result.run_id,
                decision="approved",
                reviewer="tester",
                claims=reviews,
            )
        )
    assert (
        store.reviews(result.run_id)[-1]["review"]["claims"][0]["comment"]
        == "Review evidence"
    )


def test_failed_schema_keeps_raw_and_retries_are_bounded(store, catalog):
    class Invalid(FakeLLM):
        def complete(self, *args, **kwargs):
            self.calls += 1
            return Reply('{"claims":[{"category":"key_point","text":"No references"}]}')

    model = Invalid()
    with pytest.raises(SummaryRunError) as caught:
        generate_demo(store, catalog, model, SummaryConfig(retries=1))
    assert model.calls == 2
    root = store.run_path(caught.value.run_id)
    assert len(list((root / "raw").glob("*.json"))) == 4
    assert not (root / "result.json").exists()


def test_missing_usage_never_claims_full_cost(store, catalog):
    class MissingUsage(FakeLLM):
        def complete(self, *args, **kwargs):
            return replace(super().complete(*args, **kwargs), usage={})

    result = generate_demo(
        store,
        catalog,
        MissingUsage(),
        SummaryConfig(input_usd_per_million=1, output_usd_per_million=2),
    ).result
    assert result.usage["usage_missing_calls"] == 7
    assert result.estimated_cost_usd is None


def test_model_configuration_invalidates_cache(store, catalog, monkeypatch):
    class LocalFake(FakeLLM):
        provider = "litellm"
        model = "local/model-one"

    first = generate_demo(
        store,
        catalog,
        LocalFake(),
        SummaryConfig(provider="litellm", model="local/model-one"),
    )
    second_backend = LocalFake()
    second_backend.model = "local/model-two"
    second = generate_demo(
        store,
        catalog,
        second_backend,
        SummaryConfig(provider="litellm", model="local/model-two"),
    )
    assert not second.from_cache and first.result.cache_key != second.result.cache_key


def test_absent_scope_is_validation_error(catalog):
    with pytest.raises(ValueError, match="scope absent"):
        validate_input(catalog, "absent", "0", "lecture-0", SELECTED)
