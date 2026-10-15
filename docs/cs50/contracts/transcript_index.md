# Transcript-Indexvertrag v1

Basis: master 4dcd3c7; #38 integriert. Neue Contracts ergänzen ausschließlich den
abgeleiteten Suchindex, keine bestehenden Transcript-/Knowledge-Modelle.
Die Repositorysuche auf dieser Basis ergab keine Verwendung der neuen Namen
cs50_transcript_chunks_v1 und cs50_knowledge_items_v1. Eine externe produktive
Namensbelegung wurde nicht abgefragt. Vor einer später freigegebenen Verbindung
bleibt deshalb die strikte Collectionprüfung zwingend; keine Namensadoption.

`EmbeddingConfig` bindet Modell, immutable Commitrevision, Dimension, Tokenlimit,
L2-Normalisierung, Query-/Passage-Präfixe, unveränderten Text und versionierte
Offset-Segmentierung. SHA-256 der vollständigen Konfiguration ist embedding_version.
Fake-Konfigurationen tragen ausdrücklich cs50-test-hash/fake-v1 und sind keine
echten E5-Vektoren. Der im aktiven Legacy-RAG-Runner verwendete E5-Modellname bleibt
die Wahl; kein experimenteller Modellwechsel ohne gemessenen Vorteil.

`CollectionContract` bindet cs50_transcript_chunks_v1, Cosine, Embeddingkonfiguration,
Payloadschema und vier Keyword-Filterindizes. Der vollständige Vertrag liegt in
Qdrants Collection-Metadata (Server >=1.16). Vor jedem Zugriff werden Dimension,
Metrik und Metadaten geprüft. Fremde/inkompatible bestehende Collections werden
nie adoptiert, gelöscht oder neu angelegt. Neue Erstellung muss explizit erlaubt
sein. Im lokalen Client sind Payload-Indizes nicht implementiert; Filtersemantik
wird dort getestet, physische Indizes ausschließlich auf einem separat freigegebenen
Server. Keine produktive Verbindung in Offline-Tests.

required_payload_fields und der SHA-256 des vollständigen Pydantic-JSON-Schemas
sind Bestandteil des Collectionvertrags. Readback und Retrieval prüfen die
erforderlichen Felder vor Pydantic-Validierung: fehlende Versions-, Sprach- oder
media_id-Felder dürfen nicht durch Modeldefaults als gültig erscheinen. Der
Vertrag umfasst auch nullable Felder; null ist von einem fehlenden Feld verschieden.
Frühere experimentelle Vertragsstände werden ausdrücklich als inkompatibel
abgelehnt. Es gibt keine Migration oder Übernahme unbekannter Collectioninhalte.

`TranscriptPayload` erhält Kurs-/Lecture-/Ressourcen-/Quellenidentität, Original-URL,
Sprache, originale Chunkidentität/-text/-zeiten/-segmente, zusätzliche Textoffsets,
konkrete Cue-Teilmenge/-zeiten und alle Quellen-/Plan-/Beleghashes. Provenienz bleibt
inhaltlich gebunden; unnötige absolute source_file-Pfade werden nicht indexiert.
Die unveränderten SRT-/Transcript-Artefakte und portable Inputbindung bleiben
maßgeblich. UUIDv5-Point-IDs binden Source-, Transcript-, Chunkplan-, Unit- und
Collection-/Embedding-Version. Indexänderungen benötigen einen neuen expliziten
Indexstand; keine stillen Reindexing-/Aliaswechsel.

Bestehende Wiederverwendung: CS50Executor, bind_cs50_knowledge_input,
load_knowledge_transcript, build_cs50_knowledge_chunks, KnowledgeSettings,
TranscriptDocument/TranscriptSegment und Checkpoint-Contract/Fingerprints.
Die alte qdrant_helper verbindet Cloud-Inference und ist dafür ungeeignet.
Der alte Embeddingloader importiert Chroma/App-Konfiguration und kann Gewichte
laden; der neue kleine lokale Adapter muss diese Seiteneffekte vermeiden und die
bestehende normalisierte SentenceTransformer-Encoding-Konvention beibehalten.

SDK-Bereitstellung: qdrant-client 1.19.1 plus Root-Lock-Abhängigkeiten in isolierter
uv-Umgebung, regulärer Worker unverändert. Offline-Cache war unvollständig; nur
Python-Pakete wurden nach Freigabe bereitgestellt. Keine Modellgewichte verfügbar.

Referenzen: [Qdrant Collection-Metadata](https://qdrant.tech/documentation/manage-data/collections/#collection-metadata),
[E5 Modellkarte](https://huggingface.co/intfloat/multilingual-e5-base),
[MiniLM Modellkarte](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2).
