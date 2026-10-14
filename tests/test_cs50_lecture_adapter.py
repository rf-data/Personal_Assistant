"""Real Lecture contracts, controlled Settings, local fixtures and forbidden IO."""

import importlib
import json
import os
import runpy
import socket
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "docs/course_sources/cs50"


def offline_settings(root):
    return {
        "ROOT": str(root),
        "CHROMA_DIR": str(root / "chroma"),
        "DATA_DIR": str(root / "data"),
        "WIKI_EN_API": "https://example.invalid",
        "HEADER_AGENT": "offline-cs50-test",
        "HF_API_KEY": "offline-unused",
        "OPENAI_API_KEY": "offline-unused",
    }


@pytest.fixture(scope="module")
def context(tmp_path_factory):
    before = set(sys.modules)
    directory = tmp_path_factory.mktemp("cs50_contracts")

    def forbidden(*args, **kwargs):
        raise AssertionError("Adapter must remain offline")

    with pytest.MonkeyPatch.context() as patch:
        patch.chdir(directory)  # No .env files or real API keys are required.
        for key, value in offline_settings(directory).items():
            patch.setenv(key, value)
        patch.setattr(socket.socket, "connect", forbidden)
        patch.setattr(socket.socket, "connect_ex", forbidden)
        patch.setattr(socket, "create_connection", forbidden)
        patch.setattr(socket, "getaddrinfo", forbidden)
        adapter = importlib.import_module("src.tools_lecture.adapt_cs50")
        selection = importlib.import_module("src.tools_lecture.select_cs50")
        models = importlib.import_module("src.model_discovery.cs50_selection")
        parser = importlib.import_module("src.tools_lecture.prepare_cs50")
        courses = parser.discover_fixture_courses(FIXTURES / "manifest.json")
        previews = tuple(
            selection.preview_course(
                c, models.SelectionPolicy(text_strategy="timed_knowledge")
            )
            for c in courses
        )
        plan = adapter.CS50AdapterPlan(
            courses=tuple(adapter.build_cs50_course_plan(p) for p in previews)
        )
        yield adapter, previews, plan
    # Remove only contracts imported by this fixture; keep legacy pure-selection
    # tests independent of the pre-existing Settings coupling in Lecture models.
    for name in (
        "src.tools_lecture.adapt_cs50",
        "src.model_lecture.data_resources",
        "src.core.config",
    ):
        if name not in before:
            sys.modules.pop(name, None)


@pytest.mark.parametrize(
    "index,count", [(0, 12), (1, 10), (2, 7), (3, 7), (4, 9), (5, 5)]
)
def test_real_courses_bindings_and_resource_index(context, index, count):
    adapter, previews, plan = context
    entry = plan.courses[index]
    discovery = previews[index].discovery
    assert entry.lecture_course.course_id == discovery.course_id
    assert entry.preview.discovery == discovery
    assert len(entry.bindings) == count
    assert len(entry.lecture_course.resources) == len(discovery.resources)
    by_id = {r.resource_id: r for r in discovery.resources}
    for resource_id, exported in zip(
        entry.lecture_resource_ids, entry.lecture_course.resources, strict=True
    ):
        assert exported.source_url == str(by_id[resource_id].original_url)
        assert exported.lecture_blocks == list(by_id[resource_id].section_keys)
        assert exported.downloaded is False and exported.local_path is None
    for binding in entry.bindings:
        resource = by_id[binding.resource_id]
        assert binding.lecture_id != binding.resource_id == binding.source_id
        assert binding.course_id == discovery.course_id
        assert binding.language == resource.language == "en"
        assert binding.transcript_url == str(resource.original_url)
        assert binding.provenance == resource.provenance
        assert binding.section_key in entry.lecture_course.lecture_blocks
        assert isinstance(binding.document, adapter.LectureDocument)
        assert binding.document.resource_type == "document"
        assert binding.document.file_type == "srt"


