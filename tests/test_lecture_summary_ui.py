"""Reproducible Streamlit AppTest evidence, with every LLM call offline."""

import json
from pathlib import Path

import pytest

streamlit = pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from src.c27_learning_summary.adapter import load_catalog  # noqa: E402

APP = Path(__file__).resolve().parents[1] / "lecture_summarizer_app.py"
FIXTURE = APP.parent / "tests/fixtures/lecture_summary/catalog.json"


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("LECTURE_SUMMARY_STORE", str(tmp_path / "store"))
    return AppTest.from_file(str(APP), default_timeout=30)


def element(elements, label):
    return next(e for e in elements if e.label == label)


def test_import_navigation_and_no_automatic_run(app, tmp_path):
    at = app.run()
    assert not at.exception
    assert "Lecture Summarizer" in at.header[0].value
    assert element(at.selectbox, "Woche").value == "0"
    assert len(element(at.selectbox, "Lecture / Short").options) == 2
    assert not list((tmp_path / "store/runs").iterdir())
    element(at.selectbox, "Lecture / Short").select_index(1).run()
    assert not at.exception
    assert element(at.selectbox, "Lecture / Short").value == "short-variables"
    assert len(element(at.multiselect, "Einbezogene Quellen").options) == 1


def test_empty_and_invalid_catalog(app, tmp_path, monkeypatch):
    path = tmp_path / "catalog.json"
    path.write_text('{"schema_version":1,"origin":"synthetic","courses":[]}')
    monkeypatch.setenv("LECTURE_SUMMARY_CATALOG", str(path))
    at = app.run()
    assert not at.exception and any("Kein Kurs" in info.value for info in at.info)
    path.write_text('{"invalid": true}')
    at.run()
    assert not at.exception and "Ungültiger" in at.error[0].value


def test_empty_materials_and_unprocessed(app, tmp_path, monkeypatch):
    data = load_catalog(FIXTURE).model_dump(mode="json")
    unit = data["courses"][0]["weeks"][0]["units"][0]
    unit["materials"] = []
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(data))
    monkeypatch.setenv("LECTURE_SUMMARY_CATALOG", str(path))
    at = app.run()
    assert not at.exception and any("Keine Materialien" in i.value for i in at.info)
    original = load_catalog(FIXTURE).model_dump(mode="json")
    unit["materials"] = original["courses"][0]["weeks"][0]["units"][0]["materials"]
    for m in unit["materials"]:
        m["processing_status"] = "pending"
    path.write_text(json.dumps(data))
    at.run()
    assert not at.exception
    assert element(at.button, "Summary starten").disabled


def test_generate_source_review_cache_and_exports(app, tmp_path):
    at = app.run()
    element(at.button, "Summary starten").click().run()
    assert not at.exception and not at.error
    assert any("zur Prüfung bereit" in i.value for i in at.info)
    assert any("Quelle öffnen" in e.label for e in at.expander)
    for select in at.selectbox:
        if select.label == "Aussage bewerten":
            select.select("correct")
    element(at.selectbox, "Gesamtentscheidung").select("approved")
    element(at.button, "Review speichern").click().run()
    assert not at.exception and not at.error
    assert any("freigegeben" in s.value for s in at.success)
    assert len(at.get("download_button")) == 2
    events = list((tmp_path / "store/runs").glob("*/reviews/*.json"))
    assert len(events) == 1
    assert json.loads(events[0].read_text())["review"]["decision"] == "approved"
    element(at.button, "Summary starten").click().run()
    assert not at.exception and any("aus Cache" in i.value for i in at.info)
    assert len(list((tmp_path / "store/runs").glob("*/result.json"))) == 1


def test_review_reject_unreviewed_approval(app):
    at = app.run()
    element(at.button, "Summary starten").click().run()
    element(at.selectbox, "Gesamtentscheidung").select("approved")
    element(at.button, "Review speichern").click().run()
    assert not at.exception
    assert any("Approval requires" in e.value for e in at.error)
    element(at.selectbox, "Gesamtentscheidung").select("rejected")
    element(at.button, "Review speichern").click().run()
    assert not at.exception
    assert any("rejected" in m.value for m in at.markdown)


def test_unconfigured_llm(app):
    at = app.run()
    element(at.selectbox, "Modelladapter").select("litellm").run()
    assert not at.exception
    assert element(at.button, "Summary starten").disabled
    assert any("LLM nicht konfiguriert" in w.value for w in at.warning)


def test_generation_error_state(app, monkeypatch):
    def fail(*args, **kwargs):
        raise ValueError("Synthetic validation failed")

    monkeypatch.setattr("frontend.pages.G_p0_lecture_summarizer.generate", fail)
    at = app.run()
    element(at.button, "Summary starten").click().run()
    assert not at.exception
    assert any("Synthetic validation failed" in e.value for e in at.error)
    assert not at.get("download_button")


def test_changed_material_marks_historical_summary(app, tmp_path, monkeypatch):
    path = tmp_path / "catalog.json"
    path.write_bytes(FIXTURE.read_bytes())
    monkeypatch.setenv("LECTURE_SUMMARY_CATALOG", str(path))
    at = app.run()
    element(at.button, "Summary starten").click().run()
    data = json.loads(path.read_bytes())
    data["courses"][0]["weeks"][0]["units"][0]["materials"][-1]["processing_status"] = (
        "failed"
    )
    path.write_text(json.dumps(data))
    at.run()
    assert not at.exception
    assert any("seit diesem Lauf geändert" in warning.value for warning in at.warning)
