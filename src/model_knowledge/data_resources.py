## data_resources.py
# import
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field



class LectureResource(BaseModel):
    # resource_id: str              # TODO: convert to new data models

    title: str | None = None
    source_url: str

    kind: Literal[
        "foundation",
        "supplement",
    ] = "foundation"

    resource_type: Literal[
        "video",
        "script",
        "material",
        "notebook",
        "exam", 
        "other",
    ]

    lecture_blocks: list[str] = Field(
        default_factory=list
    )

    # semester: str | None = None

    file_type: str | None = None
    local_path: Path | None = None

    downloaded: bool = False

    content_hash: str | None = None
    license: str | None = None


class LectureVideo(LectureResource):
    resource_type: Literal["video"] = "video"

    lecture_no: str | None = None
    topic: str | None = None

    youtube_url: str | None = None
    youtube_id: str | None = None
    duration: int | None = None


class LectureNotebook(LectureResource):
    resource_type: Literal["notebook"] = "notebook"


class LectureExam(LectureResource):
    resource_type: Literal["exam"] = "exam"


class LectureScript(LectureResource):
    resource_type: Literal["script"] = "script"


class LectureMaterial(LectureResource):
    resource_type: Literal["material"] = "material"


class LectureResource_old(BaseModel):
    videos: list[LectureVideo]
    scripts: list[LectureScript] 
    material: dict = Field(default_factory=dict)  # [str, LectureMaterial]
    other_links: dict[str, dict] = Field(default_factory=dict)


class LectureSection(BaseModel):
    section_id: str
    title: str | None = None

    videos: list[LectureVideo] = Field(
        default_factory=list
    )
    scripts: list[LectureScript] = Field(
        default_factory=list
    )
    materials: list[LectureMaterial] = Field(
        default_factory=list
    )


class LectureCourse(BaseModel):
    title: str
    source_url: str

    sections: list[LectureSection] = Field(
        default_factory=list
    )

    unassigned_resources: list[LectureResource] = Field(
                                            default_factory=list
                                            )

    examen: list = Field(
                default_factory=list
                )



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


