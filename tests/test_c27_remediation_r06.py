"""Independent offline probes of the final public export contract, beyond R05."""

import json
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import quote

import pytest

from scripts import c27_reviewed_week as cli
from src.c27_learning_summary.adapter import load_catalog
from src.c27_learning_summary.engine import generate
from src.c27_learning_summary.export import markdown, public_processing_report
from src.c27_learning_summary.export_policy import (
    POLICY,
    WITHHELD,
    ExportPolicy,
    exportable_source_url,
    metadata,
    source_url_key,
)
from src.c27_learning_summary.llm import FakeLLM
from src.c27_learning_summary.models import (
    Catalog,
    Review,
    SummaryConfig,
    SummaryResult,
)
from src.c27_learning_summary.store import SummaryStore
from src.content_store.models import fingerprint, sha256
from tests.test_c27_reviewed_week import review as review_fixture

CANARY = "R06_CANARY_b8a21d"
BAD = "https://cs50.harvard.edu/accessToken/" + CANARY
SCOPE = ("synthetic_cs50p", "0", "lecture-0")
PUBLIC = "https://cdn.cs50.net/python/2023/x/shorts/functions/lang/en/functions.txt"


def fixture_data():
    d = load_catalog(Path("tests/fixtures/lecture_summary/catalog.json")).model_dump(
        mode="json"
    )
    unit = d["courses"][0]["weeks"][0]["units"][0]
    unit["materials"] = [unit["materials"][0]]
    return d, unit["materials"][0]


def outcome(tmp_path, data):
    store = SummaryStore(tmp_path / "store")
    model = FakeLLM()
    first = generate(
        store,
        Catalog.model_validate(data),
        *SCOPE,
        ["transcript"],
        SummaryConfig(),
        model,
    )
    calls = model.calls
    second = generate(
        store,
        Catalog.model_validate(data),
        *SCOPE,
        ["transcript"],
        SummaryConfig(),
        model,
    )
    assert second.from_cache and model.calls == calls and first.result == second.result
    assert (
        SummaryResult.model_validate_json(first.result.model_dump_json())
        == first.result
    )
    return store, first.result


MARKERS = [
    "sessionid",
    "JSESSIONID",
    "accessToken",
    "authToken",
    "refreshToken",
    "clientSecret",
    "ACCESS_token",
    "SeSsIoNiD",
    "api.key",
    "privateKey",
    "bearer",
    "PHPSESSID",
]


@pytest.mark.parametrize("marker", MARKERS)
@pytest.mark.parametrize("encoding", [0, 1, 2, 5])
def test_markers_rejected_even_under_reviewed_host(marker, encoding):
    part = marker
    for _ in range(encoding):
        part = "".join(f"%{ord(c):02x}" for c in part)
    url = "https://cs50.harvard.edu/python/" + part + "/" + CANARY
    assert source_url_key(url) is None
    assert exportable_source_url(url) is None


@pytest.mark.parametrize(
    "suffix",
    [
        "/" + CANARY,
        "/accessToken/" + CANARY,
        "?sessionid=" + CANARY,
        "?accessToken=" + CANARY,
        "#" + CANARY,
        "%3faccessToken%3d" + CANARY,
        "%253FaccessToken%253D" + CANARY,
        "?",
        "#",
    ],
)
def test_reviewed_base_cannot_approve_added_components(suffix):
    assert exportable_source_url(PUBLIC + suffix) is None


@pytest.mark.parametrize(
    "host",
    [
        "localhost",
        "LOCALHOST.",
        "foo.localhost.",
        "home.arpa",
        "HOME.ARPA.",
        "x.home.arpa",
        "localhost..",
        "localhost。",
        "box.local",
        "private.internal",
        "127.0.0.1",
        "127.0.0.1.",
        "127.1",
        "0177.0.0.1",
        "2130706433",
        "0x7f000001",
        "10.0.0.1",
        "100.64.0.1",
        "169.254.169.254",
        "224.0.0.1",
        "255.255.255.255",
        "[::1]",
        "[::ffff:127.0.0.1]",
        "[ff01::1]",
        "[ff02::1]",
        "[ff05::1]",
        "[fd00::1]",
        "[fe80::1%25eth0]",
        "[2001:db8::1]",
        "[::1]cs50.harvard.edu",
        "cs50.harvard.edu.evil.test",
        "user:password@cs50.harvard.edu",
    ],
)
def test_local_and_ambiguous_hosts(host):
    url = "https://" + host + "/" + CANARY
    assert source_url_key(url) is None
    assert exportable_source_url(url) is None


