#!/usr/bin/env python3
"""Fetch pinned production wheels or verify/install them in a NEW disposable venv.

fetch is online; check is read-only; verify is offline except for local OS calls.
Run verify inside an independent network namespace for an OS-enforced offline proof.
"""

import argparse
import hashlib
import json
import platform
import re
import ssl
import stat
import subprocess
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
REQUIREMENTS = PACKAGE / "runtime/requirements.txt"


def requirements(path):
    result = {}
    # This production export deliberately has no markers, URLs, options or extras.
    for entry in path.read_text().replace("\\\n", " ").splitlines():
        entry = entry.strip()
        if not entry or entry.startswith("#"):
            continue
        match = re.fullmatch(
            r"([a-z0-9-]+)==([0-9][a-zA-Z0-9.]*)\s+"
            r"((?:--hash=sha256:[a-f0-9]{64}\s*)+)",
            entry,
        )
        if not match or match[1] in result:
            raise ValueError("Unsupported or duplicate production requirement")
        result[match[1]] = (match[2], re.findall(r"sha256:([a-f0-9]{64})", match[3]))
    if not result:
        raise ValueError("Empty production requirements")
    return result


def check(wheels, requirements_path=REQUIREMENTS):
    expected, found, files = requirements(requirements_path), set(), {}
    if wheels.is_symlink() or any(p.is_symlink() for p in wheels.parents):
        raise ValueError("Symlink wheelhouse refused")
    for path in sorted(wheels.iterdir()):
        if not stat.S_ISREG(path.lstat().st_mode) or path.suffix != ".whl":
            raise ValueError("Only regular wheels accepted")
        parts = path.name.split("-")
        name = parts[0].replace("_", "-")
        if len(parts) < 5 or name not in expected or name in found:
            raise ValueError("Unexpected or duplicate wheel")
        version, hashes = expected[name]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if parts[1] != version or digest not in hashes:
            raise ValueError("Wheel version/hash mismatch: " + path.name)
        found.add(name)
        files[path.name] = digest
    if found != set(expected):
        raise ValueError("Missing wheels: " + ", ".join(sorted(set(expected) - found)))
    return files


def environment():
    return dict(
        PATH="/usr/sbin:/usr/bin:/sbin:/bin",
        HOME="/nonexistent",
        LANG="C.UTF-8",
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONNOUSERSITE="1",
        PIP_CONFIG_FILE="/dev/null",
        PIP_DISABLE_PIP_VERSION_CHECK="1",
        PIP_NO_CACHE_DIR="1",
    )


def run(argv, *, cwd=None):
    return subprocess.run(
        list(map(str, argv)),
        cwd=cwd,
        env=environment(),
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def target():
    if (
        sys.implementation.name,
        sys.version_info[:2],
        sys.platform,
        platform.machine(),
    ) != ("cpython", (3, 12), "linux", "x86_64") or platform.libc_ver()[0] != "glibc":
        raise ValueError("CPython 3.12 Linux x86_64 glibc required")
    if not ssl.create_default_context(
        cafile="/etc/ssl/certs/ca-certificates.crt"
    ).get_ca_certs():
        raise ValueError("CA certificates required")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("fetch", "check", "verify"))
    parser.add_argument("--wheels", type=Path, required=True)
    parser.add_argument("--requirements", type=Path, default=REQUIREMENTS)
    parser.add_argument("--venv", type=Path)
    parser.add_argument("--source", type=Path, default=PACKAGE.parents[1])
    args = parser.parse_args(argv)
    result = dict(action=args.action, positive_frozen_install=False)
    try:
        if args.action == "fetch":
            target()
            args.wheels.mkdir(mode=0o700)  # Never consume a pre-existing cache/dir.
            run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "--isolated",
                    "--disable-pip-version-check",
                    "--no-cache-dir",
                    "download",
                    "--index-url",
                    "https://pypi.org/simple",
                    "--only-binary=:all:",
                    "--require-hashes",
                    "--retries",
                    "0",
                    "--timeout",
                    "15",
                    "--cert",
                    "/etc/ssl/certs/ca-certificates.crt",
                    "-r",
                    args.requirements,
                    "-d",
                    args.wheels,
                ]
            )
        result["wheels"] = check(args.wheels, args.requirements)
        if args.action == "verify":
            target()
            if args.venv is None or args.venv.exists() or args.venv.is_symlink():
                raise ValueError("Explicit NEW venv path required")
            run([sys.executable, "-m", "venv", args.venv])
            python = args.venv.absolute() / "bin/python"
            result["install"] = run(
                [
                    python,
                    "-m",
                    "pip",
                    "--isolated",
                    "--disable-pip-version-check",
                    "--no-cache-dir",
                    "install",
                    "--no-index",
                    "--only-binary=:all:",
                    "--require-hashes",
                    "--find-links=" + str(args.wheels.absolute()),
                    "-r",
                    args.requirements.absolute(),
                ]
            )
            result["pip_check"] = run([python, "-m", "pip", "--isolated", "check"])
            result["smoke"] = json.loads(
                run(
                    [
                        python,
                        PACKAGE / "runtime_smoke.py",
                        "--source",
                        args.source.absolute(),
                    ],
                    cwd=args.source,
                )
            )
            result["distributions"] = json.loads(
                run(
                    [
                        python,
                        "-I",
                        "-B",
                        "-c",
                        "import importlib.metadata as m,json; print(json.dumps({"
                        "d.metadata['Name'].lower().replace('_','-'):d.version "
                        "for d in m.distributions()}))",
                    ]
                )
            )
            expected = {
                name: version
                for name, (version, _hashes) in requirements(args.requirements).items()
            }
            installed = {
                name: version
                for name, version in result["distributions"].items()
                if name != "pip"
            }
            if installed != expected:
                raise ValueError(
                    "Installed distribution set differs from production closure"
                )
            result["positive_frozen_install"] = True
        result.update(
            status="checked", python=sys.version, platform=platform.platform()
        )
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        result.update(status="blocked", error_class=type(error).__name__)
        if isinstance(error, subprocess.CalledProcessError):
            result.update(
                exit=error.returncode, stdout=error.stdout, stderr=error.stderr
            )
        else:
            result["reason"] = str(error)
        print(json.dumps(result, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
