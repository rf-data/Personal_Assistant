# C24-R finale technische Validierung – 2026-10-26

Technischer Branch-Nachweis; keine Produktionsfreigabe. Gesamtstatus HOLD bis
HTTP-Nachtest, reproduzierter Installation, GitHub-Backup und Zielintegration.
Dieser Bericht ergänzt die historischen C24-R-Berichte; er ersetzt deren
Nachweisgrenzen nicht rückwirkend.

## Worktree und Erhaltung

Branch `feat/c24r-retrieval_completion`, HEAD/Basis
`4c057ae33d41ba98e227879cc8a51283338e4a0b`. Anfangs 50 geänderte/neue Dateien,
kein vorhandener staged Diff. Alle initialen Dateien inventarisiert und gehasht;
initialer getrackter Diff sowie Dependencydateien gesondert gesichert.
Außer den ausdrücklich geprüften Dependencykorrekturen bleiben diese Dateien
byteidentisch. Sechs finale Abnahme-/Inventar-/Exportdateien ergänzt.
Vollständige Liste: [c24r_final_file_inventory.md](c24r_final_file_inventory.md).

Ignored: `.venv/`, `.ruff_cache/` und `__pycache__/` bleiben lokale Artefakte.
Keine Modelle, realen Originale, privaten Laufkonfigurationen oder Testdatabases
in den Lieferumfang aufgenommen. Freier Platz anfangs rund 6,6 GiB.
Keine anderen Worktrees bearbeitet, keine Projektdateien zurückgesetzt/gelöscht.

Das ursprüngliche `/tmp/c24r-delivery/artifacts.sha256` ist vollständig gültig.
Das ergänzende Lock-Paket stimmt für Patch, Prüfprotokoll, Testlogs, vorherigen
Test, aktuelle Fixture und Lockbericht; die darin aufgeführten Dependencyhashes
weichen wegen der hier dokumentierten gezielten Korrektur ab. Die gesicherten
`*.before` stimmen mit diesen historischen Hashes überein.

## Testprofil und aktuelle Ergebnisse

Vorhandene `.venv`, Python 3.12.12, SQLite 3.50.4, pytest 9.1.1,
Pydantic 2.13.4, httpx 0.28.1, Ruff 0.16.3, PyMuPDF 1.28.2.
Umgebung und Installation: [Dependency Review](c24r_dependency_review.md).

| Lauf | Passed | Failed | Error | Skip | Deselected | Blocked* |
|---|---:|---:|---:|---:|---:|---:|
| C1 – vier Fokusdateien | 72 | 2 | 43 | 0 | 0 | 45 |
| C2 – ergänzende Regression | 667 | 0 | 0 | 17 | 1 | 0 |

*Blocked ist die begründete Teilmenge von Failed/Error, keine zusätzliche
Fallzahl. Die zwei Läufe enthalten keine gemeinsamen Testdateien; historische
Entwicklungsläufe und externe Betreiberergebnisse werden nicht dazugezählt.

C1: 181,36 Sekunden, Exitcode 1. Dateiaufteilung:

| Datei | Passed | Failed | Error | Ursache |
|---|---:|---:|---:|---|
| test_c24r_integration.py | 4 | 1 | 0 | echter Loopback: socket EPERM |
| test_content_search_http.py | 49 | 1 | 0 | echter HTTP-/Prozessrestart: socket EPERM |
| test_content_http.py | 0 | 0 | 43 | HTTPServer-Fixture: socket EPERM |
| test_content_index_jobs.py | 19 | 0 | 0 | alle bestanden |

Alle 45 Tracebacks anhand JUnit geprüft: `PermissionError: [Errno 1]
Operation not permitted` beim Socketaufbau. Keine Socketgrenze umgangen,
keiner dieser Fälle als bestanden/skip ausgewiesen. Kein fachlicher Fehler in
den ausführbaren C1-Fällen. Es gibt ausdrücklich keinen grünen C1-Gesamtlauf.

C2: **667 passed, 0 failed, 0 errors, 17 skipped, 1 deselected**,
626,84 Sekunden, Exitcode 0. Die 17 optionalen SymPyfälle sind mangels SymPy
übersprungen; der Realinventarfall wurde bewusst abgewählt. Keine Blocker in C2.
C16-/Workflow-Snapshots, Executor und native PDF-Prozesslebenszyklen bestehen.

