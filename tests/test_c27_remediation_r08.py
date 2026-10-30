"""R07's twelve counterexamples and R08's structured export boundary contract."""

import json
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import quote

import pytest

from scripts.c27_reviewed_week import main
from src.c27_learning_summary.adapter import load_catalog
from src.c27_learning_summary.engine import generate
from src.c27_learning_summary.export import (
    markdown,
    public_processing_report,
    public_result,
)
from src.c27_learning_summary.export_policy import (
    WITHHELD,
    exportable_source_url,
    metadata,
)
from src.c27_learning_summary.llm import FakeLLM
from src.c27_learning_summary.models import (
    Catalog,
    Review,
    SummaryConfig,
    SummaryResult,
)
from src.c27_learning_summary.store import SummaryStore
from src.content_store.models import sha256
from tests.test_c27_reviewed_week import review as review_fixture

ROOT = Path(__file__).resolve().parents[1]
CANARY = "R07_CANARY_c912e6"
MAIL = f"mailto:{CANARY}@private.internal"
TEL = f"tel:+490000{CANARY}"
SCOPE = ("synthetic_cs50p", "0", "lecture-0")


def seed(tmp_path):
    data = load_catalog(
        ROOT / "tests/fixtures/lecture_summary/catalog.json"
    ).model_dump(mode="json")
    unit = data["courses"][0]["weeks"][0]["units"][0]
    unit["materials"] = unit["materials"][:1]
    return data, unit["materials"][0], SummaryStore(tmp_path / "store")


def generate_once(data, store):
    return generate(
        store,
        Catalog.model_validate(data),
        *SCOPE,
        ["transcript"],
        SummaryConfig(),
        FakeLLM(),
    ).result


def set_alias(material, alias, value):
    if alias in {"title", "license"}:
        material["resource"][alias] = value
    else:
        material[alias] = value


@pytest.mark.parametrize("uri", [MAIL, TEL])
@pytest.mark.parametrize("alias", ["source_path", "title", "license", "attribution"])
def test_r07_rejected_absolute_uri_alias(tmp_path, uri, alias):
    data, material, store = seed(tmp_path)
    material["resource"]["source_url"] = uri
    set_alias(material, alias, uri)
    catalog = Catalog.model_validate(data)
    original = catalog.model_dump_json()
    result = generate_once(data, store)
    raw = store.read(result.run_id, "result.json")
    private_input = store.read(result.run_id, "input.json")
    assert CANARY in private_input.decode()
    model = FakeLLM()
    cached = generate(store, catalog, *SCOPE, ["transcript"], SummaryConfig(), model)
    assert cached.from_cache and model.calls == 0
    assert all(ref.provenance.source_url_status == "withheld" for ref in result.refs)
    assert CANARY not in store.export_json(result.run_id) + markdown(result)
    assert CANARY not in public_result(cached.result).model_dump_json()
    assert SummaryResult.model_validate_json(result.model_dump_json()) == result
    assert store.read(result.run_id, "result.json") == raw
    assert store.read(result.run_id, "input.json") == private_input
    assert catalog.model_dump_json() == original


@pytest.mark.parametrize("version", [1, 2])
def test_r07_historical_cache_review_and_report(tmp_path, version):
    data, _, store = seed(tmp_path)
    result = generate_once(data, store)
    old = result.model_dump(mode="json")
    old["schema_version"] = version
    old["title"] = MAIL
    for ref in old["refs"]:
        ref["source_path"] = MAIL
        ref["provenance"].update(
            source_url=MAIL,
            source_url_status="available",
            title=MAIL,
            license=MAIL,
            attribution=MAIL,
        )
    store.write(result.run_id, "result.json", old)
    raw = store.read(result.run_id, "result.json")
    store.finish(result.run_id, "completed", result_sha256=sha256(raw))
    # Historical review bytes must be protected on export, without rewriting them.
    event = store.save_review(
        Review(run_id=result.run_id, decision="draft", reviewer="R07")
    )
    name = f"reviews/{event['saved_ns']}-{event['review_id']}.json"
    event["review"]["comment"] = MAIL
    store.write(result.run_id, name, event)
    review_raw = store.read(result.run_id, name)
    json_export = store.export_json(result.run_id)
    restored = store.cached(result.cache_key)
    assert restored.run_id == result.run_id
    md = markdown(restored, store.reviews(result.run_id))
    report = public_processing_report(
        {
            "materials": [
                {
                    "source_url": MAIL,
                    "filename": MAIL,
                    "members": [{"original_url": MAIL}],
                }
            ],
            "summaries": [{"reason": MAIL}],
        }
    )
    assert CANARY not in json_export + md + json.dumps(report)
    assert json.loads(json_export)["review_status"] == "draft"
    assert "Review status: draft" in md
    assert store.read(result.run_id, "result.json") == raw
    assert store.read(result.run_id, name) == review_raw
    for before, after in zip(
        old["refs"], json.loads(json_export)["result"]["refs"], strict=True
    ):
        for key in ("ref_id", "source_id", "material_id", "content_hash", "locators"):
            assert after[key] == before[key]
    assert json_export == store.export_json(result.run_id)
    assert md == markdown(restored, store.reviews(result.run_id))


