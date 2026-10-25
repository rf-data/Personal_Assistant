# MAINT-04 – Migration und Betriebshinweise

Für bestehende Konfigurationsdateien ist **keine Datenmigration erforderlich**.
Alte öffentliche Imports bleiben bestehen; bestehende Runner wählen weiterhin
ihre bisherige Modellfamilie. Es gibt keinen ausgeführten Produktionslauf.
C26 bleibt **HOLD**.

Neue reine Parsingaufrufer verwenden `src.core.config_parsing`. Die internen
Feldbasen aus `src.core._parsing_settings` sind kein öffentlicher Importvertrag.
Legacyaufrufer dürfen ihre Imports nicht pauschal von `config` auf
`config_parsing` umstellen. Vorhandene Env-/Credential-/SDKvoraussetzungen von
`config` bleiben bestehen. Die Konsolidierung macht diese Legacyimporte nicht
automatisch SDK-frei.

## Bekannte Unterschiede beim Wechsel

| Ausgang / Ziel | Risiko | Erforderliche explizite Entscheidung |
| --- | --- | --- |
| legacy-unversioned → parsing-unversioned | name_log/name_logfile sind am Ziel verboten | Loggingkontext separat erhalten; Quelle unverändert archivieren; Felder nur nach dokumentierter Zustimmung aus einer Kopie entfernen |
| parsing-unversioned → legacy-unversioned | classify_header_footer/classify_foot_notes/classify_headings werden ignoriert | Wechsel ablehnen, solange Flagsemantik relevant ist; keine automatische verlustbehaftete Konvertierung |
| Legacy-PDF → Parsing-PDF ohne Flags | P ergänzt alle drei Flags=True | Gewünschtes bisheriges Pipelineverhalten erheben und Werte ausdrücklich festlegen; aus L-Payload allein ist es nicht rekonstruierbar |
| extraction_model leer | Dumpwert gleich, Schema-Default vs Factory verschieden | Herkunftsvertrag und Schema behalten; keinen Schema-/Hashvergleich allein über Defaultdumps bewerten |
| streamlit_run.yaml → P | Loggingfelder führen zu ValidationError | Passende L-Familie beibehalten oder eigene versionierte Migration reviewen |
| cfg_parsing.yaml → L | dort enthaltenes classify_header_footer=False geht bereits heute verloren | Diesen alten Verlust nicht als erfolgreich erhaltene Klassifikation ausgeben; Herkunft und Zielpipeline prüfen |
| wiki.article_to_parse/parser | beide Familien ignorieren diese Felder | Nicht automatisch in page_id umbenennen; Originalpayload erhalten und fachlichen Aufrufer klären |

`model_validate` akzeptiert fremde gleichnamige Modellinstanzen weiterhin nicht.
Auch ein `model_dump` vor Validierung ist kein allgemeiner verlustfreier Adapter:
es löst die Logging-/Flagunterschiede nicht. Private Basisklassen nicht als
Umgehung der Familienprüfung verwenden.

Für eine spätere genehmigte Migration: Originalbytes und Herkunftsfamilie sichern,
Payload unverändert mit dem bisherigen Reader validieren, unbekannte/ignorierte
Felder separat inventarisieren, Ziel-/Defaultentscheidungen dokumentieren und
erst eine neue Kopie schreiben. Vorher/Nachher-Dumps, Schema, Parserpfade,
Ausgabename und gegebenenfalls materialgebundene Hashes/Receipts getrennt prüfen.
Keine In-Place-Normalisierung und keine automatische Übernahme von Modellinstanzen.
Nicht rekonstruierbare Felder oder unbekannte Herkunft blockieren den Wechsel.

## Versionierter Folgevertrag

Vorschlag für MAINT-05, **nicht implementiert**: ein separater Envelope mit
expliziter Formatversion und Herkunftsvertrag vor der Settingsvalidierung.
Unversionierte Bestände werden nur nach ausgewähltem alten Vertrag gelesen;
unbekannte Versionen werden abgelehnt. Laufzeitpfade, IDs, Encoding und Logger
bleiben im Kontext. Neue Requiredfelder, strengere Extras oder Bereichsvalidatoren
benötigen eigene Migrations-/Fehlertests. Bestehende RunSettings-Aliase erhalten
keinen nachträglich erfundenen `meta_type` in alten Payloads.

JSON-Schemata und Tests sind mit beiden tatsächlich vorhandenen Pydanticversionen
geprüft; die offene Dependencyrange ist keine Garantie für jedes zukünftige
Release. Bei Versionswechsel zuerst Charakterisierung und Schemafingerprints
prüfen. Die MAINT-03B-Baseline nicht ungeprüft neu schreiben.

Rollback dieses Codepakets benötigt keinen Datenrollback: Die bisherigen
Konfigurations-/Parserausgaben und vorhandenen Workflow-Snapshots werden nicht
umgeschrieben. Für die Veröffentlichung gelten die Basis-/Vorgängerhinweise in
[Validierung](maint04_validation.md); reguläres Review und spätere Integration
bleiben erforderlich.
