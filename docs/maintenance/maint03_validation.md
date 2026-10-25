# MAINT-03 – Validierung und ausstehender Integrationsabschluss

25.10.2026. Basis `e68275205fefb7a5f6db42bc45060e505bfcefb5`, Branch
`audit/maint03-legacy-modernization`. C26-Produktionsstatus **HOLD**.

## Bewertung

Die drei kleinen Arbeitspakete und 34 neuen Regressionstests sind implementiert.
Inventar, 19 priorisierte Befunde, Architekturreview und Folgeplan liegen unter
`docs/maintenance/`. Der Repositoryabschluss bleibt **ausstehend**: kein lokaler
Commit, kein Draft-PR, keine Defaultintegration und keine Cleanupfreigabe.
Diese Einschränkung darf nicht als abgeschlossener Branchlifecycle erscheinen.

## Umgebung und Testgrenzen

Eine vorhandene Python-3.12.12-Testumgebung wurde ausschließlich lesend verwendet:
`/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b6-planning-results/test-env/bin/python`.
Pytest 9.1.1, Pydantic 2.14.1, HTTPX 0.28.1 und PyMuPDF 1.27.2.2 sind vorhanden.
Das ist kein exakter Nachbau des Worker-/Runtime-Locks. Qdrant-SDK, pandas,
python-docx, pydantic-settings und tiktoken fehlen in diesem Interpreter.
Es wurde nichts installiert und kein Modell, Material oder Image heruntergeladen.

Ruff 0.16.0 wurde im vorhandenen Pre-commit-Cache gefunden und direkt ausgeführt;
dies entspricht der konfigurierten Hookversion. Der Testinterpreter selbst enthält
kein Ruff-Modul; der erste `python -m ruff --version`-Versuch scheiterte deshalb.
Anschließend wurde die vorhandene Binärdatei benutzt. Keine Hook-/Dependencyupdates.

Der breite Testlauf verwendet einen temporären Pytest-Plugin-Guard für DNS,
Socket-connect/connect_ex, bind/listen und create_connection im Testhauptprozess.
Ausgeschlossen sind echte Listener-/Transportdateien und Docker-Smokes.
Bestehende Subprozessprobes bleiben separat geprüfte synthetische Offlinepfade;
der Plugin-Guard wird nicht als globaler Subprozesssandboxnachweis ausgegeben.
Keine Netzwerkdienste, Produktionsqueues oder Produktivkomponenten wurden gestartet.
Synthetische lokale Jobs, SQLite-DBs und Crashprobes sind temporäre Testdaten.

## Tatsächlich ausgeführte Prüfungen

