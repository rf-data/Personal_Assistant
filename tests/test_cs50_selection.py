"""Selection uses local fixtures exclusively; never imports execution settings."""

import ast
import socket
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.model_discovery.cs50 import ResourceRole
from src.model_discovery.cs50_selection import SelectionPolicy
from src.tools_lecture.prepare_cs50 import discover_fixture_courses
from src.tools_lecture.select_cs50 import preview_course, render_preview

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Network forbidden")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


@pytest.fixture
def courses():
    # Preserve the original four-course regression matrix; six-course cases have
    # their own tests including fully parsed Web/Cybersecurity fixtures.
    return discover_fixture_courses(
        ROOT / "docs/course_sources/cs50/regression_manifest.json"
    )[:4]


def video(preview):
    return preview.lectures[0].decisions[1]


def text(preview):
    return preview.lectures[0].decisions[0]


def replace_lecture(course, transform):
    return course.model_copy(
        update={
            "resources": tuple(
                transform(resource)
                if resource.role == ResourceRole.LECTURE_VIDEO
                else resource
                for resource in course.resources
            )
        }
    )


def test_all_seven_default_transcripts_and_preservation(courses):
    previews = tuple(preview_course(course) for course in courses)
    assert sum(len(item.lectures) for item in previews) == 7
    for course, preview in zip(courses, previews, strict=True):
        assert preview.discovery is course
        for lecture in preview.lectures:
            assert lecture.decisions[0].selected.role == ResourceRole.TRANSCRIPT
            assert lecture.decisions[0].selected.language == "en"
            assert lecture.decisions[0].actions == ("download",)
            assert lecture.decisions[1].selected is None
    assert "cs50_ai" in render_preview(previews)


@pytest.mark.parametrize("language", ["en", "pt", "es"])
@pytest.mark.parametrize("resolution", ["360p", "720p", "1080p", "4k"])
def test_language_quality_and_exactly_one_video(courses, language, resolution):
    preview = preview_course(
        courses[0],
        SelectionPolicy(
            require_video=True,
            preferred_language=language,
            preferred_video_resolution=resolution,
        ),
    )
    for lecture in preview.lectures:
        selected = lecture.decisions[1].selected
        assert selected.language == language
        assert selected.resolution == resolution
        assert selected.dynamic_range == "sdr"
        assert lecture.decisions[1].actions == ("download",)
        assert (
            sum(
                decision.purpose == "video" and decision.selected is not None
                for decision in lecture.decisions
            )
            == 1
        )


def test_hdr_preference(courses):
    assert (
        video(
            preview_course(
                courses[0], SelectionPolicy(require_video=True, prefer_sdr=False)
            )
        ).selected.dynamic_range
        == "hdr"
    )


def test_unknown_language_explicit_opt_in(courses):
    for course in courses[1:]:
        assert (
            video(preview_course(course, SelectionPolicy(require_video=True))).selected
            is None
        )
        decision = video(
            preview_course(
                course, SelectionPolicy(require_video=True, allow_unknown_language=True)
            )
        )
        assert decision.selected.resolution == "720p"
        assert any(
            "unknown_language_selected" in warning for warning in decision.warnings
        )
    assert any("missing_dynamic_range" in warning for warning in decision.warnings)


def test_reordering_is_stable_and_does_not_mutate(courses):
    course = courses[0]
    before = course.model_dump_json()
    reordered = replace_lecture(
        course,
        lambda resource: resource.model_copy(
            update={"variants": tuple(reversed(resource.variants))}
        ),
    )
    reordered = reordered.model_copy(
        update={"resources": tuple(reversed(reordered.resources))}
    )
    policy = SelectionPolicy(require_video=True)
    assert (
        preview_course(course, policy).lectures
        == preview_course(reordered, policy).lectures
    )
    assert course.model_dump_json() == before


