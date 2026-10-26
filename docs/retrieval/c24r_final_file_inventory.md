# C24-R finales Dateiinventar – 2026-10-26

56 geänderte/neue Dateien gegenüber `4c057ae33d41ba98e227879cc8a51283338e4a0b`. Commit 1: 54 Completiondateien; Commit 2: zwei Dependencydateien.

Die 50 anfänglichen Dateien sind vollständig enthalten. Alle außer den zwei
autorisierten Dependencykorrekturen sind gegenüber dem Anfangssnapshot byteidentisch.
Sechs finale Abnahme-/Inventar-/Exportdateien kommen hinzu. `.venv`, Caches,
Testlogs, private Originale und Patcharchive werden nicht committet.

Masterbezug: Remote `a8af1d9372eb435d3e1331c33b047d21120d57c2`, Methode und
Ausnahmen siehe [Integrationsmatrix](c24r_master_integration_matrix.md).
„Abweichend“ bedeutet vorhandene weiterentwickelte Datei; kein Übernahmeauftrag.

| Datei | Git-Diff | Commit | master |
|---|---|---|---|
| `.gitignore` | M | 1 | abweichend |
| `docs/api/content_index_jobs_v1.md` | A | 1 | identisch |
| `docs/api/content_index_jobs_validation.md` | A | 1 | identisch |
| `docs/api/content_search_v1.md` | A | 1 | identisch |
| `docs/api/content_search_validation.md` | A | 1 | abweichend |
| `docs/api/examples/content_index_jobs_v1.schema.json` | A | 1 | abweichend |
| `docs/api/examples/content_index_jobs_v1.synthetic.json` | A | 1 | identisch |
| `docs/api/examples/content_search_v1.schema.json` | A | 1 | abweichend |
| `docs/api/examples/content_search_v1.synthetic.json` | A | 1 | identisch |
| `docs/architecture/content_fts_implementation.md` | M | 1 | identisch |
| `docs/evaluation/loviscach/candidate_schema.v1.json` | A | 1 | fehlt |
| `docs/evaluation/loviscach/candidates.v1.json` | A | 1 | fehlt |
| `docs/evaluation/loviscach/review.v1.csv` | A | 1 | fehlt |
| `docs/evaluation/loviscach_gold_candidate_inventory.md` | A | 1 | fehlt |
| `docs/evaluation/loviscach_gold_candidate_methodology.md` | A | 1 | fehlt |
| `docs/evaluation/loviscach_gold_candidate_review.md` | A | 1 | fehlt |
| `docs/job_control/contract.v1.json` | M | 1 | abweichend |
| `docs/retrieval/c24r_acceptance_requirements.txt` | A | 1 | fehlt |
| `docs/retrieval/c24r_completion_report.md` | A | 1 | fehlt |
| `docs/retrieval/c24r_content_lock_fix.md` | A | 1 | fehlt |
| `docs/retrieval/c24r_controlled_index_jobs.md` | A | 1 | fehlt |
| `docs/retrieval/c24r_dependency_review.md` | A | 1 | fehlt |
| `docs/retrieval/c24r_final_file_inventory.md` | A | 1 | fehlt |
| `docs/retrieval/c24r_final_validation.md` | A | 1 | fehlt |
| `docs/retrieval/c24r_integration_inventory.md` | A | 1 | fehlt |
| `docs/retrieval/c24r_integration_validation.md` | A | 1 | fehlt |
| `docs/retrieval/c24r_master_integration_matrix.md` | A | 1 | fehlt |
| `docs/retrieval/c24r_operator_acceptance.md` | A | 1 | fehlt |
| `docs/retrieval/c24r_remaining_work.md` | A | 1 | fehlt |
| `docs/retrieval/c24r_search_http.md` | A | 1 | fehlt |
| `docs/workflows/contract.v1.json` | M | 1 | abweichend |
| `pyproject.toml` | M | 2 | abweichend |
| `scripts/job_control.py` | M | 1 | identisch |
| `src/content_store/search_http.py` | A | 1 | identisch |
| `src/content_store/search_models.py` | A | 1 | abweichend |
| `src/job_control/adapter_worker.py` | M | 1 | abweichend |
| `src/job_control/catalog.py` | M | 1 | abweichend |
| `src/job_control/controller.py` | M | 1 | abweichend |
| `src/job_control/executor.py` | M | 1 | abweichend |
| `src/job_control/http.py` | M | 1 | abweichend |
| `src/job_control/index_http.py` | A | 1 | identisch |
| `src/job_control/index_jobs.py` | A | 1 | abweichend |
| `src/job_control/index_models.py` | A | 1 | abweichend |
| `src/job_control/models.py` | M | 1 | abweichend |
| `src/job_control/registry.py` | M | 1 | abweichend |
| `src/model_evaluation/gold_candidates.py` | A | 1 | fehlt |
| `src/tools_evaluation/gold_candidates.py` | A | 1 | fehlt |
| `src/tools_rag/content_index.py` | M | 1 | abweichend |
| `tests/index_cancel_probe.py` | A | 1 | fehlt |
| `tests/index_job_probe.py` | A | 1 | identisch |
| `tests/index_job_support.py` | A | 1 | identisch |
| `tests/test_c24r_integration.py` | A | 1 | fehlt |
| `tests/test_content_index_jobs.py` | A | 1 | identisch |
| `tests/test_content_search_http.py` | A | 1 | identisch |
| `tests/test_gold_candidates.py` | A | 1 | fehlt |
| `uv.lock` | M | 2 | abweichend |
