# CS50-Dokumentations- und Worktree-Inventur

Stand: 2026-10-14. Nur Inventur; wegen fehlender Integration von #34–#37 keine Verschiebung oder Bereinigung.

## Dokumente

Inventar: 53 unterschiedliche Pfade / 54 Inhaltsversionen, davon 45 Pfade in origin/master. Prüfung über alle lokalen Branches und origin-Refs sowie unversionierte Markdown-Dateien registrierter Worktrees. Historisch bedeutet Entwicklungsnachweis; es ist keine Aussage, dass der Inhalt gelöscht werden darf. SHA bezeichnet Git-Blob bzw. bei untracked-Dateien SHA-256.

Eine heuristische Suche nach API-Schlüsseln/Zuweisungen ergab keine Kandidaten; das ersetzt keine vollständige manuelle Geheimnisprüfung vor Veröffentlichung. 17 Inhaltsversionen enthalten absolute /home/- oder /tmp/-Beispiele. Solche historischen Inhalte müssen vor der Archivveröffentlichung geprüft werden. Keine .env-Datei wurde gelesen.

| Datei | Status / Einordnung | Inhalt | Absolute Pfade | Eingehende Markdown-Links auf master | Beispiel für Erhaltungsort |
|---|---|---|---|---|---|
| `docs/cs50/archive/2026-10/analysis.md` | master; historischer Nachweis/Plan/Übersicht | `ec38cd937ab872261522ef2290e5b6a6b99a23ce` | nein | keine | `origin/master` |
| `docs/cs50/contracts/discovery.md` | master; aktueller Vertrag/Betrieb | `865d6a058db96dd0f55b480d84f1110c281654db` | nein | keine | `origin/master` |
| `docs/cs50/contracts/discovery.md` | nur Branch/untracked; aktueller Vertrag/Betrieb | `b8eaa94aab506666c4606f3405d0b70effad0c9f` | nein | keine | `refs/heads/feat/cs50-discovery-contracts` |
| `docs/cs50/archive/2026-10/extraction_report.md` | master; historischer Nachweis/Plan/Übersicht | `613f8ba1657dc2033a9fec32c0ffe0d5f35bb966` | nein | `docs/cs50/contracts/discovery.md` | `origin/master` |
| `docs/cs50/archive/2026-10/first_llm_quality_report.md` | master; historischer Nachweis/Plan/Übersicht | `6b0ac2d47f7465580c75e801e8784c07bb07a288` | ja | keine | `origin/master` |
| `docs/cs50/archive/2026-10/full_coverage_report.md` | master; historischer Nachweis/Plan/Übersicht | `4a3ad337ef7fadba7de6749b48824bbc1658e2e3` | ja | `docs/cs50/archive/2026-10/six_course_completion_report.md` | `origin/master` |
| `docs/cs50/operations/knowledge_input_integration_report.md` | master; historischer Nachweis/Plan/Übersicht | `6a59b434590a546b115b52360946ce0a5574997b` | ja | keine | `origin/master` |
| `docs/cs50/operations/knowledge_selection_preview.md` | master; historischer Nachweis/Plan/Übersicht | `d1317dd57b7cfa5c7c7c256c8e146e60838d2d5e` | nein | `docs/cs50/archive/2026-10/timed_knowledge_selection_report.md` | `origin/master` |
| `docs/cs50/contracts/knowledge_source_id_contract.md` | master; aktueller Vertrag/Betrieb | `a612e872b04385206d70fc17f79b85a80785407c` | nein | keine | `origin/master` |
| `docs/cs50/contracts/knowledge_transcript_provenance.md` | master; aktueller Vertrag/Betrieb | `f17f97acbe887d888d536ebe07d8e19b3ec7f618` | nein | keine | `origin/master` |
| `docs/cs50/archive/2026-10/lazy_marvin_initialization.md` | master; historischer Nachweis/Plan/Übersicht | `464c245618d51d0715c3086df6007730c5f0e8c1` | nein | keine | `origin/master` |
| `docs/cs50/operations/lecture_adapter_report.md` | master; historischer Nachweis/Plan/Übersicht | `19cf2d1ed6828016c1bae2b73752945914229177` | ja | keine | `origin/master` |
| `docs/cs50/archive/2026-10/llm_pilot_runtime_report.md` | master; historischer Nachweis/Plan/Übersicht | `8f7b17b6be7d279734fad0acfdd8b9af842b1c48` | ja | keine | `origin/master` |
| `docs/cs50/archive/2026-10/llm_smoke_preparation.md` | master; historischer Nachweis/Plan/Übersicht | `88ced5fa36e1a0100c33f16409511300bafa6ac4` | ja | keine | `origin/master` |
| `docs/cs50/archive/2026-10/math_normalization_import_fix.md` | master; historischer Nachweis/Plan/Übersicht | `8d96ad5c7b94c147139046663f280cdeb6bf821d` | nein | keine | `origin/master` |
| `docs/cs50/archive/2026-10/optional_sdk_lazy_import_report.md` | master; historischer Nachweis/Plan/Übersicht | `35af824cad7ac2e94ed0706531041c5648aa3600` | nein | keine | `origin/master` |
| `docs/cs50/archive/2026-10/portable_pilot_test_report.md` | master; historischer Nachweis/Plan/Übersicht | `2a7955f45f173c2c79dbd829770db8f0f859f690` | ja | keine | `origin/master` |
| `docs/cs50/archive/2026-10/post_merge_audit.md` | master; historischer Nachweis/Plan/Übersicht | `94932aa5d3302e2862092ea46744f1be4b36bc7f` | ja | keine | `origin/master` |
| `docs/cs50/evaluation/precise_evidence_comparison_report.md` | master; historischer Nachweis/Plan/Übersicht | `cd37919fa3d2327b1caf49e1e865f1935c1aed90` | ja | keine | `origin/master` |
| `docs/cs50/archive/2026-10/quality_synthetic_boundaries_report.md` | master; historischer Nachweis/Plan/Übersicht | `4fcc6d7da5702e3666778df9a5ac1707731d45b3` | nein | keine | `origin/master` |
| `docs/cs50/contracts/selection_policy.md` | master; aktueller Vertrag/Betrieb | `f424655cad3a5eea2bf8ce811aeb0dbf04b9957d` | nein | keine | `origin/master` |
| `docs/cs50/archive/2026-10/selection_preview.md` | master; historischer Nachweis/Plan/Übersicht | `95cb6719a571e27154274442031214d5c014fc0c` | nein | keine | `origin/master` |
| `docs/cs50/archive/2026-10/six_course_completion_report.md` | master; historischer Nachweis/Plan/Übersicht | `617f0563cfa300e7e36b3d636587ad92324b5eaf` | ja | keine | `origin/master` |
| `docs/cs50/operations/six_course_fixture_provenance.md` | master; historischer Nachweis/Plan/Übersicht | `bd662f8db33d21f0f94513c5ca142a671b00ff0e` | nein | `docs/cs50/archive/2026-10/full_coverage_report.md`; `docs/cs50/archive/2026-10/six_course_completion_report.md` | `origin/master` |
| `docs/cs50/operations/six_course_overview.md` | master; historischer Nachweis/Plan/Übersicht | `d46d5b5fb2862e7a7f2e4697769181dad78089ba` | nein | `docs/cs50/archive/2026-10/full_coverage_report.md`; `docs/cs50/archive/2026-10/six_course_completion_report.md` | `origin/master` |
| `docs/cs50/operations/six_course_preview.md` | master; historischer Nachweis/Plan/Übersicht | `e27f6682ad037718b8e15c539efe74237808c2b6` | nein | `docs/cs50/archive/2026-10/six_course_completion_report.md` | `origin/master` |
| `docs/cs50/operations/six_course_video_preview.md` | master; historischer Nachweis/Plan/Übersicht | `08ea0b749ebc6935add8c9e4d53d6b63b3e499d8` | nein | `docs/cs50/archive/2026-10/six_course_completion_report.md` | `origin/master` |
| `docs/cs50/operations/srt_executor_report.md` | master; historischer Nachweis/Plan/Übersicht | `f81fc4174f394ced5ed1108db0881123c18058bf` | ja | keine | `origin/master` |
| `docs/cs50/archive/2026-10/srt_knowledge_integration_report.md` | master; historischer Nachweis/Plan/Übersicht | `2d4d8cbe25d6cba880bd1cf0433d9d58d442191b` | nein | keine | `origin/master` |
| `docs/cs50/archive/2026-10/timed_knowledge_selection_report.md` | master; historischer Nachweis/Plan/Übersicht | `475be366136af918d43e8a21bba7bc650bfaa332` | ja | keine | `origin/master` |
| `docs/cs50/contracts/timeless_transcript_architecture.md` | master; aktueller Vertrag/Betrieb | `4c585f29f1ecce060d72cc97b940b95cf33ef89c` | nein | keine | `origin/master` |
| `docs/cs50/archive/2026-10/transcript_import_report.md` | master; historischer Nachweis/Plan/Übersicht | `1f15653c91f7e4ae5b728603a5ba341ec4fc2550` | nein | keine | `origin/master` |
| `docs/cs50/archive/2026-10/transcript_knowledge_integration_plan.md` | master; historischer Nachweis/Plan/Übersicht | `4eeea43844e0b0fd1130d7538b84eba3ba67f5a6` | nein | `docs/cs50/archive/2026-10/full_coverage_report.md` | `origin/master` |
| `docs/cs50/contracts/transcript_metadata_model_contract.md` | master; aktueller Vertrag/Betrieb | `87cb85c361c779d6f3ef9b92db9674865916cef1` | nein | keine | `origin/master` |
| `docs/cs50/archive/2026-10/uv_installed_integration_report.md` | master; historischer Nachweis/Plan/Übersicht | `a11bb5d3adbc26d17a4dd7b4edd08098c5599ae4` | ja | keine | `origin/master` |
| `docs/cs50/archive/2026-10/week_fixture_fetch_report.md` | master; historischer Nachweis/Plan/Übersicht | `7dc1014f9d7fc456317f87cb4447cf77439e2886` | nein | `docs/cs50/archive/2026-10/full_coverage_report.md` | `origin/master` |
| `docs/cs50/operations/cs50_batch_execution.md` | nur Branch/untracked; aktueller Vertrag/Betrieb | `b846601e93b108ae27fe61568665e95c43f7a342` | nein | keine | `refs/heads/feat/cs50-quality-evaluation-contract` |
| `docs/cs50/contracts/cs50_budget_contract.md` | master; aktueller Vertrag/Betrieb | `d0515e0630efcb59f82de58a5d478d5cee09d4b7` | nein | keine | `origin/master` |
| `docs/cs50/operations/cs50_course_scheduler.md` | master; aktueller Vertrag/Betrieb | `744c713481015956c63bf27ea7db3b84bea294ac` | nein | keine | `origin/master` |
| `docs/cs50/contracts/cs50_knowledge_checkpoint.md` | master; aktueller Vertrag/Betrieb | `8896f9b41237ac0ba96cb27db6b1e969689b7ad3` | nein | keine | `origin/master` |
| `docs/cs50/archive/2026-10/cs50_knowledge_checkpoint_test_report.md` | master; historischer Nachweis/Plan/Übersicht | `a16cd0db73cc3eeaae27ddb293680b8545c43513` | ja | `docs/cs50/contracts/cs50_knowledge_checkpoint.md` | `origin/master` |
| `docs/cs50/operations/cs50_lecture_completion.md` | master; aktueller Vertrag/Betrieb | `fb31d4b984d6d51f603bd33d7d312196f53a1cf4` | nein | keine | `origin/master` |
| `docs/cs50/operations/cs50_lecture_runner.md` | master; aktueller Vertrag/Betrieb | `c22202acb9150b63bfcefeb6d1cb6f34a5323b63` | nein | keine | `origin/master` |
| `docs/cs50/contracts/cs50_metadata_forwarding.md` | master; aktueller Vertrag/Betrieb | `7615302dc281a10133ef72813513bfaf5687c1f5` | nein | keine | `origin/master` |
| `docs/cs50/archive/2026-10/cs50_pipeline_completion_audit.md` | nur Branch/untracked; aktueller Vertrag/Betrieb | `dc3ef2fff50d14aba2f5bfa4511071bad244a49badf5f10db8b626da47e0fac3` | ja | keine | `untracked:<workspace>/Personal_Assistant-completion-audit` |
| `docs/cs50/archive/2026-10/cs50_pipeline_completion_plan.md` | nur Branch/untracked; aktueller Vertrag/Betrieb | `b9b7b078046ed510a93449cd13b46df96e55eae236845883400f77227bd9a635` | nein | keine | `untracked:<workspace>/Personal_Assistant-completion-audit` |
| `docs/cs50/archive/2026-10/cs50_pipeline_completion_report.md` | nur Branch/untracked; historischer Nachweis/Plan/Übersicht | `ebe85ab51df3cc340e0d38ec09a7b42c1969812a` | nein | keine | `refs/heads/review/cs50-complete` |
| `docs/cs50/operations/cs50_pipeline_test_matrix.md` | nur Branch/untracked; historischer Nachweis/Plan/Übersicht | `b2836e3eb87f9fd76d45d04bc334a64e29ad51af` | ja | keine | `refs/heads/review/cs50-complete` |
| `docs/cs50/contracts/cs50_portable_inputs.md` | master; aktueller Vertrag/Betrieb | `df0f3691a4d7fa0828d70793a12bc9b93825b722` | nein | keine | `origin/master` |
| `docs/cs50/evaluation/cs50_quality_evaluation.md` | nur Branch/untracked; aktueller Vertrag/Betrieb | `fd0ad8441d004822122b2fe90136df77f5932124` | nein | keine | `refs/heads/feat/cs50-quality-evaluation-contract` |
| `docs/cs50/operations/cs50_schedule_reporting.md` | nur Branch/untracked; historischer Nachweis/Plan/Übersicht | `51fe85a013340b4296be5dd35a1ba9769d10da14` | nein | keine | `refs/heads/feat/cs50-course-reporting` |
| `docs/cs50/archive/2026-10/github_integration_status_2026-10-14.md` | master; historischer Nachweis/Plan/Übersicht | `232c179d7144fb74fbfc496dfdee4597f2892603` | ja | keine | `origin/master` |
| `src/prio_list.md` | nur Branch/untracked; historischer Nachweis/Plan/Übersicht | `9c23c0db8b3d5c78828a79850a7cbb965ca3e14d0f63834701b2701791254422` | nein | keine | `untracked:<workspace>/gmp_compliance` |
| `workers/cs50/README.md` | master; aktueller Vertrag/Betrieb | `cb57126fd46bf21a1dfbaa6458f73780e5da7ea4` | nein | keine | `origin/master` |

