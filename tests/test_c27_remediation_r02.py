"""Offline regressions for the five independently reported C27 blockers."""

import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import c27_reviewed_week as cli
from src.c27_learning_summary.adapter import load_catalog
from src.c27_learning_summary.engine import consolidate, generate
from src.c27_learning_summary.export import markdown
from src.c27_learning_summary.llm import FakeLLM, LiteLLMSummaryModel
from src.c27_learning_summary.models import (
    Catalog,
    Claim,
    Review,
    SectionResult,
    SummaryConfig,
    SummaryResult,
)
from src.c27_learning_summary.store import SummaryStore
from src.content_store.errors import IntegrityError
from src.content_store.models import fingerprint
from tests.test_c27_reviewed_week import review as review_fixture

FIXTURE = Path("tests/fixtures/lecture_summary/catalog.json")
SCOPE = ("synthetic_cs50p", "0", "lecture-0")
UNSAFE = (OSError, ValueError, IntegrityError)


@pytest.mark.parametrize(
    "component", ["root", "ancestor", "runs", "run", "lock", "state", "raw"]
)
def test_store_rejects_links_without_touching_external_data(tmp_path, component):
    outside = tmp_path / "external"
    outside.mkdir(mode=0o700)
    sentinel = outside / "state.json"
    sentinel.write_text('{"status":"running","sentinel":"unchanged"}')
    sentinel.chmod(0o600)
    before = sentinel.read_bytes()
    root = tmp_path / "store"
    if component in {"root", "ancestor"}:
        root.symlink_to(outside, target_is_directory=True)
        if component == "ancestor":
            root /= "child"
        with pytest.raises(UNSAFE):
            SummaryStore(root)
    else:
        store = SummaryStore(root)
        if component == "runs":
            (root / "runs").rmdir()
            (root / "runs").symlink_to(outside, target_is_directory=True)
        elif component == "run":
            (root / "runs" / ("a" * 32)).symlink_to(outside, target_is_directory=True)
        elif component == "lock":
            (root / ".run.lock").symlink_to(sentinel)
        else:
            run_id = store.begin("0" * 64, {})
            target = store.run_path(run_id) / component
            if component == "state":
                target = target.with_suffix(".json")
                target.unlink()
                target.symlink_to(sentinel)
            else:
                target.rmdir()
                target.symlink_to(outside, target_is_directory=True)
        with pytest.raises(UNSAFE):
            if component == "raw":
                store.write(run_id, "raw/state.json", {"bad": True})
            else:
                with store.exclusive():
                    pass
    assert sentinel.read_bytes() == before
    assert sorted(p.name for p in outside.iterdir()) == ["state.json"]


@pytest.mark.parametrize("component", ["root", "runs", "run", "lock"])
def test_store_rejects_existing_public_permissions(tmp_path, component):
    store = SummaryStore(tmp_path / "store")
    run_id = store.begin("0" * 64, {})
    paths = {
        "root": store.root,
        "runs": store.root / "runs",
        "run": store.run_path(run_id),
        "lock": store.root / ".run.lock",
    }
    with store.exclusive():
        pass
    target = paths[component]
    target.chmod(0o644 if component == "lock" else 0o755)
    before = store.read(run_id, "state.json") if component == "lock" else None
    with pytest.raises(UNSAFE):
        with store.exclusive():
            pass
    assert target.stat().st_mode & 0o077
    if before is not None:
        assert store.read(run_id, "state.json") == before


def test_store_rejects_foreign_owner(tmp_path, monkeypatch):
    root = tmp_path / "store"
    root.mkdir(mode=0o700)
    uid = os.getuid()
    monkeypatch.setattr("src.content_store.artifacts.os.getuid", lambda: uid + 1)
    with pytest.raises(IntegrityError):
        SummaryStore(root)
    assert list(root.iterdir()) == []


