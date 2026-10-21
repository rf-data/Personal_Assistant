# C26-B5 – Implementierung, Abnahme und verbleibende Grenzen

21.10.2026. Ausgangsbasis und vor Veröffentlichung erneut live geprüfter master:
`ac67cd815155d12208cd1b8466842110faff6267`. Branch
`feat/c26b5-multiformat-transcripts`. [Matrix und separates Runbook](multiformat_pilot.md).

## Implementierter Umfang

- Bestehender `scripts.cs50_batch` um `inventory` und
  `transcripts preview|import|report` erweitert. Kein zweiter Einstieg/Worker.
- Dünner `src.tools_materials.transcripts`-Adapter zum bereits integrierten
  offiziellen Importer; keine Parserkopie, Änderung von Transcriptmodellen,
  bestehendem SRT-Executor, B3-Pilot oder C18-Typfreigaben.
- Strikter Receipt für die bisher fehlende lokale Archiv-/Lecture-Verknüpfung:
  Source/Material/Lecture/URL/Sprache/Format, unabhängige Raw-/Payloadhashes,
  unveränderliche Batch-/Freigabe-/Implementierungsbindung. Exklusive Publikation,
  keine automatische Reparatur halbfertiger Artefakte.
- Feste Auswahl höchstens zweier SRT-/TXT-Materialien, offizielle HTTPS-Hosts,
  1 MiB Raw, 20.000 Segmente, 8 MiB JSON, höchstens 64 MiB Archiv und mindestens
  5 GiB freie Reserve. Serialisierung, keine Netzwerkoperation oder C16-Jobanlage.
- Vorhandenes Snapshotinventar wiederverwendet: 16 logische Week-0-Kandidaten,
  acht Varianten, 208 rohe Link-/Bildvorkommen; fünf vorhandene C18-Adapter,
  zwei neue Transcriptanbindungen, neun ausgeschlossene Kandidaten. Einzelne
  Pythonlinks bleiben ungebunden; keine erfundenen Source-IDs oder Wochenabdeckung.

## Tatsächliche Umgebung und Befehle

Python **3.12.12**, Pydantic **2.13.4**, Pytest **9.1.1**, SQLite **3.50.4**,
BeautifulSoup **4.15.0**, PyMuPDF **1.28.2**, vorhandenes Ruff **0.16.0**.
Keine Installation, Dependencyänderung oder Downloads. Gemeinsames Pytestpräfix:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
 /home/robfra/0_Portfolio_Projekte/gmp_compliance/.venv/bin/python -m pytest \
 -q -p no:cacheprovider
