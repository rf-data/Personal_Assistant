"""SRT-first planning against all 50 fixtures; execution/network are forbidden."""

import runpy
import socket
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.model_discovery.cs50 import ResourceRole
from src.model_discovery.cs50_selection import CoursePreview, SelectionPolicy
from src.tools_lecture.prepare_cs50 import discover_fixture_courses
from src.tools_lecture.select_cs50 import (
    preview_course,
    render_preview,
    select_optional_txt,
)

ROOT = Path(__file__).resolve().parents[1] / "docs/course_sources/cs50"
TIMED = SelectionPolicy(text_strategy="timed_knowledge")


@pytest.fixture(scope="module", autouse=True)
def offline():
    def forbidden(*args, **kwargs):
        raise AssertionError("Network forbidden")

    with pytest.MonkeyPatch.context() as patch:
        for name in ("socket", "getaddrinfo", "create_connection"):
            patch.setattr(socket, name, forbidden)
        yield


@pytest.fixture(scope="module")
def courses(offline):
    return discover_fixture_courses(ROOT / "manifest.json")


def decision(course, policy=TIMED):
    return preview_course(course, policy).lectures[0].decisions[0]


def first_srt(course):
    lecture = preview_course(course).lectures[0]
    return next(
        r
        for r in course.resources
        if r.role == ResourceRole.SUBTITLES
        and r.language == "en"
        and r.section_keys == lecture.section_keys
    )


def replace_resource(course, original, replacement):
    return course.model_copy(
        update={
            "resources": tuple(
                replacement if r == original else r for r in course.resources
            )
        }
    )


@pytest.mark.parametrize(
    "index,count", [(0, 12), (1, 10), (2, 7), (3, 7), (4, 9), (5, 5)]
)
def test_all_50_preserve_identity_and_never_select_media(courses, index, count):
    course = courses[index]
    before = course.model_dump_json()
    preview = preview_course(
        course,
        TIMED.model_copy(
            update={
                "require_video": True,
                "allow_transcription": True,
                "allow_unknown_language": True,
            }
        ),
    )
    assert len(preview.lectures) == count
    assert preview.discovery is course
    for lecture in preview.lectures:
        text, video = lecture.decisions
        selected = text.selected
        assert selected and selected.role == ResourceRole.SUBTITLES
        assert selected.format == "srt" and selected.language == "en"
        assert text.actions == ("download", "parse_subtitle")
        assert video.selected is None and video.actions == ()
        resource = next(
            r for r in course.resources if r.resource_id == selected.resource_id
        )
        assert selected.original_url == resource.original_url
        assert resource.section_keys == lecture.section_keys
        assert resource.parent_resource_id in (None, lecture.resource_id)
        assert sum(d.selected is not None for d in lecture.decisions) == 1
    assert course.model_dump_json() == before
    assert CoursePreview.model_validate_json(preview.model_dump_json()) == preview


def test_reordering_resources_and_variants_is_stable(courses):
    for course in courses:
        reversed_course = course.model_copy(
            update={
                "resources": tuple(
                    r.model_copy(update={"variants": tuple(reversed(r.variants))})
                    for r in reversed(course.resources)
                )
            }
        )
        assert (
            preview_course(reversed_course, TIMED).lectures
            == preview_course(course, TIMED).lectures
        )


@pytest.mark.parametrize(
    "change",
    [
        {"language": None},
        {"language": "es"},
        {"format": "vtt"},
        {"provenance": ()},
        {"original_url": "https://example.com/lecture0.srt"},
        {
            "original_url": "https://cdn.cs50.net/sql/2022/fall/lectures/0/lang/en/lecture0.srt"
        },
        {"section_keys": ()},
    ],
)
def test_unsuitable_metadata_no_fallback(courses, change):
    course = courses[1]
    resource = first_srt(course)
    changed = replace_resource(course, resource, resource.model_copy(update=change))
    policy = TIMED.model_copy(
        update={
            "allow_unknown_language": True,
            "allow_transcription": True,
            "require_video": True,
        }
    )
    result = decision(changed, policy)
    assert result.selected is None and result.actions == ()
    assert "kein TXT-, VTT-, Audio- oder Video-Fallback" in result.reason
    assert all(
        d.selected is None
        for d in preview_course(changed, policy).lectures[0].decisions
    )


def test_missing_srt_and_multiple_official_candidates(courses):
    course = courses[1]
    resource = first_srt(course)
    missing = course.model_copy(
        update={"resources": tuple(r for r in course.resources if r != resource)}
    )
    assert decision(missing).selected is None
    duplicate = resource.model_copy(
        update={
            "original_url": str(resource.original_url).replace(
                "lecture0.srt", "alternate.srt"
            )
        }
    )
    ambiguous = course.model_copy(update={"resources": (*course.resources, duplicate)})
    result = decision(ambiguous)
    assert result.selected is None and result.actions == ()
    assert "mehrdeutig" in result.reason


def test_ambiguous_lecture_assignment_is_rejected(courses):
    course = courses[1]
    resource = first_srt(course)
    main = next(r for r in course.resources if r.role == ResourceRole.LECTURE_VIDEO)
    second = main.model_copy(
        update={"original_url": "https://www.youtube.com/watch?v=second"}
    )
    unparented = resource.model_copy(update={"parent_resource_id": None})
    changed = replace_resource(course, resource, unparented)
    changed = changed.model_copy(update={"resources": (*changed.resources, second)})
    result = decision(changed)
    assert result.selected is None
    assert "mehrdeutig" in result.reason


def test_legacy_policy_and_preview_roundtrips(courses):
    default = SelectionPolicy()
    assert "text_strategy" not in default.model_dump()
    assert SelectionPolicy.model_validate_json(default.model_dump_json()) == default
    assert SelectionPolicy.model_validate_json("{}").text_strategy == "transcript_first"
    assert SelectionPolicy.model_validate_json(TIMED.model_dump_json()) == TIMED
    old_preview = preview_course(courses[1])
    assert "text_strategy" not in old_preview.model_dump()["policy"]
    assert (
        CoursePreview.model_validate_json(old_preview.model_dump_json()) == old_preview
    )
    assert all(
        lecture.decisions[0].selected.format == "txt"
        for lecture in old_preview.lectures
    )
    with pytest.raises(ValidationError):
        SelectionPolicy(text_strategy="whisper")


def test_optional_txt_requires_separate_request(courses):
    course = courses[1]
    lecture = preview_course(course, TIMED).lectures[0]
    candidates = tuple(
        r for r in course.resources if r.section_keys == lecture.section_keys
    )
    supplement = select_optional_txt(candidates, TIMED)
    assert supplement.selected.format == "txt"
    assert supplement.actions == ("download",)
    assert "kein zeitbasierter Knowledge-Primärinput" in supplement.reason
    assert lecture.decisions[0].selected.format == "srt"
    assert len(lecture.decisions) == 2


def test_cli_writes_only_separate_knowledge_preview(courses, monkeypatch, tmp_path):
    script = ROOT.parents[2] / "scripts/report_cs50_sources.py"
    monkeypatch.setattr(
        sys, "argv", [str(script), "--knowledge-preview", "--output", str(tmp_path)]
    )
    runpy.run_path(str(script), run_name="__main__")
    assert [p.name for p in tmp_path.iterdir()] == ["knowledge_selection_preview.md"]
    expected = render_preview(
        tuple(preview_course(course, TIMED) for course in courses)
    )
    assert (tmp_path / "knowledge_selection_preview.md").read_text() == expected
    assert (
        ROOT.parents[1] / "cs50/operations/knowledge_selection_preview.md"
    ).read_text() == expected
