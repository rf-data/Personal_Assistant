# Transcript-Ingestion, Artefakte und Resume v1

Ein IngestionPlan bindet explizit eine Lecture, den vollständigen gewählten Kurs
oder alle 50 Sources. Fehlende Importbelege blockieren vollständige Kursscopes;
keine erfundenen Chunkzahlen. Portable Inputbindungen, gesamte Original-Chunks,
Offset-Units und deterministische Point-IDs werden gespeichert. Der Planhash
bindet Adapterplan, Quellen, Chunking und Collection-/Embeddingkonfiguration.

embed_plan revalidiert vorhandene originale Quellen/Belege und chunkweise
Text-/Segment-/Zeitprovenienz vor Inferenz. VectorArtifact bindet Plan- und
Embeddingversion; exklusives fsync/atomisches Speichern übernimmt das bestehende
Checkpoint-Modul. Bestehende gültige Vektordateien werden geprüft wiederverwendet;
kaputte Dateien nicht überschrieben. Ausgabe-/Statuspfade getrennt von Quellen,
keine Symlinks. Fake- und lokale Modelle bleiben strikt unterscheidbar.

upsert_plan ist standardmäßig reine Preview. execute und allow_create sind
separate explizite Freigaben. Unter POSIX-Scope-Lock werden vorhandene Points
inklusive UUID, vollständiger Payload, Dimension/Norm und konkretem VectorArtifact
geprüft. Für ausgewählte Sources sind zusätzliche alte Point-IDs ein Konflikt:
geänderte Quellen/Chunkpläne benötigen einen neuen Indexstand. Keine stillen
Löschungen oder Collection-Neuanlagen. Fremde/kaputte Points blockieren Upsert.

Uploadreceipts binden Plan-/Vektorhash, Status, erwartete/verifizierte Counts und
Fehlerklasse ohne mögliche Authentifizierungsinformationen. Nach verlorener
Schreibbestätigung wird beim Resume der tatsächliche Bestand neu gelesen;
identische vorhandene Points werden nicht erneut geschrieben. Done erst nach
vollständigem Readback aller erwarteten Points und erneuter Sourcevalidierung.
Cosine-Float32-Rundungen werden ausschließlich innerhalb enger Vektortoleranz
akzeptiert; Payloadidentität bleibt exakt. Erfolgreicher Upsert allein ist kein
Completion-Nachweis.

Single-writer-Betrieb: kooperierende Runner verwenden denselben State-Root/Lock;
kein verteilter CAS-Vertrag gegen fremde gleichzeitige Adminschreibvorgänge.
Source-/Embeddingwechsel: neue explizit benannte Collection, komplette Prüfung,
erst danach separat freigegebener Retrieval-Ziel-/Aliaswechsel. Kein automatischer
Aliaswechsel, keine Migration, keine produktive Verbindung in Tests.

Integrationsbefund: KnowledgeSettings.visual_model besitzt einen leeren, bei
Defaultkonstruktion nicht validierten Legacy-Default. Ein vollständiges direktes
model_validate(model_dump()) scheitert daran. Der Indexadapter validiert Abweichungen
von unveränderten Defaults und fordert exakte vollständige Configgleichheit; kein
erfundener Visual-Modellname und keine Änderung am bestehenden Modell.
