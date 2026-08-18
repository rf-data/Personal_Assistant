## dict_helper.py
#  import yaml
import inspect
import json
import re
from pathlib import Path
import numpy as np
import yaml
from pydantic import BaseModel
from dataclasses import is_dataclass

from src.core.config import GeneralSettings, RunSettings, parsing_env_vars
from src.core.memory import app_session
from src.utils.general_helper import inspect_single_function
from src.utils.path_helper import ensure_dir, shorten_path


# -----------------------
# CONFIGURATION METHODS
# -----------------------
def load_yaml_config(path: str | Path):
    with open(path) as f:
        return yaml.safe_load(f)


def load_yaml_as_base_model(path: str | Path, model: GeneralSettings | RunSettings):
    cfg_dict = load_yaml_config(path)

    return model.model_validate(cfg_dict)


def get_yaml_config(name: str, model: GeneralSettings | RunSettings | None = None):
    # (1) load config + logger
    # gh.load_env_vars()
    # logger = session.logger

    config_folder = parsing_env_vars.config_dir

    config_path = Path(config_folder) / f"{name}.yaml"

    print(f"Loading config_file: {shorten_path(config_path)}")

    if model is None:
        config = load_yaml_config(config_path)

    else:
        config = load_yaml_as_base_model(path=config_path, model=model)

    return config


# ---------------------
# DICT / JSON METHODS
# ---------------------
def safe_json_loads(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # try extracting text from JSON
        match = re.search(r"\{.*\}", text, re.DOTALL)
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
        return inspect_single_function(obj)
    # if isinstance(obj, torch.Tensor):           # Tensor handling
    #     return obj.detach().cpu().numpy().tolist()
    # if isinstance(obj, torch.device):
    # return str(obj)
    return str(obj)


def save_dict(data: dict, path: Path) -> None:
    logger = app_session.logger

    f_path = path.with_suffix(".json")
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

        except (TypeError, OSError) as e:
            logger.error(
                "Could not save JSON: %s\n"
                "dtype=%s\nrepr=%s",
                e,
                type(data_new),
                repr(data_new)[:2000],
                )
            raise

def save_base_model_as_dict(data: BaseModel, path: Path) -> None:
    data_dict = data.model_dump()

    return save_dict(data_dict, path)


def append_json(data: dict, path: Path) -> None:
    logger = app_session.logger

    f_path = Path(f"{path}.json")
    path = ensure_dir(f_path)
    data_new = make_json_safe(data)

    with path.open("a", encoding="utf-8") as f:
        try:
            f.write(json.dumps(data_new) + "\n")
            # print(f"Appending data on {shorten_path(path, 3)}")
            logger.info("Appending data on json_file in %s", shorten_path(f_path, 3))

        except TypeError as e:
            logger.error(
                "ERROR (non_serializable):\n%s\n\ndtype=%s\nrepr=%s",
                e,
                type(data_new),
                repr(data_new),
            )


def load_dict(path: Path | str, cls=None) -> dict:
    logger = app_session.logger

    path = ensure_dir(path)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        logger.info("Dict loaded:\t%s", shorten_path(path, 3))

    if cls is None:
        return data

    if isinstance(data, list):
        if isinstance(cls, type) and issubclass(cls, BaseModel):
            return [cls.model_validate(item) for item in data]
    
        if isinstance(cls, type) and is_dataclass(cls):
            return [cls(**item) for item in data]
    
        raise TypeError(f"Cannot deserialize list items into {cls!r}")
    
    if isinstance(data, dict):
        if isinstance(cls, type) and issubclass(cls, BaseModel):
            return cls.model_validate(data)
    
        if isinstance(cls, type) and is_dataclass(cls):
            return cls(**data)


# # -----------------
# # MODEL METHODS
# # -----------------
# def save_model(model, name):
#     # setup logger
#     logger = session.logger

#     #
#     folder = parsing_env_vars("PATH_MODEL")
#     model_path = Path(f"{folder}({name}.joblib)")
#     joblib.dump(model, model_path)

#     logger.info("Model saved as %s", ph.shorten_path(model_path))

#     return


# def load_model(name):
#     # setup logger
#     logger = session.logger

#     #
#     folder = parsing_env_vars("PATH_MODEL")
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
