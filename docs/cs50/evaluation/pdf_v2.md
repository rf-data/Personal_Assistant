# PDF-v2: Code-, Mathe- und Zeilennummernklassifizierung

Ergänzung C19: Die Klassifikation bleibt unverändert. Der Worker übernimmt bei
C16-Ausführung die kontrollierte Jobgruppe und strengere geerbte Ressourcenlimits.
[Lifecycle-Vertrag](../../job_control/pdf_lifecycle.md),
[Offline-Nachweis](../../job_control/pdf_validation.md).

Stand: 15.10.2026. Basis: `master`, `87fac39`. Keine neuen Downloads, APIs, LLMs oder Codeausführung.

## Ursache und Änderung

PDF-v1 erkannte Monospace zunächst als Code. Ein nachfolgendes einzelnes `=` überschritt diese Entscheidung jedoch bedingungslos mit `math`. Im Source-PDF wurden dadurch 23 nummerierte Python-Beispiele falsch eingeordnet. Umgekehrt wurden 24 reine Dateinamensblöcke allein wegen ihrer Schrift als Code eingestuft.

`pdf_worker.classify_text()` verwendet nun mehrere dokumentierte Quellsignale:

- Zeichenanteil monospaced Spans (mindestens 60 %), anhand Fontnamen wie Consolas/Mono/Courier oder PDF-Monospace-Flag. Schrift allein genügt nicht.
- Python-Definitionen, charakteristische Builtin-Aufrufe, String-Zuweisungen, Kommentare, mehrzeilige Blöcke, Methoden, Kontrollanweisungen und Python-CLI-Fragmente. `ast.parse()` liefert zusätzliche Strukturhinweise; AST-Parsebarkeit allein genügt ebenfalls nicht.
- Starke Python-Merkmale haben Vorrang vor einzelnen Operatoren, auch bei Keywordargumenten oder mathematischen Zeichen innerhalb von Python-Strings. Unsicherheit bleibt ausdrücklich gespeichert.
- Mathematik benötigt stärkere Notation, etwa Summen-/Integralzeichen, Wurzeln, Potenzen, LaTeX-Kommandos oder eine Gleichung ohne einfache Python-Zuweisungsstruktur. Auch monospaced Formeln können `math` bleiben.
- Eine bloße Zuweisung wie `x = y + 1` bleibt `paragraph` mit konkreter Ambiguitätswarnung. Generisches `f(x)` und ein monospaced Dateiname werden nicht automatisch Code.

Die Gründe stehen pro Block in `data.classification`: Strategie `python_math_v2`, Signalliste, `monospace_ratio` und `python_syntax_valid`. Letzteres bedeutet ausschließlich, dass **`ast.parse` einen AST bilden konnte**; keine Kompilierung, semantische Gültigkeit oder Ausführbarkeit wird behauptet. Beispielsweise ist ein isoliertes `return` kein vollständiges ausführbares Programm.

`Block`, `NormalizedDocument`, Provenienz-, Storage- und Downloadverträge bleiben bestehen. Das freie bestehende `data`-Feld genügt; keine neuen fachlichen Modelle. HTML-v2, Code- und Bildparser werden funktional nicht geändert.

## Text, Geometrie und Zeilennummern

Der Text entsteht weiterhin aus den originalen PyMuPDF-Spanstrings, mit genau einem Zeilenumbruch zwischen den extrahierten Zeilen. PDF-v2 entfernt das bisherige äußere `.strip()`; Quellleerzeichen bleiben nun vollständig erhalten. Keine Dedent-, Ersetzungs- oder Operatorreparatur. Seitenzahlen und Block-Bounding-Boxes bleiben unverändert, `data.line_bboxes` erhält zusätzlich die originale Zeilengeometrie.

Eine separate Codeansicht ist ausschließlich zulässig, wenn mindestens drei Zeilen durchgehend aufeinanderfolgende Nummern mit gleich breitem Präfix und genau zwei Trennleerzeichen enthalten, die Schrift überwiegend monospaced ist und zusätzliche Python-Merkmale Code stützen. Führende Ziffernausrichtung gehört zum Nummernpräfix; weitere Leerzeichen nach den zwei Separatoren gehören zur Codeeinrückung.

