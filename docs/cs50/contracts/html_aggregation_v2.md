# C26-A: HTML-Aggregation und technisches Quality Gate v2

Stand: 22.10.2026. Entwicklungsbasis: `master` / `e581e201ef6b3d6c06aca14de845e0687d213b37`.

Die vorhandenen Materialfenster erhalten direkte Linkreferenzen und typisierte
Listenpfade. Text, Zeichenfenster, Dokument-/Block-/Unit-IDs und Parserausgabe
bleiben erhalten. Der Parser wird nicht verändert. Diese Metadaten ermöglichen
einen späteren Dokumentconsumer; Knowledge-Extraktion wird dadurch nicht gestartet.

## Untersuchte Verträge und Zuständigkeiten

- `src/model_materials/materials.py`: bestehende `NormalizedDocument`, `Block`,
  `Location`, `ParserConfig`, `ArtifactReceipt` und `MaterialPlan`; unverändert.
- `src/tools_materials/parse_html.py`: HTML-v2 erzeugt separate Linkblöcke,
  strukturierte Listencontainer und äußere bis innere `data.list_context`-Ketten;
  unverändert. `processing.py` und `storage.py` bleiben ebenfalls unverändert.
- `src/tools_materials/mapping.py`: bestehendes `MaterialUnit` und `map_material`
  werden erweitert. Die bisherige Ausschlussfunktion wird hierher verschoben und
  vom Handoff weiter reexportiert; es gibt eine gemeinsame Ausschlussregel.
- `src/tools_materials/html_projection.py`: typisierte Referenz-/Listenmetadaten
  und reine DOM-Zuordnung auf dem vorhandenen Dokument; kein zweiter Parser.
- `src/tools_materials/quality.py`, `quality_projection.py` und
  `src/model_materials/quality.py`: bestehendes Finding-Modell und Statusregeln,
  ergänzt um technische Projektionsintegrität.
- `src/tools_lecture/material_handoff.py`: derselbe geprüfte Adapter erzeugt v2,
  behält den vollständigen Quellgraphen und liest ältere v1-Handoffs weiterhin.
- `scripts/cs50_material_quality.py`: vorhandene CLI unverändert; enthält jetzt
  versionierte v2-Reports und Handoffs in der bisherigen Batch-Hülle.

## Schema und Kompatibilität

| Vertrag | Neue Ausgabe | Kompatibilität |
|---|---|---|
| NormalizedDocument, Receipt, Plan | weiterhin Schema 1 | Keine Migration oder neuen Normalized-Dateien |
| HTML-Parser | weiterhin Version 2 | Original- und Normalized-Bytes bleiben unverändert |
| MaterialUnit | Schema 2 im neuen Handoff | v1 bleibt lesbar; v1-Serialisierung lässt neue Felder weg |
| LectureMaterialHandoff | Schema 2, `cs50_lecture_material_v2` | v1 wird mit seiner bisherigen Aggregationsregel geprüft und gelesen |
| MaterialQualityReport | Schema 2, `cs50_material_quality_v2` | v1-Reports bleiben lesbar; Version und Validator müssen zusammenpassen |
| MaterialReview / CLI-Batch-Hülle | weiterhin Schema 1 | Kinder besitzen ausdrücklich ihre eigene Version |
| MaterialCollection | weiterhin `cs50_material_blocks_v1` | Identität/Quellfenster unverändert, Ausführung weiterhin gesperrt |

`map_material(document)` behält aus Kompatibilitätsgründen die bisherigen
v1-Fenster. `map_material(document, projection_version=2)` erzeugt die kanonische,
bereits gefilterte Handoff-Auswahl mit Metadaten. Beide verwenden dieselbe
Fenstererzeugung. Der Handoff verwendet v2 ausdrücklich. PDF und andere Formate
bekommen dieselben bisherigen Textfenster; die neuen HTML-Felder bleiben leer.

