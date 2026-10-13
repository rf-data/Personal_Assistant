"""Offline behavioral tests of the real snapshots and structural edge cases."""

import http.client
import socket
import urllib.request
from collections import Counter
from pathlib import Path

import pytest

from src.model_discovery.cs50 import CourseDiscovery, MediaVariant, ResourceCandidate
from src.tools_lecture import prepare_cs50
from src.tools_lecture.prepare_cs50 import (
    CS50ParseError,
    combine_course_pages,
    discover_fixture_courses,
    merge_resource_candidates,
    parse_course_index,
    parse_week_page,
)

FIXTURES = Path(__file__).resolve().parents[1] / "docs/course_sources/cs50"
ROOTS = {"cs50x": "x", "cs50_python": "python", "cs50_sql": "sql", "cs50_ai": "ai"}
EXPECTED_KEYS = {
    "cs50x": [*map(str, range(8)), "ai", "8", "9", "10"],
    "cs50_python": list(map(str, range(10))),
    "cs50_sql": list(map(str, range(7))),
    "cs50_ai": list(map(str, range(7))),
}
EXPECTED_TITLES = {
    "cs50x": [
        "Week 0 Scratch",
        "Week 1 C",
        "Week 2 Arrays",
        "Week 3 Algorithms",
        "Week 4 Memory",
        "Week 5 Data Structures",
        "Week 6 Python",
        "Week 7 SQL",
        "Artificial Intelligence",
        "Week 8 HTML, CSS, JavaScript",
        "Week 9 Flask",
        "Week 10 The End",
    ],
    "cs50_python": [
        "Functions, Variables",
        "Conditionals",
        "Loops",
        "Exceptions",
        "Libraries",
        "Unit Tests",
        "File I/O",
        "Regular Expressions",
        "Object-Oriented Programming",
        "Et Cetera",
    ],
    "cs50_sql": [
        "Querying",
        "Relating",
        "Designing",
        "Writing",
        "Viewing",
        "Optimizing",
        "Scaling",
    ],
    "cs50_ai": [
        "Search",
        "Knowledge",
        "Uncertainty",
        "Optimization",
        "Learning",
        "Neural Networks",
        "Language",
    ],
}
PARSED_KEYS = {
    "cs50x": ["0", "1"],
    "cs50_python": ["0", "5"],
    "cs50_sql": ["0", "6"],
    "cs50_ai": ["1"],
}


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def blocked(*args, **kwargs):
        pytest.fail("Offline extraction attempted a network request")

    for target, name in (
        (socket, "socket"),
        (socket, "create_connection"),
        (socket, "getaddrinfo"),
        (urllib.request, "urlopen"),
        (http.client.HTTPConnection, "connect"),
    ):
        monkeypatch.setattr(target, name, blocked)


@pytest.fixture
def courses():
    return {
        course.course_id: course
        for course in discover_fixture_courses(FIXTURES / "regression_manifest.json")
        if course.course_id in ROOTS
    }


def index_fixture(course_id):
    return parse_course_index(
        (FIXTURES / course_id / "index.html").read_text(),
        f"https://cs50.harvard.edu/{ROOTS[course_id]}/",
        course_id=course_id,
        fixture_file=f"{course_id}/index.html",
    )


@pytest.mark.parametrize("course_id", ROOTS)
def test_index_navigation_order_titles_original_urls(course_id):
    course = index_fixture(course_id)
    assert [section.key for section in course.sections] == EXPECTED_KEYS[course_id]
    assert [section.title for section in course.sections] == EXPECTED_TITLES[course_id]
    assert [section.order for section in course.sections] == list(
        range(len(course.sections))
    )
    assert all(section.status == "referenced" for section in course.sections)
    assert all(
        str(section.original_url)
        == f"https://cs50.harvard.edu/{ROOTS[course_id]}/weeks/{section.key}/"
        for section in course.sections
    )
    assert not course.resources  # Welcome videos are not main lectures.
    assert all(
        "nav:nth-of-type" in section.provenance[0].locator
        for section in course.sections
    )