- `Block.text` bleibt unverändert einschließlich aller Nummern und Leerzeichen.
- `data.line_numbers` enthält nullbasierte Zeilenindizes, Originalnummern und das genaue Originalpräfix.
- `data.code_view` ist eine **zusätzliche**, abgeleitete Ansicht; `line_number_strategy=sequential_aligned_two_space_gutter_v1` und eine Unsicherheitsmeldung machen die Herkunft sichtbar.
- Präfix plus jeweilige Codeansichtszeile muss exakt zur Originalzeile zurückführen. Unregelmäßige Nummern, einzelne nummerierte Zeilen, unbekannte Separatoren, gewöhnliche nummerierte Prosa und reine mehrdeutige Gleichungen erzeugen keine Codeansicht.

Beispiel der tatsächlichen Source-Struktur:

```text
 8  # Comment
 9  def hello():
10      print('hi')
11      return 'ok'
```

Die zusätzliche Ansicht beginnt bei `# Comment`, dann `def hello():` und behält vier Leerzeichen vor `print` und `return`. Der Rohtext mit Nummern bleibt maßgeblich. Das Beispiel selbst ist eine kleine eigene Testfixture; die gleichen invarianten Prüfungen wurden auf alle 24 echten Codeblöcke angewendet.

## Evaluation der bereits bereitgestellten Originale

