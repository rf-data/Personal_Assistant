## plan_lecture.py
# import
from pathlib import Path

from src.core.memory import app_session
from src.core.config_transcribe import (
    SUPPORTED_AUDIO_SUFFIXES,
    SUPPORTED_TRANSCRIPT_SUFFIXES,
    SUPPORTED_VIDEO_SUFFIXES,
)
from src.model_lecture.data_resources import (
    LectureResource,
    LectureResourceType,
    LectureScript,
    LectureMedia,
    ResourceAction,
    ResourceTask,
)

from src.utils.path_helper import normalize_name, find_indexed_files
# from src.run_lecture_planning import lecture_planning


# lecture_compile


def matches_lecture_no(path: Path, lecture_no: str) -> bool:
    stem = path.stem.lower()
    lecture_no = lecture_no.lower()

    return (
        stem == lecture_no
        or stem.startswith(f"{lecture_no}_")
        or stem.startswith(f"{lecture_no}.")
    )


def get_resource_path(
    resource,
    file_index: list[Path],
) -> list[Path] | None:

    if not resource.title:
        app_session.logger.warning(
            "Resource has no title: %s",
            resource.source_url,
        )
        return None

    if not resource.lecture_blocks:
        app_session.logger.warning(
            "Resource has no lecture block: %s",
            resource.title,
        )
        return None

    resource.title = normalize_name(resource.title)

    f_paths = find_indexed_files(
        file_name=resource.title, files=file_index, exact=False
    )

    if f_paths:
        return f_paths

    app_session.logger.warning(
        "Found no matching files for %s --> Start search based on lecture_no, if applicable",
        resource.title,
        # len(f_paths),
        # "\n".join(str(path) for path in f_paths)
        # or " none"
    )

    lecture_no = getattr(
        resource,
        "lecture_no",
        None,
    )

    if not lecture_no:
        return None

    f_paths_new = find_indexed_files(
        file_name=resource.lecture_no, files=file_index, exact=False
    )

    if not f_paths_new:
        app_session.logger.warning(
            "Found no matching files for %s [based on lecture_no]",
            resource.title,
            # len(f_paths),
            # "\n".join(str(path) for path in f_paths)
            # or " none"
        )
        return None

    return f_paths_new

    # f_path = f_paths[0]

    # dst_path = folder_env_vars.data_audio / f"chapter_{resource.lecture_blocks[0]}/{resource.title}.json"

    # f_path = f_paths[0]

    # return dst_path


def classify_resource_file(
    path: Path,
) -> str:

    suffix = path.suffix.removeprefix(".").lower()
    # stem = path.stem.lower()

    if suffix == "json":
        if path.stem.endswith("_parsed") or path.stem.endswith("_docling"):
            return "parsed_document"

        elif path.stem.endswith("_know_extract_results"):
            return "knowledge"

        elif path.stem.endswith("_visual_analysis"):
            return "visual_analysis"

        elif path.stem.endswith("_info"):
            return "metadata"

        else:
            return "transcript"

    if suffix in SUPPORTED_TRANSCRIPT_SUFFIXES:
        return "subtitle"

    if suffix in SUPPORTED_VIDEO_SUFFIXES:
        return "audio"

    if suffix in SUPPORTED_AUDIO_SUFFIXES:
        return "audio"

    if suffix in {"pdf", "docx", "doc", "html", "htm"}:
        return "document"

    if suffix in {"jpg", "jpeg", "png", "webp"}:
        return "image"

    if suffix in {"zip"}:
        return "archive"

    if suffix in {"md", "txt"}:
        return "text"

    return "other"


def get_transcript_actions(
    resource: LectureResource, paths: list[Path]
) -> list[ResourceAction]:

    if paths is None:
        app_session.logger.info("Found no transcript file for %s", resource.title)

        return [ResourceAction.DOWNLOAD]

    file_types = {classify_resource_file(path) for path in paths}

    if "transcript" in file_types:
        return []

    # Subtitle ist günstiger als Whisper.
    elif "subtitle" in file_types:
        resource.local_path = get_path_by_type(
            paths,
            "subtitle",
        )
        return [ResourceAction.PARSE_SUBTITLE]

    # Audio ist vorhanden -> Whisper.
    if "audio" in file_types:
        resource.local_path = get_path_by_type(
            paths,
            "audio",
        )
        return [ResourceAction.TRANSCRIBE]

    if "archive" in file_types:
        resource.local_path = get_path_by_type(
            paths,
            "archive",
        )
        return [ResourceAction.DOWNLOAD]

    return [ResourceAction.DOWNLOAD]


def get_knowledge_actions(
    resource: LectureResource, paths: list[Path]
) -> list[ResourceAction]:

    if paths is None:
        app_session.logger.info("Found no knowledge file for %s", resource.source_url)

        return [ResourceAction.DOWNLOAD]

    # file_types = {classify_resource_file(path) for path in paths}

    return [ResourceAction.DOWNLOAD]


