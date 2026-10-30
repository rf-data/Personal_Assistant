"""C27 deterministic acceptance, synthetic sources only; no paid calls or services."""

import json
import socket
from pathlib import Path

import httpx
import pytest

from src.content_store.models import sha256
from src.lecture_summary.exports import filename, render, tex_escape
from src.lecture_summary.inventory import inventory
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


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(
        socket.socket, "connect", lambda *a, **k: pytest.fail("Unexpected network")
    )


@pytest.fixture
def context(tmp_path):
    (tmp_path / "cache").mkdir()
    lectures = []
    for i in range(1, 4):
        text = f"Synthetische Lektion {i}: Vektoren besitzen Komponenten. x_{i}=2\n"
        (tmp_path / f"l{i}.txt").write_text(text)
        artifact = Artifact(
            artifact_id=f"artifact:{i}",
            storage_id="local",
            relative_path=f"l{i}.txt",
            sha256=sha256(text.encode()),
            format="txt",
            title=f"Quelle {i}",
        )
        lectures.append(
            Lecture(
                provider_id="synthetic",
                course_id="mathe",
                lecture_id=f"l{i}",
                title=f"Lektion {i}",
                sources=(artifact,),
            )
        )
    catalog = Catalog(lectures=tuple(lectures))
    storage = RegisteredStorage({"local": {"path": str(tmp_path), "readonly": False}})
    return catalog, storage, tmp_path


def selection(ids=("l1",), **kwargs):
    return Selection(
        provider_id="synthetic", course_id="mathe", lecture_ids=ids, **kwargs
    )


@pytest.mark.parametrize("ids", [("l1",), ("l1", "l2", "l3")])
def test_single_and_three_lectures(context, ids):
    catalog, storage, root = context
    before = {p.name: p.read_bytes() for p in root.glob("*.txt")}
    result = SummaryService(catalog, storage, MockProvider()).generate(selection(ids))
    assert result.validation_status == "needs_review"
    assert set(result.content.processed_lecture_ids) == set(ids)
    assert {e.lecture_id for e in result.evidence} == set(ids)
    assert (
        len(result.content.topics) == 1
    )  # Combined thematic draft, not appended summaries.
    assert before == {p.name: p.read_bytes() for p in root.glob("*.txt")}
    assert result.schema_version == 1 and result.created_at.tzinfo


@pytest.mark.parametrize("ids", [(), ("l1",) * 2, ("l1", "l2", "l3", "l4")])
def test_selection_bounds(ids):
    with pytest.raises(ValueError):
        selection(ids)


def test_missing_invalid_and_conflicting_sources(context):
    catalog, storage, root = context
    with pytest.raises(ValueError, match="Unknown"):
        collect(catalog, selection(("unknown",)), storage)
    empty = catalog.lectures[0].model_copy(update={"sources": ()})
    with pytest.raises(ValueError, match="no registered sources"):
        collect(Catalog(lectures=(empty,)), selection(), storage)
    with pytest.raises(ValueError, match="Duplicate lecture"):
        Catalog(lectures=(catalog.lectures[0], catalog.lectures[0]))
    conflict = (
        catalog.lectures[1].sources[0].model_copy(update={"artifact_id": "artifact:1"})
    )
    with pytest.raises(ValueError, match="Conflicting artifact"):
        Catalog(
            lectures=(
                catalog.lectures[0],
                catalog.lectures[1].model_copy(update={"sources": (conflict,)}),
            )
        )
    (root / "l1.txt").unlink()
    with pytest.raises(FileNotFoundError):
        collect(catalog, selection(), storage)


