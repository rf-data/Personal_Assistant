# memory.py
from logging import Logger
from pydantic import BaseModel, Field, ConfigDict

from pydantic import Field

# from openai import OpenAI
from tiktoken import Encoding  # , encoding_for_model

from src.core.memory_parsing import ParseContext
from src.core.config import ChunkSettings, GeneralSettings, ParseSettings


# @dataclass
class AppSession(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )

    chunk_settings: ChunkSettings = Field(default_factory=ChunkSettings)
    encoder: Encoding | None = None  #  = encoding_for_model
    env_loaded: list[str] = Field(default_factory=list)
    general_settings: GeneralSettings = Field(default_factory=GeneralSettings)
    logger: Logger | None = None
    # logger: ClassVar = logging.getLogger(__name__)
    parse_settings: ParseSettings = Field(default_factory=ParseSettings)
    run_context: ParseContext = Field(default_factory=ParseContext)
    timestamp: str = Field(default_factory=str)

    # frontend_config: FrontendConfig


app_session = AppSession()


# class SimpleMemory:
#     def __init__(self):
#         self._store = {}

#     def save(self, key: str, value: Any):
#         self._store[key] = value

#     def load(self, key: str) -> Any:
#         return self._store.get(key)

#     def keys(self):
#         return list(self._store.keys())

# simple_memory = SimpleMemory()

# simple_memory = SimpleMemory()