def test_store_rejects_existing_runs_link_during_initialization(tmp_path):
    root = tmp_path / "store"
    root.mkdir(mode=0o700)
    outside = tmp_path / "external"
    outside.mkdir(mode=0o700)
    sentinel = outside / "state.json"
    sentinel.write_bytes(b"unchanged")
    (root / "runs").symlink_to(outside, target_is_directory=True)
    with pytest.raises(UNSAFE):
        SummaryStore(root)
    assert sentinel.read_bytes() == b"unchanged"
    assert list(outside.iterdir()) == [sentinel]


@pytest.mark.parametrize("name", [".run.lock", "state.json"])
def test_store_rejects_hardlinked_files(tmp_path, name):
    store = SummaryStore(tmp_path / "store")
    run_id = store.begin("0" * 64, {})
    outside = tmp_path / "sentinel.json"
    outside.write_bytes(b'{"status":"running"}')
    outside.chmod(0o600)
    target = store.root / name if name == ".run.lock" else store.run_path(run_id) / name
    if target.exists():
        target.unlink()
    os.link(outside, target)
    with pytest.raises(IntegrityError):
        with store.exclusive():
            pass
    assert outside.read_bytes() == b'{"status":"running"}'


def test_store_rechecks_root_and_runs_identity(tmp_path):
    for component in ("root", "runs"):
        store = SummaryStore(tmp_path / component)
        target = store.root if component == "root" else store.root / "runs"
        target.rename(target.with_name(target.name + "-original"))
        target.mkdir(mode=0o700)
        with pytest.raises(ValueError, match="identity changed"):
            with store.exclusive():
                pass


def test_store_write_stays_on_open_directory_during_path_swap(tmp_path, monkeypatch):
    store = SummaryStore(tmp_path / "store")
    run_id = store.begin("0" * 64, {})
    outside = tmp_path / "external"
    outside.mkdir(mode=0o700)
    sentinel = outside / "state.json"
    sentinel.write_bytes(b"external sentinel")
    sentinel.chmod(0o600)
    run = store.run_path(run_id)
    original_replace = os.replace

    def swap_then_replace(*args, **kwargs):
        run.rename(run.with_name("retained-original"))
        run.symlink_to(outside, target_is_directory=True)
        return original_replace(*args, **kwargs)

    monkeypatch.setattr("src.c27_learning_summary.store.os.replace", swap_then_replace)
    store.write(run_id, "state.json", {"status": "interrupted"})
    assert sentinel.read_bytes() == b"external sentinel"
    assert (
        json.loads((run.with_name("retained-original") / "state.json").read_bytes())[
            "status"
        ]
        == "interrupted"
    )


def test_safe_store_recovery_and_new_run(tmp_path):
    store = SummaryStore(tmp_path / "store")
    stale = store.begin("0" * 64, {})
    with store.exclusive():
        assert store.state(stale)["status"] == "interrupted"
    reopened = SummaryStore(store.root)
    model = FakeLLM()
    first = generate(
        reopened, load_catalog(FIXTURE), *SCOPE, ["transcript"], SummaryConfig(), model
    )
    calls = model.calls
    second = generate(
        reopened, load_catalog(FIXTURE), *SCOPE, ["transcript"], SummaryConfig(), model
    )
    assert second.from_cache and first.result.run_id == second.result.run_id
    assert model.calls == calls
    assert reopened.state(stale)["status"] == "interrupted"


@pytest.mark.parametrize("count", [1, 16, 17, 24, 32])
def test_consolidation_preserves_every_reference_and_order(count):
    sections = []
    for i in range(count):
        ref = fingerprint(i)
        data = dict(category="key_point", text="A supported claim.", refs=[ref])
        claim = Claim(claim_id=fingerprint(data), **data)
        sections.append(
            SectionResult(title="Section", ref_id=ref, claims=[claim, claim])
        )
    claims, warnings = consolidate(sections)
    assert not warnings
    assert [len(c.refs) for c in claims] == [16] * (count // 16) + (
        [count % 16] if count % 16 else []
    )
    assert [r for c in claims for r in c.refs] == sorted(s.ref_id for s in sections)
    assert len({c.claim_id for c in claims}) == len(claims)
    assert consolidate(sections) == (claims, warnings)
    assert consolidate(list(reversed(sections))) == (claims, warnings)