| Prüfung | Ergebnis |
| --- | --- |
| Neue Regressionen vor Anwendungscodeänderung | **12 failed, 22 passed**, 2,03 s; reproduzierte IO-/Retryfehler |
| Neue Regressionen nach Korrektur | **34 passed**, 0 failed, 0 skipped; letzter gezielter Lauf 0,54 s |
| Finaler gezielter Kompatibilitätslauf | **38 passed**, 0 failed, 0 skipped, 6,14 s: aktuelle 34 neue Fälle gemeinsam mit Berechtigungstest und den drei SRT-/Evaluatorfällen. Kein eigener neuer Fehler durch die aktuelle IO-Testfixture |
| Gesamte Pytest-Sammlung | **2.508 gesammelt, 7 Collection-Errors**, 7,82 s; alle sieben wegen fehlendem `qdrant_client` |
| Breiter Offline-Regressionslauf | **2.347 passed, 11 failed, 36 skipped**, 2 Warnungen, **2.560,77 s (42:40)**; 2.394 Fälle. Die 34 neuen Fälle sind enthalten, nicht zusätzlich addieren |
| Dieselben elf Fehlerfälle auf unverändertem Master-Quellsnapshot | **5 failed, 6 passed**, 27,55 s; keine Skips. Detaillierte Zuordnung unten |
| Ruff Check im gesamten Repository | **329 Befunde in 103 Dateien**; 139 F821, 67 I001, 52 F401, übrige siehe unten |
| Ruff Check auf geändertem Code und neuen Tests | Retry, ZIP und beide Tests: **passed**. Pfadhelper: **zwei bestehende F821**, keine neue Diagnose |
| Ruff-Diagnosevergleich mit Originalblobs | Für alle drei geänderten Src-Dateien Code+Meldung als Multiset verglichen: **keine neuen Diagnosen**; path_helper zuvor 2 / danach 2 |
| Ruff Format auf fünf bearbeiteten Pythondateien | **5 files already formatted** nach Formatierung ausschließlich der beiden neuen Testdateien |
| Ruff Format im gesamten Repository | **20 Dateien müssten formatiert werden, 760 bereits formatiert** im finalen Lauf; Codebeispiele in Markdown werden mitgeprüft. Kein Massendiff erzeugt |
| ASTscan mit Python 3.12 | **526 ursprüngliche versionierte Pythondateien geparst, 0 Syntaxfehler**; neue Tests zusätzlich geparst |
| Import-/Abhängigkeitsgraph | 281 Src-Module; 6 SCCs mit Lazyimports, 1 syntaktische Top-Level-SCC; **0 zyklische Mitglieder** nach Ausschluss von Main-/TYPE_CHECKING-Zweigen |
| APIvergleich | 24 öffentliche Funktionen der drei Src-Dateien mit denselben Namen/Argumentstrukturen; nur `list_files` erhielt präzisere Typannotationen |
| Frische Prozessimports | `src.utils.path_helper` und `src.core.retry` mit gesperrten Session-/Env-/SDKimports und gesperrtem Netz **passed**. ZIP benötigt weiterhin die kontrollierte Sessionfixture; kein behaupteter echter AppSession-Import |
| Weitere Baselineprobes | Unter umask 0077 derselbe Berechtigungstest reproduziert fehlgeschlagen; nach Modulcache-Austausch derselbe Pydantic-Klassenfehler reproduziert. Harter Prozessabbruch am Directorysync reproduziert zwei Hardlinks und korrekte Backupablehnung |
| Isolierte Async-Reproduktion R13 | Fakeclient, echter Eventloop: `RuntimeError: asyncio.run() cannot be called from a running event loop`; Coroutine danach explizit geschlossen |
| Gecachte Hooks direkt ausgeführt | `check_ast`, `debug_statement_hook` auf fünf Pythondateien, `check_json` auf Evidenz sowie Trailing-Whitespace-/End-of-file-Prüfung auf allen elf Dateien: **passed** |
| Whitespace-/Link-/Fingerprints | `git diff --check`, 23 relative Dokumentlinks, 281 Src-SHA-256-Werte sowie UTF-8/LF/Trailing-Whitespace **passed** |

Die beiden unveränderten F821 im Pfadhelper betreffen `classify_resource_file`
und `run_name` (R15). Die globale Ruff-Verteilung lautet: I001 67, UP035 2,
F821 139, F401 52, B007 6, F841 18, F541 3, F811 6, UP006 1, E741 22,
E722 1, E402 4, E713 1, UP037 1, B009 1, UP034 2, B006 1, UP015 1, B904 1.
Der Bestand ist ausdrücklich nicht lintgrün. Keine Suppressionen hinzugefügt.
Es gibt keine gemessene prozentuale Codeabdeckung.

## Fehleranalyse des breiten Laufs

Der unveränderte Quellsnapshot wurde mittels `git archive HEAD` ausschließlich aus
versioniertem Code, Konfiguration und Testmaterial unter
`/tmp/maint03-baseline-bh2h5f6u` erstellt. Keine privaten Envdateien, Gitdatenbank,
neuen Branches oder Worktreeregistrierungen. Derselbe Interpreter und derselbe
Offlineguard wurden für die elf konkret fehlgeschlagenen Node-IDs verwendet.

