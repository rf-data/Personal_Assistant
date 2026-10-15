# Complete material pipeline: final offline regression

Frozen source commit: `699be27b0b274c24f1b4197658c3cee6ef130b9c`; public master base `ad3078f`.

**570 passed, 6 failed, 5 skipped, 0 setup errors; 581 cases; 2611.17 seconds JUnit suite duration.**

New material block: 60 cases. Expected baseline comparison: no new regression; six unchanged TXT failures.

Executed in a fresh detached worktree; sources stayed unchanged throughout. Regular existing uv environment, offline/no-sync; no packages installed.

Python 3.12.12; Pydantic 2.13.4; httpx 0.28.1; BeautifulSoup 4.15.0; PyMuPDF 1.28.2; pytest 9.1.1; qdrant-client 1.19.1. Docling 2.129.0 is installed but never selected/initialized.

Command (external new scratch; configured existing worker):

```bash
CS50_TEST_PROFILE=offline uv run --offline --no-sync python -m pytest tests -q --tb=short \
  -o tmp_path_retention_policy=failed --basetemp="$SCRATCH/tests" \
  --junitxml=/tmp/materials-release-full.xml
```

ROOT/DATA_DIR/CHROMA_DIR pointed to independent temporary runtime folders; optional config values were non-secret offline placeholders. API/network guards and fake providers remained unchanged. No productive artifacts were used.

## Module counts

| Module | Passed | Failed | Setup errors | Skipped |
|---|---:|---:|---:|---:|
| test_consolidation_math_import.py | 1 | 0 | 0 | 0 |
| test_cs50_batch.py | 3 | 0 | 0 | 0 |
| test_cs50_budget.py | 12 | 0 | 0 | 0 |
| test_cs50_checkpoint.py | 37 | 0 | 0 | 0 |
| test_cs50_discovery.py | 30 | 0 | 0 | 0 |
| test_cs50_embeddings.py | 8 | 0 | 0 | 0 |
| test_cs50_evaluation.py | 7 | 0 | 0 | 0 |
| test_cs50_executor.py | 32 | 0 | 0 | 1 |
| test_cs50_extraction.py | 44 | 0 | 0 | 0 |
| test_cs50_fixture_checkout.py | 2 | 0 | 0 | 0 |
| test_cs50_full_coverage.py | 10 | 0 | 0 | 0 |
| test_cs50_index_cli.py | 4 | 0 | 0 | 0 |
| test_cs50_index_contract.py | 13 | 0 | 0 | 0 |
| test_cs50_index_end_to_end.py | 3 | 0 | 0 | 0 |
| test_cs50_ingestion.py | 9 | 0 | 0 | 0 |
| test_cs50_knowledge_index_checkpoint.py | 1 | 0 | 0 | 0 |
| test_cs50_knowledge_index_mapping.py | 5 | 0 | 0 | 0 |
| test_cs50_knowledge_input.py | 27 | 0 | 0 | 1 |
| test_cs50_knowledge_pilot.py | 19 | 0 | 0 | 1 |
| test_cs50_lecture_adapter.py | 30 | 0 | 0 | 0 |
| test_cs50_lecture_completion.py | 6 | 0 | 0 | 0 |
| test_cs50_lecture_runner.py | 9 | 0 | 0 | 0 |
| test_cs50_llm_smoke.py | 8 | 0 | 0 | 1 |
| test_cs50_material_code.py | 9 | 0 | 0 | 0 |
| test_cs50_material_contracts.py | 4 | 0 | 0 | 0 |
| test_cs50_material_download.py | 18 | 0 | 0 | 0 |
| test_cs50_material_e2e.py | 5 | 0 | 0 | 0 |
| test_cs50_material_html.py | 7 | 0 | 0 | 0 |
| test_cs50_material_inventory.py | 1 | 0 | 0 | 0 |
| test_cs50_material_mapping.py | 1 | 0 | 0 | 0 |
| test_cs50_material_pdf.py | 7 | 0 | 0 | 0 |
| test_cs50_material_processing.py | 8 | 0 | 0 | 0 |
| test_cs50_portable_input.py | 4 | 0 | 0 | 0 |
| test_cs50_precise_evidence.py | 18 | 0 | 0 | 0 |
| test_cs50_quality.py | 9 | 0 | 0 | 0 |
| test_cs50_retrieval.py | 3 | 0 | 0 | 0 |
| test_cs50_retrieval_evaluation.py | 3 | 0 | 0 | 0 |
| test_cs50_schedule.py | 5 | 0 | 0 | 0 |
| test_cs50_schedule_report.py | 2 | 0 | 0 | 0 |
| test_cs50_selection.py | 24 | 0 | 0 | 0 |
| test_cs50_six_courses.py | 9 | 0 | 0 | 0 |
| test_cs50_srt_knowledge_integration.py | 5 | 0 | 0 | 0 |
| test_cs50_timed_selection.py | 19 | 0 | 0 | 0 |
| test_cs50_uv_installed_integration.py | 0 | 0 | 0 | 1 |
| test_knowledge_source_id.py | 11 | 0 | 0 | 0 |
| test_knowledge_transcript_provenance.py | 41 | 0 | 0 | 0 |
| test_lazy_marvin_import.py | 4 | 0 | 0 | 0 |
| test_official_transcript_import.py | 33 | 6 | 0 | 0 |