Das ältere discovery.md auf feat/cs50-discovery-contracts ist eine abweichende Inhaltsversion, kein zusätzliches Dokument. Die zwei untracked Abschlussberichte sind jeweils byteidentisch in gmp_compliance und Personal_Assistant-completion-audit vorhanden; beide Kopien bleiben erhalten. src/prio_list.md ist ein unversionierter Auftrag und wird nicht automatisch archiviert.

## Zielstruktur nach erfolgreicher Integrationsprüfung

- `docs/cs50/README.md`: Architektur, verlinkte CLI-Handbücher, Offline-Tests, Ausführungsfreigaben, Grenzen und offene Qualitätsaufgaben.
- `docs/cs50/contracts/`: Discovery/Selection/Identitäten/Metadaten, Checkpoint-/Budget-/Portable-Input-Verträge.
- `docs/cs50/operations/`: Executor, Lecture-Runner, Scheduler, Batch, Reporting und Evaluation.
- `docs/cs50/archive/`: historische Analysen, Entwicklungsberichte, Testnachweise und ersetzte Pläne mit Datum/Commit-Kontext.
- HTML, Manifest und versionierte Quellen-/Task-JSONs verbleiben unter `docs/course_sources/cs50/`; keine lokalen Execution-/Transcript-Dateien aufnehmen.

