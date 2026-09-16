## process_lecture.py
# import

from src.model_lecture.data_resources import (
    # LectureCourse,
    LectureResource,
    # LectureScript,
    # LectureVideo,
    ResourceAction,
    # ResourceTask,
)


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


execute_task()
execute_tasks()

download_resource()
transcribe_resource()
parse_resource()
extract_resource_knowledge()
