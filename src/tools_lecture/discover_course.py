## create_course.py
# import
from pathlib import Path
from pydantic import BaseModel
import re

from src.core.memory import app_session
from src.core.config_transcribe import SUPPORTED_AUDIO_SUFFIXES
from src.model_lecture.data_resources import (
    DiscoveredCourseFile,
    LectureResourceType,
    ParsedLectureFilename,
)


def classify_course_file(path: Path) -> DiscoveredCourseFile:

    suffix = path.suffix.lower()

    match suffix:
        case ".wav" | ".mp3" | ".m4a":
            resource_type = LectureResourceType.AUDIO

        case ".pdf" | ".docx" | ".md" | ".txt":
            resource_type = LectureResourceType.DOCUMENT

        case ".mp4" | ".mkv" | ".webm":
            resource_type = LectureResourceType.VIDEO

        case _:
            resource_type = LectureResourceType.OTHER

            app_session.logger.info(
                "Unsupported discovered resource type: %s -> considered as 'OTHER'",
                suffix,
            )

    return DiscoveredCourseFile(
        path=path,
        # course_id=None,
        # : str | None = None
        # course_title="",
        # : str | None = None
        resource_type=resource_type,
        # : LectureResourceType | None = None
        resource_format=suffix.removeprefix("."),
        # : str | None = None
        # confidence: float | None = None
    )


def parse_lecture_filename(
    path: Path,
) -> ParsedLectureFilename:

    stem = path.stem

    parts = [part for part in re.split(r"[_\-\s]+", stem) if part]

    lecture_no: int | None = None
    sequence_no: str | None = None
    qualifier: str | None = None

    known_qualifiers = {
        "audio",
        "folie",
        "folien",
        "handout",
        "material",
        "note",
        "notes",
        "parsed",
        "script",
        "skript",
        "slides",
        "solution",
        "solutions",
        "transcript",
        "transkript",
        "video",
    }

    # --------------------------------------------------
    # 1. laufende Nummer erkennen
    # --------------------------------------------------

    if (
        path.suffix.lower() in SUPPORTED_AUDIO_SUFFIXES
        and parts
        and re.fullmatch(r"\d{3}", parts[-1])
    ):
        sequence_no = str(parts[-1]).zfill(3)
        parts = parts[:-1]

        # if parts[0].startswith

    # --------------------------------------------------
    # 2. bekannten Qualifier erkennen
    # --------------------------------------------------

    qualifier_index = None

    for i, part in enumerate(parts):
        if part.lower() in known_qualifiers:
            qualifier = part.lower()
            qualifier_index = i
            break

    if qualifier_index is not None:
        title_parts = parts[:qualifier_index]
        extra_parts = parts[qualifier_index:]
    else:
        title_parts = parts
        extra_parts = None

    title = "_".join(title_parts).strip() or None

    return ParsedLectureFilename(
        stem=stem,
        title=title,
        sequence_no=sequence_no,
        qualifier=qualifier,
        extra_parts=extra_parts,
    )


# def parse_lecture_filename(path: Path) -> ParsedLectureFileName:
#     '''
#     class ParsedLectureFilename(BaseModel):
#     lecture_no: int | None = None
#     lecture_key: str | None = None
#     title: str | None = None
#     qualifier: str | None = None
#     '''

#     return


# def infer_resource_type(
#                     path: Path,
#                     parsed_name: ParsedFilename
#                     ) -> LectureResourceType:


#     return
# lecture_compile
