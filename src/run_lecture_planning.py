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
    ResourceTask,
)

from src.tools_lecture.plan_lecture import (
    build_resource_tasks,
    load_lecture_resources,
    select_resources_for_block,
)


def run_lecture_planning() -> list[ResourceTask]:

    context_name = input("Enter name of context_file (no suffix): ")
    context_path = folder_env_vars.config_dir / f"context_{context_name}.json"
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
        # sections: list[LectureSection] = Field(default_factory=list)
        # resources: list[LectureResource] = Field(default_factory=list)
        # unassigned_resources: list[LectureResource] = Field(default_factory=list)
        # examen: list = Field(default_factory=list)
    )

    if context.prepare_lecture:
        info_path = (
            course.root
            / f"metadata"
            / f"{course.provider}_{course.course_id}_info.json"
        )
        if not info_path.exists():
            raise ValueError("Info_file does NOT exists.")

        # context.info_paths
        elements = context.extract_elements

        # for path in info_paths:
        lecture_info = lecture_preparation(f_path=info_path, elements=elements)

        # if lecture_info is not None:
        #     lectures_all.append(lecture_info)

    else:
        lecture_path = (
            course.root
            / f"metadata"
            / f"{course.provider}_{course.course_id}_lectures_new.json"
        )

        if not lecture_path.exists():
            raise ValueError("Lecture_paths does NOT exist.")

        # for path in lecture_paths:
        lecture_info = load_dict(lecture_path)

        # if lecture_info is not None:
        #     lectures_all.append(lecture_info)

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
        "Found %s todo's in lecture %s [block: %s]",
        len(todo),
        f"{course.provider} / {course.course_title}",
        block_ids,
    )

    task_open = []
    for task in todo:
        print(f"""RESOURCE_TYPE:\t {task.resource.resource_type}
RESOURCE_TITLE:\t {task.resource.title}
ACTIONS:\t{task.actions}
""")

        if len(task.actions) > 0:
            task_open.append({"name": task.resource.title, "task": task})

    save_dict(
        data=[task["task"].model_dump(mode="json") for task in task_open],
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


def lecture_planning(
    lecture_info: dict,
    block_id: str,
    file_index: list[Path],
    # course: LectureCourse
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
    run_lecture_planning()