@pytest.mark.parametrize(
    "alias", ["source_path", "title", "license", "attribution", "all"]
)
@pytest.mark.parametrize("encoded", [False, True])
def test_aliases_persist_cache_reviews_json_markdown_and_canary(
    tmp_path, alias, encoded, capsys, caplog
):
    d, m = fixture_data()
    value = "Source details: " + (
        quote(quote(BAD, safe=""), safe="") if encoded else BAD
    )
    m["resource"]["source_url"] = BAD
    for field in (
        ["source_path", "title", "license", "attribution"]
        if alias == "all"
        else [alias]
    ):
        if field in {"title", "license"}:
            m["resource"][field] = value
        else:
            m[field] = value
    store, result = outcome(tmp_path, d)
    # Internal identity and original metadata survive in the private input snapshot.
    assert CANARY in store.read(result.run_id, "input.json").decode()
    store.save_review(
        Review(run_id=result.run_id, decision="draft", reviewer="offline", comment=BAD)
    )
    raw = store.read(result.run_id, "result.json")
    restored = SummaryStore(store.root).result(result.run_id)
    j = store.export_json(result.run_id)
    md = markdown(restored, store.reviews(result.run_id))
    assert CANARY not in j + md + raw.decode()
    assert CANARY not in capsys.readouterr().out + caplog.text
    assert json.loads(j)["review_status"] == "draft" and "Review status: draft" in md
    assert all(r.provenance.source_url_status == "withheld" for r in restored.refs)
    assert store.read(result.run_id, "result.json") == raw
    store.publish(result.run_id, "export.json", j.encode())
    store.publish(result.run_id, "export.md", md.encode())
    assert all(
        CANARY not in store.read(result.run_id, p).decode()
        for p in ["export.json", "export.md"]
    )
    assert all(
        r.source_id == m["source_id"]
        and r.content_hash == m["resource"]["content_hash"]
        for r in restored.refs
    )


@pytest.mark.parametrize(
    "alias",
    ["metadata", "original_url", "source_details", "provider_metadata", "extra"],
)
def test_unknown_nested_resource_metadata_never_forwarded(tmp_path, alias):
    d, m = fixture_data()
    m["resource"]["source_url"] = BAD
    m["resource"][alias] = {
        "original_url": BAD,
        "nested": [{"metadata": {BAD: CANARY}}],
    }
    # The resource model ignores unknown extensions; the summary adapter copies
    # only its fixed source-reference schema, never the complete resource dump.
    store, result = outcome(tmp_path, d)
    assert CANARY not in store.export_json(result.run_id) + markdown(result)
    assert alias not in result.refs[0].provenance.model_dump()


def test_bounded_dynamic_metadata_unknown_types_keys_cycles_and_depth():
    class Unknown:
        def __str__(self):
            raise AssertionError("Unknown values must never be stringified")

    assert metadata(Unknown()) == WITHHELD
    assert metadata(
        {BAD: CANARY, "nested": [{"original_url": BAD}], "object": Unknown()}
    ) == {
        "nested": [{"original_url": WITHHELD}],
        "object": WITHHELD,
    }
    deep = CANARY
    for _ in range(20):
        deep = {"nested": deep}
    cycle = {}
    cycle["nested"] = cycle
    assert CANARY not in json.dumps(metadata(deep))
    assert WITHHELD in json.dumps(metadata(cycle))
    assert metadata([CANARY] * 1025) == WITHHELD
    assert metadata({str(i): CANARY for i in range(129)}) == WITHHELD


def test_unreviewed_public_sources_and_separately_reviewed_future_course(monkeypatch):
    future = "https://lectures.example.edu/course/intro.txt"
    assert source_url_key(future) is not None
    assert exportable_source_url(future) is None
    config = {
        "schema_version": 1,
        "sources": [{"id": "future-course", "review": "SEC-42", "urls": [future]}],
    }
    reviewed = ExportPolicy.from_config(config)
    assert reviewed.source_url(future) == future
    assert reviewed.source_url(future + "/" + CANARY) is None
    monkeypatch.setattr("src.c27_learning_summary.export_policy.POLICY", reviewed)
    assert exportable_source_url(future) == future
    assert exportable_source_url(PUBLIC) is None


@pytest.mark.parametrize(
    "url",
    [
        BAD,
        "http://example.edu/course",
        "https://home.arpa/source",
        "https://[ff02::1]/source",
    ],
)
def test_configuration_cannot_override_syntax_security(url):
    with pytest.raises(
        ValueError, match="Invalid public source approval configuration"
    ) as exc:
        ExportPolicy.from_config(
            {
                "schema_version": 1,
                "sources": [{"id": "bad", "review": "SEC-42", "urls": [url]}],
            }
        )
    assert CANARY not in str(exc.value)


