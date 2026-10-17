# C21-Q: Architektur und geprüfter Stand

Entwicklungsbasis: Backend-master `1c0b30771c02d377445fc58059d19ec605c776ed`,
Baum `9a38207a9b4688dbfa99bcd15f97d7afef5a4074`. Während der Arbeit wurde C21
gemergt; aktueller geprüfter PR-Zielstand ist
`01cbf3d6fb143773e08d3f7cc26b6695e8800203`
(Baum `5fe17d8a4eb6abf44121065a2ea886a3afa1424a`).
C21-Q benötigt keine ungemergten C21-Änderungen und führt keine zweite Pipeline ein.
Stand 17.10.2026: lokale Vorbereitung geliefert, Phase A wegen fehlender
Qdrant-Testumgebung **teilweise blockiert**; Phase B **blocked, keine Freigabe**.
Ein Deploymentvorschlag ist kein Nachweis einer laufenden Instanz.

```mermaid
flowchart LR
  A[Original-SRT und unveränderter Receipt] --> B[bind_cs50_knowledge_input]
  B --> C[Bestehender zeitbasierter Chunker]
  C --> D[Exact-Offset-Fenster und lokales E5]
  D --> E[IngestionPlan und VectorArtifact]
  E --> F[ensure_collection und upsert_plan]
  F --> G[Vollständiger Payload- und Vektorreadback]
  G --> H[Gefiltertes Retrieval und verify_hit]
  H --> I[Manuelle Relevanzbewertung]
```

| Implementiert auf master | Tatsächlich verfügbar / Grenze |
| --- | --- |
| `src/model_discovery/cs50_index.py` | EmbeddingConfig, CollectionContract, TranscriptPayload; kein neuer Businessvertrag |
| `src/tools_rag/cs50_embeddings.py` | Lokaler SentenceTransformer, unveränderte Texte, Offsetfenster, L2-Prüfung; FakeEmbedder ausdrücklich technisch |
| `src/tools_rag/cs50_collection.py` | Erstellung nur ausdrücklich; Dimension, Cosine, Metadaten, vier Keywordindizes |
| `src/tools_rag/cs50_ingestion.py` | Unveränderliche Quellen-/Vektorbindung, UUIDv5, Readback, Lock, Resume; keine impliziten Löschungen |
| `src/tools_rag/cs50_retrieval.py` | Source-/Course-/Lecture-/Sprachfilter, top_k 1–100, Originalverifikation |
| `src/tools_rag/cs50_retrieval_evaluation.py` | Zehn source-grounded Fragen, manuelle Urteile, gesperrte Fake-Qualitätswerte |
| `scripts/cs50_transcript_index.py` | Bestehende CLI; ergänztes Inventar und lokale Validierung, drei reine Aktionsaliase |
| C21-Q `cs50_pilot.py` | Read-only Metadaten-/Voraussetzungsbericht; keine zweite Chunk-/Uploadpipeline |

Der vorhandene Vertrag verwendet E5 `intfloat/multilingual-e5-base`, eine volle
40-stellige immutable Revision, 768 Dimensionen, Cosine, L2, 512 Tokens und exakt
`passage: ` / `query: `. Der Tokenizer muss fast sein. `LocalEmbedder` lädt nur
lokale Dateien, CPU und `trust_remote_code=False`; keine Gewichte wurden geladen.
Das [offizielle Modellblatt](https://huggingface.co/intfloat/multilingual-e5-base)
bestätigt Dimension, Präfixe und Normalisierung. Aktuell fehlen SDK, SentenceTransformers
und eine bereitgestellte Modellrevision; `torch==2.13.0+cpu` allein reicht nicht.
Das vorhandene isolierte Workerprofil pinnt `qdrant-client==1.19.1`; es wurde nicht
neu installiert. Neue Dependencies wurden nicht hinzugefügt.

Payload v1 enthält Course/Section/Lecture/Resource/Source/Media, Original-URL,
Raw-/Transcript-/Receipt-/Binding-/Provenienz-/Chunkplanhashes, Chunkingparameter,
Chunk-ID, echte Segment-IDs und Zeiten, Textfenster, Originalchunk und Versionen.
**Es enthält Text** (`text` und `original_chunk_text`). Freigabe nur für Vektoren
reicht daher nicht für den vorhandenen Upload. Rawdateien werden nicht übertragen.
Absolute lokale Quellpfade werden abgewiesen; aktuelle Modelle behalten normalisierte
`seg_id`, nicht die ursprüngliche numerische SRT-Cue-Beschriftung. Keine erfundenen IDs.

UUIDv5 bindet vollständigen Collectionvertrag, Source-/Transcript-/Chunkplan,
Chunk, Unitindex und Zeichenoffset. Neue Revision oder Schemaänderung benötigt
einen neuen Index. Ein praktikabler Name ist
`cs50_transcript_v1_e5base_r<12hex>_d768_cos_<16hex>`: erstes Fragment der
Modellrevision plus Fragment von `EmbeddingConfig.version`. Der vollständige
Vertrag bleibt in Collectionmetadaten und Payload gebunden; Namensfragmente sind
keine Validierung. Vor Erstellung Namen prüfen; kein Adoptions-/Löschpfad.

IngestionPlan und VectorArtifact sind JSON, private UploadState-Belege liegen
unter Collection-/Planhash im expliziten Statusroot. Ein gemeinsames POSIX-Lock
schützt einen Writer; verteiltes CAS wird nicht behauptet. Nach verlorener
Bestätigung verifiziert derselbe Upsert vorhandene Points und ergänzt fehlende.
Eine HTTP-Erfolgsantwort oder eine passende Pointzahl genügt nicht: Payload,
Vektoren und volle Sollmenge werden geprüft. Quellen werden vor jedem Schritt
erneut gebunden. Qdrant bleibt ein rekonstruierbarer Index, Originale bleiben maßgeblich.

Historische echte lokale Qdrant-Tests und Fake-Embeddings auf master stehen in
[transcript_index_completion.md](../cs50/operations/transcript_index_completion.md).
Diese Ergebnisse sind keine aktuelle Serverabnahme. Neu gemessen, tatsächlich
ausgeführt und blockiert sind getrennt im [Validierungsbericht](c21q_validation.md).
Deployment, Backup und dauerhafte Überwachung bleiben getrennte Betriebsfreigaben;
C22/C23 werden hier nicht vorweggenommen.
