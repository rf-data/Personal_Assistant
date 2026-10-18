# C23-06: Korpus-, Gold- und Reviewvertrag v1

Stand 18.10.2026. [Abnahme und Befehle](c23_real_material_evaluation.md),
[Inventar](c23_corpus_inventory.md),
[versioniertes Manifest](c23_06/corpus_manifest.v1.json),
[Reviewaufträge](c23_06/gold_references.v1.json).

## Architektur und vorhandene Verträge

`scripts.cs50_material_evaluation` orchestriert ausschließlich explizite lokale
Inputs. Die zwei Evaluationsverträge `CorpusManifest` und `GoldDataset` stehen
in `src/model_evaluation/material_evaluation.py`; Ausführung in
`src/tools_evaluation/evaluate_materials.py`. Es gibt keine neue Source-, Parsed-,
Lecture- oder Knowledge-Pipeline und keine Änderung an deren Modellen.

| Wiederverwendeter Bestand | Zweck und Grenze |
| --- | --- |
| `content_store.inventory.InventorySelection/Request/Result`, `inventory` | Vollständige Material-/SRT-Bundles am bestehenden B-Gate prüfen; optional bestehender Store nur read-only |
| B `_capture` / `_verify_frozen` | Explizite Dateien sicher erfassen, Graph/Hashes/Receipt/Revision und vorhandenes C10-Gate prüfen; ein zweiter Snapshot liefert die vorhandenen ContentBlocks zur Evaluation. Alle Rollenhashes müssen mit dem ersten Snapshot übereinstimmen |
| `ContentLocator`, bestehende SourceVersion und ParserConfiguration | Originale Seiten-/DOM-/Zeilen-/Zeitreferenzen, Source-Version und Konfigurationsidentität erhalten; keine IDs aus Dateinamen oder Goldtext erfinden |
| C10 / Lecture-Handoff | Technische Befunde sowie primäre, strukturelle und alternative Ansichten übernehmen; kein Text aus TOC/Links/Codeviews doppelt aggregieren |
| C11 `FormulaCase`, `evaluate_case` | Nur bestätigte, unabhängig deklarierte Formelpaare bewerten. Backend `none`: exakte/normalisierte/strukturelle Notation, keine neue Symbolik oder Rekonstruktion |
| C13 `visual_inventory.inventory` | Vorhandene technische Bild-/Seiteninventur separat nutzbar und mit eigener HTML-Testabnahme geprüft. Der Korpusrunner startet keinen automatischen Raw-Visualscan; `visual=null` bedeutet nicht ausgeführt |
| C23 Store-/Read-Verträge | Bestehende Payload-/Locator-/ACL-/HTTPtests regressieren. Der Runner publiziert nichts und behauptet keinen Real-HTTP-Roundtrip |

Die B-Gates können zur Quellenprüfung den bestehenden SRT-Importer erneut
verwenden. Das ist keine neue Transkriptionspipeline. Reale Rohsnapshots des
aktuellen Korpus erhalten **keine** künstlichen Receipts oder SourceVersions.

## CorpusManifest

Pflicht: `schema_version=1`, `dataset_version`, 1–128 eindeutig benannte `entries`.
Pro Eintrag: `entry_id`, `origin` (`real/synthetic/unknown`), Course-ID, Format
(`html/pdf/code/srt/txt`), `root_key`, `permission` und nachvollziehbare
`permission_reference`. Resource-/Source-ID, Material-ID, Sections/Lectures und
Original-URL bleiben optional, solange nicht belegt. `null` ist kein erfundener ID.

Für unvollständige Bestände nennt `artifacts` nur ausdrücklich ausgewählte relative
Raw-/Parsed-/Receipt-/Qualitydateien unter einer expliziten CLI-Wurzel. Keine
Verzeichnissuche, URLauflösung oder Pfadkorrektur. Bekannter Raw-SHA kann zusätzlich
deklariert werden. `inventory_only` erlaubt Beobachtung/Hashes, keine Goldbewertung;
`denied` oder unbekannte Herkunft erlauben keine Inhaltsreads. Außerhalb des
Actorscopes werden keine Bytes gelesen.

Ein vollständiges Bundle verwendet stattdessen die bestehende `InventorySelection`;
parallele `artifacts` sind dann verboten. Source/Course/Format, optionale Metadaten,
Original-URL und Herkunft müssen mit dem B-Gate übereinstimmen. Die Bundlewurzel
muss exakt dem zugeordneten `root_key` entsprechen. Explizite Plan-/Revisionsdateien
außerhalb dieser Wurzel bleiben gemäß vorhandenem B-Vertrag zulässig, andere
Sourceartefakte müssen innerhalb liegen. Die CLI schützt auch diese Einzelinputs
vor Reportüberlagerung.

