# C13 – Visual Assets & Document Provenance

C13 ergänzt eine deterministische, lesende Inventur für normalisierte Materialien.
Sie interpretiert keine Bilder und ändert weder Raw-Dateien noch normalisierte
Artefakte, Parserkonfigurationen oder Knowledge-Objekte. Keine neue Dependency.
Grundlage ist `master` bei `09f7384`; C10/C11/C12-Ausgaben sind nicht erforderlich.

## Vorhandene Architektur: implementiert und tatsächlich geprüft

| Komponente | Implementierter Vertrag | Verwendung/Nachweis in C13 |
| --- | --- | --- |
| `tools_materials/parse_html.py` | HTML-v2, stabile DOM-Pfade, `image_reference`-Blöcke und `ImageArtifact`; relative/externe URLs werden referenziert, unterstützte Inline-Rasterdaten als Blobs zurückgegeben; Caption aus Figure/Alt | Unverändert verwendet, um synthetische NormalizedDocuments zu erstellen; `dom_path` für zusätzliche Source-Beobachtungen wiederverwendet |
| `tools_materials/parse_pdf.py`, `pdf_worker.py` | Begrenzter PyMuPDF-Subprozess, Text-/Code-/Math-Blöcke, Rasterbilder mit Seiten-/BBox-Position und Bildbytes; keine Vektorprojektion im Materialmodell | Unverändert verwendet; `run_worker` für den zusätzlichen begrenzten Beobachtungsschritt wiederverwendet |
| `model_materials/materials.py` | `MaterialResource`, `NormalizedDocument`, `Location`, `ImageArtifact`, `ArtifactReceipt`, `MaterialPlan`; Resource-/Material-/Dokument-/Block-IDs | Bestehende Modelle bleiben unverändert; der neue Report verwendet diese direkt |
| `tools_materials/processing.py` und `storage.py` | Gehashte Raw-/Normalized-/Image-Artefakte und Receipts; Bilder relativ zum NormalizedDocument-Verzeichnis; atomare exklusive Veröffentlichung | Dateien nur lesen; `safe_path` und `publish_bytes` für Pfadprüfung/Reportpublikation wiederverwenden |
| Legacy `model_parsing/pdf_extractor.py` | `_extract_images` schreibt PNGs über Pixmaps; `_extract_drawings` liest `get_drawings()` und projiziert DrawingMeta | Quellcode untersucht; kein Import/Aufruf, keine zweite Extraktionspipeline |
| Legacy `model_parsing/base_classes_parsing.py` | `ImageMeta`, `DrawingMeta`, Elementmodelle | Anderer Legacy-Vertrag; Materialmodelle reichen hier aus |
| `run_knowledge_improvement.py`, `tools_knowledge/rebuild_knowledge.py` | Zeitbasierte Video-/Frame-Batches; lokale Docling-Analyse und optional OpenAI-Bildanalyse; Formelverifikation; `VisualAnalysisDocument` mit lokalen/API-Ergebnissen | Nur Quellcode untersucht; diese Module werden nicht importiert, initialisiert oder ausgeführt |
| `tools_knowledge/postprocess_visual.py` | Zusammenführung visueller Evidence-/Knowledge-Ergebnisse | Keine Ausführung; keine neuen semantischen Evidence-/Knowledge-Objekte erzeugt |

Tatsächlich vorliegende, neu überprüfte Ausgaben sind ausschließlich die
synthetischen HTML-/PDF-Beispielreports und die während der Tests temporär
angelegten Parserartefakte. Im untersuchten Git-Stand wurden keine versionierten
realen VisualAnalysis-Ergebnisdateien gefunden; nicht versionierte produktive
Daten wurden nicht untersucht. Das Vorhandensein der Legacy-Funktionen belegt
keinen erfolgreichen realen Visual-Enrichment-Lauf.

Noch nicht implementiert ist ein Dokument-/Seitenadapter zu den bisherigen
zeitbasierten `VisualAnalysisBatch`-/Frame-Verträgen. C13 erstellt dafür
referenzierbare Inventarobjekte, keinen neuen Enrichment- oder PDF-Parser.

## Ablauf und Eingaben

`NormalizedDocument → Bildreferenzen/Artefaktprüfung → optionale Raw-Beobachtungen
→ Provenienz-/Konsistenzbefunde → JSON/Markdown`

Einstieg: `tools_materials.visual_inventory.inventory(...)`:

- `normalized_path`, `input_root`: explizite lokale Datei und erlaubte Lesewurzel.
  JSON muss Schema-/Binding-Version 1 und eine Parser-Version explizit enthalten;
  doppelte Schlüssel, NaN/Infinity, überlaufende Fließkommazahlen und ungültige
  bestehende Modellverträge werden abgewiesen.
