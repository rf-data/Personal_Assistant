import json
import socket
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.model_discovery.cs50 import (
    CourseDiscovery,
    DiscoveryWarning,
    MediaVariant,
    Provenance,
    ResourceCandidate,
    SectionDiscovery,
    deterministic_id,
)
from src.tools_lecture.cs50_manifest import ManifestError, load_fixture_manifest

FIXTURES = Path(__file__).resolve().parents[1] / "docs/course_sources/cs50"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def blocked(*args, **kwargs):
        pytest.fail("Discovery attempted network access")

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)


def write_manifest(tmp_path, mutate=lambda data: None):
    data = json.loads((FIXTURES / "manifest.json").read_text())
    mutate(data)
    for course in data["courses"]:
        for page in course["pages"]:
            target = tmp_path / page["file"]
            target.parent.mkdir(parents=True, exist_ok=True)
            if (FIXTURES / page["file"]).is_file():
                target.write_bytes((FIXTURES / page["file"]).read_bytes())
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(data))
    return path


def test_all_63_fixtures_are_referenced_and_original_18_preserved():
    manifest = load_fixture_manifest(FIXTURES / "manifest.json")
    files = [page.file for course in manifest.courses for page in course.pages]
    assert len(files) == 63
    historical = load_fixture_manifest(FIXTURES / "regression_manifest.json")
    assert sum(len(course.pages) for course in historical.courses[:4]) == 18
    assert set(files) == {
        str(path.relative_to(FIXTURES)) for path in FIXTURES.glob("*/*.html")
    }
    assert [len(course.pages) for course in manifest.courses] == [15, 14, 8, 10, 10, 6]
    assert {course.course_id for course in manifest.courses} == {
        "cs50x",
        "cs50_python",
        "cs50_sql",
        "cs50_ai",
        "cs50_web",
        "cs50_cybersecurity",
    }


def test_fixture_checksum_mismatch(tmp_path):
    path = write_manifest(tmp_path)
    fixture = tmp_path / "cs50_web/week_0.html"
    fixture.write_bytes(fixture.read_bytes() + b"\n<!-- modified -->")
    with pytest.raises(ManifestError, match="cs50_web/week_0.html: SHA-256 mismatch"):
        load_fixture_manifest(path)


def test_legacy_manifest_without_checksums(tmp_path):
    def remove_checksums(data):
        for course in data["courses"]:
            for page in course["pages"]:
                page.pop("sha256")

    manifest = load_fixture_manifest(write_manifest(tmp_path, remove_checksums))
    assert all(p.sha256 is None for c in manifest.courses for p in c.pages)


@pytest.mark.parametrize("digest", ["not-a-hash", "A" * 64, "1" * 63])
def test_invalid_checksum(tmp_path, digest):
    path = write_manifest(
        tmp_path, lambda d: d["courses"][0]["pages"][0].update(sha256=digest)
    )
    with pytest.raises(ManifestError, match="sha256"):
        load_fixture_manifest(path)


