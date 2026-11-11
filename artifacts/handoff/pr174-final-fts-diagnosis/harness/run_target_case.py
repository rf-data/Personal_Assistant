"""Run exactly one original test, importing all product/test code from target."""
import json
import os
from pathlib import Path
import platform
import sqlite3
import sys

import fts_probe
fts_probe.install()
import pydantic
import pytest
from src.tools_rag import content_index, content_fts

target = Path(os.environ['FTS_DIAG_TARGET']).resolve()
assert Path.cwd() == target
assert Path(content_index.__file__).is_relative_to(target)
assert Path(content_fts.__file__).is_relative_to(target)
assert content_index.QUERY_SECONDS == 2.0
environment = dict(
    python=sys.version,
    executable=sys.executable,
    sqlite=sqlite3.sqlite_version,
    pydantic=pydantic.__version__,
    pytest=pytest.__version__,
    platform=platform.platform(),
    affinity=sorted(os.sched_getaffinity(0)),
    cpus=os.cpu_count(),
    product_root=str(target),
    query_seconds=content_index.QUERY_SECONDS,
    instrumentation='test-only wrappers and AST-verified timing marks; original checks retained',
    network='blocked in parent and Python child',
    target_writes='blocked by Python audit hook; bytecode and pytest cache disabled',
)
Path(os.environ['FTS_DIAG_ENV_OUTPUT']).write_text(json.dumps(environment, indent=2) + '\n')
raise SystemExit(pytest.main(sys.argv[1:]))
