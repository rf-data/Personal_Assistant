"""Local profiles for the existing CS50 adapter, never a source acquisition API."""

from pathlib import Path
from urllib.parse import urlsplit

from src.job_control.catalog import read_file, safe_path
from src.job_control.models import fingerprint
from src.model_materials.week import CourseProfile, SectionProfile
from src.tools_lecture import cs50_manifest, prepare_cs50
from src.tools_materials import batch as api
from src.tools_materials.processing import make_plan
from src.tools_materials.quality import _json

EXPECTED_TASKS = (
    "Indoor Voice",
    "Playback Speed",
    "Making Faces",
    "Einstein",
    "Tip Calculator",
)


def adapter_revision():
    return fingerprint(
        {
            name: api.sha(read_file(Path(module.__file__)))
            for name, module in (("manifest", cs50_manifest), ("parser", prepare_cs50))
        }
    )


def bounded_manifest(path):
    """Bound the declared discovery closure before using the existing loader."""
    data = cs50_manifest.FixtureManifest.model_validate(_json(read_file(path, 1048576)))
    pages = [p for c in data.courses for p in c.pages]
    if len(pages) > 120:
        raise ValueError("Discovery snapshot count exceeds existing bundle limit")
    total = 0
    for page in pages:
        raw = read_file(safe_path(path.parent, page.file), 1048576)
        total += len(raw)
        if total > 8 * 1048576:
            raise ValueError("Discovery snapshot closure exceeds 8 MiB")
        if page.sha256 is None or api.sha(raw) != page.sha256:
            raise ValueError("Declared discovery snapshot hash missing or changed")
    return cs50_manifest.load_fixture_manifest(path)


def load_profile(manifest, course_id):
    """Explicit supported snapshot sections; no inference from a domain alone."""
    path = safe_path(Path(manifest))
    data = bounded_manifest(path)
    course = next((c for c in data.courses if c.course_id == course_id), None)
    if course is None:
        raise ValueError("Unknown/absent course profile")
    graph = make_plan(path)
    sections = []
    for page in course.pages:
        if page.role != "week_overview":
            continue
        key = urlsplit(str(page.url)).path.rstrip("/").rsplit("/", 1)[-1]
        roots = tuple(
            dict.fromkeys(
                b.original_url
                for b in graph.materials
                if b.resource.course_id == course_id
                and key in b.resource.section_keys
                and b.role == "problem_set"
                and urlsplit(b.original_url).path.rstrip("/").endswith("/" + key)
            )
        )
        sections.append(
            SectionProfile(
                key=key,
                overview_url=page.url,
                assignment_roots=roots,
                expected_tasks=EXPECTED_TASKS
                if (course_id, key) == ("cs50_python", "0")
                else (),
            )
        )
    if any(page.sha256 is None for page in course.pages):
        raise ValueError("Profile requires declared snapshot hashes")
    return CourseProfile(
        course_id=course_id,
        adapter_sha256=adapter_revision(),
        manifest_sha256=api.sha(read_file(path)),
        snapshots={p.file: p.sha256 for p in course.pages},
        sections=tuple(sections),
    )


def validate_profile(profile, manifest):
    profile = CourseProfile.model_validate_json(profile.model_dump_json())
    if (profile.discovery_adapter, profile.adapter_version) != ("cs50_navigation", "1"):
        raise ValueError("Unknown or incompatible discovery adapter")
    if profile.adapter_sha256 != adapter_revision():
        raise ValueError("Discovery adapter revision changed")
    path = safe_path(manifest)
    if api.sha(read_file(path)) != profile.manifest_sha256:
        raise ValueError("Profile manifest hash changed")
    data = bounded_manifest(path)
    course = next((c for c in data.courses if c.course_id == profile.course_id), None)
    if course is None or profile.snapshots != {p.file: p.sha256 for p in course.pages}:
        raise ValueError("Profile snapshot binding changed")
    pages = {str(p.url): p for p in course.pages if p.role == "week_overview"}
    for section in profile.sections:
        url = str(section.overview_url)
        if (
            url not in pages
            or urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1] != section.key
        ):
            raise ValueError("Section does not match declared overview snapshot")
    for name, digest in profile.snapshots.items():
        if api.sha(read_file(safe_path(path.parent, name))) != digest:
            raise ValueError("Profile snapshot hash changed")
    return profile
