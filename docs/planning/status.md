# C23.0 – geprüfter Stand und offene Befunde

**17.10.2026, Europe/Berlin.** Referenz sind die tatsächlich abgefragten
Default-Branches: Backend `476f0a0d786db87eb59efad36fd21a2fadaeb1dd`,
Tree `e20f61bb8f021d098c1619195b8af3b13f6180e7`; UI
`14ccfc20d83fe57612b5298e323d9f9f1d899cbf`, Tree
`7775226597d3f32c8a9f778c58723b5e63aeb029`.
[Öffentliche Metadaten](c230_snapshot.v1.json) enthalten Commit-/PR-/Issuebelege.
Die lokalen Hauptcheckouts sind älter und wurden deshalb nicht als Statusbasis
verwendet. Beide Planungsbranches beginnen an den oben genannten Default-Heads.

## Statusachsen und Nachweistiefe

| Achse | Erforderlicher Nachweis |
| --- | --- |
| Implementiert und gemergt | Funktion im geprüften Default-Tree und zugehöriger Merge/PR; offener PR allein genügt nicht |
| Technisch getestet | konkret benannte Suite, Datenart, Ergebnis, Datum und Grenzen; ein historischer Lauf ist kein neuer C23.0-Lauf |
| Fachlich evaluiert | unabhängige echte Referenzen, nachvollziehbare Rubrik und manueller Review; synthetische Gegenbeispiele genügen nicht |
| Produktiv freigegeben | ausdrücklicher Operatorentscheid für konkrete Version, Daten, Auth, Storage, Monitoring und Recovery |
| Geplant | vereinbarter Entwurf; kein Implementierungs-, Test- oder Freigabestatus |
| Blockiert | konkrete fehlende Voraussetzung/Entscheidung und nächster prüfbarer Schritt |

C23.0 führt nur Dokumentations-/Konsistenzprüfungen aus. Die nachfolgenden
technischen Testzahlen werden aus versionierten Belegen zitiert, nicht neu
als Anwendungstests ausgeführt oder über verschiedene Suites addiert.

## C19–C22 gegen Default-Branches geprüft