def test_all_75_reviewed_urls_survive_all_export_paths(tmp_path):
    config = json.loads(
        Path("src/c27_learning_summary/public_sources.v1.json").read_bytes()
    )
    urls = config["sources"][0]["urls"]
    assert len(urls) == 75 and len(POLICY.approved) == 78
    d, m = fixture_data()
    store, result = outcome(tmp_path, d)
    for url in urls:
        assert exportable_source_url(url) == url
        data = result.model_dump(mode="json")
        data["cache_key"] = fingerprint(url)
        for ref in data["refs"]:
            ref["provenance"] = dict(source_url=url, source_url_status="available")
        run = store.begin(data["cache_key"], {})
        data["run_id"] = run
        store.write(run, "result.json", data)
        raw = store.read(run, "result.json")
        store.finish(run, "completed", result_sha256=sha256(raw))
        restored = store.result(run)
        assert url in store.export_json(run) and url in markdown(restored)
        cached = store.cached(data["cache_key"])
        assert cached is not None and cached.run_id == run
        assert all(r.provenance.source_url == url for r in cached.refs)
        assert store.read(run, "result.json") == raw


def test_final_boundary_rechecks_mutated_and_historical_models(tmp_path):
    d, _ = fixture_data()
    store, result = outcome(tmp_path, d)
    ref = result.refs[0]
    object.__setattr__(ref, "source_path", BAD)
    object.__setattr__(ref.provenance, "source_url", BAD)
    object.__setattr__(ref.provenance, "source_url_status", "available")
    object.__setattr__(ref.provenance, "license", BAD)
    object.__setattr__(result, "title", BAD)
    assert CANARY not in markdown(result)
    # Historical unsafe data is hash-checked, then projected, never overwritten.
    raw_data = result.model_dump(mode="json")
    raw_data["warnings"] = [BAD]
    raw_data["sections"][0]["uncertainties"] = [BAD]
    raw_data["refs"][0]["locators"][0]["dom"] = BAD
    raw_data["refs"][0]["locators"][0]["chapter_path"] = [BAD]
    raw_data["config"]["prompt"] = BAD
    run = store.begin(raw_data["cache_key"], {})
    raw_data["run_id"] = run
    store.write(run, "result.json", raw_data)
    raw = store.read(run, "result.json")
    store.finish(run, "completed", result_sha256=sha256(raw))
    assert CANARY in raw.decode()
    assert CANARY not in store.export_json(run) + markdown(store.result(run))
    assert store.read(run, "result.json") == raw


def test_unknown_summary_metadata_fails_without_sensitive_exception(tmp_path):
    d, _ = fixture_data()
    store, result = outcome(tmp_path, d)
    raw = result.model_dump(mode="json")
    raw["refs"][0]["provenance"]["metadata"] = {"original_url": BAD}
    store.write(result.run_id, "result.json", raw)
    store.finish(
        result.run_id,
        "completed",
        result_sha256=sha256(store.read(result.run_id, "result.json")),
    )
    with pytest.raises(ValueError) as exc:
        store.export_json(result.run_id)
    assert CANARY not in str(exc.value)


def test_learning_text_is_preserved_while_structured_metadata_is_withheld(tmp_path):
    d, m = fixture_data()
    text = "An example URL in this lesson is " + BAD + "."
    m["blocks"] = [dict(m["blocks"][0], text=text)]
    m["artifact"]["payload_sha256"] = fingerprint(m["blocks"])
    m["resource"].update(source_url=BAD, title=BAD)
    store, result = outcome(tmp_path, d)
    assert result.refs[0].text == text and result.claims[0].text == text
    assert result.refs[0].provenance.title == WITHHELD
    j = json.loads(store.export_json(result.run_id))
    assert j["result"]["refs"][0]["text"] == text
    assert text in markdown(result)


def test_cli_report_selects_schema_and_sanitizes_nested_fields():
    report = {
        "materials": [
            {"source_url": BAD, "filename": BAD, "metadata": {"original_url": BAD}}
        ],
        "summaries": [
            {"reason": BAD, "state": "blocked", "provider_metadata": {"secret": CANARY}}
        ],
        "inputs": {"local_path": BAD},
        "metadata": {"original_url": BAD},
    }
    public = public_processing_report(report)
    assert CANARY not in json.dumps(public)
    assert public["materials"][0]["source_url"] is None
    assert public["materials"][0]["source_url_status"] == "withheld"