| Fälle im breiten Lauf | Fehler / Baselinevergleich / Entscheidung |
| --- | --- |
| `test_cs50_index_end_to_end::test_full_offline_source_to_persisted_qdrant_and_resume[lecture-1/python-10/six-50]` (3) | `ModuleNotFoundError: qdrant_client`, **alle drei auch auf Baseline fehlgeschlagen**. Diese Imports erfolgen erst im Test und wurden deshalb nicht bereits durch die sieben Collection-Errors erkannt. Keine Skips daraus nachträglich behauptet. |
| `test_cs50_llm_smoke::test_real_offline_worker_prepares_schema_before_initialization` (1) | Workerreport enthält `phase=failed`, `error_stage=preparing`, `error_type=ModuleNotFoundError`, fehlendes **tiktoken**, `api_requests=0`. Deshalb fehlt `offline_contract_validated`. **Auf Baseline reproduziert**; die optional gekoppelte Vorbereitung bleibt R05/R17. |
| `test_workflow_http::test_versioned_schema_snapshots_and_original_c16_models` (1) | Versionierte JSON-Schemas und aktuelle Modellschemas unterscheiden sich, unter anderem bei Artifact/schema_version. **Auf Baseline reproduziert**. Keine Schema-Neugenerierung ohne Vertragsreview; kein bewiesener reiner Pydanticversionsfehler. R18. |
| `test_content_store_artifacts::test_private_explicit_root_and_limits` (1) | Im Gesamtlauf kein erwarteter IntegrityError, einzeln auf Baseline bestanden. Mit **umask 0077 auf Baseline reproduziert**: `mkdir(mode=0755)` erzeugt tatsächlich 0700; Storeakzeptanz ist dann korrekt. Testisolation, keine nachgewiesene aufgehobene Dateirechtegrenze. R18. |
| `test_cs50_material_evaluation::test_srt_cue_text_and_known_locator`, `test_dev03_parsing::test_existing_evaluator_recipe_frozen_inputs_and_report_hashes`, `test_transcript_unknown_time::test_unknown_locator_compatible_but_not_srt_binding` (3) | Im Gesamtlauf Pydanticfehler: gleichnamiges frisches `CS50CoursePlan` ist keine Instanz der im alten Adaptermodell gebundenen Klasse. **Alle drei einzeln auf Baseline bestanden**. Austausch des Adaptermoduls bei weiter gecachter Helferklasse reproduziert denselben Fehler auf Baseline; bestehende Fixture-Purges erklären die Klassenidentitätsdrift. R18. |
| `test_content_store_reimport::test_retry_is_recoverable_after_second_interruption[raw]` (1) | Gesamtlauf wählt alten verlassenen Run als Element 0 und findet `retry_of=None`; **Baselinewiederholung bestanden**. `inspect_recovery` sortiert nach ID, nicht nach „neuester Retry“; der Test darf keine Reihenfolge zufälliger IDs voraussetzen. Kein behaupteter stabiler Fehler der Retrytransaktion. R18. |
| `test_cs50_batch_worker::test_managed_worker_cancel_restart_resume_and_stopped_backup[signal]` (1) | Backup verweigert zwei reguläre Dateien mit `nlink=2`: `.material-*` und Receipt im eigenen synthetischen Jobroot. **Baselinewiederholung bestanden**. Zusätzlicher deterministischer Baselineprobe beendet nur den Publikationschild am Directorysync mit Exit 73: gleicher Inode, zwei Links, `inventory` verweigert korrekt. R19; keine produktiven Daten betroffen. |

Die beiden Warnungen betreffen absichtlich doppelte ZIPmembernamen in bestehenden
Negativfixtures. 36 tatsächliche Skips betreffen optionale SDK-/Original-/Profilpfade;
die elf ausgeschlossenen Dateien sind zusätzlich und werden nicht als Skips gezählt.
Kein Gesamtsuitenerfolg behauptet. Sechs erfolgreiche Baselinewiederholungen löschen
die ursprünglichen elf Fehler nicht aus der Statistik. Die gezielten Zustandsprobes
sind eigene Reproduktionen und keine zusätzlich bestandenen Unit-Testfälle.

Der Anwendungscode war vor dem breiten Lauf fertig. Die abschließende
Testfixture-Cachebereinigung wurde zusätzlich im letzten gezielten 34-Fälle-Lauf
validiert; Formatierung und Cacheteardown ändern keine Testassertions.

## Reproduzierbare Befehle

