# A01: Offline-Testbericht

14. Oktober 2026; Basis `origin/master` 571874524b8b976b68f78668a4274896629229ec,
nach Fetch und Prüfung der gemergten PRs #24/#25. Implementierung in einem
isolierten Worktree auf `feat/cs50-knowledge-checkpoints`.

## Umgebung und Reproduktion

Die bestehende reguläre uv-Worker-.venv wurde ausdrücklich verwendet:
Python 3.12.12, pytest 9.1.1, Pydantic 2.13.4. Kein Sync, SDK-Installieren,
Dependency-Upgrade, HTTP-Download oder kostenpflichtiger Aufruf.

```bash
# WORKER_VENV auf eine bereits installierte reguläre Worker-.venv setzen.
UV_PROJECT_ENVIRONMENT="$WORKER_VENV" UV_CACHE_DIR=/tmp/cs50-uv-cache \
  uv run --offline --no-sync python -m pytest \
  tests/test_cs50_checkpoint.py tests/test_cs50_knowledge_pilot.py \
  tests/test_cs50_precise_evidence.py tests/test_cs50_quality.py -q --tb=short

UV_PROJECT_ENVIRONMENT="$WORKER_VENV" UV_CACHE_DIR=/tmp/cs50-uv-cache \
  uv run --offline --no-sync python -m pytest tests -q --tb=short \
  --junitxml=/tmp/a01-full-final.xml
```

Eine vollständige Neuinstallation aus dem Lockfile wurde nicht durchgeführt.
Die bereits bekannten Worker-Rebuild-/SDK-Profilfragen bleiben getrennt.
Testdaten entstehen ausschließlich unter pytest/tmp_path. Für die neuen
Integrationstests: synthetisches SRT mit zwei Text-Cues und einem leeren Cue,
echter CS50Executor mit Fake-HTTP, import_srt, Inputbinder, KnowledgeSettings,
echtes Chunking, bestehende Evidence-Validierung und deterministische
Consolidation. Keine Stubs der geprüften Kernfunktionen. Fake-LLM-Antworten
sind technische Samples, kein fachliches Gold-Set.

## Nachgewiesene Checkpointeigenschaften

| Eigenschaft | Konkreter Nachweis in test_cs50_checkpoint.py |
|---|---|
| Erstellung / JSON-Roundtrip | test_success_roundtrip_and_reuse; Job-/Chunkmodell, Hashes, Reservoir und reguläres ChunkKnowledgeResult. |
| Wiederaufnahme ohne Request | test_worker_fake_provider_resume, jeweils chunk/segment_v1: zwei Workerruns, nur ein Fake-HTTP-Aufruf, gleiche Extraction, reguläre Consolidation und Ergebnisherkunft LLM. |
| Offline-CLI / Subprozess | test_offline_cli_checkpoint_resume: zwei echte isolierte CLI-Worker, null Requests, synthetische Herkunft bleibt erhalten. |
| Abbruch vor Publikation | test_crash_before_done[False]: vorbereiteter Receipt, fehlendes Artefakt wird abgewiesen; kein done und kein neuer Request. |
| Abbruch nach Publikation | test_crash_before_done[True]: vollständige Artefakte vor Marker; Hash-/Modellprüfung schließt prepared ohne Request ab. |
| Abrupter Prozessabbruch | test_abrupt_process_exit_preserves_reservation: os._exit im isolierten Prozess nach dauerhafter Reservierung; nächster Prozess erkennt unknown und konservativ verbrauchte Reservierung. |
| Korruption | test_corruption_conflicts_preserve_files: kaputtes Receipt-JSON, falscher Hash, kaputtes Artefakt-JSON trotz angepasstem Hash, ungültiges Ergebnismodell, fehlende Datei; bestehende Bytes werden nicht repariert/ersetzt. |
| Fremde Identität | test_identity_conflict: Raw-/Transcript-Hash, Promptversion/-Hash, Evidence-Modus/-Version, source_id/lecture_id, Provider/Modell, Chunkplan/Settings, offline/llm. |
| Gleiche Chunk-ID, anderer Inhalt | test_same_chunk_id_changed_content sowie Chunkplan-/Konfigurationsfälle. |
| Unknown / Fehler / keine Retries | test_unknown_never_retries und test_fake_dispatch_failure_no_retry; Fake-Timeout verursacht genau einen Request über zwei Starts. |
| Vor-Dispatch-Persistenz | Fake-HTTP prüft in_flight auf Platte; test_no_dispatch_if_durable_reservation_fails verhindert Transport bei Schreibfehler. test_llm_completion_requires_reservation verhindert LLM-Completion ohne dauerhaften Beleg. |
| Konkurrenz | test_concurrent_lock_and_exclusive_publication und test_concurrent_process_lock: zweiter Lock/Prozess wird abgewiesen; bestehendes Artefakt bleibt unverändert. |
| Pfade / unreceipted Daten | test_unreceipted_files_and_symlinks, test_cli_checkpoint_output_separation und test_worker_checkpoint_inside_source_rejected. |
| Bestehende Evidence-Verträge | Unveränderte test_cs50_precise_evidence: Cue-Teilmengen, ungültige/leere/duplizierte/fremde Referenzen, Originalzeiten, unterschiedliche Statements, Formeln, Whisper/Legacy. |