Noch keine endgültige Verschiebeliste: zuerst #34 integrieren und den resultierenden master erneut prüfen. Danach pro Datei git mv, relative Links einschließlich Quellen-JSON/HTML-Bezüge aktualisieren, Referenzen auch in Code/Tests prüfen. Keine Duplikate durch Kopieren erzeugen. Historische Dateiinhalte und Git-Blob-IDs erhalten; redaktionelle Korrekturen getrennt nachvollziehbar machen.

## Worktrees vor jeder Bereinigung

Alle vorhandenen Pfade wurden über ihren gemeinsamen Git-Ordner dem Repository zugeordnet. Clean umfasst hier nur versionierte/untracked Dateien; ignorierte Dateien werden separat ausgewiesen. „Enthalten“ bedeutet Commit-Ancestry, nicht bloß ähnliche Änderungen nach Squash/API-Veröffentlichung.

| Pfad | Branch | Clean/Dirty | In master enthalten? | Ungesicherte Dateien / außerhalb master liegende Commits | Empfehlung |
|---|---|---|---|---|---|
| `<workspace>/gmp_compliance` | `master` | dirty | ja | untracked: docs/cs50/archive/2026-10/cs50_pipeline_completion_audit.md, docs/cs50/archive/2026-10/cs50_pipeline_completion_plan.md, src/prio_list.md; 181 ignorierte Einträge; inkl. .venv/.env/data/persönlicher Dateien; 0 Commits außerhalb master | erhalten: Integrationsblocker; unversionierte Dateien |
| `<workspace>/Personal_Assistant-audit` | `detached` | clean | nein | 25 ignorierte Einträge; Caches/.venv; 1 Commits außerhalb master | erhalten: Integrationsblocker; Commits erhalten |
| `<workspace>/Personal_Assistant-audit-check` | `detached` | clean | nein | 17 ignorierte Einträge; Caches; 1 Commits außerhalb master | erhalten: Integrationsblocker; Commits erhalten |
| `<workspace>/Personal_Assistant-checkpoints` | `feat/cs50-knowledge-checkpoints` | clean | nein | 25 ignorierte Einträge; Caches; 1 Commits außerhalb master | erhalten: Integrationsblocker; Commits erhalten |
| `<workspace>/Personal_Assistant-completion` | `review/cs50-complete` | clean | nein | 26 ignorierte Einträge; Caches/.venv; 4 Commits außerhalb master | erhalten: Integrationsblocker; Commits erhalten |
| `<workspace>/Personal_Assistant-completion-audit` | `docs/cs50-completion-audit` | dirty | ja | untracked: docs/cs50/archive/2026-10/cs50_pipeline_completion_audit.md, docs/cs50/archive/2026-10/cs50_pipeline_completion_plan.md; 20 ignorierte Einträge; Caches; 0 Commits außerhalb master | erhalten: Integrationsblocker; unversionierte Dateien |
| `<workspace>/Personal_Assistant-final-audit` | `docs/cs50-final-archive` | clean | ja | 12 ignorierte Einträge; Caches; 0 Commits außerhalb master | erhalten: Integrationsblocker |
| `<workspace>/Personal_Assistant-lazy-sdk` | `fix/optional-knowledge-sdk-imports` | clean | nein | 24 ignorierte Einträge; Caches; 1 Commits außerhalb master | erhalten: Integrationsblocker; Commits erhalten |
| `<workspace>/Personal_Assistant-pilot-regression` | `test/portable-cs50-pilot-regression` | clean | ja | 23 ignorierte Einträge; Caches; 0 Commits außerhalb master | erhalten: Integrationsblocker |
| `<workspace>/Personal_Assistant-pilot-tests` | `test/portable-cs50-pilot` | clean | ja | 0 Commits außerhalb master | erhalten: Integrationsblocker; später potenziell sicher entbehrlich (clean, keine ignorierten Dateien) |
| `<workspace>/Personal_Assistant-provenance-models` | `fix/knowledge-transcript-metadata-contract` | clean | nein | 24 ignorierte Einträge; Caches; 1 Commits außerhalb master | erhalten: Integrationsblocker; Commits erhalten |
| `<workspace>/Personal_Assistant-quality-fix` | `fix/cs50-quality-synthetic-boundaries` | clean | nein | 23 ignorierte Einträge; Caches; 1 Commits außerhalb master | erhalten: Integrationsblocker; Commits erhalten |
| `/tmp/Personal_Assistant-lazy-baseline` | `detached` | nicht vorhanden; prunable | ja | 0 Commits außerhalb master | Metadaten erhalten; keine automatische prune-Operation |
| `/tmp/cs50-discovery-pr` | `feat/cs50-discovery-contracts` | nicht vorhanden; prunable | nein | 1 Commits außerhalb master | Metadaten erhalten; keine automatische prune-Operation |
| `/tmp/cs50-extraction-pr` | `feat/cs50-offline-extraction` | nicht vorhanden; prunable | nein | 2 Commits außerhalb master | Metadaten erhalten; keine automatische prune-Operation |
| `/tmp/cs50-full-coverage-pr2` | `feat/cs50-full-coverage` | nicht vorhanden; prunable | nein | 4 Commits außerhalb master | Metadaten erhalten; keine automatische prune-Operation |
| `/tmp/cs50-integration-audit-20261014/feature` | `detached` | nicht vorhanden; prunable | nein | 9 Commits außerhalb master | Metadaten erhalten; keine automatische prune-Operation |
| `/tmp/cs50-integration-audit-20261014/master-clean` | `detached` | nicht vorhanden; prunable | ja | 0 Commits außerhalb master | Metadaten erhalten; keine automatische prune-Operation |
| `/tmp/cs50-lecture-adapter-pr3` | `detached` | nicht vorhanden; prunable | nein | 5 Commits außerhalb master | Metadaten erhalten; keine automatische prune-Operation |
| `/tmp/cs50-selection-pr` | `feat/cs50-selection-preview` | nicht vorhanden; prunable | nein | 3 Commits außerhalb master | Metadaten erhalten; keine automatische prune-Operation |
| `/tmp/cs50-timed-knowledge-pr2` | `feat/cs50-timed-knowledge` | nicht vorhanden; prunable | nein | 4 Commits außerhalb master | Metadaten erhalten; keine automatische prune-Operation |
| `/tmp/knowledge-provenance-pr` | `feat/knowledge-transcript-provenance` | nicht vorhanden; prunable | nein | 2 Commits außerhalb master | Metadaten erhalten; keine automatische prune-Operation |
| `/tmp/knowledge-source-id-pr` | `fix/knowledge-source-id` | nicht vorhanden; prunable | nein | 1 Commits außerhalb master | Metadaten erhalten; keine automatische prune-Operation |
| `/tmp/lazy-marvin-pr` | `fix/lazy-marvin-import` | nicht vorhanden; prunable | nein | 3 Commits außerhalb master | Metadaten erhalten; keine automatische prune-Operation |
| `/tmp/math-import-pr` | `fix/math-normalization-import` | nicht vorhanden; prunable | nein | 1 Commits außerhalb master | Metadaten erhalten; keine automatische prune-Operation |
| `/tmp/official-transcript-pr` | `feat/official-transcript-import` | nicht vorhanden; prunable | nein | 1 Commits außerhalb master | Metadaten erhalten; keine automatische prune-Operation |