@pytest.mark.parametrize("course_id", ROOTS)
def test_combined_status_and_lecture_assignment(courses, course_id):
    course = courses[course_id]
    assert [s.key for s in course.sections if s.status == "parsed"] == PARSED_KEYS[
        course_id
    ]
    assert [s.key for s in course.sections] == EXPECTED_KEYS[course_id]
    lectures = [r for r in course.resources if r.role == "lecture_video"]
    assert [r.section_keys[0] for r in lectures] == PARSED_KEYS[course_id]
    assert all(r.status == "parsed" for r in lectures)
    assert all(
        r.status == "referenced" for r in course.resources if r.role != "lecture_video"
    )
    assert all(
        len(r.section_keys) == 1 and r.section_keys[0] in PARSED_KEYS[course_id]
        for r in course.resources
    )
    assert CourseDiscovery.model_validate_json(course.model_dump_json()) == course
    assert all(
        p.fixture_file and p.locator for r in course.resources for p in r.provenance
    )


@pytest.mark.parametrize(
    "course_id,key,count",
    [
        ("cs50x", "0", 30),
        ("cs50x", "1", 30),
        ("cs50_python", "0", 7),
        ("cs50_python", "5", 7),
        ("cs50_sql", "0", 10),
        ("cs50_sql", "6", 10),
        ("cs50_ai", "1", 6),
    ],
)
def test_primary_variants_each_fixture(courses, course_id, key, count):
    lecture = next(
        r
        for r in courses[course_id].resources
        if r.role == "lecture_video" and r.section_keys == (key,)
    )
    assert len(lecture.variants) == count
    assert {v.format for v in lecture.variants} == {"mp4", "cs50_player", "youtube"}
    assert all(v.media_type == "video" for v in lecture.variants)
    assert all(
        "Lecture" in p.context_path for v in lecture.variants for p in v.provenance
    )
    assert all("_files/" not in str(v.original_url) for v in lecture.variants)
    assert {v.resolution for v in lecture.variants if v.format == "mp4"} == {
        "360p",
        "720p",
        "1080p",
        "4k",
    }


@pytest.mark.parametrize(
    "course_id,key",
    [
        ("cs50x", "1"),
        ("cs50_python", "0"),
        ("cs50_python", "5"),
        ("cs50_sql", "0"),
        ("cs50_sql", "6"),
    ],
)
def test_slides_pdf_is_distinct_from_source_code_pdf(courses, course_id, key):
    resources = [
        r
        for r in courses[course_id].resources
        if r.section_keys == (key,) and r.format == "pdf"
    ]
    assert {r.role for r in resources} == {"slides", "source_code"}
    for resource in resources:
        branch = "Slides" if resource.role == "slides" else "Source Code"
        assert resource.provenance[0].context_path == ("Lecture", branch, "PDF")
        assert ("/src" in str(resource.original_url)) == (
            resource.role == "source_code"
        )


def test_languages_hdr_sdr_and_resolution_are_not_collapsed(courses):
    for lecture in [r for r in courses["cs50x"].resources if r.role == "lecture_video"]:
        assert Counter(v.language for v in lecture.variants) == {
            "en": 10,
            "pt": 10,
            "es": 10,
        }
        for language in ("en", "pt", "es"):
            direct = [
                v
                for v in lecture.variants
                if v.language == language and v.format == "mp4"
            ]
            assert {(v.dynamic_range, v.resolution) for v in direct} == {
                (dynamic_range, resolution)
                for dynamic_range in ("hdr", "sdr")
                for resolution in ("360p", "720p", "1080p", "4k")
            }
    for role in ("subtitles", "transcript"):
        assert Counter(
            r.language for r in courses["cs50x"].resources if r.role == role
        ) == {"en": 2, "pt": 2, "es": 2}
    for course_id in ("cs50_python", "cs50_sql", "cs50_ai"):
        assert all(
            r.language == "en"
            for r in courses[course_id].resources
            if r.role in ("subtitles", "transcript")
        )


