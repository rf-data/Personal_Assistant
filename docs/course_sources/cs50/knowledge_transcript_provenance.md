# Transcript-Provenienz in Knowledge-Ergebnissen

## Änderung

TranscriptKnowledgeDocument, ConsolidatedKnowledgeDocument und LectureKnowledgeDocument
haben vier gemeinsame optionale Felder: `language`, `transcript_provenance`
(vorhandenes TranscriptProvenance-Modell), `course_id` und `lecture_id`.
Alle Defaults sind None. Eine kleine gemeinsame Metadaten-Basisklasse vermeidet
unterschiedliche Validierung und Übergaben in den drei Verträgen.

Der Extraction-Runner übernimmt Sprache und Provenienz direkt aus dem geladenen
TranscriptDocument. `course_id` wird nur aus dem bereits vorhandenen LectureContext
übernommen; der Aufrufer muss dessen Kurszuordnung geprüft haben. Eine neue Prüfung
gegen Discovery oder Dateien findet hier nicht statt. LectureContext enthält keine
geprüfte einzelne Vorlesungs-ID: der Runner lässt lecture_id daher leer. Externe
Aufrufer können eine ausdrücklich geprüfte ID setzen; sie wird weitergereicht.
Keine Zuordnung wird aus Dateinamen, URL oder Abschnittszahlen geraten.

Deterministische Consolidation und beide Ergebniszweige der semantischen Consolidation
kopieren die Metadaten. Dabei wird auch die schon vorhandene media_id nicht mehr beim
Übergang über ConsolidatedKnowledgeDocument verworfen. source_id und transcript_url
werden unverändert übernommen. Keine Änderung des Chunkings, seiner IDs, Segment-IDs
oder Zeiten. Der bestehende source_id-Guard aus PR #10 bleibt erhalten.

## Validierung und Kompatibilität

Widersprüche zwischen explizitem Dokumentfeld und TranscriptProvenance werden für
language, transcript_url/source_url und media_id abgelehnt, sofern beide Angaben
bekannt sind. URLs werden dabei als deklarierte Strings verglichen; es gibt keine
stille Umschreibung oder vermutete URL-Gleichwertigkeit. Unbekannte Werte werden
nicht mit geratenen Angaben ersetzt. Fehlende Dokumentwerte werden nicht automatisch
aus verschachtelter Provenienz aufgefüllt; die originale Provenienz bleibt erhalten.

Bestehende Knowledge-JSONs ohne neue Felder sind weiterhin ladbar. Es gibt keine
Migration und kein Umschreiben gespeicherter Dateien. Die Metadaten-Basisklasse ändert
nicht das bestehende Pydantic-Verhalten bei fremden Zusatzfeldern. Neue Leser erhalten
neue Felder; ältere Leser können sie je nach Modell ignorieren und damit verlieren.
Die Validierung prüft deklarierte Konsistenz, nicht die tatsächliche Echtheit einer URL
oder Identitätsangabe. Sie erfolgt beim Erstellen/Laden des Modells; nachträgliche
ungeprüfte Mutation bestehender Pydantic-Objekte ist keine validierte Übergabe.

KnowledgeEvidence.source bleibt die Modalität `transcript`, `visual` oder
`transcript+visual`. Die Erwerbsstrategie wie `official_subtitle` oder
`official_transcript` liegt ausschließlich in transcript_provenance.transcript_source.
Es gibt keine Änderung von Evidenz- oder visuellen Modellen.

## Erhalten und weiterhin nicht abgebildet

Vollständig durchgereicht: Sprache, der vollständige vorhandene TranscriptProvenance-
Inhalt (Herkunftsstrategie, Downloadstrategie, Original-URL, lokale Quelldatei, Sprache,
Medien-ID, Format, Provider/Modell und acquired_at), explizite Kurs-/Vorlesungszuordnung,
source_id, transcript_url und bestehende media_id. Chunk-/Segment- und Zeitbelege
bleiben über die bisherigen Evidence-Builder erhalten. Die Herkunft ist dokumentweit;
Evidence verweist weiterhin über Chunk-/Segmentbelege auf dieses Dokument.

Nicht neu abgebildet: Quellen-Hash/Revision, genaue Textpositionen, Lizenzprüfung,
Discovery-Resource-IDs, mehrsprachige Mischquellen, mehrere verschiedene Transkript-
Provenienzen in einem gemeinsamen Dokument und eine verifizierte Zuordnung zu einem
Video. Die Existenz einer URL bestätigt keine Echtheit. RAG-Payloads, Visual-Rebuild-
Ergebnisneukonstruktionen und externe Exporte sind nicht Bestandteil dieses PRs und
müssen vor weitergehender Nutzung separat auf Metadatenverlust geprüft werden.

## Offline-Tests

Tests in test_knowledge_transcript_provenance.py: Konstruktion/JSON-Roundtrip für
alle in der Laufzeit unterstützten Herkunftswerte, tatsächlicher Extraction-
Funktionskörper mit synthetischem Ergebnis, deterministische Consolidation,
semantische Materialisierung ohne echte Agenten/LLM-Aufrufe, semantischer Zweig ohne
Aussagen, Legacy-JSONs aller drei Dokumentmodelle sowie neun Konfliktfälle für
Sprache/URL/Medien-ID. Beide semantischen Zweige behalten die Metadaten.

Die Tests führen die echten Funktionskörper isoliert per AST aus. Konfiguration,
Dateilader und Agentgrenzen sind kontrollierte Test-Doubles; Modelle, Evidence-
Binding, Chunking, Consolidation und semantische Materialisierung sind real. Der
Extraction-Test verwendet bekannte Zeitwerte, keine erfundenen Medienzeiten für TXT.
Socket und DNS sind gesperrt. Die bestehende falsche Formel-Helper-Importquelle ist
im isolierten Namespace korrekt verknüpft; ihre unabhängige Korrektur bleibt PR #11.

Dieser PR baut auf PR #10 auf. Offizielle Herkunfts-Enums und der Offline-Importer
kommen aus PR #9; die Tests parametrisieren sämtliche bereits verfügbaren Enums,
sodass auf dem kombinierten Workspace auch official_transcript/official_subtitle
geprüft werden. Für produktive offizielle Importe sind #9 und #11 ebenfalls nötig.
Keine Downloads, Whisper-/LLM-Aufrufe, neuen Dependencies oder Änderungen an Discovery,
Selection und zeitbasiertem Chunking. Keine Migration vorhandener Daten.
