## plan_lecture.py
# import
from pathlib import Path

from src.core.memory import app_session

from src.model_lecture.data_resources import (
    LectureResource,
    LectureScript,
    LectureVideo,
    ResourceAction,
    ResourceTask,
)

from src.utils.path_helper import find_indexed_files


TRANSCRIPT_SOURCE_SUFFIXES = {
    "vtt",
}

SUPPORTED_AUDIO_SUFFIXES = {
    "wav",
    "mp3",
    "m4a",
    "webm",
}


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
        if path.stem.endswith("_know_extract_results"):
            return "knowledge"

        elif path.stem.endswith("_visual_analysis"):
            return "visual_analysis"

        elif path.stem.endswith("_info"):
            return "metadata"

        else:
            return "transcript"

    if suffix in TRANSCRIPT_SOURCE_SUFFIXES:
        return "subtitle"

    if suffix in SUPPORTED_AUDIO_SUFFIXES:
        return "audio"

    if suffix in SUPPORTED_AUDIO_SUFFIXES:
        return "audio"

    if suffix in {"pdf", "docx", "doc"}:
        return "document"

    if suffix in {"jpg", "jpeg", "png", "webp"}:
        return "image"

    if suffix in {"md", "txt"}:
        return "text"

    return "other"


def get_transcript_actions(
    resource: LectureResource, file_index: list[Path]
) -> list[ResourceAction]:

    paths = get_resource_path(resource, file_index=file_index)

    if paths is None:
        app_session.logger.info("Found no transcript file for %s", resource.title)

        return [ResourceAction.DOWNLOAD]

    file_types = {classify_resource_file(path) for path in paths}

    if "transcript" in file_types:
        return []

    # Subtitle ist günstiger als Whisper.
    elif "subtitle" in file_types:
        return [
            ResourceAction.PARSE_SUBTITLE,
        ]

    # Audio ist vorhanden -> Whisper.
    elif "audio" in file_types:
        return [
            ResourceAction.TRANSCRIBE,
        ]

    return []


def get_knowledge_actions(
    resource: LectureResource, file_index: list[Path]
) -> list[ResourceAction]:

    paths = get_resource_path(
        resource,
        file_index=file_index,
    )

    if paths is None:
        app_session.logger.info("Found no knowledge file for %s", resource.source_url)

        return [ResourceAction.DOWNLOAD]

    file_types = {classify_resource_file(path) for path in paths}

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

    file_types = {classify_resource_file(path) for path in paths}

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

    file_types = {classify_resource_file(path) for path in paths}

    return [ResourceAction.DOWNLOAD]


def get_document_actions(
    resource: LectureResource, file_index: list[Path]
) -> list[ResourceAction]:

    paths = get_resource_path(
        resource,
        file_index=file_index,
    )

    if not paths:
        app_session.logger.info("Found no transcript file for %s", resource.source_url)

        return [ResourceAction.DOWNLOAD]

    file_types = {classify_resource_file(path) for path in paths}

    if "document" in file_types:
        return [ResourceAction.PARSE_DOCUMENT]

    # if "parsed" in file_types:
    #         return []

    # if "chunks" in file_types:
    #         return []

    # if "knowledge" in file_types:
    #         return []

    return []


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

    file_types = {classify_resource_file(path) for path in paths}

    return [ResourceAction.DOWNLOAD]


def select_resources_for_block(
    resources: list[LectureResource],
    block_id: str,
) -> list[LectureResource]:

    return [resource for resource in resources if block_id in resource.lecture_blocks]


def load_lecture_resources(data: dict) -> list[LectureResource]:
    resources: list[LectureResource] = []

    resources.extend(
        LectureVideo.model_validate(video) for video in data.get("videos", [])
    )

    resources.extend(
        LectureScript.model_validate(script) for script in data.get("scripts", [])
    )

    # materials noch nicht implementiert
    # resources.extend(
    #     # LectureMaterial.model_validate(material)
    #     material
    #     for material in data.get("material", [])
    #     )

    return resources


def build_resource_tasks(
    resources: list[LectureResource], file_index: list[Path]
) -> list[ResourceTask]:

    # for resource in resources:
    #     course_root = (
    #             folder_env_vars.data_lecture
    #             / "loviscach"
    #             / "mathe_1"
    #             )

    #     paths = get_resource_path(resource, file_index)

    #     if paths:
    #         for path in paths:
    #             organize_resource_file(
    #                 resource=resource,
    #                 source_path=path,
    #                 course_root=course_root,
    #             )

    return [
        ResourceTask(
            resource=resource,
            actions=get_required_actions(resource, file_index=file_index),
        )
        for resource in resources
    ]


def get_required_actions(
    resource: LectureResource, file_index: list[Path]
) -> list[ResourceAction]:

    resource.title = resource.title.replace(
        "Q](https://j3L7h2.de/videos/v.php?v=YiUD496LUyw)"
        "[uotientenregel](https://j3L7h2.de/videos/v.php?v=YiUD496LUyw)",
        "Quotientenregel](https://j3L7h2.de/videos/v.php?v=YiUD496LUyw)",
    )
    resource.title = resource.title.replace(",", "")

    match resource.resource_type:
        case "video":
            return get_transcript_actions(resource, file_index=file_index)

        case "script" | "material" | "exam":
            return get_document_actions(resource, file_index=file_index)

        case "notebook":
            return get_knowledge_actions(resource, file_index=file_index)

    return []