def test_cache_and_version_invalidation(context):
    catalog, storage, root = context

    class Counting(MockProvider):
        calls = 0

        def generate(self, evidence, selected):
            self.calls += 1
            return super().generate(evidence, selected)

    provider = Counting()
    service = SummaryService(catalog, storage, provider, cache=("local", "cache"))
    first = service.generate(selection())
    assert service.generate(selection()) == first and provider.calls == 1
    assert (
        service.generate(selection(options=Options(detail="detailed"))).summary_id
        != first.summary_id
    )
    assert provider.calls == 2
    (root / "l1.txt").write_text("Explizit geänderte synthetische Quelle")
    with pytest.raises(ValueError, match="version changed"):
        service.generate(selection())
    assert provider.calls == 2
    updated = (
        catalog.lectures[0]
        .sources[0]
        .model_copy(update={"sha256": sha256((root / "l1.txt").read_bytes())})
    )
    new_catalog = Catalog(
        lectures=(catalog.lectures[0].model_copy(update={"sources": (updated,)}),)
    )
    next_summary = SummaryService(
        new_catalog, storage, provider, cache=("local", "cache")
    ).generate(selection())
    assert next_summary.summary_id != first.summary_id and provider.calls == 3


def test_identical_ids_across_physical_roots(context, tmp_path):
    catalog, storage, root = context
    other = root / "copy"
    other.mkdir()
    (other / "l1.txt").write_bytes((root / "l1.txt").read_bytes())
    mirror = RegisteredStorage({"local": {"path": str(other), "readonly": True}})
    a = SummaryService(catalog, storage, MockProvider()).generate(selection())
    b = SummaryService(catalog, mirror, MockProvider()).generate(selection())
    assert a.summary_id == b.summary_id and a.evidence == b.evidence
    assert str(root) not in a.model_dump_json()


@pytest.mark.parametrize(
    "path",
    [
        "../x",
        "/etc/passwd",
        "a/../l1.txt",
        "a\\b",
        "./l1.txt",
        "a//b",
        "",
        ".",
        "x\x00y",
    ],
)
def test_traversal(context, path):
    _, storage, _ = context
    with pytest.raises(ValueError):
        storage.read("local", path)


def test_roots_symlinks_writes_and_no_implicit_mkdir(context, monkeypatch):
    _, storage, root = context
    (root / "link").symlink_to(root / "l1.txt")
    with pytest.raises(ValueError, match="Symlink"):
        storage.read("local", "link")
    readonly = RegisteredStorage({"legacy": {"path": str(root)}})
    with pytest.raises(PermissionError):
        readonly.create("legacy", "new", b"x")
    with pytest.raises(ValueError, match="Unregistered"):
        readonly.read("unknown", "l1.txt")
    with pytest.raises(FileNotFoundError):
        storage.create("local", "newdir/file", b"x")
    assert not (root / "newdir").exists()
    storage.create("local", "new", b"x")
    with pytest.raises(FileExistsError):
        storage.create("local", "new", b"overwrite")
    from src import runtime_paths

    monkeypatch.setattr(runtime_paths, "mounts", lambda **_: {root / "cache": {}})
    with pytest.raises(ValueError, match="Nested"):
        storage.read("local", "cache/x")


def test_write_contract_inside_repository():
    root = Path(__file__).resolve().parents[1]
    storage = RegisteredStorage({"code": {"path": str(root), "readonly": False}})
    with pytest.raises(ValueError, match="authorization"):
        storage.create("code", "forbidden-summary.txt", b"forbidden")
    assert not (root / "forbidden-summary.txt").exists()


def test_missing_mount_and_inventory(tmp_path):
    missing = tmp_path / "not-mounted"
    result = inventory(missing)
    assert not result["root_available"] and "unavailable" in result["error"]
    storage = RegisteredStorage({"drive": {"path": str(missing)}})
    with pytest.raises(FileNotFoundError, match="mount unavailable"):
        storage.read("drive", "x")
    course = tmp_path / "loviscach" / "mathe_1"
    (course / "transcripts").mkdir(parents=True)
    (course / "metadata").mkdir()
    (course / "transcripts" / "01.json").write_text("not read as content")
    (course / "metadata" / "course_info.json").write_text(
        json.dumps(
            {
                "course_id": "mathe_1",
                "provider": "loviscach",
                "resources": [
                    {
                        "lecture_no": "01",
                        "lecture_blocks": ["01"],
                        "local_path": str(course / "transcripts" / "01.json"),
                    },
                    {
                        "lecture_no": "02",
                        "local_path": str(course / "transcripts" / "02.json"),
                    },
                ],
            }
        )
    )
    (course / "shortcut").symlink_to(course / "transcripts", target_is_directory=True)
    report = inventory(tmp_path)
    assert not report["truncated"]
    row = report["courses"][0]
    assert row["provider"] == "loviscach" and row["course"] == "mathe_1"
    assert row["categories"] == {"metadata": 1, "transcripts": 1}
    assert row["declared_lecture_ids"] == ["01", "02"]
    assert row["identity_status"] == "metadata_consistent"
    assert [v["existence"] for v in row["resource_references"]] == [
        "present",
        "not_observed",
    ]
    assert any(v["reason"] == "symlink_or_nested_mount" for v in report["skipped"])
    assert inventory(tmp_path, max_entries=1)["truncated"]


