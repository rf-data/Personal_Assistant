"""Local lecture workspace, following the repository's show() page convention."""

import importlib.util
import json
import os
from pathlib import Path

import streamlit as st

from src.c27_learning_summary.adapter import load_catalog
from src.c27_learning_summary.engine import SummaryRunError, generate, input_snapshot
from src.c27_learning_summary.export import markdown, source_label, visible_claims
from src.c27_learning_summary.llm import FakeLLM, LiteLLMSummaryModel
from src.c27_learning_summary.models import ClaimReview, Review, SummaryConfig
from src.c27_learning_summary.store import SummaryStore
from src.content_store.models import fingerprint

ROOT = Path(__file__).resolve().parents[2]
DEMO = ROOT / "tests/fixtures/lecture_summary/catalog.json"


def _material_view(material):
    resource = material.resource
    with st.expander(
        f"{resource.title or material.material_id} · {material.processing_status}"
    ):
        st.json(
            dict(
                material_id=material.material_id,
                type=resource.resource_type,
                source=resource.source_url or material.source_path,
                available=material.available,
                verification=material.verification,
                processing_status=material.processing_status,
                last_processing_run=material.artifact.last_run
                if material.artifact
                else None,
                parser_version=material.artifact.parser_version
                if material.artifact
                else None,
                error=material.error,
            )
        )
        for block in material.blocks:
            st.caption(f"{block.block_id} · {block.aggregation_role}")
            st.text(block.text)
            st.json(
                [loc.model_dump(mode="json") for loc in block.locators], expanded=False
            )


def _review(store, result):
    events = store.reviews(result.run_id)
    latest = events[-1]["review"] if events else {}
    decision = latest.get("decision", "draft")
    st.write(f"Reviewstatus: {decision}")
    if decision == "approved":
        st.success("Summary freigegeben – für den gespeicherten Quellumfang")
    old = {c["claim_id"]: c for c in latest.get("claims", [])}
    with st.form(f"review-{result.run_id}"):
        reviewer = st.text_input(
            "Reviewer", value=latest.get("reviewer", "local-reviewer")
        )
        ratings = []
        for claim in result.claims:
            previous = old.get(claim.claim_id, {})
            st.text(claim.text)
            options = ["unreviewed", "correct", "questionable", "false"]
            rating = st.selectbox(
                "Aussage bewerten",
                options,
                index=options.index(previous.get("rating", "unreviewed")),
                key=f"rating-{result.run_id}-{claim.claim_id}",
            )
            comment = st.text_input(
                "Kommentar zur Aussage",
                value=previous.get("comment", ""),
                key=f"comment-{result.run_id}-{claim.claim_id}",
            )
            recheck = st.checkbox(
                "Zur Nachprüfung markieren",
                value=previous.get("recheck", False),
                key=f"recheck-{result.run_id}-{claim.claim_id}",
            )
            ratings.append(
                ClaimReview(
                    claim_id=claim.claim_id,
                    rating=rating,
                    comment=comment,
                    recheck=recheck,
                )
            )
        choices = ["draft", "approved", "rejected"]
        decision = st.selectbox(
            "Gesamtentscheidung", choices, index=choices.index(decision)
        )
        comment = st.text_area("Reviewkommentar", value=latest.get("comment", ""))
        submitted = st.form_submit_button("Review speichern")
    if submitted:
        try:
            store.save_review(
                Review(
                    run_id=result.run_id,
                    decision=decision,
                    reviewer=reviewer,
                    comment=comment,
                    claims=ratings,
                )
            )
            st.success(f"Review gespeichert: {decision}")
            st.rerun()
        except (ValueError, RuntimeError) as exc:
            st.error(str(exc))


