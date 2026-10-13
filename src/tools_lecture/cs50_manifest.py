"""Validate CS50 HTML fixtures without fetching or extracting course content."""

import json
import re
from pathlib import Path, PurePosixPath
from typing import Literal, Self
from urllib.parse import urlsplit

from pydantic import HttpUrl, ValidationError, field_validator, model_validator

from src.model_discovery.cs50 import CourseId, DiscoveryModel

COURSE_PATHS = {
    "cs50x": "x",
    "cs50_python": "python",
    "cs50_sql": "sql",
    "cs50_ai": "ai",
}
FixtureRole = Literal[
    "course_index",
    "week_overview",
    "lecture_notes",
    "practice_overview",
    "assignment",
    "source_code_index",
]


class ManifestError(ValueError):
    """A malformed manifest or inconsistent local fixture."""


class FixturePage(DiscoveryModel):
    file: str
    url: HttpUrl
    role: FixtureRole

    @field_validator("file")
    @classmethod
    def relative_html_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        if (
            path.is_absolute()
            or ".." in path.parts
            or "\\" in value
            or path.suffix != ".html"
            or path.as_posix() != value
        ):
            raise ValueError("Fixture file must be a normalized relative .html path")
        return value


class FixtureCourse(DiscoveryModel):
    course_id: CourseId
    source_url: HttpUrl
    pages: tuple[FixturePage, ...]

    @model_validator(mode="after")
    def course_urls(self) -> Self:
        prefix = COURSE_PATHS[self.course_id]
        expected_root = f"https://cs50.harvard.edu/{prefix}/"
        if str(self.source_url) != expected_root:
            raise ValueError(f"{self.course_id}: source_url must be {expected_root}")
        for page in self.pages:
            label = f"{self.course_id}/{page.file}"
            if PurePosixPath(page.file).parts[0] != self.course_id:
                raise ValueError(f"{label}: file contradicts course_id")
            url = urlsplit(str(page.url))
            if url.scheme != "https" or url.query or url.fragment or url.username:
                raise ValueError(
                    f"{label}: expected original HTTPS URL without query/fragment"
                )
            if page.role == "source_code_index":
                cdn_prefix = "" if self.course_id == "cs50x" else f"{prefix}/"
                pattern = rf"/{cdn_prefix}\d{{4}}/[^/]+/lectures/[^/]+/src[^/]+/"
                valid = url.netloc == "cdn.cs50.net" and re.fullmatch(pattern, url.path)
            else:
                patterns = {
                    "course_index": rf"/{prefix}/",
                    "week_overview": rf"/{prefix}/weeks/[^/]+/",
                    "lecture_notes": rf"/{prefix}/notes/[^/]+/",
                    "practice_overview": rf"/{prefix}/practice/",
                    "assignment": rf"/{prefix}/(?:psets|projects|quizzes|practice)/[^/]+(?:/[^/]+)*/",
                }
                valid = url.netloc == "cs50.harvard.edu" and re.fullmatch(
                    patterns[page.role], url.path
                )
            if not valid:
                raise ValueError(
                    f"{label}: URL {page.url} contradicts course or role {page.role}"
                )
        return self


class FixtureManifest(DiscoveryModel):
    provider: Literal["Harvard"]
    platform: Literal["CS50"]
    courses: tuple[FixtureCourse, ...]

    @model_validator(mode="after")
    def unique_entries(self) -> Self:
        courses: set[str] = set()
        files: set[str] = set()
        urls: set[str] = set()
        if not self.courses:
            raise ValueError("Manifest contains no courses")
        for course in self.courses:
            if course.course_id in courses:
                raise ValueError(f"Duplicate course_id: {course.course_id}")
            courses.add(course.course_id)
            if not course.pages:
                raise ValueError(f"{course.course_id}: no fixture pages")
            for page in course.pages:
                if page.file in files:
                    raise ValueError(f"Duplicate fixture file: {page.file}")
                if str(page.url) in urls:
                    raise ValueError(f"Duplicate fixture URL: {page.url}")
                files.add(page.file)
                urls.add(str(page.url))
        return self


def _unique_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def load_fixture_manifest(path: Path | str) -> FixtureManifest:
    """Paths resolve relative to the manifest; errors include fixture provenance.

    The browser's saved-from comment is checked when present, but is not
    required for future raw HTML fixtures. No DOM extraction or HTTP occurs.
    """
    path = Path(path)
    try:
        data = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_unique_json_keys
        )
        manifest = FixtureManifest.model_validate(data)
    except (OSError, UnicodeError, ValueError, ValidationError) as exc:
        raise ManifestError(f"Invalid CS50 manifest {path}: {exc}") from exc
    root = path.parent.resolve()
    seen_paths: set[Path] = set()
    for course in manifest.courses:
        for page in course.pages:
            fixture = (root / page.file).resolve()
            if not fixture.is_relative_to(root):
                raise ManifestError(f"{page.file}: fixture escapes manifest directory")
            if fixture in seen_paths:
                raise ManifestError(f"{page.file}: duplicate resolved fixture path")
            seen_paths.add(fixture)
            if not fixture.is_file():
                raise ManifestError(f"{page.file}: fixture file not found: {fixture}")
            try:
                html = fixture.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise ManifestError(f"{page.file}: cannot read fixture: {exc}") from exc
            original = re.search(
                r"<!--\s*saved from url=\(\d+\)(https?://\S+)\s*-->", html
            )
            if original and original.group(1) != str(page.url):
                raise ManifestError(
                    f"{page.file}: URL {page.url} contradicts saved original {original.group(1)}"
                )
    return manifest