| C2-Datei | Passed | Failed | Error | Skip |
|---|---:|---:|---:|---:|
| test_content_store_models | 25 | 0 | 0 | 0 |
| test_content_store_store | 34 | 0 | 0 | 0 |
| test_content_store_adapters | 49 | 0 | 0 | 0 |
| test_content_store_concurrency | 4 | 0 | 0 | 0 |
| test_content_read_contracts | 14 | 0 | 0 | 0 |
| test_content_index_projection | 41 | 0 | 0 | 0 |
| test_content_fts | 47 | 0 | 0 | 0 |
| test_content_vectors | 33 | 0 | 0 | 0 |
| test_content_retrieval_evaluation | 60 | 0 | 0 | 0 |
| test_content_retrieval_integration | 6 | 0 | 0 | 0 |
| test_evaluation_store | 45 | 0 | 0 | 0 |
| test_review_fts_pilot | 8 | 0 | 0 | 0 |
| test_gold_candidates | 30 | 0 | 0 | 0 |
| test_job_control | 36 | 0 | 0 | 0 |
| test_job_executor | 17 | 0 | 0 | 0 |
| test_cs50_workflows | 24 | 0 | 0 | 0 |
| test_workflow_http | 37 | 0 | 0 | 0 |
| test_pdf_job_control | 14 | 0 | 0 | 0 |
| test_cs50_material_evaluation | 37 | 0 | 0 | 0 |
| test_math_formula_evaluation | 106 | 0 | 0 | 17 |

Die vier bestandenen Integrationsfälle umfassen die reale Handlerkette über
Byte-Streams, Cancel vor Dispatch, Cancel während Indexbuild und die
deterministische Thread-/Lockprobe. Der Fixture-Fix wartet auf das Event nach
`HTTPServer.process_request()` einschließlich Request-Cleanup. `fcntl.LOCK_NB`,
ACLs, Quarantäne und Produktionscode wurden in diesem Abschlusslauf nicht geändert.
Keine künstlichen Wartezeiten oder Retryschleifen zur Lockberuhigung ergänzt.
Details: [Lockbericht](c24r_content_lock_fix.md).

## Exakte Wiederholung

Im Repository mit passend provisionierter Venv. Alle Befehle nutzen
`PYTHONDONTWRITEBYTECODE=1`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`,
`CS50_TEST_PROFILE=offline` und einen neuen beschreibbaren uv-Cache:

```bash
export PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export CS50_TEST_PROFILE=offline
export UV_CACHE_DIR=$(mktemp -d /tmp/c24r-uv-cache.XXXXXX)
uv run --offline --no-sync python -m pytest -q -o addopts= -p no:cacheprovider \
  tests/test_c24r_integration.py tests/test_content_search_http.py \
  tests/test_content_http.py tests/test_content_index_jobs.py

uv run --offline --no-sync python -m pytest -q -o addopts= -p no:cacheprovider \
  tests/test_content_store_models.py tests/test_content_store_store.py \
  tests/test_content_store_adapters.py tests/test_content_store_concurrency.py \
  tests/test_content_read_contracts.py tests/test_content_index_projection.py \
  tests/test_content_fts.py tests/test_content_vectors.py \
  tests/test_content_retrieval_evaluation.py tests/test_content_retrieval_integration.py \
  tests/test_evaluation_store.py tests/test_review_fts_pilot.py \
  tests/test_gold_candidates.py tests/test_job_control.py tests/test_job_executor.py \
  tests/test_cs50_workflows.py tests/test_workflow_http.py tests/test_pdf_job_control.py \
  tests/test_cs50_material_evaluation.py tests/test_math_formula_evaluation.py \
  -k 'not test_versioned_inventory_has_no_confirmed_real_gold'