def test_validator_rejects_invented_references_quotes_coverage_and_duplicates(context):
    catalog, storage, _ = context
    evidence, _ = collect(catalog, selection(), storage)
    draft = MockProvider().generate(evidence, selection())
    bad = Claim(text="Invented", source_ids=("absent",))
    for changed, message in [
        (draft.model_copy(update={"learning_objectives": (bad,)}), "Unknown evidence"),
        (draft.model_copy(update={"processed_lecture_ids": ("missing",)}), "coverage"),
        (
            draft.model_copy(
                update={
                    "takeaways": (
                        Claim(
                            text="fake",
                            evidence_quote="not in source",
                            source_ids=(evidence[0].source_id,),
                        ),
                    )
                }
            ),
            "quote absent",
        ),
        (
            draft.model_copy(
                update={
                    "takeaways": (
                        Claim(text="fake", source_ids=(), quality="uncertain"),
                    )
                }
            ),
            "without source",
        ),
    ]:
        status, messages = validate(changed, evidence, selection())
        assert status == "failed" and any(message in m for m in messages)
    repeated = Claim(
        text="Repeated long paragraph " * 20, source_ids=(evidence[0].source_id,)
    )
    status, messages = validate(
        draft.model_copy(update={"takeaways": (repeated, repeated)}),
        evidence,
        selection(),
    )
    assert status == "failed" and any("Duplicated" in m for m in messages)


def test_formula_uncertainty_and_safe_exports(context):
    catalog, storage, _ = context
    result = SummaryService(catalog, storage, MockProvider()).generate(selection())
    formula = Formula(
        text="Unklare Formel",
        source_ids=(result.evidence[0].source_id,),
        latex="x_1=2",
        notation="x_1 ist eine Komponente",
        assumptions="Nur ein synthetisches Beispiel",
        quality="requires_visual_context",
    )
    topic = result.content.topics[0].model_copy(update={"formulas": (formula,)})
    draft = result.content.model_copy(
        update={"topics": (topic,), "title": r"Café & 50% {α} \input{/etc/passwd}"}
    )
    result = result.model_copy(update={"content": draft})
    md, tex = render(result), render(result, latex=True)
    assert "$$\nx_1=2\n$$" in md and "requires_visual_context" in md
    assert (
        r"\documentclass" in tex and r"\end{document}" in tex and "@@BODY@@" not in tex
    )
    assert r"\[x_1=2\]" in tex and r"\input{/etc/passwd}" not in tex
    assert "Café" in tex and r"\&" in tex and r"50\%" in tex
    assert "Quellenverzeichnis" in md and "Q1" in tex
    assert filename(result, "tex").startswith(
        "lecture-summary-"
    ) and "/" not in filename(result, "tex")
    assert tex_escape(r"\write18{evil}") == r"\textbackslash{}write18\{evil\}"
    evil = formula.model_copy(update={"latex": r"\input{/etc/passwd}"})
    changed = result.model_copy(
        update={
            "content": draft.model_copy(
                update={"topics": (topic.model_copy(update={"formulas": (evil,)}),)}
            )
        }
    )
    assert r"\[\input" not in render(changed, latex=True)
    with pytest.raises(ValueError, match="Failed summary"):
        render(result.model_copy(update={"validation_status": "failed"}))


