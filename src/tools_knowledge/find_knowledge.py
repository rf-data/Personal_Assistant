## find_knowledge.py
# imports

from src.model_knowledge.data_knowledge import TranscriptChunk
from src.model_transcribe.data_transcribe import TranscriptSegment
from src.core.memory_knowledge import KnowledgeContext
                                       

def build_transcript_chunks(
    context: KnowledgeContext
    ) -> list[TranscriptChunk]:

    transcript = context.transcript     # TranscriptDocument,
    dur_target = context.target_duration   # float = 45,
    # dur_max = context.max_duration         # float = 75
    seg_overlap = context.overlap_segments  # : int = 2

    current: list[TranscriptSegment] = []
    final: list[TranscriptChunk] = []

    for seg in transcript.segments:
        current.append(seg)

        current_dur = current[-1].end - current[0].start

        # if current_dur >= dur_max:
        #     # harter Cut

        # elif current_dur >= dur_target:
        #     # bevorzugter Cut, ggf. auf Themenwechsel warten
            
        if current_dur >= dur_target:
            final.append(
                    TranscriptChunk(
                            chunk_id=f"chunk_{len(final):04d}",
                            segment_ids=[s.seg_id for s in current],
                            start=current[0].start,
                            end=current[-1].end,
                            text="\n".join(s.text for s in current),
                            n_words=sum(
                                    len(s.text.split())
                                    for s in current
                                    )
                            )
                    )

            current = current[-seg_overlap:]

    if current:
        existing_ids = set(
                    final[-1].segment_ids
                    if final
                    else []
                    )
        new_ids = {s.seg_id for s in current}

        if not new_ids.issubset(existing_ids):
            final.append(
                    TranscriptChunk(
                            chunk_id=f"chunk_{len(final):04d}",
                            segment_ids=[s.seg for s in current],
                            start=current[0].start,
                            end=current[-1].end,
                            text="\n".join(s.text for s in current),
                            n_words=sum(
                                    len(s.text.split())
                                    for s in current
                                    )
                            )
                    )

    return final    


def enrich_chunks(
            chunks: list[TranscriptChunk]
            ) -> list[TranscriptChunk]:

    n_chunks = len(chunks)

    for idx, chunk in enumerate(chunks):

        # previous_context = "\n".join(
        #     chunks[idx - 1].text.splitlines()[-3:]
        #     )

        # next_context = "\n".join(
        #     chunks[idx + 1].text.splitlines()[:3]
        #     )

        chunk.previous_context = (
                            chunks[idx-1].text 
                            if idx > 0 
                            else None
                            )
        chunk.next_context = (
                            chunks[idx+1].text 
                            if idx < n_chunks 
                            else None
                            )
    
    return chunks



def classify_chunk_knowledge(
                text_chunks: dict[str, str]    
                # ) -> KnowledgeCandidate:
                ):

    # TODO: 
    """
    TranscriptChunk
        ↓
    KnowledgeCandidate
        ↓
    relevant?
    ┌────┴────┐
    no       yes
    ↓         ↓
    skip    Extractor


    KnowledgeCandidate(
        has_knowledge=True,
        domains=["mathematics"],
        knowledge_types=[
            "formula",
            "law",
            "derivation",
        ],
        needs_visual_context=True,
        confidence=0.98,
        )

    class ChunkAnalysis(BaseModel):
        contains_math: bool
        contains_formula: bool
        formula_reconstruction_needed: bool
        visual_context_likely_needed: bool
        topic: str | None

    LLM enrichment
      ├─ sprachliche Bereinigung
      ├─ mathematischer Inhalt?
      ├─ Formeln / Symbole?
      ├─ visueller Kontext nötig?
      └─ Wissensextraktion
    """

    return 

"""

"""

def extract_chunk_knowledge() -> ExtractedKnowledge:


    return 

    #         # else: 
    #         #     hi = !
    #         start_segs = transcript.segments[idx-seg_overlap-1:idx-1]
    #         current.extend(start_segs)

    #         min_time = 1e5
    #         max_time = 0
    #         for start_s in start_segs:
    #             min_time = min(min_time, start_s.start)
    #             max_time = max(max_time, start_s.end)

    #         current_dur = max_time - min_time
    #         # (start_s.end - start_s.start)
    #         continue

    #     current.append(seg.text)
    #     current_dur += (seg.end - seg.start)


    # return 