- `raw_path`: optionales Original-HTML/PDF. Vor jeder Analyse muss dessen
  Byte-SHA-256 zum normalisierten Dokument passen. Ohne Raw bleibt `raw_scan`
  ausdrücklich `not_supplied`; fehlende `<img src>`, SVG und Vektoren können
  dann nicht aus dem normalisierten Dokument rekonstruiert werden.
- `artifact_root`: standardmäßig Elternverzeichnis der normalisierten Datei.
  Ausschließlich bereits deklarierte `ImageArtifact.artifact_path` werden darunter
  geprüft. Relative HTML-URLs werden niemals als lokale Dateipfade interpretiert.
- `receipt_path`: optionaler bestehender `ArtifactReceipt`. Geprüft werden
  Completed-Status, Binding, Parser, Raw-/Normalized-Hashes, Image-Manifest und
  der relativ zu `input_root` gespeicherte Normalized-Pfad. Das Receipt wird
  weder übernommen noch verändert.
- `plan_path`: optionaler bestehender `MaterialPlan`. Dessen vorhandene
  Graphvalidierung prüft Course-/Section-/Lecture-Verknüpfungen; das vollständige
  Materialbinding muss genau zum Dokument passen. `binding_verification` lautet
  `plan_verified`, andernfalls `declared` ohne Plan bzw. `conflict` bei Fehlern.
  Eine aus dem Dokument kopierte Lecture-Liste gilt nicht als unabhängiger Beleg.
- `limits`: versionierbare `InventoryLimits`, siehe unten. Alle Quellen,
  Receipts, Pläne und Artefakte liegen unter der expliziten Lesewurzel.

## Reportvertrag v1

[`VisualInventory`](../src/model_materials/visual_inventory.py) ist ein separater
Report mit `schema_version=1`, `inventory_version=visual_inventory_v1`.
Dokument-ID, vollständiges ursprüngliches `MaterialResource`-Binding,
Parserkonfiguration, deklarierter/ggf. beobachteter Raw-SHA, Normalized-Bytehash,
Eingabepfade, Limits, Bindingprüfung und Scanstatus bilden die gemeinsame
Provenienz. Damit bleiben Course, Sections, Lectures, Resource/Source, Material,
Original-URL und Discovery-Provenienz ohne neue parallele Geschäftsmodelle erhalten.

Jedes `VisualAsset` hat:

- eine stabile, positionsbezogene `asset_id` im Namespace `visual_asset`,
  Dokument-/Material-ID und bestehende `Location` mit DOM bzw. Seite/BBox;
- `asset_type`: `raster_image`, `vector_graphics_candidate`, `inline_svg`,
  `external_image_reference` oder `unknown_visual`;
- Originalreferenz, ggf. ursprüngliches `ImageArtifact`, originale Block-IDs
  und bestätigte Alias-Bildreferenzen; Caption/Context bleiben erhalten;
- getrennte Extraktions-, Artefakt- und Reviewstatus sowie lokale beobachtete
  SHA-256 und technische Warnungen.

IDs binden das bestehende `document_id` und die ursprüngliche Bildidentität bzw.
DOM-/PDF-Vorkommensposition. Für Vektorkandidaten sind Seite und Pfadindizes
maßgeblich. Identische Bytes an unterschiedlichen Positionen bleiben getrennte
Assets. Veränderte Raw-Bytes/Parserkonfiguration ändern die Dokumentidentität;
andere lokale Artefaktverfügbarkeit ändert nicht die Asset-IDs. Die bestehende
Dokumentidentität bindet Lecture-Listen nicht zusätzlich; deren Änderungen
werden im Binding, optionalen Planvergleich und Reporthash sichtbar.

**Referenz ist nicht Bildbytes:** `image.sha256` ist der unveränderte deklarierte
Hash des Originalmodells. `observed_sha256` entsteht ausschließlich aus wirklich
lokal gelesenen Artefaktbytes. `available` erfordert einen passenden deklarierten
Hash und ein sicher lesbares Artefakt. Das beweist Bytekonsistenz, nicht einen
korrekten Bildinhalt oder ein decodierbares Format.

| Feld | Werte/Bedeutung |
| --- | --- |
| `extraction_status` | `available`, `reference_only`, `unsupported`, `uncertain` |
| `artifact_status` | `verified`, `missing`, `not_declared`, `unverified`, `hash_mismatch`, `unsafe`, `limit_exceeded` |
| `review_status` | `requires_visual_review` oder bei technischem Konflikt `uncertain`; niemals „semantisch korrekt“ |
| `raw_scan` | `complete`, `not_supplied`, `failed`, `unsupported`; `complete` bezeichnet nur den unterstützten technischen Beobachtungsumfang |