def test_different_claims_keep_first_occurrence_order():
    ref = fingerprint("source")
    sections = []
    for text in ("First statement.", "Second statement.", "First statement."):
        data = dict(category="key_point", text=text, refs=[ref])
        sections.append(
            SectionResult(
                title="Section",
                ref_id=ref,
                claims=[Claim(claim_id=fingerprint(data), **data)],
            )
        )
    claims, _ = consolidate(sections)
    assert [c.text for c in claims] == ["First statement.", "Second statement."]


@pytest.mark.parametrize("count", [17, 24])
def test_repeated_claim_generates_once_per_chunk(tmp_path, count):
    data = load_catalog(FIXTURE).model_dump(mode="json")
    unit = data["courses"][0]["weeks"][0]["units"][0]
    material = unit["materials"][0]
    base = material["blocks"][0]
    material["blocks"] = [
        dict(base, block_id=f"repeat-{i}", order=i, text="A function returns a value.")
        for i in range(count)
    ]
    material["artifact"]["payload_sha256"] = fingerprint(material["blocks"])
    unit["materials"] = [material]
    model = FakeLLM()
    outcome = generate(
        SummaryStore(tmp_path / "store"),
        Catalog.model_validate(data),
        *SCOPE,
        [material["material_id"]],
        SummaryConfig(),
        model,
    )
    assert model.calls == count
    assert {r for c in outcome.result.claims for r in c.refs} == {
        r.ref_id for r in outcome.result.refs
    }
    assert all(len(c.refs) <= 16 for c in outcome.result.claims)


def review_input(tmp_path):
    return review_fixture.__wrapped__(tmp_path, SimpleNamespace(param="0"))


@pytest.mark.parametrize(
    "mode", ["success", "needs_attention", "rejected", "uncertainty"]
)
def test_cli_regular_states_export_and_repeat(tmp_path, monkeypatch, mode):
    root = review_input(tmp_path)
    if mode == "needs_attention":
        batch = root / "download-batch-01"
        raw = b"print( is an intentionally incomplete Python expression.\n"
        (batch / "functions.txt").write_bytes(raw)
        report_path = batch / "download-report.json"
        report = json.loads(report_path.read_bytes())
        entry = next(e for e in report["files"] if e["filename"] == "functions.txt")
        entry.update(
            bytes=len(raw), sha256=__import__("hashlib").sha256(raw).hexdigest()
        )
        report["total_bytes"] = sum(e["bytes"] for e in report["files"])
        report_path.write_text(json.dumps(report))

    class Model(FakeLLM):
        total_calls = 0

        def complete(self, *args, **kwargs):
            type(self).total_calls += 1
            reply = super().complete(*args, **kwargs)
            data = json.loads(reply.raw)
            if mode == "rejected":
                data["claims"][0]["text"] = "Not present in any supplied source."
            elif mode == "uncertainty":
                data["uncertainties"] = ["Requires source review"]
            reply.raw = json.dumps(data)
            return reply

    monkeypatch.setattr(cli, "FakeLLM", Model)
    output = tmp_path / "output"
    first = cli.run(root, output, fake_summary=True)
    assert len(first["summaries"]) == 2
    store = SummaryStore(output / "summaries")
    first_calls = Model.total_calls
    assert len(store.history()) == 2
    assert first_calls == sum(s["sections"] for s in first["summaries"])
    for summary in first["summaries"]:
        expected = (
            "needs_attention"
            if mode in {"rejected", "uncertainty"}
            or (mode == "needs_attention" and summary["unit_id"] == "short")
            else "ready_for_review"
        )
        assert summary["state"] == expected
        assert summary["cache_verified"] == (expected == "ready_for_review")
        assert store.read(summary["run_id"], "export.md")
        assert json.loads(store.read(summary["run_id"], "export.json"))
    second = cli.run(root, output, fake_summary=True)
    attention = [s for s in first["summaries"] if s["state"] == "needs_attention"]
    assert len(store.history()) == 2 + len(attention)
    assert Model.total_calls == first_calls + sum(s["sections"] for s in attention)
    assert len(second["summaries"]) == 2