def show(catalog_path=None, store_root=None):
    st.header("Lecture Summarizer & Learning Dashboard")
    st.caption(
        "Lokaler synchroner MVP · keine Downloads · keine automatische LLM-Ausführung"
    )
    catalog_path = Path(catalog_path or os.environ.get("LECTURE_SUMMARY_CATALOG", DEMO))
    store_root = Path(
        store_root
        or os.environ.get("LECTURE_SUMMARY_STORE", ROOT / "data/lecture_summary")
    )
    try:
        catalog = load_catalog(catalog_path)
    except (OSError, ValueError):
        st.error(
            "Ungültiger oder nicht lesbarer Materialkatalog; keine Verarbeitung möglich."
        )
        return
    st.caption(f"Katalog: {catalog.origin}")
    if not catalog.courses:
        st.info("Kein Kurs vorhanden.")
        return
    courses = {c.course_id: c for c in catalog.courses}
    course_id = st.selectbox(
        "Kurs", list(courses), format_func=lambda key: courses[key].course_title
    )
    course = courses[course_id]
    if not course.weeks:
        st.info("Keine Wochen vorhanden.")
        return
    weeks = {w.section_id: w for w in course.weeks}
    week_id = st.selectbox(
        "Woche",
        list(weeks),
        format_func=lambda key: weeks[key].title or key,
        key=f"week-{course_id}",
    )
    week = weeks[week_id]
    if not week.units:
        st.info("Keine Lecture oder Shorts vorhanden.")
        return
    units = {u.section_id: u for u in week.units}
    unit_id = st.selectbox(
        "Lecture / Short",
        list(units),
        format_func=lambda key: f"{units[key].kind}: {units[key].title or key}",
        key=f"unit-{course_id}-{week_id}",
    )
    unit = units[unit_id]
    scope = (course.course_id, week.section_id, unit.section_id)
    st.write(f"Materialanzahl: {len(unit.materials)}")
    if not unit.materials:
        st.info("Keine Materialien vorhanden.")
        return
    for material in unit.materials:
        _material_view(material)
    eligible = [
        m.material_id
        for m in unit.materials
        if m.available
        and m.verification != "unverified"
        and m.processing_status == "completed"
    ]
    selected = st.multiselect(
        "Einbezogene Quellen", eligible, default=eligible, key=f"sources-{scope}"
    )
    summary_type = st.selectbox(
        "Summary-Typ", ["overview", "structured", "notes", "glossary", "code"], index=1
    )
    provider = st.selectbox("Modelladapter", ["fake", "litellm"])
    model_name = st.text_input(
        "Modell",
        value="fake-extractive-v1" if provider == "fake" else "",
        key=f"model-{provider}",
    )
    defaults = SummaryConfig()
    with st.expander("Modell- und Promptkonfiguration"):
        prompt_version = st.text_input("Promptversion", value=defaults.prompt_version)
        prompt = st.text_area("Prompt", value=defaults.prompt)
        chunk_chars = st.number_input(
            "Zeichen je Quellabschnitt",
            min_value=64,
            max_value=8000,
            value=defaults.chunk_chars,
        )
        max_chunks = st.number_input(
            "Maximale Abschnitte", min_value=1, max_value=32, value=defaults.max_chunks
        )
        input_bytes = st.number_input(
            "Maximale Eingabebytes pro Aufruf",
            min_value=8000,
            max_value=64000,
            value=defaults.max_input_bytes,
        )
        output_tokens = st.number_input(
            "Maximale Ausgabetokens",
            min_value=128,
            max_value=4000,
            value=defaults.max_output_tokens,
        )
        temperature = st.slider("Temperatur", 0.0, 1.0, 0.0)
        retries = st.selectbox("Wiederholungen bei Fehlern", [0, 1])
        timeout = st.number_input(
            "Timeout pro Aufruf (Sekunden)", min_value=1, max_value=30, value=20
        )
        wall = st.number_input(
            "Laufzeitgrenze (Sekunden)", min_value=1, max_value=180, value=120
        )
        priced = st.checkbox("Modellpreise konfiguriert")
        input_price = st.number_input(
            "USD pro Million Eingabetokens", min_value=0.0, value=0.0
        )
        output_price = st.number_input(
            "USD pro Million Ausgabetokens", min_value=0.0, value=0.0
        )
    configured = provider == "fake" or (
        bool(model_name.strip()) and importlib.util.find_spec("litellm") is not None
    )
    if not configured:
        st.warning(
            "LLM nicht konfiguriert: Modell und optionale LiteLLM-Abhängigkeit erforderlich. Zugangsdaten nur über lokale Umgebung konfigurieren."
        )
    force = st.checkbox(
        "Explizit neu generieren (historische Ergebnisse bleiben erhalten)"
    )
    try:
        store = SummaryStore(store_root)
    except OSError:
        st.error("Lokaler Ergebnisspeicher ist nicht schreibbar.")
        return
    if st.button("Summary starten", disabled=not selected or not configured):
        try:
            config = SummaryConfig(
                provider=provider,
                model=model_name,
                summary_type=summary_type,
                prompt_version=prompt_version,
                prompt=prompt,
                chunk_chars=chunk_chars,
                max_chunks=max_chunks,
                max_input_bytes=input_bytes,
                max_output_tokens=output_tokens,
                temperature=temperature,
                retries=retries,
                request_timeout=timeout,
                wall_seconds=wall,
                input_usd_per_million=input_price if priced else None,
                output_usd_per_million=output_price if priced else None,
            )
            backend = (
                FakeLLM() if provider == "fake" else LiteLLMSummaryModel(model_name)
            )
            bar = st.progress(0.0, text="Summary läuft")
            with st.spinner("Abschnittsweise Verarbeitung …"):
                outcome = generate(
                    store,
                    catalog,
                    *scope,
                    selected,
                    config,
                    backend,
                    force=force,
                    progress=lambda done, total: bar.progress(
                        done / total, text=f"Abschnitt {done}/{total}"
                    ),
                )
            st.session_state[f"result-{scope}"] = outcome.result.run_id
            st.session_state[f"cached-{scope}"] = outcome.from_cache
        except (ValueError, RuntimeError, OSError) as exc:
            st.error(
                str(exc)
                if isinstance(exc, (ValueError, SummaryRunError))
                else "Summary fehlgeschlagen oder lokaler Lauf bereits aktiv."
            )
    history = []
    for state in store.history():
        inputs = json.loads(store.read(state["run_id"], "input.json"))
        if (inputs["course_id"], inputs["week_id"], inputs["lecture_id"]) == scope:
            history.append(state)
    if history:
        st.write("Gespeicherte Läufe")
        st.dataframe(
            [
                {k: s.get(k) for k in ("run_id", "status", "result_state", "error")}
                for s in history
            ],
            hide_index=True,
        )
    completed = [s["run_id"] for s in history if s["status"] == "completed"]
    if not completed:
        st.info("Summary-Status: noch kein Ergebnis.")
        return
    preferred = st.session_state.get(f"result-{scope}", completed[0])
    run_id = st.selectbox(
        "Gespeicherte Summary",
        completed,
        index=completed.index(preferred) if preferred in completed else 0,
    )
    try:
        result = store.result(run_id)
        original_selection = sorted({ref.material_id for ref in result.refs})
        current_key = fingerprint(
            input_snapshot(catalog, unit, *scope, original_selection, result.config)
        )
        if current_key != result.cache_key:
            st.warning(
                "Quellen oder Materialstatus haben sich seit diesem Lauf geändert. Erneut generieren; ein Review gilt für den gespeicherten Stand."
            )
        if st.session_state.get(f"cached-{scope}") and preferred == run_id:
            st.info("Summary aus Cache")
        if result.state == "ready_for_review":
            st.info("Summary zur Prüfung bereit")
        else:
            st.error(
                "Unvollständiges oder fehlerhaftes Ergebnis: Nachprüfung erforderlich; Freigabe gesperrt."
            )
        for warning in result.warnings:
            st.warning(warning)
        st.caption(
            f"Gespeicherter Summary-Typ: {result.config.summary_type} · Modell: {result.config.model} · Prompt: {result.config.prompt_version}"
        )
        st.json(
            dict(usage=result.usage, estimated_cost_usd=result.estimated_cost_usd),
            expanded=False,
        )
        refs = {r.ref_id: r for r in result.refs}
        claims = visible_claims(result)
        if not claims:
            st.info("Keine belegten Inhalte für diesen Summary-Typ.")
        for claim in claims:
            st.markdown(f"**{claim.category}**")
            st.text(claim.text)
            for ref_id in claim.refs:
                ref = refs[ref_id]
                with st.expander(f"Quelle öffnen · {ref.material_id} · {ref.block_id}"):
                    st.caption(source_label(ref))
                    st.text(ref.text)
                    st.json(ref.model_dump(mode="json"), expanded=False)
                    st.caption(
                        "Gesicherter Originalausschnitt. Direkter Dateisprung ist im MVP nicht verfügbar; die genaue Referenz steht oben."
                    )
        if result.config.summary_type == "notes":
            with st.expander("Abschnittsstruktur und Unsicherheiten"):
                st.json([s.model_dump(mode="json") for s in result.sections])
        _review(store, result)
        st.download_button(
            "Markdown exportieren",
            markdown(result, store.reviews(run_id)),
            file_name=f"summary-{run_id}.md",
            mime="text/markdown",
        )
        st.download_button(
            "JSON exportieren",
            store.export_json(run_id),
            file_name=f"summary-{run_id}.json",
            mime="application/json",
        )
    except (ValueError, OSError):
        st.error(
            "Gespeichertes Ergebnis ist beschädigt oder nicht lesbar; keine Freigabe möglich."
        )
