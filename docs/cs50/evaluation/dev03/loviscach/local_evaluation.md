# DEV-03E – Erste reale lokale Parsingevaluation, Goldprüfung offen

20.10.2026. **Status: `real_parsing_evaluation_completed_gold_pending`.**
Die vier genehmigten Klausuren wurden tatsächlich verarbeitet, Originalhashes
unverändert. Keine fachliche Realabnahme und keine Produktivfreigabe.

## Freigabe und tatsächliche Runtime

Betreiber und vorgesehener menschlicher Reviewer: `robfra`. DEV-03E bestätigt
die vier Datei-/Hashpaare, Namespace `loviscach_exams`, externe Identität jeweils
unveränderter Dateiname sowie die vorgeschlagenen Source-IDs aus dem integrierten
[DEV-03D-Inventar](corpus_inventory.v1.json). Dessen bestätigter Bodydigest bleibt
`a37319b9b0d18fb246f6071638a35ae30b39f39f01187a3579cf5a501862500e`.
Der frühere [Freigabeentwurf](authorization.md) und das Inventar sind historische
Metadatensnapshots; ihre alten Statusflags werden nicht stillschweigend geändert.
Eine Kurs-/Sourcebestätigung ist keine bereits erfolgte SourceVersion-Publikation.

Der ausdrücklich benannte externe private Ergebnisroot wurde nach Prüfung von
Pfad, Eltern, Identität, Abwesenheit und freier Kapazität neu angelegt. Alle
Verzeichnisse 0700, Dateien 0600, Eigentümer ausschließlich der lokale Betreiber.
Keine Symlinks, keine Überschreibung und keine automatische Löschung; Aufbewahrung
bis zu einer gesonderten ausdrücklichen Löschentscheidung. Private Hostpfade und
Originalinhalte werden hier nicht veröffentlicht. Ausgabebudget 128 MiB plus
256 MiB freier Reserve. Vor Anlage waren rund 900 MiB frei; tatsächlicher
Ergebnisbestand liegt bei rund 2,35 MB (2,24 MiB).

