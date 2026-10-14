"""Deterministic metadata adapter. Never dispatch these tasks to the legacy runner.

Lecture contracts retain their existing Settings dependency. No processing,
Whisper, downloader or LLM modules are imported here.
"""

from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from src.model_discovery.cs50 import (
    CourseDiscovery,
    CourseId,
    DiscoveryModel,
    NonEmpty,
    Provenance,
    ResourceCandidate,
    ResourceRole,
    deterministic_id,
)
from src.model_discovery.cs50_selection import CoursePreview, SelectionDecision
from src.model_lecture.data_resources import (
    ActionStatus,
    LectureCourse,
    LectureDocument,
    LectureMaterial,
    LectureMedia,
    LectureOther,
    LectureResourceUnion,
    ResourceAction,
    ResourceKind,
    ResourceTask,
)
from src.tools_lecture.select_cs50 import preview_course

Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class CS50TranscriptBinding(DiscoveryModel):
    course_id: CourseId
    section_key: NonEmpty
    lecture_id: NonEmpty
    resource_id: NonEmpty
    source_id: NonEmpty
    transcript_url: NonEmpty
    language: NonEmpty
    role: Literal["subtitles"] = "subtitles"
    format: Literal["srt"] = "srt"
    transcript_source: Literal["official_subtitle"] = "official_subtitle"
    media_id: str | None = None
    provenance: tuple[Provenance, ...]
    raw_srt_path: Path
    transcript_json_path: Path
    document: LectureDocument

    @model_validator(mode="after")
    def validate_identity(self) -> Self:
        if self.source_id != self.resource_id or self.lecture_id == self.resource_id:
            raise ValueError("source_id must alias the SRT resource_id, not lecture_id")
        if not self.provenance or self.raw_srt_path == self.transcript_json_path:
            raise ValueError("Provenance and two distinct artifact paths are required")
        if (
            self.document.source_url != self.transcript_url
            or self.document.local_path != self.raw_srt_path
            or self.document.file_type != "srt"
            or self.document.lecture_blocks != [self.section_key]
            or self.document.downloaded
        ):
            raise ValueError("SRT document contradicts its source/path/section binding")
        return self


class CS50ArtifactState(DiscoveryModel):
    """Explicit verified observations supplied by a future caller, never a file scan.

    Hashes assert validated, available artifacts; this planner cannot verify their
    contents. Unvalidated existing normalized output is a conflict, not overwrite
    permission. No actual artifacts are represented in the generated initial plan.
    """

    artifact_version: Literal[1] = 1
    source_id: NonEmpty
    transcript_url: NonEmpty
    language: NonEmpty
    raw_srt_path: Path
    transcript_json_path: Path
    raw_sha256: Sha256 | None = None
    transcript_sha256: Sha256 | None = None
    transcript_input_sha256: Sha256 | None = None
    transcript_validated: bool = False

    @model_validator(mode="after")
    def validate_receipt(self) -> Self:
        if self.transcript_validated:
            if (
                not self.transcript_sha256
                or not self.raw_sha256
                or self.transcript_input_sha256 != self.raw_sha256
            ):
                raise ValueError(
                    "Validated transcript needs output hash and matching SRT input hash"
                )
        elif self.transcript_sha256 or self.transcript_input_sha256:
            raise ValueError(
                "Existing unvalidated transcript is a conflict; do not overwrite"
            )
        return self


class CS50TaskBinding(DiscoveryModel):
    task_id: NonEmpty
    course_id: CourseId
    lecture_id: NonEmpty
    resource_id: NonEmpty
    source_id: NonEmpty
    depends_on: tuple[NonEmpty, ...] = ()
    output_path: Path
    reason: NonEmpty
    task: ResourceTask


def _ordered_resources(discovery: CourseDiscovery) -> tuple[ResourceCandidate, ...]:
    order = {section.key: section.order for section in discovery.sections}
    return tuple(
        sorted(
            discovery.resources,
            key=lambda r: (
                min((order[key] for key in r.section_keys), default=10**9),
                r.role.value,
                r.resource_id,
            ),
        )
    )


