# CS50 Lecture Notes: HTML-Normalisierung v2

Stand: 15.10.2026; Basis `master` / `6f51e34`.

## Nachgewiesene Ursache

Der alte `walk()`-Listenpfad speicherte `ul.get_text(" ", strip=True)` als Volltext und zusätzlich verschachtelte Code-/Linkblöcke. Damit enthielt der Listentext auch abgeflachten Python-Code; Absatzgrenzen gingen verloren und derselbe Code erschien nochmals als eigener Block. `<a><code>…</code></a>` erzeugte zusätzlich `unknown_block`.

Die **separaten** `<pre>`-Blöcke waren bereits in v1 exakt erhalten. Der Fehler lag dort nicht in der Codeextraktion selbst, sondern in der doppelten, whitespace-normalisierten Listenprojektion. Der bisherige DOM-Abbau von Navigation konnte außerdem Herkunftspfade verschieben.

## Änderung und bestehende Verträge

`src/tools_materials/parse_html.py` traversiert Listen jetzt in Dokumentreihenfolge. `list`-Blöcke speichern Struktur, keine aggregierten Inhaltstexte. Jedes `li` liefert eigene Textfragmente, explizite Absätze, weitere Listen, Code und Bildreferenzen in Quellreihenfolge. Wiederholte gleiche Listeneinträge bleiben mit unterschiedlichen DOM-Pfaden und Indizes erhalten.

Die vorhandenen `Block`-, `Location`-, `NormalizedDocument`- und Receiptmodelle reichen aus. Keine neuen Blocktypen oder fachlichen Modelle:

- `list.data`: `ordered`, originales `start`, `reversed`, `item_doms`; auch leere Einträge sind strukturell vorhanden.
- `data.list_context`: geordneter Pfad von äußerer zu innerer Liste mit `list_dom`, `item_dom`, nullbasiertem `item_index`, `ordered` und originalem `li.value`. Damit sind Absatz, Code und Referenzen eindeutig ihrem Eintrag zugeordnet.
- Textblöcke: `data.fragment_index` unterscheidet mehrere Textläufe desselben DOM-Containers; `data.inline_code` enthält originale Codewerte mit `start`/`end` als exklusivem Zeichenintervall im jeweiligen Blocktext und eigenem Code-DOM-Pfad. Keine künstlichen Leerzeichen an Inline-Elementgrenzen.
- `<pre>`: dekodierter DOM-Text ohne Trimmen, Separatoren oder Ausführung, einschließlich Tabs, Einrückungen, Leerzeilen und Anführungszeichen. Sprache optional aus Quellattributen/-klassen, auch Rouge-Vorfahren wie `language-py`; keine Ableitung aus Seitensprache oder Dateinamen.
- Links bleiben Referenzblöcke mit URL, DOM und gegebenenfalls eigenen Inline-Code-Spannen. `data.reference_only=true` kennzeichnet die beabsichtigte Wiederholung ihres Labels gegenüber dem Absatztext. Mathe-Kandidaten werden ebenfalls als Referenzen markiert.
- Explizite TOC-Marker (`id=markdown-toc`, `toc`/`table-of-contents` als ID/Klasse, `role=doc-toc`, passende `aria-label`) ergeben `data.content_role=table_of_contents`, einschließlich der enthaltenen Blöcke. Eine normale Ankerliste genügt nicht.
- Boilerplate wird übersprungen, ohne den DOM-Baum zuvor umzubauen. `Location.dom` bezieht sich auf den mit `html.parser` gelesenen Originalbaum.

`ParserConfig` akzeptiert nun HTML-Version `2`; der generische bisherige Default und fehlende Legacy-Versionen bleiben `1`. `parse_html()` ohne Config und `parser_for()` wählen HTML-v2 explizit. PDF-/Code-/Bildparser bleiben v1; v2 wird für andere Parserarten abgewiesen. Ein expliziter HTML-v1-Neuparsingversuch wird verständlich abgelehnt, statt v2-Inhalte mit einer v1-Identität auszugeben.

Bestehende v1-JSONs bleiben lesbar. Ein abgeschlossener v1-Receipt lässt sich mit seiner expliziten alten Config über `MaterialProcessor.inspect()` weiter prüfen. Die normale aktuelle Verarbeitung erkennt dagegen den Parserkonflikt und verändert den alten Receipt nicht. Für Reprocessing ist ein neuer Workspace vorgesehen.

`config_id`, `document_id` und Block-IDs ändern sich durch die Version, wie vom bestehenden Hashvertrag vorgesehen. Material-/Ressourcen-/Kurs-/Vorlesungsbindung, Original-URL und Raw-SHA bleiben erhalten. `schema_version=1`, der Name `normalized.v1.json`, Storage und Downloader bleiben unverändert; der Dateiname bezeichnet das Dokumentformat, nicht die Parserversion.

