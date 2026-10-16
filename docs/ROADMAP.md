# Roadmap — Personal Assistant
Stand: 2026-10-12

Gültig für: Personal_Assistant (master) und personal-assistant-ui (main).

Status-Legende: [x] = bisher als abgeschlossen geführt / Code vorhanden; [~] = Prototyp, teilweise oder nicht end-to-end geprüft; [ ] = offen. Der Status berücksichtigt Repository-Stichproben, **nicht** die tatsächlich auf Hetzner vorliegenden Datensätze oder laufende Dienste.

## Kurzfristig: stabiler Admin-Prototyp (personal-assistant-ui)

- [~] Separates UI-Repo mit Streamlit app_ui.py, Dockerfile und Coolify-Compose vorhanden; derzeit nur einfacher Dateibrowser.
- [ ] Einheitliche BaseSettings-Konfiguration mit APP_ENV, DATA_DIR, LOG_DIR und Tests.
- [ ] Admin-Einstiegspunkt: Dashboard, Dateiansicht, Logs (keine Duplikation von app_ui.py).
- [ ] Read-only Dateiinventar, Stage-Zählung (zunächst exakt *_know_extract.json und *_know_consol.json) und konfigurierbare weitere Muster.
- [ ] Zählung nach Kurs und Lecture ID statt nur nach einzelnen Dateien; fehlende Folgestufen erkennen.
- [ ] Sicherer Log-Viewer: read-only, Pfadvalidierung, begrenztes Lesen, Server-Log-Mount prüfen.
- [ ] Coolify-Konfiguration dokumentieren und UI-Zugang absichern.
- [ ] Zweiten Einstiegspunkt Knowledge Assistant vorbereiten; Chat/Evidence/Quiz getrennt von Serveradministration.

## Kurzfristig: Qualitäts- und Testfundament (Personal_Assistant)

- [x] C12: Kursweise Knowledge-Consolidation offline gehärtet und deterministisch getestet; lesender Standard, hashgebundenes Resume, kein Overwrite ([Vertrag](knowledge_consolidation_hardening.md)).
- [ ] Deterministische Unit-Tests für Resume/Skip, Pfadgenerierung und Ausnahmen (ohne echte LLM-Aufrufe).
- [ ] Echte Stage-Dateinamen aus Datenbestand erfassen und Naming-Konvention fixieren.
- [ ] Quality Checks und Gold-Eval-Set (zunächst 30–50 manuell geprüfte Fälle).
- [ ] Alte Dokumentation auf aktuellen Lecture-Fokus und UI-Trennung aktualisieren.

---

## Bestehende Phasen (bisheriger Stand, nicht automatisch hochgestuft)

PHASE 1 — DATA QUALITY
────────────────────────────────────
[x] Transcript extraction
[x] Knowledge extraction
[x] Visual verification
[x] Visual enrichment remaining lectures
[x] Visual post-processing
[ ] Quality checks


PHASE 2 — KNOWLEDGE CORE
────────────────────────────────────
[x] Canonical Knowledge Merge
[x] Evidence / Provenance model
[x] Knowledge IDs
[ ] Relation model
[ ] Basic relation extraction
[ ] Knowledge validation


PHASE 3 — EVALUATION
────────────────────────────────────
[ ] Gold/eval dataset
[ ] Retrieval evaluation
[ ] Formula reconstruction evaluation
[ ] Transcript conflict evaluation
[ ] Answer grounding evaluation


PHASE 4 — RETRIEVAL
────────────────────────────────────
[ ] Embeddings
[ ] Vector DB
[ ] Semantic Search
[ ] Metadata filtering
[ ] Evidence retrieval
[ ] Hybrid retrieval


PHASE 5 — LEARNING APPLICATION
────────────────────────────────────
[ ] Ask the Lecture
[ ] Source / evidence display
[ ] Jump to video timestamp
[ ] Quiz generation
[ ] Flashcards
[ ] Voice query


PHASE 6 — DOCUMENT GENERATION
────────────────────────────────────
[ ] Study-document model
[ ] LaTeX template
[ ] Summary export
[ ] Quiz export
[ ] Formula sheet export
[ ] PDF generation


PHASE 7 — KNOWLEDGE GRAPH
────────────────────────────────────
[ ] Relation extraction
[ ] Relation validation
[ ] Graph construction
[ ] Graph visualization
[ ] Graph-assisted retrieval