`MAINT_PYTHON` bezeichnet den oben genannten vorhandenen Interpreter,
`MAINT_RUFF` die vorhandene Datei
`/home/robfra/.cache/pre-commit/repokzno83cn/py_env-python3.12/bin/ruff`.
Die temporären Logs liegen unter `/tmp/maint03-*`; sie sind keine zusätzlichen
Produktdateien oder dauerhaften Beweise außerhalb dieses Berichts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  "$MAINT_PYTHON" -m pytest -q -o addopts='' -p no:cacheprovider \
  tests/test_legacy_io_regressions.py tests/test_legacy_retry.py

"$MAINT_RUFF" check --no-cache src/core/retry.py src/utils/path_helper.py \
  src/utils/zipfile_helper.py tests/test_legacy_io_regressions.py \
  tests/test_legacy_retry.py
"$MAINT_RUFF" format --check src/core/retry.py src/utils/path_helper.py \
  src/utils/zipfile_helper.py tests/test_legacy_io_regressions.py \
  tests/test_legacy_retry.py
"$MAINT_RUFF" check --no-cache --output-format=json .
"$MAINT_RUFF" format --check .
git diff --check
```

Die erwarteten zwei ursprünglichen F821 sind beim Gesamtdatei-Check sichtbar;
ein Exitcode 1 wird nicht als vollständiger Erfolg umgedeutet.

Die Importprobes liefen mit `python -I`, explizit hinzugefügtem Repositorypfad und
einem MetaPathFinder, der `src.core.config`, `src.core.memory`, pydantic-settings,
tiktoken, pandas, Marvin, OpenAI, Torch, Docling und Qdrant ablehnt. Zusätzlich
waren DNS/connect/create_connection gesperrt. Das prüft die tatsächlichen beiden
Module und ihr reales Pydantic-/Tenacityprofil, keine Ersatzmodule für die Ziele.

Die komplette Sammlung wurde mit `--collect-only tests`, deaktiviertem
Pluginautoload und dem Offlineguard ausgeführt. Die sieben wegen fehlendem SDK
nicht sammelbaren Dateien sind `test_cs50_index_cli.py`, `test_cs50_index_contract.py`,
`test_cs50_ingestion.py`, `test_cs50_knowledge_index_checkpoint.py`,
`test_cs50_knowledge_index_mapping.py`, `test_cs50_retrieval.py` und
`test_cs50_retrieval_evaluation.py`.

Der breite Lauf ignoriert genau diese sieben sowie `test_content_http.py`,
`test_content_search_http.py`, `test_deployment_transport.py` und
`test_worker_image_content.py`. Das sind explizite Ausschlüsse, keine Pytest-Skips.
Keine Live-/Socket-/Dockerprüfungen nachträglich als bestanden gezählt.

Inhalt des verwendeten temporären Plugins `/tmp/maint03_offline_guard.py`:

```python
import socket


def forbidden(*args, **kwargs):
    raise AssertionError("MAINT-03: live network/listener forbidden")


socket.socket.connect = forbidden
socket.socket.connect_ex = forbidden
socket.socket.bind = forbidden
socket.socket.listen = forbidden
socket.create_connection = forbidden
socket.getaddrinfo = forbidden
```

Tatsächlicher breiter Testumfang, mit Bash-Array lediglich kompakter notiert:

```bash
MAINT_IGNORED=(
  tests/test_cs50_index_cli.py tests/test_cs50_index_contract.py
  tests/test_cs50_ingestion.py tests/test_cs50_knowledge_index_checkpoint.py
  tests/test_cs50_knowledge_index_mapping.py tests/test_cs50_retrieval.py
  tests/test_cs50_retrieval_evaluation.py tests/test_content_http.py
  tests/test_content_search_http.py tests/test_deployment_transport.py
  tests/test_worker_image_content.py
)
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  "$MAINT_PYTHON" -m pytest -q -o addopts='' -p no:cacheprovider \
  -p maint03_offline_guard --junitxml=/tmp/maint03-offline.xml \
  "${MAINT_IGNORED[@]/#/--ignore=}" tests
