# Abgeleiteter CS50-Transcript-Suchindex

Entwicklungsbasis: origin/master 4dcd3c781b089fcc3939d0a7301e60033a418700;
#38 und die Abschlussänderungen #27–#37 sind integriert. Die bestehende
Dokumentationsstruktur wird ergänzt, ohne neue Archivierung oder lokale Bereinigung.

```mermaid
flowchart LR
  A[Discovery / SRT-first / Adapterplan] --> B[CS50Executor: Download und Import]
  B --> C[Geprüfte portable Inputbindung]
  C --> D[Originaler zeitbasierter Chunker]
  D --> E[Versionierte Embedding-Textfenster]
  E --> F[Lokale Embeddings / immutable Vektorartefakt]
  F --> G[Geprüfter Qdrant-Upsert und Readback]
  G --> H[Gefiltertes Retrieval / Originalquellenabgleich]
  H --> I[Manuelle fachliche Evaluation]
```

Die SRT-/Transcriptdateien sind das Quellenarchiv. Qdrant ist ein abgeleiteter,
ersetzbarer Index. LLM-Extraction ist für Transcript-Retrieval nicht erforderlich.
Das künftige Knowledge-Mapping ist separat und führt keine Collectionbefüllung aus.

| Stufe | Neue kleine Adapter | Wiederverwendeter Kern |
|---|---|---|
| Sources | tools_rag/cs50_orchestration.py | CS50Executor, SRT-Importer, bestehender 100-Task-Plan |
| Bindung/Chunks | tools_rag/cs50_embeddings.py | bind_cs50_knowledge_input, load_knowledge_transcript, build_cs50_knowledge_chunks |
| Indexvertrag | model_discovery/cs50_index.py | Pydantic und vorhandener Contract/Fingerprint |
| Collection | tools_rag/cs50_collection.py | isolierter qdrant-client, ohne Cloud-Inference |
| Plan/Vektoren/Upsert | tools_rag/cs50_ingestion.py | originale Sources/Belege, atomare Dateien und explizite Pfade |
| Suche | tools_rag/cs50_retrieval.py | echte query_points-Filter, Source-Revalidierung |
| Evaluation | tools_rag/cs50_retrieval_evaluation.py | echte geprüfte Transcriptsegmente |
| Knowledge-Vertrag | tools_rag/cs50_knowledge_index.py | reguläre Knowledge-Ergebnis- und Checkpointmodelle |

Pfade sind relativ zu src/. Die bisherigen Chroma-/App-Embeddingloader und der
Cloud-Inference-Qdranthelper werden wegen ihrer Seiteneffekte nicht aufgerufen.
Die bestehende E5-Modellwahl und normalisierte SentenceTransformer-Konvention
bleiben erhalten; die SDKs werden erst bei tatsächlicher Nutzung importiert.

Originale Chunks bleiben unverändert einschließlich Überlappung und IDs. Zu lange
Texte werden in exakte Zeichenoffset-Fenster mit überprüften Tokenlimits geteilt.
Jedes Fenster erhält den Originalchunk, konkrete Cue-Referenzen und konservative
Originalzeiten; keine interpolierten Zeiten. Ein leeres Cue erzeugt keinen Inhalt.

Der Plan bindet sämtliche Source-, Receipt-, Transcript-, Chunkplan-, Schema- und
Embeddingversionen. Unbekannte/veraltete Points oder ersetzte Sources in derselben
Kurswoche blockieren Wiederaufnahme. Keine automatische Löschung oder Migration.
Readback prüft tatsächliche Payloads und Vektoren; eine erfolgreiche API-Antwort
allein gilt nicht als Completion. Single-Writer-Lock setzt einen gemeinsam benutzten
Statuspfad voraus; verteilte Multi-Writer-CAS wird nicht behauptet.

Alle externen Schritte sind getrennte CLI-Freigaben. Remote-Qdrant verlangt TLS,
Authentifizierung und --allow-remote; reale Downloads verlangen Lizenzbestätigung.
Original-IDs, Woche 0, Abschnitt ai und cybersecurity media_id=null bleiben erhalten.
Keine unnötigen absoluten Sourcepfade oder Zugangsdaten im Indexpayload.
