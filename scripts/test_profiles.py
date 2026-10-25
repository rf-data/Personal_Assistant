"""Reproducible profile selection; uses the caller's installed interpreter."""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = (
    "test_legacy_io_regressions.py",
    "test_legacy_retry.py",
    "test_content_store_models.py",
    "test_content_read_contracts.py",
    "test_cs50_discovery.py",
    "test_knowledge_source_id.py",
    "test_knowledge_identity_arguments.py",
    "test_knowledge_transcript_provenance.py",
    "test_pipeline_metrics.py",
    "test_maint03b_profiles.py",
)


def command(profile, *, run_external=False):
    if profile == "external" and not run_external:
        raise ValueError("External integration requires explicit --run-external")
    args = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-o",
        "addopts=",
        "-p",
        "no:cacheprovider",
    ]
    if profile == "external":
        args += ["--run-external", "-m", "external_integration", "tests"]
    else:
        args += ["-p", "tests.offline_guard", "-m", "not external_integration"]
        args += [f"tests/{name}" for name in CORE] if profile == "core" else ["tests"]
    return args


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", choices=("core", "extended", "external"))
    parser.add_argument("--run-external", action="store_true")
    options, extra = parser.parse_known_args()
    if options.run_external and options.profile != "external":
        parser.error("--run-external is only valid for the external profile")
    # Prevent trailing arguments from silently changing this profile's selection.
    if any(
        arg.startswith(("-m", "-p", "--run-external", "--ignore", "--deselect"))
        or not arg.startswith("-")
        for arg in extra
    ):
        parser.error(
            "Only self-contained reporting flags, e.g. --junitxml=/tmp/core.xml"
        )
    try:
        args = command(options.profile, run_external=options.run_external) + extra
    except ValueError as error:
        parser.error(str(error))
    env = dict(os.environ)
    env.update(
        PYTHONDONTWRITEBYTECODE="1",
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
    )
    os.chdir(ROOT)
    os.execve(sys.executable, args, env)


if __name__ == "__main__":
    main()