def test_100_unique_tasks_with_explicit_dependencies_and_paths(context):
    adapter, _, plan = context
    tasks = [t for entry in plan.courses for t in entry.tasks]
    assert (
        len(tasks)
        == len({t.task_id for t in tasks})
        == len({t.output_path for t in tasks})
        == 100
    )
    assert sum(len(c.bindings) for c in plan.courses) == 50
    for entry in plan.courses:
        for binding, download, parse in zip(
            entry.bindings, entry.tasks[::2], entry.tasks[1::2], strict=True
        ):
            assert download.task.actions == [adapter.ResourceAction.DOWNLOAD]
            assert parse.task.actions == [adapter.ResourceAction.PARSE_SUBTITLE]
            assert download.depends_on == () and parse.depends_on == (download.task_id,)
            assert download.task.input_paths == []
            assert parse.task.input_paths == [binding.raw_srt_path]
            assert download.output_path == binding.raw_srt_path
            assert parse.output_path == binding.transcript_json_path
            assert (
                download.task.status
                == parse.task.status
                == adapter.ActionStatus.PENDING
            )
            assert isinstance(parse.task.resource, adapter.LectureDocument)
    assert plan.planned_only and not plan.execution_supported


def test_non_numeric_and_zero_keys_and_ambiguous_media_ids(context):
    adapter, _, plan = context
    ai = next(b for b in plan.courses[0].bindings if b.section_key == "ai")
    assert ai.document.lecture_no == "ai" and "ai" in ai.raw_srt_path.parts
    for entry in plan.courses:
        zero = next(b for b in entry.bindings if b.section_key == "0")
        assert zero.document.lecture_no == "0" and "0" in zero.raw_srt_path.parts
    cyber = plan.courses[5]
    binding = cyber.bindings[0]
    main = next(
        r
        for r in cyber.preview.discovery.resources
        if r.resource_id == binding.lecture_id
    )
    assert {v.media_id for v in main.variants if v.media_id} == {
        "kUovJpWqEMk",
        "fJYdAN4Vh5c",
    }
    assert binding.media_id is None
    exported = cyber.lecture_course.resources[
        cyber.lecture_resource_ids.index(binding.lecture_id)
    ]
    assert isinstance(exported, adapter.LectureMedia)
    assert exported.media_id is None and exported.media_url is None
    assert any(
        w.code == "multiple_lecture_media_ids" for w in cyber.preview.discovery.warnings
    )


def test_all_contracts_and_saved_plan_roundtrip(context, tmp_path):
    adapter, _, plan = context
    output = tmp_path / "plan.json"
    output.write_text(plan.model_dump_json(indent=2))
    assert adapter.CS50AdapterPlan.model_validate_json(output.read_text()) == plan
    assert (
        adapter.CS50AdapterPlan.model_validate_json(
            (FIXTURES / "cs50_lecture_plan.v1.json").read_text()
        )
        == plan
    )
    for entry in plan.courses:
        assert (
            adapter.LectureCourse.model_validate_json(
                entry.lecture_course.model_dump_json()
            )
            == entry.lecture_course
        )
        for task in entry.tasks:
            assert (
                adapter.ResourceTask.model_validate_json(task.task.model_dump_json())
                == task.task
            )
        for binding in entry.bindings:
            assert (
                adapter.CS50TranscriptBinding.model_validate_json(
                    binding.model_dump_json()
                )
                == binding
            )


