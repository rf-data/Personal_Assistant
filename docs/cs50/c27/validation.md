# C27 Validierungsbericht

Datum: 2026-10-29. Basiscommit `a8af1d9`, vorhandener Branch
`feat/c27-cs50-learning-pipeline`. Validierung lokal auf Penguin,
Python 3.12.12, Pydantic 2.13.4, pytest 9.1.1. Paketversionen und Prüfsummen:
[maschinenlesbares Ergebnis](validation.v1.json).

## Abschließende Ergebnisse

| Prüfung | Ergebnis | Protokoll |
|---|---|---|
| Ursprüngliche Patch-Integrationsregression | 280 passed, 1 skipped; vor dem abgegrenzten Fake-Label-Fix | [Ausgabe](test-results/initial-integration.txt) |
| Summarizer und UI nach Fix | 61 passed | [Ausgabe](test-results/summarizer-final.txt) |
| Neue Reviewbrücke, Week-0-/Week-1-Fixtures, echte Penguin-Daten | 36 passed, davon 1 echter lokaler Test und 35 Fixture-/Unitfälle | [Ausgabe](test-results/review-final.txt) |
| ZIP/Materialverträge/Verarbeitung/Downloaddoppel/Code/HTML/Multiformat | 159 passed, 1 skipped | [Ausgabe](test-results/pipeline-regression.txt) |
| Ruff für neue Brücke, CLI, Tests, selektierte Komponenten und Summarymodule | bestanden | maschineller Bericht |
| `git diff --check` | bestanden | maschineller Bericht |
| Zentraler Content-/Material-/Transcriptcode gegenüber HEAD | unverändert | maschineller Bericht |

Keine Addition überlappender Testgruppen. Der Skip im ursprünglichen Lauf ist
der vorhandene `test_real_operator_exports_read_only`; im weiteren Pipeline-
Lauf ein vorhandener externer Original-HTML-Test. Beide sind zusätzliche andere
Bestände und wurden nicht durch Fixtures als bestanden erklärt. Der neue echte
Penguin-Test wurde explizit mit `--run-external` und Pfad gesetzt ausgeführt.
Eine vorhandene ZIP-Duplikat-Warnung im Negativtest ist erwartet.

## Befehle

Alle pytest-Läufe verwenden `PYTHONDONTWRITEBYTECODE=1`,
`/tmp/c27-test-env/bin/python -m pytest -p tests.offline_guard`.
Der Guard verbietet Netz-/Listenerzugriffe und Infrastrukturkommandos; er ist
eine Testassertion, kein eigenständiger OS-Isolierungsnachweis.

```text
Ursprüngliche Integration:
 tests/test_lecture_summary.py tests/test_lecture_summary_ui.py
 tests/test_content_store_adapters.py tests/test_cs50_material_quality.py
 tests/test_transcript_unknown_time.py tests/test_cs50_week_materials.py -q

Nach Fake-Label-Fix:
 tests/test_lecture_summary.py tests/test_lecture_summary_ui.py -q

Neue Brücke und explizite echte Daten:
 C27_WEEK0_REVIEW_ROOT=/home/OPERATOR/cs50p-week0-review-RbZ8OQqe
 tests/test_c27_reviewed_week.py --run-external -q

Weitere Pipeline-Regression:
 tests/test_cs50_code_zip.py tests/test_cs50_zip_inventory.py
 tests/test_cs50_material_contracts.py tests/test_cs50_material_processing.py
 tests/test_cs50_material_download.py tests/test_cs50_material_code.py
 tests/test_cs50_material_html_semantics.py tests/test_cs50_multiformat.py -q
```

Der isolierte Originalpatch-Smoke lief im C27-Dateiexport über
`python -m scripts.lecture_summary_offline --output /tmp/c27-isolated-smoke`.
Sieben Abschnitte, sechs Claims und Cache ohne erneuten Fake-Aufruf bestanden.
Die volle `.gitignore`-Patchprüfung scheiterte erwartungsgemäß am Kontext;
alle übrigen Dateien ließen sich isoliert und im C27-Stand anwenden.

## Echtdaten und behobene Befunde

Der echte Read-only-Test vergleicht **alle Dateihashes des Reviewverzeichnisses
vorher/nachher**. Die sechs eindeutigen Snapshotseiten sind im Inventar siebenmal
aufgeführt, weil die Week-Seite doppelt beobachtet wurde; sämtliche eindeutigen
URL-/Hashpaare sind abgedeckt. Beide Inventare sowie beide Pläne sind jeweils
bytegleich. Der Plan-Inventarhash ist der kanonische Modellhash und stimmt;
er unterscheidet sich absichtlich vom formatierten Dateihash.

Details, Dateigrößen, Originalhashes und Scope: [Echtdatenbericht](real_data_acceptance.v1.json).
Reale HTMLs bestehen das vorhandene technische Qualitätsgate. Vollständige
HTML-Unit-Auswahlen überschreiten die unveränderten Summary-Bounds. Der echte
TXT-Smoke wählt ausdrücklich nur das Functions-Transkript und lässt andere
Materialien im Verarbeitungsbericht sichtbar. Keine stillen Kürzungen.

Während der Implementierung fanden die Tests zwei echte Fehler:

- Transcript-Importzeit war bei unterbrochener Veröffentlichung nicht stabil.
  Wiederaufnahme erhält jetzt die erste Importzeit und vergleicht alle anderen
  serialisierten Felder, bevor vorhandene Bytes wiederverwendet werden.
- Der Fake-Adapter konnte ein Themenlabel über 200 Zeichen erzeugen. Begrenzung
  nur des Labels; lange Belegtexte bleiben vollständig. Der echte TXT-Smoke und
  ein gezielter Regressionstest bestehen anschließend.

Vorherige fehlgeschlagene Testläufe sind keine Erfolge; obige Protokolle zeigen
die finalen Durchläufe. Isolierter Smoke, Fixtures und echtes lokales Material
werden ausdrücklich getrennt ausgewiesen. Keine Aussagen über reale Provider,
Fachreview, komplette Week 0 oder neue Kurse.

## Integration und Retention

Push-/Mergeverbot eingehalten. Kein Git-Metadaten-Schreibversuch; kein Commit,
kein neuer Branch/Worktree, keine Änderung an fremden Worktrees. Lokaler und
Live-Default-Branch-/PR-Integrationsnachweis ist ausstehend. Alle dauerhaften
Berichte wurden zur späteren regulären Reviewintegration im C27-Worktree
vorbereitet. Vorhandener Branch/Worktree bleiben notwendig erhalten.

Die ursprüngliche `example-summary.md` enthält sechs Zeilen mit abschließenden
Leerzeichen; sie bleibt für den bytegenauen historischen Manifestnachweis erhalten.
Das sind bekannte Whitespace-Hinweise der Originalpatch-Anwendung. Die aktuellen
Codeprüfungen sind erfolgreich; der `git diff --check`-Befund betrifft den
vorhandenen Git-Diff der bereits versionierten Dateien.
