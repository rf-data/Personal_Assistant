## logger.py
import logging
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler

# import loguru
from typing import Literal
from rich.logging import RichHandler
from rich.console import Console
from rich.traceback import install

# import sys
import re
from datetime import datetime
from pathlib import Path

from src.utils.path_helper import ensure_dir
from src.core.config import parsing_env_vars

# formatiert zusätzlich unbehandelte Exceptions
install()


def clear_handlers(logger: logging.Logger) -> None:
    """
    Remove and close all handlers attached to a logger.
    """
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)


def create_logger(
    name: str,
    file_name: str | None = None,
    folder: str | Path = None,
    level: str = "info",
    *,
    logfile_mode: Literal["time", "size"] = "time",
    file_level: str | None = None,
    retention_days: int = 14,
) -> logging.Logger:
    """
    Create a configured logger with Rich console output and
    optional daily rotating file logging.

    Parameters
    ----------
    name:
        Logger name, for example "SOP_Gen".
    file_name:
        Log file name without the ".log" suffix.
        If None, file logging is disabled.
    folder:
        Directory for log files. Defaults to parsing_env_vars.log_dir.
    level:
        Console log level.
    file_level:
        File log level. Defaults to the console level.
    retention_days:
        Number of daily backup files to retain.
    """

    level_map = {
        "not_set": logging.NOTSET,
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        # "exception": logging.exception,
        "critical": logging.CRITICAL,
    }

    console_log_level = level_map.get(level.lower(), logging.INFO)

    if file_level is None:
        file_log_level = console_log_level
    else:
        file_log_level = level_map.get(
            file_level.lower(),
            logging.DEBUG,
        )

    logger = logging.getLogger(name)

    # Der Logger muss alle Meldungen durchlassen, die irgendein Handler benötigt.
    logger.setLevel(min(console_log_level, file_log_level))
    logger.propagate = False  # VERY important with Uvicorn / Streamlit

    # Verhindert doppelte Handler bei wiederholtem Aufruf,
    # insbesondere bei Streamlit-Reruns.
    # logger.handlers.clear()
    clear_handlers(logger)

    # --------------------
    # Rich console handler
    # --------------------
    console_handler = RichHandler(
        level=console_log_level,
        rich_tracebacks=True,
        tracebacks_show_locals=False,
        show_time=True,
        show_level=True,
        show_path=False,
        markup=False,
    )

    # Rich stellt Zeit und Level selbst dar.
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(console_handler)

    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s [%(levelname)s] %(name)s:%(module)s:%(lineno)d - %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # --------------------
    # Rotating file handler
    # --------------------
    if file_name:
        if folder is None:
            folder = parsing_env_vars.log_dir

        log_dir = ensure_dir(folder)
        log_file = Path(log_dir) / f"{file_name}.log"

        if logfile_mode == "time":
            file_handler = TimedRotatingFileHandler(
                filename=log_file,
                when="midnight",
                interval=1,
                backupCount=retention_days,
                encoding="utf-8",
                delay=True,
            )
        elif logfile_mode == "size":
            file_handler = RotatingFileHandler(
                filename=log_file,
                maxBytes=10 * 1024 * 1024,
                backupCount=10,
                encoding="utf-8",
                delay=True,
            )
        else:
            raise ValueError(
                f"Unknown value in 'logfile_mode' (allowed: 'time' | 'size'):\n-> {logfile_mode}"
            )

        file_handler.setLevel(file_log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_header(logger, title: str, level="info"):
    """
    Aufruf: log_header(self.logger, "START ESCALATION CHECK")
    """
    header = (
        "\n"
        + "=" * 50
        + "\n"
        + f"--- {title} --- {datetime.now():%Y-%m-%d %H:%M:%S} ---\n"
        + "=" * 50
    )

    getattr(logger, level)(header)


def log_section(logger, title):
    """
    Header als Ereignis
    """
    logger.info("")
    logger.info("=" * 50)
    logger.info(
        "--- %s --- %s ---", title, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    logger.info("=" * 50 + "\n")

    # else:
    #     print("\n")
    #     print("=" * 50 + "\n")
    #     print(f"--- {title} --- {datetime.now():%Y-%m-%d %H:%M:%S} ---\n")
    #     print("=" * 50 + "\n")


console = Console()


def log_rich_section(
    logger: logging.Logger,
    title: str,
) -> None:
    console.rule(f"[bold cyan]{title}")
    logger.info("SECTION: %s", title)


def get_errors_from_log():
    with open("app.log") as f:
        errors = [line for line in f if re.search("ERROR|WARNING", line)]

    print("\n".join(errors[:20]))
