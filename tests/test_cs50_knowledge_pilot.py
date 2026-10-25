"""Fake LLM replies and real PR5 binding; explicit opt-in and POSIX deadline."""

import json
import sys
from pathlib import Path

import httpx
import pytest

from scripts import cs50_knowledge_pilot as cli
from src.model_knowledge.data_knowledge import ChunkKnowledgeResult, TranscriptChunk
from src.tools_knowledge.cs50_extraction_provider import (
    ENDPOINT,
    OpenAIHTTPProvider,
    RequestBudget,
    validate_response,
)

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs/course_sources/cs50/cs50_lecture_plan.v1.json"
MANIFEST = ROOT / "docs/course_sources/cs50/cs50_python_week0_knowledge_input.v1.json"


def chunk():
    return TranscriptChunk(
        chunk_id="chunk_0000",
        segment_ids=[0],
        start=1,
        end=2,
        text="A variable stores a value.",
        n_words=5,
    )


def reply():
    return {
        "model": "fake-model",
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": json.dumps(
                        {
                            "analysis": {
                                "chunk_id": "untrusted",
                                "relevant": True,
                                "needs_visual_context": False,
                            },
                            "extraction": {
                                "chunk_id": "untrusted",
                                "statements": [
                                    {
                                        "statement_id": "S1",
                                        "text": "Synthetic claim",
                                        "semantic_type": "statement",
                                        "segment_ids": [999],
                                        "start": 999,
                                        "end": 999,
                                    }
                                ],
                                "formulas": [
                                    {
                                        "expression_id": "F1",
                                        "plain_text": "x = 1",
                                        "expression_type": "equation",
                                        "segment_ids": [999],
                                        "start": 999,
                                        "end": 999,
                                    }
                                ],
                            },
                        }
                    )
                },
            }
        ],
    }


def test_fake_llm_response_and_request_contract():
    calls = []

    def handle(request):
        calls.append(request)
        payload = json.loads(request.content)
        assert str(request.url) == ENDPOINT
        assert payload["max_completion_tokens"] == 1200 and payload["n"] == 1
        assert payload["response_format"] == {"type": "json_object"}
        assert "schema" in payload["messages"][1]["content"]
        return httpx.Response(200, json=reply())

    budget = RequestBudget()
    provider = OpenAIHTTPProvider(
        api_key="fake",
        model="gpt-4o-mini",
        budget=budget,
        transport=httpx.MockTransport(handle),
    )
    record = {}
    result = provider.extract(chunk(), record)
    provider.close()
    assert isinstance(result, ChunkKnowledgeResult) and len(calls) == 1
    assert record["usage"]["total_tokens"] == 30 and budget.requests == 1


@pytest.mark.parametrize("status", [401, 429, 500])
def test_no_http_retries(status):
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(status)

    provider = OpenAIHTTPProvider(
        api_key="fake",
        model="fake",
        budget=RequestBudget(),
        transport=httpx.MockTransport(handle),
    )
    with pytest.raises(ValueError, match="no retry"):
        provider.extract(chunk(), {})
    provider.close()
    assert len(calls) == 1


@pytest.mark.parametrize("kind", ["length", "refusal", "malformed", "schema"])
def test_invalid_response(kind):
    body = reply()
    if kind == "length":
        body["choices"][0]["finish_reason"] = "length"
    if kind == "refusal":
        body["choices"][0]["message"]["refusal"] = "no"
    if kind == "malformed":
        body["choices"][0]["message"]["content"] = "not JSON"
    if kind == "schema":
        body["choices"][0]["message"]["content"] = "{}"
    with pytest.raises(ValueError):
        validate_response(body)


def test_transport_timeout_no_retry():
    calls = []

    def handle(request):
        calls.append(request)
        raise httpx.ReadTimeout("simulated timeout")

    provider = OpenAIHTTPProvider(
        api_key="fake",
        model="fake",
        budget=RequestBudget(),
        transport=httpx.MockTransport(handle),
    )
    with pytest.raises(httpx.ReadTimeout):
        provider.extract(chunk(), {})
    provider.close()
    assert len(calls) == 1


