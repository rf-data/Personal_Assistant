# Künftige Knowledge-Collection v1

KnowledgeCollectionDefinition beschreibt cs50_knowledge_items_v1 mit explizitem
Embedding-/Distanz-/Payloadvertrag. execution_supported=False: keine Erstellung,
Uploads oder Produktivbefüllung implementiert. Der Transcript-Upsert akzeptiert
diese Records nicht; synthetische LLM-Ergebnisse gelangen nicht in eine Knowledge-DB.

Read-only Mapping übernimmt die bestehenden TranscriptKnowledgeDocument- und
ConsolidatedKnowledgeDocument-Modelle. Original-Statement-/Expression-Identitäten,
Typ, Text/Latex, Topics, vollständige unveränderte Evidence mit Chunk-/Segment-/
Item-Referenzen und Originalzeiten bleiben erhalten. UUIDv5 bindet Source,
kanonische Ergebnisversion, Itemtyp/Original-ID und Evidence; separates Namespace.
Keine neuen fachlichen Knowledge-Modelle oder veränderte Evidence-Bindung.

Originale Sources/Belege/Chunkpläne werden vor Mapping revalidiert. Fehlender/
fremder source_id, widersprüchliche Kurs-/Lecture-/URL-/Transcript-Provenienz,
leere/fremde Segmente und nicht aus Original-Cues/Chunks stammende Zeiten werden
abgelehnt. KnowledgeEvidence.source ist Modalität; TranscriptProvenance.transcript_source
bleibt Herkunftsstrategie. Visual-only Evidence ohne Transcript-Referenzen ist
hier nicht abgedeckt; kombinierte Modalität bleibt erhalten, visuelle Vollständigkeit
wird ausdrücklich nicht behauptet. Keine Visual-/Whisper-Anpassung.

KnowledgeMappingContext ist nachweisbarer externer Ergebnis-/Reviewkontext:
Extraktionsprovider/-modell, Prompt-/Ergebnisschemaversion, optionale tatsächliche
Ergebnisdatei-/Receipt-Hashes und Qualitätsstatus. Fehlende Modell-/Promptangaben
bleiben null statt aus Dateinamen/URLs erfunden zu werden. Result_content_sha256
ist der kanonische Modelinhalt, nicht fälschlich der Bytehash einer unbekannten Datei.
Geprüfte Sources ergänzen verfügbare Kurs-/Lecture-/Ressourcen-/Quellenmetadaten;
fehlende Originalmetadata wird zusätzlich als solche markiert.

Fake-Extraktion und synthetische Sources bleiben ausdrücklich synthetic.
Reviewed verlangt eine konkrete manuelle Reviewreferenz; Pydantic-Validität allein
ist kein Qualitätsurteil. Originale Items werden zusätzlich unverändert erhalten.
Vor einer späteren echten Collectionbefüllung fehlen reale Qualitätsfreigabe,
vollständiger nachweisbarer Extraktionskontext und ein separat freigegebener
Knowledge-Index-Executor. Dieser Auftrag bereitet ausschließlich den Vertrag vor.

Optionaler Extraktionsbeleg: Ein angegebener Receipt-Hash erfordert die konkrete
Checkpointdatei. Status done, Jobidentität, geprüfte Source-/Transcript-/Chunkplan-
Hashes und portable Inputbindung müssen passen. Alle gespeicherten Chunkresultate
werden an den versionierten Checkpoint-Adressen gelesen und erneut gehasht.
Extraction muss diesen Originalresultaten entsprechen; konsolidierte Itemreferenzen
müssen auf tatsächlich vorhandene ursprüngliche Items zeigen. Nur dann ist
extraction_context_verified=true. Provider, Modell, Prompt-/Ergebnisschemaversion
und execution_mode kommen aus der geprüften Jobidentität; widersprechende Angaben
werden abgelehnt. Ohne Beleg bleibt der externe Kontext als ungeprüft kenntlich.
Die Modellangabe beschreibt die Jobkonfiguration. execution_mode=offline und
quality_status=synthetic bleiben erhalten und behaupten keinen ausgeführten
Modell-/API-Aufruf, auch wenn die Konfiguration einen realen Providernamen enthält.
