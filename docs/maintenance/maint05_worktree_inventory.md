# MAINT-05: Worktree-Inventar

Lesender Snapshot: 2026-10-25T21:01:16.327734+00:00. **84 registrierte Worktrees, alle HOLD.**
Kein Worktree wurde entfernt, kein bestehender Branch verändert. Die Snapshotdaten sind
eine Bestandsaufnahme, keine dauerhafte Zusicherung. Aktuelle MAINT-05-Dateien waren
zur Aufnahme noch in Bearbeitung. Die vollständigen strukturierten Felder stehen in
[maint05_inventory_snapshot.json](maint05_inventory_snapshot.json).

## Erhebung und Nachweisgrenzen

`git --no-optional-locks`, deaktivierter fsmonitor/untrackedCache; NUL-Worktree- und
Statusformate, `status --untracked-files=all --ignored=matching`, zusätzliche
`ls-files`-Abfragen einschließlich ignored und leerer Zusatzverzeichnisse. Kein Fetch,
Push, Indexrefresh, Worktree-Lock oder anderes schreibendes Gitkommando auf realen Repos.
Privatpfade werden nach der vorhandenen `repository_audit.safe_name`-Regel redigiert;
Anzahl und Status bleiben erhalten. Keine privaten Dateiinhalte gelesen. Die Erhebung
enthält alle von Git registrierten Worktrees, einschließlich der acht Detached-HEADs.
Nicht registrierte beliebige Ordner außerhalb dieser Liste sind damit nicht inventarisiert.

Alle beobachteten `origin`-URLs: `https://github.com/rf-data/Personal_Assistant.git`.
Autoritatives `git ls-remote --heads` scheiterte mit Exit 128:
`Could not resolve host: github.com`. Deshalb ist der Remote-Branch-HEAD in jeder Zeile
**unknown**, die Existenz über diesen Transport **unverified**. Fehlende Trackingrefs
werden nicht als fehlende GitHub-Branches interpretiert. Lokale Tracking-SHAs und ihre
Zähler können veraltet sein. Frische Einzelabfragen sind vor jeder späteren Handlung nötig.

Positive GitHub-Belege stammen getrennt aus einer Suche nach offenen PRs und den
danach einzeln abgefragten PR-Köpfen: [PR-Snapshot](maint05_pr_snapshot.json). Zehn
offene Draft-PRs sind belegt. Ihre zugeordneten neun Worktrees bleiben geschützt;
#148 hat keinen identisch zugeordneten Worktree, #158 ist über denselben Commit dem
anders benannten Reviewbranch zugeordnet. Die Zuordnung ist keine Gleichsetzung
der Branches. Keine fehlende Suchtrefferzeile wird als sicher fehlender PR gewertet.
C23-01/#75 ist separat als historisch gemergt belegt; auch das ersetzt keinen Backupref.

Prozess-CWD-Erkennung ist nur positive Evidenz. Keine gefundenen PIDs beweisen keine
Inaktivität. Verlässliche Codex-Sitzungs-/Writer-Freigabe ist für keinen realen Worktree
vorhanden. Stashes, Datenbanken, Venvs und andere lokale Daten bleiben unangetastet.

## Verteilung

| Klasse | Anzahl |
| --- | ---: |
| `PROTECTED_ACTIVE` | 15 |
| `UNTRACKED_OR_IGNORED_RISK` | 30 |
| `REMOTE_UNVERIFIED` | 84 |
| `PR_OR_MERGE_UNVERIFIED` | 84 |
| `DIRTY` | 18 |
| `DETACHED_HEAD` | 8 |
| `CANDIDATE_FOR_ARCHIVE` | 0 |
| `ARCHIVE_VERIFIED` | 0 |

Klassen überschneiden sich. Bei 30 Worktrees bestehen Zusatzdateirisiken, 18 enthalten
versionierte Änderungen. Zwei riskante Indexeinträge bestehen in `c26-integration`.
Die 15 ausdrücklich geschützten Worktrees und darüber hinaus sämtliche dirty,
untracked/ignored, detached oder unverified Worktrees müssen unberührt bleiben.

## Ausdrücklich geschützte Aufgaben

