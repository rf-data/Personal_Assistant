"""Snapshot the actual H candidate and run synthetic offline tests, never deploy.

Reads Git objects/diffs without index or ref writes. New source and data roots
are siblings under /tmp, preserving the existing persistent-root policy.
"""

import argparse
import hashlib
import io
import json
import os
import stat
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from scripts.c26g_offline_validation import TESTS as G_TESTS

TESTS = (*G_TESTS, "c26h_runtime", "c26h_integration", "c26h_processes")
BROAD = (
    "content_store_models",
    "content_store_store",
    "content_store_backup",
    "content_store_recovery",
    "content_read_contracts",
    "content_fts",
    "content_search_http",
    "content_index_jobs",
    "content_import_jobs",
    "evaluation_store",
    "review_fts_pilot",
    "deployment_pdf_restore",
    # Monitoring contracts require the real Git index/check-ignore metadata.
    # Run tests/test_monitoring_config.py separately in the assigned worktree.
    "pipeline_metrics",
    "maint03b_isolation",
    "workflow_course_contract",
    "runsettings_contract",
)


def prepare(repo):
    root = Path(tempfile.mkdtemp(prefix="c26h-offline-"))
    source = root / "source"
    source.mkdir()
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True
    ).strip()
    archive = subprocess.check_output(["git", "archive", head], cwd=repo)
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        stream.extractall(source, filter="data")
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", "HEAD", "-z"], cwd=repo
    )
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=repo
    )
    paths = sorted(set(p.decode() for p in (changed + untracked).split(b"\0") if p))
    for name in paths:
        path = Path(name)
        if (
            path.is_absolute()
            or ".." in path.parts
            or path.parts[0]
            not in {"src", "scripts", "tests", "deployment", "docker", "docs"}
        ):
            raise ValueError("Unexpected candidate path; review before snapshot")
        original, target = repo / path, source / path
        if not original.exists() or not stat.S_ISREG(original.lstat().st_mode):
            raise ValueError("Deleted/special candidate file; review before snapshot")
        data = original.read_bytes()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(stat.S_IMODE(original.stat().st_mode))
    # Identify complete candidate bytes, not only a commit that excludes new files.
    hashes = {
        str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(source.rglob("*"))
        if p.is_file() and not p.is_symlink()
    }
    manifest = dict(
        base=head, files=hashes, production_release="HOLD", deployment_permitted=False
    )
    (root / "source-manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n"
    )
    return root, source


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--integration-only", action="store_true")
    group.add_argument("--broad", action="store_true")
    group.add_argument("--broad-only", action="store_true")
    args = parser.parse_args(argv)
    root, source = prepare(Path(__file__).resolve().parents[1])
    selected = (
        (
            "c26g_readiness",
            "c26g_restore",
            "c26h_runtime",
            "c26h_integration",
            "c26h_processes",
        )
        if args.integration_only
        else TESTS
    )
    if args.broad_only:
        selected = BROAD
    if args.broad:
        selected = (*selected, *BROAD)
    missing = [
        name
        for name in selected
        if not (source / ("tests/test_" + name + ".py")).is_file()
    ]
    if missing:
        raise ValueError("Missing selected test modules: " + ", ".join(missing))
    command = [
        sys.executable,
        "-B",
        "-m",
        "pytest",
        "-q",
        "-o",
        "addopts=",
        "-p",
        "no:cacheprovider",
        "-p",
        "tests.offline_guard",
        "-m",
        "not external_integration",
        "--tb=short",
        "--basetemp=" + str(root / "data"),
        "--junitxml=" + str(root / "result.xml"),
    ]
    command += ["tests/test_" + name + ".py" for name in selected]
    env = dict(
        os.environ,
        PYTHONDONTWRITEBYTECODE="1",
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
    )
    env.pop("PYTHONPATH", None)
    print(
        json.dumps(
            dict(
                snapshot=str(source),
                evidence=str(root),
                production_release="HOLD",
                deployment_permitted=False,
            )
        ),
        flush=True,
    )
    return subprocess.run(command, cwd=source, env=env, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