Ohne automatische Interpretation bleibt jedes visuelle Asset ein möglicher
Prüffall, auch eine möglicherweise dekorative Linie. Fehlende Bildbytes bleiben
sichtbare Referenzen. Ungültige/unsichere Quellen werden als `unsupported`
markiert; Skripte, SVG-Links und Remote-URLs werden nicht ausgeführt/geladen.
Fehler sind zusätzlich als Severity `error` sichtbar. Ein Scanabbruch behauptet
keine vollständige Vektorerfassung und entfernt keine normalisierten Referenzen.

`counts` enthält Assets, lokal verifizierte Asset-Vorkommen, eindeutige
verifizierte Artefaktpfade, `reference_only`, mögliche Prüffälle,
Bestätigungsaliase und die Anzahl Warnungs-/Fehlerbefunde. `available_artifacts`
zählt Vorkommen, `unique_artifacts` zählt Pfade: zwei Positionen desselben
Bildartefakts ergeben zwei verfügbare Assets und ein Artefakt. `by_type` und
`by_page` zählen Assets; HTML/positionslose Einträge stehen unter
`dom_or_unknown`. Status `unsupported`/`uncertain` wird nicht fälschlich als
`reference_only` mitgezählt. Mehrere Warnungen können denselben Kandidaten betreffen.

JSON: UTF-8, sortierte Schlüssel, kompakte Separatoren, ein abschließender LF,
keine Laufzeitstempel. `report_sha256` ist der SHA-256 dieser Darstellung **ohne**
das Feld `report_sha256`. Gleiche Inputs/Pfade/Artefaktzustände/Limits und gleiche
Backendversion erzeugen denselben Report. Der Raw-Worker dokumentiert seine
BeautifulSoup-/PyMuPDF-Version in `scan_backend`; keine versionsübergreifende
Gleichheit nativer Extraktionsergebnisse wird vorausgesetzt.

## PDF: Pfade, Geometrie und bestätigte Aliase

Der zusätzliche begrenzte Worker liest `page.get_image_info(hashes=False,
xrefs=False)` und `page.get_drawings()`. Er extrahiert keine neuen Rasterbytes,
erstellt keine Pixmaps, rendert nicht und ruft keine OCR auf. Native
PyMuPDF-Seitenkoordinaten bleiben unverändert: Punkte, unrotierter Seitenraum;
Seitenrotation und unrotierte Grenzen werden im Context mitgeführt. Linien mit
null Breite/Höhe sind gültige Geometrie. Überstehende BBoxes werden gewarnt und
nicht weggeclippt.

Vektorpfade werden über überlappende/benachbarte BBoxes als Zusammenhangskomponenten
gruppiert; Standardabstand zwei Punkte. Der Report bewahrt Pfadindizes,
Pfadanzahl, Zeichenoperationsanzahl und Gruppen-BBox. Seitenfüllende BBoxes
(ab 80 % Seitenfläche) bleiben separat, damit ein möglicher Hintergrund nicht
alle unabhängigen Zeichnungen verbindet. Rechtecke, Einzelpfade und auf anderen
Seiten wiederkehrende geometrische Signaturen werden nur als technische Signale
markiert. Es wird nichts gelöscht. Ein mehrpfadiger Kandidat beweist weder ein
Diagramm noch mathematische Relevanz. Bounding-Box-Nähe ist keine Pfadtopologie.

Die synthetische PDF-Fixture weist einen bestehenden PDF-v2-Sonderfall nach:
`get_images(full=True)` kann denselben XRef mehrfach listen; für jeden Eintrag
liefert `get_image_rects` erneut sämtliche Positionen. Daraus entstehen vier
normalisierte Referenzen für zwei tatsächliche Bildvorkommen. C13 ändert die
kanonische Normalisierung nicht. Nur wenn die Raw-Inventur alle tatsächlichen
Bildvorkommen an dieser Position bereits zugeordnet hat und ein vollständiger
normalisierter Bilddatensatz bis auf `image_id` identisch ist, wird der weitere
Datensatz als Alias bewahrt. Alle ursprünglichen Bild- und Block-IDs bleiben
referenzierbar. Tatsächlich doppelt gezeichnete Bilder mit gleicher BBox bleiben
mehrere Vorkommen; ein eigener Regressionstest prüft das.