def test_r07_actual_ui_downloads(tmp_path, monkeypatch):
    from streamlit.runtime.memory_media_file_storage import MemoryMediaFileStorage
    from streamlit.testing.v1 import AppTest

    data, material, _ = seed(tmp_path)
    material["resource"].update(source_url=MAIL, title=MAIL, license=MAIL)
    material["source_path"] = MAIL
    material["attribution"] = MAIL
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(data))
    monkeypatch.setenv("LECTURE_SUMMARY_CATALOG", str(path))
    monkeypatch.setenv("LECTURE_SUMMARY_STORE", str(tmp_path / "ui-store"))
    payloads = []
    original = MemoryMediaFileStorage.load_and_get_id

    def capture(self, data, mimetype, kind, filename=None):
        if filename and filename.startswith("summary-"):
            payloads.append(data.decode() if isinstance(data, bytes) else data)
        return original(self, data, mimetype, kind, filename)

    monkeypatch.setattr(MemoryMediaFileStorage, "load_and_get_id", capture)
    app = AppTest.from_file(
        str(ROOT / "lecture_summarizer_app.py"), default_timeout=30
    ).run()
    next(
        button for button in app.button if button.label == "Summary starten"
    ).click().run()
    assert not app.exception and not app.error
    assert len(app.get("download_button")) == len(payloads) == 2
    assert all(CANARY not in content for content in payloads)


def test_r07_actual_cli_exports(tmp_path, capsys):
    root = review_fixture.__wrapped__(tmp_path, SimpleNamespace(param="0"))
    report_path = root / "download-batch-01/download-report.json"
    report = json.loads(report_path.read_bytes())
    for entry in report["files"]:
        entry.update(license=MAIL, attribution=MAIL)
    report_path.write_text(json.dumps(report))
    output = tmp_path / "output"
    main(["--review-root", str(root), "--output", str(output), "--fake-summary"])
    public = json.loads(capsys.readouterr().out)
    assert CANARY not in json.dumps(public)
    store = SummaryStore(output / "summaries")
    files = [
        store.read(summary["run_id"], name).decode()
        for summary in public["summaries"]
        for name in summary.get("exports", {}).values()
    ]
    assert len(files) == 4
    assert all(CANARY not in content for content in files)


VARIANTS = [
    MAIL,
    TEL,
    f"custom+v1.example:{CANARY}",
    f"URN:example:{CANARY}",
    f"MaIlTo:{CANARY}@private.internal",
    f"TeL:+4930{CANARY}",
    f"HTTPS://private.internal/{CANARY}",
    f"http://private.internal/{CANARY}",
    f"mailto :{CANARY}@private.internal",
    f"mailto: {CANARY}@private.internal",
    f"https : //private.internal/{CANARY}",
    f"//private.internal/{CANARY}",
    f"mailto\uff1a{CANARY}@private.internal",
    f"mailto&#58;{CANARY}@private.internal",
    f"mailto&colon;{CANARY}@private.internal",
    f"See <{MAIL}> or {TEL}",
]


@pytest.mark.parametrize("alias", ["source_path", "title", "license", "attribution"])
@pytest.mark.parametrize("uri", VARIANTS)
def test_uri_shapes_at_final_mutated_model_boundary(tmp_path, alias, uri):
    data, _, store = seed(tmp_path)
    result = generate_once(data, store)
    original = result.model_dump_json()
    ref = result.refs[0]
    if alias == "source_path":
        object.__setattr__(ref, alias, uri)
    else:
        object.__setattr__(ref.provenance, alias, uri)
    mutated = result.model_dump_json()
    public = public_result(result)
    assert CANARY not in public.model_dump_json() + markdown(result)
    assert result.model_dump_json() == mutated
    assert mutated != original
    assert public.refs[0].ref_id == ref.ref_id
    assert public.refs[0].content_hash == ref.content_hash
    assert public.refs[0].locators == ref.locators


@pytest.mark.parametrize("uri", [MAIL, TEL, f"custom:{CANARY}"])
@pytest.mark.parametrize("levels", [1, 2, 3, 4, 6])
def test_encoded_uri_views_fail_closed(uri, levels):
    value = uri
    for _ in range(levels):
        value = quote(value, safe="")
    assert metadata(value) == WITHHELD
    assert exportable_source_url(value) is None
    assert CANARY not in json.dumps(metadata({"title": value, "nested": [value]}))


