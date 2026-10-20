"""Real six-course fixtures, with all network access disabled."""

import hashlib
import json
import socket
from pathlib import Path

import pytest

from src.model_discovery.cs50 import CourseDiscovery, ResourceRole
from src.model_discovery.cs50_selection import SelectionPolicy
from src.tools_lecture.prepare_cs50 import discover_fixture_courses
from src.tools_lecture.select_cs50 import preview_course

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/course_sources/cs50/manifest.json"
ORIGINAL_HASHES = {
    "cs50x": "73b5300df02f0add0a5f30dfe951f839f4b7850e50d03b6774acaf673b7fea7b",
    "cs50_python": "8c1256b66d2ac2ad7ffce548410ccbff670d32a47eb53fd1a846cf993ab332b8",
    "cs50_sql": "05c1b24b11d990b95eae8086093731d5cde9f438dd7e1beaec1fcc6014b83d85",
    "cs50_ai": "2a0ff96345bef0732962268e67b4ab96c62441c4d9bc30a3d6047cf7a6c1a8fc",
}
NEW_TITLES = {
    "cs50_web": [
        "HTML, CSS",
        "Git",
        "Python",
        "Django",
        "SQL, Models, and Migrations",
        "JavaScript",
        "User Interfaces",
        "Testing, CI/CD",
        "Scalability and Security",
    ],
    "cs50_cybersecurity": [
        "Securing Accounts",
        "Securing Data",
        "Securing Systems",
        "Securing Software",
        "Preserving Privacy",
    ],
}


