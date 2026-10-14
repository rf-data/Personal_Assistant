# Quality-Testkorrektur für synthetische Pilot-Chunks

Stand: 14. Oktober 2026. Basis: origin/master `13d4357`, frischer separater
Worktree ohne produktive Originalpilot-Artefakte. Keine produktiven Funktionen
oder Fixtures wurden geändert; die Codekorrektur betrifft ausschließlich
`tests/test_cs50_quality.py`.

## Reproduktion und Ursache

Der unveränderte Quality-Modullauf ergab **5 passed, 4 failed in 46,48 s**:

- `[20-1]` und `[20-2]`: Der CLI wählt synthetischen Chunk 20. Sein Start ist
  `700.0`, der Test verlangt weiterhin `792.44` aus dem Originaltranskript.
- `[156-1]`: Der Test erwartet Erfolg innerhalb vermeintlicher 157 Chunks,
  obwohl die synthetische Quelle weniger Chunks enthält. Der CLI lehnt die
  Auswahl korrekt ab.
- Zusätzlich im sauberen Checkout: Der zurückgeänderte Name
  `test_capture_before_overwrite_on_real_concept_fixture` passt nicht zur
  ausdrücklich benannten synthetischen Fixture-Aktivierung in conftest.py.
  Deshalb wird erneut das nicht vorhandene Originalpilot-Manifest geöffnet.

Commit `13d4357` führte diese früheren Erwartungen nach PR #22 wieder ein.
Die lokale Beobachtung mit drei zusätzlichen Fehlern ist dadurch erklärbar;
ohne lokale Originalartefakte wird auch die vierte Abhängigkeit sichtbar.
Es wurde kein Produktionsfehler des CLI-Runners oder Chunkers nachgewiesen.

## Korrektur und stärkere Prüfung

Der Test verwendet wieder explizit portable_cs50_pilot. Letzter gültiger Index
und Index direkt danach kommen aus `len(portable_cs50_pilot.chunks)`, nicht
aus einer festgeschriebenen Originaltranskriptgröße. Geprüft werden Chunk 20
mit ein/zwei Chunks, letzter Chunk mit einem Chunk, Überlauf ab letztem Chunk
mit zwei Chunks und die Auswahl unmittelbar nach dem letzten Chunk.

Bei Erfolg wird die gesamte vom CLI gespeicherte Chunkliste mit der erwarteten
Scheibe der echten Fixture-Chunking-Ergebnisse verglichen. Zusätzlich lädt der
Test das tatsächlich importierte synthetische TranscriptDocument. Start und
Ende jedes ausgewählten Chunks müssen den ersten/letzten referenzierten
Originalsegmenten dieser synthetischen Quelle entsprechen. Die monotonen
Test-Cues haben bekannte Zeitstempel; es werden keine Ersatzzeiten erzeugt.
Bei ungültiger Auswahl bleiben Requestzahl null und chunks.json aus.

Der Sidecar-Test erhält seinen synthetischen Namen zurück; die vorhandene
Fixture greift dadurch wieder ohne Änderung an conftest.py. Die separaten
optionalen Originalpilot-Tests bleiben unverändert und werden hier nicht
durch synthetische Daten ersetzt. Legacy- und segment_v1-Funktionen, Evidence-
Bindung, LLM-Provider und produktives Chunking bleiben unverändert.

## Reproduzierbare Aufrufe

Die bestehende reguläre uv-Worker-Umgebung wurde offline mit --no-sync verwendet
(Python 3.12.12, pytest 9.1.1, Pydantic 2.13.4). Kein Dependency-Upgrade oder
SDK-Installationsversuch. UV_PROJECT_ENVIRONMENT zeigt auf diese bereits
installierte Umgebung; Code und Fixtures stammen aus dem frischen Worktree.

```bash
uv run --offline --no-sync python -m pytest tests/test_cs50_quality.py -q
uv run --offline --no-sync python -m pytest tests/test_cs50_quality.py \
  tests/test_cs50_knowledge_pilot.py tests/test_cs50_precise_evidence.py -q
uv run --offline --no-sync python -m pytest tests -q
```

Keine Original-SRTs, produktiven Execution-Belege, Transkripte oder API-Keys
wurden hinzugefügt. Keine API-/LLM-/Marvin-/Whisper-Aufrufe, echten Downloads
oder Änderungen an produktiven Daten. Der Bericht ergänzt nur die belegte
Testkorrektur; die bekannten TXT-, Provenienz-, Lazy-Import- und SDK-Probleme
werden weiterhin getrennt geführt.

## Prüfergebnisse

- Vor Korrektur: Quality-Modul **5 passed, 4 failed**, 46,48 s.
- Nach Korrektur: Quality-Modul **9 passed** innerhalb des kombinierten
  Pilot-/Präzisionslaufs; insgesamt **46 passed, 1 skipped**, 96,19 s.
  Der Skip betrifft ausschließlich den optionalen Originalpilot.
- Erster Gesamtlauf: **335 passed, 26 failed, 4 skipped**, 402,71 s.
  Neben den 25 bekannten Fällen trat ein unveränderter Smoke-Test zeitabhängig
  auf: `test_timeout_kills_grandchild_even_when_leader_exits` bekam
  FileNotFoundError beim Lesen von `/proc/<pid>/stat` zwischen Existenzprüfung
  und tatsächlichem Lesen. Isolierte unveränderte Wiederholung: **1 passed**,
  1,35 s. Dies ist eine separate Race-Bedingung des bestehenden Tests und wurde
  außerhalb des angeforderten Testbereichs nicht verändert.
- Ruff-Lint, Formatprüfung und git diff --check des betroffenen Tests bestanden.

Abschließende vollständige Wiederholung ohne parallelen Testlauf: **336 passed,
25 failed, 0 errors, 4 skipped**, 365 Fälle in **367,35 Sekunden**.
Alle neun Quality-Fälle bestehen auch innerhalb dieser Gesamtsuite. Die
Legacy-/Präzisionsmodule bestehen ebenfalls (19 passed/1 optionaler Originalpilot-
Skip beziehungsweise 18 passed). Die optionalen Originaltests bleiben unverändert.

Verbleibende Fehler ausschließlich: TXT **6**, Provenienz **14**, Lazy-Imports
**4**, fehlendes optionales OpenAI-SDK **1**. Der zuvor aufgetretene Prozess-
Timeout-Race tritt in dieser vollständigen Wiederholung nicht auf.