def test_deterministic_reordering_and_no_mutation_or_io(context, monkeypatch):
    adapter, previews, _ = context
    selection = importlib.import_module("src.tools_lecture.select_cs50")
    before = [p.model_dump_json() for p in previews]

    def forbidden(*args, **kwargs):
        raise AssertionError(
            "Planning must not read/write files or initialize providers"
        )

    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr("builtins.open", forbidden)
    for preview in previews:
        discovery = preview.discovery.model_copy(
            update={
                "resources": tuple(
                    r.model_copy(update={"variants": tuple(reversed(r.variants))})
                    for r in reversed(preview.discovery.resources)
                )
            }
        )
        reordered = selection.preview_course(discovery, preview.policy)
        original_plan = adapter.build_cs50_course_plan(preview)
        reordered_plan = adapter.build_cs50_course_plan(reordered)
        assert original_plan.lecture_course == reordered_plan.lecture_course
        assert original_plan.bindings == reordered_plan.bindings
        assert original_plan.tasks == reordered_plan.tasks
    assert [p.model_dump_json() for p in previews] == before
    assert (
        not {"marvin", "faster_whisper", "yt_dlp", "src.tools_lecture.process_lecture"}
        & sys.modules.keys()
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("resource_id", "unverified"),
        ("language", "de"),
        ("original_url", "https://example.invalid/other.srt"),
    ],
)
def test_contradictory_decision_rejected(context, field, value):
    adapter, previews, _ = context
    preview = previews[1]
    decisions = {
        lecture.resource_id: lecture.decisions[0] for lecture in preview.lectures
    }
    key = preview.lectures[0].resource_id
    chosen = decisions[key]
    decisions[key] = chosen.model_copy(
        update={"selected": chosen.selected.model_copy(update={field: value})}
    )
    with pytest.raises(ValueError, match="contradicts preview"):
        adapter.bind_cs50_selection(preview, decisions)


def test_wrong_mode_missing_decisions_and_unselected_source(context):
    adapter, previews, _ = context
    preview = previews[1]
    with pytest.raises(ValueError, match="exactly"):
        adapter.bind_cs50_selection(preview, {})
    selection = importlib.import_module("src.tools_lecture.select_cs50")
    with pytest.raises(ValueError, match="timed_knowledge"):
        adapter.bind_cs50_selection(selection.preview_course(preview.discovery), {})
    discovery = preview.discovery.model_copy(
        update={
            "resources": tuple(
                r for r in preview.discovery.resources if r.format != "srt"
            )
        }
    )
    missing = selection.preview_course(discovery, preview.policy)
    with pytest.raises(ValueError, match="No SRT selected"):
        adapter.build_cs50_course_plan(missing)


def receipt(adapter, binding, **extra):
    data = {
        field: getattr(binding, field)
        for field in (
            "source_id",
            "transcript_url",
            "language",
            "raw_srt_path",
            "transcript_json_path",
        )
    }
    return adapter.CS50ArtifactState(**(data | extra))


def test_verified_artifact_state_skips_only_matching_actions(context):
    adapter, previews, plan = context
    binding = plan.courses[1].bindings[0]
    state = receipt(adapter, binding, raw_sha256="a" * 64)
    tasks = adapter.build_cs50_transcript_tasks(
        (binding,), {binding.resource_id: state}
    )
    assert tasks[0].task.status == adapter.ActionStatus.SKIPPED
    assert tasks[1].task.status == adapter.ActionStatus.PENDING
    complete = receipt(
        adapter,
        binding,
        raw_sha256="a" * 64,
        transcript_sha256="b" * 64,
        transcript_input_sha256="a" * 64,
        transcript_validated=True,
    )
    assert (
        adapter.CS50ArtifactState.model_validate_json(complete.model_dump_json())
        == complete
    )
    tasks = adapter.build_cs50_transcript_tasks(
        (binding,), {binding.resource_id: complete}
    )
    assert all(t.task.status == adapter.ActionStatus.SKIPPED for t in tasks)
    assert tasks[1].depends_on == (tasks[0].task_id,)
    resumed = adapter.build_cs50_course_plan(
        previews[1], artifact_state={binding.resource_id: complete}
    )
    assert (
        adapter.CS50CoursePlan.model_validate_json(resumed.model_dump_json()) == resumed
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_id", "unsupported"),
        ("language", "de"),
        ("transcript_url", "https://example.invalid/other.srt"),
        ("raw_srt_path", Path("wrong.srt")),
        ("transcript_json_path", Path("wrong.json")),
    ],
)
def test_stale_receipts_rejected(context, field, value):
    adapter, _, plan = context
    binding = plan.courses[0].bindings[0]
    state = receipt(adapter, binding, **{field: value})
    with pytest.raises(ValueError, match=field):
        adapter.build_cs50_transcript_tasks((binding,), {binding.resource_id: state})


