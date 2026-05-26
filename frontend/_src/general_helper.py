# imports
import hashlib

# from src.schema.aggregation_schema import (AggregatedResult,
#                                            LLMAggregatedResult)
import inspect

# import numpy as np
import subprocess
from collections.abc import Callable, Iterable

from dotenv import find_dotenv, load_dotenv

from src.core.memory import session


def pretty_print(result):

    if isinstance(result, AggregatedResult):
        data = result.model_dump()
    elif isinstance(result, dict):
        data = result

    for key, value in data.items():
        print(f"\n=== {key.upper()} ===")

        if isinstance(value, list):
            for i, item in enumerate(value, 1):
                print(f"{i}. {item}")

        else:
            print(value)

        print()

    return


def pretty_logging(result):
    logger = session.logger

    if isinstance(result, (AggregatedResult, LLMAggregatedResult)):
        data = result.model_dump()
    elif isinstance(result, dict):
        data = result
    else:
        raise ValueError("Unknown dtype of 'result':", type(result))

    for key, value in data.items():
        logger.info("\n=== %s ===", key.upper())

        if isinstance(value, list):
            for i, item in enumerate(value, 1):
                logger.info("value #%s: %s", i, item)

        else:
            logger.info("value: %s", value)

        logger.info("")

    return


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

    env_loaded = session.state.env_loaded
    name_clear = [n for n in name if n not in env_loaded]

    for env in name_clear:
        env_path = find_dotenv(filename=env)
        if env_path:  #  and not session.env_loaded:
            load_dotenv(env_path)
            print(f"Variables loaded from '{env}'")
            env_loaded.append(env)

    session.state.env_loaded = env_loaded

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