Basis der Parser: integrierter master `ba59560` (#126–#131 gemergt).
Ausgeführter neuer Orchestrator: Commit `f0115bd`,
`scripts/acceptance/dev03_loviscach.py`. Er startet ausschließlich die bereits
integrierten, unveränderten `pdf_worker.py` (PDF-v2) und C13 `visual_worker.py`.
Workerdateihashes, Runnerhash, Pythonversion und Gitrevision sind privat gebunden.
Python 3.12.12, PyMuPDF 1.28.2, Pydantic 2.13.4, Pytest 9.1.1, Ruff 0.16.0;
keine Downloads, Installationen, externen LLM-/Cloud-/OCR-/Embeddingdienste.

**Isolierte Workerbeobachtungen:** kein erfundenes `MaterialResource`, keine
falsche CS50-Kurskennung, kein C23-Import oder Source-/ParsedVersion, kein C10-
Qualityreceipt, keine Indexgeneration und keine B1-Reviewpersistenz. Die separate
Kursvertragsänderung ergänzt `loviscach_mathe_1`, ist für diesen Lauf aber keine
Runtimevoraussetzung. CS50-Materialadapter werden dadurch noch nicht generisch.
Die vorhandenen `ParserConfig`, `InventoryLimits`, C11-Notationgrammatik und
C23-`ContentLocator`-/Hash-/Identitätshilfen werden unverändert wiederverwendet;
keine neue Evaluationsengine, PDF- oder Formelrekonstruktionspipeline.

## Tatsächliches Inventar der Extraktion

Alle Dateien haben zwei Seiten. Textblöcke umfassen auch die als mathematisch
klassifizierten Blöcke; die Spalten werden nicht addiert.

| Datei | Textblöcke | PDF-v2-Mathblöcke | Formelkandidaten | Strukturkandidaten | C13-Vektorgruppen | Rasterrefs / Tabellenkandidaten | Parserwarnungen |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| `Mathe_1_2020-01-31.pdf` | 38 | 8 | 8 | 16 | 8 | 0 / 0 | 0 |
| `Mathe_1_2022-01-28.pdf` | 41 | 8 | 8 | 17 | 7 | 0 / 0 | 0 |
| `Mathe_1_2023-03-21.pdf` | 34 | 8 | 8 | 16 | 4 | 0 / 0 | 0 |
| `Mathe_1_2024-01-31.pdf` | 41 | 9 | 10 | 17 | 11 | 0 / 0 | 0 |
| Summe | 154 | 33 | 34 | 66 | 30 | 0 / 0 | 0 |

Ein zusätzlicher Paragraph wurde aufgrund wörtlicher Notationssignale zum
Formelkandidaten. Eine Kandidatenregion ist ein Textblock und keine behauptete
Anzahl atomarer Formeln. Die 30 geometrischen Vektorgruppen sind keine 30
fachlich bestätigten Abbildungen. Null Raster-/Tabellenkandidaten beweisen nicht,
dass das Original keine visuell relevante Struktur oder Tabelle enthält.

Seitenabdeckung in Blockzahlen: 2020 **20/18**, 2022 **21/20**, 2023 **23/11**,
2024 **24/17**. Keine fehlenden/ungültigen Seiten- oder BBoxreferenzen in diesen
Ausgaben; keine widersprüchliche Seitenzahl. Keine automatisch erkannten
Überschriften durch die vorhandene Fontheuristik. Vollständigkeit, korrekte
Lesereihenfolge und richtige Aufgabengrenzen sind ohne unabhängige Referenz nicht
bewiesen. Die Native-Reihenfolge bleibt erhalten, keine automatische Korrektur.

## Syntax, Befunde und Reviewprioritäten

C11 prüft ausschließlich die tatsächlichen wörtlichen Kandidaten im unterstützten
`plain_text`-Format. Keine automatische LaTeXübersetzung oder LLMrekonstruktion.
**3 syntax_valid, 31 not_evaluable, 0 syntax_invalid**. Je einer der ersten drei
Dokumente enthält einen grammarlesbaren Kandidaten; alle zehn des vierten
Dokuments bleiben nicht evaluierbar. Ganze Blöcke können Prosa und nicht
unterstützte Notation enthalten. Deshalb ist `not_evaluable` weder ein bewiesener
Formelfehler noch ein fehlender Ausdruck; `syntax_valid` ist kein Richtigkeitsbeleg.
Keine Äquivalenzprüfung ohne unabhängige passende Formelreferenz.

- **Technisch nachgewiesen:** Keine Fehler in den ausgeführten Rawhash-,
  Seiten-/BBoxzuordnungs-, Worker-/Wiederholungs- und privaten Dateiprüfungen.
  Das ist keine universelle Aussage über Parser- oder Inhaltsfehlerfreiheit.
- **Plausible Reviewfälle:** 50 Tasklabel-/Grenzstellen und 16 wiederholte
  Textregionen (mögliche Header/Footer), 34 mathematische Textkandidaten sowie
  30 Vektorgruppen. Kein Header/Footer wird gelöscht, keine Lesereihenfolge
  automatisch umsortiert und keine Formel korrigiert.
- **Menschlich bestätigte fachliche Fehler:** bisher keine; noch keine echten
  Goldreviews ausgeführt. Qualitätsscores bleiben null, evaluierbarer Goldnenner 0.

Priorität: erst Zeichen-/Vorzeichen-/Exponententreue und 31 unentscheidbare
Notationsfälle am Original prüfen; danach Aufgabengrenzen, mögliche Header/Footer
und die semantische Zugehörigkeit geometrischer Gruppen. Konkrete Parserfixes
erst aus einem unabhängig bestätigten und reproduzierbaren Defekt ableiten.

## Reproduzierbarkeit und Ressourcen

Zunächst ausschließlich 2020, dann nach privater Hash-/Rechte-/Kapazitätskontrolle
die übrigen drei. Je Datei zwei echte PDF- und zwei C13-Workerausführungen:
**16 Workerrequests, acht byteinhaltlich identische kanonische Ergebnispaarungen**.
Alle Requests wurden gegen die jeweils genehmigten Rawhashes erneut geprüft.
Alle Originale nach Abschluss nochmals SHA256-identisch. Keine produktiven
Content-/Index-/Jobdaten sind Inputs oder Ausgaben des Reallaufs.

| Datei | Primärer PDFworker, Sekunden | Primärer C13worker, Sekunden | Höchster Worker-RSS in KiB inklusive Wiederholung |
| --- | ---: | ---: | ---: |
| 2020 | 0,908 | 0,485 | 61100 |
| 2022 | 0,776 | 0,458 | 61352 |
| 2023 | 0,607 | 0,643 | 61060 |
| 2024 | 0,864 | 0,591 | 61624 |

RSS wird pro Kindprozess mit `wait4` gemessen, nicht aus einem kumulierten
Elternprozessmaximum abgeleitet. PDF/C13 behalten ihre vorhandenen 20-s-/1024-MiB-
Limits. Die niedrige lokale Reviewdarstellung ist ebenfalls auf 1024 MiB
Adressraum begrenzt; ihr eigener RSS wurde nicht separat gemessen. Die Tabelle
ist keine Gesamtlaufzeit oder Lastfreigabe.

Private Artefakte: `execution.json`, Originalrequests, unveränderte Workerresponses
und Diagnostik, individuelle Ressourcenbelege, `analysis.json`, `report.json`,
erstes und finales Dateimanifest sowie `review/`. **115 Dateien im finalen
Manifest**, einschließlich des unveränderten ersten Stands; finales Manifest
selbst nicht selbstgehasht. Der private Reportbodydigest lautet
`6551d52db9e7cb416d91ca807adea06d30bec9589417850f8f6e5ca3726b458b`.
Zeit-/Ressourcenmessungen sind separate Ausführungsbelege; der deterministische
Reportbody bindet die Inhaltsbeobachtungen. Ableitungen und Auswahl wurden erneut
aus den gespeicherten Workerresponses berechnet und verglichen.

Lokaler Ablauf mit ausschließlich den ausdrücklich genehmigten Rootvariablen:

```sh
python -m scripts.acceptance.dev03_loviscach \
  --input-root "$DEV03_INPUT_ROOT" --output-root "$DEV03_OUTPUT_ROOT"
# Erst sicheren ersten Lauf prüfen; danach dessen exakten Namen einsetzen:
python -m scripts.acceptance.dev03_loviscach \
  --input-root "$DEV03_INPUT_ROOT" --output-root "$DEV03_OUTPUT_ROOT" \
  --complete "$DEV03_RUN_NAME"
```

Ein neuer Aufruf ohne `--complete` erzeugt einen neuen kollisionsfreien Run;
kein bestehender Report wird überschrieben. Erneute Completion desselben Runs
ist gesperrt. Abbruchbelege bleiben erhalten; keine automatische Bereinigung.
Private Inhalte gehen ausschließlich an lokale Workerdateien. Parent und Worker
blockieren Python-Socket-/HTTP-/URL-Auditereignisse; kein externer Dienst wird
aufgerufen. Dies ist keine Behauptung einer universellen Kernel-Syscallanalyse.

## Konkrete menschliche Übergabe und Retrievalgrenzen

Private `review/index.html`: Originalregion links als lokaler PNGausschnitt mit
vier PDFpunkten Kontext, unveränderter extrahierter Text rechts als escaped Text.
Keine Scripts, Remoteinhalte, aktiven Formeln oder HTMLausführung aus Originalen.
`review/candidates.json` enthält **20 Formel-, zehn Struktur-, zehn Visualfälle**,
quellenübergreifend ausgewählt: 11/11/9/9 Fälle für 2020/2022/2023/2024. IDs,
Originalhash, Seite/BBox und Responsepointer sind stabil. Der PDFpointer bezieht
sich auf die tatsächlichen `parts`, der C13-Pointer auf `observations`.

`robfra` prüft insbesondere Originalzeichen, Vorzeichen, Exponenten, Aufgabengrenzen
und Visualzuordnung unabhängig. `independent_reference`, `review_decision`,
`reviewed_by` und `reviewed_at` sind bewusst **null**, Status `pending_review`.
Urteile mit Kandidaten-ID, tatsächlicher Referenz, Begründung und Datum als neue
private Reviewrevision dokumentieren; versiegelte Ausgangsdateien nicht verändern.
Keine Parserausgabe ist bestätigtes Gold. Noch keine B1-Tasks erzeugt: dafür
fehlen echte Source-/ParsedVersions und eine passende generische Materialbindung.

Vor späterem Retrieval: Kursvertrag integrieren, generische Raw-/Material-/Receipt-
Bindung sicher ermöglichen, isolierte Content-/Review-/Indexroots und technische
Grants ausdrücklich genehmigen, unabhängige Fragen/Goldregionen vor Ranking
festlegen und den begrenzten Pool menschlich prüfen. DEV-03E erlaubt keinen
Indexbuild oder realen Retrievalvergleich; beides wurde nicht ausgeführt.

## Tests und Git-Lifecycle

Lokale Suite: **206 pass / 0 fail / 0 skip, 88,68 s** für
`test_dev03_loviscach.py`, `test_cs50_material_pdf.py`,
`test_cs50_visual_inventory.py`, `test_math_formula_evaluation.py`.
Nach der kleinen Kontextmargin-Anpassung an Vergleichsbildern der betroffene
gesamte Crop-/Escapingfall erneut: **1 pass / 0 fail / 0 skip, 1,28 s**.
Überlappende Läufe nicht addieren. Präfix mit `DEV03_PYTHON` als Alias für den
tatsächlich verwendeten vorhandenen Projektinterpreter:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  "$DEV03_PYTHON" -m pytest \
  -q -p no:cacheprovider
```

Neue Tests verwenden ausschließlich synthetische Fixtures. Erster Entwicklungslauf
6 pass/1 fail: Orchestrator nutzte den Formatnamen `plain` statt des vorhandenen
C11-Vertrags `plain_text`; vor jedem Reallauf korrigiert und erfolgreich geprüft.
Keine Änderung an C11 oder am PDFparser. Private Realdaten sind keine Testfixtures.
Ruff Check und Format Check für die zwei neuen Pythondateien sowie
`git diff --check` erfolgreich. Echte private Wiederholungs-/Hash-/Rechteprüfungen
ergänzen die Tests: 16 autorisierte Workerrequests, acht identische Ergebnispaarungen,
115 manifestgebundene Dateien und 40 deterministisch wiedergewählte Review-IDs.
Eine lokale Nichtveröffentlichungsprüfung vergleicht die vorgesehenen Gitdateien
mit vollständigen extrahierten Originalblöcken ab 24 Zeichen und prüft auf private
Original-/Ergebnisroots; keine Treffer. Keine Behauptung einer universellen
Datenabflussanalyse. Im Gitbestand sind nur Orchestrator, synthetische Tests und
dieser redigierte Bericht vorgesehen; private Originalausgaben bleiben außerhalb.

Separater Kurs-/API-Regressionslauf: 277 pass/1 fail/0 skip; ein bestehender
C16-Planungsfall traf `database is locked`. Isoliert auf geändertem und
unverändertem Runtimecode jeweils bestanden, danach alle 36 C16-Fälle bestanden.
Ursache offen; kein Parserdefekt und keine Baseline-Reproduktion behauptet.
Der vollständige Befund steht im eigenständigen Kursvertrags-PR. Diese Fallzahlen
überlappen und werden nicht mit der lokalen 206er-Suite addiert.

Code und redigierter Bericht über eigenen PR; separater PR für den Kursvertrag.
Keine automatische Zusammenführung, offene fachliche Abnahmen bleiben offen.
Eigene Branches/Worktrees bleiben bis zur bestätigten Integration erhalten.
MAINT, frühere Worktrees und private Sicherungen bleiben unberührt. Private
Realresultate werden auch nach einem späteren PRmerge nicht automatisch gelöscht.
