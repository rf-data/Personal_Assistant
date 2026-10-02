## run_lecture_compilation.py
# imports
# from pathlib import Path
from datetime import datetime

from src.core.memory_lecture import LectureContext
from src.core.config import folder_env_vars
from src.core.memory import app_session
from src.core.logger import create_logger

from src.model_lecture.data_resources import LectureCourse, ResourceTask

from src.tools_lecture.assemble_course import build_lecture_course_from_folder
from src.run_lecture_planning import plan_course_tasks
from src.utils.dict_helper import load_dict, save_dict
from src.utils.path_helper import build_file_index

from src.run_lecture_preparation import lecture_preparation
from src.run_lecture_processing import lecture_processing


def run_lecture_compilation():

    context_name = input("Enter name of context_file (no suffix): ")
    context_path = folder_env_vars.config_dir / f"context_{context_name}"
    context = load_dict(context_path, LectureContext)

    app_session.timestamp = datetime.today().strftime("%Y-%m-%d")
    app_session.logger = create_logger(
        name=context.logger_name,  # "RF_LOG"),
        file_name=context.logger_f_name,  #  "rf_log")
    )

    # root=(folder_env_vars. / "")
    # sections: list[LectureSection] = Field(default_factory=list)
    # resources: list[LectureResource] = Field(default_factory=list)
    # unassigned_resources: list[LectureResource] = Field(default_factory=list)
    # examen: list = Field(default_factory=list)

    # course_root = (
    #     folder_env_vars.data_lectures
    #     / context.provider  # loviscach"
    #     / context.course_id  # "mathe_1"
    # )

    return lecture_compilation(context)  # , course)

    # info_path = (
    #         folder_env_vars.lectures_data / \
    #             f"{context.provider}/"\
    #             f"{context.course_id}/"\
    #             "metadata/course_info.json"
    #             )

    # if info_path.exists:
    #     course = load_dict(
    #             path=info_path,
    #             cls=LectureCourse
    #             )

    # else:


def lecture_compilation(context: LectureContext):
    # , course: LectureCourse):

    course = prepare_course(context)

    tasks = process_course_until_complete(
        course=course,
        # lecture_info=lecture_info,
        context=context,
    )

    return course, tasks


def prepare_course(context: LectureContext) -> LectureCourse:
    # tuple[LectureCourse, dict]:

    match context.prepare_lecture:
        case "from_info":
            course = LectureCourse(
                course_id=context.course_id,
                course_title=context.course_title,
                provider=context.provider,
                source_url=context.source_url,
            )

            # info_path = (
            #     course.root
            #     / f"metadata"
            #     / f"{course.provider}_{course.course_id}_info.json"
            # )

            # if not info_path.exists():
            #     raise ValueError(f"Info_file does NOT exists: {info_path}")

            # # for path in info_paths:
            # lecture_info = lecture_preparation(f_path=info_path,
            #    elements=context.extract_elements)

            # lecture_info: list[int] = []

            # for key, resources in prep_dict.items():
            #     if key in ("scripts", "videos"):
            #         for res in resources:
            #             if res.lecture_blocks:
            #                 lecture_info.extend(res.lecture_blocks)

            # if lecture_info is not None:
            #     lectures_all.append(lecture_info)

        case "from_folder":
            course = build_lecture_course_from_folder(
                input_folder=(
                    folder_env_vars.data_lectures
                    / f"{context.provider}/{context.course_id}"
                ),
                course_title=context.course_title,
            )

            # lecture_info = course
            # convert_course_data(course)

        case _:
            raise ValueError(f"Unknown prepare_lecture mode: {context.prepare_lecture}")

    return course


# , lecture_info


# def convert_course_data(course: LectureCourse) -> dict:
#     """
#       {
#     "course_id": "Cannabinoide",
#     "course_title": "Cannabinoide - Ungleiche Geschwister",
#     "examen": [],
#     "provider": "lakbb",
#     "resources": [
#       {
#         "content_hash": null,
#         "downloaded": true,
#         "duration": null,
#         "file_type": "wav",
#         "lecture_blocks": [],
#         "lecture_no": null,
#         "license": null,
#         "local_path": "/mnt/chromeos/GoogleDrive/MyDrive/1_Projekte_Datensätze/1_Projekte/00_GMP_Compliance/data/lectures/lakbb/Cannabinoide/audio/2_Cannabinoide_CBD_000.wav",
#         "media_type": "audio",
#         "resource_kind": "foundation",
#         "resource_type": "media",
#         "source_url": null,
#         "title": "2 Cannabinoide CBD 000",
#         "topic": null,
#         "youtube_id": null,
#         "youtube_url": null
#       },
#       [...]
#     """

