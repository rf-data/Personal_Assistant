# imports
import hashlib
import inspect

# import numpy as np
import json

# from src.schema.aggregation_schema import (AggregatedResult,
#                                            LLMAggregatedResult)
import subprocess
from collections.abc import Callable, Iterable
from dataclasses import is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from dotenv import find_dotenv, load_dotenv
from pydantic import BaseModel

from src.core.config import parsing_env_vars
from src.core.memory import app_session
from src.utils.path_helper import ensure_dir  # , shorten_path

## USE STANDARD_LIBRARIES --> csv, json, configparser, ipaddress, sqlite3, heapq, bisect...

# def inspect_function(fn: Callable):
#     print(inspect.getsource(fn))

#     return


def iter_chunks(df, chunk_size=25):
    for start in range(0, len(df), chunk_size):
        yield df.iloc[start : start + chunk_size]


def load_env_vars(name: list | str = ".env"):
    """
    Load environment variables from .env files if available.
    """
    # session_path = find_dotenv(filename=".env.session")
    # if session_path and os.path.exists(session_path):
    #     load_dotenv(session_path, override=True)
    #     print("Variables from .env.session loaded")

    if isinstance(name, str):
        name = [name]

    env_loaded = app_session.env_loaded
    name_clear = [n for n in name if n not in env_loaded]

    for env in name_clear:
        env_path = find_dotenv(filename=env)
        if env_path:  #  and not session.env_loaded:
            load_dotenv(env_path)
            print(f"Variables loaded from '{env}'")
            env_loaded.append(env)

    app_session.env_loaded = env_loaded

    return


####################
# ANALYZE_FUNCTIONS
####################


def inspect_single_function(fn: Callable) -> dict:
    src = inspect.getsource(fn)
    return {
        "all": src,
        "name": fn.__name__,
        "qualname": fn.__qualname__,
        "module": fn.__module__,
        "source": src,
        "sha256": hashlib.sha256(src.encode("utf-8")).hexdigest(),
    }


def snapshot_dependent_functions(
    root_fn: Callable,
    dependencies: Iterable[Callable] | None = None,
) -> dict:
    snapshot = {
        "root": inspect_single_function(root_fn),
        "dependencies": {},
    }

    if dependencies:
        for dep in dependencies:
            snapshot["dependencies"][dep.__name__] = inspect_single_function(dep)

    return snapshot


def make_doc_id(
    name: str, 
    mode: Literal["file_path", "text"] = "file_path", 
    short: bool = True
) -> str:

    # ! TODO: Combine with fn below

    if mode == "file_path":
        stem = Path(name).stem.lower().strip()
        doc_id = hashlib.sha256(stem.encode("utf-8")).hexdigest()

    elif mode == "text":
        doc_id = hashlib.sha256(name.encode("utf-8")).hexdigest()

    else:
        raise ValueError("Unknown value in 'mode':\t", mode)

    if short:
        return doc_id[:16]

    return doc_id


def hash_text(text: str, short: bool = True) -> str:
    value = hashlib.sha256(
        text.strip().encode("utf-8")
    ).hexdigest()

    return value[:16] if short else value


def make_doc_id_by_content(file_path: str) -> str:
    h = hashlib.sha256()

    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)

    return h.hexdigest()  # [:16]


###################
# CACHING
###################


