# Embedding-Konfiguration und Offset-Segmentierung v1

Die vorhandenen aktiven RAG-Einstiege verwenden multilingual-e5-base; dieses Modell
bleibt gewählt. Vergleich der offiziellen Modellkarten: E5 768 Dimensionen / 512
Tokens, multilingual; MiniLM-L6-v2 384 / standardmäßig 256, überwiegend Englisch.
E5 verlangt query: bzw. passage: auch für englische Inhalte. Beide normalisiert.
CPU-Geschwindigkeit, Peak-RAM und fachliche CS50-Retrievalqualität sind hier **nicht
gemessen**; keine Gewichte lokal verfügbar. Weniger Dimensionen/kleinerer Encoder
legen geringeren Ressourcenbedarf bei MiniLM nahe, sind kein gemessener Vorteil.
Batchdefault 16 folgt dem vorhandenen Encodingpfad; die Konfiguration ist gehasht.

Der lokale Adapter nutzt dieselbe SentenceTransformer-Encoding-Konvention, aber
local_files_only=True, immutable Revision, CPU und trust_remote_code=False.
Keine Chroma-/App-Initialisierung durch das reine Embeddingmodul. Ohne vorab
bereitgestellte Gewichte/Library schlägt echte Inferenz verständlich fehl; Fake
bleibt ausdrücklich cs50-test-hash und wird nicht als E5/semantische Qualität bezeichnet.

offset_windows_v1 partitioniert Originaltext an tatsächlichen Token-Endoffsets.
Jede vollständige Präfix+Text-Eingabe einschließlich Special Tokens wird gegen das
Limit geprüft, niemals still gekürzt. Python-Character-Offsets referenzieren den
unveränderten Chunktext; keine Decoding-Rekonstruktion oder Textnormalisierung.
Originalchunk-ID, Text, Zeiten, Segmente und Konfiguration bleiben erhalten.
Units verwenden nur echte berührte nichtleere Cues, ihre konservativen Originalzeiten
(auch bei Teiltext innerhalb eines Cues), keine interpolierten Zeitmarken.
Bestehender Chunkoverlap bleibt über die mehrfach referenzierten Original-Cues
sichtbar; Units überschreiben keine Knowledge-Chunks.

Mapper revalidiert echten Executor-/Importbeleg über den bestehenden Binder,
verwendet load_knowledge_transcript und build_cs50_knowledge_chunks unverändert.
Receipt-, Inputbinding-, Raw-/Transcript- und vollständiger Chunkplanhash werden
erhalten. Qdrant-Payload enthält keine unnötigen absoluten Quelldateipfade;
Provenienzhash und separate portable Quellbindung erlauben Originalabgleich.

Quellen: [E5](https://huggingface.co/intfloat/multilingual-e5-base),
[MiniLM](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2).
