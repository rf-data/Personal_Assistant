## create_course.py
# import
from pathlib import Path
from collections import Counter
from src.model_lecture.data_resources import (
    DiscoveredCourseFile,
    LectureCourse,
    LectureDocument,
    LectureMedia,
    LectureOther,
    LectureResourceType,
    LectureResourceUnion,
    ParsedLectureFilename,
    # LectureScript,
    # LectureVideo,
    # # LectureResourceType,
    # ResourceAction,
    # ResourceTask,
)

from src.core.memory import app_session

from src.tools_lecture.discover_course import (
    DiscoveredCourseFile,
    classify_course_file,
    parse_lecture_filename,
)
from src.utils.path_helper import list_folder_files, shorten_path
from src.utils.dict_helper import save_dict


def build_lecture_course_from_folder(
    input_folder: Path,
    *,
    course_title: str | None = None,
) -> LectureCourse:

    course_id = input_folder.name

    paths = list_folder_files(input_folder)

    manifest: list[DiscoveredCourseFile] = []

    for path in paths:
        f_info = classify_course_file(path)
        f_info.course_id = course_id
        f_info.course_title = course_title

        f_info.parsed_name = parse_lecture_filename(path)

        manifest.append(f_info)

    f_types = Counter(file.resource_type or "<no_resource_type>" for file in manifest)

    f_types_sum = "\n".join(
        f"  {resource_type}: {count}" for resource_type, count in f_types.most_common()
    )

    app_session.logger.info(
        "Classified %s file(s) from %s:\n%s",
        len(manifest),
        shorten_path(input_folder),
        f_types_sum,
    )

    save_dict(
        data=[file.model_dump(mode="json") for file in manifest],
        path=(input_folder / "metdata/course_manifest.json"),
    )
    # grouped = group_files_into_lectures(discovered)

    lectures = [
        build_lecture_resource(
            file=file,
        )
        for file in manifest
        # sorted(grouped.items())
    ]

    course = LectureCourse(
        course_id=course_id,
        course_title=course_title or input_folder.name,
        provider=input_folder.parent.name,
        resources=lectures,  # resources,
        source_url=None,
        # root_folder=input_folder
    )

    save_dict(
        data=course.model_dump(mode="json"),
        # [
        #     file.model_dump(mode="json")
        #     for file in discovered
        #     ],
        path=(input_folder / "metdata/course_info.json"),
    )

    return course


def build_lecture_resource(
    file: DiscoveredCourseFile,
) -> LectureResourceUnion:

    match file.resource_type:
        case LectureResourceType.AUDIO | LectureResourceType.VIDEO:
            return LectureMedia(
                title=file.parsed_name.title,
                source_url=None,
                local_path=file.path,
                file_type=file.resource_format,
                media_type=file.resource_type.value,
                downloaded=True,
            )

        case LectureResourceType.DOCUMENT:  # LectureResourceType.DOCUMENT:
            return LectureDocument(
                title=file.parsed_name.title,
                source_url=None,
                local_path=file.path,
                file_type=file.resource_format,
                resource_type=file.resource_type.value,
                downloaded=True,
                lecture_no=file.parsed_name.sequence_no,
            )

        case _:
            app_session.logger.info(
                "Unsupported / unspecified resource type discovered in file '%s' ('%s') --> considered as 'OTHER'",
                file.path.name,
                file.resource_type,
            )

            return LectureOther(
                title=file.parsed_name.title,
                source_url=str(file.path),
                local_path=file.path,
                file_type=file.resource_format,
                resource_type=file.resource_type.value,
                downloaded=True,
            )


# def group_files_into_lectures(
#     files: list[DiscoveredCourseFile],
# ) -> dict[str, list[DiscoveredCourseFile]]:
#     ...


#     return


# def build_lecture(
#     lecture_key: str,
#     files: list[DiscoveredCourseFile],
# ) -> Lecture:
#     resources = [
#         build_lecture_resource(file)
#         for file in files
#     ]

#     return Lecture(
#         lecture_id=lecture_key,
#         resources=resources
#         )


if __name__ == "__main__":
    from src.core.config import folder_env_vars
    from src.core.memory import app_session

    # from src.core.memory_lecture import LectureContext
    from src.core.logger import create_logger

    app_session.logger = create_logger(
        name="RF_LOG",
        # context.logger_name,  # "RF_LOG"),
        file_name="rf_log",
        # context.logger_f_name,  #  "rf_log")
    )

    input_folder = folder_env_vars.data_lectures / "lakbb/Gicht"

    build_lecture_course_from_folder(
        input_folder,
        # course_id=input_folder.parent.name,
        course_title="Gicht - Die Sache mit dem dicken Zeh",
    )

    # build_lecture_course_from_folder(
    # input_folder: Path,
    # *,
    # course_id: str,
    # course_title: str | None = None,