Ohne erfolgreiche Raw-Prüfung wird diese Identität nicht behauptet: Dann werden
normalisierte Referenzen einzeln inventarisiert, und die fehlende Raw-Abdeckung
ist ausdrücklich markiert. Für eine spätere Aggregation physischer PDF-Assets
ist daher ein erfolgreicher Raw-Scan erforderlich.

## HTML: ergänzende Beobachtungen

Bestehende HTML-v2-Bildartefakte bleiben die Grundlage. Die Raw-Beobachtung
scannt zusätzlich `<img>`, äußere Inline-`<svg>`, Image-`object`/`embed` und
`picture/source`, einschließlich leerer Quellen. SVG-Unterelemente werden als
Referenzen am äußeren SVG bewahrt; kein SVG wird gerendert oder als neue Datei
publiziert. `figure/figcaption` und Alt-Text dienen nur als Quellenkontext.

Relative und HTTP(S)-Referenzen bleiben Originalreferenzen; URL-Integrität wird
gegen das bestehende normalisierte Bildmodell geprüft. `file:`, `javascript:`,
`blob:`, Credentials, Control-Zeichen und andere unsichere Referenzen werden
nicht dereferenziert. Inline-Daten werden in der Inventur nicht decodiert;
vorhandene normalisierte Inline-Artefakte werden wie andere lokale Dateien
geprüft. Nicht unterstützte Kodierung/`srcset`-Auswahl bleiben sichtbar.

Die Source-Beobachtung umfasst den Quell-DOM, nicht ausschließlich den vom
Parser gewählten Main-Bereich. Dadurch können auch zusätzliche Layout-Bilder
sichtbar werden. Inhalte in `template`/`noscript`, CSS-Hintergründe, Canvas,
JavaScript-generierte Elemente, berechnetes Layout und unspezifizierte
Browserauswahl sind nicht erfasst. HTML liefert ohne Rendering keine verlässliche
Pixel-BBox; DOM-Pfade werden nicht zu erfundenen Koordinaten umgerechnet.
Zusätzliche Raw-Caption-Vorschauen sind auf 1.000 Zeichen begrenzt; der Original-DOM
bleibt über Raw-Hash und Position referenzierbar.

## Ressourcen, sichere Dateiverarbeitung und CLI

Standardgrenzen: 16 MiB je Quelldatei und für die Summe eindeutig gelesener
Bildartefakte, 100 PDF-Seiten, 2.000 Assets, 4.000 Vektorpfade,
20.000 Zeichenoperationen, 20 Sekunden Worker-Laufzeit und 1.024 MiB
Worker-Adressraum. Harte Obergrenzen stehen im Pydantic-Modell. Der Worker hat
zusätzlich CPU-/Dateigrößenlimits; `run_worker` beendet bei Timeout die gesamte
Prozessgruppe. Paarweise Gruppierung ist begrenzt, aber im schlechtesten Fall
quadratisch. Bei überschrittenen Grenzen entsteht ein sichtbarer Scanfehler. Die Assetgrenze
wird auch vorab auf normalisierte Referenzen und Raw-Beobachtungen angewendet;
bestätigte Aliase können deren Zahl später reduzieren.

Die Pixelgrenze (standardmäßig 40 Millionen) markiert übergroße aus PDF-Metadaten
bekannte Bilder. Sie ist keine Decoderprüfung; es werden keine Pixelraster angefordert.
Die native PDF-Metadatenanalyse läuft im begrenzten Worker. HTML-/Bilddateien werden lediglich bytebegrenzt gelesen
und gehasht. Jede spätere Verarbeitung benötigt eigene Decoder-/Pixelgrenzen.
Symlinks, Traversal und Pfade außerhalb der expliziten Wurzel werden abgewiesen;
nur reguläre Dateien sind erlaubt. Schutz gegen gleichzeitig bösartig
ausgetauschte Elternverzeichnisse wird nicht behauptet. Die Inventur benötigt
keinen Lock und verändert keine Quellartefakte.

```bash
python -m scripts.cs50_visual_inventory \
  --input-root /tmp/synthetic-material-workspace \
  --normalized /tmp/synthetic-material-workspace/normalized.v1.json \
  --raw /tmp/synthetic-material-workspace/source.pdf \
  --json-report /tmp/new-visual-inventory.json \
  --markdown-report /tmp/new-visual-inventory.md
```

Optional `--artifact-root`, `--receipt`, `--plan` und `--limits` (lokale
InventoryLimits-JSON). Ohne Reportpfade gehen JSON nach stdout und die
Markdown-Zusammenfassung nach stderr. Markdown enthält höchstens 50 Assetzeilen
und 50 Befunde; JSON bleibt vollständig. Keine Quelldaten werden als aktives
HTML in Markdown ausgegeben.