`evaluation` ist eine ausdrückliche lokale Scopeerklärung, keine neue HTTProlle
oder Umgehung von Principal/Ownership/Course/ACL. Der aktuelle reale Korpus besitzt
ausdrücklich **nur `inventory_only`**. Ein Konfigurationsfeld erteilt keine D06/D07-
Freigabe und ersetzt keine rechtliche oder fachliche Prüfung.

Klassifikation: `verified_bundle`, `synthetic_fixture`, `real_incomplete_bundle`,
`unknown_origin`, `permission_restricted`. Synthetische vollständige Bundles bleiben
als synthetisch sichtbar, zusätzlich `binding_verified=true`. Ohne Store ist
Publikation `not_checked`, nicht „nicht vorhanden“. Unausgewählte Artefakte sind
`available=null`, ausdrücklich fehlende Dateien `false`; nur beobachtete Bytes
bekommen Hash und Größe.

## GoldDataset und GoldReference

`schema_version=1`, gleiche `dataset_version`, 0–2.000 eindeutige Referenzen.
Es gibt **keine automatische Goldgenerierung oder Statuspromotion**.
Das JSON-Schema wird aus dem tatsächlichen Pydanticmodell abgeleitet:
[gold_schema.v1.json](c23_06/gold_schema.v1.json).

| Feld | Vertrag |
| --- | --- |
| `gold_id`, `entry_id` | Eindeutige Annotation und existierender Korpuseintrag |
| `source_id`, `source_version_id`, `original_sha256` | Exakte Originalidentität; Source-/Versions-ID dürfen nur bei Pending unbekannt sein. Hash muss beim Vergleich zum verifizierten Bundle passen |
| `source_reference`, `created_date` | Originalfundstelle bzw. bei Pending ausdrücklich noch unannotierter Dokumentumfang und Erstellungsdatum |
| `target_pointer` | Vorhandener Payloadpointer eines ContentBlocks, z. B. `/blocks/3` oder `/segments/0`. Pending erlaubt `null`; bestätigtes Gold verlangt einen konkreten Pointer |
| `dimension` | `text`, `structure`, `code`, `formula`, `image`, `table`, `transcript`, `locator` |
| `expected_content` | Unabhängig annotierter vollständiger Block-/Cuetext bzw. Formelausdruck; keine Ableitung aus Vorhersagen |
| `expected_structure` | Nichtleere Auswahl erwarteter Blockfelder; Feldwerte, auch Zeilen-/Spaltenlisten, werden exakt verglichen. `type` bezeichnet den ursprünglichen Blocktyp, z. B. `math` |
| `expected_locator` | Bestehendes `ContentLocator`; dessen Rawhash muss zum Goldhash passen. Vergleich des vollständigen expliziten Locators, keine tolerierte Seiten-/Zeitverschiebung |
| `expected_occurrences` | Optional unabhängig annotierte Häufigkeit des exakten Texts unter primären ContentBlocks; braucht `expected_content` |
| `reference_status` | `pending_review`, `confirmed`, `rejected` |
| `method` | `independent_source_annotation`, `parser_preannotation`, `synthetic_reference` |
| `reviewer`, `review_reference`, `review_date`, `notes` | Nachvollziehbarer manueller Reviewbeleg, Datum, Unsicherheiten; aktuell keine realen Reviewer behauptet |

`confirmed` verlangt Source-ID, SourceVersion, konkreten Pointer, mindestens einen
erwarteten Inhalt/Struktur/Locator und sämtliche Reviewfelder. Parser-Vorannotation
bleibt Pending. Für reale bestätigte Referenzen ist ausschließlich
`independent_source_annotation` zulässig; synthetische Referenzen können nicht
durch Änderung von `origin` zu Realgold werden. Ein Reviewbeleg ist eine lokale
Deklaration, keine automatische Authentifizierung oder fachliche Zertifizierung.

Die fünf versionierten Pendingeinträge sind **Reviewaufträge**, keine bereits
annotierten Goldspans: keine erwarteten Inhalte, keine SourceVersion, kein
Zielpointer, kein Reviewer und kein bestätigtes Reviewdatum. Die beiden Assignment-
Snapshots besitzen zudem noch keine im vorhandenen Graphen belegte Resource-ID.

## Metriken und Befunde

