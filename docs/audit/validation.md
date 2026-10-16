# C17.0 — Validierung und bekannte Grenzen

Stand: 16.10.2026. Backendbasis `78b35a5`; UI-Inhalt treegleich zu `main`
`137651e`. [Maschinenbeleg](validation.v1.json),
[Inventar](../repository_inventory.md), [Cleanupplan](../cleanup_plan.md).
Keine neuen Dependencies, Downloads, LLM-Aufrufe, produktiven Jobs,
Deployment-/Containerstarts, Datenmigrationen oder History-Rewrites.

## Endgültige Ergebnisse

| Prüfung | Ergebnis | Aussage / Grenze |
| --- | --- | --- |
| Backend-Offlinescope | **671 passed, 3 skipped in 239.02 s** (674 Fälle) | Material/HTML/PDF/Code, C10–C13, Knowledge-Provenienz, C16/C18, Monitoring und Audit |
| abschließender Audit-/Monitoring-Fokus | **36 passed**: elf Auditfälle + 25 Monitoringfälle | fünf zusätzliche sensible Dokumentnamen geprüft; zwei Fixture-Schutztests; bestehende Assertions erhalten |
| separates UI | **71 Tests, OK in 21.559 s** | unveränderter treegleicher C17-Worktree gegen aktuelles Backend, serialisierter Offline-E2E-Transport |
| offizieller Transcript-Import, getrennt | **33 passed, 6 failed in 1.11 s** | die sechs bekannten TXT-/Unknown-Time-Vertragsfehler unverändert reproduziert |
| reine Import-Smokes | **13 bestanden** | frische isolierte Prozesse, keine globalen Settings/Memory, Socket/DNS gesperrt |
| CLI-Help-Smokes | **8 bestanden** | keine Verarbeitung, Daten, Provider oder Keys benötigt |
| AST der Ausgangsbasis | **353 Pythondateien syntaktisch lesbar** | statische Analyse; keine Ausführung der Legacy-Module |
| Ruff Check / Format | drei geänderte/neue Pythondateien bestanden; UI 31 Dateien bestanden | Auditor, dessen Tests und korrigierte Monitoring-Testfixture |
| Monitoring | **0 strukturelle Fehler; Compose config bestanden** | kein Pull/Build/Run, synthetische Umgebung, kein `.env`-Laden |
| MLflow Compose | **config --quiet: Exit 0** | nur Syntax; nicht belegter Buildpfad bleibt dokumentiert |

Der breite Lauf enthielt sechs Auditfälle. Anschließend wurde der Auditor um
fünf zusätzliche Privacyfälle für sensible Dokumentnamen geprüft und die
relevante Audit-/Monitoring-Suite erneut unverändert fachlich ausgeführt; diese
36 Fälle ersetzen keine neue behauptete Gesamtzählung.

Die drei Skips betreffen nicht lokal bereitgestellte Originalnotizen und zwei
Original-PDFs. Es wurde kein Ersatz heruntergeladen. Die Backend-Suite ist kein
Repository-Gesamtlauf mit allen optionalen SDK-/Index-/Produktivpfaden. Ihre
Erfolgszahl wird nicht mit UI- oder getrennten TXT-Fällen zu einer vermeintlichen
vollständigen Modellqualitätsquote verrechnet.

## Konkreter Testlauf

Vorhandene Backendumgebung: Python 3.12.12, Pydantic 2.13.4, Pytest 9.1.1,
Ruff 0.16.3; UI-Umgebung wie im bestehenden C17-Profil. Keine Installation oder
Neuauflösung von Locks. Frischer, ausschließlich für diesen Lauf vorgesehener
Scratchpfad auf tmpfs; die Arbeitsplatte hatte im vorherigen C18-Lauf unabhängig
reproduzierbare ENOSPC-Fehler beim atomaren Ersetzen von Metadaten gezeigt.
Die atomare Produktimplementierung wird dafür nicht umgangen oder verändert.

```bash
CS50_TEST_PROFILE=offline python -m pytest -q \
  tests/test_repository_audit.py tests/test_cs50_material_*.py \
  tests/test_cs50_visual_inventory.py tests/test_math_formula_evaluation.py \
  tests/test_consolidation_hardening.py tests/test_knowledge_source_id.py \
  tests/test_knowledge_transcript_provenance.py \
  tests/test_consolidation_math_import.py tests/test_lazy_marvin_import.py \
  tests/test_job_control.py tests/test_job_executor.py tests/test_cs50_workflows.py \
  tests/test_pipeline_metrics.py tests/test_monitoring_config.py \
  --basetemp=/dev/shm/new-c170-test-root

# Getrennter bekannter Problemvertrag, nicht als grün ausgewiesen:
CS50_TEST_PROFILE=offline python -m pytest -q tests/test_official_transcript_import.py

ruff check --no-cache scripts/repository_audit.py \
  tests/test_repository_audit.py tests/test_monitoring_config.py
ruff format --check --no-cache scripts/repository_audit.py \
  tests/test_repository_audit.py tests/test_monitoring_config.py
```

Im UI-Repository mit dessen bereits installierter Umgebung:

```bash
C16_REPO=/path/to/gmp_compliance C16_PYTHON=/path/to/backend-venv/bin/python \
  python -m unittest discover -s tests -v
```