def test_input_limits_and_cancellation(context):
    catalog, storage, root = context

    class Never(MockProvider):
        def generate(self, *args):
            pytest.fail("Model must not be called")

    service = SummaryService(catalog, storage, Never())
    with pytest.raises(InterruptedError):
        service.generate(selection(), cancelled=lambda: True)
    raw = ("large line\n" * 4000).encode()
    (root / "l1.txt").write_bytes(raw)
    artifact = catalog.lectures[0].sources[0].model_copy(update={"sha256": sha256(raw)})
    changed = Catalog(
        lectures=(catalog.lectures[0].model_copy(update={"sources": (artifact,)}),)
    )
    with pytest.raises(ValueError, match="context limit"):
        SummaryService(changed, storage, Never()).generate(selection())


def test_mock_http_single_request_no_retry_and_truncation(context):
    catalog, storage, _ = context
    evidence, _ = collect(catalog, selection(), storage)
    draft = MockProvider().generate(evidence, selection())
    calls = []

    def respond(request):
        body = json.loads(request.content)
        calls.append(body)
        assert body["store"] is False and body["n"] == 1
        assert "untrusted" in body["messages"][0]["content"]
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

    with pytest.raises(PermissionError):
        SummaryProvider(api_key="synthetic-test", model="explicit-model")
    provider = SummaryProvider(
        api_key="synthetic-test",
        model="explicit-model",
        allow_source_upload=True,
        transport=httpx.MockTransport(respond),
    )
    assert (
        SummaryService(catalog, storage, provider)
        .generate(selection())
        .validation_status
        == "needs_review"
    )
    with pytest.raises(RuntimeError, match="budget"):
        provider.generate(evidence, selection())
    assert len(calls) == 1
    provider.close()
    for status, payload in [
        (429, {}),
        (200, {"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]}),
        (200, {"choices": [{"finish_reason": "stop", "message": {"content": "{}"}}]}),
    ]:
        provider = SummaryProvider(
            api_key="synthetic-test",
            model="explicit-model",
            allow_source_upload=True,
            transport=httpx.MockTransport(
                lambda request, status=status, payload=payload: httpx.Response(
                    status, json=payload
                )
            ),
        )
        with pytest.raises(ValueError):
            provider.generate(evidence, selection())
        assert provider.budget.requests == 1
        provider.close()


def test_transcript_native_provenance_and_conflicting_metadata(context):
    catalog, storage, root = context
    raw = json.dumps(
        {
            "source": "historical/host/path.json",
            "text": "Vektoren haben Komponenten.",
            "segments": [
                {
                    "seg_id": 8,
                    "start": None,
                    "end": None,
                    "text": "Vektoren haben Komponenten.",
                }
            ],
            "provenance": {
                "transcript_source": "official_transcript",
                "source_url": "https://example.org/lecture",
                "media_id": "native-video",
            },
            "course_id": "mathe",
            "lecture_id": "l1",
        }
    ).encode()
    (root / "l1.txt").write_bytes(raw)
    artifact = (
        catalog.lectures[0]
        .sources[0]
        .model_copy(
            update={
                "format": "transcript_json",
                "role": "derived",
                "sha256": sha256(raw),
            }
        )
    )
    changed = Catalog(
        lectures=(catalog.lectures[0].model_copy(update={"sources": (artifact,)}),)
    )
    result = SummaryService(changed, storage, MockProvider()).generate(selection())
    evidence = result.evidence[0]
    assert (
        evidence.media_id == "native-video"
        and evidence.source_url == "https://example.org/lecture"
    )
    assert evidence.locator.time_status == "unknown" and evidence.locator.start is None
    assert (
        evidence.locator.original_segment_id == 8
        and evidence.locator.origin_pointer == "/segments/0"
    )
    conflicting = json.loads(raw)
    conflicting["course_id"] = "different-course"
    raw = json.dumps(conflicting).encode()
    (root / "l1.txt").write_bytes(raw)
    artifact = artifact.model_copy(update={"sha256": sha256(raw)})
    changed = Catalog(
        lectures=(catalog.lectures[0].model_copy(update={"sources": (artifact,)}),)
    )
    with pytest.raises(ValueError, match="Contradictory"):
        collect(changed, selection(), storage)


def test_source_edit_during_generation_and_corrupt_cache(context):
    catalog, storage, root = context

    class Editing(MockProvider):
        def generate(self, evidence, selected):
            (root / "l1.txt").write_text("changed during generation")
            return super().generate(evidence, selected)

    original = (root / "l1.txt").read_bytes()
    with pytest.raises(ValueError, match="version changed"):
        SummaryService(catalog, storage, Editing()).generate(selection())
    (root / "l1.txt").write_bytes(original)
    service = SummaryService(catalog, storage, MockProvider(), cache=("local", "cache"))
    result = service.generate(selection())
    (root / "cache" / (result.summary_id + ".json")).write_text("broken JSON")
    with pytest.raises(ValueError):
        service.generate(selection())


def test_unsupported_math_and_output_length_gate(context):
    catalog, storage, _ = context
    evidence, _ = collect(catalog, selection(), storage)
    draft = MockProvider().generate(evidence, selection())
    # All entries differ, so this exercises the byte gate rather than duplication.
    big = tuple(
        Claim(text=str(i) + "x" * 5990, source_ids=(evidence[0].source_id,))
        for i in range(15)
    )
    status, messages = validate(
        draft.model_copy(update={"takeaways": big}), evidence, selection()
    )
    assert status == "failed" and any("byte limit" in m for m in messages)
    from src.lecture_summary.validation import safe_formula

    assert not safe_formula(r"\write18{echo attack}")
    assert not safe_formula(r"\input{secret}")
    assert safe_formula(r"\frac{x+1}{2}")


def test_shared_material_is_deduplicated_with_all_lecture_citations(context):
    catalog, storage, root = context
    raw = ("Ein längerer gemeinsamer synthetischer Quellenausschnitt. " * 7).encode()
    (root / "l1.txt").write_bytes(raw)
    source = catalog.lectures[0].sources[0].model_copy(update={"sha256": sha256(raw)})
    lectures = tuple(
        v.model_copy(update={"sources": (source,)}) for v in catalog.lectures
    )
    result = SummaryService(
        Catalog(lectures=lectures), storage, MockProvider()
    ).generate(selection(("l1", "l2", "l3")))
    assert result.validation_status == "needs_review"
    assert len(result.content.topics[0].explanations) == 1
    assert len(result.content.topics[0].explanations[0].source_ids) == 3


@pytest.mark.parametrize(
    "config",
    [
        [],
        {},
        {"schema_version": 1, "catalog": "x"},
        {"schema_version": 1, "catalog": 4, "storage_roots": {}},
        {
            "schema_version": 1,
            "catalog": "x",
            "storage_roots": {},
            "allow_source_upload": "yes",
        },
    ],
)
def test_invalid_local_configuration_is_a_controlled_error(tmp_path, config):
    from src.lecture_summary.local import load_service

    path = tmp_path / "summary.json"
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError):
        load_service(path)


def test_root_symlink_and_identity_across_storage_ids(context):
    catalog, storage, root = context
    (root / "alias").symlink_to(root, target_is_directory=True)
    with pytest.raises(ValueError, match="Symlink"):
        RegisteredStorage({"alias": {"path": str(root / "alias")}})
    old = SummaryService(catalog, storage, MockProvider()).generate(selection())
    changed = Catalog(
        lectures=(
            catalog.lectures[0].model_copy(
                update={
                    "sources": (
                        catalog.lectures[0]
                        .sources[0]
                        .model_copy(update={"storage_id": "mirror"}),
                    )
                }
            ),
        )
    )
    mirror = RegisteredStorage({"mirror": {"path": str(root), "readonly": True}})
    new = SummaryService(changed, mirror, MockProvider()).generate(selection())
    assert new.summary_id == old.summary_id and new.evidence == old.evidence


def test_cancellation_after_model_response_does_not_publish(context):
    catalog, storage, root = context
    checks = iter((False, False, True))
    service = SummaryService(catalog, storage, MockProvider(), cache=("local", "cache"))
    with pytest.raises(InterruptedError, match="after model response"):
        service.generate(selection(), cancelled=lambda: next(checks))
    assert not list((root / "cache").iterdir())