def test_regular_cli_public_files_and_repeat_are_canary_free(tmp_path):
    root = review_fixture.__wrapped__(tmp_path, SimpleNamespace(param="0"))
    p = root / "download-batch-01/download-report.json"
    report = json.loads(p.read_bytes())
    for entry in report["files"]:
        entry.update(attribution=BAD, license=BAD)
    p.write_text(json.dumps(report))
    output = tmp_path / "output"
    for _ in range(2):
        result = cli.run(root, output, fake_summary=True)
        assert CANARY not in json.dumps(result)
        store = SummaryStore(output / "summaries")
        for s in result["summaries"]:
            for name in s["exports"].values():
                assert CANARY not in store.read(s["run_id"], name).decode()


R05_CASES = [
    *(
        ("https://example.org/" + marker + "/R05_CANARY_7f94b2", None)
        for marker in [
            "sessionid",
            "JSESSIONID",
            "accessToken",
            "authToken",
            "refreshToken",
            "clientSecret",
        ]
    ),
    *(
        ("https://" + host + "/R05_CANARY_7f94b2", None)
        for host in [
            "[ff01::1]",
            "[ff02::1]",
            "[ff05::1]",
            "224.0.0.1",
            "home.arpa",
            "HOME.ARPA.",
        ]
    ),
    *(
        ("https://example.org/token/R05_CANARY_7f94b2", alias)
        for alias in ["source_path", "title", "license", "attribution"]
    ),
]


@pytest.mark.parametrize("url,alias", R05_CASES)
def test_exact_16_r05_reproductions(tmp_path, url, alias):
    data, material = fixture_data()
    material["resource"]["source_url"] = url
    if alias in {"title", "license"}:
        material["resource"][alias] = url
    elif alias:
        material[alias] = url
    store, result = outcome(tmp_path, data)
    assert "R05_CANARY_7f94b2" not in store.export_json(result.run_id) + markdown(
        result
    )
    assert all(r.provenance.source_url_status == "withheld" for r in result.refs)


def test_policy_revocation_applies_to_existing_cache_without_rewriting(
    tmp_path, monkeypatch
):
    d, m = fixture_data()
    m["resource"]["source_url"] = PUBLIC
    store, result = outcome(tmp_path, d)
    original = store.read(result.run_id, "result.json")
    assert PUBLIC in original.decode()
    monkeypatch.setattr(
        "src.c27_learning_summary.export_policy.POLICY", ExportPolicy(frozenset())
    )
    cached = store.cached(result.cache_key)
    assert cached is not None
    assert all(r.provenance.source_url_status == "withheld" for r in cached.refs)
    assert PUBLIC not in store.export_json(result.run_id) + markdown(result)
    assert store.read(result.run_id, "result.json") == original


def test_metadata_never_unwraps_unapproved_encoded_url():
    encoded = PUBLIC.replace("/python/", "/%2570ython/")
    assert source_url_key(encoded) is None
    assert metadata(encoded) == WITHHELD
    assert metadata(quote(PUBLIC, safe="")) == WITHHELD
    assert metadata(PUBLIC.replace("/python/", "/%70ython/")) != WITHHELD


def test_dynamic_metadata_node_budget_is_bounded():
    # All leaf values after the global budget are replaced, even at shallow depth.
    value = [[str(i) for i in range(1024)] for _ in range(8)]
    value[-1][-1] = CANARY
    output = metadata(value)
    assert CANARY not in json.dumps(output)
    assert WITHHELD in json.dumps(output)


def test_final_boundary_rechecks_review_model_instances(tmp_path):
    from src.c27_learning_summary.export import public_reviews
    from src.c27_learning_summary.models import SourceProvenance

    d, _ = fixture_data()
    store, result = outcome(tmp_path, d)
    review = Review(run_id=result.run_id, decision="draft", reviewer="offline")
    object.__setattr__(review, "comment", BAD)
    events = [
        {
            "review_id": "1" * 32,
            "saved_ns": 1,
            "result_sha256": "1" * 64,
            "review": review,
        }
    ]
    assert CANARY not in json.dumps(public_reviews(events)) + markdown(result, events)
    with pytest.raises(ValueError) as exc:
        SourceProvenance.model_validate({"metadata": {"original_url": BAD}})
    assert CANARY not in str(exc.value)


def test_malformed_constructed_model_never_emits_original_in_warning_or_error(tmp_path):
    import warnings

    from src.c27_learning_summary.export import public_result

    data, _ = fixture_data()
    _, result = outcome(tmp_path, data)
    object.__setattr__(result.refs[0], "source_path", {"original_url": BAD})
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        with pytest.raises(ValueError) as exc:
            public_result(result)
    assert CANARY not in str(exc.value) + "".join(str(w.message) for w in captured)