| Worktree | Schutzgrund |
| --- | --- |
| `Personal_Assistant` | primary checkout; explicit/current-task protection |
| `Personal_Assistant-c21q` | explicit/current-task protection; [#72](https://github.com/rf-data/Personal_Assistant/pull/72) (gleicher Branch) |
| `Personal_Assistant-c2405b` | explicit/current-task protection; [#88](https://github.com/rf-data/Personal_Assistant/pull/88) (gleicher Branch) |
| `Personal_Assistant-c2405c` | explicit/current-task protection; [#89](https://github.com/rf-data/Personal_Assistant/pull/89) (gleicher Branch) |
| `Personal_Assistant-c24r` | explicit/current-task protection |
| `Personal_Assistant-c26-operations-preflight` | explicit/current-task protection; [#160](https://github.com/rf-data/Personal_Assistant/pull/160) (gleicher Branch) |
| `Personal_Assistant-c26-runtime-bootstrap` | explicit/current-task protection; [#157](https://github.com/rf-data/Personal_Assistant/pull/157) (gleicher Branch) |
| `Personal_Assistant-c26d` | explicit/current-task protection; [#161](https://github.com/rf-data/Personal_Assistant/pull/161) (gleicher Branch) |
| `Personal_Assistant-c26e` | explicit/current-task protection; [#162](https://github.com/rf-data/Personal_Assistant/pull/162) (gleicher Branch) |
| `Personal_Assistant-c26f` | explicit/current-task protection; [#163](https://github.com/rf-data/Personal_Assistant/pull/163) (gleicher Branch) |
| `Personal_Assistant-c26g` | explicit/current-task protection |
| `Personal_Assistant-c26h` | explicit/current-task protection |
| `Personal_Assistant-c27-review` | explicit/current-task protection; [#158](https://github.com/rf-data/Personal_Assistant/pull/158) (gleicher Commit; anderer Branch) |
| `Personal_Assistant-cs50-real01` | explicit/current-task protection |
| `Personal_Assistant-maint05` | explicit/current-task protection; process cwd in worktree |

Die fest geschützten Namen sind Hauptworktree, c26h, c24r, c26g, cs50-real01 und
maint05. Weitere aktive/unabgeschlossene Entwicklungsstände werden durch die
konkreten Datenrisiken unten blockiert, beispielsweise c26-compat/gate/integration,
c26b6/c26b7, maint03/maint04b und completion-audit. Eine historische MAINT-01/02/03-
Bereinigungsfreigabe wird nicht angenommen. Für alle 84 gilt derzeit HOLD.

## Einzelbefunde

`T/U/I` zählt geänderte versionierte Statuseinträge / untracked Statuseinträge /
ignored Verzeichniseinträge; ignored Verzeichnisse werden nicht rekursiv in private
Datenspeicher expandiert. Zusatzpfade aus `ls-files` stehen separat. Zähler `a/b`
sind lokale ahead/behind-Zähler gegenüber dem genannten Trackingref, niemals Live-GitHub.

### 01 · Personal_Assistant

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant`
- Branch: `refs/heads/feat/c20b-workflow-http`
- HEAD / lokaler Branch: `65b3f09155263d447c4f4540f5b3bba9f78017c1` / `65b3f09155263d447c4f4540f5b3bba9f78017c1`
- Betreff: `C20-B: expose authorized C18 workflow inspection, execute and resume over HTTP`
- Status vollständig: `True`; T/U/I: `0/0/153`.
- Upstream: `refs/remotes/origin/feat/c20b-workflow-http`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c20b-workflow-http`.
- Lokaler Tracking-SHA: `65b3f09155263d447c4f4540f5b3bba9f78017c1`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c20b-workflow-http`, SHA `65b3f09155263d447c4f4540f5b3bba9f78017c1`.
- Backupref: `refs/heads/feat/c20b-workflow-http`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `PROTECTED_ACTIVE`, `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: primary checkout; explicit/current-task protection; unsecured untracked/ignored paths (including empty directories); authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `_DELETE_2026-07-29_streamlit_demo.log` |
| `!!` | `__init__.py` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `_prototypes/_dev_code_review/` |
| `!!` | `_prototypes/_dev_to_add/` |
| `!!` | `_prototypes/excel_helper.py` |
| `!!` | `_prototypes/matlab_helper.py` |
| `!!` | `_prototypes/notes_helper.py` |
| `!!` | `_prototypes/optimise_helper.py` |
| `!!` | `configuration/_dev_/` |
| `!!` | `configuration/cfg_lecture_transcribe.json` |
| `!!` | `configuration/context_audio_record.json` |
| `!!` | `configuration/context_know_extract.json` |
| `!!` | `configuration/context_lecture_compile.json` |
| `!!` | `configuration/context_local_file_transcribe.json` |
| `!!` | `configuration/context_webinar_transcribe.json` |
| `!!` | `configuration/context_yt_transcribe.json` |
| `!!` | `configuration/input_lecture_compile.json` |
| `!!` | `[private path omitted]` |
| `!!` | `docling_test/01_Ueberblick_Vektorrechnung_p1_2_no_enrich.md` |
| `!!` | `docling_test_formula/01_Ueberblick_Vektorrechnung.md` |
| `!!` | `docs/_dev_health_check.txt` |
| `!!` | `docs/_dev_new_content.txt` |
| `!!` | `[private path omitted]` |
| `!!` | `docs/_dev_tmux.txt` |
| `!!` | `docs/_local_audit_c170/` |
| `!!` | `docs/course_sources/cs50/cs50_python_week0_knowledge_input.v1.json` |
| `!!` | `docs/course_sources/cs50/examples/official_transcript.normalized.json` |
| `!!` | `docs/course_sources/cs50/llm_smoke_offline_result.json` |
| `!!` | `docs/course_sources/cs50/uv_installed_integration_result.json` |
| `!!` | `docs/course_sources/source.json` |
| `!!` | `docs/cs50-material-inventory.v1.json` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `docs/python0-material-plan.v1.json` |
| `!!` | `docs/reviewed-one-material.v1.json` |
| `!!` | `frontend/__init__.py` |
| `!!` | `frontend/_src/__init__.py` |
| `!!` | `frontend/_src/screenshots/ContainerTools.png` |
| `!!` | `frontend/_src/screenshots/Infra_complete.png` |
| `!!` | `frontend/_src/screenshots/Interface.png` |
| `!!` | `frontend/_src/screenshots/airflow.png` |
| `!!` | `frontend/_src/screenshots/details_processing.png` |
| `!!` | `frontend/_src/screenshots/details_training.png` |
| `!!` | `frontend/_src/screenshots/etl_metric.png` |
| `!!` | `frontend/_src/screenshots/etl_trigger.png` |
| `!!` | `frontend/_src/screenshots/fastapi.png` |
| `!!` | `frontend/_src/screenshots/graph_processing.png` |
| `!!` | `frontend/_src/screenshots/graph_training.png` |
| `!!` | `frontend/_src/screenshots/infra_complete_flowchart.png` |
| `!!` | `frontend/_src/screenshots/microservice.png` |
| `!!` | `frontend/_src/screenshots/mlflow.png` |
| `!!` | `frontend/_src/screenshots/mlflow1.png` |
| `!!` | `frontend/_src/screenshots/mlflow2.png` |
| `!!` | `frontend/_src/screenshots/monitoring.png` |
| `!!` | `frontend/_src/screenshots/orchestration.png` |
| `!!` | `frontend/_src/screenshots/recommend.png` |
| `!!` | `frontend/_src/screenshots/training.png` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `frontend/pages/__init__.py` |
| `!!` | `liora/ml_engineer_0/` |
| `!!` | `liora/ml_engineer_1/` |
| `!!` | `liora/ml_engineer_2/` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `[private path omitted]` |
| `!!` | `monitoring/portainer/` |
| `!!` | `[private path omitted]` |
| `!!` | `src/__init__.py` |
| `!!` | `src/_dev_filter_html_elements.py` |
| `!!` | `src/_dev_test_script.py` |
| `!!` | `src/mathe_vorkurs_2013_urls.json` |
| `!!` | `src/test.py` |
| `!!` | `src/tools_knowledge/_dev_rebuild_knowledge.py` |
| `!!` | `src/tools_organizer/_dev_quickstart.py` |
| `!!` | `src/tools_parsing/__init__.py` |
| `!!` | `src/tools_transcribe/_dev_extract_audio.py` |
| `!!` | `src/tools_transcribe/_dev_transcriber.py` |
| `!!` | `src/tools_transcribe/_dev_write_transcript.py` |
| `!!` | `src/utils/_dev_other_modules.md` |
| `!!` | `tmux-client-14876.log` |
| `!!` | `tmux-client-15209.log` |
| `!!` | `tmux-client-15520.log` |
| `!!` | `tmux-server-14878.log` |
| `!!` | `tmux-server-15522.log` |

Zusatzpfade (17): `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `docling_test/`, `docling_test_formula/`, `docs/course_sources/mit/`, `frontend/_src/`, `[private path omitted]`, `liora/`, `[private path omitted]`, `[private path omitted]`, `src/knowledge/`, `src/lectures/`, `[private path omitted]`, `src/parsing/`, `src/rag/`, `src/transcription/`.

Ignored-Pfade (153): `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `_DELETE_2026-07-29_streamlit_demo.log`, `__init__.py`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `_prototypes/_dev_code_review/`, `_prototypes/_dev_to_add/`, `_prototypes/excel_helper.py`, `_prototypes/matlab_helper.py`, `_prototypes/notes_helper.py`, `_prototypes/optimise_helper.py`, `configuration/_dev_/`, `configuration/cfg_lecture_transcribe.json`, `configuration/context_audio_record.json`, `configuration/context_know_extract.json`, `configuration/context_lecture_compile.json`, `configuration/context_local_file_transcribe.json`, `configuration/context_webinar_transcribe.json`, `configuration/context_yt_transcribe.json`, `configuration/input_lecture_compile.json`, `[private path omitted]`, `docling_test/`, `docling_test/01_Ueberblick_Vektorrechnung_p1_2_no_enrich.md`, `docling_test_formula/`, `docling_test_formula/01_Ueberblick_Vektorrechnung.md`, `docs/_dev_health_check.txt`, `docs/_dev_new_content.txt`, `[private path omitted]`, `docs/_dev_tmux.txt`, `docs/_local_audit_c170/`, `docs/course_sources/cs50/cs50_python_week0_knowledge_input.v1.json`, `docs/course_sources/cs50/examples/official_transcript.normalized.json`, `docs/course_sources/cs50/llm_smoke_offline_result.json`, `docs/course_sources/cs50/uv_installed_integration_result.json`, `docs/course_sources/source.json`, `docs/cs50-material-inventory.v1.json`, `[private path omitted]`, `[private path omitted]`, `docs/python0-material-plan.v1.json`, `docs/reviewed-one-material.v1.json`, `frontend/__init__.py`, `frontend/_src/`, `frontend/_src/__init__.py`, `frontend/_src/screenshots/`, `frontend/_src/screenshots/ContainerTools.png`, `frontend/_src/screenshots/Infra_complete.png`, `frontend/_src/screenshots/Interface.png`, `frontend/_src/screenshots/airflow.png`, `frontend/_src/screenshots/details_processing.png`, `frontend/_src/screenshots/details_training.png`, `frontend/_src/screenshots/etl_metric.png`, `frontend/_src/screenshots/etl_trigger.png`, `frontend/_src/screenshots/fastapi.png`, `frontend/_src/screenshots/graph_processing.png`, `frontend/_src/screenshots/graph_training.png`, `frontend/_src/screenshots/infra_complete_flowchart.png`, `frontend/_src/screenshots/microservice.png`, `frontend/_src/screenshots/mlflow.png`, `frontend/_src/screenshots/mlflow1.png`, `frontend/_src/screenshots/mlflow2.png`, `frontend/_src/screenshots/monitoring.png`, `frontend/_src/screenshots/orchestration.png`, `frontend/_src/screenshots/recommend.png`, `frontend/_src/screenshots/training.png`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `frontend/pages/__init__.py`, `liora/`, `liora/ml_engineer_0/`, `liora/ml_engineer_1/`, `liora/ml_engineer_2/`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `[private path omitted]`, `monitoring/portainer/`, `[private path omitted]`, `src/__init__.py`, `src/_dev_filter_html_elements.py`, `src/_dev_test_script.py`, `src/mathe_vorkurs_2013_urls.json`, `src/test.py`, `src/tools_knowledge/_dev_rebuild_knowledge.py`, `src/tools_organizer/_dev_quickstart.py`, `src/tools_parsing/__init__.py`, `src/tools_transcribe/_dev_extract_audio.py`, `src/tools_transcribe/_dev_transcriber.py`, `src/tools_transcribe/_dev_write_transcript.py`, `src/utils/_dev_other_modules.md`, `tmux-client-14876.log`, `tmux-client-15209.log`, `tmux-client-15520.log`, `tmux-server-14878.log`, `tmux-server-15522.log`.

### 02 · Personal_Assistant-c21q

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c21q`
- Branch: `refs/heads/feat/c21q-qdrant-transcript-pilot`
- HEAD / lokaler Branch: `3a42b1675dffe823edc179a347fa97dd1a096fd0` / `3a42b1675dffe823edc179a347fa97dd1a096fd0`
- Betreff: `C21-Q.1: diagnose relocated transcript binding and preserve strict validation`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c21q-qdrant-transcript-pilot`, SHA `3a42b1675dffe823edc179a347fa97dd1a096fd0`.
- Backupref: `refs/heads/feat/c21q-qdrant-transcript-pilot`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `PROTECTED_ACTIVE`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: explicit/current-task protection; authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: [#72](https://github.com/rf-data/Personal_Assistant/pull/72), `open`, merged=False, gleicher Branch; API-head `3a42b1675dffe823edc179a347fa97dd1a096fd0`.

### 03 · Personal_Assistant-c22

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c22`
- Branch: `refs/heads/feat/c22-operations-readiness`
- HEAD / lokaler Branch: `f2842788efd487227ca95c8960f971ea14877cad` / `f2842788efd487227ca95c8960f971ea14877cad`
- Betreff: `C22: prepare single-host operations, private deployment profiles and verified restore`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c22-operations-readiness`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/feat/c22-operations-readiness`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 04 · Personal_Assistant-c230

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c230`
- Branch: `refs/heads/docs/c230-roadmap-planning`
- HEAD / lokaler Branch: `7f9fddf6d75f8db116aa33358122f4ddc90848ec` / `7f9fddf6d75f8db116aa33358122f4ddc90848ec`
- Betreff: `docs(C23.0): consolidate source-first roadmap and unapproved GitHub planning`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/docs/c230-roadmap-planning`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/docs/c230-roadmap-planning`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 05 · Personal_Assistant-c2301

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c2301`
- Branch: `refs/heads/feat/c23-01-parsed-content-adr`
- HEAD / lokaler Branch: `50699d331a769db3acd9e5e8507ad51b2de1760c` / `50699d331a769db3acd9e5e8507ad51b2de1760c`
- Betreff: `docs: specify C23 parsed content persistence architecture`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c23-01-parsed-content-adr`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/feat/c23-01-parsed-content-adr`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: [#75](https://github.com/rf-data/Personal_Assistant/pull/75), `closed`, merged=True, gleicher Branch; API-head `50699d331a769db3acd9e5e8507ad51b2de1760c`.

### 06 · Personal_Assistant-c2302a

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c2302a`
- Branch: `refs/heads/feat/c23-02a-content-store`
- HEAD / lokaler Branch: `df41af0b5f36fda6e30f9ac5fbd8c777e1f85cb2` / `df41af0b5f36fda6e30f9ac5fbd8c777e1f85cb2`
- Betreff: `feat: add isolated ContentStore persistence foundation`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c23-02a-content-store`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/feat/c23-02a-content-store`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 07 · Personal_Assistant-c2302b

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c2302b`
- Branch: `refs/heads/feat/c23-02b-content-adapters`
- HEAD / lokaler Branch: `ba2dcd4a0a74a16c63f74083d25a8fb69d244895` / `ba2dcd4a0a74a16c63f74083d25a8fb69d244895`
- Betreff: `C23-02B: verify and persist CS50 material and SRT bundles`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c23-02b-content-adapters`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/feat/c23-02b-content-adapters`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 08 · Personal_Assistant-c2302c

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c2302c`
- Branch: `refs/heads/feat/c23-02c-recovery-operations`
- HEAD / lokaler Branch: `f33df74ff09eb7d50223776080c6dd3048955a7c` / `f33df74ff09eb7d50223776080c6dd3048955a7c`
- Betreff: `C23-02C: add explicit content recovery, quarantine and verified snapshots`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c23-02c-recovery-operations`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/feat/c23-02c-recovery-operations`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 09 · Personal_Assistant-c2303

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c2303`
- Branch: `refs/heads/feat/c23-03-reimport-binding`
- HEAD / lokaler Branch: `42bbd8ae65110138bee82542ce02d99ec7d84be3` / `42bbd8ae65110138bee82542ce02d99ec7d84be3`
- Betreff: `C23-03: explicit reimport attempts and verified source inventory`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c23-03-reimport-binding`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/feat/c23-03-reimport-binding`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 10 · Personal_Assistant-c2304

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c2304`
- Branch: `refs/heads/feat/c23-04-content-read-api`
- HEAD / lokaler Branch: `ada2f185fd387312823f844fe99d9e9a54236e00` / `ada2f185fd387312823f844fe99d9e9a54236e00`
- Betreff: `C23-04: authorized content read API with signed keysets and safe downloads`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c23-04-content-read-api`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/feat/c23-04-content-read-api`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 11 · Personal_Assistant-c2305

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c2305`
- Branch: `refs/heads/feat/c23-05-txt-unknown-time`
- HEAD / lokaler Branch: `2e60d1529793bfb329a3648502cb26b589474c19` / `2e60d1529793bfb329a3648502cb26b589474c19`
- Betreff: `C23-05: support official TXT transcripts with explicit unknown times`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c23-05-txt-unknown-time`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/feat/c23-05-txt-unknown-time`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 12 · Personal_Assistant-c2306

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c2306`
- Branch: `refs/heads/feat/c23-06-real-material-evaluation`
- HEAD / lokaler Branch: `351646f0ffa545da7e3424e50ab78eb330e69542` / `351646f0ffa545da7e3424e50ab78eb330e69542`
- Betreff: `C23-06: prepare corpus inventory and independent parsing evaluation`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c23-06-real-material-evaluation`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/feat/c23-06-real-material-evaluation`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 13 · Personal_Assistant-c2401

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c2401`
- Branch: `refs/heads/docs/c24-01-indexing-retrieval`
- HEAD / lokaler Branch: `b001388e2f05472cea2e1054c2713c6c434c9de9` / `b001388e2f05472cea2e1054c2713c6c434c9de9`
- Betreff: `C24-01: define ContentStore indexing and retrieval architecture`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/docs/c24-01-indexing-retrieval`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/docs/c24-01-indexing-retrieval`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 14 · Personal_Assistant-c2402

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c2402`
- Branch: `refs/heads/feat/c24-02-deterministic-index-projection`
- HEAD / lokaler Branch: `7d1b655cf6228b87edac922e59e4b5fc2c5b80cb` / `7d1b655cf6228b87edac922e59e4b5fc2c5b80cb`
- Betreff: `C24-02: project verified ContentStore versions into deterministic index records`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c24-02-deterministic-index-projection`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/feat/c24-02-deterministic-index-projection`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 15 · Personal_Assistant-c2403

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c2403`
- Branch: `refs/heads/feat/c24-03-sqlite-fts5`
- HEAD / lokaler Branch: `0f3d9dd1066eb771629159888fb5ee97c0a75ebf` / `0f3d9dd1066eb771629159888fb5ee97c0a75ebf`
- Betreff: `Implement source-partitioned FTS5 generations and authorized lexical retrieval`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/c24-03-sqlite-fts5`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c24-03-sqlite-fts5`.
- Lokaler Tracking-SHA: `0f3d9dd1066eb771629159888fb5ee97c0a75ebf`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c24-03-sqlite-fts5`, SHA `0f3d9dd1066eb771629159888fb5ee97c0a75ebf`.
- Backupref: `refs/heads/feat/c24-03-sqlite-fts5`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 16 · Personal_Assistant-c2404

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c2404`
- Branch: `refs/heads/feat/c24-04-content-vector-adapter`
- HEAD / lokaler Branch: `12740b76a30d969b6c09d2be4ad1480a7dd8bdfd` / `12740b76a30d969b6c09d2be4ad1480a7dd8bdfd`
- Betreff: `Bound restored fake vector inventories and record final offline acceptance`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/c24-04-content-vector-adapter`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c24-04-content-vector-adapter`.
- Lokaler Tracking-SHA: `12740b76a30d969b6c09d2be4ad1480a7dd8bdfd`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c24-04-content-vector-adapter`, SHA `12740b76a30d969b6c09d2be4ad1480a7dd8bdfd`.
- Backupref: `refs/heads/feat/c24-04-content-vector-adapter`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 17 · Personal_Assistant-c2405a

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c2405a`
- Branch: `refs/heads/feat/c24-05a-retrieval-evaluation`
- HEAD / lokaler Branch: `5a7d050685c381dffd0574aaff62f704c78e7350` / `5a7d050685c381dffd0574aaff62f704c78e7350`
- Betreff: `C24-05-A: Independent retrieval evaluation contracts and offline acceptance`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/c24-05a-retrieval-evaluation`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c24-05a-retrieval-evaluation`.
- Lokaler Tracking-SHA: `5a7d050685c381dffd0574aaff62f704c78e7350`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c24-05a-retrieval-evaluation`, SHA `5a7d050685c381dffd0574aaff62f704c78e7350`.
- Backupref: `refs/heads/feat/c24-05a-retrieval-evaluation`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 18 · Personal_Assistant-c2405b

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c2405b`
- Branch: `refs/heads/feat/c24-05b-human-review-workflow`
- HEAD / lokaler Branch: `f3fae9ef6d2c919adb12b08242bf84819f2b42f2` / `f3fae9ef6d2c919adb12b08242bf84819f2b42f2`
- Betreff: `Document C24-05-B review workflow architecture and blocked prerequisites`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/c24-05b-human-review-workflow`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c24-05b-human-review-workflow`.
- Lokaler Tracking-SHA: `f3fae9ef6d2c919adb12b08242bf84819f2b42f2`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c24-05b-human-review-workflow`, SHA `f3fae9ef6d2c919adb12b08242bf84819f2b42f2`.
- Backupref: `refs/heads/feat/c24-05b-human-review-workflow`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `PROTECTED_ACTIVE`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: explicit/current-task protection; authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: [#88](https://github.com/rf-data/Personal_Assistant/pull/88), `open`, merged=False, gleicher Branch; API-head `f3fae9ef6d2c919adb12b08242bf84819f2b42f2`.

### 19 · Personal_Assistant-c2405b1

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c2405b1`
- Branch: `refs/heads/feat/c24-05b1-review-backend`
- HEAD / lokaler Branch: `20b8916900b201d8051e203327a7023e06c64914` / `20b8916900b201d8051e203327a7023e06c64914`
- Betreff: `C24-05-B1: implement authorized human review persistence and API`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/c24-05b1-review-backend`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c24-05b1-review-backend`.
- Lokaler Tracking-SHA: `20b8916900b201d8051e203327a7023e06c64914`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c24-05b1-review-backend`, SHA `20b8916900b201d8051e203327a7023e06c64914`.
- Backupref: `refs/heads/feat/c24-05b1-review-backend`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 20 · Personal_Assistant-c2405c

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c2405c`
- Branch: `refs/heads/feat/c24-05c-real-corpus-pilot`
- HEAD / lokaler Branch: `a3d253a27c4fd7aed37c2a4b9d38aa8a4ed1d81d` / `a3d253a27c4fd7aed37c2a4b9d38aa8a4ed1d81d`
- Betreff: `Integrate merged C24-05-A and retain readiness history as metadata revision 2`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/c24-05c-real-corpus-pilot`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c24-05c-real-corpus-pilot`.
- Lokaler Tracking-SHA: `a3d253a27c4fd7aed37c2a4b9d38aa8a4ed1d81d`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c24-05c-real-corpus-pilot`, SHA `a3d253a27c4fd7aed37c2a4b9d38aa8a4ed1d81d`.
- Backupref: `refs/heads/feat/c24-05c-real-corpus-pilot`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `PROTECTED_ACTIVE`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: explicit/current-task protection; authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: [#89](https://github.com/rf-data/Personal_Assistant/pull/89), `open`, merged=False, gleicher Branch; API-head `a3d253a27c4fd7aed37c2a4b9d38aa8a4ed1d81d`.

### 21 · Personal_Assistant-c2405c2

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c2405c2`
- Branch: `refs/heads/feat/c24-05c2-real-pilot`
- HEAD / lokaler Branch: `c8894abea7be1554a6f234f551ce92bc6e00bdc9` / `c8894abea7be1554a6f234f551ce92bc6e00bdc9`
- Betreff: `C24-05-C2: Authorized real-corpus evaluation pilot`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/c24-05c2-real-pilot`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c24-05c2-real-pilot`.
- Lokaler Tracking-SHA: `c8894abea7be1554a6f234f551ce92bc6e00bdc9`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c24-05c2-real-pilot`, SHA `c8894abea7be1554a6f234f551ce92bc6e00bdc9`.
- Backupref: `refs/heads/feat/c24-05c2-real-pilot`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 22 · Personal_Assistant-c2406a

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c2406a`
- Branch: `refs/heads/feat/c24-06a-local-review`
- HEAD / lokaler Branch: `4c057ae33d41ba98e227879cc8a51283338e4a0b` / `4c057ae33d41ba98e227879cc8a51283338e4a0b`
- Betreff: `Merge pull request #91 from rf-data/feat/c24-05c2-real-pilot`
- Status vollständig: `True`; T/U/I: `0/5/0`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c24-06a-local-review`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/feat/c24-06a-local-review`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: unsecured untracked/ignored paths (including empty directories); authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| `??` | `docs/operations/local_review_environment.md` |
| `??` | `scripts/_local_review_signal.py` |
| `??` | `scripts/local_review.py` |
| `??` | `tests/local_review_browser_probe.py` |
| `??` | `tests/test_local_review_environment.py` |

Zusatzpfade (5): `docs/operations/local_review_environment.md`, `scripts/_local_review_signal.py`, `scripts/local_review.py`, `tests/local_review_browser_probe.py`, `tests/test_local_review_environment.py`.

### 23 · Personal_Assistant-c24r

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c24r`
- Branch: `refs/heads/feat/c24r-retrieval_completion`
- HEAD / lokaler Branch: `4c057ae33d41ba98e227879cc8a51283338e4a0b` / `4c057ae33d41ba98e227879cc8a51283338e4a0b`
- Betreff: `Merge pull request #91 from rf-data/feat/c24-05c2-real-pilot`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c24r-retrieval_completion`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/feat/c24r-retrieval_completion`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `PROTECTED_ACTIVE`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: explicit/current-task protection; authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 24 · Personal_Assistant-c26-final-compat

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26-final-compat`
- Branch: `DETACHED_HEAD`
- HEAD / lokaler Branch: `c4b057a75c38655e43b8ac35a35cc82645ba2826` / `unknown / nicht vorhanden`
- Betreff: `Merge pull request #154 from rf-data/feat/c26-week0-acceptance`
- Status vollständig: `True`; T/U/I: `31/15/3`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `unknown / nicht vorhanden`, SHA `unknown / nicht vorhanden`.
- Backupref: `unknown / nicht vorhanden`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `DIRTY`, `UNTRACKED_OR_IGNORED_RISK`, `DETACHED_HEAD`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: tracked changes; unsecured untracked/ignored paths (including empty directories); detached HEAD unsupported for removal; authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| ` M` | `deployment/Dockerfile` |
| ` M` | `deployment/Dockerfile.dockerignore` |
| ` M` | `docker/DockerFile.worker` |
| ` M` | `docker/DockerFile.worker.dockerignore` |
| ` M` | `docs/cs50/contracts/material_quality.md` |
| ` M` | `docs/deployment/architecture.md` |
| ` M` | `docs/deployment/c26b_validation.md` |
| ` M` | `docs/deployment/configuration.md` |
| ` M` | `docs/deployment/https.md` |
| ` M` | `docs/deployment/operations.md` |
| ` M` | `docs/job_control/contract.v1.json` |
| ` M` | `scripts/cs50_batch.py` |
| ` M` | `scripts/worker_image_smoke.py` |
| ` M` | `src/job_control/catalog.py` |
| ` M` | `src/job_control/controller.py` |
| ` M` | `src/job_control/executor.py` |
| ` M` | `src/job_control/models.py` |
| ` M` | `src/job_control/operations.py` |
| ` M` | `src/job_control/store.py` |
| ` M` | `src/model_materials/quality.py` |
| ` M` | `src/model_materials/week.py` |
| ` M` | `src/tools_lecture/material_handoff.py` |
| ` M` | `src/tools_materials/batch.py` |
| ` M` | `src/tools_materials/capacity.py` |
| ` M` | `src/tools_materials/course.py` |
| ` M` | `src/tools_materials/mapping.py` |
| ` M` | `src/tools_materials/processing.py` |
| ` M` | `src/tools_materials/quality.py` |
| ` M` | `src/tools_materials/week.py` |
| ` M` | `src/workflows/definition.py` |
| ` M` | `src/workflows/models.py` |
| `??` | `docs/cs50/contracts/html_aggregation_v2.md` |
| `??` | `docs/deployment/c26_gate_validation.md` |
| `??` | `docs/deployment/c26a/html_aggregation_validation.md` |
| `??` | `docs/deployment/deployment_gate.md` |
| `??` | `scripts/c26_storage_preflight.py` |
| `??` | `scripts/deployment_gate.py` |
| `??` | `src/job_control/deployment_gate.py` |
| `??` | `src/model_materials/assignments.py` |
| `??` | `src/tools_materials/assignments.py` |
| `??` | `src/tools_materials/html_projection.py` |
| `??` | `src/tools_materials/quality_projection.py` |
| `??` | `tests/test_c26_storage_preflight.py` |
| `??` | `tests/test_cs50_assignment_integration.py` |
| `??` | `tests/test_cs50_html_projection.py` |
| `??` | `tests/test_deployment_gate.py` |
| `!!` | `docs/deployment/c26_gate_validation.v1.json` |
| `!!` | `docs/deployment/c26a/html_aggregation_validation.v1.json` |
| `!!` | `tests/fixtures/material_quality/html_projection_baseline.v1.json` |

Zusatzpfade (15): `docs/cs50/contracts/html_aggregation_v2.md`, `docs/deployment/c26_gate_validation.md`, `docs/deployment/c26a/html_aggregation_validation.md`, `docs/deployment/deployment_gate.md`, `scripts/c26_storage_preflight.py`, `scripts/deployment_gate.py`, `src/job_control/deployment_gate.py`, `src/model_materials/assignments.py`, `src/tools_materials/assignments.py`, `src/tools_materials/html_projection.py`, `src/tools_materials/quality_projection.py`, `tests/test_c26_storage_preflight.py`, `tests/test_cs50_assignment_integration.py`, `tests/test_cs50_html_projection.py`, `tests/test_deployment_gate.py`.

Ignored-Pfade (3): `docs/deployment/c26_gate_validation.v1.json`, `docs/deployment/c26a/html_aggregation_validation.v1.json`, `tests/fixtures/material_quality/html_projection_baseline.v1.json`.

### 25 · Personal_Assistant-c26-final-pilot

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26-final-pilot`
- Branch: `refs/heads/feat/c26-final-pilot-readiness`
- HEAD / lokaler Branch: `7a8e96d3a9004fabcf86962e6f0859479348c83a` / `7a8e96d3a9004fabcf86962e6f0859479348c83a`
- Betreff: `fix(c26): bind assignment discovery through C18 and prepare final gates`
- Status vollständig: `True`; T/U/I: `0/0/4`.
- Upstream: `refs/remotes/origin/feat/c26-final-pilot-readiness`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c26-final-pilot-readiness`.
- Lokaler Tracking-SHA: `7a8e96d3a9004fabcf86962e6f0859479348c83a`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c26-final-pilot-readiness`, SHA `7a8e96d3a9004fabcf86962e6f0859479348c83a`.
- Backupref: `refs/heads/feat/c26-final-pilot-readiness`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: unsecured untracked/ignored paths (including empty directories); authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| `!!` | `.ruff_cache/.gitignore` |
| `!!` | `.ruff_cache/0.16.0/` |
| `!!` | `.ruff_cache/CACHEDIR.TAG` |

Zusatzpfade (1): `.ruff_cache/`.

Ignored-Pfade (4): `.ruff_cache/`, `.ruff_cache/.gitignore`, `.ruff_cache/0.16.0/`, `.ruff_cache/CACHEDIR.TAG`.

### 26 · Personal_Assistant-c26-gate

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26-gate`
- Branch: `DETACHED_HEAD`
- HEAD / lokaler Branch: `e581e201ef6b3d6c06aca14de845e0687d213b37` / `unknown / nicht vorhanden`
- Betreff: `Merge pull request #147 from rf-data/feat/c26b-private-vpn-review`
- Status vollständig: `True`; T/U/I: `16/6/1`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `unknown / nicht vorhanden`, SHA `unknown / nicht vorhanden`.
- Backupref: `unknown / nicht vorhanden`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `DIRTY`, `UNTRACKED_OR_IGNORED_RISK`, `DETACHED_HEAD`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: tracked changes; unsecured untracked/ignored paths (including empty directories); detached HEAD unsupported for removal; authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| ` M` | `deployment/Dockerfile` |
| ` M` | `deployment/Dockerfile.dockerignore` |
| ` M` | `docker/DockerFile.worker` |
| ` M` | `docker/DockerFile.worker.dockerignore` |
| ` M` | `docs/deployment/architecture.md` |
| ` M` | `docs/deployment/c26b_validation.md` |
| ` M` | `docs/deployment/configuration.md` |
| ` M` | `docs/deployment/https.md` |
| ` M` | `docs/deployment/operations.md` |
| ` M` | `docs/job_control/contract.v1.json` |
| ` M` | `scripts/worker_image_smoke.py` |
| ` M` | `src/job_control/controller.py` |
| ` M` | `src/job_control/executor.py` |
| ` M` | `src/job_control/models.py` |
| ` M` | `src/job_control/operations.py` |
| ` M` | `src/job_control/store.py` |
| `??` | `.review-artifacts/review.bundle` |
| `??` | `docs/deployment/c26_gate_validation.md` |
| `??` | `docs/deployment/deployment_gate.md` |
| `??` | `scripts/deployment_gate.py` |
| `??` | `src/job_control/deployment_gate.py` |
| `??` | `tests/test_deployment_gate.py` |
| `!!` | `docs/deployment/c26_gate_validation.v1.json` |

Zusatzpfade (6): `.review-artifacts/`, `docs/deployment/c26_gate_validation.md`, `docs/deployment/deployment_gate.md`, `scripts/deployment_gate.py`, `src/job_control/deployment_gate.py`, `tests/test_deployment_gate.py`.

Ignored-Pfade (1): `docs/deployment/c26_gate_validation.v1.json`.

### 27 · Personal_Assistant-c26-integration

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26-integration`
- Branch: `refs/heads/feat/c26-integration-b3-b7`
- HEAD / lokaler Branch: `cba3302261be5b5cb0a36fc482250a5268b8ad44` / `cba3302261be5b5cb0a36fc482250a5268b8ad44`
- Betreff: `feat(cs50): add media-last fallback planning and remaining material adapters`
- Status vollständig: `True`; T/U/I: `20/3/0`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c26-integration-b3-b7`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/feat/c26-integration-b3-b7`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `DIRTY`, `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: tracked changes; unsecured untracked/ignored paths (including empty directories); index flags/submodules require separate evidence; authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| `A ` | `docs/deployment/c26a/code_zip_pilot.md` |
| `A ` | `docs/deployment/c26a/code_zip_validation.md` |
| `A ` | `docs/deployment/c26a/knowledge_fix01_validation.md` |
| ` M` | `docs/deployment/c26a/media_last_pilot.md` |
| `UU` | `docs/deployment/c26a/multiformat_pilot.md` |
| `UU` | `scripts/cs50_batch.py` |
| ` M` | `src/model_materials/media_plan.py` |
| `M ` | `src/run_knowledge_extraction.py` |
| `M ` | `src/tools_knowledge/consolidate_knowledge.py` |
| `M ` | `src/tools_knowledge/semantic_knowledge.py` |
| `M ` | `src/tools_materials/batch.py` |
| `A ` | `src/tools_materials/code_discovery.py` |
| `A ` | `src/tools_materials/code_import.py` |
| `A ` | `src/tools_materials/code_structure.py` |
| `A ` | `src/tools_materials/code_zip.py` |
| ` M` | `src/tools_materials/media_evidence.py` |
| ` M` | `src/tools_materials/media_plan.py` |
| `M ` | `src/tools_materials/processing.py` |
| `A ` | `tests/test_cs50_code_zip.py` |
| `A ` | `tests/test_knowledge_identity_arguments.py` |
| `??` | `docs/deployment/c26a/integration_b3_b7.md` |
| `??` | `src/tools_materials/code_evidence.py` |
| `??` | `tests/test_c26_integrated_pipeline.py` |

Zusatzpfade (3): `docs/deployment/c26a/integration_b3_b7.md`, `src/tools_materials/code_evidence.py`, `tests/test_c26_integrated_pipeline.py`.

Riskante Indexeinträge (2): `docs/deployment/c26a/multiformat_pilot.md`, `scripts/cs50_batch.py`.

### 28 · Personal_Assistant-c26-integration-review

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26-integration-review`
- Branch: `DETACHED_HEAD`
- HEAD / lokaler Branch: `cae97b48611471ba7a04e1e7236f9453f1d0dcd4` / `unknown / nicht vorhanden`
- Betreff: `Integrate B7 with merged C26 code and Knowledge contracts`
- Status vollständig: `True`; T/U/I: `1/0/1`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `unknown / nicht vorhanden`, SHA `unknown / nicht vorhanden`.
- Backupref: `unknown / nicht vorhanden`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `DIRTY`, `UNTRACKED_OR_IGNORED_RISK`, `DETACHED_HEAD`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: tracked changes; unsecured untracked/ignored paths (including empty directories); detached HEAD unsupported for removal; authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| ` M` | `docs/deployment/c26a/integration_b3_b7.md` |
| `!!` | `[private path omitted]` |

Ignored-Pfade (1): `[private path omitted]`.

### 29 · Personal_Assistant-c26-legacy-pr-audit

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26-legacy-pr-audit`
- Branch: `refs/heads/audit/c26-legacy-prs`
- HEAD / lokaler Branch: `29114d2e2877cee9c434f620da852313963e3a01` / `29114d2e2877cee9c434f620da852313963e3a01`
- Betreff: `Merge pull request #149 from rf-data/feat/c26a-html-projection`
- Status vollständig: `True`; T/U/I: `1/1/7`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/audit/c26-legacy-prs`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/audit/c26-legacy-prs`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `DIRTY`, `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: tracked changes; unsecured untracked/ignored paths (including empty directories); authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| ` M` | `docs/cs50/operations/historical_pr_review.md` |
| `??` | `docs/cs50/operations/legacy_pr_delta_audit_2026-10-24.md` |
| `!!` | `src/__pycache__/` |
| `!!` | `src/model_knowledge/__pycache__/` |
| `!!` | `src/model_transcribe/__pycache__/` |
| `!!` | `src/tools_knowledge/__pycache__/` |
| `!!` | `src/tools_lecture/__pycache__/` |
| `!!` | `src/tools_transcribe/__pycache__/` |
| `!!` | `src/utils/__pycache__/` |

Zusatzpfade (1): `docs/cs50/operations/legacy_pr_delta_audit_2026-10-24.md`.

Ignored-Pfade (7): `src/__pycache__/`, `src/model_knowledge/__pycache__/`, `src/model_transcribe/__pycache__/`, `src/tools_knowledge/__pycache__/`, `src/tools_lecture/__pycache__/`, `src/tools_transcribe/__pycache__/`, `src/utils/__pycache__/`.

### 30 · Personal_Assistant-c26-operations-preflight

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26-operations-preflight`
- Branch: `refs/heads/audit/c26-operations-preflight`
- HEAD / lokaler Branch: `ecac8cfa844a7e4da9e0066a2c49c0c49fb3541d` / `ecac8cfa844a7e4da9e0066a2c49c0c49fb3541d`
- Betreff: `docs(c26): prepare read-only operations acceptance and isolate remaining gates`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/audit/c26-operations-preflight`, SHA `ecac8cfa844a7e4da9e0066a2c49c0c49fb3541d`.
- Backupref: `refs/heads/audit/c26-operations-preflight`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `PROTECTED_ACTIVE`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: explicit/current-task protection; authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: [#160](https://github.com/rf-data/Personal_Assistant/pull/160), `open`, merged=False, gleicher Branch; API-head `ecac8cfa844a7e4da9e0066a2c49c0c49fb3541d`.

### 31 · Personal_Assistant-c26-release-readiness

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26-release-readiness`
- Branch: `refs/heads/docs/c26-release-readiness`
- HEAD / lokaler Branch: `ad4e33b63389c2d5378dfcfd733e144f20f0af2e` / `ad4e33b63389c2d5378dfcfd733e144f20f0af2e`
- Betreff: `docs(c26): audit integration and prepare operator acceptance`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/docs/c26-release-readiness`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/docs/c26-release-readiness`.
- Lokaler Tracking-SHA: `ad4e33b63389c2d5378dfcfd733e144f20f0af2e`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/docs/c26-release-readiness`, SHA `ad4e33b63389c2d5378dfcfd733e144f20f0af2e`.
- Backupref: `refs/heads/docs/c26-release-readiness`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 32 · Personal_Assistant-c26-runtime-bootstrap

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26-runtime-bootstrap`
- Branch: `refs/heads/feat/c26-runtime-bootstrap`
- HEAD / lokaler Branch: `e502aa915ad0e928dbe7e92eacd44fff0152912b` / `e502aa915ad0e928dbe7e92eacd44fff0152912b`
- Betreff: `Merge pull request #155 from rf-data/feat/c26-final-pilot-readiness`
- Status vollständig: `True`; T/U/I: `9/9/5`.
- Upstream: `refs/remotes/origin/master`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/master`.
- Lokaler Tracking-SHA: `e68275205fefb7a5f6db42bc45060e505bfcefb5`; ahead/behind: `0/6`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c26-runtime-bootstrap`, SHA `80c31e52f76c1f3f62102b6884752b722f796e7c`.
- Backupref: `refs/heads/feat/c26-runtime-bootstrap`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `PROTECTED_ACTIVE`, `DIRTY`, `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: explicit/current-task protection; tracked changes; unsecured untracked/ignored paths (including empty directories); authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: [#157](https://github.com/rf-data/Personal_Assistant/pull/157), `open`, merged=False, gleicher Branch; API-head `80c31e52f76c1f3f62102b6884752b722f796e7c`.

| Gitstatus | Pfad |
| --- | --- |
| ` M` | `deployment/Dockerfile` |
| `AM` | `deployment/c26-runtime.controller.json.example` |
| `AM` | `deployment/coolify.runtime-bootstrap.compose.yaml` |
| `AM` | `docs/deployment/c26_runtime/README.md` |
| `AM` | `docs/deployment/c26_runtime/driver_contract.md` |
| `AM` | `docs/deployment/c26_runtime/operator_checks.md` |
| `AM` | `docs/deployment/c26_runtime/rollout.md` |
| `AM` | `tests/test_c26_runtime_bootstrap.py` |
| `M ` | `tests/test_deployment_transport.py` |
| `??` | `deployment/c26-runtime.limits.json.example` |
| `??` | `docs/deployment/c26_runtime/coolify_compatibility.md` |
| `??` | `docs/deployment/c26_runtime/diagnostics.md` |
| `??` | `docs/deployment/c26_runtime/integration_matrix.md` |
| `??` | `docs/deployment/c26_runtime/resources.md` |
| `??` | `docs/deployment/c26_runtime/runtime_configuration.md` |
| `??` | `docs/deployment/c26_runtime/source_assessment.md` |
| `??` | `scripts/c26_runtime_preflight.py` |
| `??` | `tests/test_c26_runtime_preflight.py` |
| `!!` | `docs/deployment/c26_runtime/operator_inventory.v1.json` |
| `!!` | `docs/deployment/c26_runtime/runtime_configuration_validation.v1.json` |
| `!!` | `docs/deployment/c26_runtime/runtime_diagnostics.v1.json` |
| `!!` | `docs/deployment/c26_runtime/technical_sources.v1.json` |
| `!!` | `docs/deployment/c26_runtime/validation.v1.json` |

Zusatzpfade (9): `deployment/c26-runtime.limits.json.example`, `docs/deployment/c26_runtime/coolify_compatibility.md`, `docs/deployment/c26_runtime/diagnostics.md`, `docs/deployment/c26_runtime/integration_matrix.md`, `docs/deployment/c26_runtime/resources.md`, `docs/deployment/c26_runtime/runtime_configuration.md`, `docs/deployment/c26_runtime/source_assessment.md`, `scripts/c26_runtime_preflight.py`, `tests/test_c26_runtime_preflight.py`.

Ignored-Pfade (5): `docs/deployment/c26_runtime/operator_inventory.v1.json`, `docs/deployment/c26_runtime/runtime_configuration_validation.v1.json`, `docs/deployment/c26_runtime/runtime_diagnostics.v1.json`, `docs/deployment/c26_runtime/technical_sources.v1.json`, `docs/deployment/c26_runtime/validation.v1.json`.

### 33 · Personal_Assistant-c26-runtime-compat

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26-runtime-compat`
- Branch: `DETACHED_HEAD`
- HEAD / lokaler Branch: `e502aa915ad0e928dbe7e92eacd44fff0152912b` / `unknown / nicht vorhanden`
- Betreff: `Merge pull request #155 from rf-data/feat/c26-final-pilot-readiness`
- Status vollständig: `True`; T/U/I: `27/21/18`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `unknown / nicht vorhanden`, SHA `unknown / nicht vorhanden`.
- Backupref: `unknown / nicht vorhanden`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `DIRTY`, `UNTRACKED_OR_IGNORED_RISK`, `DETACHED_HEAD`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: tracked changes; unsecured untracked/ignored paths (including empty directories); detached HEAD unsupported for removal; authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| ` M` | `deployment/Dockerfile` |
| ` M` | `deployment/Dockerfile.dockerignore` |
| ` M` | `docker/DockerFile.worker` |
| ` M` | `docker/DockerFile.worker.dockerignore` |
| ` M` | `docs/cs50/contracts/material_quality.md` |
| ` M` | `docs/deployment/architecture.md` |
| ` M` | `docs/deployment/c26b_validation.md` |
| ` M` | `docs/deployment/configuration.md` |
| ` M` | `docs/deployment/https.md` |
| ` M` | `docs/deployment/operations.md` |
| ` M` | `docs/job_control/contract.v1.json` |
| ` M` | `scripts/worker_image_smoke.py` |
| ` M` | `src/core/retry.py` |
| ` M` | `src/job_control/controller.py` |
| ` M` | `src/job_control/executor.py` |
| ` M` | `src/job_control/models.py` |
| ` M` | `src/job_control/operations.py` |
| ` M` | `src/job_control/store.py` |
| ` M` | `src/model_materials/quality.py` |
| ` M` | `src/tools_knowledge/find_knowledge.py` |
| ` M` | `src/tools_lecture/material_handoff.py` |
| ` M` | `src/tools_materials/mapping.py` |
| ` M` | `src/tools_materials/quality.py` |
| ` M` | `src/utils/general_helper.py` |
| ` M` | `src/utils/path_helper.py` |
| ` M` | `tests/test_cs50_knowledge_input.py` |
| ` M` | `tests/test_deployment_transport.py` |
| `??` | `deployment/c26-runtime.controller.json.example` |
| `??` | `deployment/c26-runtime.limits.json.example` |
| `??` | `deployment/coolify.runtime-bootstrap.compose.yaml` |
| `??` | `docs/cs50/contracts/html_aggregation_v2.md` |
| `??` | `docs/deployment/c26_gate_validation.md` |
| `??` | `docs/deployment/c26_stabilization/README.md` |
| `??` | `docs/deployment/c26_stabilization/capacity.md` |
| `??` | `docs/deployment/c26_stabilization/https_vpn_operator.md` |
| `??` | `docs/deployment/c26_stabilization/week0_operator.md` |
| `??` | `docs/deployment/c26a/html_aggregation_validation.md` |
| `??` | `docs/deployment/deployment_gate.md` |
| `??` | `scripts/c26_runtime_preflight.py` |
| `??` | `scripts/deployment_gate.py` |
| `??` | `src/job_control/deployment_gate.py` |
| `??` | `src/tools_materials/html_projection.py` |
| `??` | `src/tools_materials/quality_projection.py` |
| `??` | `tests/test_c26_runtime_bootstrap.py` |
| `??` | `tests/test_c26_runtime_preflight.py` |
| `??` | `tests/test_cs50_html_projection.py` |
| `??` | `tests/test_deployment_gate.py` |
| `??` | `tests/test_job_store_contention.py` |
| `!!` | `docs/deployment/c26_gate_validation.v1.json` |
| `!!` | `docs/deployment/c26_stabilization/cache_candidates.v1.json` |
| `!!` | `docs/deployment/c26_stabilization/capacity.v1.json` |
| `!!` | `docs/deployment/c26_stabilization/pilot_candidate.v1.json` |
| `!!` | `docs/deployment/c26_stabilization/sqlite_observation.v1.json` |
| `!!` | `docs/deployment/c26_stabilization/validation.v1.json` |
| `!!` | `docs/deployment/c26a/html_aggregation_validation.v1.json` |
| `!!` | `src/agent/prompts/__pycache__/` |
| `!!` | `src/core/__pycache__/` |
| `!!` | `src/model_discovery/__pycache__/` |
| `!!` | `src/model_knowledge/__pycache__/` |
| `!!` | `src/model_lecture/__pycache__/` |
| `!!` | `src/model_transcribe/__pycache__/` |
| `!!` | `src/tools_knowledge/__pycache__/` |
| `!!` | `src/tools_lecture/__pycache__/` |
| `!!` | `src/tools_transcribe/__pycache__/` |
| `!!` | `src/utils/__pycache__/` |
| `!!` | `tests/fixtures/material_quality/html_projection_baseline.v1.json` |

Zusatzpfade (18): `deployment/c26-runtime.controller.json.example`, `deployment/c26-runtime.limits.json.example`, `deployment/coolify.runtime-bootstrap.compose.yaml`, `docs/cs50/contracts/html_aggregation_v2.md`, `docs/deployment/c26_gate_validation.md`, `docs/deployment/c26_stabilization/`, `docs/deployment/c26a/html_aggregation_validation.md`, `docs/deployment/deployment_gate.md`, `scripts/c26_runtime_preflight.py`, `scripts/deployment_gate.py`, `src/job_control/deployment_gate.py`, `src/tools_materials/html_projection.py`, `src/tools_materials/quality_projection.py`, `tests/test_c26_runtime_bootstrap.py`, `tests/test_c26_runtime_preflight.py`, `tests/test_cs50_html_projection.py`, `tests/test_deployment_gate.py`, `tests/test_job_store_contention.py`.

Ignored-Pfade (18): `docs/deployment/c26_gate_validation.v1.json`, `docs/deployment/c26_stabilization/cache_candidates.v1.json`, `docs/deployment/c26_stabilization/capacity.v1.json`, `docs/deployment/c26_stabilization/pilot_candidate.v1.json`, `docs/deployment/c26_stabilization/sqlite_observation.v1.json`, `docs/deployment/c26_stabilization/validation.v1.json`, `docs/deployment/c26a/html_aggregation_validation.v1.json`, `src/agent/prompts/__pycache__/`, `src/core/__pycache__/`, `src/model_discovery/__pycache__/`, `src/model_knowledge/__pycache__/`, `src/model_lecture/__pycache__/`, `src/model_transcribe/__pycache__/`, `src/tools_knowledge/__pycache__/`, `src/tools_lecture/__pycache__/`, `src/tools_transcribe/__pycache__/`, `src/utils/__pycache__/`, `tests/fixtures/material_quality/html_projection_baseline.v1.json`.

### 34 · Personal_Assistant-c26-stabilization

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26-stabilization`
- Branch: `refs/heads/fix/c26-stabilization`
- HEAD / lokaler Branch: `c77128b14e60b78a546fd804507ff255d4833759` / `c77128b14e60b78a546fd804507ff255d4833759`
- Betreff: `fix(c26): isolate optional imports and bound SQLite setup retries`
- Status vollständig: `True`; T/U/I: `0/0/16`.
- Upstream: `refs/remotes/origin/fix/c26-stabilization`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/fix/c26-stabilization`.
- Lokaler Tracking-SHA: `c77128b14e60b78a546fd804507ff255d4833759`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/fix/c26-stabilization`, SHA `c77128b14e60b78a546fd804507ff255d4833759`.
- Backupref: `refs/heads/fix/c26-stabilization`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: unsecured untracked/ignored paths (including empty directories); authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| `!!` | `.ruff_cache/.gitignore` |
| `!!` | `.ruff_cache/0.16.0/` |
| `!!` | `.ruff_cache/CACHEDIR.TAG` |
| `!!` | `scripts/__pycache__/` |
| `!!` | `src/agent/prompts/__pycache__/` |
| `!!` | `src/core/__pycache__/` |
| `!!` | `src/job_control/__pycache__/` |
| `!!` | `src/model_discovery/__pycache__/` |
| `!!` | `src/model_knowledge/__pycache__/` |
| `!!` | `src/model_lecture/__pycache__/` |
| `!!` | `src/model_transcribe/__pycache__/` |
| `!!` | `src/tools_knowledge/__pycache__/` |
| `!!` | `src/tools_lecture/__pycache__/` |
| `!!` | `src/tools_transcribe/__pycache__/` |
| `!!` | `src/utils/__pycache__/` |

Zusatzpfade (1): `.ruff_cache/`.

Ignored-Pfade (16): `.ruff_cache/`, `.ruff_cache/.gitignore`, `.ruff_cache/0.16.0/`, `.ruff_cache/CACHEDIR.TAG`, `scripts/__pycache__/`, `src/agent/prompts/__pycache__/`, `src/core/__pycache__/`, `src/job_control/__pycache__/`, `src/model_discovery/__pycache__/`, `src/model_knowledge/__pycache__/`, `src/model_lecture/__pycache__/`, `src/model_transcribe/__pycache__/`, `src/tools_knowledge/__pycache__/`, `src/tools_lecture/__pycache__/`, `src/tools_transcribe/__pycache__/`, `src/utils/__pycache__/`.

### 35 · Personal_Assistant-c26-stabilization-compat

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26-stabilization-compat`
- Branch: `DETACHED_HEAD`
- HEAD / lokaler Branch: `e502aa915ad0e928dbe7e92eacd44fff0152912b` / `unknown / nicht vorhanden`
- Betreff: `Merge pull request #155 from rf-data/feat/c26-final-pilot-readiness`
- Status vollständig: `True`; T/U/I: `26/11/3`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `unknown / nicht vorhanden`, SHA `unknown / nicht vorhanden`.
- Backupref: `unknown / nicht vorhanden`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `DIRTY`, `UNTRACKED_OR_IGNORED_RISK`, `DETACHED_HEAD`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: tracked changes; unsecured untracked/ignored paths (including empty directories); detached HEAD unsupported for removal; authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| ` M` | `deployment/Dockerfile` |
| ` M` | `deployment/Dockerfile.dockerignore` |
| ` M` | `docker/DockerFile.worker` |
| ` M` | `docker/DockerFile.worker.dockerignore` |
| ` M` | `docs/cs50/contracts/material_quality.md` |
| ` M` | `docs/deployment/architecture.md` |
| ` M` | `docs/deployment/c26b_validation.md` |
| ` M` | `docs/deployment/configuration.md` |
| ` M` | `docs/deployment/https.md` |
| ` M` | `docs/deployment/operations.md` |
| ` M` | `docs/job_control/contract.v1.json` |
| ` M` | `scripts/worker_image_smoke.py` |
| ` M` | `src/core/retry.py` |
| ` M` | `src/job_control/controller.py` |
| ` M` | `src/job_control/executor.py` |
| ` M` | `src/job_control/models.py` |
| ` M` | `src/job_control/operations.py` |
| ` M` | `src/job_control/store.py` |
| ` M` | `src/model_materials/quality.py` |
| ` M` | `src/tools_knowledge/find_knowledge.py` |
| ` M` | `src/tools_lecture/material_handoff.py` |
| ` M` | `src/tools_materials/mapping.py` |
| ` M` | `src/tools_materials/quality.py` |
| ` M` | `src/utils/general_helper.py` |
| ` M` | `src/utils/path_helper.py` |
| ` M` | `tests/test_cs50_knowledge_input.py` |
| `??` | `docs/cs50/contracts/html_aggregation_v2.md` |
| `??` | `docs/deployment/c26_gate_validation.md` |
| `??` | `docs/deployment/c26a/html_aggregation_validation.md` |
| `??` | `docs/deployment/deployment_gate.md` |
| `??` | `scripts/deployment_gate.py` |
| `??` | `src/job_control/deployment_gate.py` |
| `??` | `src/tools_materials/html_projection.py` |
| `??` | `src/tools_materials/quality_projection.py` |
| `??` | `tests/test_cs50_html_projection.py` |
| `??` | `tests/test_deployment_gate.py` |
| `??` | `tests/test_job_store_contention.py` |
| `!!` | `docs/deployment/c26_gate_validation.v1.json` |
| `!!` | `docs/deployment/c26a/html_aggregation_validation.v1.json` |
| `!!` | `tests/fixtures/material_quality/html_projection_baseline.v1.json` |

Zusatzpfade (11): `docs/cs50/contracts/html_aggregation_v2.md`, `docs/deployment/c26_gate_validation.md`, `docs/deployment/c26a/html_aggregation_validation.md`, `docs/deployment/deployment_gate.md`, `scripts/deployment_gate.py`, `src/job_control/deployment_gate.py`, `src/tools_materials/html_projection.py`, `src/tools_materials/quality_projection.py`, `tests/test_cs50_html_projection.py`, `tests/test_deployment_gate.py`, `tests/test_job_store_contention.py`.

Ignored-Pfade (3): `docs/deployment/c26_gate_validation.v1.json`, `docs/deployment/c26a/html_aggregation_validation.v1.json`, `tests/fixtures/material_quality/html_projection_baseline.v1.json`.

### 36 · Personal_Assistant-c26-week0-acceptance

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26-week0-acceptance`
- Branch: `refs/heads/feat/c26-week0-acceptance`
- HEAD / lokaler Branch: `fc6cf0d94cd48dac21d7f8a834a95f9de47c0fd7` / `fc6cf0d94cd48dac21d7f8a834a95f9de47c0fd7`
- Betreff: `fix(materials): bound ZIP inventory and record Week 0 acceptance gaps`
- Status vollständig: `True`; T/U/I: `0/0/4`.
- Upstream: `refs/remotes/origin/feat/c26-week0-acceptance`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c26-week0-acceptance`.
- Lokaler Tracking-SHA: `fc6cf0d94cd48dac21d7f8a834a95f9de47c0fd7`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c26-week0-acceptance`, SHA `fc6cf0d94cd48dac21d7f8a834a95f9de47c0fd7`.
- Backupref: `refs/heads/feat/c26-week0-acceptance`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: unsecured untracked/ignored paths (including empty directories); authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| `!!` | `.ruff_cache/.gitignore` |
| `!!` | `.ruff_cache/0.16.0/` |
| `!!` | `.ruff_cache/CACHEDIR.TAG` |

Zusatzpfade (1): `.ruff_cache/`.

Ignored-Pfade (4): `.ruff_cache/`, `.ruff_cache/.gitignore`, `.ruff_cache/0.16.0/`, `.ruff_cache/CACHEDIR.TAG`.

### 37 · Personal_Assistant-c26a

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26a`
- Branch: `refs/heads/feat/c26a-existing-backend-copy-handoff`
- HEAD / lokaler Branch: `071a327091bfc66cd6ddb5f1541ca2f89e4b0889` / `071a327091bfc66cd6ddb5f1541ca2f89e4b0889`
- Betreff: `Record C26 follow-up review and retention status`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/c26a-existing-backend-copy-handoff`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c26a-existing-backend-copy-handoff`.
- Lokaler Tracking-SHA: `071a327091bfc66cd6ddb5f1541ca2f89e4b0889`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c26a-existing-backend-copy-handoff`, SHA `071a327091bfc66cd6ddb5f1541ca2f89e4b0889`.
- Backupref: `refs/heads/feat/c26a-existing-backend-copy-handoff`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 38 · Personal_Assistant-c26b

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b`
- Branch: `refs/heads/feat/c26b-https`
- HEAD / lokaler Branch: `c36417516cd027322388463c10a2391f7fcb225f` / `c36417516cd027322388463c10a2391f7fcb225f`
- Betreff: `Preserve exact regression failures and reproducible acceptance commands`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/c26b-https`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c26b-https`.
- Lokaler Tracking-SHA: `c36417516cd027322388463c10a2391f7fcb225f`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c26b-https`, SHA `c36417516cd027322388463c10a2391f7fcb225f`.
- Backupref: `refs/heads/feat/c26b-https`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 39 · Personal_Assistant-c26b-vpn

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b-vpn`
- Branch: `refs/heads/feat/c26b-private-vpn-review`
- HEAD / lokaler Branch: `3b91d39195e0d13fe0442d4594b28e431b0f4236` / `3b91d39195e0d13fe0442d4594b28e431b0f4236`
- Betreff: `Merge pull request #145 from rf-data/feat/c26b7-media-last-reviewed`
- Status vollständig: `True`; T/U/I: `5/0/2`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c26b-private-vpn-review`, SHA `c8c06fdb3e45e7bb454b8153bd0efe6f194e8199`.
- Backupref: `refs/heads/feat/c26b-private-vpn-review`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `DIRTY`, `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: tracked changes; unsecured untracked/ignored paths (including empty directories); authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| ` M` | `[private path omitted]` |
| ` M` | `docs/deployment/c26b_validation.md` |
| ` M` | `docs/deployment/https.md` |
| ` M` | `scripts/https_preflight.py` |
| ` M` | `tests/test_https_preflight.py` |
| `!!` | `docs/deployment/c26b_vpn_container.v1.json` |
| `!!` | `docs/deployment/c26b_vpn_e2e.v1.json` |

Ignored-Pfade (2): `docs/deployment/c26b_vpn_container.v1.json`, `docs/deployment/c26b_vpn_e2e.v1.json`.

### 40 · Personal_Assistant-c26b-vpn-final

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b-vpn-final`
- Branch: `DETACHED_HEAD`
- HEAD / lokaler Branch: `d0a58f392530bf4112ef7d7a632c1e5e36e07a20` / `unknown / nicht vorhanden`
- Betreff: `Record paired VPN review PRs and actual role test results`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `unknown / nicht vorhanden`, SHA `unknown / nicht vorhanden`.
- Backupref: `unknown / nicht vorhanden`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `DETACHED_HEAD`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: detached HEAD unsupported for removal; authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 41 · Personal_Assistant-c26b-vpn-review

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b-vpn-review`
- Branch: `refs/heads/review/c26b-private-vpn-validated`
- HEAD / lokaler Branch: `c8c06fdb3e45e7bb454b8153bd0efe6f194e8199` / `c8c06fdb3e45e7bb454b8153bd0efe6f194e8199`
- Betreff: `Harden private VPN profile and record current HTTPS rollout gates`
- Status vollständig: `True`; T/U/I: `1/0/0`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/review/c26b-private-vpn-validated`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/review/c26b-private-vpn-validated`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `DIRTY`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: tracked changes; authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| ` M` | `docs/deployment/c26b_validation.md` |

### 42 · Personal_Assistant-c26b1

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b1`
- Branch: `refs/heads/feat/c26b1-worker-image-entrypoints`
- HEAD / lokaler Branch: `86ad27659212fe6b97d7589f8c5f0519cb84aef0` / `86ad27659212fe6b97d7589f8c5f0519cb84aef0`
- Betreff: `fix(worker): include and smoke-test C26 CLI entrypoints`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/c26b1-worker-image-entrypoints`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c26b1-worker-image-entrypoints`.
- Lokaler Tracking-SHA: `86ad27659212fe6b97d7589f8c5f0519cb84aef0`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c26b1-worker-image-entrypoints`, SHA `86ad27659212fe6b97d7589f8c5f0519cb84aef0`.
- Backupref: `refs/heads/feat/c26b1-worker-image-entrypoints`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 43 · Personal_Assistant-c26b2

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b2`
- Branch: `refs/heads/feat/c26b2-single-html-pilot`
- HEAD / lokaler Branch: `16601e7bbffe8ecc9fb2e9c1a13b454df0281e65` / `16601e7bbffe8ecc9fb2e9c1a13b454df0281e65`
- Betreff: `feat(c26): prepare a bounded HTML pilot with explicit mounted output grants`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/c26b2-single-html-pilot`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c26b2-single-html-pilot`.
- Lokaler Tracking-SHA: `16601e7bbffe8ecc9fb2e9c1a13b454df0281e65`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c26b2-single-html-pilot`, SHA `16601e7bbffe8ecc9fb2e9c1a13b454df0281e65`.
- Backupref: `refs/heads/feat/c26b2-single-html-pilot`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 44 · Personal_Assistant-c26b3

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b3`
- Branch: `refs/heads/feat/c26b3-admin-bootstrap`
- HEAD / lokaler Branch: `505bea92086746242e357675e43e51d285d41ed0` / `505bea92086746242e357675e43e51d285d41ed0`
- Betreff: `fix(c26): bootstrap private pilot roots for explicit worker identity`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/c26b3-admin-bootstrap`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c26b3-admin-bootstrap`.
- Lokaler Tracking-SHA: `505bea92086746242e357675e43e51d285d41ed0`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c26b3-admin-bootstrap`, SHA `505bea92086746242e357675e43e51d285d41ed0`.
- Backupref: `refs/heads/feat/c26b3-admin-bootstrap`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 45 · Personal_Assistant-c26b4

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b4`
- Branch: `refs/heads/feat/c26b4-week0-batch-pilot`
- HEAD / lokaler Branch: `05d46133eefcb1d7da37e2867b4e8cc30cb7633c` / `05d46133eefcb1d7da37e2867b4e8cc30cb7633c`
- Betreff: `docs(c26): keep administrative bundle checks active under optimized Python`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/c26b4-week0-batch-pilot`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c26b4-week0-batch-pilot`.
- Lokaler Tracking-SHA: `05d46133eefcb1d7da37e2867b4e8cc30cb7633c`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c26b4-week0-batch-pilot`, SHA `05d46133eefcb1d7da37e2867b4e8cc30cb7633c`.
- Backupref: `refs/heads/feat/c26b4-week0-batch-pilot`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 46 · Personal_Assistant-c26b5

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b5`
- Branch: `refs/heads/feat/c26b5-multiformat-transcripts`
- HEAD / lokaler Branch: `81897b7c06d23841f4edbbb3e91df3854221deb2` / `81897b7c06d23841f4edbbb3e91df3854221deb2`
- Betreff: `C26-B5: bind offline official transcripts to Week-0 lectures`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/c26b5-multiformat-transcripts`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c26b5-multiformat-transcripts`.
- Lokaler Tracking-SHA: `81897b7c06d23841f4edbbb3e91df3854221deb2`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c26b5-multiformat-transcripts`, SHA `81897b7c06d23841f4edbbb3e91df3854221deb2`.
- Backupref: `refs/heads/feat/c26b5-multiformat-transcripts`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 47 · Personal_Assistant-c26b5-fix01

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b5-fix01`
- Branch: `refs/heads/fix/c26b5-knowledge-identities`
- HEAD / lokaler Branch: `78a51a9312aafb0483abaf7f97f379ebcf96a315` / `78a51a9312aafb0483abaf7f97f379ebcf96a315`
- Betreff: `fix(knowledge): resolve duplicate identity arguments and setup failures`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/fix/c26b5-knowledge-identities`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/fix/c26b5-knowledge-identities`.
- Lokaler Tracking-SHA: `78a51a9312aafb0483abaf7f97f379ebcf96a315`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/fix/c26b5-knowledge-identities`, SHA `78a51a9312aafb0483abaf7f97f379ebcf96a315`.
- Backupref: `refs/heads/fix/c26b5-knowledge-identities`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 48 · Personal_Assistant-c26b6

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b6`
- Branch: `refs/heads/feat/c26b6-code-zip-import`
- HEAD / lokaler Branch: `6786b5d67b31125895d94af7b763a1002aeeea7d` / `6786b5d67b31125895d94af7b763a1002aeeea7d`
- Betreff: `Merge pull request #142 from rf-data/feat/c26b5-multiformat-transcripts`
- Status vollständig: `True`; T/U/I: `11/0/0`.
- Upstream: `refs/remotes/origin/master`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/master`.
- Lokaler Tracking-SHA: `e68275205fefb7a5f6db42bc45060e505bfcefb5`; ahead/behind: `0/29`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c26b6-code-zip-import`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/feat/c26b6-code-zip-import`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `DIRTY`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: tracked changes; authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| `A ` | `docs/deployment/c26a/code_zip_pilot.md` |
| `A ` | `docs/deployment/c26a/code_zip_validation.md` |
| `M ` | `docs/deployment/c26a/multiformat_pilot.md` |
| `M ` | `scripts/cs50_batch.py` |
| `M ` | `src/tools_materials/batch.py` |
| `A ` | `src/tools_materials/code_discovery.py` |
| `A ` | `src/tools_materials/code_import.py` |
| `A ` | `src/tools_materials/code_structure.py` |
| `A ` | `src/tools_materials/code_zip.py` |
| `M ` | `src/tools_materials/processing.py` |
| `A ` | `tests/test_cs50_code_zip.py` |

### 49 · Personal_Assistant-c26b6-compat

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b6-compat`
- Branch: `DETACHED_HEAD`
- HEAD / lokaler Branch: `da9b77db0815f0c2ab65a3e819df17200e3a3897` / `unknown / nicht vorhanden`
- Betreff: `Merge pull request #151 from rf-data/docs/c26b6-rollout-readiness`
- Status vollständig: `True`; T/U/I: `9/10/2`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `unknown / nicht vorhanden`, SHA `unknown / nicht vorhanden`.
- Backupref: `unknown / nicht vorhanden`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `DIRTY`, `UNTRACKED_OR_IGNORED_RISK`, `DETACHED_HEAD`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: tracked changes; unsecured untracked/ignored paths (including empty directories); detached HEAD unsupported for removal; authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| ` M` | `docs/cs50/contracts/material_quality.md` |
| ` M` | `scripts/cs50_week.py` |
| ` M` | `src/model_materials/quality.py` |
| ` M` | `src/model_materials/week.py` |
| ` M` | `src/tools_lecture/material_handoff.py` |
| ` M` | `src/tools_materials/mapping.py` |
| ` M` | `src/tools_materials/quality.py` |
| ` M` | `src/tools_materials/transcripts.py` |
| ` M` | `src/tools_materials/week.py` |
| `??` | `docs/cs50/contracts/html_aggregation_v2.md` |
| `??` | `docs/deployment/c26a/html_aggregation_validation.md` |
| `??` | `scripts/cs50_course.py` |
| `??` | `src/model_materials/course.py` |
| `??` | `src/tools_materials/course.py` |
| `??` | `src/tools_materials/html_projection.py` |
| `??` | `src/tools_materials/profiles.py` |
| `??` | `src/tools_materials/quality_projection.py` |
| `??` | `tests/test_cs50_course.py` |
| `??` | `tests/test_cs50_html_projection.py` |
| `!!` | `docs/deployment/c26a/html_aggregation_validation.v1.json` |
| `!!` | `tests/fixtures/material_quality/html_projection_baseline.v1.json` |

Zusatzpfade (10): `docs/cs50/contracts/html_aggregation_v2.md`, `docs/deployment/c26a/html_aggregation_validation.md`, `scripts/cs50_course.py`, `src/model_materials/course.py`, `src/tools_materials/course.py`, `src/tools_materials/html_projection.py`, `src/tools_materials/profiles.py`, `src/tools_materials/quality_projection.py`, `tests/test_cs50_course.py`, `tests/test_cs50_html_projection.py`.

Ignored-Pfade (2): `docs/deployment/c26a/html_aggregation_validation.v1.json`, `tests/fixtures/material_quality/html_projection_baseline.v1.json`.

### 50 · Personal_Assistant-c26b6-planning

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b6-planning`
- Branch: `refs/heads/feat/c26b6-course-planning`
- HEAD / lokaler Branch: `5d4c12bb3ea3acb69bf737e1466acfb12f5830bb` / `5d4c12bb3ea3acb69bf737e1466acfb12f5830bb`
- Betreff: `feat(c26b6): add profiled multi-week planning and offline preflight`
- Status vollständig: `True`; T/U/I: `0/0/7`.
- Upstream: `refs/remotes/origin/feat/c26b6-course-planning`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c26b6-course-planning`.
- Lokaler Tracking-SHA: `5d4c12bb3ea3acb69bf737e1466acfb12f5830bb`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c26b6-course-planning`, SHA `5d4c12bb3ea3acb69bf737e1466acfb12f5830bb`.
- Backupref: `refs/heads/feat/c26b6-course-planning`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: unsecured untracked/ignored paths (including empty directories); authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| `!!` | `scripts/__pycache__/` |
| `!!` | `src/model_discovery/__pycache__/` |
| `!!` | `src/model_materials/__pycache__/` |
| `!!` | `src/model_transcribe/__pycache__/` |
| `!!` | `src/tools_lecture/__pycache__/` |
| `!!` | `src/tools_materials/__pycache__/` |
| `!!` | `src/tools_transcribe/__pycache__/` |

Ignored-Pfade (7): `scripts/__pycache__/`, `src/model_discovery/__pycache__/`, `src/model_materials/__pycache__/`, `src/model_transcribe/__pycache__/`, `src/tools_lecture/__pycache__/`, `src/tools_materials/__pycache__/`, `src/tools_transcribe/__pycache__/`.

### 51 · Personal_Assistant-c26b6-readiness

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b6-readiness`
- Branch: `refs/heads/docs/c26b6-rollout-readiness`
- HEAD / lokaler Branch: `0bb9a5b89e9ab691d1614c0d07590aa53e08c75c` / `0bb9a5b89e9ab691d1614c0d07590aa53e08c75c`
- Betreff: `docs(c26b6): verify prerequisites and design multi-course rollout`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/docs/c26b6-rollout-readiness`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/docs/c26b6-rollout-readiness`.
- Lokaler Tracking-SHA: `0bb9a5b89e9ab691d1614c0d07590aa53e08c75c`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/docs/c26b6-rollout-readiness`, SHA `0bb9a5b89e9ab691d1614c0d07590aa53e08c75c`.
- Backupref: `refs/heads/docs/c26b6-rollout-readiness`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 52 · Personal_Assistant-c26b6-review

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b6-review`
- Branch: `refs/heads/feat/c26b6-code-zip-reviewed`
- HEAD / lokaler Branch: `ef0aa1cf59874b6ac461adf2008bad5d0eaf63e8` / `ef0aa1cf59874b6ac461adf2008bad5d0eaf63e8`
- Betreff: `feat(cs50): add bounded Python and ZIP source-material import`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/c26b6-code-zip-reviewed`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c26b6-code-zip-reviewed`.
- Lokaler Tracking-SHA: `ef0aa1cf59874b6ac461adf2008bad5d0eaf63e8`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c26b6-code-zip-reviewed`, SHA `ef0aa1cf59874b6ac461adf2008bad5d0eaf63e8`.
- Backupref: `refs/heads/feat/c26b6-code-zip-reviewed`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 53 · Personal_Assistant-c26b7

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b7`
- Branch: `refs/heads/feat/c26b7-media-last`
- HEAD / lokaler Branch: `6786b5d67b31125895d94af7b763a1002aeeea7d` / `6786b5d67b31125895d94af7b763a1002aeeea7d`
- Betreff: `Merge pull request #142 from rf-data/feat/c26b5-multiformat-transcripts`
- Status vollständig: `True`; T/U/I: `8/0/0`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c26b7-media-last`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/feat/c26b7-media-last`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `DIRTY`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: tracked changes; authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| `A ` | `docs/deployment/c26a/media_last_pilot.md` |
| `A ` | `docs/deployment/c26a/media_last_validation.md` |
| `M ` | `docs/deployment/c26a/multiformat_pilot.md` |
| `M ` | `scripts/cs50_batch.py` |
| `A ` | `src/model_materials/media_plan.py` |
| `A ` | `src/tools_materials/media_evidence.py` |
| `A ` | `src/tools_materials/media_plan.py` |
| `A ` | `tests/test_cs50_media_plan.py` |

### 54 · Personal_Assistant-c26b7-review

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b7-review`
- Branch: `refs/heads/feat/c26b7-media-last-reviewed`
- HEAD / lokaler Branch: `cba3302261be5b5cb0a36fc482250a5268b8ad44` / `cba3302261be5b5cb0a36fc482250a5268b8ad44`
- Betreff: `feat(cs50): add media-last fallback planning and remaining material adapters`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c26b7-media-last-reviewed`, SHA `cba3302261be5b5cb0a36fc482250a5268b8ad44`.
- Backupref: `refs/heads/feat/c26b7-media-last-reviewed`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 55 · Personal_Assistant-c26d

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26d`
- Branch: `refs/heads/feat/c26d-operation-gate-v2`
- HEAD / lokaler Branch: `8b0ba2d4ab5d0cd6fc8dfa69783276efd929666f` / `8b0ba2d4ab5d0cd6fc8dfa69783276efd929666f`
- Betreff: `docs(c26d): record persistent-root and local transport validation`
- Status vollständig: `True`; T/U/I: `0/0/4`.
- Upstream: `refs/remotes/origin/feat/c26d-operation-gate-v2`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c26d-operation-gate-v2`.
- Lokaler Tracking-SHA: `8b0ba2d4ab5d0cd6fc8dfa69783276efd929666f`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c26d-operation-gate-v2`, SHA `8b0ba2d4ab5d0cd6fc8dfa69783276efd929666f`.
- Backupref: `refs/heads/feat/c26d-operation-gate-v2`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `PROTECTED_ACTIVE`, `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: explicit/current-task protection; unsecured untracked/ignored paths (including empty directories); authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: [#161](https://github.com/rf-data/Personal_Assistant/pull/161), `open`, merged=False, gleicher Branch; API-head `8b0ba2d4ab5d0cd6fc8dfa69783276efd929666f`.

| Gitstatus | Pfad |
| --- | --- |
| `!!` | `.ruff_cache/.gitignore` |
| `!!` | `.ruff_cache/0.16.0/` |
| `!!` | `.ruff_cache/CACHEDIR.TAG` |

Zusatzpfade (1): `.ruff_cache/`.

Ignored-Pfade (4): `.ruff_cache/`, `.ruff_cache/.gitignore`, `.ruff_cache/0.16.0/`, `.ruff_cache/CACHEDIR.TAG`.

### 56 · Personal_Assistant-c26e

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26e`
- Branch: `refs/heads/feat/c26e-authenticated-runtime-collector`
- HEAD / lokaler Branch: `28e9a608d74270278cf037e35957d0bae08d50b2` / `28e9a608d74270278cf037e35957d0bae08d50b2`
- Betreff: `fix(c26e): reject stale HTTP caches and retain freshness limits`
- Status vollständig: `True`; T/U/I: `0/0/4`.
- Upstream: `refs/remotes/origin/feat/c26e-authenticated-runtime-collector`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c26e-authenticated-runtime-collector`.
- Lokaler Tracking-SHA: `28e9a608d74270278cf037e35957d0bae08d50b2`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c26e-authenticated-runtime-collector`, SHA `28e9a608d74270278cf037e35957d0bae08d50b2`.
- Backupref: `refs/heads/feat/c26e-authenticated-runtime-collector`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `PROTECTED_ACTIVE`, `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: explicit/current-task protection; unsecured untracked/ignored paths (including empty directories); authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: [#162](https://github.com/rf-data/Personal_Assistant/pull/162), `open`, merged=False, gleicher Branch; API-head `28e9a608d74270278cf037e35957d0bae08d50b2`.

| Gitstatus | Pfad |
| --- | --- |
| `!!` | `.ruff_cache/.gitignore` |
| `!!` | `.ruff_cache/0.16.0/` |
| `!!` | `.ruff_cache/CACHEDIR.TAG` |

Zusatzpfade (1): `.ruff_cache/`.

Ignored-Pfade (4): `.ruff_cache/`, `.ruff_cache/.gitignore`, `.ruff_cache/0.16.0/`, `.ruff_cache/CACHEDIR.TAG`.

### 57 · Personal_Assistant-c26f

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26f`
- Branch: `refs/heads/feat/c26f-independent-coordinator`
- HEAD / lokaler Branch: `7ffb4ed6fd4d8433edf36fb4851a382b9b9c595d` / `7ffb4ed6fd4d8433edf36fb4851a382b9b9c595d`
- Betreff: `feat(c26f): orchestrate offline deployment with independent grants and CAS fencing`
- Status vollständig: `True`; T/U/I: `0/0/4`.
- Upstream: `refs/remotes/origin/feat/c26f-independent-coordinator`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c26f-independent-coordinator`.
- Lokaler Tracking-SHA: `7ffb4ed6fd4d8433edf36fb4851a382b9b9c595d`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c26f-independent-coordinator`, SHA `7ffb4ed6fd4d8433edf36fb4851a382b9b9c595d`.
- Backupref: `refs/heads/feat/c26f-independent-coordinator`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `PROTECTED_ACTIVE`, `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: explicit/current-task protection; unsecured untracked/ignored paths (including empty directories); authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: [#163](https://github.com/rf-data/Personal_Assistant/pull/163), `open`, merged=False, gleicher Branch; API-head `7ffb4ed6fd4d8433edf36fb4851a382b9b9c595d`.

| Gitstatus | Pfad |
| --- | --- |
| `!!` | `.ruff_cache/.gitignore` |
| `!!` | `.ruff_cache/0.16.0/` |
| `!!` | `.ruff_cache/CACHEDIR.TAG` |

Zusatzpfade (1): `.ruff_cache/`.

Ignored-Pfade (4): `.ruff_cache/`, `.ruff_cache/.gitignore`, `.ruff_cache/0.16.0/`, `.ruff_cache/CACHEDIR.TAG`.

### 58 · Personal_Assistant-c26g

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26g`
- Branch: `refs/heads/feat/c26g-deployment-readiness`
- HEAD / lokaler Branch: `778367396cd52526eca59edd41c2367f5e43b897` / `778367396cd52526eca59edd41c2367f5e43b897`
- Betreff: `fix(maint04b): restore workflow schema boundary`
- Status vollständig: `True`; T/U/I: `10/0/18`.
- Upstream: `refs/remotes/origin/feat/c26g-deployment-readiness`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c26g-deployment-readiness`.
- Lokaler Tracking-SHA: `778367396cd52526eca59edd41c2367f5e43b897`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c26g-deployment-readiness`, SHA `778367396cd52526eca59edd41c2367f5e43b897`.
- Backupref: `refs/heads/feat/c26g-deployment-readiness`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `PROTECTED_ACTIVE`, `DIRTY`, `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: explicit/current-task protection; tracked changes; unsecured untracked/ignored paths (including empty directories); authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| `A ` | `deployment/c26g.staging.controller.json.example` |
| `A ` | `docs/deployment/c26g_go_no_go.md` |
| `A ` | `docs/deployment/c26g_integration_validation.md` |
| `A ` | `docs/deployment/c26g_operator_decisions.md` |
| `A ` | `docs/deployment/c26g_readiness_matrix.md` |
| `A ` | `docs/deployment/c26g_runbook.md` |
| `A ` | `scripts/c26g_offline_validation.py` |
| `A ` | `scripts/c26g_preflight.py` |
| `A ` | `tests/test_c26g_readiness.py` |
| `A ` | `tests/test_c26g_restore.py` |
| `!!` | `.ruff_cache/.gitignore` |
| `!!` | `.ruff_cache/0.16.0/` |
| `!!` | `.ruff_cache/CACHEDIR.TAG` |
| `!!` | `[private path omitted]` |
| `!!` | `scripts/__pycache__/` |
| `!!` | `src/__pycache__/` |
| `!!` | `src/content_store/__pycache__/` |
| `!!` | `src/core/__pycache__/` |
| `!!` | `src/job_control/__pycache__/` |
| `!!` | `src/model_discovery/__pycache__/` |
| `!!` | `src/model_lecture/__pycache__/` |
| `!!` | `src/model_materials/__pycache__/` |
| `!!` | `src/model_transcribe/__pycache__/` |
| `!!` | `src/tools_lecture/__pycache__/` |
| `!!` | `src/tools_materials/__pycache__/` |
| `!!` | `src/tools_transcribe/__pycache__/` |
| `!!` | `tests/__pycache__/` |

Zusatzpfade (1): `.ruff_cache/`.

Ignored-Pfade (18): `.ruff_cache/`, `.ruff_cache/.gitignore`, `.ruff_cache/0.16.0/`, `.ruff_cache/CACHEDIR.TAG`, `[private path omitted]`, `scripts/__pycache__/`, `src/__pycache__/`, `src/content_store/__pycache__/`, `src/core/__pycache__/`, `src/job_control/__pycache__/`, `src/model_discovery/__pycache__/`, `src/model_lecture/__pycache__/`, `src/model_materials/__pycache__/`, `src/model_transcribe/__pycache__/`, `src/tools_lecture/__pycache__/`, `src/tools_materials/__pycache__/`, `src/tools_transcribe/__pycache__/`, `tests/__pycache__/`.

### 59 · Personal_Assistant-c26h

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26h`
- Branch: `refs/heads/feat/c26h-controlled-integration`
- HEAD / lokaler Branch: `778367396cd52526eca59edd41c2367f5e43b897` / `778367396cd52526eca59edd41c2367f5e43b897`
- Betreff: `fix(maint04b): restore workflow schema boundary`
- Status vollständig: `True`; T/U/I: `90/0/37`.
- Upstream: `refs/remotes/origin/feat/c26h-controlled-integration`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/c26h-controlled-integration`.
- Lokaler Tracking-SHA: `778367396cd52526eca59edd41c2367f5e43b897`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c26h-controlled-integration`, SHA `778367396cd52526eca59edd41c2367f5e43b897`.
- Backupref: `refs/heads/feat/c26h-controlled-integration`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `PROTECTED_ACTIVE`, `DIRTY`, `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: explicit/current-task protection; tracked changes; unsecured untracked/ignored paths (including empty directories); authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| `M ` | `deployment/Dockerfile` |
| `M ` | `deployment/Dockerfile.dockerignore` |
| `A ` | `deployment/c26-runtime.controller.json.example` |
| `A ` | `deployment/c26-runtime.limits.json.example` |
| `A ` | `deployment/c26g.staging.controller.json.example` |
| `A ` | `deployment/c26h.staging.compose.yaml` |
| `A ` | `deployment/c26h.staging.content.json.example` |
| `A ` | `deployment/c26h.staging.review.json.example` |
| `A ` | `deployment/c26h.staging.search.json.example` |
| `A ` | `deployment/c26h.staging.ui.compose.yaml` |
| `A ` | `deployment/coolify.runtime-bootstrap.compose.yaml` |
| `M ` | `docker/DockerFile.worker` |
| `M ` | `docker/DockerFile.worker.dockerignore` |
| `M ` | `docs/deployment/architecture.md` |
| `A ` | `docs/deployment/c26_gate_validation.md` |
| `A ` | `docs/deployment/c26_runtime/README.md` |
| `A ` | `docs/deployment/c26_runtime/coolify_compatibility.md` |
| `A ` | `docs/deployment/c26_runtime/coolify_driver_plan.md` |
| `A ` | `docs/deployment/c26_runtime/deployment_trigger_audit.md` |
| `A ` | `docs/deployment/c26_runtime/diagnostics.md` |
| `A ` | `docs/deployment/c26_runtime/draft_consolidation_report.md` |
| `A ` | `docs/deployment/c26_runtime/driver_contract.md` |
| `A ` | `docs/deployment/c26_runtime/integration_matrix.md` |
| `A ` | `docs/deployment/c26_runtime/operator_binding_check.md` |
| `A ` | `docs/deployment/c26_runtime/operator_checks.md` |
| `A ` | `docs/deployment/c26_runtime/resource_matrix.md` |
| `A ` | `docs/deployment/c26_runtime/resources.md` |
| `A ` | `docs/deployment/c26_runtime/rollout.md` |
| `A ` | `docs/deployment/c26_runtime/runtime_configuration.md` |
| `A ` | `docs/deployment/c26_runtime/runtime_observer_report.md` |
| `A ` | `docs/deployment/c26_runtime/source_assessment.md` |
| `M ` | `docs/deployment/c26b_validation.md` |
| `A ` | `docs/deployment/c26d_gate_v2.md` |
| `A ` | `docs/deployment/c26e_runtime_collector.md` |
| `A ` | `docs/deployment/c26f_deployment_coordinator.md` |
| `A ` | `docs/deployment/c26g_go_no_go.md` |
| `A ` | `docs/deployment/c26g_integration_validation.md` |
| `A ` | `docs/deployment/c26g_operator_decisions.md` |
| `A ` | `docs/deployment/c26g_readiness_matrix.md` |
| `A ` | `docs/deployment/c26g_runbook.md` |
| `A ` | `docs/deployment/c26h_integration_inventory.md` |
| `A ` | `docs/deployment/c26h_integration_plan.md` |
| `A ` | `docs/deployment/c26h_remaining_gates.md` |
| `A ` | `docs/deployment/c26h_runtime_bootstrap.md` |
| `A ` | `docs/deployment/c26h_staging_runbook.md` |
| `A ` | `docs/deployment/c26h_validation.md` |
| `M ` | `docs/deployment/configuration.md` |
| `A ` | `docs/deployment/deployment_gate.md` |
| `M ` | `docs/deployment/https.md` |
| `M ` | `docs/deployment/operations.md` |
| `M ` | `docs/job_control/contract.v1.json` |
| `A ` | `scripts/c26_runtime_preflight.py` |
| `A ` | `scripts/c26g_offline_validation.py` |
| `A ` | `scripts/c26g_preflight.py` |
| `A ` | `scripts/c26h_offline_validation.py` |
| `A ` | `scripts/c26h_preflight.py` |
| `M ` | `scripts/deployment.py` |
| `A ` | `scripts/deployment_gate.py` |
| `M ` | `scripts/worker_image_smoke.py` |
| `M ` | `src/job_control/controller.py` |
| `A ` | `src/job_control/coolify_observer.py` |
| `A ` | `src/job_control/coolify_readiness.py` |
| `A ` | `src/job_control/coordinator_contracts.py` |
| `A ` | `src/job_control/coordinator_state.py` |
| `A ` | `src/job_control/deployment_coordinator.py` |
| `A ` | `src/job_control/deployment_gate.py` |
| `A ` | `src/job_control/deployment_scope.py` |
| `M ` | `src/job_control/executor.py` |
| `M ` | `src/job_control/models.py` |
| `M ` | `src/job_control/operations.py` |
| `A ` | `src/job_control/runtime_collector.py` |
| `M ` | `src/job_control/store.py` |
| `A ` | `[private path omitted]` |
| `M ` | `tests/helpers/job_control_probe.py` |
| `A ` | `tests/test_c26_runtime_bootstrap.py` |
| `A ` | `tests/test_c26_runtime_preflight.py` |
| `A ` | `tests/test_c26g_readiness.py` |
| `A ` | `tests/test_c26g_restore.py` |
| `A ` | `tests/test_c26h_compose.py` |
| `A ` | `tests/test_c26h_integration.py` |
| `A ` | `tests/test_c26h_processes.py` |
| `A ` | `tests/test_c26h_runtime.py` |
| `A ` | `tests/test_coolify_observer.py` |
| `A ` | `tests/test_coolify_readiness.py` |
| `A ` | `tests/test_coordinator_contracts.py` |
| `A ` | `tests/test_deployment_coordinator.py` |
| `A ` | `tests/test_deployment_gate.py` |
| `A ` | `tests/test_deployment_gate_v2.py` |
| `M ` | `tests/test_deployment_transport.py` |
| `A ` | `tests/test_runtime_collector.py` |
| `!!` | `.ruff_cache/.gitignore` |
| `!!` | `.ruff_cache/0.16.0/` |
| `!!` | `.ruff_cache/CACHEDIR.TAG` |
| `!!` | `docs/deployment/c26_gate_validation.v1.json` |
| `!!` | `docs/deployment/c26_runtime/collector_build_receipt.v1.schema.json` |
| `!!` | `docs/deployment/c26_runtime/collector_capture.v1.schema.json` |
| `!!` | `docs/deployment/c26_runtime/collector_envelope.v1.schema.json` |
| `!!` | `docs/deployment/c26_runtime/collector_target.v1.schema.json` |
| `!!` | `docs/deployment/c26_runtime/coolify_resource_binding.v1.json` |
| `!!` | `docs/deployment/c26_runtime/coordinator_anchor.v1.schema.json` |
| `!!` | `docs/deployment/c26_runtime/coordinator_challenge.v1.schema.json` |
| `!!` | `docs/deployment/c26_runtime/coordinator_driver_receipt.v1.schema.json` |
| `!!` | `docs/deployment/c26_runtime/coordinator_enrollment.v1.schema.json` |
| `!!` | `docs/deployment/c26_runtime/coordinator_grant.v1.schema.json` |
| `!!` | `docs/deployment/c26_runtime/coordinator_integration.v1.schema.json` |
| `!!` | `docs/deployment/c26_runtime/deployment_trigger_audit.v1.json` |
| `!!` | `docs/deployment/c26_runtime/gate_approval.v2.schema.json` |
| `!!` | `docs/deployment/c26_runtime/gate_journal_event.v2.schema.json` |
| `!!` | `docs/deployment/c26_runtime/gate_observation.v2.schema.json` |
| `!!` | `docs/deployment/c26_runtime/gate_plan.v2.schema.json` |
| `!!` | `docs/deployment/c26_runtime/host_metadata.v1.schema.json` |
| `!!` | `docs/deployment/c26_runtime/observer_consolidation_validation.v1.json` |
| `!!` | `docs/deployment/c26_runtime/operator_inventory.v1.json` |
| `!!` | `docs/deployment/c26_runtime/resource_binding_validation.v1.json` |
| `!!` | `docs/deployment/c26_runtime/runtime_configuration_validation.v1.json` |
| `!!` | `docs/deployment/c26_runtime/runtime_diagnostics.v1.json` |
| `!!` | `docs/deployment/c26_runtime/runtime_operation.v2.schema.json` |
| `!!` | `docs/deployment/c26_runtime/runtime_scope.v1.schema.json` |
| `!!` | `docs/deployment/c26_runtime/technical_sources.v1.json` |
| `!!` | `docs/deployment/c26_runtime/validation.v1.json` |
| `!!` | `docs/deployment/c26d_validation.v2.json` |
| `!!` | `docs/deployment/c26e_validation.v1.json` |
| `!!` | `docs/deployment/c26f_validation.v1.json` |
| `!!` | `docs/deployment/c26h_source_provenance.json` |
| `!!` | `scripts/__pycache__/` |
| `!!` | `src/core/__pycache__/` |

Zusatzpfade (4): `.agents/`, `.aws/`, `.codex/`, `.ruff_cache/`.

Ignored-Pfade (37): `.ruff_cache/`, `.ruff_cache/.gitignore`, `.ruff_cache/0.16.0/`, `.ruff_cache/CACHEDIR.TAG`, `docs/deployment/c26_gate_validation.v1.json`, `docs/deployment/c26_runtime/collector_build_receipt.v1.schema.json`, `docs/deployment/c26_runtime/collector_capture.v1.schema.json`, `docs/deployment/c26_runtime/collector_envelope.v1.schema.json`, `docs/deployment/c26_runtime/collector_target.v1.schema.json`, `docs/deployment/c26_runtime/coolify_resource_binding.v1.json`, `docs/deployment/c26_runtime/coordinator_anchor.v1.schema.json`, `docs/deployment/c26_runtime/coordinator_challenge.v1.schema.json`, `docs/deployment/c26_runtime/coordinator_driver_receipt.v1.schema.json`, `docs/deployment/c26_runtime/coordinator_enrollment.v1.schema.json`, `docs/deployment/c26_runtime/coordinator_grant.v1.schema.json`, `docs/deployment/c26_runtime/coordinator_integration.v1.schema.json`, `docs/deployment/c26_runtime/deployment_trigger_audit.v1.json`, `docs/deployment/c26_runtime/gate_approval.v2.schema.json`, `docs/deployment/c26_runtime/gate_journal_event.v2.schema.json`, `docs/deployment/c26_runtime/gate_observation.v2.schema.json`, `docs/deployment/c26_runtime/gate_plan.v2.schema.json`, `docs/deployment/c26_runtime/host_metadata.v1.schema.json`, `docs/deployment/c26_runtime/observer_consolidation_validation.v1.json`, `docs/deployment/c26_runtime/operator_inventory.v1.json`, `docs/deployment/c26_runtime/resource_binding_validation.v1.json`, `docs/deployment/c26_runtime/runtime_configuration_validation.v1.json`, `docs/deployment/c26_runtime/runtime_diagnostics.v1.json`, `docs/deployment/c26_runtime/runtime_operation.v2.schema.json`, `docs/deployment/c26_runtime/runtime_scope.v1.schema.json`, `docs/deployment/c26_runtime/technical_sources.v1.json`, `docs/deployment/c26_runtime/validation.v1.json`, `docs/deployment/c26d_validation.v2.json`, `docs/deployment/c26e_validation.v1.json`, `docs/deployment/c26f_validation.v1.json`, `docs/deployment/c26h_source_provenance.json`, `scripts/__pycache__/`, `src/core/__pycache__/`.

### 60 · Personal_Assistant-c27-review

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c27-review`
- Branch: `refs/heads/fix/c27-acceptance-exports`
- HEAD / lokaler Branch: `a0d3ebf7f64d44dd843f1848e70dc70a3a3af835` / `a0d3ebf7f64d44dd843f1848e70dc70a3a3af835`
- Betreff: `fix(c27): clarify cited evidence and mock excerpts, verify printable exports`
- Status vollständig: `True`; T/U/I: `0/0/4`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/fix/c27-acceptance-exports`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/fix/c27-acceptance-exports`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `PROTECTED_ACTIVE`, `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: explicit/current-task protection; unsecured untracked/ignored paths (including empty directories); authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: [#158](https://github.com/rf-data/Personal_Assistant/pull/158), `open`, merged=False, gleicher HEAD, anderer Branch; API-head `a0d3ebf7f64d44dd843f1848e70dc70a3a3af835`.

| Gitstatus | Pfad |
| --- | --- |
| `!!` | `.ruff_cache/.gitignore` |
| `!!` | `.ruff_cache/0.16.0/` |
| `!!` | `.ruff_cache/CACHEDIR.TAG` |

Zusatzpfade (1): `.ruff_cache/`.

Ignored-Pfade (4): `.ruff_cache/`, `.ruff_cache/.gitignore`, `.ruff_cache/0.16.0/`, `.ruff_cache/CACHEDIR.TAG`.

### 61 · Personal_Assistant-c27b

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c27b`
- Branch: `refs/heads/feat/c27b-legacy-catalog`
- HEAD / lokaler Branch: `117aa8411f1b516e75d97a43c177ff13a2df57d5` / `117aa8411f1b516e75d97a43c177ff13a2df57d5`
- Betreff: `feat(c27b): register evidenced legacy lecture sources with streaming inventory`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c27b-legacy-catalog`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/feat/c27b-legacy-catalog`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 62 · Personal_Assistant-c27c

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c27c`
- Branch: `refs/heads/feat/c27c-hierarchical-summary`
- HEAD / lokaler Branch: `249379f03bdafa1390d723c39dc1302ec2e533e2` / `249379f03bdafa1390d723c39dc1302ec2e533e2`
- Betreff: `feat(c27c): add bounded hierarchical summaries with original evidence and recovery`
- Status vollständig: `True`; T/U/I: `0/0/4`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/c27c-hierarchical-summary`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/feat/c27c-hierarchical-summary`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: unsecured untracked/ignored paths (including empty directories); authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| `!!` | `.ruff_cache/.gitignore` |
| `!!` | `.ruff_cache/0.16.0/` |
| `!!` | `.ruff_cache/CACHEDIR.TAG` |

Zusatzpfade (1): `.ruff_cache/`.

Ignored-Pfade (4): `.ruff_cache/`, `.ruff_cache/.gitignore`, `.ruff_cache/0.16.0/`, `.ruff_cache/CACHEDIR.TAG`.

### 63 · Personal_Assistant-completion-audit

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-completion-audit`
- Branch: `refs/heads/docs/cs50-completion-audit`
- HEAD / lokaler Branch: `571874524b8b976b68f78668a4274896629229ec` / `571874524b8b976b68f78668a4274896629229ec`
- Betreff: `Merge pull request #25 from rf-data/fix/knowledge-transcript-metadata-contract`
- Status vollständig: `True`; T/U/I: `0/2/0`.
- Upstream: `refs/remotes/origin/master`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/master`.
- Lokaler Tracking-SHA: `e68275205fefb7a5f6db42bc45060e505bfcefb5`; ahead/behind: `0/240`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/docs/cs50-completion-audit`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/docs/cs50-completion-audit`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: unsecured untracked/ignored paths (including empty directories); authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| `??` | `docs/cs50_pipeline_completion_audit.md` |
| `??` | `docs/cs50_pipeline_completion_plan.md` |

Zusatzpfade (2): `docs/cs50_pipeline_completion_audit.md`, `docs/cs50_pipeline_completion_plan.md`.

### 64 · Personal_Assistant-cs50-real01

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-cs50-real01`
- Branch: `refs/heads/feat/cs50-real01-material-pilot`
- HEAD / lokaler Branch: `778367396cd52526eca59edd41c2367f5e43b897` / `778367396cd52526eca59edd41c2367f5e43b897`
- Betreff: `fix(maint04b): restore workflow schema boundary`
- Status vollständig: `True`; T/U/I: `0/10/15`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/cs50-real01-material-pilot`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/feat/cs50-real01-material-pilot`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `PROTECTED_ACTIVE`, `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: explicit/current-task protection; unsecured untracked/ignored paths (including empty directories); authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| `??` | `deployment/c26g.controller.offline.json.example` |
| `??` | `docs/deployment/c26g_go_no_go.md` |
| `??` | `docs/deployment/c26g_integration_validation.md` |
| `??` | `docs/deployment/c26g_operator_decisions.md` |
| `??` | `docs/deployment/c26g_readiness_matrix.md` |
| `??` | `docs/deployment/c26g_runbook.md` |
| `??` | `scripts/c26g_readiness.py` |
| `??` | `tests/test_c26g_compose_integration.py` |
| `??` | `tests/test_c26g_readiness.py` |
| `??` | `tests/test_c26g_restore_integration.py` |
| `!!` | `.ruff_cache/.gitignore` |
| `!!` | `.ruff_cache/0.16.3/` |
| `!!` | `.ruff_cache/CACHEDIR.TAG` |
| `!!` | `src/__pycache__/` |
| `!!` | `src/content_store/__pycache__/` |
| `!!` | `src/job_control/__pycache__/` |
| `!!` | `src/model_discovery/__pycache__/` |
| `!!` | `src/model_lecture/__pycache__/` |
| `!!` | `src/model_materials/__pycache__/` |
| `!!` | `src/model_transcribe/__pycache__/` |
| `!!` | `src/tools_lecture/__pycache__/` |
| `!!` | `src/tools_materials/__pycache__/` |
| `!!` | `src/tools_transcribe/__pycache__/` |
| `!!` | `tests/__pycache__/` |

Zusatzpfade (14): `.agents/`, `.aws/`, `.codex/`, `.ruff_cache/`, `deployment/c26g.controller.offline.json.example`, `docs/deployment/c26g_go_no_go.md`, `docs/deployment/c26g_integration_validation.md`, `docs/deployment/c26g_operator_decisions.md`, `docs/deployment/c26g_readiness_matrix.md`, `docs/deployment/c26g_runbook.md`, `scripts/c26g_readiness.py`, `tests/test_c26g_compose_integration.py`, `tests/test_c26g_readiness.py`, `tests/test_c26g_restore_integration.py`.

Ignored-Pfade (15): `.ruff_cache/`, `.ruff_cache/.gitignore`, `.ruff_cache/0.16.3/`, `.ruff_cache/CACHEDIR.TAG`, `src/__pycache__/`, `src/content_store/__pycache__/`, `src/job_control/__pycache__/`, `src/model_discovery/__pycache__/`, `src/model_lecture/__pycache__/`, `src/model_materials/__pycache__/`, `src/model_transcribe/__pycache__/`, `src/tools_lecture/__pycache__/`, `src/tools_materials/__pycache__/`, `src/tools_transcribe/__pycache__/`, `tests/__pycache__/`.

### 65 · Personal_Assistant-dev01a

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-dev01a`
- Branch: `refs/heads/feat/dev01a-authorized-search`
- HEAD / lokaler Branch: `b1c3c9cc292d4abab210a3316952878827cc57f0` / `b1c3c9cc292d4abab210a3316952878827cc57f0`
- Betreff: `docs(search): record package A PR and Project verification`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/dev01a-authorized-search`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/dev01a-authorized-search`.
- Lokaler Tracking-SHA: `b1c3c9cc292d4abab210a3316952878827cc57f0`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/dev01a-authorized-search`, SHA `b1c3c9cc292d4abab210a3316952878827cc57f0`.
- Backupref: `refs/heads/feat/dev01a-authorized-search`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 66 · Personal_Assistant-dev01b

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-dev01b`
- Branch: `refs/heads/feat/dev01b-controlled-index-jobs`
- HEAD / lokaler Branch: `c07ed9a17c703df17a44dfac075603fdbe108907` / `c07ed9a17c703df17a44dfac075603fdbe108907`
- Betreff: `Add controlled C16 index jobs and scoped FTS5 status`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/dev01b-controlled-index-jobs`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/dev01b-controlled-index-jobs`.
- Lokaler Tracking-SHA: `c07ed9a17c703df17a44dfac075603fdbe108907`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/dev01b-controlled-index-jobs`, SHA `c07ed9a17c703df17a44dfac075603fdbe108907`.
- Backupref: `refs/heads/feat/dev01b-controlled-index-jobs`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 67 · Personal_Assistant-dev02b

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-dev02b`
- Branch: `refs/heads/feat/dev02b-controlled-import`
- HEAD / lokaler Branch: `2af5cec1d8b51b43827dd16f147c57d829d50789` / `2af5cec1d8b51b43827dd16f147c57d829d50789`
- Betreff: `docs: finalize verified task-owned lifecycle evidence`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/dev02b-controlled-import`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/dev02b-controlled-import`.
- Lokaler Tracking-SHA: `2af5cec1d8b51b43827dd16f147c57d829d50789`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/dev02b-controlled-import`, SHA `2af5cec1d8b51b43827dd16f147c57d829d50789`.
- Backupref: `refs/heads/feat/dev02b-controlled-import`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 68 · Personal_Assistant-dev03b

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-dev03b`
- Branch: `refs/heads/feat/dev03b-parsing-evaluation`
- HEAD / lokaler Branch: `4f12bb7e190c690d08083232db9b29025c70708a` / `4f12bb7e190c690d08083232db9b29025c70708a`
- Betreff: `docs: record DEV-03B exam availability and synthetic revalidation`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/dev03b-parsing-evaluation`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/dev03b-parsing-evaluation`.
- Lokaler Tracking-SHA: `4f12bb7e190c690d08083232db9b29025c70708a`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/dev03b-parsing-evaluation`, SHA `4f12bb7e190c690d08083232db9b29025c70708a`.
- Backupref: `refs/heads/feat/dev03b-parsing-evaluation`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 69 · Personal_Assistant-dev03c

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-dev03c`
- Branch: `refs/heads/feat/dev03c-retrieval-evaluation`
- HEAD / lokaler Branch: `edf6f05fdc24a33297ce445a54e1a804cb8b0796` / `edf6f05fdc24a33297ce445a54e1a804cb8b0796`
- Betreff: `docs: record DEV-03 integration boundaries and retained review branches`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/dev03c-retrieval-evaluation`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/dev03c-retrieval-evaluation`.
- Lokaler Tracking-SHA: `edf6f05fdc24a33297ce445a54e1a804cb8b0796`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/dev03c-retrieval-evaluation`, SHA `edf6f05fdc24a33297ce445a54e1a804cb8b0796`.
- Backupref: `refs/heads/feat/dev03c-retrieval-evaluation`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 70 · Personal_Assistant-dev03d

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-dev03d`
- Branch: `refs/heads/feat/dev03d-exam-inventory`
- HEAD / lokaler Branch: `419b9c2ff9572ea7bbe15bb68c5d053dc206fd3d` / `419b9c2ff9572ea7bbe15bb68c5d053dc206fd3d`
- Betreff: `docs: track the two explicitly approved metadata JSON manifests`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/dev03d-exam-inventory`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/dev03d-exam-inventory`.
- Lokaler Tracking-SHA: `419b9c2ff9572ea7bbe15bb68c5d053dc206fd3d`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/dev03d-exam-inventory`, SHA `419b9c2ff9572ea7bbe15bb68c5d053dc206fd3d`.
- Backupref: `refs/heads/feat/dev03d-exam-inventory`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 71 · Personal_Assistant-dev03e

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-dev03e`
- Branch: `refs/heads/feat/dev03e-local-evaluation`
- HEAD / lokaler Branch: `08218c0800a47f10fbb260d1d42edb9a2e4a37c4` / `08218c0800a47f10fbb260d1d42edb9a2e4a37c4`
- Betreff: `docs: record authorized real exam results and independent review handoff`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/dev03e-local-evaluation`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/dev03e-local-evaluation`.
- Lokaler Tracking-SHA: `08218c0800a47f10fbb260d1d42edb9a2e4a37c4`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/dev03e-local-evaluation`, SHA `08218c0800a47f10fbb260d1d42edb9a2e4a37c4`.
- Backupref: `refs/heads/feat/dev03e-local-evaluation`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 72 · Personal_Assistant-dev03e-course

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-dev03e-course`
- Branch: `refs/heads/feat/dev03e-content-course`
- HEAD / lokaler Branch: `d6f16d0547b3e2139235a8b1bbfaac17d747e353` / `d6f16d0547b3e2139235a8b1bbfaac17d747e353`
- Betreff: `feat: add explicit Loviscach scope to content and ACL course contracts`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/dev03e-content-course`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/dev03e-content-course`.
- Lokaler Tracking-SHA: `d6f16d0547b3e2139235a8b1bbfaac17d747e353`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/dev03e-content-course`, SHA `d6f16d0547b3e2139235a8b1bbfaac17d747e353`.
- Backupref: `refs/heads/feat/dev03e-content-course`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 73 · Personal_Assistant-dev03f

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-dev03f`
- Branch: `refs/heads/feat/dev03f-human-review`
- HEAD / lokaler Branch: `fa8a8830efc12ab54bef9448bcd8c0d985442c8b` / `fa8a8830efc12ab54bef9448bcd8c0d985442c8b`
- Betreff: `docs(dev03f): record review handoff publication`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/feat/dev03f-human-review`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/feat/dev03f-human-review`.
- Lokaler Tracking-SHA: `fa8a8830efc12ab54bef9448bcd8c0d985442c8b`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/dev03f-human-review`, SHA `fa8a8830efc12ab54bef9448bcd8c0d985442c8b`.
- Backupref: `refs/heads/feat/dev03f-human-review`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 74 · Personal_Assistant-html-parser

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-html-parser`
- Branch: `refs/heads/fix/cs50-html-semantics`
- HEAD / lokaler Branch: `9e7fda602b00c4aca6846317cb3e9f590b2b8f54` / `9e7fda602b00c4aca6846317cb3e9f590b2b8f54`
- Betreff: `Fix CS50 notes HTML list and inline code normalization`
- Status vollständig: `True`; T/U/I: `1/0/0`.
- Upstream: `refs/remotes/origin/master`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/master`.
- Lokaler Tracking-SHA: `e68275205fefb7a5f6db42bc45060e505bfcefb5`; ahead/behind: `1/188`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/fix/cs50-html-semantics`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/fix/cs50-html-semantics`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `DIRTY`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: tracked changes; authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| ` M` | `.gitignore` |

### 75 · Personal_Assistant-maint01

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-maint01`
- Branch: `refs/heads/docs/maint01-inventory-consolidation`
- HEAD / lokaler Branch: `568d3835c880f616a1535458b36779f2b4276038` / `568d3835c880f616a1535458b36779f2b4276038`
- Betreff: `docs(maint01): inventory branches and preserve historical review ADR`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/docs/maint01-inventory-consolidation`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/docs/maint01-inventory-consolidation`.
- Lokaler Tracking-SHA: `568d3835c880f616a1535458b36779f2b4276038`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/docs/maint01-inventory-consolidation`, SHA `568d3835c880f616a1535458b36779f2b4276038`.
- Backupref: `refs/heads/docs/maint01-inventory-consolidation`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 76 · Personal_Assistant-maint02

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-maint02`
- Branch: `refs/heads/docs/maint02-cleanup-verification`
- HEAD / lokaler Branch: `0308217d2213b7a2d6e39b731ec22f640b8a4a3d` / `0308217d2213b7a2d6e39b731ec22f640b8a4a3d`
- Betreff: `docs: verify MAINT-02 cleanup candidates and guarded recovery plan`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/docs/maint02-cleanup-verification`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/docs/maint02-cleanup-verification`.
- Lokaler Tracking-SHA: `0308217d2213b7a2d6e39b731ec22f640b8a4a3d`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/docs/maint02-cleanup-verification`, SHA `0308217d2213b7a2d6e39b731ec22f640b8a4a3d`.
- Backupref: `refs/heads/docs/maint02-cleanup-verification`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 77 · Personal_Assistant-maint03

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-maint03`
- Branch: `refs/heads/audit/maint03-legacy-modernization`
- HEAD / lokaler Branch: `6b397eb4576bac93b318d0e1b8e954d16cb5e08e` / `6b397eb4576bac93b318d0e1b8e954d16cb5e08e`
- Betreff: `fix(maint03): harden legacy file utilities and document audit`
- Status vollständig: `True`; T/U/I: `65/0/25`.
- Upstream: `refs/remotes/origin/audit/maint03-legacy-modernization`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/audit/maint03-legacy-modernization`.
- Lokaler Tracking-SHA: `6b397eb4576bac93b318d0e1b8e954d16cb5e08e`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/audit/maint03-legacy-modernization`, SHA `6b397eb4576bac93b318d0e1b8e954d16cb5e08e`.
- Backupref: `refs/heads/audit/maint03-legacy-modernization`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `DIRTY`, `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: tracked changes; unsecured untracked/ignored paths (including empty directories); authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| ` M` | `docs/course_sources/cs50/cs50_ai/index.html` |
| ` M` | `docs/course_sources/cs50/cs50_ai/lecture_1.html` |
| ` M` | `docs/course_sources/cs50/cs50_ai/practice.html` |
| ` M` | `docs/course_sources/cs50/cs50_ai/week_0.html` |
| ` M` | `docs/course_sources/cs50/cs50_ai/week_1.html` |
| ` M` | `docs/course_sources/cs50/cs50_ai/week_2.html` |
| ` M` | `docs/course_sources/cs50/cs50_ai/week_3.html` |
| ` M` | `docs/course_sources/cs50/cs50_ai/week_4.html` |
| ` M` | `docs/course_sources/cs50/cs50_ai/week_5.html` |
| ` M` | `docs/course_sources/cs50/cs50_ai/week_6.html` |
| ` M` | `docs/course_sources/cs50/cs50_cybersecurity/index.html` |
| ` M` | `docs/course_sources/cs50/cs50_cybersecurity/week_0.html` |
| ` M` | `docs/course_sources/cs50/cs50_cybersecurity/week_1.html` |
| ` M` | `docs/course_sources/cs50/cs50_cybersecurity/week_2.html` |
| ` M` | `docs/course_sources/cs50/cs50_cybersecurity/week_3.html` |
| ` M` | `docs/course_sources/cs50/cs50_cybersecurity/week_4.html` |
| ` M` | `docs/course_sources/cs50/cs50_python/cdn.html` |
| ` M` | `docs/course_sources/cs50/cs50_python/index.html` |
| ` M` | `docs/course_sources/cs50/cs50_python/lecture_5.html` |
| ` M` | `docs/course_sources/cs50/cs50_python/practice_1.html` |
| ` M` | `docs/course_sources/cs50/cs50_python/week_0.html` |
| ` M` | `docs/course_sources/cs50/cs50_python/week_1.html` |
| ` M` | `docs/course_sources/cs50/cs50_python/week_2.html` |
| ` M` | `docs/course_sources/cs50/cs50_python/week_3.html` |
| ` M` | `docs/course_sources/cs50/cs50_python/week_4.html` |
| ` M` | `docs/course_sources/cs50/cs50_python/week_5.html` |
| ` M` | `docs/course_sources/cs50/cs50_python/week_6.html` |
| ` M` | `docs/course_sources/cs50/cs50_python/week_7.html` |
| ` M` | `docs/course_sources/cs50/cs50_python/week_8.html` |
| ` M` | `docs/course_sources/cs50/cs50_python/week_9.html` |
| ` M` | `docs/course_sources/cs50/cs50_sql/index.html` |
| ` M` | `docs/course_sources/cs50/cs50_sql/week_0.html` |
| ` M` | `docs/course_sources/cs50/cs50_sql/week_1.html` |
| ` M` | `docs/course_sources/cs50/cs50_sql/week_2.html` |
| ` M` | `docs/course_sources/cs50/cs50_sql/week_3.html` |
| ` M` | `docs/course_sources/cs50/cs50_sql/week_4.html` |
| ` M` | `docs/course_sources/cs50/cs50_sql/week_5.html` |
| ` M` | `docs/course_sources/cs50/cs50_sql/week_6.html` |
| ` M` | `docs/course_sources/cs50/cs50_web/index.html` |
| ` M` | `docs/course_sources/cs50/cs50_web/week_0.html` |
| ` M` | `docs/course_sources/cs50/cs50_web/week_1.html` |
| ` M` | `docs/course_sources/cs50/cs50_web/week_2.html` |
| ` M` | `docs/course_sources/cs50/cs50_web/week_3.html` |
| ` M` | `docs/course_sources/cs50/cs50_web/week_4.html` |
| ` M` | `docs/course_sources/cs50/cs50_web/week_5.html` |
| ` M` | `docs/course_sources/cs50/cs50_web/week_6.html` |
| ` M` | `docs/course_sources/cs50/cs50_web/week_7.html` |
| ` M` | `docs/course_sources/cs50/cs50_web/week_8.html` |
| ` M` | `docs/course_sources/cs50/cs50x/index.html` |
| ` M` | `docs/course_sources/cs50/cs50x/lecture_0.html` |
| ` M` | `docs/course_sources/cs50/cs50x/practice_problems.html` |
| ` M` | `docs/course_sources/cs50/cs50x/week_0.html` |
| ` M` | `docs/course_sources/cs50/cs50x/week_1.html` |
| ` M` | `docs/course_sources/cs50/cs50x/week_10.html` |
| ` M` | `docs/course_sources/cs50/cs50x/week_2.html` |
| ` M` | `docs/course_sources/cs50/cs50x/week_3.html` |
| ` M` | `docs/course_sources/cs50/cs50x/week_4.html` |
| ` M` | `docs/course_sources/cs50/cs50x/week_5.html` |
| ` M` | `docs/course_sources/cs50/cs50x/week_6.html` |
| ` M` | `docs/course_sources/cs50/cs50x/week_7.html` |
| ` M` | `docs/course_sources/cs50/cs50x/week_8.html` |
| ` M` | `docs/course_sources/cs50/cs50x/week_9.html` |
| ` M` | `docs/course_sources/cs50/cs50x/week_ai.html` |
| ` M` | `docs/cs50/evaluation/c24_05c/r3/synthetic/report.v1.json` |
| ` M` | `docs/cs50/operations/material_coverage.md` |
| `!!` | `.ruff_cache/.gitignore` |
| `!!` | `.ruff_cache/0.16.0/` |
| `!!` | `.ruff_cache/CACHEDIR.TAG` |
| `!!` | `[private path omitted]` |
| `!!` | `docs/maintenance/maint03_static_evidence.json` |
| `!!` | `scripts/__pycache__/` |
| `!!` | `src/__pycache__/` |
| `!!` | `src/agent/prompts/__pycache__/` |
| `!!` | `src/content_store/__pycache__/` |
| `!!` | `src/core/__pycache__/` |
| `!!` | `src/job_control/__pycache__/` |
| `!!` | `src/model_discovery/__pycache__/` |
| `!!` | `src/model_evaluation/__pycache__/` |
| `!!` | `src/model_knowledge/__pycache__/` |
| `!!` | `src/model_lecture/__pycache__/` |
| `!!` | `src/model_materials/__pycache__/` |
| `!!` | `src/model_transcribe/__pycache__/` |
| `!!` | `src/tools_evaluation/__pycache__/` |
| `!!` | `src/tools_knowledge/__pycache__/` |
| `!!` | `src/tools_lecture/__pycache__/` |
| `!!` | `src/tools_materials/__pycache__/` |
| `!!` | `src/tools_transcribe/__pycache__/` |
| `!!` | `src/utils/__pycache__/` |
| `!!` | `tests/__pycache__/` |

Zusatzpfade (1): `.ruff_cache/`.

Ignored-Pfade (25): `.ruff_cache/`, `.ruff_cache/.gitignore`, `.ruff_cache/0.16.0/`, `.ruff_cache/CACHEDIR.TAG`, `[private path omitted]`, `docs/maintenance/maint03_static_evidence.json`, `scripts/__pycache__/`, `src/__pycache__/`, `src/agent/prompts/__pycache__/`, `src/content_store/__pycache__/`, `src/core/__pycache__/`, `src/job_control/__pycache__/`, `src/model_discovery/__pycache__/`, `src/model_evaluation/__pycache__/`, `src/model_knowledge/__pycache__/`, `src/model_lecture/__pycache__/`, `src/model_materials/__pycache__/`, `src/model_transcribe/__pycache__/`, `src/tools_evaluation/__pycache__/`, `src/tools_knowledge/__pycache__/`, `src/tools_lecture/__pycache__/`, `src/tools_materials/__pycache__/`, `src/tools_transcribe/__pycache__/`, `src/utils/__pycache__/`, `tests/__pycache__/`.

### 78 · Personal_Assistant-maint03b

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-maint03b`
- Branch: `refs/heads/audit/maint03b-test-stabilization`
- HEAD / lokaler Branch: `aafba19d549316300a79da37f0ab5f9224d82d37` / `aafba19d549316300a79da37f0ab5f9224d82d37`
- Betreff: `test(maint03b): stabilize offline test infrastructure`
- Status vollständig: `True`; T/U/I: `0/0/25`.
- Upstream: `refs/remotes/origin/audit/maint03b-test-stabilization`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/audit/maint03b-test-stabilization`.
- Lokaler Tracking-SHA: `aafba19d549316300a79da37f0ab5f9224d82d37`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/audit/maint03b-test-stabilization`, SHA `aafba19d549316300a79da37f0ab5f9224d82d37`.
- Backupref: `refs/heads/audit/maint03b-test-stabilization`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: unsecured untracked/ignored paths (including empty directories); authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| `!!` | `.ruff_cache/.gitignore` |
| `!!` | `.ruff_cache/0.16.0/` |
| `!!` | `.ruff_cache/CACHEDIR.TAG` |
| `!!` | `scripts/__pycache__/` |
| `!!` | `scripts/acceptance/__pycache__/` |
| `!!` | `src/__pycache__/` |
| `!!` | `src/agent/prompts/__pycache__/` |
| `!!` | `src/content_store/__pycache__/` |
| `!!` | `src/core/__pycache__/` |
| `!!` | `src/job_control/__pycache__/` |
| `!!` | `src/model_discovery/__pycache__/` |
| `!!` | `src/model_evaluation/__pycache__/` |
| `!!` | `src/model_knowledge/__pycache__/` |
| `!!` | `src/model_lecture/__pycache__/` |
| `!!` | `src/model_materials/__pycache__/` |
| `!!` | `src/model_transcribe/__pycache__/` |
| `!!` | `src/tools_evaluation/__pycache__/` |
| `!!` | `src/tools_knowledge/__pycache__/` |
| `!!` | `src/tools_lecture/__pycache__/` |
| `!!` | `src/tools_materials/__pycache__/` |
| `!!` | `src/tools_rag/__pycache__/` |
| `!!` | `src/tools_transcribe/__pycache__/` |
| `!!` | `src/utils/__pycache__/` |
| `!!` | `tests/__pycache__/` |

Zusatzpfade (4): `.agents/`, `.aws/`, `.codex/`, `.ruff_cache/`.

Ignored-Pfade (25): `.ruff_cache/`, `.ruff_cache/.gitignore`, `.ruff_cache/0.16.0/`, `.ruff_cache/CACHEDIR.TAG`, `scripts/__pycache__/`, `scripts/acceptance/__pycache__/`, `src/__pycache__/`, `src/agent/prompts/__pycache__/`, `src/content_store/__pycache__/`, `src/core/__pycache__/`, `src/job_control/__pycache__/`, `src/model_discovery/__pycache__/`, `src/model_evaluation/__pycache__/`, `src/model_knowledge/__pycache__/`, `src/model_lecture/__pycache__/`, `src/model_materials/__pycache__/`, `src/model_transcribe/__pycache__/`, `src/tools_evaluation/__pycache__/`, `src/tools_knowledge/__pycache__/`, `src/tools_lecture/__pycache__/`, `src/tools_materials/__pycache__/`, `src/tools_rag/__pycache__/`, `src/tools_transcribe/__pycache__/`, `src/utils/__pycache__/`, `tests/__pycache__/`.

### 79 · Personal_Assistant-maint04

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-maint04`
- Branch: `refs/heads/refactor/maint04-parsing-config`
- HEAD / lokaler Branch: `1a973f40199302416c4726658eb641c40dbae724` / `1a973f40199302416c4726658eb641c40dbae724`
- Betreff: `refactor(maint04): consolidate parsing config definitions`
- Status vollständig: `True`; T/U/I: `0/0/25`.
- Upstream: `refs/remotes/origin/refactor/maint04-parsing-config`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/refactor/maint04-parsing-config`.
- Lokaler Tracking-SHA: `1a973f40199302416c4726658eb641c40dbae724`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/refactor/maint04-parsing-config`, SHA `1a973f40199302416c4726658eb641c40dbae724`.
- Backupref: `refs/heads/refactor/maint04-parsing-config`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: unsecured untracked/ignored paths (including empty directories); authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| `!!` | `.ruff_cache/.gitignore` |
| `!!` | `.ruff_cache/0.16.0/` |
| `!!` | `.ruff_cache/CACHEDIR.TAG` |
| `!!` | `scripts/__pycache__/` |
| `!!` | `scripts/acceptance/__pycache__/` |
| `!!` | `src/__pycache__/` |
| `!!` | `src/agent/prompts/__pycache__/` |
| `!!` | `src/content_store/__pycache__/` |
| `!!` | `src/core/__pycache__/` |
| `!!` | `src/job_control/__pycache__/` |
| `!!` | `src/model_discovery/__pycache__/` |
| `!!` | `src/model_evaluation/__pycache__/` |
| `!!` | `src/model_knowledge/__pycache__/` |
| `!!` | `src/model_lecture/__pycache__/` |
| `!!` | `src/model_materials/__pycache__/` |
| `!!` | `src/model_transcribe/__pycache__/` |
| `!!` | `src/tools_evaluation/__pycache__/` |
| `!!` | `src/tools_knowledge/__pycache__/` |
| `!!` | `src/tools_lecture/__pycache__/` |
| `!!` | `src/tools_materials/__pycache__/` |
| `!!` | `src/tools_rag/__pycache__/` |
| `!!` | `src/tools_transcribe/__pycache__/` |
| `!!` | `src/utils/__pycache__/` |
| `!!` | `tests/__pycache__/` |

Zusatzpfade (1): `.ruff_cache/`.

Ignored-Pfade (25): `.ruff_cache/`, `.ruff_cache/.gitignore`, `.ruff_cache/0.16.0/`, `.ruff_cache/CACHEDIR.TAG`, `scripts/__pycache__/`, `scripts/acceptance/__pycache__/`, `src/__pycache__/`, `src/agent/prompts/__pycache__/`, `src/content_store/__pycache__/`, `src/core/__pycache__/`, `src/job_control/__pycache__/`, `src/model_discovery/__pycache__/`, `src/model_evaluation/__pycache__/`, `src/model_knowledge/__pycache__/`, `src/model_lecture/__pycache__/`, `src/model_materials/__pycache__/`, `src/model_transcribe/__pycache__/`, `src/tools_evaluation/__pycache__/`, `src/tools_knowledge/__pycache__/`, `src/tools_lecture/__pycache__/`, `src/tools_materials/__pycache__/`, `src/tools_rag/__pycache__/`, `src/tools_transcribe/__pycache__/`, `src/utils/__pycache__/`, `tests/__pycache__/`.

### 80 · Personal_Assistant-maint04b

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-maint04b`
- Branch: `refs/heads/fix/maint04b-schema-legacy`
- HEAD / lokaler Branch: `778367396cd52526eca59edd41c2367f5e43b897` / `778367396cd52526eca59edd41c2367f5e43b897`
- Betreff: `fix(maint04b): restore workflow schema boundary`
- Status vollständig: `True`; T/U/I: `1/1/25`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/fix/maint04b-schema-legacy`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/fix/maint04b-schema-legacy`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `DIRTY`, `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: tracked changes; unsecured untracked/ignored paths (including empty directories); authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| ` M` | `scripts/test_profiles.py` |
| `??` | `scripts/maint04b_legacy_probe.py` |
| `!!` | `.ruff_cache/.gitignore` |
| `!!` | `.ruff_cache/0.16.0/` |
| `!!` | `.ruff_cache/CACHEDIR.TAG` |
| `!!` | `scripts/__pycache__/` |
| `!!` | `scripts/acceptance/__pycache__/` |
| `!!` | `src/__pycache__/` |
| `!!` | `src/agent/prompts/__pycache__/` |
| `!!` | `src/content_store/__pycache__/` |
| `!!` | `src/core/__pycache__/` |
| `!!` | `src/job_control/__pycache__/` |
| `!!` | `src/model_discovery/__pycache__/` |
| `!!` | `src/model_evaluation/__pycache__/` |
| `!!` | `src/model_knowledge/__pycache__/` |
| `!!` | `src/model_lecture/__pycache__/` |
| `!!` | `src/model_materials/__pycache__/` |
| `!!` | `src/model_transcribe/__pycache__/` |
| `!!` | `src/tools_evaluation/__pycache__/` |
| `!!` | `src/tools_knowledge/__pycache__/` |
| `!!` | `src/tools_lecture/__pycache__/` |
| `!!` | `src/tools_materials/__pycache__/` |
| `!!` | `src/tools_rag/__pycache__/` |
| `!!` | `src/tools_transcribe/__pycache__/` |
| `!!` | `src/utils/__pycache__/` |
| `!!` | `tests/__pycache__/` |

Zusatzpfade (2): `.ruff_cache/`, `scripts/maint04b_legacy_probe.py`.

Ignored-Pfade (25): `.ruff_cache/`, `.ruff_cache/.gitignore`, `.ruff_cache/0.16.0/`, `.ruff_cache/CACHEDIR.TAG`, `scripts/__pycache__/`, `scripts/acceptance/__pycache__/`, `src/__pycache__/`, `src/agent/prompts/__pycache__/`, `src/content_store/__pycache__/`, `src/core/__pycache__/`, `src/job_control/__pycache__/`, `src/model_discovery/__pycache__/`, `src/model_evaluation/__pycache__/`, `src/model_knowledge/__pycache__/`, `src/model_lecture/__pycache__/`, `src/model_materials/__pycache__/`, `src/model_transcribe/__pycache__/`, `src/tools_evaluation/__pycache__/`, `src/tools_knowledge/__pycache__/`, `src/tools_lecture/__pycache__/`, `src/tools_materials/__pycache__/`, `src/tools_rag/__pycache__/`, `src/tools_transcribe/__pycache__/`, `src/utils/__pycache__/`, `tests/__pycache__/`.

### 81 · Personal_Assistant-maint05

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-maint05`
- Branch: `refs/heads/feat/maint05-worktree-archival`
- HEAD / lokaler Branch: `e68275205fefb7a5f6db42bc45060e505bfcefb5` / `e68275205fefb7a5f6db42bc45060e505bfcefb5`
- Betreff: `Merge pull request #159 from rf-data/audit/c26-legacy-prs`
- Status vollständig: `True`; T/U/I: `0/5/13`.
- Upstream: `refs/remotes/origin/master`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/master`.
- Lokaler Tracking-SHA: `e68275205fefb7a5f6db42bc45060e505bfcefb5`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/feat/maint05-worktree-archival`, SHA `unknown / nicht vorhanden`.
- Backupref: `refs/heads/feat/maint05-worktree-archival`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[1, 2]`; Inaktivität nicht bewiesen.
- Klassen: `PROTECTED_ACTIVE`, `UNTRACKED_OR_IGNORED_RISK`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: explicit/current-task protection; process cwd in worktree; unsecured untracked/ignored paths (including empty directories); authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

| Gitstatus | Pfad |
| --- | --- |
| `??` | `docs/maintenance/maint05_archive_safety.md` |
| `??` | `docs/maintenance/maint05_c2301_pilot.md` |
| `??` | `docs/maintenance/maint05_operator_runbook.md` |
| `??` | `scripts/worktree_archive.py` |
| `??` | `tests/test_worktree_archive.py` |
| `!!` | `.pytest_cache/.gitignore` |
| `!!` | `.pytest_cache/CACHEDIR.TAG` |
| `!!` | `.pytest_cache/README.md` |
| `!!` | `.pytest_cache/v/` |
| `!!` | `.ruff_cache/.gitignore` |
| `!!` | `.ruff_cache/0.16.3/` |
| `!!` | `.ruff_cache/CACHEDIR.TAG` |
| `!!` | `docs/maintenance/maint05_pilot_github.json` |
| `!!` | `docs/maintenance/maint05_pr_snapshot.json` |
| `!!` | `scripts/__pycache__/` |
| `!!` | `tests/__pycache__/` |

Zusatzpfade (8): `.agents/`, `.aws/`, `.codex/`, `.pytest_cache/`, `.ruff_cache/`, `docs/maintenance/`, `scripts/worktree_archive.py`, `tests/test_worktree_archive.py`.

Ignored-Pfade (13): `.pytest_cache/`, `.pytest_cache/.gitignore`, `.pytest_cache/CACHEDIR.TAG`, `.pytest_cache/README.md`, `.pytest_cache/v/`, `.ruff_cache/`, `.ruff_cache/.gitignore`, `.ruff_cache/0.16.3/`, `.ruff_cache/CACHEDIR.TAG`, `docs/maintenance/maint05_pilot_github.json`, `docs/maintenance/maint05_pr_snapshot.json`, `scripts/__pycache__/`, `tests/__pycache__/`.

### 82 · Personal_Assistant-pm01

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-pm01`
- Branch: `refs/heads/docs/pm01-project-consolidation`
- HEAD / lokaler Branch: `e06a29c47310d347af26b7a8c61e574d0cef172a` / `e06a29c47310d347af26b7a8c61e574d0cef172a`
- Betreff: `docs(pm01): reconcile C23–C32 roadmap and authorized planning scope`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/docs/pm01-project-consolidation`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/docs/pm01-project-consolidation`.
- Lokaler Tracking-SHA: `e06a29c47310d347af26b7a8c61e574d0cef172a`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/docs/pm01-project-consolidation`, SHA `e06a29c47310d347af26b7a8c61e574d0cef172a`.
- Backupref: `refs/heads/docs/pm01-project-consolidation`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 83 · Personal_Assistant-pm02

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-pm02`
- Branch: `refs/heads/docs/pm02-project-operationalization`
- HEAD / lokaler Branch: `024cab7893701a6cf52c85975682c76869dc2f5e` / `024cab7893701a6cf52c85975682c76869dc2f5e`
- Betreff: `docs(pm02): reconcile Project #1 targets and document operational blocker`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `refs/remotes/origin/docs/pm02-project-operationalization`; konfigurierter Remote/Mergeref: `origin` / `refs/heads/docs/pm02-project-operationalization`.
- Lokaler Tracking-SHA: `024cab7893701a6cf52c85975682c76869dc2f5e`; ahead/behind: `0/0`.
- Namensgleicher Cache-Ref: `refs/remotes/origin/docs/pm02-project-operationalization`, SHA `024cab7893701a6cf52c85975682c76869dc2f5e`.
- Backupref: `refs/heads/docs/pm02-project-operationalization`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.

### 84 · Personal_Assistant_C23_Test

- Pfad: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant_C23_Test`
- Branch: `DETACHED_HEAD`
- HEAD / lokaler Branch: `d654f0580f6c5d6aa5698f33dc5c93dec5ba66d5` / `unknown / nicht vorhanden`
- Betreff: `Merge pull request #81 from rf-data/feat/c23-05-txt-unknown-time`
- Status vollständig: `True`; T/U/I: `0/0/0`.
- Upstream: `unknown / nicht vorhanden`; konfigurierter Remote/Mergeref: `unknown / nicht vorhanden` / `unknown / nicht vorhanden`.
- Lokaler Tracking-SHA: `unknown / nicht vorhanden`; ahead/behind: `unknown / nicht vorhanden`.
- Namensgleicher Cache-Ref: `unknown / nicht vorhanden`, SHA `unknown / nicht vorhanden`.
- Backupref: `unknown / nicht vorhanden`; Remote-SHA `unknown`; Live-Existenz `unverified`; Remote-ahead/behind `unknown`.
- Aktivität: CWD-PIDs `[]`; Inaktivität nicht bewiesen.
- Klassen: `DETACHED_HEAD`, `REMOTE_UNVERIFIED`, `PR_OR_MERGE_UNVERIFIED`.
- **HOLD**: detached HEAD unsupported for removal; authoritative remote SHA unverified. Zusätzlich: Operatorfreigabe, Writerstillstand und Restorebeleg fehlen.
- PR-Bezug: `unknown`; kein positiver Nachweis aus den abgefragten offenen PRs.
