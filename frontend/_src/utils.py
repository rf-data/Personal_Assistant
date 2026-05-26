import subprocess
import time
from datetime import datetime
from pathlib import Path

import streamlit as st


def load_env_vars(name: List | str = ".env"):
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


def ensure_dir(f_path: Union[str | Path]) -> Path:

    p = Path(f_path)

    target_dir = p.parent if p.suffix else p
    target_dir.mkdir(parents=True, exist_ok=True)

    return p


def shorten_path(path, n=3):
    p = Path(path).parts
    return "/".join(p[-n:])


def live_command_demo(cmd, log_name, mode="a"):
    placeholder = st.empty()
    start_time = datetime.now()

    log_file = Path(f"{log_name}.log")

    with open(log_file, mode, buffering=1) as log:
        # log.write("")
        log.write("\n" + "=" * 80 + "\n")
        log.write(f"[START] {start_time.isoformat()} | CMD: {' '.join(cmd)}\n")
        log.write("=" * 80 + "\n")
        log.flush()

        process = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, text=True)

    while True:
        if log_file.exists():
            placeholder.code(log_file.read_text(), language="text")
        else:
            placeholder.info("Waiting for log output...")

        exit_code = process.poll()

        if exit_code is not None:
            with open(log_file, mode, buffering=1) as log:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                # --- END MARKER ---
                log.write("-" * 80 + "\n")
                log.write(
                    f"[END] {end_time.isoformat()} | "
                    f"EXIT CODE: {exit_code} | "
                    f"DURATION: {duration:.1f}s\n"
                )
                log.write("-" * 80 + "\n")
                log.flush()

                placeholder.code(log_file.read_text(), language="text")

            break

        time.sleep(1)

    return exit_code


def clear_others(active_key):
    for key in ["presentation", "demo", "extra"]:
        if key != active_key and key in st.session_state:
            st.session_state[key] = None
