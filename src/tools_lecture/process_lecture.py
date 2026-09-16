## process_lecture.py
# import

from src.core.config import folder_env_vars
from src.core.memory_transcribe import AudioContext
from src.core.memory import app_session

from src.model_transcribe.data_transcribe import DownloadResult
from src.model_lecture.data_resources import (
    # LectureCourse,
    LectureResource,
    # LectureScript,
    # LectureVideo,
    LectureResourceType,
    ResourceAction,
    ResourceTask,
)
from src.model_transcribe.provider_transcript import get_transcription_provider

from src.tools_transcribe.process_subtitle import parse_subtitle, transcribe_files

from src.utils.dict_helper import load_dict

from src.run_audio_transcription import audio_transcription


def execute_task(task: ResourceTask):
    resource = task.resource

    # while True:
    #    actionable_tasks = [action for action in resource_task.actions]

    # if not actionable_tasks:
    #     break

    for action in task.actions:
        if resource.resource_type == LectureResourceType.VIDEO:
            execute_video_action(
                resource=resource,
                action=action,
            )

        elif resource.resource_type in (
            LectureResourceType.SCRIPT,
            LectureResourceType.EXAM,
        ):
            execute_document_action(
                resource=resource,
                action=action,
            )

        # file_index = build_file_index(folder_path)

    return


def execute_document_action(
    resource: LectureResource,
    action: ResourceAction,
) -> None:

    match action:
        case ResourceAction.DOWNLOAD:
            ...

        case ResourceAction.TRANSCRIBE:
            ...

        case ResourceAction.PARSE_SUBTITLE:
            ...

        case ResourceAction.PARSE_DOCUMENT:
            ...

    return


def execute_video_action(
    resource: LectureResource,
    action: ResourceAction,
) -> None:

    audio_context = load_dict(
        path=(folder_env_vars.config_dir / "cfg_lecture_transcribe"), cls=AudioContext
    )
    audio_context.source = "local"
    audio_context.local_path = [resource.local_path]
    # (
    #                         source="",
    #                         local_path="",
    #                         cfg_transcribe={
    #                             "model_size":""
    #                         }
    # )
    provider = get_transcription_provider(
        context=audio_context,
        logger=app_session.logger,
    )

    match action:
        case ResourceAction.DOWNLOAD:
            transcript = audio_transcription(audio_context)

        case ResourceAction.TRANSCRIBE:
            source_result = DownloadResult(success=True, paths=[])

            transcript = transcribe_files(source_result, provider, audio_context)

        case ResourceAction.PARSE_SUBTITLE:
            transcript = parse_subtitle(path="")

        # case ResourceAction.PARSE_DOCUMENT:
        #     ...

    return transcript


# execute_task()
# execute_tasks()

# download_resource()
# transcribe_resource()
# parse_resource()
# extract_resource_knowledge()
