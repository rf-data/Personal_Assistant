# C23-05: Offline-Abnahme des TXT-/Nullzeitvertrags

Stand 18.10.2026, Basis Master
`b2b994a3bc09b061992ba5f4ba7c6b6a36fd9aa0`.
[Root Cause, Vertrag, PR-#9-Vergleich und Verbrauchermatrix](../contracts/official_transcript_unknown_time.md).
Keine Migration, Downloads, Installationen, LLM-, Whisper-, Embedding- oder
Qdrantaufrufe. Ausschließlich synthetische lokale Fixtures; keine realen
Transkriptdateien/Receipts verändert. C23-04 wird nicht vorausgesetzt.

## Umgebung

Python 3.12.12, Pydantic 2.13.5, SQLite 3.50.4, System-Pytest 7.2.1,
Pluggy 1.0.0+repack, BeautifulSoup **4.11.2** im tatsächlich verwendeten
`PYTHONPATH`, Ruff 0.16.0. Das verfügbare Projektumfeld enthält kein nutzbares
Pytest 9/PyMuPDF; vorhandener Interpreter aus `ai-job-search/.venv` mit
System-Pytest verwendet, nichts installiert. `tiktoken`, `qdrant_client`,
`pymupdf`, `faster_whisper` und `marvin` fehlen. Pytest-7-AST-Warnungen unter
Python 3.12 sind keine Skips oder Erfolge nicht ausgeführter Prüfungen.

Alle nachfolgenden Pytest-Aufrufe verwenden dieses tatsächliche Präfix:

```sh
PYTHONPATH=/usr/lib/python3/dist-packages PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /home/robfra/0_Portfolio_Projekte/ai-job-search/.venv/bin/python -m pytest
```

## Vertragstests

Abschließender gemeinsamer Lauf: **111 passed, 0 failed, 0 skipped**, 46,31 s.

```sh
-q --disable-warnings \
 tests/test_official_transcript_import.py tests/test_transcript_unknown_time.py \
 tests/test_knowledge_transcript_provenance.py \
 tests/test_cs50_srt_knowledge_integration.py \
 --basetemp=/tmp/c2305-contracts-final
```

| Bereich | Pass / Fail / Skip | Nachweis |
| --- | --- | --- |
| Vollständiger offizieller Importer | **39 / 0 / 0** | TXT/SRT/VTT, Encodings, korrupte Cues, exklusive Speicherung, leichte Imports |
| Neue Unknown-Time-Fälle | **26 / 0 / 0** | Reale Pydantic-Konstruktion/JSON/Schema, ungültige Intervalle, bekannte Alt-JSONs, gemischte Dokumente, Source-/Provenienz-Roundtrip, Timed-Evidence/Retrievalfenster und SRT-Bundlegrenze |
| Knowledge-Provenienz | **41 / 0 / 0** | Bestehende tatsächliche Funktionskörper isoliert von LLM-/Settingsimports |
| SRT-Knowledge-Vertragsintegration | **5 / 0 / 0** | Synthetische Original-SRTs, echte Modelle/Serialisierung, bestehende isolierte Funktionskörper; keine Extraktion durch ein Modell |

Die sechs bisher fehlschlagenden Importtests sind unverändert enthalten und
bestanden: `test_txt_unknown_timestamps_paragraphs_and_unicode`,
`test_explicit_encoding[cp1252]`, `test_explicit_encoding[utf-16]`,
`test_exclusive_save_and_no_overwrite`,
`test_knowledge_chunking_contract_without_llm_imports` und
`test_import_does_not_load_whisper_or_application_settings`.

`test_txt_preserves_text_provenance_raw_hash_and_repeats` weist den Roundtrip
mit BOM/CRLF, Randspaces, Mehrfachleerzeilen, Café, getrenntem kombinierendem Akzent,
∑ und x² nach. Vollständiger LF-Text und Provenienz einschließlich Importzeitpunkt
bleiben bei JSONspeicherung/-laden identisch, der SHA256 der Rawdatei unverändert.
Wiederholte Importe vergleichen alle Werte außer dem jeweiligen `acquired_at`.
Der zusätzliche frische Pythonprozess bestätigt fehlende Settings-/Whisper-/LLM-
Initialisierung bei Netzwerkverbot.

Die neuen Tests verwenden reale Modelle, Rawbytes und die bestehende synthetische
SRT-Bundlefabrik. Ein absichtlich manipuliertes Testbundle wird auch mit erneut
berechneten Receipt-/Implementierungshashes an der Nullzeitgrenze abgewiesen;
das ist keine Änderung realer Receipts. `source_time_window` ist die tatsächlich
in Mapping/Revalidierung/Retrievalvorlagen verwendete Funktion. Deren isolierter
Test ersetzt keine vollständige Qdrant-/Knowledge-Runtimeabnahme.

## Weitere ausgeführte Regressionen

| Lauf auf Ausgangsmaster `b2b994a` plus C23-05 | Pass / Fail / Skip / Error | Dauer |
| --- | --- | --- |
| Vollständige A/B/C-/C23-03-ContentStore-Suite | **225 / 1 / 0 / 0** | 513,45 s |
| Material/Discovery/Lecture/Executor/C16/C18 | **188 / 2 / 2 / 0** | 351,00 s |

ContentStore: alle elf bestehenden Module (226 Fälle):

```sh
-q --disable-warnings \
 tests/test_content_store_models.py tests/test_content_store_artifacts.py \
 tests/test_content_store_store.py tests/test_content_store_adapters.py \
 tests/test_content_store_recovery.py tests/test_content_store_concurrency.py \
 tests/test_content_store_integrity.py tests/test_content_store_backup.py \
 tests/test_content_store_limits.py tests/test_content_store_reimport.py \
 tests/test_content_store_inventory.py --basetemp=/tmp/c2305-content
```

Der Fehler `test_retry_is_recoverable_after_second_interruption[binding]` ist
eine vorhandene Reihenfolgeannahme: `inspect_recovery` enthält auch abgelehnte
Runs und sortiert nach UUID, der Test wählt aber `[0]` als vermeintlichen Retry.
Keine Änderung an dieser Semantik oder dem Test im TXTpaket.
Gezielte Überprüfung beider Parameter, mit identischem Pytestpräfix:

```sh
-q --disable-warnings \
 tests/test_content_store_reimport.py::test_retry_is_recoverable_after_second_interruption \
 --basetemp=/tmp/c2305-retry-recheck
```

**2 passed**, 13,89 s auf C23-05. Derselbe Befehl im unveränderten Baselinearchiv
(Basetemp `/tmp/c2305-retry-baseline-tests`) ergibt **1 passed / 1 failed**, 12,12 s,
mit demselben Binding-Node und derselben Assertion `retry_of=None` am alten Run.
Das macht den 226er-Lauf nicht nachträglich grün und ist keine neue Runtimefreigabe.

Pipelinebefehl (192 Fälle):

```sh
-q --disable-warnings \
 tests/test_cs50_material_contracts.py tests/test_cs50_material_html.py \
 tests/test_cs50_material_html_semantics.py tests/test_cs50_material_code.py \
 tests/test_cs50_material_mapping.py tests/test_cs50_discovery.py \
 tests/test_cs50_lecture_adapter.py tests/test_cs50_executor.py \
 tests/test_job_control.py tests/test_cs50_workflows.py \
 --basetemp=/tmp/c2305-pipeline
```

Darin **36 C16- und 24 C18-Tests bestanden**. Beide Fehler sind die unveränderten
Wrapperfälle `test_code_preserves_exact_whitespace_quotes_entities_and_unicode`
(`héllo` → `h√©llo`); siehe unveränderte Baseline unten. Beide Skips betreffen
nicht vorhandene echte HTML-/SRT-Bestände. Kein HTML-/PDFparserfix.

## Abgleich mit dem inzwischen aktualisierten Master

Während der Tests wurde #80 gemergt. Der eigene Branch wurde vor PR-Erstellung
auf `1254c2c79d99525f150cf3d84050d0e5d504d6ce` aktualisiert. Alle C23-05-
Pythonänderungen bleiben identisch; die beiden überlappenden Plan-/Architekturdocs
erhalten sämtliche C23-03-/C23-04-Nachträge. Keine Übernahme alter offenen Branches.
Die vorherigen Regressionen behalten ihren oben genannten Basisbezug.

Abschließend auf dem aktuellen Master plus C23-05:

```sh
-q --disable-warnings \
 tests/test_official_transcript_import.py tests/test_transcript_unknown_time.py \
 tests/test_knowledge_transcript_provenance.py \
 tests/test_cs50_srt_knowledge_integration.py tests/test_content_read_contracts.py \
 --basetemp=/tmp/c2305-current-master
```

**125 passed / 0 failed / 0 skipped**, 19,29 s: dieselben 111 Transcriptfälle
und alle 14 Content-Read-Vertragsfälle. Ergebnisse überlappen, nicht addieren.

Zusätzlich nach dem Masterabgleich:

```sh
-q --disable-warnings tests/test_job_control.py --basetemp=/tmp/c2305-current-c16
```

**36 passed / 0 failed / 0 skipped**, 11,52 s. C18-Code und seine Verträge wurden
durch #80 nicht verändert; der oben dokumentierte 24er-Nachweis bleibt gültig.

## Bekannte Umgebungsgrenzen und Baseline

Ein zusätzlicher Entwicklungslauf ausführte:

```sh
-q --disable-warnings tests/test_official_transcript_import.py \
 tests/test_cs50_knowledge_input.py tests/test_cs50_precise_evidence.py \
 --basetemp=/tmp/c2305-initial
```

Ergebnis: **54 passed, 1 failed, 0 skipped, 30 setup errors**, 3,11 s.
Alle 39 Importtests bestanden. 28 Knowledge-Setupfälle und zwei Precise-Pilot-
Setups sowie `test_whisper_and_legacy_binding_unchanged` scheitern an fehlendem
`tiktoken`; diese Runtimepfade sind nicht abgenommen.

Unveränderte Baseline als `git archive b2b994a3bc09b061992ba5f4ba7c6b6a36fd9aa0`
in `/tmp/c2305-baseline` entpackt, dort mit demselben Präfix:

```sh
-q --disable-warnings tests/test_official_transcript_import.py \
 tests/test_cs50_material_html_semantics.py tests/test_cs50_knowledge_input.py \
 tests/test_cs50_precise_evidence.py --basetemp=/tmp/c2305-baseline-tests
```

Ergebnis: **63 passed, 9 failed, 1 skipped, 30 setup errors**, 12,02 s.
Genau die sechs TXTfehler, zwei HTML-Unicode-Fehler und derselbe fehlende
`tiktoken`-Importfehler; die 30 Setupfehler haben dieselbe Dependencyursache.
Der Skip benötigt einen nicht vorhandenen echten HTMLbestand.

Weitere ausgeführte Befehle:

```sh
-q --disable-warnings tests/test_cs50_embeddings.py tests/test_cs50_retrieval.py \
 tests/test_cs50_retrieval_evaluation.py tests/test_cs50_knowledge_index_mapping.py \
 --basetemp=/tmp/c2305-rag
```

Dieser Lauf brach bei **drei Collectionfehlern** wegen `qdrant_client` ab;
**keine Tests ausgeführt**. Gesondert:

```sh
-q --disable-warnings tests/test_cs50_embeddings.py --basetemp=/tmp/c2305-embeddings
```

**4 passed, 0 failed, 0 skipped, 4 setup errors**, 5,22 s: reine Offset-/Vektor-
Verträge bestanden, vier SRT-Mapping-Setups benötigen fehlendes `tiktoken`.
Keine Installation, keine lokale oder externe Qdrantinstanz, kein Modellaufruf.
PDFparser-/PDFworkflowtests wurden wegen fehlendem PyMuPDF nicht ausgeführt;
sie werden nicht als zusätzliche Skips gezählt.

Frühere Entwicklungsläufe: Importer plus damals 22 neue Fälle **60 passed /
1 failed** (5,14 s): falsche Testerwartung des redigierten Bundlefehlers korrigiert.
Danach dieselben vier Vertragsmodule **107 passed** (48,26 s), vor vier weiteren
Schema-/Copy-Guardfällen. Maßgeblich ist der abschließende 111er-Lauf; Ergebnisse
überlappen und werden nicht addiert. Keine vollständige grüne Repositorysuite
oder reale TXT-/RAG-/CS50-End-to-End-Freigabe wird behauptet.

## Verbleibende Integrationsarbeit

TXTimport und Speicherung mit Nullzeiten sind unterstützt. Zeitbasierte Chunks,
Zeitevidenz, Visual-Enrichment und SRT-/Transcript-Retrieval verlangen bekannte
Originalzeiten. Für zeitlose Verarbeitung fehlen ein expliziter Textanker-/Chunk-
und Evidencevertrag sowie das vollständige TXT-Source-/Receipt-/ContentStore-
Binding. Danach gezielte Runtimeabnahme mit vorhandenen freigegebenen Dependencies
und unabhängigem realem Korpus; keine erfundenen Zeiten oder automatische
TXT-zu-SRT-Konvertierung als Übergang.

## Statische Prüfung und Arbeitsartefakte

Ruff Check und Format Check erfolgreich für alle elf geänderten Pythondateien:

```sh
RUFF=/home/robfra/.cache/pre-commit/repokzno83cn/py_env-python3.12/bin/ruff
"$RUFF" check \
 src/model_transcribe/data_transcribe.py src/tools_transcribe/import_transcript.py \
 src/tools_knowledge/find_knowledge.py src/tools_knowledge/cs50_precise_evidence.py \
 src/tools_lecture/execute_cs50.py src/content_store/operations.py \
 src/tools_rag/cs50_embeddings.py src/tools_rag/cs50_ingestion.py \
 src/tools_rag/cs50_knowledge_index.py src/tools_rag/cs50_retrieval_evaluation.py \
 tests/test_transcript_unknown_time.py
```

`format --check` mit derselben Dateiliste: elf Dateien bereits formatiert.
`git diff --check` erfolgreich. Die bestehenden `str, Enum`-Klassen behalten
aus Kompatibilitätsgründen ihre bisherige Stringsemantik; zwei gezielte UP042-
Ausnahmen vermeiden einen fachfremden Wechsel auf StrEnum. Alte ungenutzte
Imports/Importreihenfolge in den berührten Dateien wurden für Ruff bereinigt.

Vollständige lokale Testlogs bleiben außerhalb des Repositories unter
`/tmp/c2305-*.log`. Eigene synthetische Testroots, Gitarchiv, Abgleichskopien und
erzeugte Caches werden nach Abschluss entfernt. Der eigene Worktree bleibt
solange der PR offen ist bestehen; keine anderen Worktrees, Nutzdaten, Envs
oder Originalartefakte werden bereinigt.