Keine Worktrees oder Branches entfernt; auch prunable Einträge bleiben registriert. Detached Commits ohne master-Ancestry müssen vor späterer Metadatenbereinigung durch explizite dauerhafte Git-Refs gesichert werden. Lokale Branches mit äquivalentem Inhalt, aber abweichenden Commit-IDs werden nicht als integriert gelöscht.

## Weitere Dateien: ausschließlich Dry-Run

Potenzielle spätere Kandidaten: von Tests erzeugte `.pytest_cache`, `.ruff_cache` und `__pycache__` in zusätzlichen Worktrees, nach konkreter Herkunftsprüfung. Keine Löschbefehle ausgeführt. Virtuelle Umgebungen bleiben bis zur Prüfung ihrer Reproduzierbarkeit erhalten.

Ausdrücklich ausgeschlossen: `data/`, Originaltranskripte, Execution-Belege, `.env*`, Datenbanken, unbekannte Caches, Cookies, persönliche Dateien und unversionierte Berichte. Die Hauptarbeitskopie ist 20 Commits hinter origin/master und enthält die genannten untracked Dateien; kein automatischer Checkout/Reset/Pull.

## Lokale Branches

Zusätzliche Commits sind ancestry-basiert gezählt. Eine andere API-/Squash-Commit-ID kann bereits veröffentlichten Inhalt besitzen; deshalb bedeutet die Zahl nicht automatisch unveröffentlichten Inhalt. Eine fehlende origin-Ref beweist ebenfalls keinen Datenverlust. Keine Branchlöschung vorgenommen.

