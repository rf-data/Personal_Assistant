#!/usr/bin/env python3
"""READ-ONLY host inventory, including before installation; standard library only.

No source/network probes, package installs, writes, service mutations or Docker API.
Output is private: addresses, usernames, process names and local paths may occur.
"""

import json
import os
import platform
import pwd
import shutil
import stat
import subprocess
import sys
from pathlib import Path

PATHS = (
    "/opt/cs50p-download-only",
    "/var/lib/cs50p-download-only",
    "/var/lib/cs50p-download-only/archive",
    "/var/lib/cs50p-download-only/reports",
    "/var/cache/cs50p-download-only",
    "/opt/.cs50p-download-only-install.lock",
)
COMMANDS = {
    "systemd": ["systemctl", "--version"],
    "units": ["systemctl", "list-units", "--all", "--no-pager", "--plain", "cs50p*"],
    "unit_files": ["systemctl", "list-unit-files", "--no-pager", "cs50p*"],
    "unit_properties": [
        "systemctl",
        "show",
        "cs50p-download-only.service",
        "cs50p-worker.service",
        "cs50p-native@.service",
        "-p",
        "Id,LoadState,ActiveState,SubState,UnitFileState,FragmentPath,DropInPaths",
    ],
    "listeners": ["ss", "-lntup"],
    "ssh": [
        "systemctl",
        "show",
        "ssh.service",
        "ssh.socket",
        "-p",
        "Id,LoadState,ActiveState,SubState,Listen",
    ],
    "tailscale_service": [
        "systemctl",
        "show",
        "tailscaled.service",
        "-p",
        "LoadState,ActiveState,SubState",
    ],
    "tailscale": ["tailscale", "status"],
    "python": [
        "python3.12",
        "-I",
        "-B",
        "-c",
        "import sys,ssl,venv,ensurepip,platform; print(sys.version); "
        "print(platform.machine()); print(ensurepip.version()); "
        "print(ssl.OPENSSL_VERSION); "
        'print("system_CA_count", len(ssl.create_default_context('
        'cafile="/etc/ssl/certs/ca-certificates.crt").get_ca_certs()))',
    ],
    "cgroup": ["stat", "-fc", "%T", "/sys/fs/cgroup"],
    "load": ["cat", "/proc/loadavg"],
    "swap": ["cat", "/proc/swaps"],
}
PREREQUISITES = (
    "python3.12",
    "systemctl",
    "systemd-analyze",
    "runuser",
    "useradd",
    "findmnt",
    "stat",
    "ss",
    "tar",
    "sha256sum",
    "flock",
)


def command(argv):
    env = dict(
        PATH="/usr/sbin:/usr/bin:/sbin:/bin",
        HOME="/nonexistent",
        LANG="C.UTF-8",
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONNOUSERSITE="1",
        SYSTEMD_PAGER="cat",
        SYSTEMD_COLORS="0",
    )
    try:
        value = subprocess.run(
            argv, capture_output=True, text=True, timeout=5, env=env, check=False
        )
        return dict(
            argv=argv,
            exit=value.returncode,
            stdout=value.stdout[:65536],
            stderr=value.stderr[:8192],
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return dict(argv=argv, error_class=type(error).__name__)


def path_info(name):
    path = Path(name)
    result = dict(path=name, exists=path.exists(), symlink=path.is_symlink())
    try:
        info = path.lstat()
        result.update(
            uid=info.st_uid, gid=info.st_gid, mode=oct(stat.S_IMODE(info.st_mode))
        )
        if path.is_symlink():
            result["target"] = os.readlink(path)
        elif path.is_dir():
            # Metadata only. Never print private config contents or walk archives.
            result["entries"] = sorted(p.name for p in path.iterdir())[:100]
    except FileNotFoundError:
        pass
    except OSError as error:
        result["error_class"] = type(error).__name__
    existing = path
    while not existing.exists() and existing != existing.parent:
        existing = existing.parent
    result["capacity_path"] = str(existing)
    result["disk"] = dict(
        zip(("total", "used", "free"), shutil.disk_usage(existing), strict=True)
    )
    result["mount"] = command(
        [
            "findmnt",
            "-n",
            "-o",
            "TARGET,SOURCE,FSTYPE,OPTIONS",
            "--target",
            str(existing),
        ]
    )
    return result


def collect():
    result = dict(
        schema_version=1,
        status="HOLD",
        host_review_required=True,
        read_only=True,
        effective_uid=os.geteuid(),
        os=platform.freedesktop_os_release(),
        kernel=platform.release(),
        machine=platform.machine(),
        libc=platform.libc_ver(),
        cpus=os.cpu_count(),
        memory=Path("/proc/meminfo").read_text(),
        prerequisites={p: shutil.which(p) for p in PREREQUISITES},
    )
    users = []
    for name in ("cs50p-download", "cs50p"):
        try:
            user = pwd.getpwnam(name)
            users.append(
                dict(
                    name=name,
                    uid=user.pw_uid,
                    gid=user.pw_gid,
                    home=user.pw_dir,
                    shell=user.pw_shell,
                    groups=os.getgrouplist(name, user.pw_gid),
                )
            )
        except KeyError:
            users.append(dict(name=name, absent=True))
    result["users"] = users
    result["paths"] = [path_info(p) for p in PATHS]
    result["commands"] = {name: command(argv) for name, argv in COMMANDS.items()}
    result["unit_paths"] = []
    for folder in (
        "/etc/systemd/system",
        "/run/systemd/system",
        "/usr/lib/systemd/system",
        "/run/systemd/transient",
        "/etc/systemd/system.control",
        "/run/systemd/system.control",
    ):
        result["unit_paths"].extend(
            path_info(str(p)) for p in sorted(Path(folder).glob("cs50p*"))
        )
    result["notes"] = [
        "No listening port is required by this oneshot download runtime.",
        "Missing identity/paths/units are expected before first installation; existing resources require review.",
        "Review Ubuntu 24.04, systemd >=255, cgroup2fs, CPython 3.12 x86_64 glibc, CA count >0.",
        "Review capacity beside existing Coolify workload; >=5 GiB reserve AFTER release installation.",
        "Read-only metadata cannot prove flock/fsync/renameat2/cgroup enforcement or real systemd execution.",
        "No write probe, source DNS resolution, SSH connection or network connectivity test was performed.",
    ]
    return result


if __name__ == "__main__":
    try:
        print(json.dumps(collect(), indent=2))
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps(dict(status="HOLD", error_class=type(error).__name__)))
        sys.exit(2)
