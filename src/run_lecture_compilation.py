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
from src.utils.dict_helper import load_dict, save_dict
from src.utils.path_helper import (
    move_file,
    # find_folder_files,
    shorten_path,
)
from src.model_knowledge.data_resources import (
    LectureCourse,
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

RESOURCE_FILE_FOLDERS = {
    "audio": "audio",
    "subtitle": "subtitles",
    "transcript": "transcripts",
    "knowledge": "knowledge",
    "visual_analysis": "visual_analysis",
    "metadata": "metadata",
    "document": "documents",
    "image": "images",
    "text": "text",
    "other": "other",
}


# lecture_compile


def run_lecture_compilation() -> list[ResourceTask]:

    context_name = input("Enter name of context_file (no suffix): ")
    context_path = folder_env_vars.config_dir / f"context_{context_name}.json"
    context = load_dict(context_path, KnowledgeContext)

    app_session.timestamp = datetime.today().strftime("%Y-%m-%d")
    app_session.logger = create_logger(
        name=context.logger_name,  # "RF_LOG"),
        file_name=context.logger_f_name,  #  "rf_log")
    )

    course = LectureCourse(
        course_id=context.course_id,
        title=context.course_title,
        provider=context.provider,
        source_url=context.source_url,
        # sections: list[LectureSection] = Field(default_factory=list)
        # resources: list[LectureResource] = Field(default_factory=list)
        # unassigned_resources: list[LectureResource] = Field(default_factory=list)
        # examen: list = Field(default_factory=list)
    )

    course_root = (
        folder_env_vars.data_lectures
        / course.provider  # loviscach"
        / course.course_id  # "mathe_1"
    )

    save_dict(
        data=course.model_dump(),
        path=(course_root / "metadata" / f"{course.course_id}_course"),
    )

    if context.prepare_compilation:
        if not context.info_paths:
            raise ValueError("No info_file configured.")

        info_path = (
            course_root
            / f"metadata"
            / f"{course.provider}_{course.course_id}_info.json"
        )
        # context.info_paths
        elements = context.extract_elements

        # for path in info_paths:
        lecture_info = prepare_lecture_compilation(f_path=info_path, elements=elements)

        # if lecture_info is not None:
        #     lectures_all.append(lecture_info)

    else:
        lecture_path = (
            course_root
            / f"metadata"
            / f"{course.provider}_{course.course_id}_lectures_new.json"
        )

        if not lecture_path.exists():
            raise ValueError("No lecture_paths configured.")

        # for path in lecture_paths:
        lecture_info = load_dict(lecture_path)

        # if lecture_info is not None:
        #     lectures_all.append(lecture_info)

    file_index = build_file_index(course_root)

    block_ids = [f"{block_id:02d}" for block_id in range(1, 29)]

    todo: list[ResourceTask] = []

    for block_id in block_ids:
        todo.extend(
            lecture_compilation(
                lecture_info=lecture_info, block_id=block_id, file_index=file_index
            )
        )

    app_session.logger.info(
        "Found %s todo's in lecture %s [block: %s]",
        len(todo),
        f"{course.provider} / {course.course_title}",
        block_ids,
    )

    task_open = {}
    for task in todo:
        print(f"""RESOURCE_TYPE:\t {task.resource.resource_type}
RESOURCE_TITLE:\t {task.resource.title}
ACTIONS:\t{task.actions}
""")

        if len(task.actions) > 0:
            task_open[task.resource.title] = {
                "type": task.resource.resource_type,
                "actions": task.actions,
            }

    save_dict(
        data=task_open, path=(course_root / "metadata" / f"{course.course_id}_tasks")
    )

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


def get_resource_target_folder(
    resource: LectureResource,
    path: Path,
) -> str:

    file_type = classify_resource_file(path)

    if resource.resource_type == "script":
        return "scripts"

    if resource.resource_type == "exam":
        return "exams"

    if resource.resource_type == "material":
        return "material"

    if file_type == "other":
        app_session.logger.warning(
            "Unclassified file, not moving: %s",
            path,
        )
        return path

    return RESOURCE_FILE_FOLDERS[file_type]


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


def organize_resource_file(
    resource: LectureResource,
    source_path: Path,
    course_root: Path,
    dry_run: bool = False,
) -> Path | None:

    source_path = Path(source_path)

    if not source_path.is_file():
        raise ValueError(f"Source path is not a file: {source_path}")

    dst_folder = get_resource_target_folder(
        resource=resource,
        path=source_path,
    )

    dst_path = course_root / dst_folder / source_path.name

    if source_path.resolve() == dst_path.resolve():
        app_session.logger.debug(
            "File already organized: %s",
            source_path,
        )
        return source_path

    if dst_path.exists():
        app_session.logger.warning(
            "Destination already exists. "
            "File will not be moved:\n"
            "source: %s\n"
            "target: %s",
            source_path,
            dst_path,
        )
        return dst_path

    if dry_run:
        app_session.logger.info(
            "Would move:\n%s\n-> %s",
            source_path,
            dst_path,
        )

        return dst_path

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


def build_file_index(
    folder: str | Path,
) -> list[Path]:

    folder = Path(folder)

    app_session.logger.info("Start building file index")
    if not folder.exists():
        raise FileNotFoundError(f"Folder does not exist: {folder}")

    if not folder.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {folder}")

    files = [path for path in folder.rglob("*") if path.is_file()]

    app_session.logger.info(
        "Built file index with %s files from %s",
        len(files),
        shorten_path(folder, 4),
    )

    return files


def normalize_name(name: str) -> str:
    return (
        name.casefold()
        .replace("ä", "a")
        .replace("ö", "o")
        .replace("ü", "u")
        .replace("ß", "ss")
    )


def find_indexed_files(
    file_name: str,
    files: list[Path],
    suffix: str | None = None,
    exact: bool = True,
) -> list[Path]:

    search_name = normalize_name(file_name)

    suffix = suffix.removeprefix(".").casefold() if suffix else None

    matches = []

    for path in files:
        if suffix and path.suffix.removeprefix(".").casefold() != suffix:
            continue

        stem = normalize_name(path.stem)  # .casefold()

        if exact:
            is_match = stem == search_name
        else:
            is_match = stem.startswith(search_name)

        if is_match:
            matches.append(path)

    app_session.logger.info(
        "Found %s indexed matching file(s):\n%s",
        len(matches),
        "\n".join(f"  {shorten_path(path, 4)}" for path in matches) or "  none",
    )

    return matches


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

    match resource.resource_type:
        case "video":
            return get_transcript_actions(resource, file_index=file_index)

        case "script" | "material" | "exam":
            return get_document_actions(resource, file_index=file_index)

        case "notebook":
            return get_knowledge_actions(resource, file_index=file_index)

    return []


def lecture_compilation(
    lecture_info: dict, block_id: str, file_index: list[Path]
) -> list[ResourceTask]:
    # lecture = load_dict(lecture_path)

    resources = load_lecture_resources(lecture_info)
    # resources = parse_resources(lecture_data)

    block_resources = select_resources_for_block(
        resources,
        block_id=block_id,
    )

    return build_resource_tasks(block_resources, file_index)


if __name__ == "__main__":
    run_lecture_compilation()
