# imports
import hashlib

# from src.schema.aggregation_schema import (AggregatedResult,
#                                            LLMAggregatedResult)
import inspect

# import numpy as np
import json
import os
import subprocess
from collections.abc import Callable, Iterable
from datetime import datetime
from pathlib import Path
from dotenv import find_dotenv, load_dotenv

from src.core.memory import app_session
from src.utils.path_helper import ensure_dir    # , shorten_path



def make_cache_key(url: str, params: dict) -> str:

    payload = {"url": url, "params": params}

    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)

    # h =
    # h.update(url.encode("utf-8"))

    # for key, value in params.items():
    #     dict_text = f"{key}_{value}"
    #     h.update(dict_text.encode("utf-8"))

    # h.update(namespace.encode("utf-8"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def save_to_cache(key: str, folder: str | Path, data: dict):

    cache_dir = os.getenv("CACHE_DIR")

    data["created_at"] = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    fn = Path(cache_dir) / folder / f"{key}.json"

    ensure_dir(fn)

    with open(fn, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger = app_session.logger
    logger.info("Saved cached data (key=%s).", key)

    return


def load_from_cache(key: str, folder: str | Path):

    cache_dir = os.getenv("CACHE_DIR")

    fn = Path(cache_dir) / folder / f"{key}.json"

    ensure_dir(fn)

    if fn.exists():
        logger = app_session.logger
        logger.info("Loaded cached data (key=%s).", key)

        with open(fn) as f:
            return json.load(f)

    return None


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


def snapshot_single_function(fn: Callable) -> dict:
    src = inspect.getsource(fn)
    return {
        "name": fn.__name__,
        "qualname": fn.__qualname__,
        "module": fn.__module__,
        "source": src,
        "sha256": hashlib.sha256(src.encode("utf-8")).hexdigest(),
    }


# def describe_function(fn):
#     return {
#         "module": fn.__module__,

#         "name": fn.__name__,
#     }


def snapshot_dependent_functions(
    root_fn: Callable,
    dependencies: Iterable[Callable] | None = None,
) -> dict:
    snapshot = {
        "root": snapshot_single_function(root_fn),
        "dependencies": {},
    }

    if dependencies:
        for dep in dependencies:
            snapshot["dependencies"][dep.__name__] = snapshot_single_function(dep)

    return snapshot


# def hash_function_source(fn) -> str:
#     src = inspect.getsource(fn)
#     return src, hashlib.sha256(src.encode("utf-8")).hexdigest()


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