## Failure IDs

- `test_official_transcript_import.py::test_txt_unknown_timestamps_paragraphs_and_unicode` (failed)
- `test_official_transcript_import.py::test_explicit_encoding[cp1252]` (failed)
- `test_official_transcript_import.py::test_explicit_encoding[utf-16]` (failed)
- `test_official_transcript_import.py::test_exclusive_save_and_no_overwrite` (failed)
- `test_official_transcript_import.py::test_knowledge_chunking_contract_without_llm_imports` (failed)
- `test_official_transcript_import.py::test_import_does_not_load_whisper_or_application_settings` (failed)

All six known TXT cases attempt unknown None timestamps against the unchanged numeric TranscriptSegment contract. No TXT assertions/models/importer were changed.

## Skips

- `test_cs50_executor.py::test_real_python0_pilot`
- `test_cs50_knowledge_input.py::test_real_local_pilot`
- `test_cs50_knowledge_pilot.py::test_offline_local_original_pilot`
- `test_cs50_llm_smoke.py::test_installed_provider_configuration_without_api`
- `test_cs50_uv_installed_integration.py::test_real_installed_srt_pipeline`

## Preparation failures and filesystem recovery

An earlier run was deliberately interrupted after final boundary corrections. A first frozen run then hit ENOSPC during ordinary atomic receipt replacement. Two independent focused repeats and a native unsandboxed repeat reproduced it; a standalone fsync/replace loop did too, despite df showing approximately 3.7 GiB free on Btrfs. The precise allocator cause was not established; this was not attributed to model/SDK errors.

Only five exact stopped scratch roots created by this task were removed (about 98 MiB synthetic test copies). Symlinks were unlinked using the safe rmtree implementation, never followed. Logs/JUnit, all worktrees/environments/caches/backups/original and productive data were retained. The standalone ten-replacement probe and all eight embedding tests then passed. Final run uses pytest’s built-in failed retention policy, removing only passed-test temporary directories after teardown. No assertions, skip rules or production atomicity were weakened, and no balance/mount/database/OS setting was changed.

Final separate focused proofs before freezing: material 60 passed/53.73s; shared executor/adapter/lazy/binding/index-CLI 98 passed + 2 originalpilot skips/269.09s. PATH-only real CLI preview/local-import/parse/resume/status and SDK guard pass without application settings/API credentials.

Material semantics, licensed live availability, real PDF/layout/formula/visual quality, native slide/archive support, and productive embeddings/uploads remain outside this offline technical proof. See the completion/support reports.
