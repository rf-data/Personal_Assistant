## run_lecture_processing.py
# import
from pathlib import Path
from datetime import datetime

from src.core.memory_lecture import LectureContext
from src.core.config import folder_env_vars
from src.core.memory import app_session

from src.model_lecture.data_resources import (
    # LectureCourse,
    # LectureResource,
    # LectureScript,
    # LectureVideo,
    # ResourceAction,
    ResourceTask,
)

from src.utils.path_helper import build_file_index
from src.utils.dict_helper import load_dict, save_dict


def run_lecture_processing():

    context_name = input("Enter name of context_file (no suffix): ")
    context_path = folder_env_vars.config_dir / f"context_{context_name}.json"
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

    task_path = course_root / "metadata" / f"{context.course_id}_task"

    task_list = load_dict(task_path, ResourceTask)

    for task in task_list.items():
        app_session.logger.info(
            "Start processing resource '%s' [type=%s]",
            task.resource.title,
            task.resource.resource_type,
        )

        if not task.actions:
            app_session.logger.info("  --> Found no actions.\n")

        task_new = lecture_processing(task.actions, course_root)

    return


def lecture_processing(
    resource_task: ResourceTask,
    folder_path: Path,
    # course: LectureCourse
):

    while True:
        actionable_tasks = [action for action in resource_task.actions]

        if not actionable_tasks:
            break

        for task in actionable_tasks:
            if resource.resource_type == "video":
                execute_video_action(
                    task.resource,
                    task.actions[0],
                )
            elif resource.resource_type in ("script", "exam"):
                execute_document_action(
                    task.resource,
                    task.actions[0],
                )

        file_index = build_file_index(folder_path)

    return


if __name__ == "__main__":
    run_lecture_processing()
