## process_lecture.py
# import
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlretrieve
from tiktoken import encoding_for_model

from src.core.config import folder_env_vars
from src.core.memory_transcribe import AudioContext
from src.core.memory_parsing import ParseContext
from src.core.config_parsing import ParseSettings, GeneralSettings
from src.core.memory import app_session
from src.utils.general_helper import make_doc_id_by_content
from src.model_parsing.pdf_extractor import PDFCleanExtractor
from src.model_parsing.feature_enricher import FeatureEnricher
from src.model_transcribe.data_transcribe import DownloadResult
from src.model_lecture.data_resources import (
    # LectureCourse,
    LectureResource,
    # LectureScript,
    LectureMedia,
    # LectureResourceType,
    ResourceAction,
    ResourceTask,
)
from src.model_transcribe.provider_transcript import get_transcription_provider
from src.tools_transcribe.process_subtitle import parse_subtitle, transcribe_files
from src.tools_parsing.parse_document import parse_document

# from src.tools_lecture.plan_lecture import (
#                                     get_resource_path,
#                                     get_required_actions
#                                     )
from src.utils.dict_helper import load_dict, load_yaml_config

# , save_dict
from src.utils.path_helper import ensure_dir, shorten_path
from src.tools_transcribe.process_url import acquire_transcript_source
# audio_transcription


ALLOWED_TEXT_TYPES = ("pdf", "txt", "md", "docx")


def execute_task(task: ResourceTask, course_root: Path) -> None:
    resource = task.resource

    # while True:
    #    actionable_tasks = [action for action in resource_task.actions]

    # if not actionable_tasks:
    #     break

    for action in task.actions:
        match resource.resource_type:
            case (
                "video"
                # | LectureResourceType.VIDEO
            ):
                execute_video_action(
                    resource=resource, action=action, course_root=course_root
                )

            case (
                # LectureResourceType.SCRIPT
                # | LectureResourceType.EXAM
                # | LectureResourceType.MATERIAL
                "script" | "exam" | "material"
            ):
                execute_document_action(
                    resource=resource, action=action, course_root=course_root
                )

            case (
                "notebook"
                # | LectureResourceType.NOTEBOOK
            ):
                print("not yet implemented")

            case _:
                app_session.logger.warning(
                    "Unsupported resource type '%s' for '%s'.",
                    resource.resource_type,
                    resource.title,
                )
        # file_index = build_file_index(folder_path)

    return


# uv run docling convert \
#     /home/robfra/0_Portfolio_Projekte/gmp_compliance/data/JLoviscach_Mathe_1/01_Ueberblick_Vektorrechnung.pdf \
#     --to md \
#     --to json \
#     --no-ocr \
#     --enrich-formula \
#     --output ./docling_test

# def execute_document_action(
#     resource: LectureResource,
#     action: ResourceAction,
# ) -> None:

#     match action:
#         case ResourceAction.DOWNLOAD:
#             download_document(resource)

#         case ResourceAction.PARSE_DOCUMENT:
#             parse_document(resource)


def execute_document_action(
    resource: LectureResource, action: ResourceAction, course_root: Path
) -> None:

    match action:
        case ResourceAction.DOWNLOAD:
            download_document(resource, course_root)

        case ResourceAction.PARSE_DOCUMENT:
            if resource.local_path is None:
                raise ValueError(f"No local_path for resource: {resource.title}")

            parse_context = build_document_parse_context(
                resource=resource, course_root=course_root
            )

            # parse_document(resource, course_root)
            parse_document(resource.local_path, parse_context=parse_context)

        case _:
            app_session.logger.warning(
                "Unsupported document action '%s' for '%s'.",
                action,
                resource.title,
            )

    return None


def build_document_parse_context(resource, course_root) -> ParseContext:

    if resource.local_path is None:
        raise ValueError(f"Resource has no local_path: {resource.title}")

    parse_settings = load_yaml_config(
        path=(folder_env_vars.config_dir / "cfg_parsing"), cls=ParseSettings
    )
    general_settings = load_yaml_config(
        path=(folder_env_vars.config_dir / "cfg_general"), cls=GeneralSettings
    )

    file_path = Path(resource.local_path)

    if not file_path.exists():
        raise FileNotFoundError(file_path)

    suffix = file_path.suffix.lower().removeprefix(".")

    if suffix not in ALLOWED_TEXT_TYPES:
        raise ValueError(f"Unsupported document type: {suffix}")

    save_folder = Path(course_root) / "parsed"

    ensure_dir(save_folder)

    context = ParseContext(
        parse_settings=parse_settings,
        general_settings=general_settings,
        local_path=resource.local_path,
        save_folder=save_folder,
        save_name=file_path.stem,
        text_type=suffix,
        doc_id=make_doc_id_by_content(str(file_path)),
        doc_kind="lecture",
        run_id=file_path.stem,
        # timestamp=app_session.timestamp,
    )

    app_session.parse_context = context
    context.encoder = encoding_for_model(parse_settings.llm_model)

    return context


# ParseContext(
#         parse_settings=ParseSettings(
#                             file_name=resource.title
#                             ),
#         save_path=resource.local_path,
#         save_folder=course_root
#     )


def execute_video_action(
    resource: LectureMedia, action: ResourceAction, course_root: Path
) -> list[Path]:

    audio_context = load_dict(
        path=(folder_env_vars.config_dir / "cfg_lecture_transcribe"), cls=AudioContext
    )

    audio_context.cfg_download.cookie_file = folder_env_vars.yt_cookies
    audio_context.save_folder = course_root
    audio_context.f_name = resource.title

    # (
    #                         source="",
    #                         local_path="",
    #                         cfg_transcribe={
    #                             "model_size":""
    #                         }
    # )

    match action:
        case ResourceAction.DOWNLOAD:
            audio_context.source = "url"
            audio_context.url = resource.youtube_url or resource.source_url

            # transcript_paths = audio_transcription(audio_context)
            source_result = acquire_transcript_source(audio_context)

            return source_result.paths

        case ResourceAction.TRANSCRIBE:
            audio_context.source = "local"
            # audio_context.local_path = []

            source_result = DownloadResult(
                success=True, transcript_source="whisper", paths=[resource.local_path]
            )

            provider = get_transcription_provider(
                context=audio_context,
                logger=app_session.logger,
            )

            transcript_paths = transcribe_files(source_result, provider, audio_context)

        case ResourceAction.PARSE_SUBTITLE:
            # audio_context["source"] = "local"
            # audio_context["local_path"] = [resource.local_path]

            transcript_paths = parse_subtitle(
                f_path=(course_root / f"subtitles/{resource.title}.de.vtt")
            )

        # case ResourceAction.PARSE_DOCUMENT:
        #     ...

        case _:
            raise ValueError(f"Unsupported video action: {action}")

    return transcript_paths


def download_document(resource: LectureResource, course_root: Path) -> Path:

    if resource.local_path is not None:
        path = Path(resource.local_path)

        if path.exists():
            app_session.logger.info(
                "Document already exists: %s",
                path,
            )
            return path

    suffix = Path(urlparse(resource.source_url).path).suffix.lower()

    if not suffix:
        suffix = ".pdf"

    target_dir = course_root / "documents"

    file_name = resource.title or resource.lecture_no or "document"

    target_path = target_dir / f"{file_name}{suffix}"
    ensure_dir(target_path)

    app_session.logger.info(
        "Downloading document '%s' -> %s",
        resource.source_url,
        shorten_path(target_path, 4),
    )

    urlretrieve(
        resource.source_url,
        target_path,
    )

    return target_path
