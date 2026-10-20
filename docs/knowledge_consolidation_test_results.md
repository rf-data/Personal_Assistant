# C12 – Offline-Testresultate

Umgebung: Python 3.12.12, Pydantic 2.13.4, Pytest 9.1.1, Ruff 0.16.3.
Verwendet wurde die bereits installierte Umgebung; keine Installation oder
Downloads. Basis: `master` (`09f7384`). Tests verwenden temporäre Verzeichnisse,
synthetische Extrakte und deterministische Providerdoubles. Neue Tests sperren
Socketverbindungen/DNS; ein isolierter Prozess blockiert zusätzlich SDK-,
Settings- und Memory-Imports und läuft ohne Umgebungsvariablen/API-Schlüssel.

## Knowledge-/Runner-Regression

```bash
python -m pytest -q \
  tests/test_consolidation_hardening.py \
  tests/test_knowledge_source_id.py \
  tests/test_consolidation_math_import.py \
  tests/test_knowledge_transcript_provenance.py \
  tests/test_lazy_marvin_import.py \
  tests/test_cs50_checkpoint.py \
  tests/test_cs50_knowledge_input.py \
  tests/test_cs50_knowledge_pilot.py \
  tests/test_cs50_precise_evidence.py \
  tests/test_cs50_quality.py \
  tests/test_cs50_srt_knowledge_integration.py
```

Ergebnis: **249 passed, 2 skipped** (251 Fälle, davon 77 neue C12-Tests).
Beide Skips betreffen optionale lokale Original-Pilotartefakte. Synthetische
End-to-End-Tests für Import, Extraktion, Completion, Qualität und Evidence laufen.

Die neuen Tests prüfen:

- Zwei Lectures, je zwei unabhängige Sources, mehrere Chunks, komplette
  Source-Metadaten und disjunkte Evidence wiederholter Fakten.
- Keine Merges unterschiedlicher Operatoren, Case, Negationen, Exponenten,
  Indizes, Bruchterme oder widersprüchlicher Plain-/LaTeX-Darstellungen.
- Chunk-/Item-ID-Kollisionen, fehlende Provenienz, fehlende Referenzen,
  unvollständige Chunks, kaputte JSON-Dateien, Duplicate Keys und NaN.
- Alle sechs Runstatus; neue Verarbeitung, verifiziertes Skip, stale Input/Config,
  fehlende und ungültige Outputs, beschädigte Receipts/Marker, Altdateien ohne
  Receipt, Unterbrechung vor/nach Output sowie verifizierte Wiederaufnahme.
- Source-/Dateinamenskollisionen, Lecture-Auswahl, Symlinks inklusive
  Elternverzeichnis, Root-Grenzen, Traversal, Lockkonflikt, exklusive Publikation,
  unveränderte Bytes/mtime bei Wiederholung und Änderung des Inputs während Stage.
- Explizite semantische Übergabe, Fehlerfortsetzung pro Kurs, Cache-ID-Prüfung,
  unveränderte Formeln, vollständige Evidence und korrekte Statementzuordnung.
- Reportversion, Hashes, reproduzierbaren Beispielreport, CLI-Ausgaben und
  Exitcodes, No-Overwrite für Reports und Outputs, lesende Standardaufrufe.

## Zusätzliche Material-/Parser-Regression

```bash
python -m pytest -q \
  tests/test_cs50_material_quality.py \
  tests/test_cs50_material_html_semantics.py \
  tests/test_cs50_material_pdf_v2.py
```

Ergebnis: **150 passed, 3 skipped**. Skips: optionale originale HTML-Notizen sowie
zwei nicht lokal bereitgestellte Original-PDFs. Kein Download wurde versucht.
HTML-/PDF-Parser wurden nicht verändert. Zusammen: **399 passed, 5 skipped**.

## Statische Prüfung und konkrete Reproduktion

```bash
ruff check src/run_knowledge_consolidation.py \
  src/tools_knowledge/consolidate_knowledge.py \
  src/tools_knowledge/consolidation_run.py \
  src/tools_knowledge/consolidation_validation.py \
  src/tools_knowledge/semantic_knowledge.py \
  tests/test_consolidation_hardening.py
ruff format --check src/run_knowledge_consolidation.py \
  src/tools_knowledge/consolidate_knowledge.py \
  src/tools_knowledge/consolidation_run.py \
  src/tools_knowledge/consolidation_validation.py \
  src/tools_knowledge/semantic_knowledge.py \
  tests/test_consolidation_hardening.py
git diff --check
```

Ergebnis: Ruff **All checks passed**, sechs Python-Dateien korrekt formatiert;
keine Whitespace-Fehler. Python-AST, JSON, finale Newlines, Dateigrößen und lokale
Dokumentlinks wurden zusätzlich geprüft. Netzwerkabhängige Pre-Commit-Umgebungen
wurden nicht initialisiert; ihre zutreffenden Prüfungen wurden lokal ausgeführt.

Der echte CLI-Dry-Run für beide synthetischen Lecture-0-Sources erzeugte einen
explizit angeforderten neuen JSON-Report, aber keinen Ausgabeordner:
`Lectures=1 inputs=2 objects=16 merged=4 errors=0 warnings=8`, Exitcode 0.
Der direkte Moduleinstieg `python -m src.tools_knowledge.consolidate_knowledge
--help` funktioniert ebenfalls ohne SDK-/Settings-Initialisierung.

Zusätzlich wurde die unveränderte Konsolidierungsfunktion aus `master` isoliert
auf denselben synthetischen Input angewendet: Sie führte sowohl
`continuous`/`not continuous` als auch `a + b`/`a - b` zusammen. Mit C12 bleiben
alle vier Aussagen getrennt, während die echte Wiederholung mit anderer
Evidence zusammengeführt wird.

## Umfang der Aussage

Keine Live-LLM-, Netzwerk-, produktiven Datenbank- oder Serverprüfungen. Keine
Modellqualitätswerte. Qdrant-Index-/Retrieval-Suiten wurden nicht ausgeführt:
Die optionale Dependency `qdrant_client` fehlt in der vorhandenen Umgebung;
sie wurde nicht nachinstalliert. Ein vollständiger Repository-Gesamtlauf wird
nicht behauptet. Verbleibende fachliche und betriebliche Grenzen stehen im
[Resume-/Skip-Vertrag](knowledge_consolidation_hardening.md).