def get_visual_context_actions(
    resource: LectureResource, file_index: list[Path]
) -> list[ResourceAction]:

    paths = get_resource_path(
        resource,
        file_index=file_index,
    )

    if paths is None:
        app_session.logger.info("Found no transcript file for %s", resource.source_url)

        return [ResourceAction.DOWNLOAD]

    # file_types = {classify_resource_file(path) for path in paths}

    return [ResourceAction.DOWNLOAD]


def get_frame_actions(
    resource: LectureResource, file_index: list[Path]
) -> list[ResourceAction]:

    paths = get_resource_path(
        resource,
        file_index=file_index,
    )

    if paths is None:
        app_session.logger.info("Found no transcript file for %s", resource.source_url)

        return [ResourceAction.DOWNLOAD]

    # file_types = {classify_resource_file(path) for path in paths}

    return [ResourceAction.DOWNLOAD]


def get_path_by_type(
    paths: list[Path],
    file_type: str,
) -> Path | None:

    for path in paths:
        if classify_resource_file(path) == file_type:
            return path

    return None


def get_archive_actions(
    resource: LectureResource, paths: list[Path]
) -> list[ResourceAction]:

    if not paths:
        app_session.logger.info("Found no document file for %s", resource.source_url)

        return [ResourceAction.DOWNLOAD]

    return []


def get_document_actions(
    resource: LectureResource, paths: list[Path]
) -> list[ResourceAction]:

    if not paths:
        app_session.logger.info("Found no document file for %s", resource.source_url)

        return [ResourceAction.DOWNLOAD]

    file_types = {classify_resource_file(path) for path in paths}

    if "parsed_document" in file_types:
        return []

    document_path = get_path_by_type(
        paths,
        "document",
    )

    if document_path is not None:
        resource.local_path = document_path
        return [ResourceAction.PARSE_DOCUMENT]

    return [ResourceAction.DOWNLOAD]

    # file_types = {classify_resource_file(path) for path in paths}

    # if "document" in file_types:
    #     document_paths = [
    #         path
    #         for path in paths
    #         if classify_resource_file(path) == "document"
    #     ]

    #     resource.local_path = document_paths[0]

    #     return [ResourceAction.PARSE_DOCUMENT]

    # if "parsed" in file_types:
    #         return []

    # if "chunks" in file_types:
    #         return []

    # if "knowledge" in file_types:
    #         return []

    # return [ResourceAction.DOWNLOAD]


def get_chunk_actions(
    resource: LectureResource, file_index: list[Path]
) -> list[ResourceAction]:

    paths = get_resource_path(
        resource,
        file_index=file_index,
    )

    if paths is None:
        app_session.logger.info("Found no transcript file for %s", resource.source_url)

        return [ResourceAction.DOWNLOAD]

    # file_types = {classify_resource_file(path) for path in paths}

    return [ResourceAction.DOWNLOAD]


def select_resources_for_block(
    resources: list[LectureResource],
    block_id: str,
) -> list[LectureResource]:

    return [resource for resource in resources if block_id in resource.lecture_blocks]


def load_lecture_resources(data: dict) -> list[LectureResource]:
    resources: list[LectureResource] = []

    n_videos = len(data.get("videos", []))
    resources.extend(
        LectureMedia.model_validate(video) for video in data.get("videos", [])
    )

    n_scripts = len(data.get("scripts", []))
    resources.extend(
        LectureScript.model_validate(script) for script in data.get("scripts", [])
    )

    app_session.logger.info("Added %s videos and %s scripts", n_videos, n_scripts)
    # materials noch nicht implementiert
    # resources.extend(
    #     # LectureMaterial.model_validate(material)
    #     material
    #     for material in data.get("material", [])
    #     )

    return resources


def build_resource_tasks(
    resources,
    file_index,
):

    tasks = []

    for resource in resources:
        paths = (
            get_resource_path(
                resource,
                file_index,
            )
            or []
        )

        actions = get_required_actions(
            resource,
            paths,
        )

        tasks.append(
            ResourceTask(
                resource=resource,
                input_paths=paths,
                actions=actions,
            )
        )

    return tasks


def get_required_actions(
    resource: LectureResource, paths: list[Path]
) -> list[ResourceAction]:

    resource.title = resource.title.replace(
        "02A.4_Q",
        "Quotientenregel](https://j3L7h2.de/videos/v.php?v=YiUD496LUyw)",
        # Q](https://j3L7h2.de/videos/v.php?v=YiUD496LUyw)"
        # "[uotientenregel](https://j3L7h2.de/videos/v.php?v=YiUD496LUyw)",
    )

    if resource.title:
        resource.title = resource.title.replace(",", "")

    match resource.resource_type:
        case (
            "media"
            # | LectureResourceType.VIDEO
        ):
            return get_transcript_actions(resource, paths=paths)

        case (
            # LectureResourceType.SCRIPT
            # | LectureResourceType.MATERIAL
            # | LectureResourceType.EXAM
            "script" | "material" | "exam" | "document"
        ):
            return get_document_actions(resource, paths=paths)

        case (
            "notebook"
            # | LectureResourceType.NOTEBOOK
        ):
            return get_knowledge_actions(resource, paths=paths)

        case "archive":
            return get_archive_actions(resource, paths=paths)

    return []
