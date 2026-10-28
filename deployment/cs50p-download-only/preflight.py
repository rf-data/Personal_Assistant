#!/usr/bin/env python3
"""Read-only host preflight; never resolves sources, starts units or writes data."""

import json
import os
import platform
import pwd
import shutil
import stat
import subprocess
from pathlib import Path


def run(argv):
    release = Path("/opt/cs50p-download-only/current").resolve(strict=True)
    env = dict(
        PATH="/usr/sbin:/usr/bin:/sbin:/bin",
        HOME="/var/cache/cs50p-download-only",
        LANG="C.UTF-8",
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONNOUSERSITE="1",
    )
    return subprocess.run(
        argv, check=True, text=True, capture_output=True, cwd=release / "app", env=env
    ).stdout.strip()


def main():
    if os.geteuid() != 0:
        raise PermissionError(
            "Run as administrator to check private files and service identity"
        )
    release = Path("/opt/cs50p-download-only/current").resolve(strict=True)
    account = "cs50p-download"
    identity = pwd.getpwnam(account)
    if (
        identity.pw_uid == 0
        or identity.pw_shell != "/usr/sbin/nologin"
        or os.getgrouplist(account, identity.pw_gid) != [identity.pw_gid]
    ):
        raise ValueError("Unexpected service identity/groups")
    for path in (
        release,
        release.parent,
        release.parent.parent,
        release / "ready.json",
        release / "app",
        release / "venv",
    ):
        info = path.lstat()
        if info.st_uid != 0 or stat.S_IMODE(info.st_mode) & 0o022:
            raise ValueError(
                "Root-owned code without group/other write access required"
            )
    unit = Path("/etc/systemd/system/cs50p-download-only.service")
    if (
        unit.is_symlink()
        or unit.read_bytes() != (release.parent.parent / "unit.service").read_bytes()
    ):
        raise ValueError("Installed unit changed")
    # These are required host checks, not claims based on a different local OS.
    info = platform.freedesktop_os_release()
    if (info["ID"], info["VERSION_ID"]) != ("ubuntu", "24.04"):
        raise ValueError("Host review requires Ubuntu 24.04")
    if int(run(["systemctl", "--version"]).split()[1]) < 255:
        raise ValueError("systemd 255 required")
    if run(["stat", "-fc", "%T", "/sys/fs/cgroup"]) != "cgroup2fs":
        raise ValueError("cgroup v2 required")
    for name in ("cs50p-worker.service", "cs50p-native@.service"):
        mask = Path("/etc/systemd/system") / name
        if not mask.is_symlink() or os.readlink(mask) != "/dev/null":
            raise ValueError("Worker mask missing")
    for path in ("/var/lib/cs50p-download-only", "/var/cache/cs50p-download-only"):
        if shutil.disk_usage(path).free < 5 * 1024**3:
            raise ValueError("5 GiB free reserve required")
        fs = run(["findmnt", "-n", "-o", "FSTYPE", "--target", path])
        if fs not in {"ext4", "xfs", "btrfs"}:
            raise ValueError("Reviewed local filesystem required")
    python = str(release / "venv/bin/python")
    run(
        [
            "runuser",
            "-u",
            account,
            "--",
            python,
            "-I",
            "-c",
            "import sys,ssl; assert sys.version_info[:2] == (3,12); assert ssl.create_default_context().get_ca_certs()",
        ]
    )
    run(["runuser", "-u", account, "--", python, "-m", "pip", "check"])
    result = run(
        [
            "runuser",
            "-u",
            account,
            "--",
            python,
            "-m",
            "scripts.cs50p_download_only",
            "preflight",
        ]
    )
    print(
        json.dumps(
            dict(
                status="checked",
                release=release.name,
                runtime=json.loads(result),
                host_review_required=True,
            )
        )
    )


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(json.dumps(dict(status="blocked", error_class=type(error).__name__)))
        raise SystemExit(2) from None
