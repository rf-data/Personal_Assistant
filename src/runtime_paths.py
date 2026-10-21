"""Explicit persistent output grants for mounts inside an application checkout.

No default exception by directory name; no environment-supplied path aliases.
The operator's private policy is re-read together with kernel mount identities.
"""

import json
import os
import re
import stat
from pathlib import Path

POLICY_ENV = "PA_PERSISTENT_ROOTS_FILE"
PURPOSES = {"job_workspace", "material_artifacts"}


def checked_path(value):
    path = Path(value)
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("Absolute nontraversing path required")
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError("Symlink output paths are forbidden")
    if path.resolve() != path:
        raise ValueError("Output path resolution changed")
    return path


def mounts():
    def decode(value):
        return re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), value)

    result = {}
    for line in Path("/proc/self/mountinfo").read_text().splitlines():
        before, after = line.split(" - ", 1)
        fields, filesystem = before.split(), after.split()
        point = Path(decode(fields[4]))
        if not point.is_absolute() or ".." in point.parts:
            raise ValueError("Invalid mountpoint")
        if point in result:
            raise ValueError("Ambiguous stacked mount")
        result[point] = dict(
            device=fields[2],
            root=decode(fields[3]),
            filesystem=filesystem[0],
            source=decode(filesystem[1]),
            writable="rw" in fields[5].split(","),
        )
    return result


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate policy key")
        result[key] = value
    return result


def load_policy(repo):
    if os.getuid() != os.geteuid():
        raise ValueError("Unambiguous worker UID required")
    path = checked_path(os.environ.get(POLICY_ENV, ""))
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != 0o600
        ):
            raise ValueError("Private owned path policy required")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            data = stream.read(65537)
        if len(data) > 65536:
            raise ValueError("Path policy too large")
    finally:
        os.close(fd)
    policy = json.loads(data, object_pairs_hook=unique)
    if (
        set(policy) != {"schema_version", "repository", "roots"}
        or type(policy["schema_version"]) is not int
        or policy["schema_version"] != 1
        or checked_path(policy["repository"]) != repo
        or not isinstance(policy["roots"], list)
        or not 1 <= len(policy["roots"]) <= 16
    ):
        raise ValueError("Invalid path policy")
    for grant in policy["roots"]:
        if set(grant) != {
            "path",
            "mount_point",
            "mount_identity",
            "purposes",
            "owner_uid",
        }:
            raise ValueError("Invalid path grant")
        root, point = checked_path(grant["path"]), checked_path(grant["mount_point"])
        if (
            root == point
            or not root.is_relative_to(point)
            or point == repo
            or not point.is_relative_to(repo)
            or point.relative_to(repo).parts[0]
            in {"src", "scripts", ".git", ".venv", "tests", "docker", "deployment"}
            or type(grant["owner_uid"]) is not int
            or grant["owner_uid"] != os.geteuid()
            or not isinstance(grant["purposes"], list)
            or not grant["purposes"]
            or not set(grant["purposes"]) <= PURPOSES
            or not isinstance(grant["mount_identity"], dict)
            or set(grant["mount_identity"])
            != {"device", "root", "filesystem", "source", "writable"}
            or grant["mount_identity"]["writable"] is not True
            or grant["mount_identity"]["filesystem"] not in {"ext4", "xfs", "btrfs"}
            or grant["mount_identity"]["root"] == "/"
            or any(
                not isinstance(grant["mount_identity"][k], str)
                or not grant["mount_identity"][k]
                for k in ("device", "root", "filesystem", "source")
            )
            or path == root
            or path.is_relative_to(root)
        ):
            raise ValueError("Invalid or unsafe path authorization")
    return policy


def output_path(value, purpose, *, repository=None):
    path = checked_path(value)
    repo = checked_path(repository or Path(__file__).resolve().parents[1])
    if purpose not in PURPOSES or path == Path("/") or repo.is_relative_to(path):
        raise ValueError("Output overlaps application code")
    if not path.is_relative_to(repo):
        return path  # Unchanged external-workspace contract.
    try:
        policy = load_policy(repo)
        current = mounts()
        for grant in policy["roots"]:
            root, point = Path(grant["path"]), Path(grant["mount_point"])
            if not path.is_relative_to(root) or purpose not in grant["purposes"]:
                continue
            if current.get(point) != grant["mount_identity"]:
                raise ValueError("Mount identity changed")
            point_info = point.stat()
            if (
                not point.is_dir()
                or point_info.st_uid not in {0, os.geteuid()}
                or stat.S_IMODE(point_info.st_mode) & 0o022
            ):
                raise ValueError("Persistent mount parent is not trusted")
            if any(
                m != point
                and m.is_relative_to(point)
                and (m.is_relative_to(root) or root.is_relative_to(m))
                for m in current
            ):
                raise ValueError("Nested mount in authorized output subtree")
            ancestor = root
            while not ancestor.exists():
                ancestor = ancestor.parent
            if not ancestor.is_dir() or not os.access(ancestor, os.W_OK | os.X_OK):
                raise ValueError("Worker cannot write authorized root")
            if root.exists() and (
                root.stat().st_uid != grant["owner_uid"]
                or stat.S_IMODE(root.stat().st_mode) != 0o700
            ):
                raise ValueError("Private owned data root required")
            for component in (path, *path.parents):
                if component == root:
                    break
                if component.exists():
                    info = component.stat()
                    expected = 0o700 if component.is_dir() else 0o600
                    if (
                        info.st_uid != grant["owner_uid"]
                        or stat.S_IMODE(info.st_mode) != expected
                    ):
                        raise ValueError("Unowned or nonprivate output component")
                    if component.is_dir() and not os.access(
                        component, os.W_OK | os.X_OK
                    ):
                        raise ValueError("Worker cannot write output component")
            return path
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        raise ValueError("Persistent output authorization unavailable") from error
    raise ValueError("Output subtree or purpose not authorized")
