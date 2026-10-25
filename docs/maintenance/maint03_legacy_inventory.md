# MAINT-03 – Legacy-Inventar und Prüfgrenzen

Stand: 25.10.2026. Dies ist der **Code-Audit** im Branch
`audit/maint03-legacy-modernization`, nicht die historische Gitbereinigung gleichen
Namens unter [docs/audit/maint03](../audit/maint03/README.md). Deren Entscheidungen
sowie MAINT-01/02/04/05 werden weder überschrieben noch neu ausgeführt.
Produktionsstatus C26: **HOLD**.

## Basis und vorhandene Arbeit

GitHub meldet `master` als Default von `rf-data/Personal_Assistant`. Sein am
25.10.2026 gelesener Commit ist `e68275205fefb7a5f6db42bc45060e505bfcefb5`;
der anfänglich saubere Aufgabenworktree und `origin/master` zeigen genau darauf.
Der lokale Branch `master` zeigt dagegen auf `c1007ef` und ist keine geeignete
aktuelle Basis. Kein Fetch, Rebase, Merge oder Cherry-Pick wurde benötigt.
Der gewünschte Branch und Worktree waren bereits vor diesem Lauf vorhanden.
Sie wurden nicht neu angelegt und werden nicht als entbehrliche Eigenzugänge behandelt.