def test_all_aliases_and_learning_prose_are_separate(tmp_path):
    data, material, store = seed(tmp_path)
    for alias in ("source_path", "title", "license", "attribution"):
        set_alias(material, alias, MAIL)
    material["resource"]["source_url"] = MAIL
    result = generate_once(data, store)
    text = f"Literal lesson URI {MAIL}; equation x:y = 1:2."
    object.__setattr__(result.refs[0], "text", text)
    object.__setattr__(result.claims[0], "text", text)
    object.__setattr__(result.sections[0].claims[0], "text", text)
    public = public_result(result)
    assert (
        public.refs[0].text
        == public.claims[0].text
        == public.sections[0].claims[0].text
        == text
    )
    assert text in markdown(result)
    assert public.refs[0].source_path == WITHHELD
    assert public.refs[0].provenance.title == WITHHELD
    assert public.refs[0].provenance.license == WITHHELD
    assert public.refs[0].provenance.attribution == WITHHELD
    assert public.refs[0].provenance.source_url_status == "withheld"


def test_approved_urls_and_legitimate_metadata_identity(tmp_path):
    urls = json.loads(
        (ROOT / "tests/fixtures/lecture_summary/r08-approved-urls.json").read_text()
    )
    assert len(urls) == len(set(urls)) == 75
    data, material, store = seed(tmp_path)
    material["resource"].update(
        title="Functions and Variables", license="CC BY-NC-SA 4.0"
    )
    material["attribution"] = "CS50, Harvard University"
    result = generate_once(data, store)
    original = result.model_dump(mode="json")
    for url in urls:
        assert metadata(url) == exportable_source_url(url) == url
        candidate = json.loads(json.dumps(original))
        for ref in candidate["refs"]:
            ref["provenance"].update(source_url=url, source_url_status="available")
        store.write(result.run_id, "result.json", candidate)
        raw = store.read(result.run_id, "result.json")
        store.finish(result.run_id, "completed", result_sha256=sha256(raw))
        public = json.loads(store.export_json(result.run_id))["result"]
        md = markdown(store.result(result.run_id))
        assert url in md
        for before, after in zip(candidate["refs"], public["refs"], strict=True):
            assert before == after
            assert after["provenance"]["title"] in md
            assert after["provenance"]["license"] in md
            assert after["provenance"]["attribution"] in md
        assert public["claims"] == original["claims"]
        assert public["state"] == original["state"]
        assert store.read(result.run_id, "result.json") == raw
    assert metadata("Lecture 0 – Functions; CC BY-NC-SA 4.0; CS50, Harvard") != WITHHELD
    assert metadata("00:01") == "00:01"


@pytest.mark.parametrize(
    "value", ["synthetic:transcript", "resource:" + "a" * 64, "notes:0"]
)
def test_identity_grammar_is_field_scoped(value):
    assert metadata({"source_id": value})["source_id"] == value
    for alias in ("source_path", "title", "license", "attribution"):
        assert metadata({alias: value})[alias] == WITHHELD
    assert metadata({"source_id": MAIL})["source_id"] == WITHHELD


def test_original_catalog_identities_and_locators_survive(tmp_path):
    data, material, store = seed(tmp_path)
    result = generate_once(data, store)
    public = public_result(result)
    assert public.refs[0].source_id == material["source_id"]
    assert public.refs[0].artifact_id == material["artifact"]["artifact_id"]
    assert public.refs[0].block_id == material["blocks"][0]["block_id"]
    assert (
        public.refs[0].locators[0].model_dump(mode="json")
        == material["blocks"][0]["locators"][0]
    )


def test_direct_labels_and_review_snapshots_apply_field_policy(tmp_path):
    from src.c27_learning_summary.export import public_reviews, source_label

    data, _, store = seed(tmp_path)
    result = generate_once(data, store)
    local_identity = "resource:" + "a" * 64
    object.__setattr__(result.refs[0], "source_path", local_identity)
    assert local_identity not in source_label(result.refs[0])
    review = Review(
        run_id=result.run_id, reviewer="R08", decision="draft", comment=local_identity
    )
    event = {
        "review_id": "b" * 32,
        "saved_ns": 1,
        "result_sha256": "c" * 64,
        "review": review,
    }
    assert public_reviews([event])[0]["review"]["comment"] == WITHHELD
    assert review.comment == local_identity
    assert metadata({"artifact_id": "a" * 64 + ":token.txt"})["artifact_id"] == WITHHELD
