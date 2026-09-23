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


class LectureResource(BaseModel):
    # resource_id: str              # TODO: convert to new data models

    title: str | None = None
    source_url: str | None = None

    lecture_no: str | None = None
    topic: str | None = None

    resource_kind: Literal[
        "foundation",
        "supplement",
    ] = "foundation"

    resource_type: LectureResourceType

    lecture_blocks: list[str] = Field(default_factory=list)

    # semester: str | None = None

    file_type: str | None = None
    local_path: Path | None = None

    downloaded: bool = False
    content_hash: str | None = None
    license: str | None = None


class LectureMedia(LectureResource):
    resource_type: Literal["media"] = "media"

    media_type: Literal["audio", "video"]
    #     LectureResourceType.VIDEO
    # ] = LectureResourceType.VIDEO

    youtube_url: str | None = None
    youtube_id: str | None = None
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

    sections: list[LectureSection] = Field(default_factory=list)
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


# class LectureVideo(BaseModel):
#     title: str
#     kind: Literal["foundation", "supplement"]   #  = "foundation"

#     lecture_no: str | None = None
#     topic: str | None = None
#     section: str | None = None

#     source_url: str
#     youtube_url: str | None #  = None
#     youtube_id: str | None  #  = None

#     # duration: str | None = None
#     duration: int | None = None


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