```

Der eine Realinventarfall wird vor jedem Zugriff abgewählt, damit keine
historischen Originalwurzeln geöffnet werden. Ergänzende Testdateien entsprechen
der dokumentierten C24-R-Auswahl plus Store-Concurrency und C23-/Formelevaluation.
Die gesamte Repository-/SDK-/Produktionssuite ist NOT APPLICABLE für diese
begrenzte Offlineabnahme und wurde nicht ausgeführt; kein Repo-Gesamtpass behauptet.

## Statische und Vertragsprüfungen

- PASS: Ruff check und format --check auf allen 23 geänderten/neuen Pythondateien.
- PASS: `git diff --check`; vollständige Patch-/Indexprüfung im isolierten Lieferbaum.
- PASS: neun JSONschema-Snapshots exakt gegen Pydanticmodelle (Search/Index/Pool).
- PASS: unabhängiger JSON-Schema-Draft-2020-12-Check (System-jsonschema): neun
  Schemas sowie beide synthetischen Beispiele und leerer Pool valide. Beide
  API-Beispiele zusätzlich über echte DTOs validiert; JSON parsebar.
- PASS: Kandidaten-CLI: 0 pending Kandidaten, reale Abnahme ausdrücklich blockiert.
- PASS: Testcollection der ausgewählten Suite ohne fehlende Imports/Collectionerrors.
- PASS: C16-/Workflow-Snapshotregression innerhalb C2 bestanden.
- PASS: alle neun JSON-/CSV-Lieferdateien explizit enthalten und nicht ignoriert;
  61 lokale Markdown-Linkziele vorhanden.
- PASS: Secret-Scan; neun Entropietreffer manuell als synthetische Generationen,
  Fingerprints und SHA-256-Felder in zwei Beispiel-JSONs geprüft. Keine Credentials.
- Historische absolute Benutzerpfade finden sich in übernommenen API-/Architektur-
  Laufberichten und im Lockbericht. Als reine Nachweisherkunft geprüft und bewusst
  erhalten, nicht als portable Voraussetzung verwendet. Neue Operatorbefehle nutzen
  `$HOME`/relative Pfade; keine privaten Materialpfade oder Tokens ergänzt.

Der erste ad-hoc Schema-Checker importierte einen falschen Modulnamen; korrigiert.
Der erste Metadatenchecker verglich die Reihenfolge gleichwertiger Specifiertexte;
auf normalisierte Specifier umgestellt. Finale statische Prüfungen bestehen;
diese Hilfsskriptfehler waren keine Projekt-Collectionfehler.

## Git, Sicherung und Integration

Gemeinsamer Git-Speicher liegt außerhalb der beschreibbaren Roots im
Hauptrepository. Kein Staging/Commit/Fetch/Push dorthin versucht und keine
Berechtigungsumgehung. Originalindex unverändert/leer; damit sind dessen
`git diff --cached --stat` und `--check` leer/erfolgreich, kein Stagingnachweis.
Der vollständige Commit-1-/Commit-2-Diff wird stattdessen im isolierten
Testrepository explizit gestagt, geprüft und als Patch geliefert.

Finales Paket: `/tmp/c24r-final-validation-20261026/`, einschließlich
`c24r-final-completion.patch`, `c24r-final-dependencies.patch`,
`c24r-final-full.patch`, `files.sha256`, `artifacts.sha256`,
`commit1-files.txt`, `commit2-files.txt`, Testlogs/JUnit und Prüfscripten.
Vorwärts-/Rückwärtsanwendung, alle finalen Dateihashes und Wiederherstellung
sämtlicher Baseline-Zieldateien werden in `patch-verification.txt` ausgewiesen.
Diese Sicherung ist lokal; kein dauerhafter GitHub-Backupnachweis.
Keine neuen echten Branch-Commit-SHAs; HEAD bleibt die Basis. Technische
Hilfscommits im isolierten Prüfbaum sind keine Repositoryliefercommits.

GitHub-Abfrage des Zielbackupbranches ergab 404; kein Backup nachgewiesen.
Shellnetz scheitert an DNS. Kein Connector-Push als Umgehung des Git-Fallbacks.
[Integrationsmatrix](c24r_master_integration_matrix.md): Remote-master read-only
verifiziert, Search-/Index-Duplikate erkannt; nur gezielte neue Test-/Goldvorbereitung
zur späteren Übernahme empfohlen. Keine Zielmaster-Testausführung behauptet.

## Abnahmegrenze

Extern mitgeteilte **44 passed / 1 failed** beziehen sich auf den Stand vor dem
Fixture-Fix; das ist ein externer Hinweis ohne hier vorliegenden Rohlog und kein
Post-Fix-Erfolg. `test_actual_loopback_job_to_search` muss außerhalb der Sandbox
mit dem jetzigen Fixture bestehen, zusätzlich Search-Restart und Content-HTTP.

Loviscach: 0 reale Kandidaten, 0 bestätigte Goldstandards. Vorbereitung PASS;
Materialrechte, Originalbelege, Reviewer und fachliche Pilotabnahme HOLD.
C26-Produktionsfreigabe bleibt HOLD. Konkrete Betreiberbefehle und Einzelstatus:
[c24r_operator_acceptance.md](c24r_operator_acceptance.md).
