#!/usr/bin/env python3
"""Offline install/upgrade/rollback/uninstall; never starts or enables a service.

Trust boundary: root reviews this script and all supplied source/wheels/specs.
Uninstall removes only the unchanged owned unit; code, data, user and masks remain.
"""

import argparse
import fcntl
import hashlib
import json
import os
import pwd
import re
import stat
import subprocess
import sys
from pathlib import Path

ACCOUNT = "cs50p-download"
UNIT = "cs50p-download-only.service"
MASKS = ("cs50p-worker.service", "cs50p-native@.service")
PACKAGE = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode()


def command(argv, *, cwd=None):
    # No ambient Python, proxy, TLS, package-index or credential environment.
    env = dict(
        PATH="/usr/sbin:/usr/bin:/sbin:/bin",
        HOME="/root",
        LANG="C.UTF-8",
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONNOUSERSITE="1",
        PIP_CONFIG_FILE="/dev/null",
        PIP_DISABLE_PIP_VERSION_CHECK="1",
        PIP_NO_CACHE_DIR="1",
    )
    return subprocess.run(
        [str(x) for x in argv],
        cwd=cwd,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def regular(path):
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError("Regular nonsymlink input required: " + str(path))
    for parent in path.parents:
        if parent.is_symlink():
            raise ValueError("Symlink input parent refused")
    return path.read_bytes()


def tree(root):
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not (path.is_dir() or path.is_file()):
            raise ValueError("Special input refused")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = regular(path)
    if len(result) > 20000 or sum(map(len, result.values())) > 512 * 1024**2:
        raise ValueError("Package size limit")
    return result


def safe_name(name):
    path = Path(name)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError("Unsafe package path")
    return path


class Installer:
    """Filesystem root and command adapter are injectable only for offline tests."""

    def __init__(self, root=Path("/"), run=command, identity=None):
        self.root, self.run, self.identity = root, run, identity
        self.base = root / "opt/cs50p-download-only"
        self.data = root / "var/lib/cs50p-download-only"
        self.cache = root / "var/cache/cs50p-download-only"
        self.units = root / "etc/systemd/system"

    def inactive(self):
        output = self.run(
            [
                "systemctl",
                "list-units",
                "--all",
                "--plain",
                "--no-legend",
                "--state=active,activating,deactivating,reloading",
                "cs50p-download*.service",
                "cs50p-worker.service",
                "cs50p-native@*.service",
            ]
        )
        if output.strip():
            raise ValueError("Stop existing CS50P units and investigate before change")

    def validate_paths(self):
        for path in (self.base, self.data, self.cache, self.units):
            for item in (path, *path.parents):
                if item.is_symlink():
                    raise ValueError("Symlink destination refused")
        if self.base.exists():
            if regular(self.base / ".c26-cs50p-04") != b"download-only-v1\n":
                raise ValueError("Foreign installation")
        elif any(p.exists() for p in (self.data, self.cache)):
            raise ValueError("Unknown data paths; no adoption")
        pointer = self.base / "current"
        if pointer.exists() or pointer.is_symlink():
            if not pointer.is_symlink() or not re.fullmatch(
                r"releases/[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", os.readlink(pointer)
            ):
                raise ValueError("Unknown release pointer")
        unit = self.units / UNIT
        if unit.exists() or unit.is_symlink():
            if not self.base.exists() or regular(unit) != regular(
                self.base / "unit.service"
            ):
                raise ValueError("Unknown/changed unit; no replacement")
        for name in MASKS:
            mask = self.units / name
            if name == "cs50p-native@.service" and any(
                p.name != name for p in self.units.glob("cs50p-native@*.service")
            ):
                raise ValueError("Existing native instance unit")
            if mask.is_symlink() and os.readlink(mask) == "/dev/null":
                continue
            if mask.exists() or mask.is_symlink():
                raise ValueError("Existing worker unit requires separate host review")
        # Drop-ins and enablement links could alter or automatically start our unit.
        for folder in (
            self.units,
            self.root / "run/systemd/system",
            self.root / "usr/lib/systemd/system",
            self.root / "run/systemd/transient",
            self.root / "run/systemd/system.control",
            self.root / "etc/systemd/system.control",
            self.root / "run/systemd/generator.early",
            self.root / "run/systemd/generator",
            self.root / "run/systemd/generator.late",
        ):
            for pattern in (
                "cs50p-*.service.d",
                "cs50p-*.service.wants",
                "*.wants/cs50p-*.service",
                "*.requires/cs50p-*.service",
                "cs50p-download-only.timer",
            ):
                if list(folder.glob(pattern)):
                    raise ValueError(
                        "Existing CS50P drop-in/dependency/timer requires review"
                    )
            if folder != self.units and any(folder.glob("cs50p-*.service")):
                raise ValueError("Conflicting runtime/vendor unit")

    def user(self):
        if self.identity is not None:
            return self.identity
        try:
            account = pwd.getpwnam(ACCOUNT)
        except KeyError:
            self.run(
                [
                    "useradd",
                    "--system",
                    "--user-group",
                    "--home-dir",
                    "/var/cache/cs50p-download-only",
                    "--shell",
                    "/usr/sbin/nologin",
                    ACCOUNT,
                ]
            )
            account = pwd.getpwnam(ACCOUNT)
        else:
            if not self.base.exists():
                raise ValueError("Existing account requires ownership review")
        if (
            account.pw_uid == 0
            or account.pw_shell != "/usr/sbin/nologin"
            or account.pw_dir != "/var/cache/cs50p-download-only"
        ):
            raise ValueError("Unexpected service identity")
        if os.getgrouplist(ACCOUNT, account.pw_gid) != [account.pw_gid]:
            raise ValueError("Service account must have no supplementary groups")
        return account.pw_uid, account.pw_gid

    def public_directory(self, path):
        if not path.exists():
            self.public_directory(path.parent)
            path.mkdir(mode=0o755)
            path.chmod(0o755)

    def write(self, path, data, mode=0o644, owner=None):
        self.public_directory(path.parent)
        with path.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        path.chmod(mode)
        if owner:
            os.chown(path, *owner)

    def verify_release(self, release):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", release):
            raise ValueError("Invalid release name")
        path = self.base / "releases" / release
        manifest = json.loads(regular(path / "ready.json"))
        for name, expected in manifest["files"].items():
            if digest(regular(path / safe_name(name))) != expected:
                raise ValueError("Release integrity failed")
        return path, manifest

    def select(self, release):
        self.verify_release(release)
        pointer = self.base / "current"
        if pointer.exists() or pointer.is_symlink():
            if not pointer.is_symlink() or not re.fullmatch(
                r"releases/[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", os.readlink(pointer)
            ):
                raise ValueError("Unknown release pointer")
        temporary = self.base / ".current-next"
        temporary.symlink_to("releases/" + release)
        os.replace(temporary, pointer)
        fd = os.open(self.base, os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def install(self, source, wheels, specs, release):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", release):
            raise ValueError("Invalid release")
        self.inactive()
        self.validate_paths()
        # Source must be a reviewed, clean git archive export; never copy .env/data.
        payload = {}
        for directory in ("src", "scripts"):
            for name, data in tree(source / directory).items():
                if name.endswith(".py") and name not in (
                    "cs50p_native.py",
                    "cs50_worker.py",
                ):
                    payload["app/" + directory + "/" + name] = data
        payload["requirements.txt"] = regular(
            source / "deployment/cs50p-download-only/runtime/requirements.txt"
        )
        payload["app/scripts/cs50p_download_only.py"] = regular(PACKAGE / "pilot.py")
        wheel_files, spec_files = tree(wheels), tree(specs)
        if not wheel_files or any(
            not name.endswith(".whl") or "/" in name for name in wheel_files
        ):
            raise ValueError("Flat wheelhouse required")
        for name in ("batch.json", "limits.json", "approvals.json"):
            if name not in spec_files:
                raise ValueError("Incomplete reviewed specs")
        # No controller/jobs/admission material accepted by this profile.
        if set(spec_files) - {"batch.json", "limits.json", "approvals.json"} != {
            name for name in spec_files if name.startswith("snapshots/")
        }:
            raise ValueError("Only specs and snapshots accepted")
        # Verify the complete reviewed artifact set before creating users or releases.
        self.run(
            [
                sys.executable,
                PACKAGE / "wheelhouse.py",
                "check",
                "--wheels",
                wheels,
                "--requirements",
                source / "deployment/cs50p-download-only/runtime/requirements.txt",
            ]
        )
        old = json.loads(spec_files["batch.json"])
        if digest(canonical(old["batch"])) != old["sha256"]:
            raise ValueError("Input batch digest mismatch")
        batch = old["batch"]
        if (
            batch.get("source_origin", "official") != "official"
            or batch.get("schema_version", 1) != 1
        ):
            raise ValueError("Official v1 material batch required for first pilot")
        if not 1 <= len(batch["materials"]) <= 3:
            raise ValueError("One to three materials required")
        # Relocate a reviewed snapshot closure, without changing source identities or hashes.
        target = self.base / "releases" / release
        manifest_name = Path(batch["manifest"]).name
        for name, expected in batch["files"].items():
            safe_name(name)
            if digest(spec_files["snapshots/" + name]) != expected:
                raise ValueError("Snapshot closure mismatch")
        batch["manifest"] = str(target / "specs/snapshots" / manifest_name)
        relocated = dict(batch=batch, sha256=digest(canonical(batch)))
        payload.update({"specs/" + name: data for name, data in spec_files.items()})
        payload["specs/batch.json"] = canonical(relocated)
        unit_bytes = regular(PACKAGE / UNIT)
        bundle_id = digest(
            canonical(
                {
                    "payload": {n: digest(b) for n, b in payload.items()},
                    "wheels": {n: digest(b) for n, b in wheel_files.items()},
                    "unit": digest(unit_bytes),
                }
            )
        )
        identity = self.user()
        if not self.base.exists():
            self.public_directory(self.base)
            self.write(self.base / ".c26-cs50p-04", b"download-only-v1\n")
        for directory in (
            self.data,
            self.data / "archive",
            self.data / "reports",
            self.cache,
        ):
            if not directory.exists():
                directory.mkdir(parents=True, mode=0o700)
                os.chown(directory, *identity)
            info = directory.lstat()
            if (
                not stat.S_ISDIR(info.st_mode)
                or info.st_uid != identity[0]
                or stat.S_IMODE(info.st_mode) != 0o700
            ):
                raise ValueError("Unsafe persistent directory")
        if target.exists():
            _, previous = self.verify_release(release)
            if previous["bundle_id"] != bundle_id:
                raise ValueError("Release ID already used by different package")
            self.runtime_check(target)
        else:
            self.public_directory(target)
            # A failed/partial release is deliberately retained and cannot be reused.
            for name, data in payload.items():
                self.write(
                    target / name,
                    data,
                    0o600 if name.startswith("specs/") else 0o644,
                    identity if name.startswith("specs/") else None,
                )
            for path in [target / "specs", *(target / "specs").rglob("*")]:
                if path.is_dir():
                    path.chmod(0o700)
                    os.chown(path, *identity)
            self.run(["python3.12", "-m", "venv", target / "venv"])
            python = target / "venv/bin/python"
            self.run(
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
                    "--find-links=" + str(wheels),
                    "--require-hashes",
                    "-r",
                    target / "requirements.txt",
                ]
            )
            self.run([python, "-m", "pip", "check"])
            # Root's restrictive umask must not make the runtime unreadable to the service.
            # Never follow the Python/lib64 symlinks generated by venv.
            runtime = target / "venv"
            if runtime.exists():
                runtime.chmod(0o755)
                for path in runtime.rglob("*"):
                    if path.is_symlink():
                        continue
                    path.chmod(
                        0o755 if path.is_dir() or path.stat().st_mode & 0o111 else 0o644
                    )
            self.runtime_check(target)
            self.write(
                target / "ready.json",
                canonical(
                    dict(
                        bundle_id=bundle_id,
                        files={n: digest(b) for n, b in payload.items()},
                    )
                ),
            )
        # Install/mask only after the positive offline dependency/runtime check.
        for name in MASKS:
            mask = self.units / name
            if not mask.is_symlink():
                mask.symlink_to("/dev/null")
        unit = self.units / UNIT
        if unit.exists():
            if regular(unit) != unit_bytes:
                raise ValueError("Unit changes require separately reviewed migration")
        else:
            self.write(unit, unit_bytes)
        recorded = self.base / "unit.service"
        if not recorded.exists():
            self.write(recorded, unit_bytes)
        self.select(release)
        self.run(["systemctl", "daemon-reload"])
        return dict(
            status="installed_stopped", release=release, processing_enabled=False
        )

    def runtime_check(self, path):
        code = (
            "import socket; "
            "deny=lambda *a,**k: (_ for _ in ()).throw(PermissionError('offline')); "
            "socket.getaddrinfo=deny; socket.socket.connect=deny; "
            "from pathlib import Path; from scripts.cs50p_download_only import check; "
            "check(Path("
            + repr(str(path / "specs"))
            + "), Path('/var/lib/cs50p-download-only'))"
        )
        self.run(
            ["runuser", "-u", ACCOUNT, "--", path / "venv/bin/python", "-c", code],
            cwd=path / "app",
        )

    def rollback(self, release):
        self.inactive()
        self.validate_paths()
        path, _ = self.verify_release(release)
        self.runtime_check(path)
        self.select(release)
        return dict(status="rolled_back_stopped", release=release)

    def uninstall(self):
        self.inactive()
        self.validate_paths()
        unit = self.units / UNIT
        if unit.exists():
            unit.unlink()
            self.run(["systemctl", "daemon-reload"])
        return dict(
            status="uninstalled",
            retained="user, releases, specs, data, reports, cache, worker masks",
        )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    install = sub.add_parser("install")
    for name in ("source", "wheelhouse", "specs"):
        install.add_argument("--" + name, type=Path, required=True)
    install.add_argument("--release", required=True)
    rollback = sub.add_parser("rollback")
    rollback.add_argument("--release", required=True)
    sub.add_parser("uninstall")
    args = parser.parse_args(argv)
    if os.geteuid() != 0:
        parser.error("Administrator required")
    os.umask(0o077)
    # Serializes this installer across install, rollback and uninstall invocations.
    fd = os.open(
        "/opt/.cs50p-download-only-install.lock",
        os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW,
        0o644,
    )
    os.fchmod(fd, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        installer = Installer()
        if args.action == "install":
            result = installer.install(
                args.source.absolute(),
                args.wheelhouse.absolute(),
                args.specs.absolute(),
                args.release,
            )
        elif args.action == "rollback":
            result = installer.rollback(args.release)
        else:
            result = installer.uninstall()
        print(json.dumps(result))
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(
            json.dumps(
                dict(
                    status="blocked",
                    error_class=type(error).__name__,
                    action=args.action,
                    recovery="retain partial release; investigate; use new release ID",
                )
            )
        )
        return 2
    finally:
        os.close(fd)
    return 0


if __name__ == "__main__":
    sys.exit(main())