def _unique_media_id(
    resource: ResourceCandidate, language: str | None = None
) -> str | None:
    ids = {
        v.media_id
        for v in resource.variants
        if v.media_id and (language is None or v.language in (None, language))
    }
    return next(iter(ids)) if len(ids) == 1 else None


def _lecture_resource(resource: ResourceCandidate) -> LectureResourceUnion:
    common = dict(
        title=resource.title,
        source_url=str(resource.original_url),
        lecture_no=resource.section_keys[0]
        if len(resource.section_keys) == 1
        else None,
        lecture_blocks=list(resource.section_keys),
        file_type=resource.format,
        resource_kind=(
            ResourceKind.FOUNDATION
            if resource.role
            in {
                ResourceRole.LECTURE_VIDEO,
                ResourceRole.AUDIO,
                ResourceRole.SUBTITLES,
                ResourceRole.TRANSCRIPT,
                ResourceRole.NOTES,
                ResourceRole.SLIDES,
            }
            else ResourceKind.SUPPLEMENT
        ),
    )
    if resource.role in {ResourceRole.LECTURE_VIDEO, ResourceRole.AUDIO}:
        return LectureMedia(
            **common,
            media_type="video"
            if resource.role == ResourceRole.LECTURE_VIDEO
            else "audio",
            media_id=_unique_media_id(resource),
            # References only: no video quality/player URL is selected for download.
            media_url=None,
        )
    if resource.role in {
        ResourceRole.SUBTITLES,
        ResourceRole.TRANSCRIPT,
        ResourceRole.NOTES,
        ResourceRole.SLIDES,
    }:
        return LectureDocument(**common)
    if resource.role in {
        ResourceRole.SOURCE_CODE,
        ResourceRole.PROJECT,
        ResourceRole.PROBLEM_SET,
        ResourceRole.QUIZ,
        ResourceRole.PRACTICE,
        ResourceRole.STARTER_FILES,
        ResourceRole.REFERENCE,
    }:
        return LectureMaterial(**common)
    return LectureOther(**common)


def adapt_cs50_course(discovery: CourseDiscovery) -> LectureCourse:
    """Export one reference per candidate; preserve missing titles and all block keys."""
    discovery = CourseDiscovery.model_validate(discovery.model_dump())
    return LectureCourse(
        course_id=discovery.course_id,
        course_title=discovery.title or discovery.course_id,
        provider=discovery.provider,
        source_url=str(discovery.original_url),
        lecture_blocks=[
            s.key for s in sorted(discovery.sections, key=lambda s: (s.order, s.key))
        ],
        resources=[_lecture_resource(r) for r in _ordered_resources(discovery)],
    )


def _text_decisions(preview: CoursePreview) -> dict[str, SelectionDecision]:
    decisions = {}
    for lecture in preview.lectures:
        text = [d for d in lecture.decisions if d.purpose == "text"]
        if len(text) != 1 or lecture.resource_id in decisions:
            raise ValueError("Each logical lecture requires exactly one text decision")
        decisions[lecture.resource_id] = text[0]
    return decisions