```

| Prüfung | Tatsächliches Ergebnis |
| --- | --- |
| Neue Adapter-/CLI-/Inventarfälle, abschließender Stand | **32 passed, 0 failed, 0 skipped**, 15,17 s |
| Gemeinsamer Transcript-/Lecturelauf vor abschließendem HTTPS-Hosttest | **159 passed, 0 failed, 1 skipped**, 64,56 s; enthält die 32 neuen Fälle, nicht addieren |
| C26/B3/B4/Batchworker/Capacity/Image-Content einschließlich historischer Knowledge-Batchdatei | **120 passed, 0 failed, 3 skipped, 3 setup errors**, 152,19 s |
| Knowledge-Baseline aus unverändertem Masterarchiv | **39 passed, 2 failed, 0 skipped, 5 setup errors**, 38,72 s |
| Historischer Knowledge-Batch aus demselben Masterarchiv | **0 passed, 0 failed, 0 skipped, 3 setup errors**, 2,17 s |
| Ruff Check / Format Check / `git diff --check` | erfolgreich für alle drei geänderten/neuen Pythondateien und den gesamten Diff |

Die abschließenden neuen Fälle verwenden obiges Präfix mit:

```sh
tests/test_cs50_multiformat.py --basetemp=/dev/shm/c26b5-final-adapter
```

Gemeinsamer Transcript-/Lecturelauf:

```sh
tests/test_cs50_multiformat.py tests/test_official_transcript_import.py \
tests/test_transcript_unknown_time.py tests/test_cs50_lecture_adapter.py \
tests/test_cs50_executor.py --basetemp=/dev/shm/c26b5-transcript-release
```

C26-Regression:

```sh
tests/test_cs50_week_pilot.py tests/test_cs50_pilot.py tests/test_cs50_batch.py \
tests/test_cs50_batch_worker.py tests/test_cs50_capacity.py \
tests/test_worker_image_content.py --basetemp=/dev/shm/c26b5-c26-regression
```

Die bestehenden Tests führen tatsächliche synthetische C16-/C18-HTMLworkflows
einschließlich Quality/Handoff und Codeerhalt aus; HTTP bleibt isolierter
Testtransport. Die neue Suite verwendet echte Importermodelle, synthetische
Rawbytes, Discovery-/Lecturegraph und private Archive; keine statischen
Erfolgsscreens oder vorgetäuschten Originaldaten.

Geprüft: getrennte Prozess-/Downloadfreigabe, fehlender SHA/Grant/Input,
URL-/Course-/Lecturekonflikt, SRT-Cuezeiten einschließlich
Überlappung und leerer Cues, TXT ohne Zeiten, BOM/CRLF/Unicode/Einrückung,
Pfadtraversal/Symlinks/FIFO, unbekanntes Format, HTTPS-/Hostgrenzen,
Größen-/Kapazitätsgrenzen, tatsächliche flock-Konkurrenz, private Rechte,
Importerrevision und Widerruf, Hashmanipulation, fehlende Receipts,
byteidentische Wiederholung, expliziter Retry nach fehlendem Input,
CLI-Bestätigung/Reporthash/No-Overwrite und Inventarklassifikation.

Die vier Skips über beide Läufe sind konkret: nicht bereitgestelltes originales
CS50-SRT; nicht aktivierter privilegierter synthetischer B3-Root-Handofftest;
nicht aktivierter nativer Docker-Context-Audit und kein bereitgestelltes gebautes
Workerimage. Kein Docker-Build oder Image-/Containerzugriff als neuer Erfolg
behauptet. Dockerfiles, COPY-Closure, Mounts, CMD und Restart bleiben unverändert.

## Reproduzierte Altfehler und Entwicklungsläufe

Die vorhandenen Knowledgefunktionen enthalten bereits auf dieser Masterbasis
doppelte Keywordargumente: `language` in `src/run_knowledge_extraction.py:250`,
`media_id` in `src/tools_knowledge/semantic_knowledge.py:624` und
`src/tools_knowledge/consolidate_knowledge.py:446`. Das blockiert zwei bestehende
Provenienzfälle, alle fünf SRT-Knowledge-Setups und drei historische
`test_cs50_batch.py`-Setups. Diese Dateien und Tests bleiben unverändert;
kein Absenken von Assertions und keine Knowledgefreigabe durch B5.

Nachweis auf unabhängigem unverändertem Archiv: `git archive HEAD src tests
scripts docs/course_sources pyproject.toml` auf der genannten Basis in einem
neuen privaten `/tmp/c26b5-baseline-*`-Root ausgepackt. Dort mit obigem Präfix
`tests/test_knowledge_transcript_provenance.py
 tests/test_cs50_srt_knowledge_integration.py
 --basetemp=/tmp/c26b5-baseline-tests` und separat
`tests/test_cs50_batch.py --basetemp=/tmp/c26b5-baseline-batch-tests` ausgeführt.
Genau dieselben Fehler; keine vollständige grüne Repositoryregression behauptet.

Ein vorangegangener Transcriptlauf unter `/tmp/c26b5-release` hatte **142 passed,
16 failed, 1 skipped**, 123,11 s: Receipt-Renames des unveränderten Executors
meldeten `ENOSPC`. Die vollständige betroffene Suite wurde anschließend in
`/dev/shm` erfolgreich wiederholt; Produktionslimits wurden nicht geändert.
Die zusätzliche Preview-Missing-Prüfung erklärt den Anstieg von 159 auf 160 Fälle.

Frühe Entwicklungsläufe: zunächst 21 pass/1 fail (Receipt-Leerzeichen wurden
akzeptiert), danach im erweiterten Lauf 196 pass/3 fail/1 skip/5 Setupfehler.
Der eine neue Fehler dort war eine zu enge Erwartung der Fehlermeldung
`hash mismatch` statt tatsächlichem `SHA-256 mismatch`; die übrigen waren die oben
reproduzierten Knowledgefehler. Receipt-Bytes werden jetzt exakt verglichen,
die neue Assertion entspricht dem bestehenden Fehlervertrag. Die abschließenden
gezielten Läufe prüfen beides. Keine Entwicklungslaufzahlen als Zusatzabnahme addieren.

## Ausstehend und Lifecycle

Keine Realdatei für diesen Auftrag geöffnet, kein Download, SSH, Deployment,
neuer Content-/EvaluationStore oder externer LLM-/Embeddingaufruf. Fachliche
Qualität und echte Wochenvollständigkeit bleiben ungeprüft. Noch nötig: individuelle
Rechte-/Nutzungs-/Verarbeitungsbelege, konkrete Rawdateien mit bestätigten Hashes,
neuer privater Ausgaberoot und bei Hostnutzung gesondertes Update/Mountfreigabe.
Für Hetzner bleibt die Processingidentität UID/GID 1000:1000 maßgeblich.

PR #9 bleibt unverändert offen; vorhandener Importercode wird verwendet.
ZIP/Python-Einzelbindung/weitere Aufgaben/Shorts-/Medienintegration und die
Knowledge-Syntaxfehler sind konkret im Runbook abgegrenzt. Keine automatische
fachliche Freigabe, kein realer Qualitätswert aus synthetischen Testresultaten.

Die fünf auftragseigenen Dateien gehen über einen regulären PR nach master.
Bis zu dessen ausdrücklich bestätigtem Merge bleiben Branch und Worktree erhalten;
damit ist die Defaultbranchintegration noch offen. Kein automatischer Merge oder
Cleanup alter DEV-/MAINT-/Pilotbranches, keine Änderung geschützter Originale.
Nur eigene synthetische Testroots/temporäres Masterarchiv und erzeugte `.pyc`-Caches
werden nach abgeschlossenen Prüfungen entfernt; keine unbekannten/privaten Daten.
