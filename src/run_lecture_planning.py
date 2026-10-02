## run_lecture_planning.py
# import
from pathlib import Path
from datetime import datetime

from src.core.config import folder_env_vars
from src.core.memory import app_session
from src.core.memory_lecture import LectureContext
from src.core.logger import create_logger

from src.run_lecture_preparation import lecture_preparation
from src.utils.dict_helper import load_dict, save_dict
from src.utils.path_helper import build_file_index

from src.model_lecture.data_resources import (
    LectureCourse,
    LectureResourceUnion,
    ResourceTask,
)

from src.tools_lecture.plan_lecture import (
    build_resource_tasks,
    load_lecture_resources,
    select_resources_for_block,
)


def run_lecture_planning() -> list[ResourceTask]:

    context_name = input("Enter name of context_file (no suffix): ")
    context_path = folder_env_vars.config_dir / f"context_{context_name}"
    context = load_dict(context_path, LectureContext)

    app_session.timestamp = datetime.today().strftime("%Y-%m-%d")
    app_session.logger = create_logger(
        name=context.logger_name,  # "RF_LOG"),
        file_name=context.logger_f_name,  #  "rf_log")
    )

    course = LectureCourse(
        course_id=context.course_id,
        course_title=context.course_title,
        provider=context.provider,
        source_url=context.source_url,
        # root=(folder_env_vars. / "")
        # sections: list[LectureSection] = Field(default_factory=list)
        # resources: list[LectureResource] = Field(default_factory=list)
        # unassigned_resources: list[LectureResource] = Field(default_factory=list)
        # examen: list = Field(default_factory=list)
    )

    file_index = build_file_index(course.root)

    block_ids = [f"{block_id:02d}" for block_id in range(1, 29)]

    todo: list[ResourceTask] = []

    for block_id in block_ids:
        todo.extend(
            lecture_planning(
                lecture_info=lecture_info, block_id=block_id, file_index=file_index
            )
        )

    app_session.logger.info(
        "Found %s todo's in lecture %s\n[block: %s]",
        len([task for task in todo if len(task.actions) > 0]),
        f"{course.provider} / {course.course_title}",
        block_ids,
    )

    task_open = [task for task in todo if task.actions]

    for task in task_open:
        # if len(task.actions) > 0:
        #     task_open.append({"name": task.resource.title, "task": task})

        print(f"""RESOURCE_TYPE:\t {task.resource.resource_type}
RESOURCE_TITLE:\t {task.resource.title}
ACTIONS:\t{task.actions}
""")

    save_dict(
        data=[task.model_dump(mode="json") for task in task_open],
        path=(course.root / "metadata" / f"{course.course_id}_tasks"),
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


def plan_course_tasks(
    resources: list[LectureResourceUnion],
    file_index: list[Path],
    block_ids: list[str] | None = None,
):

    # block_ids = [f"{block_id:02d}" for block_id in range(1, 29)]

    # task_list: list[ResourceTask] = []

    if block_ids:
        resources = [
            resource
            for resource in resources
            if any(block_id in resource.lecture_blocks for block_id in block_ids)
        ]

        # for block_id in block_ids:
        #     task_list.extend(
        #         lecture_planning(
        #             lecture_info=lecture_info,
        #             # context=
        #             block_id=block_id,
        #             file_index=file_index,
        #         )
        #     )

    return [
        task
        for task in build_resource_tasks(
            resources=resources,
            file_index=file_index,
        )
        if task.actions
    ]


# task for task in task_list if task.actions


def lecture_planning(
    lecture_info: dict,
    block_id: str,
    file_index: list[Path],
    # context: LectureContext
    # course: LectureCourse
) -> list[ResourceTask]:
    # lecture = load_dict(lecture_path)

    resources = load_lecture_resources(lecture_info)
    # resources = parse_resources(lecture_data)

    block_resources = select_resources_for_block(
        resources,
        block_id=block_id,
    )

    app_session.logger.info(
        "Selected %s resources for block %s", len(block_resources), block_id
    )

    return build_resource_tasks(block_resources, file_index)


if __name__ == "__main__":
    run_lecture_planning()
