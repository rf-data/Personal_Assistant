# imports
import hashlib
import ast
# from src.schema.aggregation_schema import (AggregatedResult,
#                                            LLMAggregatedResult)
import re
import inspect
from typing import Any

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


######################
# DEPENDENCY_ANALYZER
######################

# import ast

# with open("module.py") as f:
#     tree = ast.parse(f.read())

# for node in ast.walk(tree):
#     if isinstance(node, ast.Import):
#         for name in node.names:
#             print(name.name)

# ######################
# # RETRY_FRAMEWORK
# ######################

# import time

# def retry(func, attempts=3):
#     for i in range(attempts):
#         try:
#             return func()
#         except Exception:
#             if i == attempts - 1:
#                 raise

#             time.sleep(2 ** i)

# ######################

# def extract_functions(file_path):
#     with open(file_path, "r") as f:
#         tree = ast.parse(f.read())
#     return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

# functions = extract_functions("app.py")
# for fn in functions:
#     print(f"Explain what `{fn}` does and why it exists.")



def get_file_config(
            config_root: Any, 
            file_type: str
            ) -> Any:
    try:
        return getattr(config_root, file_type)
    except AttributeError as exc:
        raise ValueError(
                f"No config found for file_type='{file_type}' "
                f"in {type(config_root).__name__}"
                ) from exc


def get_git_difference():
    diff = subprocess.check_output(["git", "diff", "--stat"])
    print(diff.decode())
    return 


def git_stats():
    commits = subprocess.check_output(
        ["git", "rev-list", "--count", "HEAD"]
    ).decode().strip()
    return {"commits": commits}
print(git_stats())


import ast
import os
'''
def find_unused_imports(path):
    for file in os.listdir(path):
        if file.endswith(".py"):
            tree = ast.parse(open(os.path.join(path, file)).read())
            imports = {n.name for n in ast.walk(tree) if isinstance(n, ast.Import)}
            names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
            unused = imports - names
            if unused:
                print(file, unused)

find_unused_imports("src")
'''
def find_unused_imports(file_path):
    with open(file_path, "r",
              encoding="utf-8") as f:
        tree = ast.parse(f.read())
    
    imports = set()
    
    used = set()
    
    for node in ast.walk(tree):
        
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.Name):
            used.add(node.id)
    return imports - used

# print(find_unused_imports("app.py"))


patterns = {
    "AWS Key":
        r"AKIA[0-9A-Z]{16}",
    "OpenAI Key":
        r"sk-[A-Za-z0-9]{20,}",
    "Generic Token":
        r"(?i)(api|secret|token).{0,20}[=:].+"
}

def scan_file(file_path):
    
    with open(file_path,
              encoding="utf-8",
              errors="ignore") as f:
        content = f.read()
    
    for name, pattern in patterns.items():
        if re.search(pattern, content):
            print(
                f"Potential {name} found "
                f"in {file_path}"
            )

# scan_file("config.py")

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

import subprocess
import sys
'''
checks = [
    ["python", "-m", "compileall", "."],
    ["pytest"],
]

for cmd in checks:
    if subprocess.call(cmd) != 0:
        print("❌ Check failed:", cmd)
        sys.exit(1)

print("✅ All checks passed.")
'''


'''
import hashlib

def calculate_hash(filename):

    sha256 = hashlib.sha256()

    with open(filename, "rb") as f:
        while chunk := f.read(4096):
            sha256.update(chunk)

    return sha256.hexdigest()

def verify_file(file_path, expected_hash):

    current_hash = calculate_hash(file_path)

    if current_hash == expected_hash:
        print("File integrity verified")
        return True

    else:
        print("File corrupted")
        return False
'''

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
