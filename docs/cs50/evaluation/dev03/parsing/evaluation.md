# DEV-03B – Synthetische Parsing-, Formel- und Visualevaluation

20.10.2026. Basis: Backend-master `7a4f2be`; vorhandene C10/C11/C13/C23-06-
Verträge. Ausschließlich bereits autorisierte, handgeschriebene/generierte
synthetische Fixtures. Keine reale Originaldatei, LLM-/Provider-/Embeddinganfrage,
Migration, Knowledgeänderung oder fachliche Freigabe.
**Realstatus: `blocked_pending_source_authorization`.**

## Ausgeführter Umfang und bestehende Verträge

`scripts/acceptance/dev03_parsing.py` komponiert vorhandene Funktionen und
Testfixturehilfen, ohne neue Evaluationsmodelle, Registry, Indexengine oder Parser.
Es akzeptiert nur neue externe synthetische Workspace-/Ergebnisroots; keine
Originalpfad-, URL- oder Corpusoption. Runtime-/Parseralgorithmen bleiben gleich;
einzige notwendige Runtimekorrektur ist die unten nachgewiesene C23-Bilderfassung.
Keine Verwendung neuer/unintegrierter A- oder C-Verträge.

| Testbestand | Tatsächliche Verarbeitung | Grenze |
| --- | --- | --- |
| HTML-v2 `material_quality/notes.html` | bestehender Parser, kompletter C23-Bundle-/Receipt-/Revisionsgate, C10 und C13 | Kleine synthetische Notes, keine reale HTMLqualität |
| Code mit Ä/CRLF | bestehender Codeparser, bestehende Material-/Goldverträge | Exakte Zeichen, kein ausgeführter Sourcecode |
| PDF-v2-Vertragsfixture | bestehender normalisierter Testvertrag mit Code/Table/Math | **Kein** nativer PDFparser für diese Tabelle/Formel |
| Nativer zweitseitiger PDF `visual_inventory/source.pdf.b64` | exakte versionierte synthetische Rawbytes, tatsächlicher PDF-v2-Worker zweimal, vollständiges C23-Bundle und C13-Scan | Geometrische Testformen; kein semantischer Diagramm-/Formelgoldstandard |
| SRT | bestehender Importer/Gate, Text und bekannte überlappende Cuezeiten | Keine historische D06-Pfadübernahme, keine TXT/VTT-Behauptung |
| 42 C11-Formelpaare | bestehende Datensätze/Evaluator, Backend `none` und isoliertes `sympy` | Absichtlich richtige/falsche/unklare Paare; keine Modellqualitätsmessung |

Die acht Parsingreferenzen sind vorab im Rezept geschriebene Konstanten aus den
bereits autorisierten synthetischen Fixture-Spezifikationen. Parserausgaben liefern
nur Zielpointer/Identitätsbindung, niemals die erwarteten Texte. Reviewer-/Datums-
felder sind ausdrücklich Testmarker, keine echte menschliche Goldbestätigung.
SRT-Locator ist aus dem handgeschriebenen Cue `.1–3.0` und Segment 0 spezifiziert.
Native PDFbbox-/Diagrammsemantik wird nicht aus dem Parser als Gold abgeschrieben.

Bestehender CorpusManifest/GoldDataset und Evaluator liefern **acht bestandene
Vergleichsfenster** aus fünf verifizierten synthetischen Bundles: HTMLtext/Code,
Codezeile, Vertragstabelle/-formel, zwei native PDFseitentexte und SRTcue/Locator.
[Materialreport](run/materials/evaluation_report.v1.json) und
[Zusammenfassung](run/materials/summary.md). Vollständigkeits- oder Struktur-PR
für einen Realkorpus ist daraus nicht ableitbar. Alle Realnenner bleiben 0/Raten null.

## Nachgewiesener technischer Fehler und minimale Korrektur