@pytest.fixture
def courses(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Network forbidden during discovery/selection")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    return discover_fixture_courses(MANIFEST)


def test_original_graphs_ids_provenance_and_previews_are_unchanged(courses):
    # Captured before extending CourseId or editing the parser, not regenerated
    # from the new implementation. Includes full variants, IDs and provenance.
    for course in discover_fixture_courses(
        MANIFEST.with_name("regression_manifest.json")
    )[:4]:
        payload = {
            "discovery": course.model_dump(mode="json"),
            "preview": preview_course(course).model_dump(mode="json"),
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()
        assert digest == ORIGINAL_HASHES[course.course_id]


@pytest.mark.parametrize(
    "course_id,count", [("cs50_web", 9), ("cs50_cybersecurity", 5)]
)
def test_complete_navigation_and_unique_lecture_assignment(courses, course_id, count):
    course = next(c for c in courses if c.course_id == course_id)
    assert [s.key for s in course.sections] == list(map(str, range(count)))
    assert [s.title for s in course.sections] == NEW_TITLES[course_id]
    assert [s.order for s in course.sections] == list(range(count))
    assert all(s.status == "parsed" for s in course.sections)
    lectures = [r for r in course.resources if r.role == ResourceRole.LECTURE_VIDEO]
    assert len(lectures) == count
    assert {r.section_keys for r in lectures} == {(str(i),) for i in range(count)}
    assert len({r.resource_id for r in course.resources}) == len(course.resources)
    assert CourseDiscovery.model_validate_json(course.model_dump_json()) == course
    for resource in course.resources:
        assert resource.course_id == course_id and resource.section_keys
        assert all(
            key in {s.key for s in course.sections} for key in resource.section_keys
        )
        assert resource.provenance
        for variant in resource.variants:
            assert variant.provenance
            assert all(
                p.fixture_file.startswith(course_id + "/") for p in variant.provenance
            )


def test_web_imperative_lecture_and_inline_projects(courses):
    web = courses[4]
    assert not web.warnings
    assert sum(r.role == ResourceRole.PROJECT for r in web.resources) == 6
    assert any(
        str(r.original_url).endswith("/projects/final/")
        for r in web.resources
        if r.role == ResourceRole.PROJECT
    )
    for lecture in (r for r in web.resources if r.role == ResourceRole.LECTURE_VIDEO):
        direct = [v for v in lecture.variants if v.format == "mp4"]
        assert {v.resolution for v in direct} == {"360p", "720p", "1080p", "4k"}
        assert all(v.dynamic_range is None for v in direct)
        assert {v.format for v in lecture.variants} == {"mp4", "cs50_player", "youtube"}
        assert any(".mp4.download" in str(v.original_url) for v in direct)


def test_cybersecurity_source_code_pdf_is_not_slides(courses):
    course = courses[5]
    source = [r for r in course.resources if r.role == ResourceRole.SOURCE_CODE]
    assert {r.format for r in source} == {None, "pdf", "zip"}
    assert {r.section_keys for r in source} == {("0",)}
    assert all("src0" in str(r.original_url) for r in source)
    assert all(
        "src0" not in str(r.original_url)
        for r in course.resources
        if r.role == ResourceRole.SLIDES
    )
    assert sum(r.role == ResourceRole.PROBLEM_SET for r in course.resources) == 5
    assert sum(r.role == ResourceRole.PROJECT for r in course.resources) == 1


def test_cybersecurity_ranges_and_inconsistent_player_ids_preserved(courses):
    cyber = courses[5]
    lectures = [r for r in cyber.resources if r.role == ResourceRole.LECTURE_VIDEO]
    for lecture in lectures:
        assert {
            (v.resolution, v.dynamic_range)
            for v in lecture.variants
            if v.format == "mp4"
        } == {
            (quality, dynamic_range)
            for quality in ("360p", "720p", "1080p", "4k")
            for dynamic_range in ("hdr", "sdr")
        }
    ids = {v.media_id for v in lectures[0].variants if v.media_id}
    assert ids == {"kUovJpWqEMk", "fJYdAN4Vh5c"}
    assert [(w.code, w.section_key) for w in cyber.warnings] == [
        ("multiple_lecture_media_ids", "0")
    ]


@pytest.mark.parametrize("course_index", [4, 5])
def test_text_and_video_previews_no_duplicate_downloads(courses, course_index):
    course = courses[course_index]
    before = course.model_dump_json()
    strict = preview_course(course, SelectionPolicy(require_video=True))
    assert all(
        lecture.decisions[0].selected.format == "txt" for lecture in strict.lectures
    )
    assert all(
        lecture.decisions[0].selected.language == "en" for lecture in strict.lectures
    )
    assert all(lecture.decisions[1].selected is None for lecture in strict.lectures)
    policy = SelectionPolicy(require_video=True, allow_unknown_language=True)
    preview = preview_course(course, policy)
    selected = []
    for lecture in preview.lectures:
        text, video = lecture.decisions
        assert text.actions == video.actions == ("download",)
        assert video.selected.resolution == "720p" and video.selected.format == "mp4"
        assert video.selected.resource_id == lecture.resource_id
        assert video.selected.dynamic_range == ("sdr" if course_index == 5 else None)
        selected.append(str(video.selected.original_url))
    assert len(set(selected)) == len(preview.lectures)
    reversed_course = course.model_copy(
        update={
            "resources": tuple(
                r.model_copy(update={"variants": tuple(reversed(r.variants))})
                for r in reversed(course.resources)
            )
        }
    )
    assert preview_course(reversed_course, policy).lectures == preview.lectures
    assert course.model_dump_json() == before


def test_six_course_totals_and_offered_transcript_formats(courses):
    assert len(courses) == 6 and sum(len(c.sections) for c in courses) == 50
    assert sum(len(preview_course(c).lectures) for c in courses) == 50
    assert sum(s.status == "parsed" for c in courses for s in c.sections) == 50
    for course in courses[4:]:
        for section in course.sections:
            resources = [r for r in course.resources if section.key in r.section_keys]
            assert {
                (r.role, r.format)
                for r in resources
                if r.role in {ResourceRole.SUBTITLES, ResourceRole.TRANSCRIPT}
            } == {(ResourceRole.SUBTITLES, "srt"), (ResourceRole.TRANSCRIPT, "txt")}
