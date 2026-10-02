## run_knowledge_consolidation.py
# import
from __future__ import annotations

import gc
from pathlib import Path

from src.core.config import folder_env_vars
from src.core.memory import app_session
from src.core.logger import create_logger
from src.core.memory_lecture import LectureContext

from src.model_knowledge.data_knowledge import (
    LectureKnowledgeDocument,
    TranscriptKnowledgeDocument,
)
from src.tools_knowledge.consolidate_knowledge import consolidate_knowledge
from src.tools_knowledge.semantic_knowledge import consolidate_semantic_knowledge

from src.utils.dict_helper import save_dict, load_dict
from src.utils.llm_helper import configure_marvin

# deterministic = consolidate_knowledge(
#     document=knowledge_document
# )

# semantic = consolidate_semantic_knowledge(
#     document=deterministic,
#     model_name=context.llm_model,
# )

# save_dict(
#     data=semantic.model_dump(
#         mode="json"
#     ),
#     path=output_path,
# )


def run_knowledge_consolidation():

    dict_name = "lecture_compile"
    dict_path = folder_env_vars.config_dir / f"context_{dict_name}.json"
    context = load_dict(
        path=dict_path,
        cls=LectureContext,
        # TranscriptDocument
    )

    # app_session.timestamp = datetime.today().strftime("%Y-%m-%d")
    app_session.logger = create_logger(
        name=context.logger_name, file_name=context.logger_f_name
    )

    configure_marvin(context)

    lecture_folder = (
        folder_env_vars.data_lectures
        / context.provider  # loviscach"
        / context.course_id  # "mathe_1"
        / "knowledge"
    )

    know_extracts = [f for f in lecture_folder.rglob("*_know_extract.json")]

    return process_course_knowledge(
        input_paths=know_extracts,
        output_folder=lecture_folder,
        model_name=context.cfg_knowledge.llm_model,
    )


def process_course_knowledge(
    input_paths: list[Path],
    output_folder: Path,
    model_name: str,
) -> None:

    n_files = len(input_paths)

    for idx, input_path in enumerate(
        input_paths,
        start=1,
    ):
        output_path = output_folder / input_path.name.replace(
            "_know_extract.json",
            "_know_consol.json",
        )

        # Resume:
        # already completed lectures are skipped
        if output_path.exists():
            app_session.logger.info(
                "[%d/%d] Already completed, skipping: %s",
                idx,
                n_files,
                input_path.name,
            )
            continue

        app_session.logger.info(
            "[%d/%d] Starting: %s",
            idx,
            n_files,
            input_path.name,
        )

        try:
            process_knowledge_file(
                input_path=input_path,
                output_path=output_path,
                model_name=model_name,
            )

        except KeyboardInterrupt:
            app_session.logger.warning("Run interrupted by user.")
            raise

        except Exception:
            app_session.logger.exception(
                "Knowledge consolidation failed for: %s",
                input_path,
            )

            # Continue with next lecture
            continue

        finally:
            # Avoid retaining objects from previous lectures
            gc.collect()


def process_knowledge_file(
    input_path: Path,
    output_path: Path,
    model_name: str,
) -> LectureKnowledgeDocument:

    app_session.logger.info(
        "Processing knowledge file: %s",
        input_path.name,
    )

    raw = load_dict(
        input_path,
        cls=TranscriptKnowledgeDocument,
    )

    consolidated = consolidate_knowledge(raw)

    result = consolidate_semantic_knowledge(
        document=consolidated,
        model_name=model_name,
    )

    save_dict(
        data=result.model_dump(mode="json"),
        path=output_path,
    )

    app_session.logger.info(
        "Finished: %s",
        output_path.name,
    )

    return result


if __name__ == "__main__":
    run_knowledge_consolidation()