def bind_cs50_selection(
    preview: CoursePreview,
    decisions: Mapping[str, SelectionDecision],
    *,
    artifact_root: Path = Path("data/lectures"),
) -> tuple[CS50TranscriptBinding, ...]:
    """Decision keys are logical lecture IDs, never filenames or media IDs."""
    preview = CoursePreview.model_validate(preview.model_dump())
    if preview.policy.text_strategy != "timed_knowledge":
        raise ValueError("CS50 transcript binding requires timed_knowledge selection")
    if ".." in artifact_root.parts:
        raise ValueError("artifact_root must not contain parent traversal")
    if preview_course(preview.discovery, preview.policy).lectures != preview.lectures:
        raise ValueError("Preview contradicts the checked discovery/selection")
    if set(decisions) != {lecture.resource_id for lecture in preview.lectures}:
        raise ValueError(
            "Decisions must cover exactly the preview's logical lecture IDs"
        )
    by_id = {r.resource_id: r for r in preview.discovery.resources}
    expected_decisions = _text_decisions(preview)
    bindings = []
    for lecture in preview.lectures:
        decision = decisions[lecture.resource_id]
        expected = expected_decisions[lecture.resource_id]
        if decision != expected:
            raise ValueError(
                f"Decision contradicts preview for lecture {lecture.resource_id}"
            )
        if decision.selected is None:
            raise ValueError(
                f"No SRT selected for {lecture.resource_id}: {decision.reason}"
            )
        if len(lecture.section_keys) != 1:
            raise ValueError(
                "SRT binding requires one explicit section per logical lecture"
            )
        key = lecture.section_keys[0]
        if key in (".", "..") or any(c in key for c in ("/", "\\", "\x00")):
            raise ValueError(f"Unsafe section path component: {key!r}")
        resource = by_id[decision.selected.resource_id]
        if resource.section_keys != lecture.section_keys:
            raise ValueError("SRT sections contradict the logical lecture assignment")
        target = (
            artifact_root
            / preview.discovery.provider
            / resource.course_id
            / "cs50-v1"
            / key
            / lecture.resource_id.removeprefix("resource:")
            / resource.resource_id.removeprefix("resource:")
        )
        document = _lecture_resource(resource)
        if not isinstance(document, LectureDocument):
            raise ValueError("Selected subtitle must export as LectureDocument")
        bindings.append(
            CS50TranscriptBinding(
                course_id=resource.course_id,
                section_key=key,
                lecture_id=lecture.resource_id,
                resource_id=resource.resource_id,
                source_id=resource.resource_id,
                transcript_url=str(resource.original_url),
                language=resource.language,
                media_id=_unique_media_id(
                    by_id[lecture.resource_id], resource.language
                ),
                provenance=resource.provenance,
                raw_srt_path=target / "source.srt",
                transcript_json_path=target / "transcript.json",
                document=document.model_copy(
                    update={"local_path": target / "source.srt"}
                ),
            )
        )
    return tuple(bindings)


def build_cs50_transcript_tasks(
    bindings: tuple[CS50TranscriptBinding, ...],
    artifact_state: Mapping[str, CS50ArtifactState],
) -> tuple[CS50TaskBinding, ...]:
    """Two tasks per source, including externally explained SKIPPED resume steps.

    ResourceTask has no dependency/output fields. CS50TaskBinding is required to
    interpret the plan safely; existing runners must not execute its naked tasks.
    """
    bindings = tuple(
        CS50TranscriptBinding.model_validate(b.model_dump()) for b in bindings
    )
    ids = [b.resource_id for b in bindings]
    paths = [p for b in bindings for p in (b.raw_srt_path, b.transcript_json_path)]
    lectures = [(b.course_id, b.lecture_id) for b in bindings]
    if len(set(ids)) != len(ids) or len(set(lectures)) != len(lectures):
        raise ValueError("Duplicate SRT resource or logical lecture binding")
    if len(set(paths)) != len(paths):
        raise ValueError("Colliding CS50 artifact target paths")
    if set(artifact_state) - set(ids):
        raise ValueError("Artifact state contains an unknown SRT resource_id")
    tasks = []
    for binding in bindings:
        state = artifact_state.get(binding.resource_id)
        if state is not None:
            state = CS50ArtifactState.model_validate(state.model_dump())
            for field in (
                "source_id",
                "transcript_url",
                "language",
                "raw_srt_path",
                "transcript_json_path",
            ):
                if getattr(state, field) != getattr(binding, field):
                    raise ValueError(
                        f"Artifact state contradicts {field} for {binding.resource_id}"
                    )
        download_id = deterministic_id(
            "cs50_task",
            "1",
            binding.course_id,
            binding.lecture_id,
            binding.resource_id,
            "download",
        )
        for action in (ResourceAction.DOWNLOAD, ResourceAction.PARSE_SUBTITLE):
            skip = bool(
                state
                and (
                    state.raw_sha256
                    if action == ResourceAction.DOWNLOAD
                    else state.transcript_validated
                )
            )
            tasks.append(
                CS50TaskBinding(
                    task_id=deterministic_id(
                        "cs50_task",
                        "1",
                        binding.course_id,
                        binding.lecture_id,
                        binding.resource_id,
                        action.value,
                    ),
                    course_id=binding.course_id,
                    lecture_id=binding.lecture_id,
                    resource_id=binding.resource_id,
                    source_id=binding.source_id,
                    depends_on=()
                    if action == ResourceAction.DOWNLOAD
                    else (download_id,),
                    output_path=(
                        binding.raw_srt_path
                        if action == ResourceAction.DOWNLOAD
                        else binding.transcript_json_path
                    ),
                    reason=(
                        "Externally verified artifact; skip this action."
                        if skip
                        else "Planned only; execution and validation require the future CS50 handler."
                    ),
                    task=ResourceTask(
                        resource=binding.document.model_copy(
                            deep=True,
                            update={
                                "downloaded": bool(state and state.raw_sha256),
                            },
                        ),
                        input_paths=[]
                        if action == ResourceAction.DOWNLOAD
                        else [binding.raw_srt_path],
                        actions=[action],
                        status=ActionStatus.SKIPPED if skip else ActionStatus.PENDING,
                    ),
                )
            )
    return tuple(tasks)