def test_audio_demo_and_player_screen_parameter(courses):
    cs50x = courses["cs50x"]
    demo = next(r for r in cs50x.resources if r.role == "demo")
    assert demo.variants[0].media_id == "zkPUmtxeji8"
    assert all(
        v.media_id != "zkPUmtxeji8"
        for r in cs50x.resources
        if r.role == "lecture_video"
        for v in r.variants
    )
    for course in courses.values():
        assert all(
            r.variants[0].media_type == "audio"
            for r in course.resources
            if r.role == "audio"
        )
    sql_player = next(
        v
        for r in courses["cs50_sql"].resources
        if r.role == "lecture_video"
        for v in r.variants
        if v.format == "cs50_player"
    )
    assert (
        str(sql_player.original_url)
        == "https://video.cs50.io/vHYeChEf2lA?screen=6UZILCexEZ4"
    )
    assert sql_player.media_id == "vHYeChEf2lA"
    ai_video = next(
        r for r in courses["cs50_ai"].resources if r.role == "lecture_video"
    )
    assert all(
        str(v.original_url).endswith(".mp4.download")
        for v in ai_video.variants
        if v.format == "mp4"
    )
    assert all(
        v.dynamic_range is None for v in ai_video.variants
    )  # No HDR/SDR assertion in this snapshot.


def test_short_lists_and_deferred_details(courses, monkeypatch):
    assert len([r for r in courses["cs50_python"].resources if r.role == "short"]) == 6
    assert len([r for r in courses["cs50x"].resources if r.role == "section"]) == 1
    assert {r.role for r in courses["cs50_ai"].resources} >= {"quiz", "project"}
    seen = []
    original = prepare_cs50._parse_fixture

    def tracked(page, *args):
        seen.append(page.role)
        return original(page, *args)

    monkeypatch.setattr(prepare_cs50, "_parse_fixture", tracked)
    discover_fixture_courses(FIXTURES / "manifest.json")
    assert Counter(seen) == {"course_index": 6, "week_overview": 50}


def test_report_warnings_and_deterministic_results(courses):
    missing = {"cs50x": 10, "cs50_python": 8, "cs50_sql": 5, "cs50_ai": 6}
    for course_id, course in courses.items():
        assert Counter(w.code for w in course.warnings) == {
            "missing_week_fixture": missing[course_id],
            "local_embed_ignored": len(PARSED_KEYS[course_id]),
        }
        assert [
            w.section_key for w in course.warnings if w.code == "missing_week_fixture"
        ] == [s.key for s in course.sections if s.status == "referenced"]
    assert [c.model_dump_json() for c in courses.values()] == [
        c.model_dump_json()
        for c in discover_fixture_courses(FIXTURES / "regression_manifest.json")
        if c.course_id in ROOTS
    ]
    python = courses["cs50_python"]
    assert python.sections[0].title == "Functions, Variables"
    assert python.sections[0].provenance[1].context_path == ("Week 0 Functions",)


def synthetic_index(keys=("0", "1", "ai")):
    links = "".join(f'<li><a href="weeks/{key}/">Topic {key}</a></li>' for key in keys)
    return parse_course_index(
        f"<title>Test</title><nav><ol>{links}</ol></nav><main><h1>Welcome</h1></main>",
        "https://cs50.harvard.edu/x/",
        course_id="cs50x",
    )


def synthetic_week(key="0", extra="", iframe="", video=""):
    return f"""<nav><a href="https://example.com/nav.pdf">Ignore</a></nav>
    <main><h1>Week {key} Topic</h1>{iframe}
    <details><ol><li><a href="https://example.com/instructions.zip">Ignore</a></li></ol></details>
    <ul><li><span class="fa-li"><i>icon</i></span><span>Lecture</span><ol>
    <li>Notes <a href="../../notes/{key}/">Notes</a></li>
    <li>Slides<ul><li><a href="https://example.com/shared.pdf">PDF</a></li></ul></li>
    <li>Source Code<ol><li><a href="https://example.com/code.pdf">PDF</a></li></ol></li>
    <li>Video<ol><li><a href="https://video.cs50.io/AAA111aaa11?screen=BBB222bbb22">CS50 Video Player</a></li>{video}</ol></li>
    {extra}</ol></li></ul></main>"""