| Branch | Head | Commits außerhalb master | Exakter Head in origin-Historie? |
|---|---|---|---|
| `add_audio_transcript` | `b3b59b66942e4470475cc41657f4caf515338c67` | 0 | `origin/add_audio_transcript`; `origin/add_knowledge_db`; `origin/add_local_LLM`; `origin/add_organizer`; `origin/codespace-opulent-barnacle-x5p7wpgwp6w6f57w`; `origin/feat/cs50-bounded-llm-pilot`; `origin/feat/cs50-course-reporting`; `origin/feat/cs50-course-scheduler`; `origin/feat/cs50-discovery-contracts`; `origin/feat/cs50-durable-budget`; `origin/feat/cs50-full-coverage`; `origin/feat/cs50-knowledge-input-binding`; `origin/feat/cs50-lecture-adapter`; `origin/feat/cs50-lecture-completion`; `origin/feat/cs50-lecture-runner`; `origin/feat/cs50-offline-extraction`; `origin/feat/cs50-portable-inputs`; `origin/feat/cs50-quality-evaluation-contract`; `origin/feat/cs50-selection-preview`; `origin/feat/cs50-six-course-batch`; `origin/feat/cs50-srt-executor`; `origin/feat/cs50-timed-knowledge`; `origin/feat/knowledge-transcript-provenance`; `origin/feat/official-transcript-import`; `origin/fix/knowledge-metadata-forwarding`; `origin/fix/knowledge-source-id`; `origin/fix/lazy-marvin-import`; `origin/fix/math-normalization-import`; `origin/improve_wiki_extract`; `origin/master`; `origin/offline_add`; `origin/test/cs50-completion-integration`; `origin/test/cs50-worker-profiles` |
| `audit/post-merge-fixtures` | `90ce44f39d55ecb158206af078170eb21bb48ccd` | 2 | nein; äquivalenter Inhalt separat prüfen |
| `docs/cs50-completion-audit` | `571874524b8b976b68f78668a4274896629229ec` | 0 | `origin/feat/cs50-course-reporting`; `origin/feat/cs50-course-scheduler`; `origin/feat/cs50-durable-budget`; `origin/feat/cs50-lecture-completion`; `origin/feat/cs50-lecture-runner`; `origin/feat/cs50-portable-inputs`; `origin/feat/cs50-quality-evaluation-contract`; `origin/feat/cs50-six-course-batch`; `origin/fix/knowledge-metadata-forwarding`; `origin/master`; `origin/test/cs50-completion-integration`; `origin/test/cs50-worker-profiles` |
| `docs/cs50-final-archive` | `1ae6a4471681085222ba4ec589665fbdd15073f2` | 0 | `origin/master` |
| `feat/cs50-course-reporting` | `70cbf4df5faa1d27081a46e896daf0a1eabb048f` | 8 | nein; äquivalenter Inhalt separat prüfen |
| `feat/cs50-course-scheduler` | `3c21a02d1f3cad4e73b30006b213212112a2620d` | 7 | nein; äquivalenter Inhalt separat prüfen |
| `feat/cs50-discovery-contracts` | `8ed80f3b2dff4768af11789684e0cb921c64cdc3` | 1 | nein; äquivalenter Inhalt separat prüfen |
| `feat/cs50-durable-budget` | `c1facec470decb677565c670fd73d009ec2ff549` | 1 | nein; äquivalenter Inhalt separat prüfen |
| `feat/cs50-full-coverage` | `e2bb1f2fc939e686cbee618d12c2f6b3f410e479` | 4 | nein; äquivalenter Inhalt separat prüfen |
| `feat/cs50-knowledge-checkpoints` | `809988be888a1305a2787524d6c96e2498a40f07` | 1 | nein; äquivalenter Inhalt separat prüfen |
| `feat/cs50-lecture-completion` | `654a3a1ef57f7e6847b47f9c2f3c6595bc08b5f6` | 6 | nein; äquivalenter Inhalt separat prüfen |
| `feat/cs50-lecture-runner` | `838c4c0b2812cced8449512681777ec9aab43bbe` | 5 | nein; äquivalenter Inhalt separat prüfen |
| `feat/cs50-offline-extraction` | `40d441e11c1610660ae2e0017de0e313f76b9247` | 2 | nein; äquivalenter Inhalt separat prüfen |
| `feat/cs50-portable-inputs` | `b1696a37d7df22045b3d5aef2bfc31b4df333ffd` | 2 | nein; äquivalenter Inhalt separat prüfen |
| `feat/cs50-quality-evaluation-contract` | `e22171583f147e02281e61a782b54a2e041f6930` | 10 | nein; äquivalenter Inhalt separat prüfen |
| `feat/cs50-selection-preview` | `fa3dcd4c9d0da9b68b6271120c520def320a5305` | 3 | nein; äquivalenter Inhalt separat prüfen |
| `feat/cs50-six-course-batch` | `33d11e6bdff359212739e240813d04a14fd183f0` | 9 | nein; äquivalenter Inhalt separat prüfen |
| `feat/cs50-timed-knowledge` | `e2bb1f2fc939e686cbee618d12c2f6b3f410e479` | 4 | nein; äquivalenter Inhalt separat prüfen |
| `feat/knowledge-transcript-provenance` | `b1933e6ad8f6dd4c6fc53852ee23c62d40a10ee2` | 2 | nein; äquivalenter Inhalt separat prüfen |
| `feat/official-transcript-import` | `1ba121fdada0e3016e3c1c0475ddb86210b0e377` | 1 | nein; äquivalenter Inhalt separat prüfen |
| `fix/cs50-quality-synthetic-boundaries` | `b4d4ca4e3aa22d0c4dc0833bbfe166b7ef929249` | 1 | nein; äquivalenter Inhalt separat prüfen |
| `fix/knowledge-metadata-forwarding` | `a6d34208859f34382c696d9fd58fa7c96368a65a` | 3 | nein; äquivalenter Inhalt separat prüfen |
| `fix/knowledge-source-id` | `e46c3f0430d2d42831a3acda3db29975ab44d909` | 1 | nein; äquivalenter Inhalt separat prüfen |
| `fix/knowledge-transcript-metadata-contract` | `dde15bf4434c4adb5e92755508d38428b9b090b8` | 1 | nein; äquivalenter Inhalt separat prüfen |
| `fix/lazy-marvin-import` | `ee309bc9ddf8c3c5334b8e06dcf5098dc468cd00` | 3 | nein; äquivalenter Inhalt separat prüfen |
| `fix/math-normalization-import` | `65ba14fda025384ab9debe8aeb4784038c71ce87` | 1 | nein; äquivalenter Inhalt separat prüfen |
| `fix/optional-knowledge-sdk-imports` | `4315896cfc63716e3e46f1ed5b6eae66b148eba8` | 1 | nein; äquivalenter Inhalt separat prüfen |
| `master` | `f0056beba3c238ed8068223ad4561db320d4e0dc` | 0 | `origin/feat/cs50-course-reporting`; `origin/feat/cs50-course-scheduler`; `origin/feat/cs50-durable-budget`; `origin/feat/cs50-lecture-completion`; `origin/feat/cs50-lecture-runner`; `origin/feat/cs50-portable-inputs`; `origin/feat/cs50-quality-evaluation-contract`; `origin/feat/cs50-six-course-batch`; `origin/fix/knowledge-metadata-forwarding`; `origin/master`; `origin/test/cs50-completion-integration`; `origin/test/cs50-worker-profiles` |
| `offline_add` | `c5454badf0cdea6876f20aabf87f8f8e817c7dd0` | 0 | `origin/feat/cs50-bounded-llm-pilot`; `origin/feat/cs50-course-reporting`; `origin/feat/cs50-course-scheduler`; `origin/feat/cs50-discovery-contracts`; `origin/feat/cs50-durable-budget`; `origin/feat/cs50-full-coverage`; `origin/feat/cs50-knowledge-input-binding`; `origin/feat/cs50-lecture-adapter`; `origin/feat/cs50-lecture-completion`; `origin/feat/cs50-lecture-runner`; `origin/feat/cs50-offline-extraction`; `origin/feat/cs50-portable-inputs`; `origin/feat/cs50-quality-evaluation-contract`; `origin/feat/cs50-selection-preview`; `origin/feat/cs50-six-course-batch`; `origin/feat/cs50-srt-executor`; `origin/feat/cs50-timed-knowledge`; `origin/feat/knowledge-transcript-provenance`; `origin/feat/official-transcript-import`; `origin/fix/knowledge-metadata-forwarding`; `origin/fix/knowledge-source-id`; `origin/fix/lazy-marvin-import`; `origin/fix/math-normalization-import`; `origin/master`; `origin/offline_add`; `origin/test/cs50-completion-integration`; `origin/test/cs50-worker-profiles` |
| `recover-offline-add` | `978472d6528f37c3672ad1aa18aad0e2ca925d99` | 0 | `origin/add_audio_transcript`; `origin/add_knowledge_db`; `origin/add_local_LLM`; `origin/add_organizer`; `origin/add_runpod`; `origin/codespace-opulent-barnacle-x5p7wpgwp6w6f57w`; `origin/feat/cs50-bounded-llm-pilot`; `origin/feat/cs50-course-reporting`; `origin/feat/cs50-course-scheduler`; `origin/feat/cs50-discovery-contracts`; `origin/feat/cs50-durable-budget`; `origin/feat/cs50-full-coverage`; `origin/feat/cs50-knowledge-input-binding`; `origin/feat/cs50-lecture-adapter`; `origin/feat/cs50-lecture-completion`; `origin/feat/cs50-lecture-runner`; `origin/feat/cs50-offline-extraction`; `origin/feat/cs50-portable-inputs`; `origin/feat/cs50-quality-evaluation-contract`; `origin/feat/cs50-selection-preview`; `origin/feat/cs50-six-course-batch`; `origin/feat/cs50-srt-executor`; `origin/feat/cs50-timed-knowledge`; `origin/feat/knowledge-transcript-provenance`; `origin/feat/official-transcript-import`; `origin/fix/knowledge-metadata-forwarding`; `origin/fix/knowledge-source-id`; `origin/fix/lazy-marvin-import`; `origin/fix/math-normalization-import`; `origin/improve_wiki_extract`; `origin/master`; `origin/offline_add`; `origin/recover-offline-add`; `origin/test/cs50-completion-integration`; `origin/test/cs50-worker-profiles` |
| `review/cs50-complete` | `a6b49d9eed1d6a56c1f9bc81cafb7953ccfafa42` | 4 | `origin/feat/cs50-course-reporting`; `origin/test/cs50-completion-integration` |
| `test/cs50-completion-integration` | `0bc649c75aa112ac75086b49614f30390df51987` | 11 | nein; äquivalenter Inhalt separat prüfen |
| `test/cs50-worker-profiles` | `4dd8cfcaa1b15c154b8902741794cb58045dd0af` | 4 | nein; äquivalenter Inhalt separat prüfen |
| `test/portable-cs50-pilot` | `f0056beba3c238ed8068223ad4561db320d4e0dc` | 0 | `origin/feat/cs50-course-reporting`; `origin/feat/cs50-course-scheduler`; `origin/feat/cs50-durable-budget`; `origin/feat/cs50-lecture-completion`; `origin/feat/cs50-lecture-runner`; `origin/feat/cs50-portable-inputs`; `origin/feat/cs50-quality-evaluation-contract`; `origin/feat/cs50-six-course-batch`; `origin/fix/knowledge-metadata-forwarding`; `origin/master`; `origin/test/cs50-completion-integration`; `origin/test/cs50-worker-profiles` |
| `test/portable-cs50-pilot-regression` | `13d435751b7bf37702c754eae07065665e0270d0` | 0 | `origin/feat/cs50-course-reporting`; `origin/feat/cs50-course-scheduler`; `origin/feat/cs50-durable-budget`; `origin/feat/cs50-lecture-completion`; `origin/feat/cs50-lecture-runner`; `origin/feat/cs50-portable-inputs`; `origin/feat/cs50-quality-evaluation-contract`; `origin/feat/cs50-six-course-batch`; `origin/fix/knowledge-metadata-forwarding`; `origin/master`; `origin/test/cs50-completion-integration`; `origin/test/cs50-worker-profiles` |