def test_invalid_json(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text('{"courses": [}')
    with pytest.raises(ManifestError, match="Invalid CS50 manifest.*line 1"):
        load_fixture_manifest(path)


def test_duplicate_json_keys(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text('{"provider":"Harvard","provider":"Other"}')
    with pytest.raises(ManifestError, match="Duplicate JSON key"):
        load_fixture_manifest(path)


def test_missing_file(tmp_path):
    path = write_manifest(tmp_path)
    (tmp_path / "cs50x/week_0.html").unlink()
    with pytest.raises(
        ManifestError, match="cs50x/week_0.html: fixture file not found"
    ):
        load_fixture_manifest(path)


@pytest.mark.parametrize(
    "field,value,message",
    [
        ("url", "https://cs50.harvard.edu/sql/", "contradicts course or role"),
        ("file", "cs50_sql/index.html", "file contradicts course_id"),
        ("url", "https://evil.example/x/", "contradicts course or role"),
        ("url", "https://cs50.harvard.edu/x/notes/0/", "contradicts course or role"),
        ("url", "http://cs50.harvard.edu/x/", "expected original HTTPS"),
        ("role", "lecture", "Input should be"),
        ("file", "../index.html", "normalized relative"),
    ],
)
def test_invalid_page(tmp_path, field, value, message):
    path = write_manifest(
        tmp_path, lambda d: d["courses"][0]["pages"][0].update({field: value})
    )
    with pytest.raises(ManifestError, match=message):
        load_fixture_manifest(path)


def test_saved_original_mismatch(tmp_path):
    path = write_manifest(tmp_path)
    fixture = tmp_path / "cs50_ai/week_1.html"
    fixture.write_text(
        fixture.read_text().replace(
            "https://cs50.harvard.edu/ai/weeks/1/",
            "https://cs50.harvard.edu/ai/weeks/2/",
        )
    )
    with pytest.raises(ManifestError, match="contradicts saved original"):
        load_fixture_manifest(path)


@pytest.mark.parametrize("kind", ["file", "url", "course"])
def test_duplicates(tmp_path, kind):
    def mutate(data):
        course = data["courses"][0]
        if kind == "course":
            data["courses"].append(course)
        else:
            page = dict(course["pages"][0])
            if kind == "url":
                page["file"] = "cs50x/another.html"
            course["pages"].append(page)

    path = write_manifest(tmp_path, mutate)
    with pytest.raises(ManifestError, match="Duplicate"):
        load_fixture_manifest(path)


def test_wrong_root(tmp_path):
    path = write_manifest(
        tmp_path,
        lambda d: d["courses"][0].update(source_url="https://cs50.harvard.edu/sql/"),
    )
    with pytest.raises(ManifestError, match="source_url must be"):
        load_fixture_manifest(path)


def make_course():
    section = SectionDiscovery(
        course_id="cs50x", key="ai", original_url="https://cs50.harvard.edu/x/weeks/ai/"
    )
    resource = ResourceCandidate(
        course_id="cs50x",
        role="lecture_video",
        section_keys=("ai",),
        original_url="https://video.cs50.io/example?screen=second",
        status="parsed",
        language="en",
        provenance=(
            Provenance(
                original_url=section.original_url,
                fixture_file="cs50x/week_ai.html",
                locator="main > ul > li",
                context_path=("Lecture", "Video", "English"),
            ),
        ),
        variants=(
            MediaVariant(
                original_url="https://cdn.cs50.net/example-720p.mp4",
                media_type="video",
                resolution="720p",
                dynamic_range="sdr",
                language="en",
            ),
            MediaVariant(
                original_url="https://cdn.cs50.net/example-4k-hdr.mp4",
                media_type="video",
                resolution="4k",
                dynamic_range="hdr",
                language="en",
            ),
        ),
    )
    return CourseDiscovery(
        course_id="cs50x",
        original_url="https://cs50.harvard.edu/x/",
        sections=(section,),
        resources=(resource,),
        warnings=(
            DiscoveryWarning(
                course_id="cs50x",
                code="missing_fixture",
                message="Week not locally available",
                section_key="ai",
            ),
        ),
    )


def test_models_roundtrip_variants_and_ids():
    course = make_course()
    restored = CourseDiscovery.model_validate_json(course.model_dump_json())
    assert restored == course
    assert course.sections[0].status == "referenced"
    assert course.resources[0].status == "parsed"
    assert len(course.resources[0].variants) == 2
    assert "?screen=second" in str(course.resources[0].original_url)
    assert restored.resources[0].resource_id == course.resources[0].resource_id
    assert restored.sections[0].section_id == course.sections[0].section_id
    assert deterministic_id("x", "ab", "c") != deterministic_id("x", "a", "bc")
    changed = ResourceCandidate.model_validate(
        {**course.resources[0].model_dump(), "title": "New title"}
    )
    assert changed.resource_id == course.resources[0].resource_id
    assert (
        make_course().resources[0].variants[0].variant_id
        == course.resources[0].variants[0].variant_id
    )


@pytest.mark.parametrize(
    "change,message",
    [
        ({"course_id": "cs50_sql"}, "Child course_id contradicts"),
        ({"sections": ()}, "Unknown section key"),
        ({"sections": (make_course().sections[0],) * 2}, "Duplicate section"),
        ({"unexpected": True}, "Extra inputs"),
    ],
)
def test_course_model_validation(change, message):
    data = make_course().model_dump()
    data.update(change)
    with pytest.raises(ValidationError, match=message):
        CourseDiscovery.model_validate(data)


def test_section_parent_validation():
    course = make_course()
    section = course.sections[0].model_dump()
    section["parent_key"] = "ai"
    with pytest.raises(ValidationError, match="hierarchy cycle"):
        CourseDiscovery.model_validate({**course.model_dump(), "sections": [section]})
    section["parent_key"] = "missing"
    with pytest.raises(ValidationError, match="Unknown parent section"):
        CourseDiscovery.model_validate({**course.model_dump(), "sections": [section]})


def test_invalid_variant_and_resource():
    resource = make_course().resources[0].model_dump()
    resource["variants"] *= 2
    with pytest.raises(ValidationError, match="Duplicate media variant"):
        ResourceCandidate.model_validate(resource)
    with pytest.raises(ValidationError):
        MediaVariant(original_url="file:///tmp/local.mp4", media_type="video")
    with pytest.raises(ValidationError):
        SectionDiscovery(course_id="cs50x", key="", original_url="https://example.com")


def test_symlink_escape(tmp_path):
    path = write_manifest(tmp_path)
    fixture = tmp_path / "cs50x/week_0.html"
    fixture.unlink()
    fixture.symlink_to(FIXTURES / "cs50x/week_0.html")
    with pytest.raises(ManifestError, match="escapes manifest directory"):
        load_fixture_manifest(path)


def test_multiple_sections_and_parent_resource():
    course = make_course()
    second = SectionDiscovery(
        course_id="cs50x",
        key="0",
        parent_key="ai",
        original_url="https://cs50.harvard.edu/x/weeks/0/",
        status="parsed",
    )
    parent = course.resources[0]
    child = ResourceCandidate(
        course_id="cs50x",
        role="source_code",
        section_keys=("ai", "0"),
        original_url="https://cdn.cs50.net/example.zip",
        parent_resource_id=parent.resource_id,
    )
    result = CourseDiscovery.model_validate(
        {
            **course.model_dump(),
            "sections": (course.sections[0], second),
            "resources": (parent, child),
        }
    )
    assert result.resources[1].section_keys == ("ai", "0")
    assert result.resources[1].parent_resource_id == parent.resource_id
    invalid = child.model_dump()
    invalid["parent_resource_id"] = "missing"
    with pytest.raises(ValidationError, match="Unknown parent resource"):
        CourseDiscovery.model_validate(
            {**result.model_dump(), "resources": [parent, invalid]}
        )