def test_cli_invalid_input_is_explicit(tmp_path):
    root = review_input(tmp_path)
    with pytest.raises(ValueError, match="Explicit unique"):
        cli.run(root, tmp_path / "output", fake_summary=True, material_ids=["unknown"])
    (root / "download-batch-01/functions.txt").write_bytes(b"tampered")
    with pytest.raises(ValueError):
        cli.run(root, tmp_path / "other", fake_summary=True)


def test_cli_cache_miss_does_not_generate_again(tmp_path, monkeypatch):
    root = review_input(tmp_path)
    monkeypatch.setattr(SummaryStore, "cached", lambda *args: None)
    result = cli.run(root, tmp_path / "output", fake_summary=True)
    assert all(
        not s["cache_verified"] and s["cache_verification_error"]
        for s in result["summaries"]
    )
    assert all(s["fake_calls"] == s["sections"] for s in result["summaries"])


@pytest.mark.parametrize(
    "url,license_text",
    [
        ("https://cs50.harvard.edu/python/2022/weeks/0/", "CC BY-NC-SA 4.0"),
        ("https://cs50.harvard.edu/python/2022/weeks/0/", None),
        (None, "CC BY-NC-SA 4.0"),
    ],
)
def test_standalone_exports_preserve_available_provenance(tmp_path, url, license_text):
    data = load_catalog(FIXTURE).model_dump(mode="json")
    material = data["courses"][0]["weeks"][0]["units"][0]["materials"][0]
    material["resource"].update(source_url=url, license=license_text, title="Functions")
    material["attribution"] = "CS50, Harvard University"
    store = SummaryStore(tmp_path / "store")
    result = generate(
        store,
        Catalog.model_validate(data),
        *SCOPE,
        [material["material_id"]],
        SummaryConfig(),
        FakeLLM(),
    ).result
    assert result.schema_version == 2
    store.save_review(
        Review(run_id=result.run_id, decision="draft", reviewer="offline-reviewer")
    )
    exported = json.loads(store.export_json(result.run_id))
    restored = SummaryResult.model_validate(exported["result"])
    assert restored == result
    assert exported["review_status"] == "draft"
    md = markdown(result, store.reviews(result.run_id))
    assert "Review status: draft" in md and "offline-reviewer" in md
    for ref in restored.refs:
        assert ref.provenance.source_url == url
        assert ref.provenance.license == license_text
        assert ref.provenance.attribution == material["attribution"]
        assert (
            ref.material_id == material["material_id"]
            and ref.source_id == material["source_id"]
        )
        assert ref.content_hash == material["resource"]["content_hash"]
        assert ref.locators and ref.block_id and ref.ref_id
        assert ref.content_hash in md and ref.source_id in md
    assert material["attribution"] in md
    if url:
        assert url in md and url in json.dumps(exported)
    else:
        assert "Original URL: missing" in md
    if license_text:
        assert license_text in md
    else:
        assert "License:" not in md


@pytest.mark.parametrize(
    "url",
    [
        "https://user:SECRET@example.org/source",
        "https://example.org/source?token=SECRET",
        "https://example.org/source#SECRET",
        "https://example.org/token/SECRET",
        "https://example.org/api_key=SECRET",
        "https://example.org/%74oken/SECRET",
        "https://localhost/SECRET",
        "https://127.0.0.1/SECRET",
        "https://private.internal/SECRET",
        "https://example.org/\nSECRET",
        "file:///SECRET",
    ],
)
def test_sensitive_source_urls_are_withheld_in_both_exports(tmp_path, url):
    data = load_catalog(FIXTURE).model_dump(mode="json")
    material = data["courses"][0]["weeks"][0]["units"][0]["materials"][0]
    material["resource"]["source_url"] = url
    store = SummaryStore(tmp_path / "store")
    result = generate(
        store,
        Catalog.model_validate(data),
        *SCOPE,
        [material["material_id"]],
        SummaryConfig(),
        FakeLLM(),
    ).result
    assert all(
        r.provenance.source_url is None and r.provenance.source_url_status == "withheld"
        for r in result.refs
    )
    assert "SECRET" not in markdown(result)
    assert "SECRET" not in store.export_json(result.run_id)
    assert "withheld" in markdown(result)


