"""Focused acceptance setup/preflight tests; synthetic sources and no API client."""

import json

import httpx
import pytest

from scripts.lecture_summary import register
from scripts.lecture_summary_acceptance import CASES, SOURCES, inspect, prepare, selection
from src.lecture_summary.local import load_service
from src.lecture_summary.providers import MockProvider, SummaryProvider
from src.lecture_summary.sources import collect


@pytest.fixture
def originals(tmp_path):
    root = tmp_path / "originals"
    folder = root / "loviscach/mathe_1/transcripts"
    folder.mkdir(parents=True)
    for lecture, stem, _ in SOURCES:
        text = "Ausdrücklich synthetische Testquelle über Vektoren."
        (folder / f"{lecture}_{stem}.json").write_text(
            json.dumps(
                {
                    "source": "synthetic",
                    "text": text,
                    "segments": [{"seg_id": 0, "start": 0, "end": 1, "text": text}],
                }
            )
        )
    return root


def test_prepare_all_cases_cache_and_originals_unchanged(originals, tmp_path):
    before = {p: p.read_bytes() for p in originals.rglob("*.json")}
    config = prepare(originals, tmp_path / "workspace")
    settings = json.loads(config.read_text())
    assert settings["model"] == "mock-extractive-v1"
    assert settings["allow_source_upload"] is False
    assert settings["storage_roots"]["source"]["readonly"] is True
    service = load_service(config)
    for ids in CASES.values():
        summary = service.generate(selection(ids))
        assert summary.validation_status == "needs_review"
        assert tuple(summary.content.processed_lecture_ids) == ids
    assert len(list((config.parent / "cache").glob("*.json"))) == 3
    assert before == {p: p.read_bytes() for p in before}
    with pytest.raises(FileExistsError):
        prepare(originals, config.parent)
    assert json.loads(config.read_text()) == settings


def test_missing_originals_fail_before_any_output(tmp_path):
    with pytest.raises(FileNotFoundError):
        prepare(tmp_path / "missing-mount", tmp_path / "workspace")
    assert not (tmp_path / "workspace").exists()


def test_preflight_creates_no_http_client(originals, tmp_path, monkeypatch):
    config = prepare(originals, tmp_path / "workspace")
    monkeypatch.setattr(httpx, "Client", lambda **kw: pytest.fail("HTTP client forbidden"))
    report = inspect(config, model="synthetic-model")
    assert set(report) == set(CASES)
    assert all(case["live_budget_ok"] for case in report.values())


def test_live_config_is_rejected_before_client_or_key_lookup(
    originals, tmp_path, monkeypatch
):
    config = prepare(originals, tmp_path / "workspace")
    values = json.loads(config.read_text())
    values.update(model="synthetic-live", allow_source_upload=True)
    config.write_text(json.dumps(values))
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-not-a-secret")
    monkeypatch.setattr(httpx, "Client", lambda **kw: pytest.fail("HTTP client forbidden"))
    with pytest.raises(ValueError, match="unchanged mock"):
        inspect(config, model="synthetic-live")


def test_large_complete_request_is_rejected_without_client(
    originals, tmp_path, monkeypatch
):
    lecture, stem, _ = SOURCES[0]
    path = originals / f"loviscach/mathe_1/transcripts/{lecture}_{stem}.json"
    text = "Ausdrücklich synthetischer Budgettest. " * 3
    path.write_text(
        json.dumps(
            {
                "source": "synthetic",
                "text": text,
                "segments": [
                    {"seg_id": i, "start": i, "end": i + 1, "text": text}
                    for i in range(150)
                ],
            }
        )
    )
    config = prepare(originals, tmp_path / "workspace")
    monkeypatch.setattr(httpx, "Client", lambda **kw: pytest.fail("HTTP client forbidden"))
    report = inspect(config, model="synthetic-model")
    assert report["text"]["input_upper_bound"] > 30000
    assert not report["text"]["live_budget_ok"]
    assert "before request" in report["text"]["error"]


def test_preflight_and_real_dispatch_use_identical_payload(originals, tmp_path):
    config = prepare(originals, tmp_path / "workspace")
    service = load_service(config)
    chosen = selection(CASES["text"])
    evidence, _ = collect(service.catalog, chosen, service.storage)
    captured = []

    def respond(request):
        captured.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "choices": [{
                    "finish_reason": "stop",
                    "message": {
                        "content": MockProvider().generate(evidence, chosen).model_dump_json()
                    },
                }]
            },
        )

    provider = SummaryProvider(
        api_key="synthetic", model="synthetic-model", allow_source_upload=True,
        transport=httpx.MockTransport(respond),
    )
    try:
        provider.generate(evidence, chosen)
        assert captured == [
            provider.request_payload(evidence, chosen, model=provider.model)
        ]
        assert provider.budget.requests == 1
        expected = inspect(config, model=provider.model)["text"]["input_upper_bound"]
        assert provider.budget.reserved == expected + 2000
    finally:
        provider.close()


def test_existing_one_file_register_remains_usable(originals, tmp_path):
    lecture, stem, title = SOURCES[0]
    config = register(
        tmp_path / "single", originals,
        f"loviscach/mathe_1/transcripts/{lecture}_{stem}.json",
        "loviscach", "mathe_1", lecture, title, "transcript_json",
    )
    assert len(load_service(config).catalog.lectures) == 1