#     lecture_blocks: list[int] = []
#     for res in course.resources:
#         if res.lecture_blocks:
#             lecture_blocks.extend(res.lecture_blocks)

#     return {
#         "lecture_blocks": lecture_blocks
#         }

# lecture_path = (
#         course.root
#         / f"metadata"
#         / f"{course.provider}_{course.course_id}_lectures_new.json"
#     )

#     if not lecture_path.exists():
#         raise ValueError(f"Lecture_path does NOT exist: {lecture_path}")

#     # for path in lecture_paths:
#     lecture_info = load_dict(lecture_path)

# if lecture_info is not None:
#     lectures_all.append(lecture_info)

# for task in task_list:
#         # if len(task.actions) > 0:
#         #     task_open.append({"name": task.resource.title, "task": task})

#     print(f"""RESOURCE_TYPE:\t {task.resource.resource_type}
# RESOURCE_TITLE:\t {task.resource.title}
# ACTIONS:\t{task.actions}
# """)


def get_block_ids(course: LectureCourse) -> list[str]:
    return course.lecture_blocks
    # or []


# , [])


def process_course_until_complete(
    course: LectureCourse,
    context: LectureContext,
    # context: LectureContext,
    *,
    max_cycles: int = 20,
) -> list[ResourceTask]:
    # save_dict(
    #         data=[
    #             task.model_dump(mode="json") for task in task_list
    #             ],
    #         path=(course.root / "metadata" / f"{course.course_id}_tasks")
    #     )

    context.lecture_root = course.root

    previous_signature = None
    last_tasks: list[ResourceTask] = []

    for cycle in range(1, max_cycles + 1):
        app_session.logger.info(
            "Start compilation cycle %s",
            cycle,
        )

        # Wichtig:
        # neuen Dateistand erfassen
        file_index = build_file_index(course.root)

        tasks = plan_course_tasks(
            resources=course.resources,
            # lecture_info=lecture_info,
            block_ids=get_block_ids(course),
            file_index=file_index,
        )

        save_task_list(
            course=course,
            tasks=tasks,
        )

        if not tasks:
            app_session.logger.info(
                "Lecture compilation completed after %s cycle(s)",
                cycle - 1,
            )

            return last_tasks

        signature = get_task_signature(tasks)

        if signature == previous_signature:
            raise RuntimeError(
                "Lecture compilation made no progress. "
                "Planning produced the same tasks twice."
            )

        app_session.logger.info(
            "Cycle %s: processing %s task(s)",
            cycle,
            len(tasks),
        )

        lecture_processing(tasks, context)

        previous_signature = signature
        last_tasks = tasks

    raise RuntimeError(f"Lecture compilation did not finish after {max_cycles} cycles.")


def get_task_signature(
    tasks: list[ResourceTask],
) -> tuple:

    return tuple(
        sorted(
            (
                task.resource.title,
                task.resource.resource_type,
                tuple(action.value for action in task.actions),
            )
            for task in tasks
        )
    )


def save_task_list(
    course: LectureCourse,
    tasks: list[ResourceTask],
) -> None:

    save_dict(
        data=[task.model_dump(mode="json") for task in tasks],
        path=(course.root / "metadata" / f"{course.course_id}_tasks"),
    )

    return None

    # task_state = Counter()
    # n_states_old = sum(list(task_state.values()))
    # state_types_old = list(task_state.keys())

    # n_states: int | None = None
    # state_types: list | None = None

    # while (
    #     (
    #     not state_types and not n_states
    #     ) or (
    #     # state_types and state_types_new
    #     # and
    #     n_states and n_states_old > n_states
    #     ) or (
    #     state_types and state_types != state_types_old
    #     )
    # ):

    #     lecture_processing(task_list)

    #     save_dict(
    #             data=[
    #                 task.model_dump(mode="json") for task in task_list
    #                 ],
    #             path=(course.root / "metadata" / f"{course.course_id}_tasks")
    #             )

    #     task_state = Counter()
    #     n_states = sum(list(task_state.values()))
    #     state_types = list(task_state.keys())

    #     n_states_new: int | None = None
    #     state_types_new: list | None = None

    # return None


if __name__ == "__main__":
    run_lecture_compilation()
