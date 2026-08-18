## run_knowledge_extraction.py
# imports
from src.tools_knowledge.find_knowledge import (
                                    build_transcript_chunks,
                                    enrich_chunks, 
                                    classify_chunk_knowledge
                                    )

def run_math_retrieval(context: KnowledgeContext):


    chunks = build_transcript_chunks(context)
    chunks_enriched = enrich_chunks(chunks)
    
    for chunk in chunks_enriched:

        text_chunks = {
                "previous_chunk": chunk.previous_context_context,
                "chunk": chunk.text,
                "next_chunk": chunk.next_context
                }

        classify_chunk_knowledge(text_chunks) 
        # is True:
        #     chunk = ""
        #     hi = !
        

    # if doc_rep: # BaseModel subclass = 
    #     hi = !

    # for chunk in chunkdoc_rep.segments:


    return 


"""
Skizze Pipeline:
JSON transcript
      ↓
LLM extraction
      ↓
Math candidates + timestamps
      ↓
ffmpeg
      ↓
frames
      ↓
formula OCR
      ↓
LLM validation / fusion
      ↓
structured knowledge JSON


1. RAW
   TranscriptSegment

2. EXTRACTION
   erkannte Begriffe, Formeln, Reaktionen, Aussagen

(
2.5 PREPARATION NORMALIZATION
    Chemical OCR / structure recognition / SMILES normalization
    Math OCR / LaTeX normalization
)

3. NORMALIZATION
   canonical entities + relations

4. KNOWLEDGE
   VectorDB + optional GraphDB

####

Bsp.-Knowledge-JSON:
{
  "name": "Cosinussatz",
  "kind": "formula",
  "latex": "b^2 = a^2 + c^2 - 2ac\\cos(\\beta)",
  "plain_text": "Quadrat von b gleich a² plus c² minus 2ac mal Cosinus beta",
  "segment_ids": [92, 93],
  "start": 245.16,
  "end": 256.16,
  "source": "transcript+visual"
}
"""