def parse_synthetic(key="0", **kwargs):
    return parse_week_page(
        synthetic_week(key, **kwargs),
        f"https://cs50.harvard.edu/x/weeks/{key}/",
        course_id="cs50x",
    )


def test_relative_urls_mixed_lists_and_excluded_instructions():
    course = parse_synthetic()
    assert (
        str(next(r for r in course.resources if r.role == "notes").original_url)
        == "https://cs50.harvard.edu/x/notes/0/"
    )
    assert {r.role for r in course.resources} == {
        "lecture_video",
        "notes",
        "slides",
        "source_code",
    }
    assert not course.warnings


def test_duplicate_navigation_and_main_links_do_not_add_sections():
    html = '<nav><ul><li><a href="weeks/ai/">AI</a></li><li><a href="weeks/0/">Zero</a></li><li><a href="weeks/ai/">Again</a></li><li><a href="https://cs50.harvard.edu/sql/weeks/0/">Other course</a></li></ul></nav><main><a href="weeks/9/">Not navigation</a></main>'
    course = parse_course_index(html, "https://cs50.harvard.edu/x/", course_id="cs50x")
    assert [s.key for s in course.sections] == ["ai", "0"]
    assert [s.title for s in course.sections] == ["AI", "Zero"]
    assert len(course.sections[0].provenance) == 2


def test_merge_shared_resources_and_input_order():
    index = synthetic_index()
    zero, one = parse_synthetic("0"), parse_synthetic("1")
    course = combine_course_pages(index, [one, zero, zero])
    assert course == combine_course_pages(index, [zero, one])
    shared = next(r for r in course.resources if r.role == "slides")
    assert shared.section_keys == ("0", "1")
    assert len(shared.provenance) == 2
    assert [s.status for s in course.sections] == ["parsed", "parsed", "referenced"]
    assert course.sections[2].key == "ai"


def test_merge_variants_and_weeks_preserves_evidence():
    first = parse_synthetic().resources[0]
    second = ResourceCandidate.model_validate(
        {
            **first.model_dump(),
            "section_keys": ("1",),
            "variants": (
                *first.variants,
                MediaVariant(
                    original_url="https://example.com/720p.mp4",
                    media_type="video",
                    resolution="720p",
                ),
            ),
        }
    )
    merged = merge_resource_candidates([first, second, first])
    assert len(merged) == 1
    assert merged[0].section_keys == ("0", "1")
    assert len(merged[0].variants) == 2
    assert merged[0].resource_id == first.resource_id


def test_duplicate_video_links_merge_provenance():
    html = '<li><a href="https://youtu.be/AAA111aaa11">YouTube</a></li>'
    course = parse_synthetic(video=html * 2)
    variants = course.resources[0].variants
    assert len(variants) == 2  # Player and YouTube remain separate offers.
    assert len(variants[1].provenance) == 2
    assert variants[0].media_id == variants[1].media_id == "AAA111aaa11"


def test_live_data_src_and_demo_embed_remain_separate():
    course = parse_synthetic(
        iframe='<iframe data-video data-src="https://www.youtube.com/embed/AAA111aaa11" src="./saved_resource.html"></iframe>',
        extra='<li>Demos<ul><li>Example<iframe data-video src="https://www.youtube.com/embed/CCC333ccc33"></iframe></li></ul></li>',
    )
    primary = next(r for r in course.resources if r.role == "lecture_video")
    demo = next(r for r in course.resources if r.role == "demo")
    assert {v.media_id for v in primary.variants} == {"AAA111aaa11"}
    assert demo.variants[0].media_id == "CCC333ccc33"
    assert not course.warnings


@pytest.mark.parametrize(
    "raw", ["./Lecture_files/CCC333ccc33(1).html", "./saved_resource.html"]
)
def test_local_embed_filename_never_becomes_media_id(raw):
    course = parse_synthetic(iframe=f'<iframe data-video src="{raw}"></iframe>')
    assert [w.code for w in course.warnings] == ["local_embed_ignored"]
    assert len(course.resources[0].variants) == 1
    assert course.resources[0].variants[0].media_id == "AAA111aaa11"


