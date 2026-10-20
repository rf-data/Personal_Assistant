# Finale Transcript-Index-Regression

Stand 15.10.2026. Basis master 4dcd3c781b089fcc3939d0a7301e60033a418700.

Vollständige Offline-Suite: **510 passed, 6 failed, 5 skipped, 0 Setupfehler**;
pytest-Gesamtlaufzeit 3141,06 s (52:21), JUnit-Suitezeit 3133,03 s.

Die neue Index-/Mappinggruppe umfasst 49 zusätzliche Tests. Keine Assertions
des bekannten TXT-Zeitstempelvertrags geändert, keine Xfails/Skips ergänzt.
Reale Qdrant-Clientinstanz; ausschließlich synthetische HTTP-/Embeddingdaten.

## Nach Testmodul

| Modul | Passed | Failed | Skipped | Setupfehler | Testzeit s |
|---|---:|---:|---:|---:|---:|
| test_consolidation_math_import | 1 | 0 | 0 | 0 | 0.79 |
| test_cs50_batch | 3 | 0 | 0 | 0 | 839.55 |
| test_cs50_budget | 12 | 0 | 0 | 0 | 1.88 |
| test_cs50_checkpoint | 37 | 0 | 0 | 0 | 44.52 |
| test_cs50_discovery | 30 | 0 | 0 | 0 | 8.39 |
| test_cs50_embeddings | 8 | 0 | 0 | 0 | 15.68 |
| test_cs50_evaluation | 7 | 0 | 0 | 0 | 36.90 |
| test_cs50_executor | 32 | 0 | 1 | 0 | 40.43 |
| test_cs50_extraction | 44 | 0 | 0 | 0 | 43.94 |
| test_cs50_fixture_checkout | 2 | 0 | 0 | 0 | 0.11 |
| test_cs50_full_coverage | 10 | 0 | 0 | 0 | 6.76 |
| test_cs50_index_cli | 4 | 0 | 0 | 0 | 58.76 |
| test_cs50_index_contract | 13 | 0 | 0 | 0 | 0.87 |
| test_cs50_index_end_to_end | 3 | 0 | 0 | 0 | 1041.65 |
| test_cs50_ingestion | 9 | 0 | 0 | 0 | 131.27 |
| test_cs50_knowledge_index_checkpoint | 1 | 0 | 0 | 0 | 23.04 |
| test_cs50_knowledge_index_mapping | 5 | 0 | 0 | 0 | 66.80 |
| test_cs50_knowledge_input | 27 | 0 | 1 | 0 | 54.17 |
| test_cs50_knowledge_pilot | 19 | 0 | 1 | 0 | 15.25 |
| test_cs50_lecture_adapter | 30 | 0 | 0 | 0 | 20.01 |
| test_cs50_lecture_completion | 6 | 0 | 0 | 0 | 65.91 |
| test_cs50_lecture_runner | 9 | 0 | 0 | 0 | 94.56 |
| test_cs50_llm_smoke | 8 | 0 | 1 | 0 | 1.77 |
| test_cs50_portable_input | 4 | 0 | 0 | 0 | 8.38 |
| test_cs50_precise_evidence | 18 | 0 | 0 | 0 | 9.87 |
| test_cs50_quality | 9 | 0 | 0 | 0 | 33.55 |
| test_cs50_retrieval | 3 | 0 | 0 | 0 | 32.90 |
| test_cs50_retrieval_evaluation | 3 | 0 | 0 | 0 | 15.55 |
| test_cs50_schedule | 5 | 0 | 0 | 0 | 229.87 |
| test_cs50_schedule_report | 2 | 0 | 0 | 0 | 96.39 |
| test_cs50_selection | 24 | 0 | 0 | 0 | 29.16 |
| test_cs50_six_courses | 9 | 0 | 0 | 0 | 28.28 |
| test_cs50_srt_knowledge_integration | 5 | 0 | 0 | 0 | 15.57 |
| test_cs50_timed_selection | 19 | 0 | 0 | 0 | 6.96 |
| test_cs50_uv_installed_integration | 0 | 0 | 1 | 0 | 0.00 |
| test_knowledge_source_id | 11 | 0 | 0 | 0 | 0.07 |
| test_knowledge_transcript_provenance | 41 | 0 | 0 | 0 | 0.20 |
| test_lazy_marvin_import | 4 | 0 | 0 | 0 | 6.52 |
| test_official_transcript_import | 33 | 6 | 0 | 0 | 0.32 |

## Verbleibende Fehler

- `test_official_transcript_import::test_txt_unknown_timestamps_paragraphs_and_unicode`
- `test_official_transcript_import::test_explicit_encoding[cp1252]`
- `test_official_transcript_import::test_explicit_encoding[utf-16]`
- `test_official_transcript_import::test_exclusive_save_and_no_overwrite`
- `test_official_transcript_import::test_knowledge_chunking_contract_without_llm_imports`
- `test_official_transcript_import::test_import_does_not_load_whisper_or_application_settings`

## Skips des bestehenden Offline-Profils

- `test_cs50_executor::test_real_python0_pilot`
- `test_cs50_knowledge_input::test_real_local_pilot`
- `test_cs50_knowledge_pilot::test_offline_local_original_pilot`
- `test_cs50_llm_smoke::test_installed_provider_configuration_without_api`
- `test_cs50_uv_installed_integration::test_real_installed_srt_pipeline`

## Reproduktion und Einordnung

Python 3.12.12 / Pydantic 2.13.4 / pytest 9.1.1 / qdrant-client 1.19.1.
Die temporäre Regression-venv nutzt ausschließlich bereits vorhandene, uv-
bereitgestellte Site-Packages über explizite .pth-Verweise; auch Python -I
findet sämtliche benötigten Abhängigkeiten. Keine Dependency-Upgrades.
Der erste PYTHONPATH-Aufbau war für isolierte CLI-Worker unvollständig
(tiktoken und pydantic_settings fehlten). Dieser Umgebungsfehler wurde
reproduziert, ohne die Produktions-CLI zu ändern. Die finale Suite nutzt
den korrigierten Aufbau. Ein frischer deklarativer Offline-Sync benötigt
weiterhin das fehlende exakte grpcio-Wheel im Lockcache.
Erster Gesamtversuch: 495 passed / 21 failed / 5 skipped, 3067,21 s;
alle 15 zusätzlichen CLI-/Import-/Pilotfehler verschwanden durch den korrigierten
Workeraufbau. Die 49 neuen Index-/Mappingtests bestehen vollständig.

[Aufbau](../../../../workers/cs50_index/README.md) und
[Abschlussbilanz](../../operations/transcript_index_completion.md).
Die JUnitdatei und vollständigen Logs bleiben außerhalb des Repositorys;
keine Maschinenpfade, produktiven Quelldateien oder Secrets versioniert.
Testzeiten einzelner Module schließen Fixtureaufbau ein; Rundungsdifferenzen
zur Gesamtlaufzeit sind möglich. Fake-Embeddings sind kein Qualitätsbenchmark.