Ein älterer Consumer, der nur v1 akzeptiert, darf den neuen Handoff nicht
ungeprüft übernehmen. Er muss v2 unterstützen oder einen bereits vorhandenen
v1-Snapshot verwenden. Die Unit-ID bezeichnet weiterhin das Quellzeichenfenster;
Caches müssen zusätzlich Schema-/Adapterversion berücksichtigen. Alte Reports
sind keine erneute Freigabe. `prepare_material_handoff` prüft explizite Artefaktpfade
bei jeder Verwendung erneut. `execution_supported` und `knowledge_fact_verified`
bleiben `false`.

## Linkreferenzen

Jede v2-Unit besitzt `references`. Ein Eintrag enthält:

```json
{
  "source_block_id": "material_block:<link-id>",
  "source_dom": "/main[1]/ol[1]/li[7]/ul[1]/li[1]/a[1]",
  "text": "Indoor Voice",
  "original_url": "https://cs50.harvard.edu/python/psets/0/indoor/",
  "relation": "linked_block",
  "kind": "task_material"
}
```

Die Link-ID löst im vollständigen `handoff.document.blocks` den Linkblock auf.
Die Unit selbst referenziert ihren ursprünglichen Inhaltsblock und dessen
Zeichenfenster. Der nächste eindeutige Inhaltsvorfahr im DOM wird als Besitzer
verwendet. Gleichlautende Texte sind kein Zuordnungskriterium. Mehrere Links in
einem Absatz behalten ihre separaten Link-IDs und Quellreihenfolge.

Bei mehreren Fenstern eines Inhaltsblocks stehen alle Referenzen ausschließlich
am ersten Fenster (`char_start=0`). `linked_block` bezeichnet ausdrücklich die
Beziehung zum ganzen Block, keine behauptete exakte Link-Zeichenposition innerhalb
dieses Fensters. Ein Consumer gruppiert Fenster über `unit.block.block_id` und
liest dessen Referenzen einmal. Linktext wird weder angehängt noch als zusätzliche
Texteinheit aggregiert.

`original_url` wird exakt aus `link.data.original_url` übernommen. Bereits der
bestehende Parser löst relative HTML-hrefs auf; deren ursprüngliche Schreibweise
ist nicht nachträglich rekonstruierbar. Die Projektion normalisiert diese gespeicherte
URL nicht erneut. `source_dom` führt zum ursprünglichen HTML-Element.

Die Klassifikation ist strukturell:

- `internal_anchor`: nicht leeres Fragment derselben gespeicherten Dokument-URL;
- `task_material`: gleiches HTTP(S)-Origin und untergeordneter Pfad einer als
  `problem_set` gebundenen Quellseite; keine Behauptung über den Zielinhalt;
- `document_reference`: andere HTTP(S)-Dokumentreferenz desselben Origins,
  auch mit Fragment eines anderen Dokuments;
- `external_reference`: anderes HTTP(S)-Origin;
- `other_scheme`: z. B. `mailto:`.

Kein Ziel wird abgerufen. Parserbedingt verlorene reine `#`-Marker und äquivalente,
aber anders geschriebene URLs werden nicht heuristisch rekonstruiert.

`handoff.unresolved_references` enthält Referenz plus `reason`: `excluded_content`
bei ausdrücklich ausgeschlossenen TOC-Inhalten, `no_unique_owner` bei fehlendem
oder mehrdeutigem DOM-Besitzer. Beispielsweise können mehrere Textfragmente nach
einer Bildunterbrechung denselben Quell-DOM-Pfad haben. Dann wird kein Absatz
erraten. Die Originalreferenz bleibt erhalten und im Report sichtbar.

## Listen rekonstruieren

`unit.list_context` ist eine vollständige äußere bis innere Kette. Jeder Eintrag
enthält `source_block_id` des Listencontainers, `list_dom`, `item_dom`, `depth`
(1-basiert), `item_index` (0-basiert), `parent_item_dom`, `ordered`, die unveränderten
Tokens `start` und `value`, `reversed` sowie den abgeleiteten `ordinal`.

