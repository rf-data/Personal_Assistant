# C10: Offline Material Quality Gate und Lecture-Handoff v1/v2

Stand: 22.10.2026. Ursprünglicher Vertrag: `master` / `90f4ade` (PR #60).

C26-A erweitert den vorhandenen Adapter um versionierte Link- und Listenmetadaten.
Details, Kompatibilität und Grenzen: [HTML-Aggregation v2](html_aggregation_v2.md).

## Tatsächliche Übergabekette

| Stufe | Vorhandener Vertrag / Funktion | Bedeutung |
|---|---|---|
| Lokale Discovery | `CourseDiscovery`, `SectionDiscovery`, `ResourceCandidate`, `Provenance`; `discover_fixture_courses` | Bestehende Ressourcen-, Kurs- und Abschnittsidentitäten samt Fundstellen |
| Geprüfter Materialplan | `MaterialPlan`, `MaterialResource`; `make_plan`, `plan.select` | Lecture-IDs sind die logischen `lecture_video.resource_id` desselben Abschnitts; Varianten bleiben getrennte Materialbindungen |
| Lokales Artefakt | `MaterialDownloader.obtain(local_file=…)`, `ArtifactReceipt` | Raw-Bytes und deren SHA-256; Quelle und Importherkunft bleiben erhalten |
| Normalisierung | `MaterialProcessor.parse`, HTML-v2 / PDF-v2 | `NormalizedDocument`, `Block`, `Location`, `ImageArtifact`; Parserkonfiguration bestimmt Dokument-/Blockidentität |
| Bestehende technische Inspektion | `MaterialProcessor.inspect` | Verifiziert Binding, Raw-/Normalized-/Bildhashes und Parserkonfiguration; scheitert beim ersten Konflikt |
| C10 Quality Gate | `validate_material` | Liest explizite Pfade ohne Lock/Resume/Schreibzugriff; sammelt versionierte technische Befunde und Hinweise zur semantischen Prüfung |
| C10 Lecture-Handoff | `prepare_material_handoff` | Prüft erneut und liefert `MaterialReview(report, handoff)`; bei technischen Fehlern `handoff=null` |
| Bestehendes Blockmapping | `map_material`, `MaterialUnit` | Exakte Zeichenfenster im ursprünglichen `Block.text`; C10 filtert Referenzprojektionen aus der Aggregationsauswahl |
| Bestehende Lecture-/Knowledge-Pfade | `adapt_cs50`, `CS50Executor` → SRT → `bind_cs50_knowledge_input` → Chunks → Knowledge-Kandidaten → `KnowledgeEvidence` / Konsolidierung | Eigenständiger, zeitbasierter Transcript-Pfad; C10 wird dort nicht automatisch ausgeführt |

`LectureCourse` und seine `LectureResource`-Objekte bilden Kursmetadaten und
`lecture_blocks` ab. Den Ressourcen fehlen stabile Ressourcen-/Material-/Block-IDs
und vollständige Quellenprovenienz. Der bestehende CS50-Adapter hält deshalb bereits
einen separaten Index `lecture_resource_ids` und einen vollständigen Discovery-Graphen.
`ResourceTask`/`process_lecture.execute_task` führen dagegen Downloads, Parsing und
weitere Aktionen aus; sie sind kein sicherer Read-only-Einstieg für diese Materialien.

`KnowledgeEvidence` verlangt `start` und `end` und erlaubt nur zeitbasierte Quellen
`transcript`, `visual`, `transcript+visual`. `TranscriptKnowledgeDocument` und die
präzise Evidence-Bindung referenzieren Transcript-Chunks/Segmente. Dokumentseiten,
DOM-Pfade und Materialblöcke dürfen dort keine erfundenen Zeitintervalle erhalten.
C10 verwendet daher den ausdrücklich erlaubten Übergabevertrag statt einer
verlustbehafteten Konvertierung in Legacy-Lecture- oder Knowledge-Objekte.

Quellcode: `src/model_materials/materials.py` (einschließlich des unveränderten, weiterhin
aus `processing.py` reexportierten `MaterialPlan`), `src/tools_materials/processing.py`,
`src/tools_materials/mapping.py`, `src/tools_lecture/adapt_cs50.py`,
`src/model_lecture/data_resources.py`, `src/tools_lecture/process_lecture.py`,
`src/tools_knowledge/bind_cs50_transcript.py`, `src/tools_knowledge/cs50_precise_evidence.py`,
`src/model_knowledge/data_knowledge.py`. Allgemeine Runner:
`run_lecture_processing.py` und `run_knowledge_extraction.py`.

## Eingabevertrag

Beide Python-Funktionen nehmen dieselben expliziten Keyword-Argumente entgegen:

```python
validate_material(
    normalized_path=normalized_json,
    receipt_path=receipt_json,
    raw_path=raw_source,
    plan_path=reviewed_plan_json,
    workspace=artifact_workspace,
)
```

- `normalized_path`: vorhandene Datei im Vertrag `NormalizedDocument`, Dokument-Schema **1**.
- `receipt_path`: zugehöriger `ArtifactReceipt`, Schema **1**, Status `completed`, ohne Fehler.
- `raw_path`: vorhandene Originalbytes, kein Download und kein erneutes Parsing.
- `plan_path`: vorhandener geprüfter `MaterialPlan`, Schema **1**, einschließlich vollständigem Discovery-Graphen. Kein Verzeichnis-Scan und kein Auffinden ähnlicher Lectures nach Dateinamen.
- `workspace`: explizite Wurzel des bestehenden Materialworkspaces. Raw, Receipt und normalisiertes Dokument müssen darunter liegen und exakt ihren bestehenden Storage-/Receiptpfaden entsprechen. Symlinks und `..` in Artefaktpfaden werden über `locate`/`safe_path` abgewiesen. Der Plan darf außerhalb liegen.

Relative CLI-Pfade beziehen sich auf das aktuelle Arbeitsverzeichnis; normalisierte
Receiptpfade auf `workspace`; Bildartefakte auf das Verzeichnis der normalisierten
Datei. Raw und Receipt liegen unter `<material-digest>/raw/source` beziehungsweise
`<material-digest>/receipt.v1.json`. Der Validator erzeugt diese Pfade nicht.

Schema-Versionen von Dokument, Receipt, Materialbindung und Plan sowie
`parser.version` müssen ausdrücklich deklariert sein. Legacy-Modelldefaults gelten
nicht als Versionsnachweis. HTML/PDF-v1 bleiben mit bestehenden Lesern lesbar,
werden aber von diesem v2-Handoff zurückgehalten; keine Migration. Parser- und
Dokumentschema-Version sind unabhängig: `normalized.v1.json` mit HTML/PDF-Parser `2`.

Die Funktion liest mit bestehenden Modellen streng validiertes JSON; doppelte
JSON-Schlüssel, ungültige Kodierung, nicht endliche Zahlen, fehlende Dateien und
Schemafehler ergeben Befunde. Fehlerhafte Blockidentitäten werden mit konkretem
Index, Block-ID und verfügbarer DOM-/Seitenposition ausgewiesen, auch wenn die
bestehende Modellvalidierung das gesamte Dokument ablehnt.

## Qualitätsregeln und Ausgabe

Neue `MaterialQualityReport`-Ausgaben haben `schema_version=2` und
`validator_version=cs50_material_quality_v2`; ältere v1-Berichte bleiben lesbar. Er enthält:

| Feld | Vertrag |
|---|---|
| `status` | `failed` bei mindestens einem Fehler; sonst `passed_with_warnings` oder `passed` |
| `inputs` | Die fünf expliziten Eingabepfade; keine stillschweigend ausgewählten Alternativen |
| `observed_sha256` | Tatsächlich gelesene Raw-, Normalized-, Receipt- und Planhashes, soweit verfügbar |
| `document_id`, `material_id`, `resource_id`, `course_id`, `section_keys`, `lecture_ids` | Aus dem validierten bestehenden Binding; bei unlesbarem Dokument nicht behauptet |
| `findings[]` | `code`, `severity`, `category`, `message`, `input`, optional `field`, `block_id`, `block_order`, `location`, `image_id` |

`input` benennt `normalized`, `receipt`, `raw`, `plan` oder `image`. `location`
verwendet das bestehende `Location`-Modell: DOM, Seite, BBox und gegebenenfalls
Zeilenintervall. Dokumentweite Befunde besitzen keine erfundene Blockposition.
Terminalausgaben verbinden diese Angaben mit den Eingabepfaden.

**Nachweisbare technische Fehler** (`category=technical`, `severity=error`) sperren
den Handoff: ungültige Versionen/IDs/Blockreihenfolgen; falsche Raw-/Normalized-
Hashes; abweichende Parser-/Receipt-/Planbindungen; fehlende oder ungültige
Lecture-Verknüpfungen; widersprüchliche Identitätsmetadaten; fehlende
Quellenprovenienz; ungültige DOM-/Seitenzuordnung oder Geometrie; defekte Listen-,
TOC-, Link- oder Inlinecodeprojektionen; beschädigte Codeansichten; falsche oder
fehlende deklarierte Bildartefakte/-hashes. PDF-v2-Klassifikationsmetadaten und
Zeilen-BBoxes werden strukturell geprüft, ohne die Parserheuristik zu wiederholen.

**Mögliche semantische Probleme** (`category=semantic_review`, `severity=warning`)
sind keine bewiesenen Inhaltsfehler: Parserwarnungen/-unsicherheiten, nicht
abgedeckte PDF-Seiten, reine Bildreferenzen ohne archivierte Bildbytes,
unverifizierte Mathe-/Unknown-Blöcke und mögliche Tabellenüberlappung. Eine Seite
kann leer oder bildbasiert sein; fehlende Blöcke allein beweisen keinen Datenverlust.
Fehlende optionale Titel/Metadaten oder BBoxes sind technische Warnungen.
`info` erklärt erhaltene Referenzprojektionen und reversible Codeansichten.
Warnungen erlauben den referenzierenden Handoff und bleiben für Review sichtbar.

Eine deklarierte `data.code_view` braucht Codeblock, PDF-v2, passende Strategie,
mindestens drei sequenzielle Nummern, gleiche Präfixbreite, exakte Zeilenindizes
und die zeichengetreue Rekonstruktion `prefix + code_view_line == source_line`.
Der Originaltext bleibt maßgeblich; keine Codeausführung oder semantische Prüfung.
Bilder ohne `artifact_path` bleiben Referenzen; eine deklarierte lokale Datei
muss dagegen existieren und ihren Hash sowie den Receiptmanifest-Eintrag erfüllen.

Ausgaben sind für dieselben Eingabepfade/-bytes deterministisch. Keine Uhrzeit,
Zufalls-ID oder Dateisystemauflistung wird ergänzt. Nach Relokation ändern sich die
expliziten Pfadangaben; Quellidentitäten und Hashes bleiben erhalten.
Ein vollständig erzeugtes [HTML-Beispiel](../examples/material-quality-html.v1.json)
und [PDF-Beispiel](../examples/material-quality-pdf.v1.json) bleiben historische v1-Nachweise und verwenden ausschließlich
eigene synthetische Fixtures, keine Aussage über die realen CS50-Originale.

## Lecture-Handoff und einmalige Aggregation

`prepare_material_handoff(**paths)` führt denselben Gate-Lauf aus und liefert
`MaterialReview(schema_version=1, report, handoff)`.
Ein alter JSON-Report ist keine Eingabe oder Freigabe für einen späteren Lauf.

Neue `LectureMaterialHandoff`-Ausgaben haben Schema **2**, Adapterversion
`cs50_lecture_material_v2` (v1 bleibt lesbar), `execution_supported=false` und
`knowledge_fact_verified=false`. Er bindet `course_id`, `section_keys` und
`lecture_ids` an die bereits existierenden IDs im geprüften Graphen. Er erhält
`document: NormalizedDocument` und `receipt: ArtifactReceipt` vollständig,
einschließlich Original-URLs, Varianten, Quellprovenienz, Importherkunft,
Parserkonfiguration, Raw-Hash, Block-/Bildpositionen, Metadaten und Unsicherheiten.
`normalized_sha256` und `plan_sha256` binden den Handoff an den geprüften Snapshot.

`aggregation_units` verwendet ausschließlich das bestehende `MaterialUnit`-Modell
und dessen exakte Zeichenfenster mit Standardfenstergröße 2.000. V2 ergänzt
`references`, `list_context` und das Handoff-Inventar `unresolved_references`. Für einen künftigen
Textconsumer ist **ausschließlich diese Auswahl** der Aggregationseingang:

| Originalstruktur | Aggregationsregel |
|---|---|
| Heading, Absatz, Code, HTML-Tabelle | Einmal aus dem Originalblock, in Block-/Fensterreihenfolge |
| `content_role=table_of_contents` | Vollständig im Dokument erhalten, in `excluded_blocks` ausgewiesen |
| Link / `reference_only=true` | Referenzprojektion; Text bereits im Quellabsatz, keine zusätzliche Zählung |
| Leerer Listencontainer | Struktur bleibt erhalten; Listeneinträge kommen aus ihren Absatz-/Codeblöcken |
| PDF-Tabelle | Konservativ als geometrische Projektion ausgeschlossen; Originaltabelle bleibt referenzierbar |
| `data.code_view` | In `alternative_views` referenziert; keine zusätzlichen Units; Originalcode mit Nummern bleibt kanonisch |
| Math, Bild, Unknown | Referenzen erhalten; nach bestehendem Mapping keine faktischen Textunits |

`excluded_blocks` enthält Block-ID → Grund. Modell-Roundtrips prüfen die exakte
Aggregationsauswahl und lehnen zusätzliche/duplizierte Fenster ab. Wiederholte
Materialien in einem CLI-Batch werden abgewiesen. Identische Inhalte aus
verschiedenen Originalressourcen werden nicht heuristisch zusammengelegt.

Kein `ResourceTask`, keine Knowledge-Extraktion, kein Embedding/Vectorupload,
keine Lecture-/Datenbankdatei und kein Receipt werden angelegt oder verändert.

## CLI

```bash
python -m scripts.cs50_material_quality \
  --plan "$REVIEWED_PLAN" --workspace "$EXISTING_WORKSPACE" \
  --normalized "$EXISTING_NORMALIZED_JSON" \
  --receipt "$EXISTING_RECEIPT_JSON" --raw "$EXISTING_RAW_SOURCE"
```

Standard: JSON auf stdout (`{"schema_version":1,"reviews":[...]}`), kurze Zuordnung
und Fehler/Warnungen mit Herkunft auf stderr. Keine Dateien werden geschrieben.
Für mehrere Materialien `--normalized`, `--receipt` und `--raw` gleich oft in
zusammengehöriger Reihenfolge wiederholen; ein gemeinsamer Plan/Workspace.

Nur mit `--output /explicit/new/report.json` wird ein neuer Report geschrieben.
Bestehende Dateien werden auch dann niemals ersetzt; die vorhandene exklusive
atomare Publikation wird wiederverwendet. Der Ausgabeort muss außerhalb des
Eingabeworkspaces liegen; Symlinkpfade werden abgewiesen. Exitcodes:
`0` alle Gates bestanden (gegebenenfalls Warnungen), `1` Materialbefunde mit
Fehlern, `2` CLI-Vertragsfehler oder gescheiterte Reportpublikation.

## Grenzen und konkreter nächster Schritt

SHA-256 beweist die interne Übereinstimmung mit dem gelieferten Receipt, nicht die
Authentizität des Publishers. Der Validator prüft die vorliegenden Normalisierungen;
er rendert/parst Originale nicht erneut und kann verlorene Quellabsätze oder
falsche Klassifikationen nicht vollständig erkennen. Das Inhaltsverzeichnis wird
anhand des vorhandenen v2-Markers behandelt; unbekannte Publisherkonventionen
brauchen eigene Evaluation. PDF-Seitenabdeckung ist ein Hinweis, kein OCR-Nachweis.
Keine semantische Richtigkeit, didaktische Vollständigkeit oder Bildinterpretation.
Geometrische PDF-Tabellen sind konservativ nicht im Aggregationstext; strukturelle
Tabelle und Quellenblöcke bleiben erhalten.

Handoffs/Reports sind lokale Snapshots ohne Signatur, keine Ausführungsberechtigung.
Vor späterer Nutzung `prepare_material_handoff` mit den tatsächlichen Pfaden erneut
aufrufen. Es gibt keinen Snapshot-Lock gegen gleichzeitige externe Änderungen;
die Artefakte müssen während der Prüfung ruhen. Die sichere Legacy-Lecture-
Integration und ein nicht zeitbasierter Knowledge-Evidence-Vertrag fehlen weiterhin.

Empfehlung für C11: Zuerst einen Read-only-Lecture-Consumer implementieren, der den
Handoff anhand der existierenden logischen Lecture-ID registriert und ausschließlich
`aggregation_units` nutzt. Danach `KnowledgeEvidence` kontrolliert um eine
unterscheidbare nicht zeitbasierte Materialreferenz erweitern (Dokument-/Block-ID,
Zeichenfenster, DOM/Seite, Raw-/Normalized-Hash und Provenienz). Die bestehende
zeitbasierte Transcript-Evidence beibehalten. Mit je einem Notes-, Slides- und
Source-Handoff Quellenzitate, fehlende Bildbytes und einmalige Aggregation
nachweisen, bevor eine separat autorisierte Extraktion angeschlossen wird.