def test_missing_hash_unvalidated_output_and_unknown_state_rejected(context):
    adapter, _, plan = context
    binding = plan.courses[0].bindings[0]
    with pytest.raises(ValidationError, match="matching SRT input hash"):
        receipt(adapter, binding, transcript_validated=True, transcript_sha256="b" * 64)
    with pytest.raises(ValidationError, match="do not overwrite"):
        receipt(adapter, binding, transcript_sha256="b" * 64)
    with pytest.raises(ValueError, match="unknown"):
        adapter.build_cs50_transcript_tasks(
            (binding,), {"unknown": receipt(adapter, binding)}
        )


def test_duplicate_bindings_and_paths_are_rejected(context):
    adapter, _, plan = context
    first, second = plan.courses[0].bindings[:2]
    with pytest.raises(ValueError, match="Duplicate"):
        adapter.build_cs50_transcript_tasks((first, first), {})
    collision = second.model_copy(
        update={
            "raw_srt_path": first.raw_srt_path,
            "document": second.document.model_copy(
                update={"local_path": first.raw_srt_path}
            ),
        }
    )
    with pytest.raises(ValueError, match="Colliding"):
        adapter.build_cs50_transcript_tasks((first, collision), {})


@pytest.mark.parametrize(
    "kind",
    [
        "provenance",
        "dependency",
        "version",
        "duplicate_course",
        "missing_text_decision",
    ],
)
def test_json_contract_rejects_tampering(context, kind):
    adapter, _, plan = context
    data = plan.model_dump(mode="json")
    if kind == "provenance":
        data["courses"][0]["bindings"][0]["provenance"][0]["original_url"] = (
            "https://example.invalid/"
        )
    elif kind == "dependency":
        data["courses"][0]["tasks"][1]["depends_on"] = ["unknown_task"]
    elif kind == "version":
        data["schema_version"] = 2
    elif kind == "duplicate_course":
        data["courses"].append(data["courses"][0])
    else:
        data["courses"][0]["preview"]["lectures"][0]["decisions"] = []
    with pytest.raises(ValidationError):
        adapter.CS50AdapterPlan.model_validate_json(json.dumps(data))


def test_artifact_root_parent_traversal_rejected(context):
    adapter, previews, _ = context
    with pytest.raises(ValueError, match="parent traversal"):
        adapter.build_cs50_course_plan(
            previews[0], artifact_root=Path("data/../lectures")
        )


def test_report_cli_exclusive_output_and_no_artifact_directories(
    context, tmp_path, monkeypatch
):
    _, _, plan = context
    report = tmp_path / "report.json"
    artifact_root = tmp_path / "future-artifacts"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "report_cs50_lecture_plan.py",
            "--output",
            str(report),
            "--artifact-root",
            str(artifact_root),
        ],
    )
    runpy.run_path(
        str(ROOT / "scripts/report_cs50_lecture_plan.py"), run_name="__main__"
    )
    data = json.loads(report.read_text())
    assert len(data["courses"]) == len(plan.courses)
    assert not artifact_root.exists()
    before = report.read_bytes()
    with pytest.raises(FileExistsError):
        runpy.run_path(
            str(ROOT / "scripts/report_cs50_lecture_plan.py"), run_name="__main__"
        )
    assert report.read_bytes() == before


def test_fresh_synchronous_real_import_without_execution(tmp_path):
    env = {
        key: value
        for key, value in os.environ.items()
        if key in ("PATH", "LANG", "TMPDIR")
    }
    env.update(offline_settings(tmp_path))
    script = """
import socket, sys
sys.path.insert(0, sys.argv[1])
def forbidden(*args, **kwargs):
    raise AssertionError('Network forbidden')
socket.socket.connect = forbidden
socket.socket.connect_ex = forbidden
socket.create_connection = forbidden
socket.getaddrinfo = forbidden
import src.tools_lecture.adapt_cs50
assert not {'marvin', 'faster_whisper', 'yt_dlp', 'src.tools_lecture.process_lecture'} & sys.modules.keys()
print('real synchronous import passed')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", script, str(ROOT)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert "real synchronous import passed" in result.stdout