def test_budget_before_request():
    budget = RequestBudget(input_limit=1)
    provider = OpenAIHTTPProvider(
        api_key="fake",
        model="fake",
        budget=budget,
        transport=httpx.MockTransport(lambda req: pytest.fail("Over-budget request")),
    )
    with pytest.raises(ValueError, match="token budget"):
        provider.extract(chunk(), {})
    assert budget.requests == 0
    provider.close()
    budget = RequestBudget()
    budget.claim({"messages": []})
    with pytest.raises(RuntimeError):
        budget.claim({"messages": []})


@pytest.mark.parametrize(
    "args", [["--max-chunks", "3"], ["--timeout", "121"], ["--output-limit", "2001"]]
)
def test_cli_limits(tmp_path, args):
    with pytest.raises(SystemExit):
        cli.main(
            [
                "--plan",
                str(PLAN),
                "--manifest",
                str(MANIFEST),
                "--output",
                str(tmp_path / "run"),
                *args,
            ]
        )
    assert not (tmp_path / "run").exists()


def test_execute_needs_key(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(SystemExit):
        cli.main(
            [
                "--plan",
                str(PLAN),
                "--manifest",
                str(MANIFEST),
                "--output",
                str(tmp_path / "run"),
                "--execute-llm",
            ]
        )
    assert not (tmp_path / "run").exists()


def test_offline_synthetic_subprocess(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    monkeypatch.setenv("OPENAI_API_KEY", "secret-must-not-leak")
    output = tmp_path / "run"
    assert (
        cli.main(
            ["--plan", str(PLAN), "--manifest", str(MANIFEST), "--output", str(output)]
        )
        == 0
    )
    report = json.loads((output / "supervision.json").read_text())
    assert report["worker"]["validated"] and report["worker"]["requests"] == 0
    assert (
        report["worker"]["provider"] == "marvin"
        and report["worker"]["result_origin"] == "synthetic"
    )
    assert "secret-must-not-leak" not in (output / "supervision.json").read_text()
    with pytest.raises(FileExistsError):
        cli.main(
            ["--plan", str(PLAN), "--manifest", str(MANIFEST), "--output", str(output)]
        )


def test_fake_llm_full_pilot_binding(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    from src.core.config_knowledge import KnowledgeSettings
    from src.tools_knowledge.bind_cs50_transcript import (
        CS50AdapterPlan,
        CS50KnowledgeInputManifest,
        build_cs50_knowledge_chunks,
        build_cs50_knowledge_document,
    )
    from src.tools_knowledge.consolidate_knowledge import consolidate_knowledge

    plan = CS50AdapterPlan.model_validate_json(PLAN.read_bytes())
    input = CS50KnowledgeInputManifest.model_validate_json(
        MANIFEST.read_bytes()
    ).inputs[0]
    chunks = build_cs50_knowledge_chunks(
        plan, input, KnowledgeSettings(), workspace=ROOT
    )[:1]
    provider = OpenAIHTTPProvider(
        api_key="fake",
        model="fake",
        budget=RequestBudget(),
        transport=httpx.MockTransport(lambda req: httpx.Response(200, json=reply())),
    )
    result = provider.extract(chunks[0], {})
    result.analysis.chunk_id = chunks[0].chunk_id
    document = build_cs50_knowledge_document(
        input, chunks, [result], plan=plan, workspace=ROOT
    )
    result = consolidate_knowledge(document)
    assert (
        result.source_id == input.source_id
        and result.transcript_provenance == input.transcript_provenance
    )
    assert result.statements[0].evidence[0].segment_ids == chunks[0].segment_ids
    assert result.formulas[0].evidence[0].start == chunks[0].start
    assert 999 not in result.statements[0].evidence[0].segment_ids
    provider.close()
    for name, value in [("extraction", document), ("consolidation", result)]:
        cli.save(tmp_path / f"{name}.json", value.model_dump(mode="json"))
        assert (
            type(value).model_validate_json((tmp_path / f"{name}.json").read_bytes())
            == value
        )


def test_offline_local_original_pilot(tmp_path, monkeypatch):
    """Optional original-pilot check; never substitute synthetic artifacts here."""
    if not MANIFEST.exists():
        pytest.skip("Optional local original pilot manifest unavailable")
    test_offline_synthetic_subprocess(tmp_path, monkeypatch)


@pytest.fixture(scope="module", autouse=True)
def controlled_settings(tmp_path_factory):
    import socket

    directory = tmp_path_factory.mktemp("pilot-settings")
    with pytest.MonkeyPatch.context() as patch:
        patch.chdir(directory)
        for key, value in {
            "ROOT": str(directory),
            "DATA_DIR": str(directory / "data"),
            "CHROMA_DIR": str(directory / "chroma"),
            "WIKI_EN_API": "https://example.invalid",
            "HEADER_AGENT": "offline",
            "HF_API_KEY": "unused",
            "OPENAI_API_KEY": "unused",
        }.items():
            patch.setenv(key, value)

        def forbidden(*args, **kwargs):
            raise AssertionError("Real network forbidden")

        patch.setattr(socket.socket, "connect", forbidden)
        patch.setattr(socket, "getaddrinfo", forbidden)
        yield
        assert "marvin" not in sys.modules


def test_fake_worker_two_chunks(tmp_path, monkeypatch):
    from src.tools_knowledge import cs50_extraction_provider as providers

    original = providers.OpenAIHTTPProvider

    def fake(**kwargs):
        return original(
            **kwargs,
            transport=httpx.MockTransport(
                lambda req: httpx.Response(200, json=reply())
            ),
        )

    monkeypatch.setattr(providers, "OpenAIHTTPProvider", fake)
    monkeypatch.setenv("CS50_KNOWLEDGE_EXECUTE_LLM", "1")
    configuration = {
        "execute_llm": True,
        "provider": "openai_http",
        "model": "fake-model",
        "probe_marvin": False,
        "plan": str(PLAN),
        "manifest": str(MANIFEST),
        "workspace": str(ROOT),
        "max_chunks": 2,
        "token_budget": 60000,
        "input_limit": 28000,
        "output_limit": 1200,
    }
    cli.save(tmp_path / "configuration.json", configuration)
    assert cli.worker(tmp_path / "configuration.json") == 0
    report = json.loads((tmp_path / "worker_result.json").read_text())
    assert report["validated"] and report["requests"] == 2
    assert len(report["results"]) == 2 and all(
        r["usage"]["total_tokens"] == 30 for r in report["results"]
    )
    document = json.loads((tmp_path / "extraction.json").read_text())
    expected = json.loads(MANIFEST.read_text())["inputs"][0]
    for field in (
        "source_id",
        "course_id",
        "lecture_id",
        "language",
        "media_id",
        "transcript_url",
        "transcript_provenance",
    ):
        assert document[field] == expected[field]
    assert document["lecture_id"] != document["source_id"]


def test_authorization_gate(tmp_path, monkeypatch):
    monkeypatch.delenv("CS50_KNOWLEDGE_EXECUTE_LLM", raising=False)
    cli.save(tmp_path / "configuration.json", {"execute_llm": True})
    with pytest.raises(ValueError, match="authorization"):
        cli.worker(tmp_path / "configuration.json")


def test_output_symlink_into_production_rejected(tmp_path):
    alias = tmp_path / "data-alias"
    alias.symlink_to(ROOT / "data", target_is_directory=True)
    with pytest.raises(SystemExit):
        cli.main(
            [
                "--plan",
                str(PLAN),
                "--manifest",
                str(MANIFEST),
                "--output",
                str(alias / "forbidden-test-run"),
            ]
        )