| Laufender Strang | Live-Head | Basis / Zustand bei Abfrage |
| --- | --- | --- |
| C26-D, [#161](https://github.com/rf-data/Personal_Assistant/pull/161) | `8b0ba2d4ab5d0cd6fc8dfa69783276efd929666f` | `master`, Draft, ungemergt |
| C26-E, [#162](https://github.com/rf-data/Personal_Assistant/pull/162) | `28e9a608d74270278cf037e35957d0bae08d50b2` | auf C26-D gestapelt, Draft |
| C26-F, [#163](https://github.com/rf-data/Personal_Assistant/pull/163) | `7ffb4ed6fd4d8433edf36fb4851a382b9b9c595d` | auf C26-E gestapelt, Draft |
| C27, [#158](https://github.com/rf-data/Personal_Assistant/pull/158) | `a0d3ebf7f64d44dd843f1848e70dc70a3a3af835` | `feat/c27-lecture-summarizer`, Draft |
| C26-Bootstrap, #157 | `80c31e52f76c1f3f62102b6884752b722f796e7c` | Draft; lokaler gleichnamiger Branch ist älter |
| C26-Gate, #148 | `f98eedd671c8a9d9eb58a3b957eda1a91713844d` | Draft |
| C26-Betriebsprüfung, #160 | `ecac8cfa844a7e4da9e0066a2c49c0c49fb3541d` | Draft |

Zusätzlich offen: #72, #88 und #89. Keine dieser Arbeiten ist Bestandteil der
Implementierung dieses Audits. C27-B/C werden durch den aktuellen C27-Draft und
seine bestehenden lokalen Worktrees respektiert; keine Übernahme ihrer Dateien.
Die UI ist ein separates Repository und wurde nicht verändert.

Gelesene Vorgaben: [AGENTS.md](../../AGENTS.md), [Roadmap](../ROADMAP.md),
[Architekturübersicht](../architecture.md),
[Content-ADR](../architecture/parsed_content_persistence_adr.md),
[Retrieval-ADR](../architecture/retrieval_indexing_adr.md),
[Review-ADR](../architecture/human_review_workflow_adr.md),
[Workflowarchitektur](../workflows/architecture.md).
Historische Statusangaben dieser Dokumente sind keine aktuellen Liefernachweise:
ContentStore, Content-Suche und Reviewbackend existieren inzwischen im Code.

MAINT-01/02 liefern bereits Branch-, Worktree- und Dokumenthistorien. Verwendet
wurden ihre [Bestände](../audit/maint02/README.md),
[Deltaentscheidungen](../audit/maint02/maint01_delta.md) und
[Schutz-/Einzelgates](../audit/maint02/maint03_execution_plan.md).
Die 239 alten Cleanupobjekte wurden nicht erneut als Codebefunde inventarisiert.
Auch die früheren gleichnamigen MAINT-04-Berichte bleiben historisch erhalten.

## Methode und Reichweite

Alle 526 bereits versionierten Pythondateien wurden mit **Python 3.12.12** per AST
geparst; 281 davon liegen unter `src/`. Keine Syntaxfehler. Ein erster Lauf mit dem
System-Python 3.11 scheiterte an gültiger Python-3.12-Typparametersyntax in
`tools_lecture/prepare_cs50.py`; das ist ein Interpreterfehler, kein Codebefund.
Ein vorhandenes Escape-SyntaxWarning in `_prototypes/run_PCA.py:145` ist separat
vom erfolgreichen 3.12-Parsing zu bewerten. Die beiden neuen Testdateien wurden
zusätzlich geparst und ausgeführt.

Die [maschinenlesbare Evidenz](maint03_static_evidence.json) enthält für jedes
Src-Modul Pfad, Zeilen-/Funktions-/Klassenanzahl und SHA-256, außerdem große
Funktionen, syntaktische Importkomponenten, fehlende lokale Module und exakte
Funktionsduplikate. Die Fingerprints beziehen sich auf den geprüften Arbeitsbaum,
die Dateiliste auf die ursprüngliche Gitbasis. Zeilenzahlen enthalten Kommentare
und Leerzeilen; sie messen keine cyclomatische Komplexität.

Statische Importkanten wurden mit tatsächlichen `rg`-Aufrufstellen, CLI-Guards,
Runnern, Registry und vorhandenen Tests abgeglichen. Der Detailreview konzentriert
sich auf Legacy-Parser, Konfiguration, IO, Retry sowie die Übergänge zu
Content/Jobs/Knowledge/RAG. Es ist kein manueller Zeilenreview sämtlicher Module
und keine vollständige Sicherheits- oder Laufzeitabnahme.

## Verantwortlichkeiten und Integrationspfade

| Bereich | Aufgaben und wichtige Module | Aufruf-/Vertragsbelege |
| --- | --- | --- |
| `model_parsing` / `tools_parsing` | Legacy-PDF/HTML/Wiki/Notebook/Text extrahieren, reinigen, klassifizieren und assemblieren; `base_*`, `feature_enricher`, `parse_document` | `tools_lecture/process_lecture.py`, `run_st_pdf_extract.py`, Parserbackend-Auswahl in `parse_document.py`; nicht pauschal unbenutzt |
| `core/config*`, `memory*` | Pydantic-Settings, Envkonfiguration, globale AppSession und prozessinterne Kontexte | Legacy-Runner und viele Utils; neuere reine Modelle benutzen `config_parsing` bzw. eigene Contract-Modelle |
| `core/logger`, `retry`, `observability`, `pipeline_metrics` | Loggerinitialisierung, API-Retry, Metriken und begrenzte Beobachtungsdaten | `find_knowledge`, `rebuild_knowledge`, `extract_video`; aktuelle Job-/Monitoringtests |
| `utils` | Pfade/JSON/Text, optionale SDK-, Datenframe-, Media- und Persistenzhelfer | Viele direkte Legacy-Aufrufer; Sessionabhängigkeiten verhindern pauschale Übernahme in den Kern |
| `model_discovery`, `tools_lecture` | Source-/Lectureauswahl, deterministische CS50-Pläne, Transcriptimport und Handoff | `scripts/cs50_*.py`, Lecture-/Discovery-/Transcript-Tests |
| `model_materials`, `tools_materials` | Typisierte Materialien, begrenzte Downloads, HTML/PDF/Code, ZIP, Receipts, Qualität und Inventare | `MaterialProcessor`, Workflowadapter, `content_store.adapters`; eigene aktuelle, versionsgebundene Parser |
| `model_transcribe`, `tools_transcribe` | Audio-/Videoadapter, SRT/TXT und Transcriptmodelle | Legacy-Audiorunner und offizieller Offlineimport; Media-SDKs bleiben optional |
| `model_knowledge`, `tools_knowledge` | Evidence, Extraktion, Budget/Checkpoint, konservative Konsolidierung, optionale visuelle/semantische Ableitungen | `run_knowledge_consolidation`, CS50-Pilot/Batch; keine Voraussetzung für Parsed Content |
| `model_rag`, `tools_rag` | Legacy-Chroma/SOP und Chunker; Transcript-Qdrant-Pilot; neue Contentprojektion/FTS und optionale Vektoradapter | Drei unterschiedliche Inhalts-/Rechteverträge; `content_index` bindet aktuelle Contentautorisierung |
| `content_store` | Autoritative Source-/Versions-/ACLmodelle, unveränderliche Blobs, Veröffentlichung, Reader, Projektion, Backup/Recovery | Eigene SQLite-DB, explizite Initialisierung, Material-/Transcriptadapter, HTTP-/Suchgrenzen |
| `job_control` | Allowlist, bestehende Queue, Controller/Executor/Guardian, Import-/Indexjobs, redigierte HTTPmodelle | `registry.py` benennt Runner auch als Strings; deren fehlende Pythonreferenz bedeutet keine Obsoleszenz |
| `workflows` | Deklarative Stufen, DAGvalidierung, Pipelinezustand, Resume, Service/HTTP | C18/C20 über vorhandene C16-Jobs; keine zweite Queue |
| `model_evaluation`, `tools_evaluation`, `evaluation_store` | Parsing-/Formel-/Retrievalgold, technische Evaluation und expliziter menschlicher Review | Store/Service/HTTP und bestehende Negativtests; Urteile ersetzen keine Produktionsfreigabe |
| `model_course` | Getrennte Legacy-/Contentkursidentitäten | Material-/Content-/Evaluationsmodelle; keine freie Aliasmigration |
| `llm`, `agent` | SDKkonfiguration, Prompts und SOPtemplates | Explizite optionale LLM-Aufrufe; kein automatischer Live-Smoke |
| `model_organizer`, `tools_organizer` | E-Mailmodelle/-helfer und Kalenderplatzhalter | Experimentelle Skripte, kein aktivierter Jobprozess |
| `run_*.py` / `scripts/*.py` | Legacy-Anwendungsrunner bzw. aktuelle explizite CLI-Einstiege | `python -m ...`, Makefile und Dokumentation; Importgraph allein kann CLI-Nutzung nicht widerlegen |
| `frontend/` und Root-Apps | 28 historische Streamlitseiten/-helfer und vier Rootdateien: `main.py` ist ein Hello-Einstieg, `st_admin_app.py` nur eine auskommentierte Integrationsnotiz, `st_chat_app.py`/`streamlit_app.py` sind Legacy-UIrunner | Statisch mitgeprüft; `streamlit_app.py` importiert nicht mehr definiertes `get_yaml_config` (R06). Die heutige separate Admin-UI wird dadurch nicht ersetzt. |
| `deployment/` | Betriebs-/Bootstrap-/Runtime-/Backupverträge außerhalb `src` | ASTscan eingeschlossen; keine Hostbefehle, Live-Checks oder Betriebsänderungen |
| `_prototypes/` | Historische Experimente außerhalb Src-Kern | Nur statisch untersucht; keine Import-/Modell-/Laufzeitinitialisierung |

Die 526 versionierten Pythondateien verteilen sich auf `src` 281, `tests` 138,
`scripts` 49, `frontend` 28, `_prototypes` 24, Root 4, `deployment` 1 und
`workers` 1. Die 138 Testdateien umfassen auch Support-/Fixture-/Probeprogramme,
nicht ausschließlich `test_*.py`. Pythoncode in Markdownblöcken ist nicht Teil
dieser AST-Dateizählung; Ruff-Format prüft zusätzlich solche Codeblöcke.

## Ungenutzter Code und Duplikate

Kein vollständiges Modul und keine öffentliche Funktion/Klasse wurde als sicher
ungenutzt entfernt. Die fünf AST-leeren Src-Dateien sind `tools_organizer/calendar.py`,
`tools_parsing/augment.py`, `utils/__init_.py`, `utils/file_helper.py` und
`utils/word_helper.py`. Das belegt Platzhalter, keine Löschfreigabe. `__init_.py`
ist kein regulärer Paketinitializer; die Namespacepakete funktionieren trotzdem.

Die Root- und Worker-Manifeste enthalten keine `project.scripts`- oder
`project.entry-points`-Registrierungen. Explizite Moduleinstiege, Prozessregistry,
Subprozessrunner und dokumentierte Shell-/Make-Aufrufe wurden berücksichtigt.
Die einzige syntaktisch gefundene dynamische Importfunktion innerhalb `src` ist
`__import__('hashlib')` in `tools_materials/parse_pdf.py:100`; das schließt externe
Plugins oder dynamisch aufgebaute Aufrufe außerhalb dieser Scanmethode nicht aus.

Sieben exakte AST-Funktionsduplikatgruppen (je zwei Funktionen, mindestens elf
Quellzeilen): drei HTML/URL-Helfer (`_clean_text`, `_scrape_image`, `_is_blacklisted`),
`_subdivide_heading` in PDF/Wikiklassifikation und drei Record-/Payloadbuilder in
`run_record_upload`/`tools_rag.chunk`. Namen, Defaults und Dekoratoren wurden
mitverglichen; Kommentar-/Positionsunterschiede nicht. Nahezu gleiche Funktionen
werden nur als manuelle Konsolidierungskandidaten behandelt, nicht als automatisch
gleichwertig. Details und Positionen stehen im JSON und in der Risikomatrix.

Die **identische doppelte Definition** von `RETRYABLE_STATUS_CODES` wurde im
implementierten Retry-Paket entfernt. Alle anderen Duplikate bleiben erhalten,
bis Inputs, Klassenidentität, Sideeffects und Aufruferkompatibilität geprüft sind.

## APIs, Dependencies und Validierung

Die Suche nach alten Pydantic-Aufrufmustern (`@validator`, `root_validator`,
`parse_obj`, `parse_raw`, `.dict()`, `class Config`) liefert im aktiven Src-Bestand
keinen entsprechenden bestätigten APIbefund. Gefundene `.json()`-Aufrufe gehören
zu HTTPresponses, Streamlit oder eigenen IOmethoden und wurden nicht als
deprecated Pydantic-API fehlklassifiziert. Die Suche nach alten OpenAI-
`ChatCompletion`-/`Completion`-Aufrufen und entfernten NumPy-Skalaraliasen ergab
ebenfalls keinen bestätigten Src-Treffer. Das ist keine vollständige SDKprüfung.

Doppelte Dependencies im Root-Manifest und abweichende Modellkonfigurationen sind
dagegen konkret belegt (R08/R14). Die vorhandenen Pydantic-v2-Content-/Jobmodelle,
Versionsfelder, Hash-/Locatorvalidierung und negativen Store-/Workflowtests bilden
die stärkeren aktuellen Grenzen. Legacy-globales Envloading, ungebundene Namen,
freie IO und wenig dokumentierte Fehler bleiben eigene Auditbereiche.
Ein Online-Vulnerabilitätsaudit oder pauschale Behauptungen veralteter Pakete
werden ohne passenden Nachweis ausdrücklich nicht ergänzt.

## Bewusst nicht verändert

Unverändert bleiben sämtliche Parser-/Knowledge-/RAGmodelle und Pipelines,
Konfigurationen, moderne Material-/ZIPgrenzen, Content-/Evaluation-Stores,
Job-/Workflow-/Deploymentmodule, Runner, Manifeste, Locks und Sicherheitsverträge.
Nur `src/core/retry.py`, `src/utils/path_helper.py` und
`src/utils/zipfile_helper.py` wurden im Anwendungscode bearbeitet.
Die vollständige Dateiliste unten umfasst daher zugleich die überprüfbare Menge
aller bewusst unveränderten Src-Module: alle außer diesen drei.

Verknüpfte Ergebnisse: [Risiken](maint03_risk_matrix.md),
[Architektur](maint03_architecture_review.md),
[Umsetzung](maint03_modernization_plan.md), [Validierung](maint03_validation.md).

## Vollständiger Src-Modulindex

Die Aufgaben ergeben sich aus obiger Bereichszuordnung und den Modul-/Symbolnamen;
die Kennzahlen sind AST-Messwerte des final geprüften Src-Arbeitsbaums.

| Modul unter `src/` | Zeilen | Funktionen / Klassen | Aufgabe (Modulbeschreibung oder Symbole) |
| --- | ---: | --- | --- |
| `agent/prompts/prompt_know_extract.py` | 291 | 3 / 0 | build_visual_verification_prompt, extract_visual_knowledge_prompt, build_knowledge_extraction_prompt |
| `agent/prompts/prompts_know_consolidate.py` | 159 | 0 / 0 | Platzhalter / Modulkonstanten |
| `agent/prompts/sop_prompts.py` | 141 | 0 / 0 | Platzhalter / Modulkonstanten |
| `agent/templates/sop_template.py` | 59 | 0 / 0 | ## YAML |
| `attach_mathe_vorkurs_urls.py` | 154 | 3 / 0 | load_url_mapping, get_playlist_index_from_filename, attach_urls_to_transcripts |
| `content_store/__init__.py` | 5 | 0 / 0 | Offline content persistence; bundle verification remains disabled until C23-02B. |
| `content_store/_testing.py` | 399 | 8 / 1 | Internal synthetic fixture contract, NEVER a verified CS50/publication adapter. |
| `content_store/adapters.py` | 687 | 15 / 6 | Offline, explicit CS50 bundle verification. No Knowledge or inference imports. |
| `content_store/artifacts.py` | 273 | 14 / 1 | Private POSIX blob primitives. Internal only: SHA possession is not authority. |
| `content_store/backup.py` | 413 | 12 / 3 | Isolated manifest-last snapshots via SQLite backup API. Never activation. |
| `content_store/errors.py` | 41 | 1 / 9 | Closed error codes suitable for later redacted transport adapters. |
| `content_store/http.py` | 190 | 6 / 2 | Content routes inside the authenticated C16 gateway, not another server. |
| `content_store/index_models.py` | 225 | 10 / 7 | C24 projection contracts. No index backend, generation activation or I/O. |
| `content_store/index_projection.py` | 718 | 11 / 1 | One scoped read-only ContentStore projection. No parser, backend or file output. |
| `content_store/inventory.py` | 305 | 9 / 5 | Read-only evaluation of an explicit bundle list using the existing B gates. |
| `content_store/limits.py` | 65 | 3 / 0 | Fixed conservative single-host limits; no retries or production auto-tuning. |
| `content_store/models.py` | 368 | 18 / 18 | content-v1 identity domains; original payloads are always opaque exact bytes. |
| `content_store/operations.py` | 1000 | 17 / 0 | Explicit single-host recovery/integrity. No parsing, adoption or auto-release. |
| `content_store/operations_models.py` | 126 | 2 / 7 | Durable post-verification commit intentions, not caller publication authority. |
| `content_store/publication.py` | 471 | 10 / 0 | Verified adapters use the existing content-v1 transaction/artifact primitives. |
| `content_store/read_files.py` | 50 | 3 / 0 | Linux anonymous sealed response files; fixed ABI, no content execution. |
| `content_store/read_models.py` | 152 | 1 / 13 | Versioned opt-in configuration and redacted content wire contracts. |
| `content_store/read_views.py` | 206 | 9 / 0 | Deliberate metadata allowlists. Internal payloads remain byte-identical. |
| `content_store/reader.py` | 529 | 18 / 4 | Authorized keyset projections over the existing content-v1 register. |
| `content_store/schema.py` | 155 | 1 / 0 | Exact content-v1 DDL. No adoption, upgrade, queue or automatic migration. |
| `content_store/search_http.py` | 139 | 5 / 2 | Read-only C16 search adapter. Keep the retrieval guard through HTTP delivery. |
| `content_store/search_models.py` | 86 | 3 / 3 | Opt-in lexical HTTP contract; hits/pages remain the existing C24 DTOs. |
| `content_store/source_status.py` | 198 | 3 / 2 | Source-local catalogue status, never a substitute for read-time byte verification. |
| `content_store/store.py` | 867 | 38 / 1 | Independent content-v1 register. No implicit initialization or bundle import. |
| `core/config.py` | 499 | 20 / 26 | FolderEnvVars, load_folder_env_vars, AgenticEnvVars, load_agentic_env_vars, MLOpsEnvVars … |
| `core/config_knowledge.py` | 51 | 0 / 1 | KnowledgeSettings |
| `core/config_parsing.py` | 216 | 0 / 21 | ParseFileSettings, ParseDOCXSettings, ParseHTMLSettings, ParseMDSettings, ParseNotebookSettings … |
| `core/config_transcribe.py` | 94 | 0 / 4 | TranscribeSettings, DownloadSettings, RecordingSettings, ScreenshotSettings |
| `core/logger.py` | 206 | 6 / 0 | clear_handlers, create_logger, log_header, log_section, log_rich_section … |
| `core/memory.py` | 52 | 0 / 1 | AppSession |
| `core/memory_lecture.py` | 31 | 0 / 1 | LectureContext |
| `core/memory_parsing.py` | 65 | 0 / 2 | PARSER_BACKEND, ParseContext |
| `core/memory_sop.py` | 73 | 0 / 2 | LLMContext, SOPGenContext |
| `core/memory_transcribe.py` | 48 | 0 / 1 | AudioContext |
| `core/mlflow_logger.py` | 246 | 13 / 1 | ExperimentLogger, get_experiment_logger |
| `core/monitoring_validation.py` | 277 | 6 / 1 | Offline structural checks, explicitly distinct from native product validation. |
| `core/observability.py` | 26 | 1 / 0 | configure_llm_observability |
| `core/pipeline_metrics.py` | 232 | 3 / 2 | Metrics v1: bounded aggregate samples, no exporter, I/O or worker imports. |
| `core/retry.py` | 233 | 8 / 0 | is_retryable_exception, retry_remote_call, retry_llm_call, retry_download, retry_summary … |
| `evaluation_store/__init__.py` | 1 | 0 / 0 | Explicit, private human review persistence; no automatic source publication. |
| `evaluation_store/http.py` | 178 | 3 / 1 | Opt-in human review capability inside the existing authenticated gateway. |
| `evaluation_store/models.py` | 225 | 5 / 20 | Workflow envelopes around the authoritative C23/C24 gold contracts. |
| `evaluation_store/service.py` | 753 | 14 / 1 | Live-authorized review operations under Content -> Evaluation lock order. |
| `evaluation_store/store.py` | 258 | 8 / 1 | Bounded append-only ledger with transactional materialized heads, no migration. |
| `job_control/__init__.py` | 1 | 0 / 0 | Local offline job control. No service or worker starts on import. |
| `job_control/adapter_worker.py` | 153 | 5 / 0 | Fixed offline adapter entry point. Never takes commands or source host paths. |
| `job_control/catalog.py` | 187 | 6 / 0 | Only declared, hashed operator inputs. No browser filesystem traversal. |
| `job_control/controller.py` | 251 | 14 / 2 | Authorized short operations only. Actual execution belongs to the worker. |
| `job_control/executor.py` | 225 | 6 / 1 | Single bounded Linux supervisor, independent from the HTTP lifecycle. |
| `job_control/guardian.py` | 264 | 10 / 0 | Linux guardian: confirmed process-group cleanup before terminal status. |
| `job_control/http.py` | 448 | 9 / 2 | Bounded local JSON HTTP adapter; no file serving, proxy roles or executor. |
| `job_control/import_http.py` | 223 | 3 / 1 | Authenticated import selection/plan; actual writes stay in the C16 worker. |
| `job_control/import_jobs.py` | 258 | 9 / 0 | Pinned byte snapshots -> real C23 candidate -> existing ContentStore publication. |
| `job_control/import_models.py` | 66 | 1 / 4 | Controlled C16 imports of operator-pinned existing C23 bundles. |
| `job_control/index_http.py` | 154 | 3 / 1 | Scoped index status and approved inputs in the existing C16 gateway. |
| `job_control/index_jobs.py` | 412 | 12 / 0 | Approved catalog selection -> existing builder, always through the C16 worker. |
| `job_control/index_models.py` | 94 | 4 / 4 | C16 index job input and redacted status; existing C24 index formats unchanged. |
| `job_control/metrics.py` | 138 | 2 / 0 | Pull-only SQLite aggregates following the published C15 contract, if present. |
| `job_control/models.py` | 285 | 7 / 16 | Versioned transport/configuration contracts; no Knowledge business models. |
| `job_control/operations.py` | 340 | 12 / 0 | Local single-host operations for C22-managed roles; no remote deployment. |
| `job_control/pdf_adapter.py` | 74 | 2 / 0 | Approved receipt workspace -> private PDF-v2 workspace, using existing runners. |
| `job_control/registry.py` | 151 | 2 / 1 | Two default entries; opt-in PDF and workflow. No command/path parameters. |
| `job_control/store.py` | 311 | 15 / 3 | Private SQLite v1 state. Atomic requests and bounded durable structured events. |
| `llm/data_llm.py` | 33 | 0 / 2 | LLMProvider, LLMUsage |
| `llm/model_litellm.py` | 192 | 5 / 1 | LLMClient |
| `model_course.py` | 7 | 0 / 0 | Explicit Content/ACL course scope; CS50 discovery keeps its own closed set. |
| `model_discovery/cs50.py` | 182 | 7 / 9 | Offline discovery contracts; independent of lecture execution models. |
| `model_discovery/cs50_index.py` | 299 | 8 / 3 | Derived transcript index contracts; no embedding/DB SDK import or source mutation. |
| `model_discovery/cs50_selection.py` | 65 | 1 / 5 | Immutable dry-run contracts; action names do not import execution configuration. |
| `model_evaluation/content_retrieval.py` | 394 | 11 / 20 | Independent region review and offline evidence; no replacement for live ACLs. |
| `model_evaluation/material_evaluation.py` | 166 | 5 / 5 | Evaluation-only corpus/review contracts; reuse Content locators and B bundles. |
| `model_evaluation/math_evaluation.py` | 138 | 3 / 6 | Independent formula evaluation contracts; never Knowledge verification flags. |
| `model_knowledge/data_knowledge.py` | 898 | 6 / 49 | KnowledgeSemanticType, MathExpressionType, Domain, KnowledgeSource, KnowledgeEntityType … |
| `model_lecture/data_resources.py` | 322 | 3 / 20 | LectureResourceType, ResourceAction, ActionStatus, ResourceKind, LectureResource … |
| `model_materials/assignments.py` | 23 | 1 / 1 | Pinned, explicitly selected overview inputs for additive C18 discovery. |
| `model_materials/course.py` | 315 | 6 / 9 | Bounded envelopes around B5; no new execution, queue or receipt contracts. |
| `model_materials/materials.py` | 258 | 11 / 8 | Versioned identities and normalized source blocks, never inferred timestamps. |
| `model_materials/media_plan.py` | 151 | 3 / 7 | Versioned planning inputs; no execution capabilities or new workflow engine. |
| `model_materials/quality.py` | 58 | 2 / 2 | Versioned audit output; source documents retain their existing material models. |
| `model_materials/visual_inventory.py` | 122 | 2 / 4 | Visual observations layered on existing material/location/image contracts. |
| `model_materials/week.py` | 382 | 9 / 12 | Additive week planning contracts; existing discovery, receipts and jobs stay v1. |
| `model_organizer/data_email.py` | 55 | 0 / 3 | Attachment, Mailbox, EmailMessage |
| `model_parsing/__classes_pdf_parsing.py` | 450 | 0 / 0 | class BaseMeta(BaseModel): |
| `model_parsing/apollo_extractor.py` | 404 | 3 / 1 | ApolloCleanExtractor |
| `model_parsing/base_assembler.py` | 334 | 7 / 1 | BaseAssembler |
| `model_parsing/base_classes_parsing.py` | 523 | 0 / 51 | BaseMeta, ElementMeta, DrawingMeta, HeadingMeta, ListMeta … |
| `model_parsing/base_classifier.py` | 59 | 3 / 1 | BaseClassifier |
| `model_parsing/base_cleaner.py` | 18 | 1 / 1 | BaseCleaner |
| `model_parsing/base_extractor.py` | 78 | 5 / 1 | BaseExtractor |
| `model_parsing/classes_html_parsing.py` | 54 | 0 / 7 | TextNode, CodeNode, LinkNode, ImageNode, CiteNode … |
| `model_parsing/data_classes_wiki.py` | 132 | 0 / 4 | WikiPageMeta, ResultItem, SearchResult, WikiPage |
| `model_parsing/document_assembler.py` | 393 | 4 / 1 | DocumentAssembler |
| `model_parsing/docx_extractor.py` | 593 | 15 / 1 | DOCXCleanExtractor |
| `model_parsing/feature_enricher.py` | 426 | 8 / 1 | FeatureEnricher |
| `model_parsing/html_extractor.py` | 738 | 12 / 1 | HTMLCleanExtractor |
| `model_parsing/notebook_extractor.py` | 479 | 6 / 1 | NoteBookCleanExtractor |
| `model_parsing/pdf_assembler.py` | 471 | 4 / 1 | PDFAssembler |
| `model_parsing/pdf_classifier.py` | 516 | 13 / 1 | PDFClassifier |
| `model_parsing/pdf_cleaner.py` | 328 | 7 / 1 | PDFCleaner |
| `model_parsing/pdf_extractor.py` | 909 | 22 / 1 | PDFCleanExtractor |
| `model_parsing/pdf_merger.py` | 541 | 11 / 1 | PDFMerger |
| `model_parsing/text_classifier.py` | 423 | 4 / 1 | TXTClassifier |
| `model_parsing/text_extractor.py` | 688 | 3 / 2 | TXTCleanExtractor, MDCleanExtractor |
| `model_parsing/url_extractor.py` | 588 | 8 / 1 | URLCleanExtractor |
| `model_parsing/wiki_assembler.py` | 133 | 3 / 1 | WikiPageAssembler |
| `model_parsing/wiki_classifier.py` | 373 | 9 / 1 | WikiClassifier |
| `model_parsing/wiki_client.py` | 333 | 7 / 1 | WikipediaClient |
| `model_rag/data_records.py` | 181 | 0 / 11 | RAGRecord, SourceReference, RetrievedChunk, IngestedChunk, ExtractedFact … |
| `model_rag/data_sop.py` | 126 | 0 / 9 | SOPType, SOPChapter, AssignedFact, UnassignedFact, FactEvaluationItem … |
| `model_rag/templates_sop.py` | 178 | 0 / 0 | Platzhalter / Modulkonstanten |
| `model_transcribe/data_transcribe.py` | 148 | 4 / 6 | TranscriptSegment, TranscriptSource, DownloadStrategy, DownloadResult, TranscriptProvenance … |
| `model_transcribe/provider_transcript.py` | 143 | 3 / 1 | FasterWhisperProvider, get_transcription_provider |
| `run_audio_recording.py` | 281 | 6 / 0 | run_audio_recording, detect_monitor_source, start_system_audio_recording, stop_system_audio_recording, fixed_audio_recording … |
| `run_audio_transcription.py` | 109 | 2 / 0 | run_audio_transcription, audio_transcription |
| `run_chunk_embed.py` | 116 | 1 / 0 | run_chunk_and_embed |
| `run_dependency_check.py` | 308 | 5 / 0 | run_pip_audit, extract_findings, build_summary, parse_args, main |
| `run_knowledge_consolidation.py` | 185 | 4 / 0 | Existing consolidation entry points with explicit offline, read-only defaults. |
| `run_knowledge_extraction.py` | 259 | 4 / 0 | main, run_knowledge_extraction, is_regular_lecture, knowledge_extraction |
| `run_knowledge_improvement.py` | 720 | 4 / 0 | validate_knowledge_context, run_visual_enrichment, find_local_media_path, visual_enrichment |
| `run_lecture_compilation.py` | 245 | 8 / 0 | main, run_lecture_compilation, lecture_compilation, prepare_course, get_block_ids … |
| `run_lecture_planning.py` | 183 | 3 / 0 | run_lecture_planning, plan_course_tasks, lecture_planning |
| `run_lecture_preparation.py` | 377 | 3 / 0 | run_lecture_preparation, lecture_preparation, extract_course_materials |
| `run_lecture_processing.py` | 105 | 2 / 0 | run_lecture_processing, lecture_processing |
| `run_mlflow_setup_test.py` | 33 | 0 / 0 | Platzhalter / Modulkonstanten |
| `run_record_upload.py` | 289 | 7 / 0 | run_record_upload, build_rag_records_from_transcript, build_rag_records_from_knowledge, build_formula_rag_records, build_knowledge_rag_records … |
| `run_st_SOP_generation.py` | 280 | 1 / 0 | run_st_sop_generation |
| `run_st_pdf_extract.py` | 47 | 1 / 0 | run_pdf_extraction |
| `run_video_transcription.py` | 284 | 3 / 0 | run_video_transcription, add_transcript_provenance, video_transcription |
| `runtime_paths.py` | 188 | 6 / 0 | Explicit persistent output grants for mounts inside an application checkout. |
| `tools_eda/profile_dataset.py` | 193 | 1 / 0 | profile_dataset |
| `tools_evaluation/evaluate_materials.py` | 587 | 7 / 0 | Read-only corpus evaluation using existing gates; no new extraction or gold. |
| `tools_evaluation/evaluate_math.py` | 278 | 11 / 0 | Deterministic evaluation of independent gold/prediction pairs, no extraction. |
| `tools_evaluation/evaluate_retrieval.py` | 537 | 7 / 0 | Bounded offline evaluation of supplied evidence and actual C24 result DTOs. |
| `tools_evaluation/generation_metrics.py` | 23 | 0 / 0 | Zur automatisierten Messung dieser Metriken setzen Entwickler meist auf sogenannte "LLM-as-a-Judge"-Frameworks. |
| `tools_evaluation/math_equivalence.py` | 78 | 1 / 0 | Optional, isolated and bounded equivalence checking of parsed syntax trees. |
| `tools_evaluation/math_predictions.py` | 60 | 1 / 0 | Bind an existing visual prediction to independently supplied gold, read-only. |
| `tools_evaluation/math_reports.py` | 103 | 4 / 0 | Deterministic report serialization and explicit exclusive bundle publication. |
| `tools_evaluation/math_syntax.py` | 318 | 14 / 3 | Bounded notation grammar for evaluation, not a renderer or document parser. |
| `tools_evaluation/retrieval_metrics.py` | 28 | 2 / 0 | Backend-independent arithmetic; callers establish independent relevance first. |
| `tools_evaluation/sympy_worker.py` | 215 | 5 / 1 | Private bounded polynomial worker. Receives validated notation trees, never code. |
| `tools_knowledge/batch_cs50.py` | 81 | 2 / 0 | B05: thin six-course scope over the same sequential scheduler and budget. |
| `tools_knowledge/bind_cs50_transcript.py` | 359 | 14 / 4 | Read-only checked SRT input binding; no runner dispatch or inference calls. |
| `tools_knowledge/complete_cs50_lecture.py` | 165 | 1 / 1 | Full-lecture completion requires every verified A01 chunk, never file existence. |
| `tools_knowledge/consolidate_knowledge.py` | 455 | 11 / 0 | build_statement_evidence, build_formula_evidence, evidence_overlaps, statement_score, expression_score … |
| `tools_knowledge/consolidation_run.py` | 522 | 11 / 4 | Offline consolidation audit and immutable write-ahead receipts (POSIX). |
| `tools_knowledge/consolidation_validation.py` | 294 | 6 / 1 | Conservative identity/evidence checks shared by consolidation and its runner. |
| `tools_knowledge/cs50_budget.py` | 196 | 9 / 5 | A02: durable, shared conservative request reservations; no refunds/retries. |
| `tools_knowledge/cs50_checkpoint.py` | 341 | 16 / 6 | Versioned execution receipts, not new Knowledge business models (POSIX). |
| `tools_knowledge/cs50_evaluation.py` | 173 | 4 / 4 | C01: manual review contract. Valid cue bindings never imply semantic/didactic truth. |
| `tools_knowledge/cs50_extraction_provider.py` | 248 | 14 / 4 | Optional bounded extraction adapters, using the existing prompt and result model. |
| `tools_knowledge/cs50_precise_evidence.py` | 155 | 4 / 1 | Candidate cue references; authoritative times come only from original segments. |
| `tools_knowledge/cs50_quality.py` | 158 | 1 / 0 | Deterministic diagnostic proxies; no relevance judging or automatic filtering. |
| `tools_knowledge/find_knowledge.py` | 483 | 13 / 0 | build_knowledge_source_metadata, make_knowledge_source_metadata, build_transcript_chunks, enrich_chunks, _extract_knowledge_contract … |
| `tools_knowledge/postprocess_visual.py` | 1316 | 32 / 4 | EvidenceItem, CanonicalKnowledgeItem, KnowledgeRelation, CanonicalKnowledgeDocument, deduplicate_evidence … |
| `tools_knowledge/rebuild_knowledge.py` | 1385 | 29 / 0 | evidence_overlaps_interval, evidence_time_range, evidence_time_windows, formula_requires_visual_verification, select_visual_verification_targets … |
| `tools_knowledge/report_cs50_schedule.py` | 123 | 2 / 0 | B04: weighted quality/coverage from validated completion sets, never ratios averaged. |
| `tools_knowledge/run_cs50_lecture.py` | 454 | 9 / 2 | Verified CS50 lecture execution; bounded pilot remains a separate entry point. |
| `tools_knowledge/schedule_cs50.py` | 313 | 9 / 6 | B03: explicit sequential course scope, shared budget and verified next-pending. |
| `tools_knowledge/semantic_knowledge.py` | 758 | 13 / 0 | get_statement_time_range, build_semantic_statement_batches, statement_to_llm_payload, consolidate_semantic_batch, validate_semantic_batch_result … |
| `tools_lecture/adapt_cs50.py` | 475 | 12 / 5 | Deterministic metadata adapter. Never dispatch these tasks to the legacy runner. |
| `tools_lecture/assemble_course.py` | 198 | 2 / 0 | build_lecture_course_from_folder, build_lecture_resource |
| `tools_lecture/cs50_manifest.py` | 181 | 5 / 4 | Validate CS50 HTML fixtures without fetching or extracting course content. |
| `tools_lecture/discover_course.py` | 146 | 2 / 0 | classify_course_file, parse_lecture_filename |
| `tools_lecture/execute_cs50.py` | 384 | 13 / 2 | Controlled CS50 SRT execution; no general processing or inference imports. |
| `tools_lecture/material_handoff.py` | 162 | 6 / 2 | Checked read-only lecture material references. Never create ResourceTasks. |
| `tools_lecture/plan_lecture.py` | 442 | 15 / 0 | matches_lecture_no, get_resource_path, classify_resource_file, get_transcript_actions, get_knowledge_actions … |
| `tools_lecture/prepare_cs50.py` | 651 | 22 / 1 | Offline CS50 index/week discovery. Linked detail pages are never opened. |
| `tools_lecture/prepare_lecture.py` | 384 | 12 / 0 | get_resource_metadata_from_url, enrich_resource_metadata, normalize_resource_title, parse_resource_title, validate_lecture_resources … |
| `tools_lecture/prepare_loviscach.py` | 537 | 18 / 0 | find_lecture_table, contains_lecture_resources, get_lecture_block_nodes, lecture_block_extraction, infer_block_id … |
| `tools_lecture/process_lecture.py` | 310 | 5 / 0 | execute_task, execute_document_action, build_document_parse_context, execute_media_action, download_document |
| `tools_lecture/select_cs50.py` | 439 | 8 / 0 | Pure offline resource selection. Never creates or executes ResourceTasks. |
| `tools_materials/assignments.py` | 243 | 3 / 0 | Shared one-level assignment derivation; no URL acquisition or execution. |
| `tools_materials/batch.py` | 656 | 17 / 3 | Explicit CS50 archive-to-C18 handoff. C16 remains the only execution queue. |
| `tools_materials/capacity.py` | 140 | 13 / 3 | C26 capacity checks around existing bounded writers; not a disk quota. |
| `tools_materials/code_discovery.py` | 124 | 2 / 0 | Opt-in, one-level promotion of links from declared, bound code indexes. |
| `tools_materials/code_evidence.py` | 151 | 2 / 0 | Read-only bridge from immutable B6 imports to B7; no reparse or staging. |
| `tools_materials/code_import.py` | 449 | 12 / 1 | Thin offline Python/ZIP adapter over code-v1, material quality and handoff. |
| `tools_materials/code_structure.py` | 90 | 2 / 0 | Optional AST projection in an isolated, resource-limited Python process. |
| `tools_materials/code_zip.py` | 232 | 4 / 0 | Bounded ZIP inspection in memory. Never extract member paths to disk. |
| `tools_materials/course.py` | 561 | 12 / 0 | Bounded course planning and read-only preflight using the existing B5 planner. |
| `tools_materials/download.py` | 290 | 7 / 2 | Material archiving built on the existing CS50 bounded streaming primitive. |
| `tools_materials/html_projection.py` | 163 | 4 / 3 | DOM-bound metadata for the existing material windows; never rewrite source text. |
| `tools_materials/inventory.py` | 237 | 6 / 0 | Catalog existing discovery nodes, variants and every snapshot link/image. |
| `tools_materials/mapping.py` | 164 | 4 / 2 | Read-only material input mapping. No transcript collection/Knowledge changes. |
| `tools_materials/media_evidence.py` | 132 | 1 / 0 | Read-only verification of explicitly named evidence; never scans archives. |
| `tools_materials/media_plan.py` | 528 | 6 / 0 | Deterministic F0-F6 proposals, not an executable acquisition pipeline. |
| `tools_materials/parse_code.py` | 55 | 1 / 0 | Strict local text/source import. No evaluation, execution or archive extraction. |
| `tools_materials/parse_html.py` | 478 | 16 / 0 | Structured HTML/assignment import. No fetches, rendered JS or inference. |
| `tools_materials/parse_pdf.py` | 118 | 4 / 0 | PyMuPDF text/images in a killable CPU/address-space/page/output bounded worker. |
| `tools_materials/pdf_worker.py` | 304 | 5 / 0 | Private bounded subprocess entrypoint. Stdout is a capped result file. |
| `tools_materials/processing.py` | 305 | 6 / 1 | Explicit snapshot plan and hash-bound material parser/resume orchestration. |
| `tools_materials/profiles.py` | 117 | 4 / 0 | Local profiles for the existing CS50 adapter, never a source acquisition API. |
| `tools_materials/quality.py` | 808 | 14 / 1 | Read-only offline checks of exact artifact bytes and existing CS50 contracts. |
| `tools_materials/quality_projection.py` | 216 | 1 / 0 | Technical integrity checks for v2 HTML handoff metadata, without raw reparsing. |
| `tools_materials/storage.py` | 61 | 5 / 0 | Reuse the CS50 executor's hash, path, directory sync and receipt primitives. |
| `tools_materials/transcripts.py` | 387 | 10 / 1 | Bounded offline adapter to the integrated official transcript importer. |
| `tools_materials/visual_inventory.py` | 759 | 12 / 0 | Read-only material visual inventory; no parser, image download or inference. |
| `tools_materials/visual_worker.py` | 251 | 6 / 0 | Private, bounded source observations. No image extraction, rendering or OCR. |
| `tools_materials/week.py` | 693 | 8 / 0 | Read-only week inventory and admission plans around existing C26 adapters. |
| `tools_organizer/calendar.py` | 36 | 0 / 0 | Platzhalter / Modulkonstanten |
| `tools_organizer/email.py` | 114 | 1 / 0 | check_mailbox |
| `tools_parsing/assemble_pdf.py` | 362 | 1 / 0 | assemble_single_pdf |
| `tools_parsing/augment.py` | 0 | 0 / 0 | Platzhalter / Modulkonstanten |
| `tools_parsing/classify_txt.py` | 62 | 1 / 0 | classify_txt_file |
| `tools_parsing/extract_html.py` | 84 | 1 / 0 | extract_html_file |
| `tools_parsing/extract_images.py` | 197 | 3 / 0 | scrape_images_from_url, run_scrape_images_from_url, _extract_image_urls |
| `tools_parsing/extract_md.py` | 71 | 1 / 0 | extract_md_file |
| `tools_parsing/extract_medium.py` | 294 | 1 / 0 | extract_from_medium |
| `tools_parsing/extract_notebook.py` | 117 | 1 / 0 | extract_notebook_json |
| `tools_parsing/extract_pdf.py` | 123 | 1 / 0 | extract_pdf_file |
| `tools_parsing/extract_txt.py` | 69 | 1 / 0 | extract_txt_file |
| `tools_parsing/extract_wiki.py` | 150 | 1 / 0 | extract_wiki_article |
| `tools_parsing/parse_document.py` | 259 | 5 / 0 | parse_document, render_bbox, find_unresolved_formulas, parse_document_docling, parse_pdf_diy |
| `tools_parsing/post_extract_processing_pdf.py` | 436 | 1 / 0 | post_process_pdf |
| `tools_parsing/post_extract_processing_wiki.py` | 424 | 1 / 0 | process_wiki |
| `tools_parsing/search_wiki.py` | 65 | 1 / 0 | wiki_article_search |
| `tools_rag/chunk.py` | 528 | 10 / 0 | chunk_text, document_json_to_blocks, merge_small_blocks, _normalize_text_value, prepare_chunk_df … |
| `tools_rag/content_fts.py` | 172 | 5 / 0 | Source-local FTS5 backend. No ContentStore writes, embeddings or SDKs. |
| `tools_rag/content_index.py` | 974 | 30 / 2 | Explicit private FTS generations and live-authorized lexical retrieval. |
| `tools_rag/content_index_files.py` | 141 | 7 / 1 | Private bounded derivative files using existing ContentStore inode primitives. |
| `tools_rag/content_index_models.py` | 167 | 1 / 13 | Versioned derived-index, receipt and redacted lexical-search contracts. |
| `tools_rag/content_vector_models.py` | 184 | 10 / 6 | ContentRecord vectors, deliberately incompatible with timed TranscriptPayload. |
| `tools_rag/content_vector_transport.py` | 104 | 6 / 1 | Isolated fake transport. No SDK, model files, endpoints or environment access. |
| `tools_rag/content_vectors.py` | 515 | 20 / 2 | Optional ContentRecord adapter on the existing lifecycle and retrieval guard. |
| `tools_rag/create_embeds.py` | 254 | 6 / 0 | _to_chroma_scalar, _create_or_update_metadata, load_embedding_model, create_embed_from_query, embed_text … |
| `tools_rag/cs50_collection.py` | 58 | 3 / 0 | Explicit Qdrant collections; imports SDK only when actually used. |
| `tools_rag/cs50_embeddings.py` | 249 | 13 / 2 | Offline local encoding and additive exact-text offset windows. No model downloads. |
| `tools_rag/cs50_ingestion.py` | 571 | 17 / 4 | Immutable source plans, verified vector artifacts and fail-closed Qdrant resume. |
| `tools_rag/cs50_knowledge_index.py` | 445 | 6 / 3 | Read-only future Knowledge collection mapping. No DB/LLM execution path. |
| `tools_rag/cs50_orchestration.py` | 89 | 3 / 0 | Source orchestration reuses CS50Executor; no index/LLM operation here. |
| `tools_rag/cs50_retrieval.py` | 113 | 2 / 1 | Text retrieval only; no answer generation, downloads or implicit index writes. |
| `tools_rag/cs50_retrieval_evaluation.py` | 170 | 4 / 3 | Verified source windows and manual judgments; fake scores are never quality metrics. |
| `tools_rag/generate_chunks_facts.py` | 640 | 16 / 0 | _ingest_chunk, extract_chunk_facts, extract_facts, build_chunk_fact_pool, filter_facts … |
| `tools_rag/generate_sop.py` | 436 | 8 / 0 | get_supporting_chunks, plan_core_chapter, format_fact_ids, build_fact_lookup, filter_chapter_facts … |
| `tools_rag/retrieve.py` | 456 | 8 / 0 | get_templates, build_retrieval_queries, retrieve_for_sop, retrieve_chunks, normalise_chroma_results … |
| `tools_rag/text_qa.py` | 42 | 3 / 0 | score_doc, retrieve_docs, build_qa_input |
| `tools_transcribe/extract_audio.py` | 196 | 1 / 0 | download_audio |
| `tools_transcribe/extract_resources.py` | 150 | 3 / 0 | download_lecture_resource, download_subtitles, extract_section_no |
| `tools_transcribe/extract_video.py` | 643 | 11 / 0 | expand_download_window, prepare_local_visual_sections, download_sections_with_retry, download_visual_sections, download_video_section … |
| `tools_transcribe/import_transcript.py` | 182 | 7 / 0 | Import official local transcripts without inference, downloads or execution config. |
| `tools_transcribe/process_subtitle.py` | 276 | 6 / 0 | transcribe_files, add_transcript_provenance, parse_subtitle, _timestamp_to_seconds, _clean_vtt_text … |
| `tools_transcribe/process_url.py` | 263 | 4 / 0 | process_youtube_video, select_subtitle_language, inspect_yt_file, acquire_transcript_source |
| `utils/__init_.py` | 0 | 0 / 0 | Platzhalter / Modulkonstanten |
| `utils/chroma_helper.py` | 342 | 5 / 0 | get_chroma_client, get_chroma_collection, list_files_in_coll, add_chroma_data, run_chroma_query |
| `utils/df_helper.py` | 659 | 22 / 0 | load_dfs, read_french_csv_smart, load_files_from_folder, detect_delimiter, load_processed_files … |
| `utils/dict_helper.py` | 238 | 6 / 0 | load_yaml_config, safe_json_loads, make_json_safe, ensure_json_suffix, save_dict … |
| `utils/docling_helper.py` | 67 | 2 / 0 | get_docling_image_converter, get_docling_converter |
| `utils/email_helper.py` | 684 | 16 / 0 | context_imap_connection, list_mailboxes, detect_mailbox_type, quote_imap_mailbox, get_sent_datetime … |
| `utils/file_helper.py` | 2 | 0 / 0 | Platzhalter / Modulkonstanten |
| `utils/general_helper.py` | 385 | 16 / 0 | get_value, normalize_whitespace, iter_chunks, load_env_vars, inspect_single_function … |
| `utils/html_helper.py` | 104 | 5 / 0 | read_html_file, scrape_source_code, show_element_attributes, normalize_url, check_and_get_elements |
| `utils/latex_helper.py` | 161 | 4 / 0 | normalize_latex, normalize_math_text, validate_latex_basic, find_suspicious_latex_patterns |
| `utils/llm_helper.py` | 249 | 9 / 0 | log_openai_usage, log_anthropic_usage, configure_marvin, get_openai_client, _make_cache_key … |
| `utils/log_helper.py` | 9 | 1 / 0 | log_memory |
| `utils/mlflow_helper.py` | 253 | 3 / 0 | save_model, create_mlflow_client, mlflow_fingerprint_check |
| `utils/path_helper.py` | 364 | 13 / 0 | organize_resource_file, get_resource_target_folder, normalize_name, build_file_index, find_indexed_files … |
| `utils/pdf_helper.py` | 453 | 3 / 0 | pdf_page_count, check_pdf_split, split_pdf |
| `utils/qdrant_helper.py` | 65 | 3 / 0 | get_qdrant_client, ensure_collection, upload_records |
| `utils/spacy_helper.py` | 17 | 2 / 0 | load_spacy_model, remove_stop_words |
| `utils/st_eda_helper.py` | 34 | 1 / 0 | st_df_profile |
| `utils/streamlit_helper.py` | 138 | 3 / 0 | st_file_preview, live_command_demo, show_tree |
| `utils/text_file_helper.py` | 207 | 7 / 0 | get_soffice, convert_docx, read_docx_tables, read_docx_text, read_text_file … |
| `utils/text_helper.py` | 85 | 5 / 0 | normalize_text_for_matching, normalize_label, text_similarity, find_illegal_control_chars, remove_illegal_control_chars |
| `utils/transcribe_helper.py` | 46 | 1 / 0 | get_audio_info |
| `utils/word_helper.py` | 2 | 0 / 0 | Platzhalter / Modulkonstanten |
| `utils/yt_helper.py` | 111 | 3 / 0 | build_base_ydl_opts, format_speed, yt_progress_hook |
| `utils/zipfile_helper.py` | 57 | 3 / 0 | preview_zip_content, unpack_single_zipfile, unpack_entire_zipfolder |
| `workflows/definition.py` | 273 | 2 / 1 | Read-only preparation with existing discovery, selection and parser contracts. |
| `workflows/engine.py` | 386 | 7 / 1 | Deterministic decisions and sequential execution inside one bounded C16 job. |
| `workflows/graph.py` | 22 | 1 / 0 | Deterministic graph validation, no execution or implicit dependency invention. |
| `workflows/http.py` | 388 | 12 / 1 | Authorized C18 HTTP handoff; C16 alone queues, executes and cancels jobs. |
| `workflows/http_models.py` | 114 | 1 / 9 | C20-B wire envelopes reuse the complete C18 report and C16 job contracts. |
| `workflows/models.py` | 149 | 4 / 5 | Small execution envelopes around existing C16 and material contracts. |
| `workflows/service.py` | 269 | 8 / 0 | Workflow lifecycle delegates every actual run/cancel to the existing C16 queue. |
| `workflows/state.py` | 67 | 5 / 0 | Existing private C16 workspace, atomic JSON metadata, no database or queue. |
| `workflows/validation.py` | 152 | 5 / 0 | Hash, provenance, schema and exact configuration checks before any skip. |
