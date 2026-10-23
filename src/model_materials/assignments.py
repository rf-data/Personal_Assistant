"""Pinned, explicitly selected overview inputs for additive C18 discovery."""

from pathlib import Path
from typing import Literal

from pydantic import field_validator

from src.job_control.models import Sha
from src.tools_lecture.cs50_manifest import FixturePage


class AssignmentSnapshot(FixturePage):
    # file is the stable provenance label; path is relocated at bundle sealing.
    role: Literal["assignment"] = "assignment"
    sha256: Sha
    path: Path

    @field_validator("path")
    @classmethod
    def bounded_path(cls, value):
        if ".." in value.parts or "\\" in str(value) or str(value) == ".":
            raise ValueError("Explicit normalized snapshot path required")
        return value