Baseline `7a4f2be`: Der native PDF enthält zwei räumlich verschiedene Verwendungen
desselben 2×2-Bildes. PDF-v2 erhält dafür mehrere Referenzen/Aliases mit einem
hashadressierten Dateipfad. C23 `_capture` wollte denselben Bildpfad erneut in
sein Frozen-Dateiinventar aufnehmen und verweigerte das gültige Bundle mit
`bundle input collision or count limit`. Dies wurde vor jeder Codeänderung direkt
am tatsächlichen Gate reproduziert und als bestehender
[Baseline-C23-Report](baseline/evaluation_report.v1.json) festgehalten.

Korrektur ausschließlich in `src/content_store/adapters.py`: Bereits erfasste
**Bildpfade** nicht erneut als Byte-Datei aufnehmen. Distinkte Image-IDs und
Positionen bleiben unverändert, Source-/Payload-/Receipt-/Implementationshashes und
sämtliche vorhandenen Prüfungen bleiben maßgeblich. Kollisionen mit Raw-/Payload-
oder anderen Rollen bleiben im bisherigen `take` abgewiesen. Der Regressionstest
verändert eine einzelne Bildhashdeklaration bei neu gebundenem Receipt/Evidence;
das echte Gate verweigert weiterhin. Ein Bildpfad auf die Normalized-Payload bleibt
als Rollenkollision gesperrt. Keine pauschale Freigabe doppelter Dateireferenzen.

Danach wird derselbe versionierte synthetische Raw-PDFhash vom Gate angenommen;
alle fünf Bundles sind verifiziert. Das ist eine Korrektur der technischen
Bundleaufnahme, **keine gemessene Verbesserung der Parser-/Formelqualität**.
Baseline hat kein bestätigtes Gold und keine fachlichen Scores. Neue acht
Vergleichsfenster werden daher nicht als Vorher-/Nachher-Qualitätssteigerung verkauft.
Keine Parseränderung, Originalmigration oder Reparatur vorhandener Artefakte.

## C11-Ergebnisse und Nenner

[Notation/Struktur](run/math-none/summary.md),
[isolierte SymPyprüfung](run/math-sympy/summary.md),
[gemeinsamer Datensatz](../../../../math_evaluation/formula_cases.v1.json).
Beide Läufe verwenden denselben unveränderten Inputhash.

| Zählwert | Backend none | Backend sympy |
| --- | ---: | ---: |
| Synthetische Fälle | 42 | 42 |
| Gepaarte eindeutige Referenz/Vorhersage | 37 | 37 |
| Exact Match | 10/37 | 10/37 |
| Normalized Match | 12/37 | 12/37 |
| Strukturell vergleichbar / Übereinstimmungen | 33 / 12 | 33 / 12 |
| Entschiedene Äquivalenzprüfungen / äquivalent | 12 / 12 | 28 / 16 |
| Davon durch SymPy erkannt | 0 | 4 |
| Nicht entschiedene Rekonstruktionen | 25 | 11 |
| Reale Fälle / Nenner | 0 / 0 | 0 / 0 |

Kein LLM rekonstruiert hier neue Formeln. Die zusätzliche Symbolik entscheidet nur
explizit unterstützte Syntax unter unveränderten Zeit-/Ressourcenlimits; unbekannt
bleibt `undetermined`. Unterschiedliche Backendabdeckung ist keine Verbesserung
eines Rekonstruktionsmodells. Fehlende/zusätzliche/teilweise/falsche Formeln,
Operator-/Exponent-/Index-/Bruch-/Syntaxfehler bleiben in den C11-Einzelbefunden.
Die absichtlich adversarialen Referenzpaare sind keine beobachteten Fehlerquoten
eines echten Dokuments. Unklare Visualkontexte erfordern später menschlichen Review.

## C13-Beobachtungen

| Bestand | Visualassets | Verifizierte Bildpositionen | Einzigartige Bildbytes | Reference-only | Fehler |
| --- | ---: | ---: | ---: | ---: | ---: |
| HTML | 1 | 0 | 0 | 1 | 0 |
| Nativer PDF | 8 | 2 | 1 | 6 | 0 |

