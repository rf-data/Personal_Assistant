# memory.py
from pathlib import Path
from pydantic import BaseModel, Field   # , ConfigDict
from typing import Any, Optional      # Callable, List, Dict
# from dataclasses import 
import logging
from datetime import datetime
# from dataclasses import dataclass, field

from src.core.pdf_extractor import PDFCleanExtractor
from src.core.text_structure_builder import TextStructureBuilder
from src.core.feature_enricher import FeatureEnricher
from src.core.pdf_classifier import PDFClassifier
from src.core.text_classifier import TXTClassifier
# from src.core._dev_block_classifier import BlockClassifier
from src.core.pdf_cleaner import PDFCleaner
from src.core.document_assembler import DocumentAssembler

from tiktoken import encoding_for_model
# import json

# import utils.general_helper as ph

class SessionState(BaseModel):
    timestamp: datetime|str|None = Field(default=None)
    env_loaded: list[str] = Field(default_factory=list)
    suffix: str = Field(default_factory=str)
    save_folder: str | Path = Field(default_factory=str)
    save_name: str | Path = Field(default_factory=str)
    

class Session():

    # def __init__(self):
    state = SessionState()
    logger = logging.getLogger(__name__)
    extractor: Optional[PDFCleanExtractor]
    builder: Optional[TextStructureBuilder]
    enricher: Optional[FeatureEnricher]      # field(default_factory=)
    cleaner: Optional[PDFCleaner]
    classifier: Optional[PDFClassifier, TXTClassifier]
    assembler: Optional[DocumentAssembler]
    model_config: dict={}
    encoder = encoding_for_model
    # ConfigDict(arbitrary_types_allowed=True)

session = Session()


class SimpleMemory:
    def __init__(self):
        self._store = {}
 
    def save(self, key: str, value: Any):
        self._store[key] = value
 
    def load(self, key: str) -> Any:
        return self._store.get(key)
    
    def keys(self):
        return list(self._store.keys())
    
    # as lazy import to prevent circular imports
    # import src.utils.path_helper as ph
    # root = ph.find_project_root()

    # model_config = 

    # logger: logging.Logger = Field(default_factory=lambda: logging.getLogger(__name__))
    # preprocessor: "TextPreprocessor" = Field(default_factory=TextPreprocessor)
    # now: datetime = Field(default_factory=datetime.now)
    # env_loaded: Optional[List[str]] = Field(default_factory=list)

# class LLM_State(BaseModel):
#     logger: 
#     preprocessor:  
#     now = 

    
    #############


#     def __init__(self):
#         # as lazy import to prevent circular imports
#         import src.utils.path_helper as ph

#         # --- runtime / env ---
#         self.env = None
#         self.branch = None
#         self.root = ph.find_project_root()
#         self.venv = None
#         self.url_repo = None
#         self.backup_dir: str | Path | None = None
        
#         self.logger = None
#         self.cleaner = None
#         self.now = None
#         self.df_name = None
#         self.save_folder = None
#         self.model_class = None

#         # --- 'general' parameters ---
#         self.gen_params: Dict[str, Any] | None = None
#         # self.num_feats: List | None = None
#         # self.cat_feats: List | None = None
#         # self.log_name: str | None = None        # name of logger
#         # self.log_file: str | None = None        # name logger file

#         # --- 'experiment-related' parameters ---
#         self.exp_params: Dict[str, Any] | None = None
#         # self.h3_idx: str | None = None
#         # self.split_method: str | None = None
#         # self.features: List | None = None
#         # self.n_splits: int | List | None = None

#         # --- 'preparation-related' parameters ---
#         self.prep_params: Dict[str, Any] | None = None
#         # self.inflate: bool | None = None
#         # self.encode: Dict | None = None
#         # self.h3_values: int | List | None = None
#         # self.cols_needed: str | List | None = None
#         # self.frequence: str | None = None
#         # self.plotting: List | None = None

