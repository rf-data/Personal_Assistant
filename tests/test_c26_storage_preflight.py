"""Capacity observations use existing budgets and perform no filesystem writes."""

from types import SimpleNamespace

import pytest

from scripts.c26_storage_preflight import check, main


@pytest.mark.parametrize(
    "free,inodes,total,status",
    [
        (4 * 1024**3, 100, 200, "blocked"),
        (10 * 1024**3, 0, 200, "blocked"),
        (10 * 1024**3, 0, 0, "operator_action_required"),
        (10 * 1024**3, 100, 200, "operator_action_required"),
    ],
)
def test_capacity_and_inode_observations_never_authorize_work(
    tmp_path, monkeypatch, free, inodes, total, status
):
    (tmp_path / "keep").write_bytes(b"unchanged")
    before = {p: p.read_bytes() for p in tmp_path.iterdir()}
    monkeypatch.setattr("shutil.disk_usage", lambda _: SimpleNamespace(free=free))
    monkeypatch.setattr(
        "os.statvfs", lambda _: SimpleNamespace(f_favail=inodes, f_files=total)
    )
    report = check(tmp_path)
    assert report["status"] == status and not report["execution_permitted"]
    assert report["reserve_bytes"] == 5 * 1024**3
    assert report["required_free_bytes"] == 5 * 1024**3 + 80 * 1024**2
    assert report["inode_status"] == ("unknown" if not total else "observed")
    assert {p: p.read_bytes() for p in tmp_path.iterdir()} == before


def test_no_implicit_target_creation_or_unverified_week_estimate(tmp_path, capsys):
    missing = tmp_path / "new"
    assert main(["--target-parent", str(missing)]) == 3
    assert not missing.exists()
    assert main(["--target-parent", str(tmp_path), "--purpose", "week-pilot"]) == 3
    assert "execution_permitted" in capsys.readouterr().out
    with pytest.raises(ValueError):
        check(tmp_path, purpose="unknown")