Der erfolgreiche Resume bindet das normalisierte Ergebnis erneut über den echten
CS50-Inputbinder an die Originalsegmente. Source-/Course-/Lecture-/Media-Metadaten
werden weiterhin regulär über bestehende Dokumentmodelle gespeichert. resource_id,
section_key und Input-/Provenienzdigests bleiben zusätzlich im Checkpointvertrag.
Ein kaputtes oder fremdes Artefakt wird auch bei einem behaupteten done abgelehnt.

## Tatsächlich ausgeführte Ergebnisse

| Lauf | Ergebnis | Laufzeit |
|---|---|---|
| Checkpoint + Pilot + precise Evidence + Quality (Zwischenstand mit 34 neuen Fällen) | 80 passed, 1 skipped | 109,96 s |
| Erweiterter Checkpointlauf einschließlich abruptem Prozessabbruch / Reservierungspflicht (36 Fälle) | 36 passed | 43,24 s |
| Abschließende vollständige Offline-Suite (424 Fälle) | **411 passed, 9 failed, 0 errors, 4 skipped** | **354,47 s** |

Im abschließenden Lauf bestehen **alle 37 Checkpointfälle**, alle 19 aktiven
Pilotfälle, 18 precise-Evidence- und neun Quality-Fälle. Ebenfalls erfolgreich:
Discovery, Selection, Adapter, Fake-Executor, Inputbinding, SRT-Integration,
Source-ID-Vertrag, echter Math-Modulimport und alle vier Lazy-Import-Fälle.

Die Baseline aus dem Abschlussaudit hatte 374 passed / 9 failed / 4 skipped.
Jetzt kommen exakt 37 bestandene neue Checkpointfälle hinzu; dieselben neun
bekannten Fehler bleiben. Vollständiges JUnit: `/tmp/a01-full-final.xml`;
Log: `/tmp/a01-full-final.log` (temporäre Diagnoseartefakte, nicht versioniert).

Ruff-Lint und Formatprüfung der vier betroffenen Python-Dateien sowie
`git diff --check` bestanden. Es gibt keine neuen Skip-/Xfail-Markierungen.

## Getrennte bekannte Fehler

- **Sechs TXT-Fälle** in test_official_transcript_import: unbekannte None-Zeiten
  aus import_txt treffen auf verpflichtende float-Zeiten im Segmentmodell.
  Betroffen: test_txt_unknown_timestamps_paragraphs_and_unicode,
  test_explicit_encoding[cp1252], test_explicit_encoding[utf-16],
  test_exclusive_save_and_no_overwrite,
  test_knowledge_chunking_contract_without_llm_imports und
  test_import_does_not_load_whisper_or_application_settings. Nicht geändert.
- **Zwei Metadatenweitergabe-Fälle** in test_knowledge_transcript_provenance:
  test_real_extraction_and_deterministic_and_semantic_contracts und
  test_semantic_no_statements_branch_preserves_explicit_assignment_and_media.
  Allgemeiner Extraction-Runner / semantischer Leerzweig; bestehender CS50-
  Direktpfad mit deterministischer Consolidation ist erfolgreich. Nicht geändert.
- **Ein optionaler SDK-Smoke-Fall**:
  test_installed_provider_configuration_without_api in test_cs50_llm_smoke;
  das OpenAI-SDK ist nicht installiert. Nicht als Produktionsfehler des
  SDK-freien HTTP-Providers umgedeutet oder still übersprungen.

Die vier bestehenden Skips betreffen drei optionale lokale Originalpilot-Tests
und die installierte-Marvin-Integration. Originalpilot-Testverträge unverändert;
für A01 werden ausschließlich portable synthetische Daten verwendet.

## Verbleibende Grenzen / A02

Kein Nachweis realer Providerabrechnung, kein neues Marvin-/SQLite-Setup und
keine Kurs-/Lecture-Batchfähigkeit. RequestBudget bleibt pro Prozess und maximal
zwei Chunks. Dauerhafte Reservierung und terminales unknown verhindern automatische
Doppelrequests; ein globaler Budget-Scheduler und eine ausdrückliche manuelle
Unknown-Auflösung folgen separat. Checkpoint-done bezeichnet das ausgewählte
Fenster. Aggregate und Quality werden bei Resume im neuen Output neu erzeugt,
nicht aus ungeprüften alten Rundateien adoptiert.
