# C23-02B: geprüfte Contentadapter

Bestandsprüfung vor Implementierung, 17.10.2026. Basis: `master`
`6ef394a2f7a4debccce75f7b5e1ef3449f9457aa`, einschließlich gemergtem C23-02A
(PR #76). [ADR](parsed_content_persistence_adr.md),
[Datenmodell](parsed_content_data_model.md),
[Core](content_store_implementation.md),
[Folgearbeiten](../planning/c23_implementation_plan.md).

## Tatsächliche Zuordnung und Prüfinvarianten

| Bestehendes Objekt | ContentStore-Entität / Beziehung | Prüfung und Herkunft |
| --- | --- | --- |
| `ResourceCandidate`, vollständiger `MaterialPlan` bzw. `CS50AdapterPlan` | Source, Bindingartefakt, unveränderte Planbytes; keine neue Discovery | Bestehende Modellvalidatoren prüfen Course/Section/Lecture/Resourcegraph. CS50 Source-ID bleibt Resource-ID; Material und Lecture sind eigene IDs |
| Raw Material / SRT | SourceVersion mit primärem RawArtifact; mehrere Parserstände pro Rawversion | Receipt-/Input-/Outputhashes, exakte Pfade, Größe; Rawmanifest enthält nur seine fünf vereinbarten Felder |
| `ArtifactReceipt` | Unverändertes Receiptartefakt je geprüfter Publication, nicht eine globale veränderbare Versionstabelle | completed, Raw-/Normalized-/Bildhashes, Parserconfig und Storagepfade; C10 erneut ausführen |
| `NormalizedDocument` | ParsedDocument-Stream `material:<material_id>` plus Parsed-Version; Original-ID als Alias | Vorhandenes Modell, Document-/Blockidentitäten, Parser-/Schema-Version, vollständige Payloadbytes unverändert |
| `ImageArtifact` | Bildmetadaten im Originalpayload, lokale Bytes als versionierte Artefaktreferenzen | Keine Rawversionsänderung durch andere Parserbildausgabe. Referenz ohne Bytes bleibt Referenz; deklarierte lokale Datei muss vorhanden/hashkorrekt sein |
| `MaterialQualityReport`, `MaterialReview`, `LectureMaterialHandoff` | Neu erzeugter Gatebeleg und exakte Aggregationsprojektion | `prepare_material_handoff` prüft den eingefrorenen Snapshot. Callerreport/`verified=true` ist keine Freigabe |
| `CS50TranscriptBinding`, ausgewählter Courseplan | Sourcebinding und vollständiger Originalplan als Beleg | Source=Subtitle-Resource, Lecture verschieden; `CS50AdapterPlan` rederiviert Auswahl, Pfade, Tasks und Abhängigkeiten |
| Executionreceipt | Unveränderte Byteartefakte; **kein bestehendes Pydantic-Modell namens ExecutionReceipt** | Executor verwendet dict Schema 1: binding + actions. Genau zwei passende done-Tasks, korrekte Actions, SHA und Parse-Inputhash |
| `TranscriptDocument`, `TranscriptProvenance` | Parsed-Stream `transcript:srt:<resource_id>`, Payload ohne erfundene eigene Schemaversion | `validate_document` reparst Original-SRT und vergleicht Text/alle Segmente; kein Knowledgebinderimport |
| Material-`Block` / `TranscriptSegment` | Alle Originalblöcke bzw. ein Absatzblock je Cue | Materialblock-ID erhalten. Cue-ID nach C23 aus Parsed-Version/Originalseg_id ableiten; seg_id zusätzlich unverändert erhalten |
| `Location` / Cue | ContentLocator mit Rawhash und Ursprungspointer | DOM, Seite, Zeilen, BBox bzw. bekannte Cuezeiten; fehlende Geometriekonvention bleibt unknown, keine erfundenen Zeitwerte |

## Vorab geklärte Vertragsgrenzen

- Materialreceipts und SRTreceipts enthalten keine Implementierungsrevision.
  Ein zusätzlicher expliziter Implementierungsbeleg muss Original-Revision,
  vollständige Parameter und Raw-/Payload-/Receipthashes binden. Er wird archiviert.
  Er ist eine nachvollziehbare lokale Attestierung, keine unabhängige Signatur
  oder nachträglich erfundene Publisherauthentizität. Fehlender Beleg sperrt.
- `model_lecture.data_resources` importiert bisher Settings schon auf Modulebene;
  tatsächlich benötigt nur `LectureCourse.root` diese. Der Import wird genau
  dorthin verzögert. Verifikation ruft diese Property nicht auf; ihre spätere
  Legacyfunktion bleibt erhalten. Keine neue parallele Lecturemodellhierarchie.
- Der content-v1-SQL-CHECK kennt Runarten `raw` und `synthetic`. Ohne Migration
  bezeichnet `raw` in B die byteerhaltende Artefaktübernahme eines geprüften
  Bundles; ein zugehöriger `parsed_version_id` kennzeichnet Publication.
  `synthetic` bleibt ausschließlich der isolierte A-Testvertrag. DDL unverändert.
- Portable relative SRTbindings werden unterstützt. Absolute Bindings können
  nicht ohne Umschreiben in eigenes Staging gelegt werden und bleiben gesperrt.
  Insbesondere keine Suche nach `data/Harvard` statt `data/lectures/Harvard` (#72).
- C10-Gates enthalten Ausführungspfade. Nur neu erzeugte Gatebelege werden auf
  explizite logische Snapshotpfade bezogen, damit sie deterministisch sind.
  Originalpayloads, Pläne, Receipts und optional gelieferte frühere Reports
  bleiben unverändert. Die Originalprovenienz wird nicht aus Pfaden abgeleitet.

Implementierte Signaturen, Trust Boundary, Projektion und Testergebnisse stehen
im [B-Abschnitt der Implementierungsdokumentation](content_store_implementation.md#c23-02b-geprüfte-bundleadapter).
`adapters.py` stellt nur nach Gate ausgestellte Prozess-Candidates bereit;
`publication.py` verwendet die bestehenden Storeprimitiven ohne DDLänderung.
Spätere Gate-/Receiptbelege können in einem neuen geprüften Run archiviert werden,
ohne die bestehende Parsed-Version zu ändern. Keine automatische Bestandsübernahme,
kein HTTP-Publish und keine Freigabe für produktive Daten.
