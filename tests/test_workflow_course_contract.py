"""CS50 workflow v1/v2 stays separate from the broader Content/ACL scope."""

import json
from typing import get_args

import pytest
from pydantic import TypeAdapter, ValidationError

from src.job_control.models import Principal, WorkflowParams
from src.model_discovery.cs50 import CourseId
from src.workflows import http_models
from src.workflows.models import Definition, State, Workflow
from tests.parsing_config_support import ROOT

COURSES = get_args(CourseId)


def definition(course, version):
    data = dict(course_id=course, sources={"manifest": "manifest.json"})
    if version == 2:
        data.update(
            schema_version=2,
            assignment_snapshots=[
                dict(
                    file="cs50_python/task.html",
                    url="https://cs50.harvard.edu/python/psets/0/",
                    path="assignments/task.html",
                    sha256="a" * 64,
                )
            ],
        )
    return data


def report(course):
    return dict(
        workflow_id="synthetic",
        course_id=course,
        lecture_ids=[],
        created_at=None,
        status="pending",
        stages=[],
        dependencies={},
        input_refs=[],
        configuration_hash="a" * 64,
        initiated_by="synthetic",
        run_id="run_synthetic",
        report_sha256="b" * 64,
    )


@pytest.mark.parametrize("course", COURSES)
@pytest.mark.parametrize("version", [1, 2])
def test_historical_cs50_definition_report_state_roundtrips(course, version):
    value = Definition.model_validate(definition(course, version))
    assert Definition.model_validate_json(value.model_dump_json()) == value
    workflow = Workflow.model_validate(report(course))
    state = State(report=workflow, attempts=("run_synthetic",))
    assert State.model_validate_json(state.model_dump_json()) == state
    params = WorkflowParams(
        course_id=course, source_ref="synthetic", workflow_id="synthetic"
    )
    assert WorkflowParams.model_validate_json(params.model_dump_json()) == params
    assert workflow.schema_version == 1


@pytest.mark.parametrize("course", ["loviscach_mathe_1", "unknown_course"])
@pytest.mark.parametrize("version", [1, 2])
def test_non_discovery_course_rejected_at_definition_report_and_job(course, version):
    for model, data in (
        (Definition, definition(course, version)),
        (Workflow, report(course)),
        (
            WorkflowParams,
            dict(source_ref="synthetic", workflow_id="synthetic", course_id=course),
        ),
        (State, dict(report=report(course), attempts=["run_synthetic"])),
    ):
        with pytest.raises(ValidationError) as error:
            model.model_validate_json(json.dumps(data))
        assert any(
            e["loc"][-1] == "course_id" and e["type"] == "literal_error"
            for e in error.value.errors()
        )


def test_content_acl_still_accepts_loviscach_without_changing_workflow_scope():
    actor = Principal(
        subject="synthetic", role="viewer", courses=("loviscach_mathe_1",)
    )
    assert Principal.model_validate_json(actor.model_dump_json()) == actor


@pytest.mark.parametrize(
    "path", ["docs/job_control/contract.v1.json", "docs/workflows/contract.v1.json"]
)
def test_complete_published_workflow_schemas_remain_unchanged(path):
    snapshot = json.loads((ROOT / path).read_text())["workflow_http"]
    assert snapshot["protocol"] == "personal_assistant_workflows_v1"
    for name, expected in snapshot["models"].items():
        assert getattr(http_models, name).model_json_schema() == expected


@pytest.mark.parametrize(
    "path", ["example-report.v1.json", "example-pdf-report.v1.json"]
)
def test_published_stored_reports_roundtrip_without_field_loss(path):
    data = json.loads((ROOT / "docs/workflows" / path).read_text())
    reports = [data["preview"], data["report"]] if "preview" in data else [data]
    for payload in reports:
        value = Workflow.model_validate(payload)
        assert value.model_dump(mode="json", exclude_unset=True) == payload
        assert Workflow.model_validate_json(value.model_dump_json()) == value


def test_workflow_and_content_course_aliases_have_separate_acceptance():
    from src.job_control.models import Course

    assert (
        TypeAdapter(Course).validate_python("loviscach_mathe_1") == "loviscach_mathe_1"
    )
    assert Definition.model_json_schema()["properties"]["course_id"]["enum"] == list(
        COURSES
    )
    assert Workflow.model_json_schema()["properties"]["course_id"]["enum"] == list(
        COURSES
    )