[HTMLinventar](run/html-visual.json), [PDFinventar](run/pdf-native-visual.json).
Vier normalisierte PDFbildreferenzen ergeben in C13 zwei physische Bildpositionen
mit zwei Aliasreferenzen. Die sechs übrigen geometrischen Kandidaten sind keine
fachlich verifizierten Diagramme. Alle Assets behalten `requires_visual_review`
oder `uncertain`; 15 PDFwarnungen sind keine pauschalen fachlichen Fehler.

Die öffentlichen Inventare verwenden das vorhandene `VisualInventory`-Modell;
nur `inputs` erhält explizite `synthetic/…`-Pfadaliases statt privater Hostroots,
der bestehende Modelldigest wird darüber neu berechnet. Diese Projektionen sind
keine direkt ausführbaren Pfadfreigaben. Native Analyseergebnisse/Originalhashes
bleiben unverändert; kein neuer konkurrierender Visualreportvertrag.

## Reproduzierbarkeit und tatsächliche Umgebung

Python 3.12.12/Pydantic 2.13.4/Pytest 9.1.1, PyMuPDF **1.28.2**, BeautifulSoup
**4.15.0**, isolierter SymPyworker **1.14.0**, Ruff 0.16.0; vorhandene Umgebung,
keine Installation. Tatsächlicher erfolgreicher CLI-Aufruf:

```sh
PYTHONDONTWRITEBYTECODE=1 \
/home/robfra/0_Portfolio_Projekte/gmp_compliance/.venv/bin/python \
-m scripts.acceptance.dev03_parsing \
--workspace /tmp/dev03b-synthetic-release --output /tmp/dev03b-reports-release
```

Native PDFausgaben werden zweimal wirklich extrahiert und verglichen. C23-Report
und C13-Inventare wiederholen dieselben eingefrorenen Inputs deterministisch.
Alle ursprünglichen Fixture-/Bundlebytes bleiben vor/nach Evaluation identisch.
Private Corpus-/Gold-Snapshots liegen nur im neu erzeugten Workspace. Ein neuer
Workspace erzeugt einen anderen Corpusdigest wegen vorhandener absoluter
InventorySelection-Pfade; gleiche eingefrorene Inputs ergeben identische Digests.
Keine checkoutunabhängige Bytegleichheit dieses pfadgebundenen Digests behauptet.
C13-Aliaspfade sind explizit dokumentiert; C11-Eingabepfad ist ein Repositoryalias.

Versionierte Dateien sind die tatsächlichen CLI-Reportbytes/markierten C13-
Pfadprojektionen; [Dateimanifest](run/manifest.json) bindet exakte Bytes. Kein
privater Hostroot steht darin. Der erste CLI-Versuch wurde vom beschriebenen
ursprünglichen Gate abgewiesen. Ein Entwicklungstest erwartete zwei statt vier
normalisierte Aliasreferenzen (1 pass/1 fail, 73,47 s); korrigiert wurde die
Testannahme zugunsten des exakten zweifachen Positionsnachweises, kein Parser.
Abschließende Suite und Priorisierung folgen unten.

