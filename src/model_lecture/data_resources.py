## data_resources.py
# import
from enum import Enum
from datetime import datetime
from pathlib import Path
from typing import Literal, Annotated
from pydantic import BaseModel, Field  # , property

from src.core.config import folder_env_vars


class LectureResourceType(Enum):
    MEDIA = "media"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    SCRIPT = "script"
    MATERIAL = "material"
    NOTEBOOK = "notebook"
    EXAM = "exam"
    OTHER = "other"


class ResourceAction(Enum):
    CHUNK = "chunk"
    DOWNLOAD = "download"
    EXTRACT_FRAMES = "extract_frames"
    EXTRACT_KNOWLEDGE = "extract_knowledge"
    EXTRACT_META = "extract_metadata"
    PARSE_DOCUMENT = "parse_document"
    PARSE_SUBTITLE = "parse_subtitle"
    TRANSCRIBE = "transcribe"


class ActionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


class ResourceKind(Enum):
    FOUNDATION = (
        "foundation",
        (
            "Primary course material that is part of the core learning path "
            "and is expected to contain knowledge required to understand "
            "the course or lecture."
        ),
        (
            "Use for resources that form the main instructional content, "
            "such as primary lecture videos, official lecture scripts, "
            "or other materials that are intended to teach the core subject matter."
        ),
    )

    SUPPLEMENT = (
        "supplement",
        (
            "Additional material that supports, illustrates, extends, "
            "or reinforces the primary course content."
        ),
        (
            "Use for optional or secondary resources such as supplementary "
            "videos, exercises, examples, references, or additional explanations. "
            "Do not use when the resource is required to follow the main course content."
        ),
    )

    def __init__(
        self,
        value: str,
        description: str,
        guidance: str,
    ):
        self._value_ = value
        self.description = description
        self.guidance = guidance

    @classmethod
    def prompt_description(cls) -> str:
        return "\n".join(
            f"""
- {item.value}:
  Description: {item.description}
  Guidance: {item.guidance}
"""
            for item in cls
        )


class LectureResource(BaseModel):
    # resource_id: str              # TODO: convert to new data models

    title: str | None = None
    source_url: str | None = None

    lecture_no: str | None = None
    topic: str | None = None

    resource_kind: ResourceKind = ResourceKind.FOUNDATION

    resource_type: LectureResourceType

    lecture_blocks: list[str] = Field(default_factory=list)

    # semester: str | None = None

    file_type: str | None = None
    local_path: Path | None = None

    downloaded: bool = False
    content_hash: str | None = None
    license: str | None = None


class KnowledgeSourceMetadata(BaseModel):
    source_id: str

    resource_kind: ResourceKind

    resource_type: str | None = None

    course_id: str | None = None
    lecture_no: str | None = None
    topic: str | None = None
    title: str | None = None

    source_url: str | None = None
    license: str | None = None


class LectureMedia(LectureResource):
    resource_type: Literal["media"] = "media"

    media_type: Literal["audio", "video"]
    #     LectureResourceType.VIDEO
    # ] = LectureResourceType.VIDEO

    media_url: str | None = None
    media_id: str | None = None
    duration: int | None = None


class LectureNotebook(LectureResource):
    resource_type: Literal["notebook"] = "notebook"
    #     LectureResourceType.NOTEBOOK
    # ] = LectureResourceType.NOTEBOOK


class LectureExam(LectureResource):
    resource_type: Literal["exam"] = "exam"
    #     LectureResourceType.EXAM
    # ] = LectureResourceType.EXAM


class LectureDocument(LectureResource):
    resource_type: Literal["document"] = "document"


class LectureScript(LectureResource):
    resource_type: Literal["script"] = "script"
    #     LectureResourceType.SCRIPT
    # ] = LectureResourceType.SCRIPT


class LectureMaterial(LectureResource):
    resource_type: Literal["material"] = "material"
    #     LectureResourceType.MATERIAL
    # ] = LectureResourceType.MATERIAL

    material_type: Literal["repository", "other"] = "other"


class LectureOther(LectureResource):
    resource_type: Literal["other"] = "other"


LectureResourceUnion = Annotated[
    LectureMedia
    # | "video"
    | LectureDocument
    | LectureScript
    # | "script"
    | LectureMaterial
    # | "material"
    | LectureExam
    # | "exam"
    | LectureNotebook
    # | "notebook"
    | LectureOther,
    # )
    Field(discriminator="resource_type"),
]


class ResourceTask(BaseModel):
    resource: LectureResourceUnion
    input_paths: list[Path] = Field(default_factory=list)

    actions: list[ResourceAction] = Field(default_factory=list)

    status: ActionStatus = ActionStatus.PENDING
    error: str | None = None


class RawLectureBlock(BaseModel):
    block_id: str
    title: str | None = None
    date_text: str | None = None

    resources: list[LectureResource] = Field(default_factory=list)


class LectureResource_old(BaseModel):
    videos: list[LectureMedia]
    scripts: list[LectureScript]
    material: dict = Field(default_factory=dict)  # [str, LectureMaterial]
    other_links: dict[str, dict] = Field(default_factory=dict)


class LectureSection(BaseModel):
    section_id: str
    title: str | None = None

    resources: list[LectureResource] = Field(default_factory=list)
    # videos: list[LectureVideo] = Field(
    #     default_factory=list
    # )
    # scripts: list[LectureScript] = Field(
    #     default_factory=list
    # )
    # materials: list[LectureMaterial] = Field(
    #     default_factory=list
    # )


class LectureCourse(BaseModel):
    course_id: str
    course_title: str
    provider: str
    source_url: str | None

    @property
    def root(self) -> Path:
        return (
            folder_env_vars.data_lectures
            / self.provider  # loviscach"
            / self.course_id  # "mathe_1"
        )

    lecture_blocks: list[str] = Field(default_factory=list)
    # sections: list[LectureSection] = Field(default_factory=list)
    resources: list[LectureResourceUnion] = Field(default_factory=list)

    unassigned_resources: list[LectureResourceUnion] = Field(default_factory=list)

    examen: list[LectureExam] = Field(default_factory=list)


class ParsedLectureFilename(BaseModel):
    stem: str

    title: str | None = None
    sequence_no: str | None = None
    qualifier: str | None = None

    extra_parts: list[str] | None = None


class DiscoveredCourseFile(BaseModel):
    path: Path
    parsed_name: ParsedLectureFilename | None = None

    course_id: str | None = None
    course_title: str | None = None

    resource_type: LectureResourceType | None = None
    resource_format: str | None = None


##################################
# KNOWLEDGE_SOURCES
##################################

# TODO:
# class LectureBook(BaseModel):
#     title: str | None = None
#     source_url: str
#     section: str | None = None

# TODO:
# class LectureChapter(BaseModel):
#     title: str | None = None
#     source_url: str
#     section: str | None = None


# class LectureScript(BaseModel):
#     title: str | None = None
#     source_url: str
#     section: str | None = None


# class LectureMaterial(BaseModel):
#     title: str | None = None
#     source_url: str
#     section: str | None = None
#     file_type: str | None = None


# class LectureSection(BaseModel):
#     title: str
#     script_url: str | None = None
#     videos: list[LectureVideo]


# class LectureCourse(BaseModel):
#     title: str
#     source_url: str
#     sections: list[LectureSection]
