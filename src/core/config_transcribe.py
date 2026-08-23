## config_transcribe.py
# import
from pathlib import Path
from typing import Literal  
from pydantic import BaseModel     

TranscriptionBackend = Literal[
    "faster_whisper",
    "whisper_live",
    "cloud_stt",
]


class TranscribeSettings(BaseModel):
    backend: TranscriptionBackend = "faster_whisper"

    model_size: Literal[
                    "tiny",
                    "base",
                    "small",
                    "medium",
                    "large-v3",
                ] = "medium" # ? TODO: "large-v3"

    device: Literal["cpu", "cuda"] = "cpu"

    compute_type: Literal[
                    "int8",
                    "float16",
                    "float32",
                    "int8_float16",
                ] = "int8"

    cpu_threads: int = 6  # os.cpu_count()

    language: str | None = None

    vad_filter: bool=False


class DownloadSettings(BaseModel):
    # relevant for both
    no_playlist: bool = True
    playlist_items: str | None = None
    playlist_name: str|None = None
    
    quiet: bool = False

    socket_timeout: int = 30
    retries: int = 20
    fragment_retries: int = 20
    continue_download: bool = True
    ignore_errors: bool = True

    show_progress: bool = True
    
    cookie_file: Path | None = None

    # relevant for video 
    video_format: str = "bv/b"
    force_keyframes_at_cuts: bool = True
    padding: float = 2.0
    
    # relevant for audio
    audio_format: str = "bestaudio/best"


class ScreenshotSettings(BaseModel):
    image_format: str = "png"
    
    f_times_interval: float = 5.0
    min_distance: int = 2
    merge_gap: float = 2.0

    min_hash_distance: int = 5
    max_hash_distance: int = 20
    max_time_gap: float = 15.0


    # f_times_interval: float = 5.0