def test_unknown_and_invalid_links_are_diagnosed_fragments_ignored():
    course = parse_synthetic(
        extra='<li>Books<a href="https://example.com/book.pdf">Book</a><a href="javascript:alert(1)">Bad</a><a href="#same-page">Permalink</a></li>'
    )
    assert {w.code for w in course.warnings} == {
        "unknown_resource_role",
        "invalid_link",
    }
    assert (
        str(next(r for r in course.resources if r.role == "other").original_url)
        == "https://example.com/book.pdf"
    )
    assert not any("same-page" in str(r.original_url) for r in course.resources)


@pytest.mark.parametrize(
    "html,url,message",
    [
        ("<nav></nav>", "https://cs50.harvard.edu/x/", "missing main"),
        ("<main></main>", "https://cs50.harvard.edu/x/", "navigation has no"),
        (
            "<main></main>",
            "https://cs50.harvard.edu/x/weeks/0/",
            "missing week heading",
        ),
        (
            "<main><h1>Week 1 Topic</h1></main>",
            "https://cs50.harvard.edu/x/weeks/0/",
            "heading week 1 contradicts",
        ),
        (
            "<main><h1></h1></main>",
            "https://cs50.harvard.edu/x/weeks/0/",
            "empty week heading",
        ),
        ("<main></main>", "https://cs50.harvard.edu/sql/weeks/0/", "invalid week URL"),
    ],
)
def test_structural_and_course_errors(html, url, message):
    parser = (
        parse_course_index if url == "https://cs50.harvard.edu/x/" else parse_week_page
    )
    with pytest.raises(CS50ParseError, match=message):
        parser(html, url, course_id="cs50x")


def test_ambiguous_lecture_branches_fail():
    html = synthetic_week().replace(
        "</ul></main>", "<li>Lecture<ul><li>Notes</li></ul></li></ul></main>"
    )
    with pytest.raises(CS50ParseError, match="multiple Lecture branches"):
        parse_week_page(html, "https://cs50.harvard.edu/x/weeks/0/", course_id="cs50x")


def test_missing_lecture_is_reported_not_invented():
    course = parse_week_page(
        "<main><h1>Week ai AI</h1></main>",
        "https://cs50.harvard.edu/x/weeks/ai/",
        course_id="cs50x",
    )
    assert course.sections[0].key == "ai"
    assert not course.resources
    assert [w.code for w in course.warnings] == ["missing_lecture"]


def test_merge_rejects_foreign_or_unlisted_week():
    with pytest.raises(CS50ParseError, match="not present in course navigation"):
        combine_course_pages(synthetic_index(("ai",)), [parse_synthetic()])
    other = parse_week_page(
        "<main><h1>Week 0 Querying</h1></main>",
        "https://cs50.harvard.edu/sql/weeks/0/",
        course_id="cs50_sql",
    )
    with pytest.raises(CS50ParseError, match="contradicts index course"):
        combine_course_pages(synthetic_index(), [other])


def test_conflicting_variant_metadata_is_not_silently_discarded():
    first = parse_synthetic().resources[0]
    second = ResourceCandidate.model_validate(
        {
            **first.model_dump(),
            "variants": [{**first.variants[0].model_dump(), "media_id": "CCC333ccc33"}],
        }
    )
    with pytest.raises(CS50ParseError, match="conflicting variant media_id"):
        merge_resource_candidates([first, second])


def test_incremental_merge_removes_outdated_missing_week_warning():
    index = synthetic_index()
    first = combine_course_pages(index, [parse_synthetic("0")])
    assert {w.section_key for w in first.warnings} == {"1", "ai"}
    combined = combine_course_pages(first, [parse_synthetic("1")])
    assert {w.section_key for w in combined.warnings} == {"ai"}
    assert combined == combine_course_pages(
        index, [parse_synthetic("0"), parse_synthetic("1")]
    )