#         # --- 'SQL-related' parameters ---
#         self.sql_params: Dict[str, Any] | None = None
#         # self.p_key: str | None = None
#         # self.scheme: str | None = None
#         # self.src_table: str | None = None
#         # self.tmp_tbl: str | None = None

#         self.env_loaded = False
#         self.env_audit_agent_loaded = False

#     # ---------- configuration ----------
#     def load_config(self, config: Dict[str, Any]):
#         """Load relevant configuration / settings into session."""

#         # self.gen_params = config.get("general_parameters", None)
#         # self.sql_params = config.get("sql_parameters", None)
#         # self.exp_params = config.get("experiment_parameters", None)
#         # self.prep_params = config.get("preparation_parameters", None)

#         # # --- 'general' properties ---
#         # self.num_feats = config.get("num_feats", None)
#         # self.cat_feats = config.get("cat_feats", None)
#         # self.log_name = config.get("log_name", None)
#         # self.log_file = config.get("log_file", None)

#         # # --- 'FeatEng', 'EDA' and 'TrainPrep' ---
#         # self.encode = config.get("encode", None)
#         # self.h3_values = config.get("h3_values", None)
#         # self.cols_needed = config.get("cols_needed", None)
#         # self.frequence = config.get("freq", None)
#         # self.plotting = config.get("plotting", None)
#         # self.h3_idx = config.get("h3_idx", None)
#         # self.split_method = config.get("split_method", None)
#         # self.features = config.get("features", None)
#         # self.n_splits = config.get("n_splits", None)

#         # # --- 'SQL-relevant' properties ---
#         # self.p_key = config.get("p_key", None)
#         # self.scheme = config.get("scheme", None)
#         # self.src_table = config.get("src_table", None)
#         # self.tmp_tbl = config.get("tmp_tbl", None)
#         # self.inflate = config.get("inflate", False)

#     # ---------- persistence ----------
#     def save_session(self):
#         if self.root is None:
#             raise RuntimeError("Session.root must be set before saving session.")
#         file_path = Path(self.root) / ".env.session"

#         state = {
#             "SESSION_ENV": self.env if self.env is not None else None,
#             "SESSION_BRANCH": self.branch if self.branch is not None else None,
#             "SESSION_ROOT": str(self.root) if self.root is not None else None,
#             "SESSION_VENV": str(self.venv) if self.venv is not None else None,
#             "SESSION_URL_REPO": self.url_repo if self.url_repo is not None else None,
#             "SESSION_BACKUP_DIR": (
#                 self.backup_dir if self.backup_dir is not None else None
#             ),
#         }

#         with open(file_path, "w") as f:
#             for key, value in state.items():
#                 f.write(f"{key}={value}\n")

#     # def save_snapshot(self, folder=None):
#     #     """Save full experiment snapshot (for MLflow / debugging)."""
#     #     # lazy import to prevent circular imports
#     #     import utils.file_helper as fh

#     #     if self.root is None:
#     #         raise RuntimeError("Session.root must be set before saving snapshot.")

#     #     if folder is None:
#     #         folder = Path(f"{self.backup_dir}/{self.experiment_name}")

#     #     snapshot_path = folder / f"{self.now}_session_snapshot.json"

#     #     snapshot = {
#     #         "experiment_name": self.experiment_name,
#     #         "artifacts_location": self.artifacts_location,
#     #         "llm_model": self.llm_model,
#     #         "mode": self.mode,
#     #         "namespace": self.namespace,
#     #         "now": self.now,
#     #         "tags": self.tags,
#     #         "parameters": self.parameters,
#     #         "prompt": self.prompt,
#     #         "allowed_values": self.allowed_values,
#     #         "json_scheme": self.json_scheme,
#     #         "dep_function": self.dep_function,
#     #         "dep_function_name": self.dep_function_name,
#     #         "run_time": self.run_time,
#     #         "preprocess_function": self.preprocess_function
#     #     }

#     #     fh.save_dict(snapshot_path, snapshot)


# session = Session()
