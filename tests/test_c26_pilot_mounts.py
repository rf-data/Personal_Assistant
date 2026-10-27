"""Mount security options must survive YAML parsing as one tmpfs declaration."""

from pathlib import Path

import pytest
import yaml


@pytest.mark.parametrize(
    "name",
    [
        "compose.yaml",
        "coolify.runtime-bootstrap.compose.yaml",
        "coolify.ui.compose.yaml",
        "monitoring.compose.yaml",
        "c26-pilot.compose.yaml",
    ],
)
def test_tmpfs_options_are_one_mount_with_explicit_security_and_size(name):
    root = Path(__file__).resolve().parents[1]
    document = yaml.safe_load((root / "deployment" / name).read_bytes())
    for role in document["services"].values():
        if "tmpfs" not in role:
            continue
        assert len(role["tmpfs"]) == 1
        path, options = role["tmpfs"][0].split(":", 1)
        assert path == "/tmp"
        assert {"rw", "noexec", "nosuid", "nodev"} <= set(options.split(","))
        assert any(option.startswith("size=") for option in options.split(","))
