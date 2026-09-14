## run_lecture_compilation.py
# import
from pathlib import Path
from datetime import datetime
from pathlib import Path

from src.core.config import folder_env_vars
from src.core.memory import app_session
from src.core.memory_knowledge import KnowledgeContext
from src.core.logger import create_logger

from src.run_prepare_lecture_compilation import prepare_lecture_compilation
from src.utils.dict_helper import load_dict  # save_dict,
from src.utils.path_helper import move_file, find_folder_files
from src.model_knowledge.data_resources import (
    LectureResource,
    LectureScript,
    LectureVideo,
    ResourceAction,
    ResourceTask,
)

TRANSCRIPT_SOURCE_SUFFIXES = {
    "vtt",
}

SUPPORTED_AUDIO_SUFFIXES = {
    "wav",
    "mp3",
    "m4a",
    "webm",
}


def run_lecture_compilation():

    context_name = input("Enter name of context_file (no suffix): ")
    context_path = folder_env_vars.config_dir / f"context_{context_name}.json"
    context = load_dict(context_path, KnowledgeContext)

    app_session.timestamp = datetime.today().strftime("%Y-%m-%d")
    app_session.logger = create_logger(
        name=context.logger_name,  # "RF_LOG"),
        file_name=context.logger_f_name,  #  "rf_log")
    )

    if context.prepare_compilation:
        if not context.info_paths:
            raise ValueError("No info_file configured.")

        info_paths = context.info_paths
        elements = context.extract_elements

        # for path in info_paths:
        lecture_info = prepare_lecture_compilation(
            f_path=info_paths[0], elements=elements
        )

        # if lecture_info is not None:
        #     lectures_all.append(lecture_info)

    else:
        lecture_paths = context.lecture_paths

        if not lecture_paths:
            raise ValueError("No lecture_paths configured.")

        # for path in lecture_paths:
        lecture_info = load_dict(lecture_paths[0])

        # if lecture_info is not None:
        #     lectures_all.append(lecture_info)

    todo = lecture_compilation(
        lecture_info=lecture_info,
        block_id="01",
    )

    for task in todo:
        print(
            task.resource.resource_type,
            task.resource.title,
            task.actions,
        )

        # execute_resource_task()

    return todo


# ! TODO: in anderem Skript einbauen
# def execute_action(
#     resource: LectureResource,
#     action: ResourceAction,
# ) -> None:

#     match action:

#         case "download":
#             download_resource(resource)

#         case "transcribe":
#             transcribe_video(resource)

#         case "parse_document":
#             parse_document(resource)

#         case "extract_knowledge":
#             extract_resource_knowledge(resource)

#         case "extract_frames":
#             extract_visual_context(resource)


def get_resource_path(resource) -> list[Path] | None:

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

    f_paths = find_folder_files(
        file_name=resource.title,
        folder=folder_env_vars.data_audio,
        exact=False,
        recursive=True,
    )

    if len(f_paths) == 0:
        app_session.logger.warning(
            "Found no matching files for %s",
            resource.title,
            # len(f_paths),
            # "\n".join(str(path) for path in f_paths)
            # or " none"
        )
        return None

    return f_paths


def organize_resource_file(
    # resource: LectureResource,
    source_path: Path,
    dst_folder: str,
    # dst_suffix: str | None = None
) -> Path | None:
    # source_suffix = source_path.suffix.removeprefix(".").lower()

    # if dst_suffix is None:
    #     dst_suffix = source_suffix

    # invalid_suffixes = {
    #                 "vtt",
    #                 }
    # if source_suffix in invalid_suffixes:
    #     app_session.logger.warning(
    #                         "Found unsupported suffix '%s': %s",
    #                         source_suffix,
    #                         source_path
    #                                )
    #     return None

    dst_path = (
        folder_env_vars.data_audio
        / dst_folder  # f"chapter_{resource.lecture_blocks[0]}"
        / source_path.name
    )

    if (
        source_path != dst_path
        # and source_suffix == dst_suffix
    ):
        move_file(source_path, dst_path)

    return dst_path

    # f_path = f_paths[0]

    # dst_path = folder_env_vars.data_audio / f"chapter_{resource.lecture_blocks[0]}/{resource.title}.json"

    # f_path = f_paths[0]

    # return dst_path