def make_cache_key(
    url: str = None, params: dict = None, message: str = None, model: str = None
) -> str:
    payload = {}

    for arg_name, arg in [
        ("url", url),
        ("params", params),
        ("message", message),
        ("model", model),
    ]:
        if arg is not None:
            payload.update({arg_name: arg})

    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)

    # h =
    # h.update(url.encode("utf-8"))

    # for key, value in params.items():
    #     dict_text = f"{key}_{value}"
    #     h.update(dict_text.encode("utf-8"))

    # h.update(namespace.encode("utf-8"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def save_to_cache(
            key: str,
            folder: str | Path,
            data: dict,
            metadata: dict | None = None,
            ):
    cache_dir = parsing_env_vars.cache_dir

    fn = Path(cache_dir) / folder / f"{key}.json"
    ensure_dir(fn)

    payload = {
        "metadata": {
            "created_at":datetime.now().isoformat(),
            **(metadata or {}),
            },
        "result": data
        }

    with open(fn, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    app_session.logger.info("Saved cached data (key=%s).", key)

    return


def load_from_cache(key: str, folder: str | Path, cls=None):
    cache_dir = parsing_env_vars.cache_dir

    fn = Path(cache_dir) / folder / f"{key}.json"
    ensure_dir(fn)

    if not fn.exists():
        return None

    app_session.logger.info("Loaded cached data (key=%s).", key)

    with open(fn) as f:
        data = json.load(f)

    if isinstance(data, dict) and "result" in data:
        data = data["result"]

    if cls is None:
        return data

    if isinstance(data, list):
        if issubclass(cls, BaseModel):
            return [cls.model_validate(item) for item in data]

        if is_dataclass(cls):
            return [cls(**item) for item in data]

        raise TypeError(f"Cannot deserialize list items into {cls!r}")

    if isinstance(data, dict):
        if isinstance(cls, type) and issubclass(cls, BaseModel):
            return cls.model_validate(data)

        if isinstance(cls, type) and is_dataclass(cls):
            return cls(**data)

    # if issubclass(cls, BaseModel):
    #     return cls.model_validate(data)

    # if :
    #     return cls(**data)

    return data


def get_file_config(config_root: Any, file_type: str) -> Any:
    try:
        return getattr(config_root, file_type)
    except AttributeError as exc:
        raise ValueError(
            f"No config found for file_type='{file_type}' "
            f"in {type(config_root).__name__}"
        ) from exc


###################
# GIT_FUNCTIONS
###################


def get_git_difference():
    diff = subprocess.check_output(["git", "diff", "--stat"])
    print(diff.decode())
    return


def git_stats():
    commits = (
        subprocess.check_output(["git", "rev-list", "--count", "HEAD"]).decode().strip()
    )
    return {"commits": commits}


# print(git_stats())


def get_git_commit():
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode("utf-8")
            .strip()
        )
    except Exception:
        return "unknown"


# def pretty_print(result):

#     if isinstance(result, AggregatedResult):
#         data = result.model_dump()
#     elif isinstance(result, dict):
#         data = result

#     for key, value in data.items():

#         print(f"\n=== {key.upper()} ===")

#         if isinstance(value, list):
#             for i, item in enumerate(value, 1):
#                 print(f"{i}. {item}")

#         else:
#             print(value)

#         print()

#     return


# def pretty_logging(result):
#     from src.core.memory import session

#     logger = session.logger

#     if isinstance(result, (AggregatedResult,
#                            LLMAggregatedResult)):
#         data = result.model_dump()
#     elif isinstance(result, dict):
#         data = result
#     else:
#         raise ValueError("Unknown dtype of 'result':", type(result))

#     for key, value in data.items():

#         logger.info("\n=== %s ===",
#                     key.upper())

#         if isinstance(value, list):
#             for i, item in enumerate(value, 1):
#                 logger.info("value #%s: %s",
#                             i,
#                             item)

#         else:
#             logger.info("value: %s",
#                         value)

#         logger.info("")

#     return


# def describe_function(fn):
#     return {
#         "module": fn.__module__,

#         "name": fn.__name__,
#     }


# def hash_function_source(fn) -> str:
#     src = inspect.getsource(fn)
#     return src, hashlib.sha256(src.encode("utf-8")).hexdigest()


"""
checks = [
    ["python", "-m", "compileall", "."],
    ["pytest"],
]

for cmd in checks:
    if subprocess.call(cmd) != 0:
        print("❌ Check failed:", cmd)
        sys.exit(1)

print("✅ All checks passed.")
"""