| Paket | Implementiert/gemergt | Technischer Nachweis | Fachliche Evaluation | Produktivfreigabe / offene Arbeit |
| --- | --- | --- | --- | --- |
| C19 | Backend [#69](https://github.com/rf-data/Personal_Assistant/pull/69), `src/job_control/{guardian,executor,pdf_adapter}.py`, `src/tools_materials/parse_pdf.py` | [C19](../job_control/pdf_validation.md): finale 25 lokale Linux-/PDF-Fälle und echte synthetische fünfstufige Kette; [C22](../deployment/c22_validation.md) prüfte diese Verträge erneut | keine allgemeine Qualitätsfreigabe echter PDF-Kurse | nicht freigegeben; PID-Namespace/cgroups/Container-SIGTERM/OOM noch prüfen |
| C20-B | Backend [#70](https://github.com/rf-data/Personal_Assistant/pull/70), `src/workflows/{http,http_models,service}.py` | [HTTP-Vertrag/Abnahme](../workflows/http_validation.md), C21 tatsächlich über TCP | keine Inhalts-/Suchqualität | HTTP-Vertrag ist vorhanden, öffentlicher Betrieb nicht freigegeben |
| C20-C | UI [#3](https://github.com/rf-data/personal-assistant-ui/pull/3), `admin_ui_package/workflow_contract.py`, `workflow_state.py`, `workflow_view.py` und `c16_client.py` | [UI-Nachweis](https://github.com/rf-data/personal-assistant-ui/blob/14ccfc20d83fe57612b5298e323d9f9f1d899cbf/docs/c20_validation.md), C21/C22 AppTest-/TCP-Integration | keine Nutzer-/Inhaltsabnahme | vorhanden: Inspect, Execute, Resume, Cancel, Run-Historie; Search UI C25 fehlt noch |
| C21 | Backend [#71](https://github.com/rf-data/Personal_Assistant/pull/71), UI [#4](https://github.com/rf-data/personal-assistant-ui/pull/4) | [Ergebnisse](../acceptance/c21_results.md): 585 erfolgreiche Backendfälle nach gezielten Wiederholungen, drei Original-Fixture-Skips; 115 UI-Tests; echte TCP-/native Prozessbelege | Notes Week 5 technisch geprüft; keine unabhängige reale Formel-/Material-Goldabnahme | Browser/TLS/OIDC und Zielbetrieb offen; kein vollständig grüner Full-Erstlauf behauptet |
| C22 | Backend [#73](https://github.com/rf-data/Personal_Assistant/pull/73), UI [#5](https://github.com/rf-data/personal-assistant-ui/pull/5), `deployment/`, `scripts/deployment.py`, `src/job_control/operations.py` und UI-Startschutz | [Abnahme](../deployment/c22_validation.md): 148 verschiedene Backendfälle, 123 UI-Fälle, 9 TCP-Prüfpunkte; synthetischer PDF-Provenienz-Restore, Compose-Rendering | keine allgemeine Fach-/Modellqualitätsfreigabe | **blockiert:** Images/Containerlaufzeit, UI-Authlib/OIDC, TLS, finales Volume, Monitoring/Alarmierung |

Die Tabellenpfade benennen vorhandene Module, keine neu eingeführten Verträge.
C16-Queue bleibt SQLite/flock, C18 besitzt eigene Workflowdateien. C22 verlangt
Single-Host mit identischen lokalen Mountpfaden/UIDs, keine verteilte Queue.

## Vorhandene Persistenz und Suche zuerst wiederverwenden

- `src/model_materials/materials.py`: versionierte Materialbindings,
  ArtifactReceipt, NormalizedDocument mit strukturierten Blöcken/Provenienz.
- `src/model_transcribe/data_transcribe.py`, `tools_lecture/adapt_cs50.py` und
  `tools_knowledge/bind_cs50_transcript.py`: Transcript/Cues, Quellenprüfung und
  portable Inputreferenzen. Der Funktionsname Knowledge macht die Bindung nicht
  zu einer verpflichtenden Extraktion.
- `src/model_parsing/`/`src/tools_parsing/`: allgemeine/Legacy-Parser mit anderen
  Verträgen; vor neuer Vereinheitlichung abgleichen, keine pauschale Migration.
- `src/tools_rag/cs50_{ingestion,retrieval,embeddings}.py`,
  `src/model_discovery/cs50_index.py`: vorhandener versionierter Transcriptindex
  und quellgebundenes Retrieval ohne verpflichtende Knowledge-Extraktion.
  [Frühere technische Indexabnahme](../cs50/operations/transcript_index_completion.md)
  nutzte synthetische Quellen/Fake-Embeddings und lokales Qdrant. Das ist kein
  aktueller Real-E5-/Servernachweis.
- C16 SQLite ist eine Jobhistorie, keine bereits beschlossene allgemeine
  Source-/Parsed-Datenbank. PostgreSQL und ein eventueller Volltextindex müssen
  erst im C23-/C24-ADR gegen diese Modelle begründet werden.
- Wikimedia ist etwa in `src/model_parsing/wiki_client.py`, `wiki_assembler.py`
  und `src/tools_parsing/{search_wiki,extract_wiki}.py` vorhanden. C27/C30 prüfen
  Wiederverwendung und externe Informationsqualität, statt neue Clients zu behaupten.

## Noch offene Bugs, Daten- und Deployment-Gates

| Befund | Gegen aktuellen Code/Nachweis geprüft | Einmaliger Planbezug |
| --- | --- | --- |
| TXT unknown times | `TranscriptSegment.start/end: float`; TXT-Importer erzeugt `None`. C21 dokumentiert 6 fehlgeschlagene TXT-Fälle, 33 übrige Importfälle bestanden. Kein Fix im Default-Tree | C23-05; offener PR #9 nur als Teilvorgänger |
| Originalpfad vs. Binding | [Draft #72](https://github.com/rf-data/Personal_Assistant/pull/72), Head `3a42b167`, enthält C21-Q.1: Dateien unter `data/Harvard`, Receipt/Provenienz unter `data/lectures/Harvard`; kein Runtimefallback/keine Migration | C23-03; persistente Originalbindung weiterhin unverified |
| E5/Qdrant Realpilot | PR #72 offen und Draft; dort 84 gezielte Tests/2 optionale Fixture-Skips bei Q.1 dokumentiert. Fehlende Runtime-/Modell-/Serverfreigaben bleiben dort blockiert | optionale C24-04, kein zweiter Pilot |
| Authlib | aktuelles UI-`pyproject.toml`/`uv.lock` enthalten es nicht; `container_runtime.py` verweigert Produktionsstart. Ein Root-Backend-Lockeintrag ist keine UI-Installation | C26-01 |
| Browser/TLS/Container | C22-Nachweis benennt diese Abnahmen ausdrücklich blocked; AppTest/TCP ist kein Browser-/TLS-Nachweis | C25-04, C26-02/C26-03, getrennte Scopes |
| Produktionsmonitoring | C15/C22-Dateien vorhanden, Ziel-Scrape/Hostdisk und echte Alarmzustellung nicht nachgewiesen | C26-05 |
| Originalmaterialien | C21s drei optionale Tests für ursprüngliche Notes-0-/PDF-Artefakte ohne Eingaben; anderes Notes-5-HTML separat technisch geprüft | C23-06 |
| Reale Formelqualität | C11 besitzt 42 synthetische Fälle und begrenzte SymPy-Schnittstelle, aber 0 reale Goldfälle im Beispielbericht | C23-06; keine Qualität echter Extraktion erfunden |

Kein neuer Funktions-/LLM-/Embedding-/Datenbank-/Containerlauf in C23.0. Lokale
unversionierte Quelldaten und Secrets wurden nicht eingelesen. Phase-B-Freigabe
für Qdrant lässt sich auch aus dem neuen Plattformziel nicht ableiten.

## Bestehende GitHub-Vorgänge und Deduplizierung

Die vollständig gelesenen `issues?state=all&per_page=100`-Antworten enthielten
Backend 71 und UI fünf Einträge, jeweils weniger als eine Seite. **Alle sind PRs;
keine eigenständigen offenen oder geschlossenen Issues gefunden.** „Issues“ im
REST-Endpunkt umfasst auch PRs; sie wurden ausdrücklich herausgefiltert.

Backend-PRs #6/#9/#10/#11 sind weiter offen. Der
[bisherige Einzelreview](../cs50/operations/historical_pr_review.md) bezeichnet
#6/#10/#11 funktional als ersetzt; dies ist keine neue Merge-/Closeentscheidung.
#9 enthält den relevanten TXT-Rest und wird in C23-05 verlinkt. PR #72 wird in
C23-03/C24-04 referenziert; Pfadübernahme und optionaler Suchpilot sind getrennte
Aufgaben, keine doppelte Ingestion. UI hat keine offenen PRs im Abgleich.

Der Connector liefert Repositoryrechte admin/maintain/push/triage/pull. Er lehnt
jedoch Milestone-Listen, Owner-Projects-Seite und GraphQL als nicht unterstützte
Endpoints ab (`INVALID_ARGUMENT`). Projects/Milestones sind deshalb **unbekannt**,
nicht „nicht vorhanden“. `has_projects=true` beweist keinen Projects-v2-Zugriff.
Lokal ist `gh` nicht installiert. Keine Credentialdatei wurde dafür gelesen.
[Umsetzbarer Plan und spätere Zugriffsprüfung](github_execution.md).

[C23.0-Dokumentationsprüfung und Grenzen](validation.md).