Abschließende gemeinsame Prüfung:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
/home/robfra/0_Portfolio_Projekte/gmp_compliance/.venv/bin/python -m pytest \
-q -p no:cacheprovider tests/test_dev03_parsing.py \
tests/test_cs50_material_quality.py tests/test_math_formula_evaluation.py \
tests/test_cs50_visual_inventory.py tests/test_content_store_adapters.py \
tests/test_content_store_inventory.py tests/test_cs50_material_pdf.py \
--basetemp=/tmp/dev03b-contracts
```

**370 passed / 0 failed / 0 skipped**, 217,80 s: zwei neue Fälle, 94 bestehende
C10-, 123 C11-, 69 C13-, 49 C23-Adapter-, 26 C23-Inventar- und sieben native
PDFfälle. Kein Gesamtrepositorylauf. Netzwerkzugriff in den Tests verboten.
Nach diesem Lauf wurde der erste neue Fall zusätzlich um echte C23-Publikation
und unveränderten Raw-/Payload-Byte-Roundtrip ergänzt; gezielte Nachprüfung unten.
Ruff Check/Format Check für die drei geänderten Pythondateien und diff check
sind erfolgreich. Keine Assertions oder Runtimegrenzen abgeschwächt.

Priorisierte Folgearbeit: P1 ist der hier isoliert behobene Aufnahmefehler für
geteilte Bildbytes. P0 für die Realabnahme bleibt die fehlende Source-/Root-/
Nutzungs-/Aufbewahrungs-/Reviewerfreigabe; ohne sie keine realen Inhalte prüfen.
P2 erst danach: visuell unentscheidbare Formelregionen am Original reviewen,
Tabellen-/Lesereihenfolgen und geometrische Referenzen fachlich annotieren. In den
synthetischen Befunden ist kein zusätzlicher Parser-/Rankingalgorithmusfehler
nachgewiesen. Kein Folge-Issue für absichtlich falsche C11-Testpaare erfunden.
Bestehende C23-/C24-/C25-Trackingobjekte weiterverwenden; keine Realabnahme schließen.

Branch/Worktree und dauerhafte Berichte bleiben für den regulären PRprozess
bestehen. Keine automatische Zusammenführung, kein MAINT-Cleanup.

Gezielte Nachprüfung des erweiterten Publikationsfalls:
`tests/test_dev03_parsing.py::test_same_image_bytes_preserve_distinct_occurrences_and_hash_guards
 --basetemp=/tmp/dev03b-image-publication` mit demselben Präfix:
**1 passed / 0 failed / 0 skipped**, 3,17 s. Tatsächliche C23-Storepublikation mit
geteilten Bildbytes und unveränderter Raw-/Parsed-Payload; widersprüchliche Hashes
und Rollenalias weiterhin gesperrt. Überschneidet den 370er-Lauf, nicht addieren.

Beim Commit prüfte der bestehende Whitespacehook die erzeugte Markdownkurzfassung
und fand Leerzeichen am Zeilenende bei leeren Befundlisten. Der vorhandene
`evaluate_materials.publish` entfernt jetzt ausschließlich diese abschließenden
Leerzeichen (`rstrip` je Inventarzeile); keine Prüfung/Hook wurde übersprungen.
Derselbe eingefrorene Report wurde im neuen externen Ziel erneut publiziert.
JSON-/Metrikbody unverändert, Markdown-/Dateimanifesthash entsprechend neu gebunden.
Der äußere Snapshot bindet diese tatsächlichen Publisherbytes. Keine bestehenden
externen Reportziele wurden überschrieben. Gezielte Publikationsnachprüfung unten.

Gezielte Nachprüfung der Markdownpublikation mit bestehender CLI/Hash-/No-Overwrite-
Prüfung: **1 passed / 0 failed / 0 skipped**, 1,23 s
(`tests/test_cs50_material_evaluation.py::test_cli_reproducible_hashes_and_no_overwrite
 --basetemp=/tmp/dev03b-report-format`, gleiches Präfix). Alle vier geänderten
Pythondateien wurden abschließend mit Ruff geprüft. Die zusätzliche Textformatierung
ändert keine JSONbefunde oder semantischen Metriken.

Nach der Ausgangsprüfung wurde DEV-02B #127 inzwischen extern gemergt
(`61ad351`); UI #17 ist weiterhin offen. Dies ändert keine Realfreigabe.
Die obigen Läufe behalten ihren genauen Basisbezug `7a4f2be`; keine ungemergte
DEV-03-A/B/C-Implementierung ist als Voraussetzung dieser Evaluatoren verwendet.