Ein Consumer gruppiert Inhaltsfenster nach `(document_id, item_dom)`. Mehrere
Absätze und Codefenster desselben Listenelements bleiben dadurch zusammen.
`parent_item_dom` verbindet den inneren Eintrag mit dem äußeren; die zugehörige
Listenblock-ID und der vollständige Dokumentgraph bleiben erreichbar. Geschwister
werden nach `item_index` sortiert. `ordinal` berücksichtigt Startwert, explizite
`li[value]` und rückwärts nummerierte Listen. Ungeordnete Listen haben keinen
Ordinalwert. Die ursprünglichen Tokens bleiben auch bei ungültiger Nummerierung
erhalten.

Bei leerem Listenelement ohne Inhalts-/Kontextblock lässt die bisherige
Normalisierung dessen etwaigen `li[value]` nicht erkennen. Eine davon abhängige
Nummerierung bleibt deshalb `null`, bis ein bekannter expliziter Wert sie wieder
bestimmt. Ungültige Start-/Werttokens erzeugen ebenfalls `null` und eine Warnung.
Leere Elemente bleiben über `list.item_doms` im Dokument rekonstruierbar; es
entstehen keine zusätzlichen Textunits. Der Parser wird dafür nicht umgebaut.

## Technische Qualitätsprüfungen

Die bisherigen Hash-, Binding-, Geometrie-, Codeansichts- und Quellenprüfungen
bleiben bestehen. Bei bereits fehlerhaften Eingangsdaten bleibt der Handoff
blockiert; typed projections werden erst auf strukturell gültigen Daten erzeugt.

| Finding | Severity / Bedeutung |
|---|---|
| `reference_source_missing` | error: referenzierter Quell-Linkblock fehlt |
| `reference_projection_invalid` | error: URL/DOM/Text/Klassifikation, Besitzer oder Unresolved-Inventar widerspricht der Quelle |
| `reference_projection_missing` | error: Quell-Link weder einmal projiziert noch ausdrücklich unresolved |
| `reference_duplicate` | error: Link mehrfach projiziert/inventarisiert |
| `reference_unresolved` | info bei TOC; warning bei nicht eindeutiger Inhaltszuordnung |
| `list_parent_missing` | error: Kontext passt nicht zum einschließenden Listen-/Item-DOM |
| `list_hierarchy_inconsistent` | error: fehlende/verkehrte Tiefe oder Eltern, widersprüchliche Werte, Reihenfolge oder projizierte Ancestry |
| `list_numbering_unresolved` | warning: angezeigte Nummer aus vorhandenen Quelldaten nicht sicher bestimmbar |
| `aggregation_content_mismatch` | error: Quellblock oder lückenlose, einmalige Zeichenfensterabdeckung verändert |
| `projection_invalid` | error: untypisierbare Metadaten oder zusätzliche Struktur-/Referenz-Textunits |

Vorhandene Codes wie `list_context_invalid`, `list_invalid`,
`link_projection_invalid` und `block_identity` bleiben erhalten. Blockbezogene
Findings nennen Block-ID, Reihenfolge und verfügbare DOM-Position. Ein Fehler
sperrt den Handoff; Warnungen bleiben sichtbar und führen zu
`passed_with_warnings`. Ein ausgeschlossener Strukturblock ist kein Fehler.

Die Prüfung vergleicht Unit-Abdeckung und Codezeichen mit dem normalisierten
Quellblock. Sie behauptet keine erneute inhaltliche Prüfung des HTML-Parsers.
Ein `passed` bestätigt technische Integrität, keine fachliche Richtigkeit oder
Vollständigkeit einer späteren Wissensextraktion.

## Nachweise und echter Week-0-Vergleich

Siehe [Validierung](../../deployment/c26a/html_aggregation_validation.md) und
[Baseline-Fingerprints](../../../tests/fixtures/material_quality/html_projection_baseline.v1.json).
Die echten Pilot-Exporte werden ausschließlich nach lokaler Bereitstellung gelesen.
Es gibt keinen SSH-Zugriff, Download, Job-Replay oder Schreibzugriff auf Pilotdaten.
