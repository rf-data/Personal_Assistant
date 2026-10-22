# C26-B5-FIX01 – Knowledge-Identitätsargumente und Regression

Beginn 21.10.2026, Fortsetzung 22.10.2026. Basis: aktueller master
`6786b5d67b31125895d94af7b763a1002aeeea7d`, inklusive #141 und #142.
Eigener Branch `fix/c26b5-knowledge-identities`, isolierter Worktree. Der primäre
Checkout und sämtliche früheren Pilot-/DEV-/MAINT-Worktrees bleiben unverändert.
[Historischer B5-Befund](multiformat_validation.md) und
[Multiformatvertrag](multiformat_pilot.md) wurden zuerst gelesen.

## Reproduktion vor jeder Codeänderung

Gemeinsames tatsächlich verwendetes Testpräfix, ohne Installation/Sync:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
 /home/robfra/0_Portfolio_Projekte/gmp_compliance/.venv/bin/python -m pytest \
 -q -p no:cacheprovider
```

Vorhandene Umgebung: Python **3.12.12**, Pydantic **2.13.4**, Pytest **9.1.1**,
SQLite **3.50.4**, Ruff **0.16.0**. Kein Nachinstallieren fehlender Pakete.

Unveränderter Master mit `--tb=long`:

```sh
tests/test_knowledge_transcript_provenance.py \
tests/test_cs50_srt_knowledge_integration.py tests/test_cs50_batch.py \
--basetemp=/dev/shm/c26b5fix01-before
```

**39 passed, 2 failed, 8 setup errors**, 29,19 s, 49 Fälle. Die 46 Fälle der
historischen Knowledge-Baseline ergeben weiterhin 39 pass/2 fail/5 errors; die
zusätzlichen drei Setupfehler stammen aus dem historischen Knowledge-Batch.
Die vollständigen Tracebacks wurden am 21.10.2026 unter
`/tmp/c26b5fix01-before.log` ausgewertet. Nach der Sitzungsunterbrechung ist dieses
temporäre Log nicht mehr vorhanden; die relevanten Test-/Funktionsketten sind
unten erhalten. Die drei Compilerfehler wurden am 22.10.2026 zusätzlich aus exakt
diesem Gitcommit erneut bestätigt (`baseline_compile.log` im unten genannten
privaten Testlogroot). Keine bloße Übernahme der Diagnose aus dem B5-Bericht.

## Fehlerzuordnung und tatsächlich nachgewiesene Ursachen

| Test in `tests/` | Betroffene Funktion / relevante Tracebackkette | Exception vor Fix | Einordnung |
| --- | --- | --- | --- |
| `test_knowledge_transcript_provenance.py::test_real_extraction_and_deterministic_and_semantic_contracts` | `run_extraction` → `functions` → `compile` → `src/run_knowledge_extraction.py:250`, `knowledge_extraction` | `SyntaxError: keyword argument repeated: language` | Produktionscode; außerdem doppelte `transcript_provenance` und `course_id`. |
| `test_knowledge_transcript_provenance.py::test_semantic_no_statements_branch_preserves_explicit_assignment_and_media` | `semantic` → `functions` → `compile` → `src/tools_knowledge/semantic_knowledge.py:624`, `consolidate_semantic_knowledge` | `SyntaxError: keyword argument repeated: media_id` | Produktionscode; beide Ergebniszweige enthalten dieselbe Redundanz. |
| `test_cs50_srt_knowledge_integration.py::test_import_and_chunking` | Fixture `pilot` → `production_functions` → `compile` → `src/tools_knowledge/consolidate_knowledge.py:446`, `consolidate_knowledge` | `SyntaxError: keyword argument repeated: media_id` | Gemeinsamer Produktionsfehler im Fixture-Import, kein defektes SRT. |
| `test_cs50_srt_knowledge_integration.py::test_json_and_deterministic_consolidation` | dieselbe Fixture-/Compilekette | derselbe SyntaxError | Keine unabhängige JSON-/Hashursache. |
| `test_cs50_srt_knowledge_integration.py::test_language_and_official_provenance_do_not_survive_current_contract` | dieselbe Fixture-/Compilekette | derselbe SyntaxError | Test konstruiert absichtlich ein Dokument ohne diese optionalen Metadaten; kein veralteter Vertrag. |
| `test_cs50_srt_knowledge_integration.py::test_legacy_missing_source_identity_is_blocked` | dieselbe Fixture-/Compilekette | derselbe SyntaxError | Bestehende Ablehnung fehlender Sourceidentität bleibt erhalten. |
| `test_cs50_srt_knowledge_integration.py::test_formula_normalization_import_is_corrected` | dieselbe Fixture-/Compilekette | derselbe SyntaxError | LaTeX-Import ist bereits korrekt; keine Parser-/Formeländerung nötig. |
| `test_cs50_batch.py::test_full_six_course_end_to_end_and_resume` | Fixture `context` in `test_cs50_knowledge_input.py:40` → `import_module` → `consolidate_knowledge.py:446` | derselbe SyntaxError | Derselbe Produktionsfehler verhindert den Batchstart. |
| `test_cs50_batch.py::test_explicit_six_ids_and_cli_gate` | dieselbe Fixture-/Importkette | derselbe SyntaxError | Kein CLI-/Freigabefehler. |
| `test_cs50_batch.py::test_isolated_course_cli_v2_resume` | dieselbe Fixture-/Importkette | derselbe SyntaxError | Kein nachgewiesener Resume-/Persistenzfehler. |

Damit sind es mehrere fehlerhafte Konstruktorstellen in drei Produktionsdateien,
aber keine zehn unabhängigen fachlichen Fehler und keine zu korrigierenden Fixtures.
`ast.parse` allein erkennt die mehrfachen Literal-Keywords nicht; `compile` bzw.
ein tatsächlicher Modulimport lehnen sie vor Funktionsausführung ab.

Zusätzlich nachgewiesen: In der deterministischen Konsolidierung sind `language`,
`transcript_provenance`, `course_id` und `lecture_id` sowohl explizit als auch in
`**document.transcript_metadata()` enthalten. Diagnose ausschließlich im Speicher:
Originalfunktion aus `git show 6786b5d:src/tools_knowledge/consolidate_knowledge.py`
geladen, nur doppelte **explizite**
AST-Keywords entfernt, mit leerem synthetischem Dokument aufgerufen. Ergebnis:

```text
TypeError: src.model_knowledge.data_knowledge.ConsolidatedKnowledgeDocument()
got multiple values for keyword argument 'language'
```

Nur den sichtbaren `media_id`-Syntaxfehler zu entfernen genügt daher nicht.
Auch beide semantischen Zweige übergaben den Metadaten-Spread zweimal.
Es wird kein `dict.update` zur stillen Konfliktauflösung eingeführt.

## Minimaler Fix und Identitätsvertrag

Genau **zwölf redundante Argumentzeilen** entfernt:

- `src/run_knowledge_extraction.py`: Sprache, Provenienz und Course nur einmal;
  explizite Lecture-Zuordnung, Sourceableitung und Media-ID-Verfahren unverändert.
- `src/tools_knowledge/consolidate_knowledge.py`: Source-ID und Media-ID weiterhin
  explizit; die vier zusätzlichen Metadaten ausschließlich einmal über die
  vorhandene `transcript_metadata()`-Methode. Transcript-URL bleibt explizit.
- `src/tools_knowledge/semantic_knowledge.py`: dasselbe einmalige Schema sowohl
  im Zweig ohne Statements als auch im regulären Ergebniszweig.

Keine Modell-, Schema-, API- oder Ressourcenänderung, kein Default-Fallback und
keine neue Identität. `source_id`, `lecture_id`, `course_id` und `media_id` bleiben
verschiedene Felder; eine unbekannte Media-ID bleibt null. Die betroffenen Modelle
besitzen kein `document_id`-Feld; es wird keines erfunden oder aus Media/Source
abgeleitet. Bekannte Widersprüche zur Transcriptprovenienz werden weiterhin vom
bestehenden Modell abgewiesen. Keine Datenmigration oder Artefaktumschreibung.

Neu: `tests/test_knowledge_identity_arguments.py`, acht synthetische Fälle.
Drei kompilieren die vollständigen Module ohne deren Imports auszuführen. Vier
prüfen unterschiedliche Source-/Lecture-/Course-/Media-Werte, null Media und
beide semantischen Zweige einschließlich JSON-Roundtrip und unverändertem Input.
Ein Fall prüft die Extraktion mit expliziter Lecture- und separater Source-/Media-ID
sowie echten Segmentbelegen. Agent-/Providergrenzen werden durch vorhandene
Offline-Testhilfen ersetzt; es erfolgen keine Modell- oder Netzaufrufe.

## Validierung

Bereits vollständig abgeschlossene Läufe auf dem unveränderten Fixstand:

- Transcript-/Lecture-/B5-Regression am **21.10.2026**: **159 passed, 1 skipped**,
  196,22 s, 160 Fälle. Enthält sämtliche **32 bestandenen B5-Fälle**; nicht addieren.
- C26-B3/B4-/Batchworker-/Capacity-/Image-Content-Regression am **22.10.2026**:
  **120 passed, 3 skipped**, 215,96 s, 123 Fälle. Die drei historischen
  `test_cs50_batch.py`-Fälle wurden separat ausgeführt, statt den großen
  Sechs-Kurs-Test zweimal zu starten.
- Historischer Knowledge-Batch am **22.10.2026**: **3 passed**, 1022,44 s,
  **keine Setupfehler**. Tatsächlich ausgeführt: vollständige sechs Kurse,
  Wiederanlauf, explizite Kurs-/CLI-Grenzen und portabler isolierter Kurslauf.
- Vollständige betroffene Knowledge-Kernsuite am **22.10.2026**:
  **339 passed, 2 skipped, 0 failed, 0 errors**, 1127,05 s, 341 Fälle.
  Enthält alle **acht neuen bestandenen Regressionstests** sowie die 46 Fälle
  der bisherigen Knowledge-Baseline. Kein neuer Skip oder Xfail eingeführt.

| Testsuite / identische Fallauswahl | Vorher laut B5, auf FIX01-Basis bestätigt | Nachher |
| --- | --- | --- |
| Knowledge-Baseline, 46 Fälle | 39 passed, 2 failed, 5 errors | **46 passed**, enthalten in der 341er-Kernsuite |
| C26-Regression einschließlich drei Legacy-Knowledge-Batchfällen | 120 passed, 3 skipped, 3 errors | **120 passed, 3 skipped** im C26-Lauf; **3 passed** im separaten Legacy-Batchlauf, keine verbleibenden Errors |
| Transcript-/Lecture-Regression einschließlich B5 | 159 passed, 1 skipped | **159 passed, 1 skipped** |
| Neue B5-Tests | 32 passed | **32 passed**, enthalten im Transcriptlauf |
| Neue FIX01-Tests | nicht vorhanden | **8 passed**, enthalten in der Kernsuite |

Die logische C26-Fallauswahl ist damit vollständig geprüft, aber **nicht** als
ein einzelner kombinierter 126er-Nachherlauf ausgegeben. Kernsuite, Baseline-
Teilauswahl und neue Tests überschneiden sich; keine Addition zu einer erfundenen
unabhängigen Gesamtfallzahl. Es wurden keine weiteren Codeänderungen benötigt.

Tatsächlicher Transcript-/Lecturelauf mit obigem Präfix:

```sh
tests/test_cs50_multiformat.py tests/test_official_transcript_import.py \
tests/test_transcript_unknown_time.py tests/test_cs50_lecture_adapter.py \
tests/test_cs50_executor.py --basetemp=/dev/shm/c26b5fix01-transcripts
```

Tatsächlicher C26-Lauf mit obigem Präfix:

```sh
tests/test_cs50_week_pilot.py tests/test_cs50_pilot.py \
tests/test_cs50_batch_worker.py tests/test_cs50_capacity.py \
tests/test_worker_image_content.py --basetemp=/dev/shm/c26b5fix01-c26-final
```

Die am 21.10.2026 unterbrochenen Knowledge-/Batch-/C26-Läufe werden **nicht** als
bestanden gezählt. Die oben ausgewiesenen vollständigen Ergebnisse stammen aus
den erneuten Läufen vom 22.10.2026. Der Legacy-Batch wurde mit
`tests/test_cs50_batch.py --basetemp=/dev/shm/c26b5fix01-batch-final` geprüft.

Die vollständige betroffene Knowledge-Kernsuite umfasst Konstruktor-/Identitäts-
verträge, deterministische und semantische Konsolidierung, Extraktion/Evidence,
Lecture-Runner/-Completion, Checkpoints, Budgets, Schedule/Reports, portable Inputs
und synchrone Offline-Importe. Keine RAG-/Embedding-/Vektordatenbanktests und
keine vollständige Repositorysuite. Tatsächlicher Aufruf mit obigem Präfix:

```sh
tests/test_knowledge_identity_arguments.py tests/test_knowledge_source_id.py \
tests/test_knowledge_transcript_provenance.py \
tests/test_cs50_srt_knowledge_integration.py \
tests/test_consolidation_hardening.py tests/test_consolidation_math_import.py \
tests/test_cs50_knowledge_input.py tests/test_cs50_extraction.py \
tests/test_cs50_precise_evidence.py tests/test_cs50_knowledge_pilot.py \
tests/test_cs50_lecture_runner.py tests/test_cs50_lecture_completion.py \
tests/test_cs50_checkpoint.py tests/test_cs50_budget.py \
tests/test_cs50_schedule.py tests/test_cs50_schedule_report.py \
tests/test_cs50_portable_input.py tests/test_cs50_quality.py \
tests/test_lazy_marvin_import.py --basetemp=/dev/shm/c26b5fix01-knowledge-final
```

Die neuen vollständigen Logs liegen privat unter
`$WORKSPACE/c26b5fix01-testlogs-20261022/`: `knowledge.log`, `batch.log`, `c26.log`,
`baseline_compile.log`, `ruff.log`. Keine Originaltexte oder Secrets. Temporäre
Logs des Vortags sind nach der Sitzungsunterbrechung nicht mehr vorhanden; dessen
hier ausgewiesener Transcript-Abschluss wurde vor der Unterbrechung tatsächlich
beobachtet. Seitdem gab es keine weitere Python-Codeänderung.

Die beiden Kernsuite-Skips betreffen nicht bereitgestellte optionale
Original-Pilotbestände (`test_cs50_knowledge_input`, `test_cs50_knowledge_pilot`).
Der Transcript-Skip betrifft ebenfalls ein fehlendes Original-SRT. Die drei
C26-Skips betreffen den nicht aktivierten privilegierten synthetischen
B3-Handofftest, den nativen Docker-Context-Audit und ein nicht bereitgestelltes
gebautes Workerimage. Keine Image-/Docker-/Hostprüfung als ausgeführt behauptet.

## Grenzen und Lifecycle

Keine B3-/B4-/B5-Ablauf-, HTML-/PDF-Parser-, Speicher-, Limit- oder Konfigurations-
änderung; keine realen Downloads, LLMs, Transkription, Embeddings, SSH oder
Deployments. Nur synthetische temporäre Testroots. Der eigene Branch/Worktree
bleibt für den offenen eigenständigen Review-PR erhalten; keine automatische
Zusammenführung und keine Bereinigung früherer Arbeitsstände. Defaultbranch-
integration und daraus folgende Lifecyclebereinigung bleiben bis zum Merge offen.

## Ruff und unveränderte Altbefunde

Standard-`ruff check --no-cache` auf den vier Pythondateien wurde ausgeführt.
Neue Regressionstests, deterministische und semantische Konsolidierung sind
ohne Befund. `src/run_knowledge_extraction.py` meldet weiterhin drei Befunde
an unveränderten Stellen: **I001** Importreihenfolge, **E402** später `import re`
und **E722** bestehendes nacktes `except`. Die vorliegende Änderung entfernt
dort ausschließlich die drei nachgewiesen redundanten Konstruktorargumente.
Kein neuer Ignore/Noqa und keine Änderung des Exception-Verhaltens, um außerhalb
des Auftrags eine grüne Zahl zu erzeugen. Damit wird **kein vollständig grüner
Ruff-Check für alle vier Dateien behauptet**.

`ruff format --check --no-cache` besteht für alle vier Pythondateien.
Der separate Standardcheck der drei befundfreien Dateien besteht ebenfalls.
`git diff --check` besteht; die öffentlichen Modelle und C26-Entrypoints sind
gegenüber der Basis unverändert. Die drei Lintbefunde bleiben separate Folgearbeit.
