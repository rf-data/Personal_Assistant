# Roadmap — Personal Assistant

Stand: 16.10.2026. Verifiziert gegen Backend-`master` `78b35a5` und UI-`main`
`137651e`; [Commit-/PR-Snapshot](audit/remote_snapshot.v1.json).
Die [lokale Inventur](repository_inventory.md) trennt gemergte Funktionen von
alten Arbeitskopien. Ein Merge und technische Offline-Tests sind keine Freigabe
für produktive Dienste, reale Kursqualität oder kostenpflichtige Verarbeitung.

## C10–C18: belegter Stand

| Paket | Repository / gemergter PR | Status und tatsächlicher Umfang | Verbleibende Grenze |
| --- | --- | --- | --- |
| C10 Material Quality Gate | Backend [#61](https://github.com/rf-data/Personal_Assistant/pull/61) | implementiert, offline getestet, gemergt: Hash-/Schema-/Provenienzprüfung und read-only Lecture-Material-Handoff | keine automatische Knowledge-Extraktion oder fachliche Semantikfreigabe |
| C11 Mathematical Evaluation | Backend [#62](https://github.com/rf-data/Personal_Assistant/pull/62) | implementiert, offline getestet, gemergt: 40 synthetische Fälle, exakter/normalisierter/struktureller Vergleich, optionale isolierte Polynomprüfung | unabhängige reale Goldreferenzen und breitere mathematische Syntax offen |
| C12 Consolidation Hardening | Backend [#63](https://github.com/rf-data/Personal_Assistant/pull/63) | implementiert, offline getestet, gemergt: konservative Deduplikation, Evidence, hashgebundenes Resume und No-Overwrite | semantischer/live Adapter bleibt explizit freizugeben |
| C13 Visual Inventory | Backend [#64](https://github.com/rf-data/Personal_Assistant/pull/64) | implementiert, offline getestet, gemergt: technische Raster-/SVG-/Vektor-/Dokumentprovenienz | kein neues Enrichment, keine OCR oder fachliche Diagrammbewertung |
| C14 Admin UI | UI [#1](https://github.com/rf-data/personal-assistant-ui/pull/1) | implementiert, getestet, gemergt: kanonische Admin-App, Rollen, Inventar/Logs und getrennte Fake-Demo | keine Aussage zu Live-Deployment oder Knowledge-Chatqualität |
| C15 Monitoring | Backend [#65](https://github.com/rf-data/Personal_Assistant/pull/65) | implementiert, offline getestet, gemergt: begrenzte Composeprofile, Provisionierung und endlicher Metricsvertrag | explizite Images/Secrets/Targets und Runtime-/Lastfreigabe offen |
| C16 Job Execution Backend | Backend [#66](https://github.com/rf-data/Personal_Assistant/pull/66) | implementiert, offline getestet, gemergt: zwei Defaultadapter, Auth/Owner/Course, SQLitequeue, Executor/Guardian, Cancel/Restart/Metriken | lokaler HTTPServer; kein dediziertes Produktionsimage/TLS-/Mehrhostmodell |
| C17 UI Integration | UI [#2](https://github.com/rf-data/personal-assistant-ui/pull/2) | implementiert, technisch E2E getestet, gemergt: echter C16-Client für Planung/Qualitätsjobs | C18-Workflow-DTOs noch nicht integriert; kein Live-Deployment belegt |
| C18 Pipeline Orchestration | Backend [#67](https://github.com/rf-data/Personal_Assistant/pull/67) | implementiert, offline getestet, gemergt: optionaler lokaler Materialworkflow mit DAG, Preview, Skip/Stale/Resume und Reports | drei HTML-/Code-Materialien; PDF-Lebensdauer, UI und automatische Folgestufen offen |

Beim Auditabruf waren diese PRs alle gemergt. Es wurde kein offener PR als
fertige Masterfunktion dargestellt. Die Begrenzungen der jeweiligen Verträge
bleiben verbindlich, auch wenn das Arbeitspaket technisch abgeschlossen ist.

## Priorisierte nächste Integrationsschritte

1. **PDF unter C16 kontrollieren:** bestätigte vollständige Cancel-/Timeout-/
   Worker-Restart-Lebensdauer des vorhandenen PDF-Subprozesses nachweisen;
   erst danach C18-Parsing freigeben. Keine Ersatzparser entwickeln.
2. **C18 in C17 sichtbar machen:** eigener UI-PR für versionierte Workflow-
   Capabilities/DTOs, Preview, Status, Artefakte, Stale-/Resume-/Cancelanzeigen;
   bestehende zwei Defaultprozesse müssen kompatibel bleiben.
3. **Fachliche Evaluation:** reale unabhängig annotierte Formel-/Evidencefälle,
   nachvollziehbare Herkunft und manuelle Review; synthetische Erfolgsquoten
   nicht als Modellqualität darstellen. C13-Dokumentpositionen separat an den
   bisherigen zeit-/framebasierten Visualvertrag anbinden.
4. **Deploymentfreigabe:** dedizierte API-/Executorprofile, private gemeinsame
   Persistenz, TLS/Ingress, Secretdateien, Ressourcengrenzen und Last-/Recoverytests;
   getrenntes UI-Deployment und autoritative Metrics-Scrapeidentität.
5. **Bekannte technische Lücken:** TXT ohne Zeitstempel (`TranscriptSegment`
   verlangt Zahlen), optionale SDK-/Indexprofile und unvollständige Legacy-
   Visualverdrahtung gezielt behandeln; keine künstlichen Zeitstempel oder
   Tests mit abgeschwächten Assertions.
6. **Bereinigung mit konkreter Freigabe:** [Cleanupplan](cleanup_plan.md) für
   Legacy-UI, alte API-/MLflow-Buildpfade, Dependencyduplikate, Prototypen,
   unerwartete Artefakte und alte Worktrees. Keine pauschale Löschung.

## Vorhandene zusätzliche Fähigkeiten

Discovery-/SRT-first-Verträge für sechs CS50-Kurse, Lecture-/Kursrunner,
Checkpoint/Budget/Evidence, Transcript-Ingestion und quellgebundenes Retrieval
sind implementiert und besitzen Offline-Nachweise. Lokale Inferenz, echte
LLM-Kursverarbeitung und kanonischer Knowledge-Index sind davon getrennte
Freigabe-/Evaluationsschritte. [CS50-Einstieg](cs50/README.md),
[Indexgrenzen](cs50/operations/transcript_index_completion.md).

Allgemeines Dokumentparsing, Chroma-/SOP-RAG und yt-dlp-/Whisperpfade bleiben
als Legacy-/optionale Implementierungen vorhanden. Sie werden nicht wegen
vorhandener Dateien pauschal als produktionsreif markiert. E-Mail/Kalender,
SOP-Updates, Knowledge-Graph, Lernchat, Quiz/Flashcards, Grounded QA und
Studydokumentexport bleiben geplant oder experimentell, soweit kein eigener
aktueller Nachweis vorliegt.

## Audit C17.0

Dieses Paket ist ein Dokumentations-/Konsolidierungsaudit und nicht das bereits
gemergte UI-Paket C17. Es aktualisiert Einstiegspunkte, Status und Referenzen,
erfasst alle verfügbaren Dokumentvarianten und legt riskante Maßnahmen als
Freigabeliste vor. Kein History-Rewrite, keine Worktree-/Branchentfernung,
kein automatisches Merge oder Deployment. Die lokale unversionierte
Roadmap-Ergänzung und private ignorierte Berichte bleiben unverändert.

Die vorherigen pauschalen Phasenhäkchen und C01–C09-Planungen sind im
[historischen Überblick](archive/2026-10/repository-overview/ROADMAP.md) erhalten.
Sie sind weder ein aktueller Fertigstellungsnachweis noch ein aktiver Jobauftrag.

## Weiterhin offene historische PRs

Backend #6, #9, #10 und #11 sind laut API weiterhin offen. Ihre Existenz bedeutet
nicht, dass ihre alten Patches ungeprüft in den aktuellen Master gehören:
Discovery, Source-IDs und der Importfix sind fachlich ersetzt; #9 enthält den
noch offenen TXT-Unknown-Time-Rest. [Einzelprüfung und Empfehlung](cs50/operations/historical_pr_review.md).
Schließung oder Komplettübernahme erfolgt hier nicht automatisch.
