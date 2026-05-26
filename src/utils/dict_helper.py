# import yaml
import inspect
import json
import os
import re
from pathlib import Path

# import torch
# import joblib
import numpy as np

# from datetime import datetime
# from functools import reduce
# import io
# import ast
import yaml
from pydantic import BaseModel

# import src.core.logger as log
from src.core.memory import session_state

# import hashlib
from src.utils.general_helper import snapshot_single_function
from src.utils.path_helper import ensure_dir, shorten_path


# -----------------------
# CONFIGURATION METHODS
# -----------------------
def load_yaml_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


def get_yaml_config(name):
    # (1) load config + logger
    # gh.load_env_vars()
    # logger = session.logger

    config_folder = os.getenv("CONFIG_PATH")

    config_path = Path(config_folder) / f"{name}.yaml"

    print(f"Loading config_file: {shorten_path(config_path)}")

    config = load_yaml_config(config_path)

    return config


# ---------------------
# DICT / JSON METHODS
# ---------------------
def safe_json_loads(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # try extracting text from JSON
        match = re.search(r"\{.*\}", ext, re.DOTALL)
        if match:
            return json.loads(match.group())

        raise ValueError("Invalid JSON:\n", text)


def make_json_safe(obj):
    if isinstance(obj, dict):
        return {str(k): make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [make_json_safe(v) for v in obj]
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, Path):
        return str(obj)
    if inspect.isfunction(obj):
        return snapshot_single_function(obj)
    # if isinstance(obj, torch.Tensor):           # Tensor handling
    #     return obj.detach().cpu().numpy().tolist()
    # if isinstance(obj, torch.device):
    # return str(obj)
    return str(obj)


def save_base_model_as_dict(data: BaseModel, path: Path) -> None:

    data_dict = data.model_dump()

    return save_dict(data_dict, path)


def save_dict(data: dict, path: Path) -> None:
    logger = session_state.logger

    f_path = Path(f"{path}.json")
    f_path = ensure_dir(f_path)
    data_new = make_json_safe(data)

    with f_path.open("w", encoding="utf-8") as f:
        try:
            json.dump(
                data_new,
                f,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            logger.info("Dict saved as %s", shorten_path(f_path, 3))

        except TypeError as e:
            logger.error(
                "ERROR (non_serializable):\n%s\n\ndtype=%s\nrepr=%s",
                e,
                type(data_new),
                repr(data_new),
            )


def append_json(data: dict, path: Path) -> None:

    path = ensure_dir(path)
    data_new = make_json_safe(data)

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data_new) + "\n")
        print(f"Appending data on {shorten_path(path, 3)}")


def load_dict(path: Path | str) -> dict:
    logger = session_state.logger

    path = ensure_dir(path)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        logger.info("Dict loaded:\t%s", shorten_path(path, 3))

    return data


def load_base_model_from_dict(path: Path | str, model_class: BaseModel):

    data_dict = load_dict(path)

    return model_class.model_validate(data_dict)


# # -----------------
# # MODEL METHODS
# # -----------------
# def save_model(model, name):
#     # setup logger
#     logger = session.logger

#     #
#     folder = os.getenv("PATH_MODEL")
#     model_path = Path(f"{folder}({name}.joblib)")
#     joblib.dump(model, model_path)

#     logger.info("Model saved as %s", ph.shorten_path(model_path))

#     return


# def load_model(name):
#     # setup logger
#     logger = session.logger

#     #
#     folder = os.getenv("PATH_MODEL")
#     model_path = Path(f"{folder}({name}.joblib)")
#     model = joblib.load(model_path)

#     logger.info("Model loaded from %s", ph.shorten_path(model_path))

#     return model


# # ---------------------
# # (C) DF PREVIEW / EDA
# # ---------------------


# def info_as_string(df):
#     buffer = io.StringIO()
#     df.info(buf=buffer)
#     return buffer.getvalue()


# # -----------------
# # TEXT METHODS
# # -----------------


# def save_text(path: Path, data: str):
#     # make_text_safe(data)
#     data_new = str(data)
#     with open(path, "w", encoding="utf-8", newline="\n") as f:
#         f.write(data_new)
#     print(f"Text file saved as {ph.shorten_path(path, 3)}")


# """
# logger.log_text(
#     "red_flags.yaml",
#     yaml.safe_dump(RED_FLAGS, sort_keys=True, allow_unicode=True)
# )
# """