def test_actual_legacy_result_is_read_without_rewriting_or_inventing_metadata(tmp_path):
    from src.content_store.models import sha256

    legacy = json.loads(Path("docs/lecture_summary/example-summary.json").read_bytes())[
        "result"
    ]
    assert legacy["schema_version"] == 1
    store = SummaryStore(tmp_path / "store")
    run_id = legacy["run_id"]
    with store.directory(f"runs/{run_id}/reviews", create=True):
        pass
    store.write(run_id, "result.json", legacy)
    raw = store.read(run_id, "result.json")
    store.write(
        run_id,
        "state.json",
        dict(
            run_id=run_id,
            status="completed",
            cache_key=legacy["cache_key"],
            result_sha256=sha256(raw),
            started_ns=1,
        ),
    )
    result = store.result(run_id)
    assert result.schema_version == 2 and all(r.provenance is None for r in result.refs)
    assert store.read(run_id, "result.json") == raw
    assert "unknown (legacy result)" in markdown(result)
    exported = json.loads(store.export_json(run_id))
    assert exported["review_status"] == "unreviewed"
    assert SummaryResult.model_validate(exported["result"]) == result
    old_hash = store.state(run_id)["result_sha256"]
    store.save_review(Review(run_id=run_id, reviewer="legacy-reader", decision="draft"))
    assert store.reviews(run_id)[0]["result_sha256"] == old_hash
    assert store.read(run_id, "result.json") == raw
    future = dict(legacy, schema_version=99)
    with pytest.raises(ValueError):
        SummaryResult.model_validate(future)


def test_reviewed_material_attribution_reaches_export(tmp_path):
    root = review_input(tmp_path)
    path = root / "download-batch-01/download-report.json"
    report = json.loads(path.read_bytes())
    for entry in report["files"]:
        entry["attribution"] = "Synthetic CS50 attribution"
    path.write_text(json.dumps(report))
    output = tmp_path / "output"
    result = cli.run(root, output, fake_summary=True)
    store = SummaryStore(output / "summaries")
    for summary in result["summaries"]:
        md = store.read(summary["run_id"], "export.md").decode()
        exported = json.loads(store.read(summary["run_id"], "export.json"))
        assert "Synthetic CS50 attribution" in md
        assert all(
            r["provenance"]["attribution"] == "Synthetic CS50 attribution"
            for r in exported["result"]["refs"]
        )


def test_cli_repeat_exports_current_review_without_overwriting_earlier_export(tmp_path):
    root = review_input(tmp_path)
    output = tmp_path / "output"
    first = cli.run(root, output, fake_summary=True)
    store = SummaryStore(output / "summaries")
    summary = first["summaries"][0]
    original = store.read(summary["run_id"], "export.json")
    store.save_review(
        Review(run_id=summary["run_id"], reviewer="offline-reviewer", decision="draft")
    )
    second = cli.run(root, output, fake_summary=True)
    current = next(s for s in second["summaries"] if s["run_id"] == summary["run_id"])
    assert current["fake_calls"] == 0 and current["cache_verified"]
    assert current["exports"]["json"].startswith("export-review-")
    assert store.read(summary["run_id"], "export.json") == original
    assert (
        json.loads(store.read(summary["run_id"], current["exports"]["json"]))[
            "review_status"
        ]
        == "draft"
    )
    assert (
        "Review status: draft"
        in store.read(summary["run_id"], current["exports"]["markdown"]).decode()
    )


