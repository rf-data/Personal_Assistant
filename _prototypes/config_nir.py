## config.py
# import
from typing import Annotated, Literal  # Dict,
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# from src.core.memory import session_state
# from src.utils.general_helper import load_env_vars
# from src.utils.dict_helper import get_yaml_config


class NIRSettigs(BaseModel):
    n_pca_comps: int = Field(default_factory=int)
    q_quantile: float = Field(default_factory=float)
    t2_quantile: float = Field(default_factory=float)

    sg_deriv: int = Field(default_factory=int)
    sg_poly: int = Field(default_factory=int)
    sg_window_len: int = Field(default_factory=int)
