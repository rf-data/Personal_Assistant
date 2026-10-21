"""Synthetic kernel mount records and real private files; no host mount changes."""

import json
import os
from pathlib import Path

import pytest

from src import runtime_paths as paths
from src.job_control.guardian import clean_environment
from src.job_control.models import Settings
from src.tools_materials.storage import artifact_root


@pytest.fixture
def mounted(tmp_path, monkeypatch):
    os.umask(0o077)
    repo = tmp_path / "app"
    repo.mkdir(mode=0o700)
    for name in ("src", "scripts", "data", "configuration"):
        (repo / name).mkdir(mode=0o700)
    root = repo / "data/pilot"
    identity = dict(
        device="8:1",
        root="/srv/personal-assistant/data",
        filesystem="ext4",
        source="/dev/vda1",
        writable=True,
    )
    document = dict(
        schema_version=1,
        repository=str(repo),
        roots=[
            dict(
                path=str(root),
                mount_point=str(repo / "data"),
                mount_identity=identity,
                purposes=["material_artifacts"],
                owner_uid=os.geteuid(),
            ),
            dict(
                path=str(root / "jobs"),
                mount_point=str(repo / "data"),
                mount_identity=identity,
                purposes=["job_workspace"],
                owner_uid=os.geteuid(),
            ),
        ],
    )
    policy = repo / "configuration/pilot.paths.json"
    policy.write_text(json.dumps(document))
    policy.chmod(0o600)
    records = [
        "1 0 0:1 / / rw - overlay overlay rw",
        f"10 1 8:1 /srv/personal-assistant/data {repo}/data rw - ext4 /dev/vda1 rw",
    ]
    read = Path.read_text

    def kernel(path, *args, **kwargs):
        if str(path) == "/proc/self/mountinfo":
            return "\n".join(records)
        return read(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", kernel)
    monkeypatch.setattr(paths, "__file__", str(repo / "src/runtime_paths.py"))
    monkeypatch.setenv(paths.POLICY_ENV, str(policy))
    return repo, root, policy, document, records


def test_explicit_mounted_subtrees_work_with_both_existing_contracts(mounted):
    _repo, root, _policy, _document, _records = mounted
    assert artifact_root(root / "archive") == root / "archive"
    assert Settings(root=root / "jobs").root == root / "jobs"
    with pytest.raises(ValueError):
        Settings(root=root / "archive")  # Purpose is not inferred from a name.


@pytest.mark.parametrize(
    "relative",
    [
        "src/output",
        "scripts/output",
        "configuration/out",
        "data/other",
        "data/lectures/loviscach",
        ".venv/out",
        ".git/out",
    ],
)
def test_other_code_and_data_roots_remain_forbidden(mounted, relative):
    repo, _root, *_rest = mounted
    with pytest.raises(ValueError):
        paths.output_path(repo / relative, "material_artifacts")


def test_absent_policy_does_not_infer_authorization(mounted, monkeypatch):
    _repo, root, *_rest = mounted
    monkeypatch.delenv(paths.POLICY_ENV)
    with pytest.raises(ValueError):
        artifact_root(root)


@pytest.mark.parametrize(
    "change",
    [
        "absent",
        "device",
        "root",
        "readonly",
        "nested",
        "ancestor",
        "stacked",
        "malformed",
    ],
)
def test_mount_changes_fail_closed(mounted, change):
    repo, root, _policy, _document, records = mounted
    if change == "absent":
        records.pop()
    elif change == "device":
        records[-1] = records[-1].replace("8:1", "8:2")
    elif change == "root":
        records[-1] = records[-1].replace("/srv/personal-assistant/data", "/srv/other")
    elif change == "readonly":
        records[-1] = records[-1].replace(" rw ", " ro ")
    elif change in {"nested", "ancestor"}:
        point = root / "archive" if change == "nested" else root
        records.append(f"11 10 8:1 /different {point} rw - ext4 /dev/vda1 rw")
    elif change == "stacked":
        records.append(records[-1])
    else:
        records[:] = ["not mountinfo"]
    with pytest.raises(ValueError):
        paths.output_path(root / "archive", "material_artifacts", repository=repo)


def test_unreadable_kernel_mount_information_fails_closed(mounted, monkeypatch):
    _repo, root, *_rest = mounted

    def denied():
        raise PermissionError("synthetic mountinfo denied")

    monkeypatch.setattr(paths, "mounts", denied)
    with pytest.raises(ValueError):
        artifact_root(root)


@pytest.mark.parametrize(
    "change",
    [
        "public",
        "missing",
        "duplicate_json",
        "unknown_version",
        "unowned",
        "policy_in_data",
        "code_mount",
        "root_mount",
    ],
)
def test_bad_operator_policy_fails_closed(mounted, change):
    repo, root, policy, document, _records = mounted
    if change == "public":
        policy.chmod(0o644)
    elif change == "missing":
        policy.unlink()
    elif change == "duplicate_json":
        policy.write_text('{"schema_version":1,"schema_version":1}')
    else:
        if change == "unknown_version":
            document["schema_version"] = 2
        elif change == "unowned":
            document["roots"][0]["owner_uid"] = os.geteuid() + 1
        elif change == "policy_in_data":
            document["roots"][0]["path"] = str(repo / "configuration")
            document["roots"][0]["mount_point"] = str(repo / "configuration")
        elif change == "code_mount":
            document["roots"][0]["path"] = str(repo / "src/output")
            document["roots"][0]["mount_point"] = str(repo / "src")
        else:
            document["roots"][0]["mount_identity"]["root"] = "/"
        policy.write_text(json.dumps(document))
    with pytest.raises(ValueError):
        artifact_root(root)


def test_symlinks_traversal_and_bad_component_permissions(mounted):
    repo, root, policy, *_rest = mounted
    root.mkdir(mode=0o700)
    outside = repo.parent / "outside"
    outside.mkdir()
    (root / "alias").symlink_to(outside, target_is_directory=True)
    for path in (root / "alias/output", root / "../other", root / "alias/../out"):
        with pytest.raises(ValueError):
            artifact_root(path)
    (root / "public").mkdir(mode=0o755)
    (root / "public").chmod(0o755)
    with pytest.raises(ValueError):
        artifact_root(root / "public/out")
    original = policy.with_suffix(".original")
    policy.rename(original)
    policy.symlink_to(original)
    with pytest.raises(ValueError):
        artifact_root(root)


def test_actual_worker_access_required(mounted, monkeypatch):
    _repo, root, *_rest = mounted
    monkeypatch.setattr(paths.os, "access", lambda *_args: False)
    with pytest.raises(ValueError):
        artifact_root(root)


def test_other_writable_mount_parent_is_not_trusted(mounted):
    repo, root, *_rest = mounted
    (repo / "data").chmod(0o777)
    with pytest.raises(ValueError):
        artifact_root(root)


def test_grant_revocation_is_not_cached(mounted):
    _repo, root, policy, document, _records = mounted
    assert artifact_root(root) == root
    document["roots"] = document["roots"][1:]
    policy.write_text(json.dumps(document))
    with pytest.raises(ValueError):
        artifact_root(root)


def test_only_policy_path_survives_existing_clean_environment(monkeypatch):
    monkeypatch.setenv(paths.POLICY_ENV, "/explicit/private/policy.json")
    monkeypatch.setenv("SYNTHETIC_SECRET", "not-forwarded")
    environment = clean_environment()
    assert environment[paths.POLICY_ENV] == "/explicit/private/policy.json"
    assert "SYNTHETIC_SECRET" not in environment


def test_external_workspaces_still_work_without_policy(tmp_path, monkeypatch):
    monkeypatch.delenv(paths.POLICY_ENV, raising=False)
    assert artifact_root(tmp_path / "archive") == tmp_path / "archive"
    assert Settings(root=tmp_path / "jobs").root == tmp_path / "jobs"


def test_policy_inside_granted_write_subtree_rejected(mounted, monkeypatch):
    _repo, root, _policy, document, _records = mounted
    root.mkdir(mode=0o700)
    unsafe = root / "policy.json"
    unsafe.write_text(json.dumps(document))
    unsafe.chmod(0o600)
    monkeypatch.setenv(paths.POLICY_ENV, str(unsafe))
    with pytest.raises(ValueError):
        artifact_root(root)


def test_kernel_mount_parser_decodes_escaped_paths(monkeypatch):
    original = Path.read_text

    def read(path, *args, **kwargs):
        if str(path) == "/proc/self/mountinfo":
            return "10 1 8:1 /srv/my\\040data /tmp/my\\040app/data rw - ext4 /dev/vda1 rw\n"
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read)
    assert paths.mounts()[Path("/tmp/my app/data")]["root"] == "/srv/my data"