## Vergleich am echten Original

Bereits lokal bereitgestellte Quelle: [CS50 Python, Notes 0](https://cs50.harvard.edu/python/notes/0/). Kein Ersatzdownload.

Raw: 71.718 Bytes, SHA-256 `54b34c0b0d4b7598d20b37f2763b53cb361b3e22e793965d47fe3fd6be6ecaf8`.

Der erneut ausgeführte Parser aus dem Basiscommit reproduziert das vorhandene v1-Dokument vollständig. Vergleich auf identischen Raw-Bytes:

| Messung | v1 | v2 |
|---|---:|---:|
| Blöcke insgesamt | 105 | 237 |
| Headings | 20 | 20 |
| Listencontainer | 20 | 22 |
| Absätze | 1 | 136 |
| Codeblöcke | 34 | 34 |
| Linkreferenzen | 25 | 25 |
| Unknown-Blöcke | 5 | 0 |
| Bildreferenzen | 0 | 0 |
| Textzeichen aller Blöcke | 23.692 | 18.779 |
| Textzeichen der Listenaggregate | 18.552 | 0 |
| `<pre>`-Text exakt wie im DOM | 34/34 | 34/34 |
| Explizit erhaltene Inline-Code-Stellen | 0/112 | 112/112 |
| Als TOC markierte Blöcke | 0 | 41 |
| Fehlende Quelltoken | 0 | 0 |
| Zusätzlich ausgegebene Inhaltstoken | 1.410 | 0 |

Die 22 Listencontainer entsprechen allen tatsächlichen `ul`/`ol`, einschließlich zweier früher nur in verschachtelten Listenmetadaten erfasster Container. Von 136 Absätzen gehören 19 zum Inhaltsverzeichnis. Die 41 TOC-Blöcke sind drei Listen, 19 Absätze und 19 Links. Mehr Blöcke bedeuten hier erhaltene Struktur, nicht mehr Quellinhalt.

Konkrete Stelle: Ein `li` enthält einen erklärenden `p`-Absatz und anschließend einen Rouge-Wrapper mit:

```python
input("What's your name? ")
print("hello, world")
```

v1 schrieb Erklärung und abgeflachte Codezeilen in den übergeordneten Listentext und gab das `<pre>` nochmals aus. v2 enthält eine Strukturreferenz für den Eintrag, einen Absatz und genau einen Codeblock mit dem originalen abschließenden Zeilenumbruch. Die tatsächliche Inline-Referenz `<a …><code>print</code></a>` bleibt Teil ihres Absatzes, besitzt eine präzise Code-Spanne und einen separaten Link; kein Unknown-Block entsteht.

Die unabhängige Prüfung vergleicht nicht nur Tokenmengen: Die **gesamte geordnete Tokenfolge** aller sichtbaren Quelltextknoten entspricht der Ausgabe ohne Link-/Mathe-/Bildreferenzprojektionen. Tokenisierung: `\w+|[^\w\s]`; ordinary HTML-Whitespace wird hierbei ignoriert, Code separat zeichengetreu verglichen. Alle 112 Inline-Code-DOMs und Werte kommen genau einmal in den primären Textspannen vor. Dies ist ein Text-/Strukturnachweis, keine semantische oder didaktische Gold-Evaluation.

Zusätzlich tatsächlich ausgeführt: Import derselben Originalbytes in einen frischen externen Workspace über `MaterialDownloader.obtain(local_file=…)`, Parsing mit `MaterialProcessor.parse(execute=True)`, Modell-Roundtrip und erneut geprüftes Resume. Neuer Receipt: `origin=local_import`, Status `completed`. Der alte HTTP-Receipt wurde nicht kopiert, umgedeutet oder geändert. Hashes des ursprünglichen Raw-HTML, Receipts und normalisierten JSON blieben unverändert.

## Offline-Tests

**129 passed, 0 failed, 0 skipped** in 54,43 s auf unverändertem finalem Code, Python 3.12.12, bestehender uv-Regressionumgebung, ohne Installation/Sync. Darin 78 Materialtests einschließlich 18 neuer Semantikfälle, drei Executor-Prüfungen, 30 Lecture-Adapter- und 18 präzise Evidence-Tests. Ruff und Formatprüfung sowie `git diff --check` erfolgreich.

```bash
CS50_TEST_PROFILE=offline uv run --offline --no-sync python -m pytest \
  tests/test_cs50_material_*.py \
  tests/test_cs50_executor.py::test_fresh_sync_import \
  tests/test_cs50_executor.py::test_success_and_verified_resume \
  tests/test_cs50_lecture_adapter.py tests/test_cs50_precise_evidence.py -q
```

Der optionale Originaltest verwendet die bereits bereitgestellten Artefakte unter `/tmp/python0-notes-artifacts/`, alternativ `CS50_NOTES_ARTIFACTS`. Fehlen sie, wird nur dieser Test übersprungen, ohne Download oder synthetischen Ersatz. Separat mit absichtlich fehlendem Original ausgeführt: **17 passed, 1 skipped** in 1,11 s. Alle übrigen neuen Semantiktests verwenden eigene kleine Inline-Fixtures. Sie prüfen insbesondere mehrteilige/nestende Listen, gleiche Einträge, Absatz-/Bild-/Codereihenfolge, Code in Links, Entities/Unicode/Quotes/Tabs, DOM und Roundtrip, TOC-Negativfall, Byte-/Block-/Bildlimits sowie v1-Receipt-/Hashkonflikte und getrenntes v2-Reprocessing.

Frühere Vorbereitungschecks: 28 Tests bestanden; der erste größere Lauf entdeckte einen Fehler im neu geschriebenen Vergleichstest (`Counter(dict)` statt `Counter(dict.keys())`). Dieser Testfehler wurde korrigiert; der oben dokumentierte Lauf wurde danach auf unverändertem Code vollständig wiederholt. Kein umfangreicher Gesamtsuitenlauf; bekannte TXT-Vertragsfehler und andere Pipelines unverändert.

## Kontrolliertes erneutes Parsing ohne Download

Erst nach Integration dieses PRs, im passenden bestehenden uv-Worker. Einen geprüften Plan mit **genau einem** freigegebenen Notes-HTML-Binding verwenden. Die Variablen zeigen auf vorhandene lokale Dateien; kein Receipt und kein altes `normalized.v1.json` werden kopiert oder bearbeitet:

```bash
# REVIEWED_ONE_NOTES_PLAN: vorhandener, geprüfter Plan mit genau einem Notes-Binding.
# ORIGINAL_RAW_HTML: bereits gespeichertes raw/source aus dem bisherigen Workspace.
NEW_WORKSPACE=$(mktemp -d /tmp/cs50-notes-html-v2-XXXXXX)
uv run --offline --no-sync python -m scripts.cs50_materials import-local \
  --plan "$REVIEWED_ONE_NOTES_PLAN" --workspace "$NEW_WORKSPACE" \
  --course cs50_python --section 0 --local-file "$ORIGINAL_RAW_HTML" --execute-import
uv run --offline --no-sync python -m scripts.cs50_materials parse \
  --plan "$REVIEWED_ONE_NOTES_PLAN" --workspace "$NEW_WORKSPACE" \
  --course cs50_python --section 0 --execute-parse
uv run --offline --no-sync python -m scripts.cs50_materials status \
  --plan "$REVIEWED_ONE_NOTES_PLAN" --workspace "$NEW_WORKSPACE" \
  --course cs50_python --section 0
```

Die ausgewählte Parse-Config muss im neuen Receipt `name=html, version=2` sein. Die ursprüngliche Raw-SHA vergleichen. Bei Identitäts-, Hash- oder Configkonflikten abbrechen; keine Ausweichdateisuche, kein Downloadfallback und kein Overwrite. Siehe [Betriebsanleitung](../operations/material_ingestion.md).

## Grenzen

HTML-Whitespace außerhalb von Code wird normalisiert; rohe HTML-Bytepositionen werden nicht behauptet. DOM-Pfade beziehen sich auf den BeautifulSoup-Parsebaum, nicht auf einen Browser mit JavaScript. Fragment-Indizes unterscheiden gesplittete Läufe, sind keine Zeichenoffsets im Raw-HTML.

Links bleiben absichtlich zusätzlich zum Absatz referenziert. Vor einer späteren Textaggregation müssen Verbraucher Referenzprojektionen bewusst behandeln; das bestehende read-only Materialmapping wurde nicht umgebaut. TOC-Inhalt wird markiert, nicht automatisch von künftiger Knowledge-Verarbeitung ausgeschlossen.

Andere TOC-Konventionen und komplexe Tabellen bleiben separat zu evaluieren; die bisherige Tabellenprojektion ist unverändert. Keine neue semantische Math-/Layout-Erkennung, kein Browserrendering. HTML hat weiterhin Byte-/Block-/Bildgrenzen, aber keinen neuen CPU-/RAM-Subprozessvertrag. Es wurden keine Knowledge-/Discovery-/Selection- oder Downloaderalgorithmen geändert.