```

## Git-/GitHubgrenze und Erhalt

Das gemeinsame Git-Verzeichnis des vorbestehenden Worktrees ist im aktuellen
Sandboxprofil **read-only**. Bereits `git add --dry-run` scheitert mit
`Unable to create .../index.lock: Read-only file system`.
Index, lokaler Branchhead und Commits konnten deshalb nicht aktualisiert werden.
Die Änderungen liegen als Arbeitsbaumänderungen im benannten Branchworktree,
**nicht als lokale Commits auf dessen Head**. Keine Umgehung oder Gitreparatur.

Der vorhandene GitHub-Connector hat Repositoryzugriff und bestätigt `master`
sowie die offenen geschützten Drafts. Der eigene Remote-Branch war nicht vorhanden.
Ein unreferenziertes Treeobjekt mit den drei Code- und zwei Testdateien wurde
erzeugt: `19fb76dea1b7012aa2b2d9cd29d009a8418011c8`.
Der anschließende Create-Commit-Aufruf wurde von der Toolrichtlinie abgelehnt:
**`MCP tool call requires approval, but approval policy is never`**.
Es wurde kein Commit, Remote-Branch oder Draft-PR erzeugt; das Treeobjekt ist
kein veröffentlichter Review-/Integrationsnachweis und enthält nicht die Berichte.
Keine alternative Schreibmethode zur Umgehung dieser Sperre versucht.

Das Mergeverbot des Auftrags bleibt verbindlich. Die von AGENTS.md geforderte
Verfügbarkeit dauerhafter Berichte in `master` ist daher ausstehend. Ein später
autorisierter Lauf muss die Arbeitsbaumänderungen regulär committen, einen eigenen
Draft-PR erstellen, den Reviewprozess respektieren und nach erlaubter Integration
tatsächlich integrierten Code und alle Dokumente prüfen.

Lokale Branch-/Trackingrefs, vollständige Worktreeregistrierungen und Stash-IDs
wurden mit dem Eingangssnapshot verglichen: **unverändert**. Eine erneute
GitHub-Abfrage findet weiterhin keinen eigenen Remote-Branch. Andere lokale
Worktrees wurden nicht verändert oder für Testausführung verwendet; nur der
vorhandene Interpreter und gecachte Hookwerkzeuge wurden daraus gelesen.

Die erneute Liveprüfung bestätigt denselben `master`-SHA und unveränderte Heads
von #161/#162/#163/#158, weiterhin Draft und ungemergt. Der Abschluss ist rein
lokal und ausstehend; die Remoteprüfung ersetzt keine Integration.

Der **vorbestehende** Aufgabenbranch und Worktree bleiben erhalten. Keine weiteren
lokalen Branches oder Worktrees wurden erzeugt; keine alten MAINT-/C26-/C27-/UI-
Artefakte, Stashes, Venvs, Daten, Secrets oder unbekannten Dateien entfernt.
Das unreferenzierte GitHub-Treeobjekt besitzt keinen löschbaren Aufgabenbranch;
keine Repository-GC oder fremde Refbereinigung wurde angefordert.

Temporäre Logs, JUnitdaten, isolierte Quellsnapshots und ausschließlich synthetische
Crashreste unter `/tmp/maint03-*` bleiben als nachprüfbare Arbeitsbelege erhalten.
Sie sind weder produktive Backups noch zusätzliche Gitworktrees. Der abschließende
Patch `/tmp/maint03-review.patch` enthält die elf beabsichtigten Dateien; sein
Reverse-Apply-Check prüft die Übereinstimmung mit dem lokalen Arbeitsbaum ohne
Änderung von Dateien oder Index. Die dauerhaften Ergebnisse stehen in diesen
Berichten und im lokalen Anwendungscode, nicht nur in temporären Logs.

## Offene Prüfungen und nächste Abnahme

Nicht ausgeführt: exakte Worker-/Runtime-Lockinstallation, optionale Qdrant-/DOCX-/
SDKprofile, Modellinferenz, Browser-/UIabnahme, Live-LLM, Online-CVEaudit,
Produktions-/Host-/Backup-/Restoreabnahme und Integration auf C26-/C27-Branches.
Die synthetischen Store-/Crashprüfungen sind keine Produktiv-DBänderung.
Empfehlungen sind in [Plan und MAINT-04-Vorschlag](maint03_modernization_plan.md)
priorisiert; offene Risiken R05–R19 bleiben sichtbar.