Die 13 sicheren Imports betreffen Discovery-, Material-/Quality-/Visual-/Math-/
Transcriptmodelle, Transcriptimport, Offline-Konsolidierung, C16-Registry/Modelle,
Workflowmodelle/-graph und Auditor. Die acht Hilfepfade sind Materialien,
Quality Gate, mathematische Evaluation, Visual Inventory, C16, C18,
Konsolidierung und Audit. Jeder lief in einem frischen `python -I`-Prozess mit
explizitem Repositorypfad, bereinigter Umgebung und gesperrtem Socket/DNS.
`src.core.config` und `src.core.memory` wurden nicht initialisiert.
Der MLflow-Sanityrunner und die alten Streamlit-/Whisper-/Visualproviderpfade
wurden bewusst nicht importiert oder ausgeführt.

## Monitoring-Fixture: gefundener und korrigierter Fehler

Der erste Backendlauf ergab **655 passed, 3 skipped, 14 Setupfehler**. Ursache:
Die vorhandene `configs`-Fixture kopierte rekursiv den gesamten lokalen
`monitoring/`-Ordner. In der Hauptarbeitskopie liegen darunter ignorierte lokale
Runtimevolumes. Die Fixture konnte dadurch auch lesbare Runtimeeinträge in
private temporäre Testkopien übernehmen und scheiterte an nicht lesbaren
Unterverzeichnissen/Dateien. Diese Inhalte wurden nicht publiziert oder in den
PR übernommen; keine Originaldatei oder laufende Anwendung wurde verändert.
Der anfängliche Lauf wird nicht als erfolgreiche vollständige Regression gezählt.

Die Fixture kopiert jetzt nur von Git gelistete versionierte Konfigurationen;
auch YAML-Inhaltsprüfungen iterieren diese Liste statt lokale Runtimepfade zu
scannen. Symlinks werden abgewiesen. Neue synthetische Tests prüfen, dass
unversionierte Runtime-/Secretdateien fehlen und versionierte Symlinks nicht
verfolgt werden. Keine bestehende Assertion wurde abgeschwächt. Der fokussierte
Lauf bestand mit **31 Tests**, anschließend die vollständige obige Regression.
Das ist eine Testisolationkorrektur, kein geänderter Produktions-/Monitoringvertrag.

## Bekannter TXT-Vertrag, unverändert

`import_txt` erzeugt unbekannte Zeitstempel `None`; `TranscriptSegment.start/end`
verlangen weiterhin Zahlen. Die sechs Fehler betreffen TXT-Absätze, zwei
Encodings, exklusives Speichern, den Unknown-Time-Chunkingguard und den reinen
Importsmoke. Der ausstehende Guard kann deshalb noch nicht erreicht werden.
Die betroffenen Produktions-/Testdateien sind unverändert gegenüber der Basis.
[Historischer PR #9](../cs50/operations/historical_pr_review.md) enthält diesen
Rest; seine komplette alte Patchserie wird hier nicht zurückgemergt.
Keine künstlichen Zeitstempel, Xfails oder abgeschwächten Assertions.

## Dokument-/Konfigurationskontrollen

Alle aktuellen und archivierten versionierten Markdown-/RST-Dateiziele sowie die
neuen Auditdokumente werden auf lokale Inline-Linkziele geprüft. Externe URLs,
Ankersemantik, dynamische Beispiele und private Ziele sind davon ausdrücklich
getrennt. Archivierte Linkziele wurden auf die erhaltenen kanonischen Dateien
umgeschrieben. JSON-Syntax, Archivquell-/Zielhashes, dokumentierte Treegleichheit,
No-Overwrite und die bytegleiche unversionierte Benutzer-Roadmap wurden geprüft.
Neu generierte Auditberichte liefern keine selbstreferenziellen Goldhashes.

`python -m scripts.validate_monitoring --native` meldet Docker-Compose erfolgreich,
`promtool check`, `promtool test rules` und `amtool check-config` als `not_run`
(nicht installiert). Kein nativer PromQL-/Grafana-Laufzeitnachweis wird behauptet.
Die MLflow-Syntaxprüfung verwendet nur synthetische Platzhaltervariablen und
`--env-file /dev/null`; Buildkontext, Imagekompatibilität und Persistenz sind
nicht freigegeben. Beide Worker-Lockprüfungen bestanden offline unverändert (32 bzw. 43 Pakete);
eine neue vollständige Profilinstallation wurde nicht durchgeführt.

## Verbleibende Grenzen

Keine produktive Last-/TLS-/Proxy-/Mehrhost-/Deploymentprüfung; kein genereller
Nachweis lauffähiger Legacy-UIs oder Visual-/Whisperrunner; kein neues reales
Goldset. Private/ignorierte Bestände wurden durch den Auditor nur nach Metadaten
erfasst; fehlende Leserechte begrenzen die Zählung. Die beim ersten Testlauf
gefundenen Runtime-Kopien sind davon transparent getrennt dokumentiert.
Keine riskante Freigabelistenmaßnahme wird automatisch mit dem Dokumentations-PR
aktiviert. UI-Dateien, lokale Benutzerdateien, Datenbanken und Volumes bleiben
unverändert; der [Cleanupplan](../cleanup_plan.md) legt weitere Schritte fest.

## Datenschutz der Veröffentlichung

Die automatische Freigabeprüfung lehnte zunächst den Upload der vollständigen
Inventur mit lokalen Pfad-/Hash-/Worktree-Metadaten ab. Diese Fassung wurde nicht
übertragen. Die Detailberichte bleiben lokal mit privaten Dateirechten in einer
ignorierten Ablage. Die bereinigte PR-Fassung enthält nur Basispfade/Blob-IDs,
die unabhängig gegen den veröffentlichten GitHub-Tree des ausdrücklich
beauftragten Repositories geprüft wurden, sowie öffentliche Dokumentations- und
Testbelege. Lokale Detailmetadaten und private Commit-Ancestry werden nicht
veröffentlicht. Der frühere lokale Auditcommit bleibt erhalten; es erfolgt kein
History-Rewrite.
