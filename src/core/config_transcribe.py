## config.py
# import
from typing import Annotated, Literal  # Dict,
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# from src.core.memory import session_state
# from src.utils.general_helper import load_env_vars
# from src.utils.dict_helper import get_yaml_config

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
                ] = "medium" # später: "large-v3"

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
    format: str = "bestaudio/best"

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
    
    
