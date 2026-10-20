"""Complete 50-week coverage; no HTTP, execution runner or LLM imports."""

import socket
from collections import Counter
from pathlib import Path

import pytest

from src.model_discovery.cs50 import ResourceRole
from src.tools_lecture.cs50_manifest import load_fixture_manifest
from src.tools_lecture.prepare_cs50 import (
    combine_course_pages,
    discover_fixture_courses,
    parse_week_page,
)
from src.tools_lecture.select_cs50 import preview_course

ROOT = Path(__file__).resolve().parents[1] / "docs/course_sources/cs50"


@pytest.fixture(scope="module", autouse=True)
def no_network():
    def forbidden(*args, **kwargs):
        raise AssertionError("Offline coverage attempted network access")

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(socket, "socket", forbidden)
        monkeypatch.setattr(socket, "getaddrinfo", forbidden)
        monkeypatch.setattr(socket, "create_connection", forbidden)
        yield


@pytest.fixture(scope="module")
def courses(no_network):
    return discover_fixture_courses(ROOT / "manifest.json")


def test_every_fixture_has_verifiable_hash():
    manifest = load_fixture_manifest(ROOT / "manifest.json")
    assert len([p for c in manifest.courses for p in c.pages]) == 63
    assert all(
        p.sha256 and len(p.sha256) == 64 for c in manifest.courses for p in c.pages
    )


@pytest.mark.parametrize(
    "course_id,count",
    [
        ("cs50x", 12),
        ("cs50_python", 10),
        ("cs50_sql", 7),
        ("cs50_ai", 7),
        ("cs50_web", 9),
        ("cs50_cybersecurity", 5),
    ],
)
def test_one_main_lecture_and_english_timed_source_per_section(
    courses, course_id, count
):
    course = next(c for c in courses if c.course_id == course_id)
    assert len(course.sections) == count
    assert all(s.status == "parsed" for s in course.sections)
    assert not any(w.code == "missing_week_fixture" for w in course.warnings)
    lectures = [r for r in course.resources if r.role == ResourceRole.LECTURE_VIDEO]
    assert Counter(key for r in lectures for key in r.section_keys) == {
        section.key: 1 for section in course.sections
    }
    for section in course.sections:
        candidates = [r for r in course.resources if section.key in r.section_keys]
        assert (
            sum(
                r.role == ResourceRole.SUBTITLES
                and r.format == "srt"
                and r.language == "en"
                for r in candidates
            )
            == 1
        )
        assert (
            sum(
                r.role == ResourceRole.TRANSCRIPT
                and r.format == "txt"
                and r.language == "en"
                for r in candidates
            )
            == 1
        )
        assert any(r.role == ResourceRole.NOTES for r in candidates)
        assert any(r.role == ResourceRole.SLIDES for r in candidates)
        assert any(v.format == "mp4" for r in candidates for v in r.variants)
    assert len(preview_course(course).lectures) == count


def test_non_numeric_ai_and_actual_resource_absences(courses):
    cs50x = courses[0]
    assert [s.key for s in cs50x.sections] == [
        *map(str, range(8)),
        "ai",
        "8",
        "9",
        "10",
    ]
    lecture = next(
        r
        for r in cs50x.resources
        if r.role == ResourceRole.LECTURE_VIDEO and r.section_keys == ("ai",)
    )
    assert lecture.title == "Artificial Intelligence"
    assert {v.language for v in lecture.variants if v.format == "mp4"} == {
        "en",
        "pt",
        "es",
    }
    assert not any(
        r.role == ResourceRole.SOURCE_CODE and "10" in r.section_keys
        for r in cs50x.resources
    )
    # A seminar link is retained, without inventing its internal resources.
    other = [r for r in cs50x.resources if r.role == ResourceRole.OTHER]
    assert len(other) == 1 and other[0].section_keys == ("10",)
    assert other[0].provenance[0].context_path == ("Seminars",)
    assert sum(w.code == "unknown_resource_role" for w in cs50x.warnings) == 1
    assert not any(r.format == "vtt" for c in courses for r in c.resources)


def test_existing_resource_and_variant_identities_are_preserved(courses):
    historical = discover_fixture_courses(ROOT / "regression_manifest.json")
    for before, after in zip(historical, courses, strict=True):
        by_id = {r.resource_id: r for r in after.resources}
        assert len(by_id) == len(after.resources)
        for resource in before.resources:
            current = by_id[resource.resource_id]
            assert (
                current.original_url == resource.original_url
                and current.role == resource.role
            )
            assert set(current.section_keys) >= set(resource.section_keys)
            assert set(current.provenance) >= set(resource.provenance)
            variants = {v.variant_id: v for v in current.variants}
            assert len(variants) == len(current.variants)
            for variant in resource.variants:
                assert variants[variant.variant_id] == variant


def test_replaying_parsed_week_does_not_duplicate_graph(courses):
    course = courses[0]
    page = parse_week_page(
        (ROOT / "cs50x/week_ai.html").read_text(),
        "https://cs50.harvard.edu/x/weeks/ai/",
        course_id="cs50x",
        fixture_file="cs50x/week_ai.html",
    )
    assert combine_course_pages(course, [page, page]) == course
