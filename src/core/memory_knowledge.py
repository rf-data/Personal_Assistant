## memory_knowledge.py
# import
from pydantic import BaseModel  # , Field, ConfigDict

from src.model_transcribe.data_transcribe import TranscriptDocument

class KnowledgeContext(BaseModel):
    transcript: TranscriptDocument,
    target_duration: float = 45
    max_duration: float = 75
    overlap_segments: int = 2
    