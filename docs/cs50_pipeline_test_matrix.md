# CS50-Abschluss: tatsächliche Offline-Testmatrix

Basis de4ac38 + dokumentierter PR-Stack #27–#36 + finale Integrationschecks.
Reguläre bestehende uv-Workerumgebung: Python 3.12.12, pytest 9.1.1, Pydantic 2.13.4.
Keine Paket-/SDK-Upgrades, bezahlten API-Aufrufe oder realen Kursmaterial-Downloads.

| Stufe | Ausgeführter Testlauf | Ergebnis / Dauer |
|---|---|---|
| A02 Budget + A01 Regression | test_cs50_budget + test_cs50_checkpoint | 45 passed / 43,30 s (erste 8 Budgetfälle). |
| A02 Fake-HTTP Fehler | erweiterte Budgettests | 11 passed / 1,53 s. |
| A03 Inputportabilität + Legacy | portable_input + knowledge_input | 31 passed, 1 bestehender Originalpilot-Skip / 64,10 s. |
| A04 Metadata/IDs/Lazy | provenance + source_id + lazy_marvin_import | 56 passed / 6,57 s; beide alten Weitergabefehler behoben. |
| A05 SDK-freies Profil | llm_smoke + lazy_marvin_import | 12 passed, 1 expliziter SDK-Skip / 15,44 s. |
| A05 installiertes Profil | explizit CS50_TEST_PROFILE=sdk, configuration test | 1 nachvollziehbarer Fehler / 0,45 s: openai/pydantic_ai fehlen; kein API. |
| B01 komplette Lecture / Resume | lecture_runner (8 Fälle) | 8 passed / 65,91 s; echtes Chunking >2 Chunks, Fake-HTTP, Caps/unknown/Paths/CLI. |
| B02 Completion + Runner | lecture_completion + lecture_runner | 14 passed / 142,48 s; teilweise/irrelevant/kaputt/fremd/Marker-Crash. |
| B03 zehn Python-Lectures | schedule (4 Fälle) | 4 passed / 186,58 s; next-pending, invalid source, unknown, Lock/Status. |
| B03 unknown/Usage | schedule unknown + runner failures | 3 passed / 36,14 s. |
| B03 HTTP-Timeoutstatus | zusätzlicher Schedule-Timeoutfall | 1 passed / 23,56 s. |
| B04 gewichtete Reports | schedule_report (2 Fälle) | 2 passed / 84,36 s; ungleiche Sizes und validierte Teilfortschritte. |
| B05 alle 50 / 100 | batch (2 Fälle) | 2 passed / 476,30 s; echte Kernfunktionen, Fake-HTTP/Provider, kompletter Resume. |
| B05 isolierte Kurs-CLI | zusätzliche echte Subprozess-/v2-CLI-Regressionsprüfung | 1 passed / 79,90 s; zehn Lectures offline plus Audit-Resume, null Requests. |
| C01 Reviewvertrag | evaluation (7 Fälle) | 7 passed / 31,71 s; Quellen-/Cue-/Provenienzprüfung ohne erfundene Urteile. |
| Finale Boundary Guards | budget + invalid precise sidecar | 13 passed / 4,74 s; Usageüberschreitung blockiert, unvalidierte Rawfelder separat. |

Die vollständige Suite auf dem finalen Implementierungsstand: **461 passed, 6 failed, 0 errors, 5 skipped**, 472 Fälle, **1437,83 s (23:57)**.

Alle neuen CS50-Module sind grün. Verbleibend sind genau die sechs unveränderten TXT-None/float-Vertragsfehler. Die zwei alten Metadatenweitergabefehler sind behoben. Der SDK-Smoke ist gemäß explizitem Offlineprofil separat optional; bei ausdrücklich aktiviertem SDK-Profil bleibt dessen fehlende Installation ein Fehler.

| Testmodul | bestanden | Fehler | Skips |
|---|---:|---:|---:|
| test_consolidation_math_import | 1 | 0 | 0 |
| test_cs50_batch | 3 | 0 | 0 |
| test_cs50_budget | 12 | 0 | 0 |
| test_cs50_checkpoint | 37 | 0 | 0 |
| test_cs50_discovery | 30 | 0 | 0 |
| test_cs50_evaluation | 7 | 0 | 0 |
| test_cs50_executor | 32 | 0 | 1 |
| test_cs50_extraction | 44 | 0 | 0 |
| test_cs50_fixture_checkout | 2 | 0 | 0 |
| test_cs50_full_coverage | 10 | 0 | 0 |
| test_cs50_knowledge_input | 27 | 0 | 1 |
| test_cs50_knowledge_pilot | 19 | 0 | 1 |
| test_cs50_lecture_adapter | 30 | 0 | 0 |
| test_cs50_lecture_completion | 6 | 0 | 0 |
| test_cs50_lecture_runner | 9 | 0 | 0 |
| test_cs50_llm_smoke | 8 | 0 | 1 |
| test_cs50_portable_input | 4 | 0 | 0 |
| test_cs50_precise_evidence | 18 | 0 | 0 |
| test_cs50_quality | 9 | 0 | 0 |
| test_cs50_schedule | 5 | 0 | 0 |
| test_cs50_schedule_report | 2 | 0 | 0 |
| test_cs50_selection | 24 | 0 | 0 |
| test_cs50_six_courses | 9 | 0 | 0 |
| test_cs50_srt_knowledge_integration | 5 | 0 | 0 |
| test_cs50_timed_selection | 19 | 0 | 0 |
| test_cs50_uv_installed_integration | 0 | 0 | 1 |
| test_knowledge_source_id | 11 | 0 | 0 |
| test_knowledge_transcript_provenance | 41 | 0 | 0 |
| test_lazy_marvin_import | 4 | 0 | 0 |
| test_official_transcript_import | 33 | 6 | 0 |

## Reproduzierbarer vollständiger Aufruf

```bash
# Bestehende Worker-.venv als WORKER_VENV explizit angeben.
UV_PROJECT_ENVIRONMENT="$WORKER_VENV" UV_CACHE_DIR=/tmp/cs50-uv-cache \
  CS50_TEST_PROFILE=offline uv run --offline --no-sync python -m pytest tests -q \
  --tb=short --junitxml=/tmp/cs50-completion-final.xml
```

Ruff wird auf den neuen/gezielt geänderten CS50-Modulen, CLIs, Fixtures und Tests
geprüft; kein Repo-weites Legacy-Lint-Refactoring. git diff --check und vorhandene
pre-commit-Hooks zusätzlich. uv lock --offline --check --project workers/cs50
prüft den eingefrorenen 32-Paket-Lockgraphen. Fresh sync scheitert am fehlenden
lokalen ruff-Wheel; kein Download/Upgrade wurde zugelassen und keine frische
vollständige Umgebung behauptet.

Die sechs bekannten TXT-Fälle liegen außerhalb des SRT-Pfads. Optionaler Original-
SRT-/Knowledge-/CLI-Pilot und Marvin-Integration behalten ihre separaten Tests.
Neue technische Tests benötigen weder diese lokalen Daten noch API-Keys. Eine
reale lokale Python-0-Quelle wurde zusätzlich ausschließlich read-only geprüft,
8/157 Reviewfenster extern temporär erzeugt, zero Claims/Reviews. Keine Original-
Transkripte/Execution-Belege oder maschinenlokalen Datenpfade im Git aufgenommen.