Reportpfade müssen unterschiedlich, neu und außerhalb der Lesewurzel sein;
Elternordner müssen existieren. Beide Pfade werden vorab geprüft. Jeder Report
wird über die bestehende exklusive atomare Publikation geschrieben. Es gibt
keinen Overwrite-/Force-Schalter und keine automatische Extraktion oder Downloads.
Die beiden Dateien bilden keine atomare gemeinsame Transaktion: Bei einem
Abbruch nach dem ersten Report bleibt dieser bestehen; mit neuen Reportnamen
wiederholen. Keine automatische Löschung oder Reparatur.

Exitcodes: 0 bei Inventur ohne technische Fehler (Warnungen erlaubt), 1 bei
berichteten Scan-/Provenienz-/Artefaktfehlern, 2 bei ungültigen Eingaben,
Pfad-/Schema-/Reportpublikationsfehlern. Eine fehlende Raw-Datei als expliziter
Input ist ein berichteter Scanfehler; keine Raw-Option ist ein begrenzter,
entsprechend gewarnter Normalized-only-Lauf.

## Beispiele und Offline-Nachweis

Die [Fixture-Beschreibung](../tests/fixtures/visual_inventory/README.md) und der
[Generator](../tests/fixtures/visual_inventory/build_fixture.py) dokumentieren
alle synthetischen Quellen. Die genauen PDF-Bytes sind offline als Base64
versioniert. Keine Kursdaten wurden heruntergeladen oder kopiert.

- [HTML JSON](examples/visual_inventory/html.inventory.v1.json) und
  [HTML Markdown](examples/visual_inventory/html.inventory.v1.md): zwölf
  Positionen, davon zwei verfügbare Rasterbilder desselben Artefakts, fünf
  externe Referenzen, ein Inline-SVG und vier unklare/fehlende Quellen.
- [PDF JSON](examples/visual_inventory/pdf.inventory.v1.json) und
  [PDF Markdown](examples/visual_inventory/pdf.inventory.v1.md): acht Assets,
  davon zwei Rastervorkommen und sechs Vektorkandidaten; zwei bestätigte Aliase.
  Alle acht ursprünglichen Zeichenpfade bleiben in den Gruppen referenzierbar.

Die Beispielreports stammen aus tatsächlichen Offline-Läufen. Ausschließlich
Eingabepfade wurden für die Ablage auf `synthetic-inputs/...` umgestellt und der
Reporthash anschließend neu berechnet. Tests prüfen die Reproduzierbarkeit mit
der aufgezeichneten Backendversion. Kein Report ist eine semantische Goldbewertung.

Befehle und Ergebnisse stehen in [Testresultate](visual_inventory_test_results.md).

## Nächster Integrationsschritt und verbleibende Grenzen

Ein nachfolgender Adapter sollte Inventar-ID, Dokument-ID, Raw-/Normalized-Hash,
Position und originale Bild-/Block-IDs als Evidence-Schlüssel übernehmen. Für
automatische Weitergabe sind `raw_scan=complete`, keine technischen Fehler,
ein verifiziertes Kursbinding und ggf. vorhandene Artefakte explizit zu verlangen.
Die C10-Qualitätsprüfung kann diesen Report später als zusätzliche Referenz
konsumieren; sie ist hier keine Laufzeitabhängigkeit.

Für Dokumentseiten passen die bisherigen Videozeit-/Frame-Verträge noch nicht.
Ein gesondert versionierter Adapter muss PDF-Seite/BBox bzw. HTML-DOM als
Dokumentprovenienz erhalten und darf keine Videozeitstempel erfinden. Wenn für
Vektoren/SVG später Bildcrops notwendig sind, müssen diese ausdrücklich,
ressourcenbegrenzt und in einem eigenen Artefaktvertrag erzeugt werden. Erst
danach kann bestehende lokale Visual Analysis gezielt angebunden werden.

Es verbleiben bewusst Grenzen: keine OCR, kein Beweis fachlicher Bildrelevanz,
keine mathematische/semantische Diagrammprüfung, keine vollständige Browser-
oder PDF-Renderingabdeckung (z. B. Annotationen/Clipping-Semantik). Hashes prüfen
Konsistenz, nicht die Authentizität einer Quelle. Ein lesender Lauf sieht einen
Dateisystem-Snapshot ohne Änderungssperre. Es erfolgt keine produktive
Indizierung, kein LLM-Aufruf und keine automatische Knowledge-Änderung.