@pytest.mark.parametrize(
    "provided,expected",
    [
        (
            {"prompt_tokens": 7, "completion_tokens": 3},
            {"input_tokens": 7, "output_tokens": 3},
        ),
        (None, {}),
        ({}, {}),
        ({"prompt_tokens": 7}, {"input_tokens": 7}),
        ({"completion_tokens": 3}, {"output_tokens": 3}),
        ({"prompt_tokens": 7, "completion_tokens": None}, {"input_tokens": 7}),
        ({"prompt_tokens": None, "completion_tokens": 3}, {"output_tokens": 3}),
        ({"prompt_tokens": -1, "completion_tokens": 3}, {"output_tokens": 3}),
        ({"prompt_tokens": "7", "completion_tokens": 3}, {"output_tokens": 3}),
        ({"prompt_tokens": 7.0, "completion_tokens": True}, {}),
        (
            {"prompt_tokens": 0, "completion_tokens": 0},
            {"input_tokens": 0, "output_tokens": 0},
        ),
    ],
)
@pytest.mark.parametrize("mapping", [False, True])
def test_provider_usage_is_known_only_for_valid_integer_fields(
    tmp_path, monkeypatch, provided, expected, mapping
):
    from src.llm.model_litellm import LLMClient

    fake = FakeLLM()

    def completion(messages, **kwargs):
        raw = fake.complete(messages, config=SummaryConfig(), timeout=1).raw
        usage = provided if provided is None or mapping else SimpleNamespace(**provided)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    finish_reason="stop", message=SimpleNamespace(content=raw)
                )
            ],
            usage=usage,
        )

    monkeypatch.setattr(
        LLMClient,
        "bounded",
        classmethod(lambda cls, **kwargs: SimpleNamespace(completion=completion)),
    )
    config = SummaryConfig(
        provider="litellm",
        model="offline/stub",
        input_usd_per_million=1,
        output_usd_per_million=1,
    )
    model = LiteLLMSummaryModel(config.model)
    # Exercise the adapter itself and its aggregation contract, without a provider.
    from src.c27_learning_summary.adapter import source_slices
    from src.c27_learning_summary.engine import messages_for

    catalog = load_catalog(FIXTURE)
    ref = source_slices(
        *SCOPE, [catalog.courses[0].weeks[0].units[0].materials[0]], config
    )[0]
    assert (
        model.complete(messages_for(ref, config), config=config, timeout=1).usage
        == expected
    )
    result = generate(
        SummaryStore(tmp_path / "store"), catalog, *SCOPE, ["transcript"], config, model
    ).result
    count = result.usage["calls"]
    complete = len(expected) == 2
    assert result.usage["usage_missing_calls"] == (0 if complete else count)
    for direction in ("input", "output"):
        name = f"{direction}_tokens"
        if name in expected:
            assert result.usage[name] == expected[name] * count
            assert result.usage[f"{direction}_usage_missing_calls"] == 0
        else:
            assert name not in result.usage
            assert result.usage[f"{direction}_usage_missing_calls"] == count
    assert (result.estimated_cost_usd is not None) == complete


def test_usage_becomes_unknown_after_a_later_partial_reply(tmp_path):
    class Partial(FakeLLM):
        def complete(self, *args, **kwargs):
            reply = super().complete(*args, **kwargs)
            reply.usage = (
                {"input_tokens": 7, "output_tokens": 3}
                if self.calls == 1
                else {"input_tokens": 0}
            )
            return reply

    result = generate(
        SummaryStore(tmp_path / "store"),
        load_catalog(FIXTURE),
        *SCOPE,
        ["transcript"],
        SummaryConfig(input_usd_per_million=1, output_usd_per_million=1),
        Partial(),
    ).result
    assert result.usage["calls"] > 1
    assert result.usage["input_tokens"] == 7
    assert "output_tokens" not in result.usage
    assert result.usage["known_output_tokens"] == 3
    assert result.usage["output_usage_missing_calls"] == result.usage["calls"] - 1
    assert result.estimated_cost_usd is None
