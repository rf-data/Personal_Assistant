"""Fail on network/listener calls and native infrastructure commands in pytest.

This is a test assertion boundary, not an OS sandbox. Isolated (-I) child Python
processes must supply their own network guard; the managed execution sandbox and
existing subprocess fixtures remain necessary.
"""

import os
import shlex
import socket
import subprocess
from pathlib import Path

import pytest


def forbidden(*args, **kwargs):
    raise AssertionError("Offline profile forbids network/listeners")


def pytest_configure(config):
    patch = pytest.MonkeyPatch()
    config.add_cleanup(patch.undo)
    for name in ("connect", "connect_ex", "bind", "listen"):
        patch.setattr(socket.socket, name, forbidden)
    for name in ("create_connection", "getaddrinfo"):
        patch.setattr(socket, name, forbidden)
    original = subprocess.Popen

    def offline_process(args, *positional, **kwargs):
        if kwargs.get("shell"):
            raise AssertionError("Offline profile requires explicit subprocess argv")
        words = shlex.split(args) if isinstance(args, str) else list(args)
        executable = kwargs.get("executable") or words[0]
        if Path(os.fsdecode(executable)).name in {
            "docker",
            "podman",
            "ssh",
            "scp",
            "sftp",
            "kubectl",
            "curl",
            "wget",
            "aws",
            "gcloud",
            "az",
        }:
            raise AssertionError("Offline profile forbids infrastructure commands")
        return original(args, *positional, **kwargs)

    patch.setattr(subprocess, "Popen", offline_process)
