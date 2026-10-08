## run_lecture_preparation.py
# imports

from pathlib import Path
from datetime import datetime

from src.core.config import folder_env_vars
from src.core.logger import create_logger
from src.core.memory import app_session
from src.core.memory_lecture import LectureContext

from src.model_parsing.base_classes_parsing import RawDocument
from src.model_lecture.data_resources import (
    # LectureResource,
    LectureScript,
    LectureMedia,
    # RawLectureBlock
)
from src.tools_lecture.prepare_lecture import (
    # assign_video_blocks_by_order,
    classify_links,
    deduplicate_scripts,
    deduplicate_videos,
    enrich_resource_metadata,
    # enrich_urls,
    # extract_scripts,
    filter_html_elements,
    # lecture_block_extraction,
    # resolve_video_url,
    validate_lecture_resources,
)
from src.tools_lecture.prepare_loviscach import (
    assign_video_blocks_by_order,
    enrich_urls,
    extract_scripts,
    extract_media_id,
    lecture_block_extraction,
    resolve_video_url,
)
from src.utils.dict_helper import load_dict, save_dict


# ! TODO:
# Info_2_python lieferte dagegen:
#
# n_videos: 0
# n_scripts: 0
# n_material: 0
# n_other: 0
#
# obwohl der HTML-Parser Content gefunden hatte.
#
################################################
#
# ? NEXT_COURSES
# (1) Harvard CS50x
# --> "https://cs50.harvard.edu/x/"
#
# (2) Harvard CS50 Python
# --> "https://cs50.harvard.edu/python/"
#
# (3) Harvard CS50 SQL
# --> "https://cs50.harvard.edu/sql/"
#
# (4) Harvard CS50 AI + Harvard CS50 Professional Certificate AI
# --> "https://cs50.harvard.edu/ai/"

# ! TODO: DataModel MIT_Course
# (1): 6.1200J Mathematics for Computer Science (Spring 2024)
# -> url="https://ocw.mit.edu/courses/6-1200j-mathematics-for-computer-science-spring-2024"
#
# (2): 18.01SC Single Variable Calculus | Fall 2010
# -> "https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/"
#
# (3): [01/26/2027 -> 05/16/2027] Machine Learning with Python: from Linear Models to Deep Learning- 6.86x
# --> https://learn.mit.edu/courses/course-v1:MITxT+6.86x
#
# (4): [09/01/2026 -> 12/24/2026] Probability - The Science of Uncertainty and Data - 6.431x
# --> "https://learn.mit.edu/courses/course-v1:MITxT+6.431x"
#
# (5): [09/01/2026 -> 12/22/2026] Fundamentals of Statistics - 18.6501x
# --> "https://learn.mit.edu/courses/course-v1:MITxT+18.6501x"
#
# (6): [01/19/027 -> 05/17/2027] Data Analysis: Statistical Modeling and Computation in Applications
# --> "https://learn.mit.edu/courses/course-v1:MITxT+6.419x"
#
# (7): Capstone Exam in Statistics and Data Science - DS-CFx
# -> https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/

# Course
# ├── metadata
# │   ├── institution
# │   ├── course_number
# │   ├── title
# │   ├── semester
# │   ├── instructors
# │   ├── department
# │   ├── level
# │   └── prerequisites
# │
# ├── syllabus
# ├── calendar
# │
# ├── lectures[]
# │   ├── lecture_no
# │   ├── title
# │   ├── topics
# │   ├── video
# │   ├── notes
# │   └── readings
# │
# ├── assignments[]
# ├── exams[]
# └── other_resources[]
#
# 18.01SC Single Variable Calculus
# │
# ├── 1. Differentiation
# │   ├── Part A
# │   ├── Part B
# │   └── Exam 1
# │
# ├── 2. Applications of Differentiation
# ├── 3. Definite Integral and Applications
# ├── 4. Techniques of Integration
# └── 5. Exploring the Infinite
#     │
#     └── Sessions
#          ├── Lecture Video
#          ├── Course Notes
#          ├── Worked Examples
#          └── Problems


def run_lecture_preparation() -> None:

    dict_name = input("Enter name of context_file (no suffix): ")
    context_path = folder_env_vars.config_dir / f"context_{dict_name}.json"
    context = load_dict(context_path, LectureContext)

    app_session.timestamp = datetime.today().strftime("%Y-%m-%d")
    app_session.logger = create_logger(
        name=context.logger_name,
        # , "RF_LOG"),
        file_name=context.logger_f_name,
        # ", "rf_log")
    )

    info_paths = context.info_paths
    elements = context.extract_elements

    app_session.logger.info(
        """
Preparing lecture compilation for %s course(s)
Filtering %s elements: %s
""",
        len(info_paths),
        len(elements),
        elements,
    )

    for i_path in info_paths:
        lecture_preparation(Path(i_path), elements)

    return None


def lecture_preparation(f_path: Path, elements: list[str]) -> dict[str, list]:
    info_dict = load_dict(
        f_path,
        RawDocument,
    )
    lecture_blocks = lecture_block_extraction(info_dict)

    all_videos: list[LectureMedia] = []
    all_scripts: list[LectureScript] = []

    all_materials = []
    all_other = []

    for block in lecture_blocks:
        # block_id = block["block_id"]
        block_node = block["node"]

        links = filter_html_elements(
            block_node,
            elements,
        )

        links = classify_links(links)

        videos = enrich_urls(links["video"])

        scripts = extract_scripts(links["script"])

        scripts = deduplicate_scripts(scripts)

        for video in videos:
            # video.lecture_blocks = [block_id]

            if video.media_url:
                continue

            resolved_url = resolve_video_url(video.source_url)

            if resolved_url:
                video.media_url = resolved_url
                video.media_id = extract_media_id(resolved_url)

        all_videos.extend(videos)
        all_scripts.extend(scripts)

        all_materials.extend(links["material"].values())

        all_other.extend(links["other"].values())

    all_videos = assign_video_blocks_by_order(all_videos)

    all_videos = deduplicate_videos(all_videos)

    all_videos = [enrich_resource_metadata(video) for video in all_videos]

    all_scripts = deduplicate_scripts(all_scripts)

    all_scripts = [enrich_resource_metadata(script) for script in all_scripts]

    all_materials = [enrich_resource_metadata(material) for material in all_materials]

    # exams = [
    #     enrich_resource_metadata(exam)
    #     for exam in exams
    #     ]

    f_name = "_".join(f_path.stem.split("_")[:-1])

    save_path = f_path.with_stem(f"{f_name}_lectures_new")

    resource_data = {
        "videos": [vid.model_dump(mode="json") for vid in all_videos],
        "scripts": [script.model_dump(mode="json") for script in all_scripts],
        "material": all_materials,
        # [mat.model_dump(mode="json") for mat in all_material],
        "other_links": all_other,
        # [other.model_dump(mode="json") for other in all_other],
    }

    resource_data.update({"report": validate_lecture_resources(resource_data)})

    save_dict(data=resource_data, path=save_path)

    return resource_data


if __name__ == "__main__":
    run_lecture_preparation()