def classify_resource_file(
    path: Path,
) -> str:

    suffix = path.suffix.removeprefix(".").lower()

    if suffix == "json":
        if path.stem.endswith("_know_extract_results"):
            return "knowledge_extract"

        elif path.stem.endswith("_visual_analysis"):
            return "visual_analysis"

        elif path.stem.endswith("_info"):
            return "file_info"

        else:
            return "transcript"

    if suffix in TRANSCRIPT_SOURCE_SUFFIXES:
        return "subtitle"

    if suffix in SUPPORTED_AUDIO_SUFFIXES:
        return "audio"

    return "other"


def get_transcript_actions(
    resource: LectureResource,
) -> list[ResourceAction]:

    paths = get_resource_path(resource)

    if paths is None:
        app_session.logger.info("Found no transcript file for %s", resource.source_url)

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

    return [ResourceAction.DOWNLOAD]


def get_knowledge_actions(
    resource: LectureResource,
) -> list[ResourceAction]:

    paths = get_resource_path(resource)

    if paths is None:
        app_session.logger.info("Found no knowledge file for %s", resource.source_url)

        return [ResourceAction.DOWNLOAD]

    file_types = {classify_resource_file(path) for path in paths}

    return [ResourceAction.DOWNLOAD]


def get_visual_context_actions(
    resource: LectureResource,
) -> bool:

    paths = get_resource_path(resource)

    if paths is None:
        app_session.logger.info("Found no transcript file for %s", resource.source_url)

        return [ResourceAction.DOWNLOAD]

    file_types = {classify_resource_file(path) for path in paths}

    return [ResourceAction.DOWNLOAD]


def get_frame_actions(
    resource: LectureResource,
) -> bool:

    paths = get_resource_path(resource)

    if paths is None:
        app_session.logger.info("Found no transcript file for %s", resource.source_url)

        return [ResourceAction.DOWNLOAD]

    file_types = {classify_resource_file(path) for path in paths}

    return [ResourceAction.DOWNLOAD]


def get_parsed_document_actions(
    resource: LectureResource,
) -> bool:

    paths = get_resource_path(resource)

    if paths is None:
        app_session.logger.info("Found no transcript file for %s", resource.source_url)

        return [ResourceAction.DOWNLOAD]

    file_types = {classify_resource_file(path) for path in paths}

    return [ResourceAction.DOWNLOAD]


def get_chunk_actions(
    resource: LectureResource,
) -> bool:

    paths = get_resource_path(resource)

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
    resources: list[LectureResource],
) -> list[ResourceTask]:

    return [
        ResourceTask(
            resource=resource,
            actions=get_required_actions(resource),
        )
        for resource in resources
    ]


def get_required_actions(
    resource: LectureResource,
) -> list[ResourceAction]:

    actions = []

    if not resource.downloaded:
        actions.append(ResourceAction.DOWNLOAD)

    match resource.resource_type:
        case "video":
            trans_actions = get_transcript_actions(resource)

            if trans_actions is not None:
                actions.extend(trans_actions)

            # if not knowledge_exists(resource):
            #     actions.append("extract_knowledge")

            # elif visual_context_needed(resource):
            #     if not frames_exist(resource):
            #         actions.append("extract_frames")

        case "script" | "material":
            if not parsed_document_exists(resource):
                actions.append("parse_document")

            if not chunks_exist(resource):
                actions.append("chunk")

            if not knowledge_exists(resource):
                actions.append("extract_knowledge")

        case "notebook":
            if not knowledge_exists(resource):
                actions.append("extract_knowledge")

    return actions


def lecture_compilation(lecture_info: dict, block_id: str):
    # lecture = load_dict(lecture_path)

    resources = load_lecture_resources(lecture_info)
    # resources = parse_resources(lecture_data)

    block_resources = select_resources_for_block(
        resources,
        block_id=block_id,
    )

    return build_resource_tasks(block_resources)


if __name__ == "__main__":
    run_lecture_compilation()
