"""Only an absent top-level SDK is optional; broken installed packages must fail."""

import importlib
import importlib.util

import pytest


def require_qdrant():
    if importlib.util.find_spec("qdrant_client") is None:
        pytest.skip(
            "Optional Qdrant SDK absent; install uv group test-qdrant "
            "for local persisted-Qdrant tests (no server or models required)",
            allow_module_level=True,
        )
    # Import failures inside an installed SDK deliberately propagate.
    return importlib.import_module("qdrant_client")