class CS50CoursePlan(DiscoveryModel):
    preview: CoursePreview  # Contains the entire original Discovery graph.
    lecture_course: LectureCourse
    # Index i maps directly to lecture_course.resources[i], which lacks an ID.
    lecture_resource_ids: tuple[NonEmpty, ...]
    artifact_root: Path = Path("data/lectures")
    bindings: tuple[CS50TranscriptBinding, ...]
    artifact_state: dict[str, CS50ArtifactState] = Field(default_factory=dict)
    tasks: tuple[CS50TaskBinding, ...]

    @model_validator(mode="after")
    def verify_contracts(self) -> Self:
        discovery = self.preview.discovery
        if self.lecture_course != adapt_cs50_course(discovery):
            raise ValueError("LectureCourse contradicts the original Discovery graph")
        if self.lecture_resource_ids != tuple(
            r.resource_id for r in _ordered_resources(discovery)
        ):
            raise ValueError("Lecture resource index binding contradicts Discovery")
        decisions = _text_decisions(self.preview)
        if self.bindings != bind_cs50_selection(
            self.preview, decisions, artifact_root=self.artifact_root
        ):
            raise ValueError(
                "Transcript bindings contradict checked selection/provenance/paths"
            )
        if self.tasks != build_cs50_transcript_tasks(
            self.bindings, self.artifact_state
        ):
            raise ValueError(
                "Task/dependency/output bindings contradict transcript plan"
            )
        return self


class CS50AdapterPlan(DiscoveryModel):
    schema_version: Literal[1] = 1
    adapter_version: Literal["cs50_selection_lecture_v1"] = "cs50_selection_lecture_v1"
    planned_only: Literal[True] = True
    execution_supported: Literal[False] = False
    courses: tuple[CS50CoursePlan, ...]

    @model_validator(mode="after")
    def unique_courses_and_tasks(self) -> Self:
        ids = [c.lecture_course.course_id for c in self.courses]
        tasks = [t for c in self.courses for t in c.tasks]
        if len(set(ids)) != len(ids) or len({t.task_id for t in tasks}) != len(tasks):
            raise ValueError("Duplicate course or task identity in CS50 plan")
        if len({t.output_path for t in tasks}) != len(tasks):
            raise ValueError("Colliding target paths across CS50 courses")
        return self


def build_cs50_course_plan(
    preview: CoursePreview,
    *,
    artifact_root: Path = Path("data/lectures"),
    artifact_state: Mapping[str, CS50ArtifactState] | None = None,
) -> CS50CoursePlan:
    decisions = _text_decisions(preview)
    bindings = bind_cs50_selection(preview, decisions, artifact_root=artifact_root)
    state = dict(artifact_state or {})
    return CS50CoursePlan(
        preview=preview,
        lecture_course=adapt_cs50_course(preview.discovery),
        lecture_resource_ids=tuple(
            r.resource_id for r in _ordered_resources(preview.discovery)
        ),
        artifact_root=artifact_root,
        bindings=bindings,
        artifact_state=state,
        tasks=build_cs50_transcript_tasks(bindings, state),
    )
