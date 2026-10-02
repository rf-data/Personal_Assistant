## run_lecture_processing.py
# import
from pathlib import Path
from datetime import datetime

from src.core.memory_lecture import LectureContext
from src.core.config import folder_env_vars
from src.core.memory import app_session
from src.core.logger import create_logger

from src.model_lecture.data_resources import (
    LectureCourse,
    # LectureResource,
    LectureResourceType,
    # LectureScript,
    # LectureVideo,
    # ResourceAction,
    ResourceTask,
)

from src.tools_lecture.process_lecture import execute_task

# from src.utils.path_helper import build_file_index
from src.utils.dict_helper import load_dict  # , save_dict


def run_lecture_processing():

    context_name = input("Enter name of context_file (no suffix): ")
    context_path = folder_env_vars.config_dir / f"context_{context_name}"
    context = load_dict(context_path, LectureContext)

    app_session.timestamp = datetime.today().strftime("%Y-%m-%d")
    app_session.logger = create_logger(
        name=context.logger_name,  # "RF_LOG"),
        file_name=context.logger_f_name,  #  "rf_log")
    )

    course_root = (
        folder_env_vars.data_lectures
        / context.provider  # loviscach"
        / context.course_id  # "mathe_1"
    )

    # course_path=(
    #         course_root
    #         / "metadata"
    #         / f"{context.course_id}_course"
    #         )

    # course = load_dict(course_path, LectureCourse)

    task_path = course_root / "metadata" / f"{context.course_id}_tasks"

    task_list = load_dict(task_path, ResourceTask)

    return lecture_processing(task_list, course_root)


def lecture_processing(
    task_list: list[ResourceTask],
    course: LectureCourse,
    # context: LectureContext,
    # resource_task: ,
    # folder_path: Path,
    # course: LectureCourse
) -> None:

    n_resources = len(task_list)
    for idx, task in enumerate(task_list, start=1):  # .items()
        if task.resource.title == "02A.4_Q":
            task.resource.title = "02A.4_Quotientenregel"

        app_session.logger.info(
            "[%s/%s] Start processing resource '%s' [type=%s, n_task=%s]",
            idx,
            n_resources,
            task.resource.title,
            task.resource.resource_type,
            len(task.actions),
        )

        if not task.actions:
            app_session.logger.info("  --> Found no actions.\n")

        execute_task(task, course)
        # _new = lecture_processing(task, course_root)

    return


if __name__ == "__main__":
    run_lecture_processing()