Alle Gruppen sind strikt getrennt nach Herkunft (`real/synthetic`), Format und
Dimension; `dataset_version` und Evaluatormethode stehen im Reportkopf.
Jede Metrik enthält `numerator`, `denominator`, `rate`; bei Nenner null ist
`rate=null`. Kein globaler Qualitätsscore.

- `exact_content`: identische Zeichenfolge, einschließlich Unicode, Whitespace,
  Einrückung, Quotes und Zeilenumbrüchen.
- `normalized_text`: zusätzliche reine Textmetrik mit NFC und zusammengefassten
  Whitespacefolgen. Sie ersetzt Exact Match nicht; **kein** Whitespace-/Unicode-
  Folding für Code oder Formeln.
- `structure`: exakte Übereinstimmung der ausdrücklich annotierten Felder.
- `locator`: mindestens ein vorhandener Original-ContentLocator stimmt vollständig.
- `occurrences`: erwartete Anzahl exakter Texte in primären Blöcken; alternative
  Ansichten/Referenzprojektionen zählen nicht mit. Wiederholter Text ist ohne
  annotierte Häufigkeit **kein automatisch behaupteter Duplikationsfehler**.
- `formula_correct`: unveränderter C11-Status; unsupported/undetermined bleibt ohne
  mathematische Entscheidung. Exakter Formeltext beweist keine unterstützte Syntax.

Nenner sind ausschließlich bestätigte, gebundene Referenzen, für die die jeweilige
Metrik tatsächlich ausgeführt wurde. Pending/Rejected, falsche SourceVersion und
fehlende Rechte/Bundles zählen nicht hinein. `not_evaluable` und `undetermined`
werden separat gezählt. Ein Fall kann Exact Match liefern und bei C11 trotzdem
nicht entscheidbar sein. `gold_counts` trennt Herkunft und Reviewstatus;
`missing_entries` zählt Einträge ohne jeden Reviewauftrag,
`entries_without_confirmed` alle Einträge ohne bestätigte Referenz.

Keine Recall-/Precision-/Duplikationsrate über ganze Dokumente: Dafür fehlt eine
unabhängige vollständige Annotation aller relevanten Elemente samt klarer Region.
Der Runner vergleicht explizite Block-/Cuefenster, kein heuristisches Matching.
Dieselben Goldanker lassen später separate Detektionsmetriken zu; derzeit keine
Prozentzahl über unannotierte Dokumente oder leere Goldgruppen.

Befunde gruppieren Beobachtungen als `parsing_candidate`,
`source_binding_provenance`, `persistence_projection`, `data_permission` und
`evaluation_gap`. Ein Content-/Locatormismatch ist vor manueller Ursachenprüfung
kein automatisch bewiesener neuer Parserfehler. Ergebnisse enthalten IDs, Scores
und feste Codes, keine vollständigen erwarteten/vorhergesagten Texte.

## Reproduktion und Grenzen

CLI und konkrete Befehle: [Abnahmebericht](c23_real_material_evaluation.md).
Ausgaben: gehashter `evaluation_report.v1.json`, `corpus_inventory.v1.json`, kurze
`summary.md` und zuletzt ein Hashmanifest. Ein neues Verzeichnis außerhalb aller
Inputs ist Pflicht; kein Force/Overwrite. Abgebrochene Ausgaben ohne abschließendes
Manifest sind kein abgeschlossener Report. Rootpfade werden nicht in den Report
aufgenommen; ein zukünftiges Manifest mit privaten absoluten Bundlepfaden bleibt
ein privater Operationsinput und darf nicht ungeprüft in Git gelangen.
`corpus_sha256` und `gold_sha256` binden die kanonischen validierten v1-Modelle
einschließlich Defaults; sie sind keine Behauptung unveränderter Whitespacebytes
der Eingabe-JSONs. Rawhashes und das Output-Dateimanifest binden dagegen exakte Bytes.

Vorhandene Größen-/JSON-/Symlinkchecks und Gate-Snapshots werden wiederverwendet.
Maximal 128 Einträge/2.000 Referenzen, 100.000 Zeichen pro erwarteter Textreferenz,
128 MiB kumuliert beobachtete Artefaktbytes. Keine Downloads, Codeausführung,
LLM-/Embeddingaufrufe, Storewrites, Recovery, Migration oder automatische
Produktions-/Formatfreigabe. Hashroundtrip und HTTPprojektion sind technische
Eigenschaften; die fachliche Realabnahme bleibt ein separater manueller Schritt.
