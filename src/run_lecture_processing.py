## run_lecture_processing.py
# import

from src.model_knowledge.data_resources import (
    # LectureCourse,
    LectureResource,
    # LectureScript,
    # LectureVideo,
    ResourceAction,
    # ResourceTask,
)
from src.run_lecture_compilation import build_file_index


def run_lecture_processing():

    return lecture_processing()


def execute_action(
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


def lecture_processing():

    while True:
        tasks = lecture_compilation(...)

        actionable_tasks = [task for task in tasks if task.actions]

        if not actionable_tasks:
            break

        for task in actionable_tasks:
            execute_action(
                task.resource,
                task.actions[0],
            )

        file_index = build_file_index(course_root)

    return


if __name__ == "__main__":
    run_lecture_processing()
