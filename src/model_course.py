"""Explicit Content/ACL course scope; CS50 discovery keeps its own closed set."""

from typing import Literal

from src.model_discovery.cs50 import CourseId

ContentCourseId = Literal[CourseId, "loviscach_mathe_1"]