def test_missing_transcript_falls_back_to_subtitles(courses):
    course = courses[0].model_copy(
        update={
            "resources": tuple(
                resource
                for resource in courses[0].resources
                if resource.role != ResourceRole.TRANSCRIPT
            )
        }
    )
    decision = text(preview_course(course))
    assert decision.selected.role == ResourceRole.SUBTITLES
    assert decision.actions == ("download", "parse_subtitle")
    assert any("SRT" in warning for warning in decision.warnings)


def test_no_text_no_arbitrary_audio_transcription(courses):
    course = courses[0].model_copy(
        update={
            "resources": tuple(
                resource
                for resource in courses[0].resources
                if resource.role
                not in {ResourceRole.TRANSCRIPT, ResourceRole.SUBTITLES}
            )
        }
    )
    assert text(preview_course(course)).selected is None
    decision = text(
        preview_course(
            course,
            SelectionPolicy(allow_transcription=True, allow_unknown_language=True),
        )
    )
    assert decision.selected.role == ResourceRole.AUDIO
    assert decision.actions == ("download", "transcribe")


def test_missing_resolution_and_players_never_quality_fallback(courses):
    course = replace_lecture(
        courses[0],
        lambda resource: resource.model_copy(
            update={
                "variants": tuple(
                    variant
                    for variant in resource.variants
                    if variant.resolution != "720p"
                )
            }
        ),
    )
    decision = video(preview_course(course, SelectionPolicy(require_video=True)))
    assert decision.selected is None
    assert "kein Qualitätsfallback" in decision.reason
    assert decision.alternatives


def test_ambiguous_equal_quality_refuses_arbitrary_url(courses):
    def duplicate(resource):
        variant = next(
            item
            for item in resource.variants
            if item.language == "en"
            and item.resolution == "720p"
            and item.dynamic_range == "sdr"
        )
        extra = variant.model_copy(
            update={"original_url": "https://example.com/alternative.mp4"}
        )
        return resource.model_copy(update={"variants": (*resource.variants, extra)})

    decision = video(
        preview_course(
            replace_lecture(courses[0], duplicate), SelectionPolicy(require_video=True)
        )
    )
    assert decision.selected is None
    assert any("ambiguous_selection" in warning for warning in decision.warnings)


def test_action_vocabulary_matches_real_enum_without_import():
    module = ast.parse((ROOT / "src/model_lecture/data_resources.py").read_text())
    enum = next(
        node
        for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == "ResourceAction"
    )
    values = {
        node.value.value
        for node in enum.body
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
    }
    assert {"download", "parse_subtitle", "transcribe"} <= values


def test_invalid_policy():
    with pytest.raises(ValidationError):
        SelectionPolicy(preferred_video_resolution="480p")
    with pytest.raises(ValidationError):
        SelectionPolicy(preferred_language="")


def test_video_transcription_reuses_one_download(courses):
    course = courses[0].model_copy(
        update={
            "resources": tuple(
                resource
                for resource in courses[0].resources
                if resource.role
                not in {
                    ResourceRole.TRANSCRIPT,
                    ResourceRole.SUBTITLES,
                    ResourceRole.AUDIO,
                }
            )
        }
    )
    preview = preview_course(
        course, SelectionPolicy(require_video=True, allow_transcription=True)
    )
    for lecture in preview.lectures:
        text_decision, video_decision = lecture.decisions
        assert text_decision.selected == video_decision.selected
        assert text_decision.actions == ("transcribe",)
        assert (
            sum(decision.actions.count("download") for decision in lecture.decisions)
            == 1
        )


def test_preview_and_render_do_not_access_files_or_execution(courses, monkeypatch):
    import builtins
    import sys

    def forbidden(*args, **kwargs):
        raise AssertionError("Preview must not read or write files")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(Path, "open", forbidden)
    assert render_preview(tuple(preview_course(course) for course in courses))
    assert "src.core.config" not in sys.modules
    assert "src.tools_lecture.process_lecture" not in sys.modules