| Quelle | Seiten | Raw-SHA-256 |
|---|---:|---|
| [lecture0.pdf](https://cdn.cs50.net/python/2022/x/lectures/0/lecture0.pdf) | 32 | `a14304ba0354ff5e48061b0bf335304e6ff4e2cc1039b4c9ff5677571b8e2edc` |
| [src0.pdf](https://cdn.cs50.net/python/2022/x/lectures/0/src0.pdf) | 24 | `9f869c2727f268309a93a34cd4064cae1bde24edc08e02e6e159e8f0d600683d` |

| Quelle / Typ | v1 | v2 |
|---|---:|---:|
| Lecture: paragraph | 33 | 31 |
| Lecture: code | 0 | 3 |
| Lecture: math | 1 | 0 |
| Source: paragraph | 0 | 24 |
| Source: code | 25 | 24 |
| Source: math | 23 | 0 |
| Source: separat erkannte nummerierte Codeansichten | 0 | 24 |

**Alle 82 Textblöcke** stimmen in Quellreihenfolge, Seitenzuordnung, Bounding Boxes und jedem Zeichen mit einer unabhängigen PyMuPDF-Dictionary-Extraktion überein. Alle bisherigen Blöcke behalten dieselbe Position und erfüllen `v2.text.strip() == v1.text`. Drei Lecture- und vier Source-Blöcke erhalten lediglich die früher entfernten äußeren Originalleerzeichen zurück. Es wird keine synthetische Einrückung aus Koordinaten erfunden.

Die 23 fehlerhaften Source-Blöcke auf Seiten 2–24 wurden einzeln mit ihren vollständigen Inhalten überprüft: Kommentare, reale Python-Aufrufe/Zuweisungen und zuletzt Funktionsdefinitionen; alle 23 ergeben nach der separat geprüften Nummernprojektion einen Python-AST. Die bereits richtig erkannte Codeprobe auf Seite 1 bleibt Code. Alle 24 Dateinamensblöcke werden als monospaced Text mit Unsicherheit gespeichert.

| Source-Seite | v1 → v2 | Geprüfte zusätzliche Merkmale |
|---:|---|---|
| 2 | math → code | assignment, python_builtin_call, python_comment |
| 3 | math → code | assignment, python_builtin_call, python_comment |
| 4 | math → code | assignment, python_builtin_call, python_comment |
| 5 | math → code | assignment, python_builtin_call, python_comment |
| 6 | math → code | assignment, python_builtin_call, python_comment |
| 7 | math → code | assignment, python_builtin_call, python_comment, python_method_call |
| 8 | math → code | assignment, python_builtin_call, python_comment, python_method_call |
| 9 | math → code | assignment, python_builtin_call, python_comment |
| 10 | math → code | assignment, python_builtin_call, python_comment |
| 11 | math → code | assignment, python_builtin_call, python_comment |
| 12 | math → code | assignment, python_builtin_call, python_comment |
| 13 | math → code | assignment, python_builtin_call, python_comment |
| 14 | math → code | assignment, python_builtin_call, python_comment |
| 15 | math → code | assignment, python_builtin_call, python_comment |
| 16 | math → code | assignment, python_builtin_call, python_comment |
| 17 | math → code | assignment, python_builtin_call, python_comment |
| 18 | math → code | assignment, python_builtin_call, python_comment |
| 19 | math → code | assignment, python_builtin_call, python_comment |
| 20 | math → code | assignment, python_builtin_call, python_comment, python_definition |
| 21 | math → code | assignment, python_builtin_call, python_comment, python_definition |
| 22 | math → code | assignment, python_builtin_call, python_comment, python_definition |
| 23 | math → code | assignment, python_builtin_call, python_comment, python_definition |
| 24 | math → code | assignment, python_builtin_call, python_comment, python_control, python_definition |

Auf den Slides wurden drei Änderungen anhand des Inhalts geprüft: Seite 2 `python hello.py` als CLI-Code, Seite 15 die `print`-Signatur mit Keywordargumenten als Code statt Mathe, Seite 31 das monospaced `return` als unsicheres Python-Fragment. `round(number[, ndigits])` und weitere nicht eindeutige Wörter bleiben konservativ Text. Es gibt in diesen beiden Originalen keinen nachgewiesenen echten mathematischen Formelblock; die Null bei Mathe ist daher allein kein Qualitätsbeweis.

Gegenbeweis gegen pauschales `math → code`: Tests prüfen Gleichungen, Potenz-, Summen-, Integral- und LaTeX-Notation jeweils mit proportionaler **und** Monospace-Schrift. Ein echtes erzeugtes PDF enthält zugleich `print(x=1)` und `x^2 + y^2 = z^2`; der reale isolierte Worker klassifiziert sie getrennt als Code und Mathe.

Beide Originale wurden zusätzlich jeweils in einen neuen externen Workspace über `MaterialDownloader.obtain(local_file=…)` importiert und mit `MaterialProcessor.parse(execute=True)` verarbeitet. Modell-Roundtrip und geprüftes Resume bestehen. Original-URLs, Bindings und Raw-Hashes bleiben identisch; neue Receipts haben korrekt `origin=local_import`. Hashes der alten Raw-, Receipt- und normalisierten Dateien wurden vorher/nachher unverändert geprüft; keine alten HTTP-Receipts kopiert oder umgedeutet.

## Versionierung und Kompatibilität

PDF-v2 wird explizit durch `parse_pdf()` und `parser_for()` ausgewählt. Der generische `ParserConfig`-Default und fehlende Legacy-Versionen bleiben `1`. Version `2` ist jetzt für HTML **und PDF** erlaubt; Code-/Bildparser bleiben unverändert auf v1. Der kleine bestehende HTML-Vertragstest wurde nur entsprechend dieser erweiterten Versionsfreigabe angepasst.

Bestehende PDF-v1-JSONs, IDs und Receipts bleiben lesbar und mit expliziter alter Config über `MaterialProcessor.inspect()` prüfbar. Ein neuer expliziter v1-Parseversuch wird verständlich abgelehnt; der aktuelle Standardparser meldet bei bereits abgeschlossenem v1-Workspace einen Configkonflikt ohne Änderung seiner Artefakte. Keine automatische Migration.

Neue Config-ID führt gemäß bestehendem Hashvertrag zu neuen Dokument-/Block-IDs. Material-, Ressourcen-, Kurs-/Vorlesungsbindung, Original-URL und Raw-SHA ändern sich nicht. Schema und Dateiname `normalized.v1.json` bleiben bestehen: `v1` bezeichnet hier das Dokumentformat, nicht die Parserimplementierung.

## Tests und Reproduktion

**170 passed, 0 failed, 0 skipped**, 107,76 s, auf unverändertem finalem Code. Darin alle 119 Materialtests einschließlich 41 neuer PDF-v2-Fälle, drei gemeinsame Executor-Prüfungen, 30 Lecture-Adapter- und 18 präzise Evidence-Tests. Der erste gezielte PDF-Lauf zuvor bestand mit 45 Tests. Python 3.12.12, vorhandene uv-Umgebung, PyMuPDF 1.28.2; keine neue Dependency, kein Sync/Upgrade. Ruff, Format-, Diff- und Dokumentenlinkprüfungen erfolgreich.

```bash
# Optional auf die vorhandenen Original-Workspaces setzen; keine Ersatzdownloads:
# CS50_LECTURE_PDF_ARTIFACTS=/path/to/existing/lecture-workspace
# CS50_SOURCE_PDF_ARTIFACTS=/path/to/existing/source-workspace
CS50_TEST_PROFILE=offline uv run --offline --no-sync python -m pytest \
  tests/test_cs50_material_*.py \
  tests/test_cs50_executor.py::test_fresh_sync_import \
  tests/test_cs50_executor.py::test_success_and_verified_resume \
  tests/test_cs50_lecture_adapter.py tests/test_cs50_precise_evidence.py -q
```

Die zwei Originaltests werden ohne explizite lokale Workspace-Variablen einzeln übersprungen; alle übrigen neuen Fälle verwenden eigene Strings/PDFs. Das eigenständige portable Profil wurde ohne diese Variablen separat ausgeführt: **39 passed, 2 skipped**. Kein Gesamtsuitenlauf; bekannte TXT-Vertragsfehler nicht bearbeitet.

Abgedeckt: Calls/Keywordargumente, Input-Zuweisung, Definitionen, Kommentare, mehrzeilige/nummerierte Funktionen, Font-Flags und Namen, echte Mathe versus Ambiguität, falsche Nummern/Separatoren, genau erhaltene Zeichen/Einrückungen und BBoxes, JSON-Roundtrip, Byte-/Seiten-/Block-/Bildlimits, echte Worker-Prozessisolation, Timeout und Abbruch der gesamten Prozessgruppe einschließlich Kindprozessen sowie alte Receipts und getrenntes Reprocessing.

## Kontrolliertes Reprocessing ohne neuen Download

Im uv-Worker nach Integration dieses PRs einen vorhandenen, geprüften Plan mit **genau einem** PDF-Binding nutzen. Variablen auf tatsächliche lokale Dateien setzen; nicht nach ähnlich benannten Dateien suchen, keine Receipts kopieren oder bearbeiten:

```bash
NEW_PDF_WORKSPACE=$(mktemp -d /tmp/cs50-pdf-v2-XXXXXX)
uv run --offline --no-sync python -m scripts.cs50_materials import-local \
  --plan "$REVIEWED_ONE_PDF_PLAN" --workspace "$NEW_PDF_WORKSPACE" \
  --course cs50_python --section 0 --local-file "$ORIGINAL_RAW_PDF" --execute-import
uv run --offline --no-sync python -m scripts.cs50_materials parse \
  --plan "$REVIEWED_ONE_PDF_PLAN" --workspace "$NEW_PDF_WORKSPACE" \
  --course cs50_python --section 0 --execute-parse
uv run --offline --no-sync python -m scripts.cs50_materials status \
  --plan "$REVIEWED_ONE_PDF_PLAN" --workspace "$NEW_PDF_WORKSPACE" \
  --course cs50_python --section 0
```

Neuer Receipt muss `name=pdf, version=2` und denselben geprüften Raw-SHA aufweisen. Bei Konflikt stoppen; kein Overwrite, kein Downloadfallback. Für die zweite PDF einen weiteren neuen Workspace verwenden. Siehe [Materialbetrieb](../operations/material_ingestion.md).

## Einschränkungen

Deterministische Heuristik, keine vollständige Sprach-/Formelerkennung oder mathematische Verifikation. Gemischte Prosa-/Code-/Formelblöcke werden nicht neu segmentiert; Unsicherheit bleibt sichtbar. Python-ähnliche Fragmente müssen nicht ausführbar sein. Reine numerische Zuweisungen und generische Funktionsnotation können absichtlich unklassifiziert bleiben.

Die Nummernansicht ist keine zweite kanonische Quelle: andere Gutter-/Umbruchmuster werden nicht repariert. Bestehende PDF-Textreihenfolge und explizite Leerzeichen sind maßgeblich; fehlende Leerzeichen werden nicht aus Geometrie ergänzt. Keine OCR-/Formelrekonstruktion, keine Ausführung und keine Erweiterung der bisherigen Tabellen-/Bildinterpretation.

Der bestehende `-I`-Subprozess, CPU-/Adressraum-/Ausgabelimits sowie Timeout-Prozessgruppenabbruch bleiben unverändert und gelten auch für die neue AST-/Regexarbeit. Keine globalen Änderungen an Ressourcen-, Event-Loop-, Datenbank- oder LLM-Konfigurationen.