PHASE 8 — PRODUCT
────────────────────────────────────
[ ] FastAPI backend
[ ] Streamlit / web frontend
[ ] Evaluation dashboard
[ ] Observability
[ ] Deployment


PHASE 9 — PORTFOLIO / DOCUMENTATION
────────────────────────────────────
[ ] Architecture diagram
[ ] Dataset description
[ ] Evaluation methodology
[ ] Benchmark results
[ ] Example failure cases
[ ] Demo video
[ ] README
[ ] Technical case study

---

## Codex-Backlog — kurze, kontrollierbare PRs

Priorität: C01 → C02 → C03/C04 → C05 → C06 → C07/C08/C09.
Jede Aufgabe in genau **einem** Repo und mit eigener PR, ohne Live-Server-Zugriff.

| ID | Repo | Konkrete Aufgabe | Fertig, wenn |
|---|---|---|---|
| C01 | personal-assistant-ui | Environment-Konfiguration als BaseSettings (local/server/auto), klare Defaults | Tests für env overrides und Pfade bestehen |
| C02 | personal-assistant-ui | Reine Stage-Klassifikation + Read-only Dateiinventar | Testdateien *_know_extract.json, *_know_consol.json werden eindeutig gezählt, unbekannte separat |
| C03 | personal-assistant-ui | Dateiansicht mit Filter nach Stage, Größe und mtime | Kein Schreibzugriff, keine unbeschränkte Dateivorschau |
| C04 | personal-assistant-ui | Sicherer Log-Viewer mit Tail-Begrenzung | Pfadtraversal-/Symlink-Tests; nur LOG_DIR |
| C05 | personal-assistant-ui | Dashboard aus gemeinsamem Datei-Inventar | Keine wiederholte Scanlogik, leere Ordner funktionieren |
| C06 | personal-assistant-ui | Docker/Coolify README und Mount-Konfiguration | Lokal und Coolify dokumentiert; read-only Mounts |
| C07 → C12 | Personal_Assistant | Knowledge Consolidation Hardening implementiert: Resume/Skip, Evidence, Identitäten, Reports | Synthetische Offline-Tests; [Vertrag](knowledge_consolidation_hardening.md) |
| C08 | Personal_Assistant | pyproject.toml: doppelte lecture-worker Dependencies beseitigen | Lock/Tests ohne ungefragte Upgrades |
| C09 | Personal_Assistant | README und docs/architecture.md gegen aktuellen Repo-Code abgleichen | Keine unbelegten Aussagen; kleine Doku-PR |
| C13 | Personal_Assistant | Read-only Visual-Asset-Inventur implementiert: Raster-/SVG-/Vektorkandidaten und Dokumentprovenienz | [Vertrag, CLI und Grenzen](visual_inventory.md); deterministische Offline-Tests und HTML-/PDF-Beispielreports |

### Größere Arbeiten: erst nach Evaluation / Architekturentscheidung
- Canonical Knowledge Embedding/Vector DB, Retrieval, Hybrid Search und Grounded QA.
- Knowledge-Graph, große Refactorings, Agenten und produktive Job-Steuerung.
- Live-LLM-Jobs, umfangreiche Cloud-Tests oder Änderungen an produktiven Servern.

### Arbeitsregeln für Codex
1. Ein Ticket = ein Repo = ein PR; niemals direkt deployen oder mergen.
2. Kein Zugriff auf echte Daten, Geheimnisse, .env-Dateien oder produktive Volumes.
3. Vorhandene Interfaces und Ausgabeformate beibehalten.
4. Neue Logik mit Tests, Ruff/Pytest-Resultate in der PR-Beschreibung.
5. Kein pauschales Reformatting und keine neuen Dependencies ohne Begründung.

### Beobachtete Risiken (Stand 2026-10-12)
- UI-Repo auf GitHub enthält bisher app_ui.py als einfachen Dateibrowser, nicht die lokal besprochene Admin-App.
- UI-Container mountet /srv/personal-assistant/data read-only; Logs sind noch nicht als separater Mount belegt.
- Im Haupt-Repo existiert allgemeine RAG/Chroma-Infrastruktur, ein Index kanonischer Lecture-Knowledge-Objekte ist **nicht** belegt.
- Die README/architecture.md im Haupt-Repo beschreiben noch stark die frühere GMP-Anwendung.
