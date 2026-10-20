# Quellenidentität zwischen Knowledge Extraction und Consolidation

## Ursache und Korrektur

TranscriptKnowledgeDocument deklarierte kein `source_id`. Der Extraction-Runner
übergab diese ID zwar an den Konstruktor, Pydantic ignorierte das unbekannte Feld
jedoch mit seinem Standardverhalten. `model_dump` speicherte sie anschließend nicht.
`consolidate_knowledge` verwendete später `document.source_id`, was zu einem
AttributeError führen konnte. Ein im Alt-JSON vorhandenes source_id-Feld wurde mit
dem alten Modell ebenfalls nicht erhalten.

Minimale Korrektur: `source_id: str | None` mit Default `None`, Mindestlänge 1 und
mindestens einem Nicht-Whitespace-Zeichen. Vorhandene IDs werden beim Erstellen,
Speichern und Laden erhalten. Leere oder reine Whitespace-IDs werden bei der
Modellvalidierung abgelehnt. Die Konsolidierung prüft die Quellenidentität vor der
Verarbeitung und meldet bei fehlender ID einen verständlichen ValueError.
Es wird kein globales `extra=forbid` eingeführt, das andere Alt-Daten beeinflussen könnte.

## Geprüfte Datenwege

| Stelle | Verwendung / Ergebnis |
|---|---|
| `model_knowledge/data_knowledge.py` | Einzige Definition von TranscriptKnowledgeDocument; source_id nun explizites optionales Feld |
| `run_knowledge_extraction.knowledge_extraction` | Lädt das originale TranscriptDocument; ID entsteht aus `transcript_path.name.removesuffix(".json")`; der anschließende Konstruktor übergibt source_id bereits korrekt |
| `run_knowledge_extraction.run_knowledge_extraction` | Speichert den Model-Dump über save_dict unter `<Transkriptname>_know_extract.json`; das ergänzte Modell erhält die ID jetzt im Dump |
| `run_knowledge_consolidation.process_knowledge_file` | load_dict mit TranscriptKnowledgeDocument, danach deterministische und semantische Konsolidierung; fehlende ID scheitert vor semantischen LLM-Schritten |
| `tools_knowledge/consolidate_knowledge.py`: Entwicklungsaufruf | Lädt ebenfalls als TranscriptKnowledgeDocument und ruft dieselbe geschützte Funktion auf |
| `consolidate_knowledge` | Übergibt geprüfte ID an ConsolidatedKnowledgeDocument; bestehende semantische Materialisierung übernimmt die Dokumentidentität |
| `tools_knowledge/rebuild_knowledge.py` | Verwendet den Modelltyp als Annotation in build_visual_batches; keine aktive Konstruktion oder Speicherung dieses Eingangstyps |
| `run_knowledge_improvement.py` | Importiert den Typ, aktiver Ladepfad verwendet LectureKnowledgeDocument; alte Beispiele sind Kommentare |
| `tools_knowledge/find_knowledge.py` | Frühere Konstruktion von TranscriptKnowledgeDocument steht nur in Kommentaren |
| `utils/dict_helper.py` | Generischer JSON-Model-Dump und model_validate beim Laden; benötigt keine Änderung |

Der bestehende Runner verwendet den Namen des tatsächlich geladenen Original-
Transkripts als Identität innerhalb seines Kurs-/Vorlesungskontexts. Diese Konvention
bleibt unverändert; sie ist kein neuer global eindeutiger Hash und kein Beleg, dass
die gleiche ID kursübergreifend eindeutig ist. Insbesondere darf der Dateiname einer
beliebigen alten Extraktionsdatei nicht automatisch als Original-Transkript-ID gelten.

## Kompatibilität und fehlende Identität

Alt-JSON **ohne** source_id und mit explizitem `null` bleibt ladbar. Das Feld ist dann
`None`; Daten werden weder migriert noch umgeschrieben. Gültige bestehende source_id-
Felder werden jetzt korrekt gelesen. Explizit leere, Whitespace- oder nichttextuelle
IDs werden als ungültige Metadaten abgelehnt.

Laden ist von Verarbeiten getrennt: Konsolidierung benötigt zwingend eine nichtleere
Quellenidentität, auch für ein Dokument ohne fachliche Ergebnisse. Fehlende Identität
wird nicht durch URL, media_id, Extraktions-Dateinamen oder einen zufälligen Default
ersetzt. Eine URL alleine belegt die ursprüngliche lokale Identitätskonvention nicht.

Falls ein Aufrufer eine nachweislich zugehörige Original-Transkript-ID aus geprüftem
Kontext kennt, kann er daraus ein neues validiertes Eingangsmodell erstellen. Der
PR implementiert keinen automatischen Resolver und überschreibt dabei keine Altdatei.
Bei unbekannter Zuordnung bleibt ein klarer Fehler. Die Modellprüfung kann die
inhaltliche Wahrheit einer vom Aufrufer angegebenen ID nicht beweisen; sie verhindert
fehlende/ungültige Werte und bewahrt explizite Angaben zuverlässig.

## Tests und Umfang

11 Unit-Testfälle: Erstellung mit source_id, JSON-Datei-Roundtrip, Altdateien ohne ID
und mit null, Konsolidierung eines fachlichen Ergebnisses mit erhaltener ID/Evidenz,
früher verständlicher Fehler bei fehlender ID trotz vorhandener URL, explizite
Zuordnung aus verifiziertem externem Kontext sowie ungültige IDs.

Die Tests führen die tatsächlichen deterministischen Produktionsfunktionen mittels
AST isoliert mit den realen Modellen und Texthelfern aus. App-Konfiguration und
LLM-Imports werden damit vermieden; Socket/DNS sind gesperrt. Keine semantische
LLM-Konsolidierung wurde ausgeführt. Aufruf:
`python -m pytest tests/test_knowledge_source_id.py -q`.

Zusätzliche Regression: vorhandene offizielle Transcript-Import- und CS50-Tests im
Workspace. Ruff, Repository-Commit-Hooks und `git diff --check` prüfen die Änderung.
Keine Änderung an Discovery, Selection, zeitbasiertem Chunking, Import, Loviscach oder
bestehenden gespeicherten Daten. Produktiv ändern sich nur das Modellfeld und die
frühe Konsolidierungsprüfung.
