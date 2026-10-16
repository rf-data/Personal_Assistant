"""C20-B wire envelopes reuse the complete C18 report and C16 job contracts."""

from typing import Literal

from pydantic import Field, field_validator

from src.job_control.models import (
    Artifact,
    Contract,
    Identifier,
    Job,
    Sha,
    StartRequest,
)
from src.workflows.models import Workflow


class WorkflowInspectRequest(Contract):
    schema_version: Literal[1] = 1
    source_ref: Identifier
    workflow_id: Identifier


class WorkflowExecuteRequest(WorkflowInspectRequest):
    preview_id: Sha
    current_run_id: Identifier | None
    confirmed: Literal[True]

    @field_validator("confirmed", mode="before")
    @classmethod
    def explicit_confirmation(cls, value):
        return StartRequest.explicit_confirmation(value)


class WorkflowResumeRequest(WorkflowExecuteRequest):
    current_run_id: Identifier


class WorkflowInspection(Contract):
    schema_version: Literal[1] = 1
    protocol: Literal["personal_assistant_workflows_v1"] = (
        "personal_assistant_workflows_v1"
    )
    preview_id: Sha
    workflow: Workflow
    persisted_report: Workflow | None
    current_job: Job | None
    previous_run_id: Identifier | None
    report_artifact: Artifact | None
    history: tuple[Job, ...] = Field(max_length=100)
    history_total: int = Field(ge=0)
    history_offset: int = Field(ge=0, le=1000)
    history_limit: int = Field(ge=1, le=100)


class WorkflowSubmission(Contract):
    schema_version: Literal[1] = 1
    protocol: Literal["personal_assistant_workflows_v1"] = (
        "personal_assistant_workflows_v1"
    )
    workflow_id: Identifier
    run_id: Identifier
    job: Job


class WorkflowRunReport(Contract):
    schema_version: Literal[1] = 1
    protocol: Literal["personal_assistant_workflows_v1"] = (
        "personal_assistant_workflows_v1"
    )
    workflow_id: Identifier
    run_id: Identifier
    job: Job
    report: Workflow | None
    report_artifact: Artifact | None


class WorkflowCapabilities(Contract):
    schema_version: Literal[1] = 1
    protocol: Literal["personal_assistant_workflows_v1"] = (
        "personal_assistant_workflows_v1"
    )
    enabled: bool
    execution_enabled: bool
    worker_available: bool
    max_response_bytes: Literal[524288] = 524288
    history_max_limit: Literal[100] = 100
    inspect_route: Literal["/v1/workflows/inspect"] = "/v1/workflows/inspect"
    execute_route: Literal["/v1/workflows/execute"] = "/v1/workflows/execute"
    resume_route: Literal["/v1/workflows/resume"] = "/v1/workflows/resume"
    status_route: Literal["/v1/workflows/{workflow_id}"] = "/v1/workflows/{workflow_id}"
    run_route: Literal["/v1/workflows/{workflow_id}/runs/{run_id}"] = (
        "/v1/workflows/{workflow_id}/runs/{run_id}"
    )


class WorkflowRequestReceipt(Contract):
    """Immutable request binding, never a queue or an execution instruction."""

    schema_version: Literal[1] = 1
    owner: Identifier
    intent: Sha
    request: WorkflowExecuteRequest
    operation: Literal["execute", "resume"]
    existing_job_id: Identifier | None
    c16_intent: Sha | None


class WorkflowReuseAcceptance(Contract):
    """Proof that service.submit actually returned an existing job successfully."""

    schema_version: Literal[1] = 1
    intent: Sha
    job_id: Identifier
