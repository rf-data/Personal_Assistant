"""Private bounded failure evidence; never persist exception text or SQL."""

import json
import os
import sqlite3
from pathlib import Path

from pydantic import TypeAdapter

from src.job_control.catalog import safe_path
from src.job_control.models import Identifier


def record_failure(root, job_id, component, error):
    """Best effort only: evidence failure never changes the execution decision."""
    classes = (sqlite3.Error, OSError, ValueError, KeyError, RuntimeError)
    kind = next(
        (base.__name__ for base in classes if isinstance(error, base)), "Exception"
    )
    code = getattr(error, "sqlite_errorcode", None)
    phase = getattr(error, "job_db_phase", None)
    value = {
        "schema_version": 1,
        "component": component,
        "category": kind,
        "sqlite_code": code if type(code) is int else None,
        "phase": phase if phase in ("setup", "begin", "body", "commit") else None,
    }
    try:
        if component not in ("adapter", "guardian"):
            return
        TypeAdapter(Identifier).validate_python(job_id)
        path = safe_path(
            Path(root), "jobs/" + job_id + "/" + component + "-failure.v1.json"
        )
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
    except (OSError, ValueError):
        pass
