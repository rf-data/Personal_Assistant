# Transcript-Ingestion, Artefakte und Resume v1

C23-05: Dieser Indexpfad bleibt zeitbasierten, vollständig gebundenen SRTs
vorbehalten. [TXT-/Nullzeitvertrag](../contracts/official_transcript_unknown_time.md):
Lokaler TXTimport ist kein IngestionPlan. Sourceprüfung/Chunking und
`source_time_window` weisen unbekannte Medienzeiten ausdrücklich ab; keine
Zeichenoffsets als Sekunden und keine implizite TXT-zu-SRT-Konvertierung.

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

Integrationsbefund: KnowledgeSettings enthält auch nicht für Chunking benötigte
Visual-/Download-/Dateikonfiguration. Indexpayloads speichern ausschließlich die
vollständigen drei tatsächlich verwendeten Chunkerparameter (target_duration,
max_duration, overlap_segments), nicht private Pfade oder sonstige LLM-Konfiguration.
Dies vermeidet zugleich den leeren Legacy-Visual-Default beim Config-Roundtrip,
ohne KnowledgeSettings oder den Chunker zu ändern. Konfigurationsgleichheit wird
kanonisch und exakt geprüft, einschließlich Typkonvertierung.
