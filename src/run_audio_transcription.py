## run_audio_transcription.py
# imports                             
from pathlib import Path
from datetime import datetime
from yt_dlp.utils import DownloadError

from src.core.config import parsing_env_vars
from src.core.memory_transcribe import AudioContext
from src.core.memory import app_session
from src.core.logger import create_logger
from src.model_transcribe.provider_transcript import get_transcription_provider
from src.model_transcribe.data_transcribe import (
                                            DownloadResult,
                                            TranscriptProvenance,
                                            TranscriptSource
                                            )
from src.model_knowledge.data_resources import (
                                            # LectureVideo,
                                            LectureResource_old
                                            )
from src.tools_transcribe.process_url import acquire_transcript_source    
from src.tools_transcribe.extract_subtitle import parse_subtitle 


from src.utils.dict_helper import save_dict, load_dict
from src.utils.path_helper import shorten_path


# ! TODO: change LectureResource_old -> new data models

def run_audio_transcription():
    
    dict_name = input("Enter name of context_file (no suffix): ")
    dict_path = parsing_env_vars.config_dir / f"context_{dict_name}.json"
    context = load_dict(dict_path, cls=AudioContext)

    app_session.timestamp = datetime.today().strftime("%Y-%m-%d")
    app_session.logger = create_logger(
                    name=context.logger_name,  
                    file_name=context.logger_f_name  
                )
    
    cache_dir = parsing_env_vars.cache_dir
    memory_f_path = Path(cache_dir) / f"videos_processed/{context.memory_f_name}" 
   
    if memory_f_path.exists():
        memory_file = load_dict(memory_f_path)

        video_list = (
                memory_file
                if isinstance(memory_file, dict)
                else {}
                )
        
    else: 
        video_list: dict[str, dict] = {}

    video_list_clean = {
                video_id
                for video_id, meta in video_list.items()
                if meta.get("result") == "success"
                }


    app_session.logger.info(
            "Found %s already processed videos in memory, %s successful",
            len(video_list),
            len(video_list_clean)
                        )
    
    failed_downloads: list[dict[str, str]] = []

    for f_path in context.lecture_files:
        lecture = load_dict(
                path=f"{parsing_env_vars.data_html}/{f_path}", 
                cls=LectureResource_old
                )
        videos = lecture.videos     #", [])

        n_videos = len(videos)
        app_session.logger.info(
            "[%s] Videos: total=%s, foundation=%s, supplement=%s, \n"
            "with_url=%s, foundation_with_url=%s, supplement_with_url=%s, \n"
            "already_processed=%s",
            shorten_path(f_path, 1),
            n_videos,
            sum(v.kind == "foundation" for v in videos),
            sum(v.kind == "supplement" for v in videos),
            sum(bool(v.youtube_url) for v in videos),
            sum(
                v.kind == "foundation" and bool(v.youtube_url)
                for v in videos
            ),
            sum(
                v.kind == "supplement" and bool(v.youtube_url)
                for v in videos
                ),
            len(video_list_clean)
        )

        playlist_name = "_".join(Path(f_path).stem.split("_")[:-1])
        for idx, vid in enumerate(videos):
            url = vid.youtube_url
            vid.title = vid.title if not " " in vid.title else "_".join(vid.title.split())

            if not url:
                app_session.logger.warning(
                    "[File #%s] Foundation video has no YouTube URL: %s",
                    idx,
                    vid.title,
                )
                continue

            if vid.kind not in context.kind:
                continue

            # Bereits erfolgreich verarbeitet
            video_id = vid.youtube_id or url

            if video_id in video_list_clean:
                app_session.logger.info(
                            "[File #%s] Already processed. Skip '%s'",
                            idx,
                            vid.title
                            )
                continue

            context.f_name=f"{vid.lecture_no or 'noLecID'}__{vid.topic or 'noTop'}__{vid.youtube_id or 'noYTID'}",
            context.url=url
            context.cfg_download.playlist_name=playlist_name                  
            context.cfg_download.cookie_file=parsing_env_vars.yt_cookies

            app_session.logger.info(
                    "[File #%s / %s] Start processing '%s'",   
                    idx,
                    n_videos,
                    vid.title,
                    )
         
            result = "success" 

            try:
                transcript = audio_transcription(context)
                if transcript is None:
                    raise RuntimeError(
                        f"No transcript generated for {vid.title}"
                        )

            except DownloadError as exc: 
                result = type(exc).__name__ 

                failed_downloads.append(
                                {
                                "url": url,  
                                "error": str(exc)
                                }
                            )
                
            except Exception as e:
                app_session.logger.exception(
                                "[File #%s] Processing failed: '%s'",
                                idx,
                                vid.title
                                )
                result = type(e).__name__   

            # Nur nach erfolgreichem Download + Transkription
            video_list[str(video_id)] = {
                                "title": vid.title,
                                "result": result,
                                "source": (
                                        transcript.provenance.transcript_source
                                        if transcript is not None
                                        else None
                                        ),
                                "strategy": (
                                    transcript.provenance.download_strategy
                                    if transcript is not None
                                    else None
                                    )
                                }

            save_dict(
                data=video_list,
                path=memory_f_path
                    )

            if result == "success":
                app_session.logger.info(
                        "[File #%s] Successfully processed '%s'",
                        idx,
                        vid.title,
                        )
            else:
                app_session.logger.warning(
                            "[File #%s] Processing failed for '%s': %s",
                            idx,
                            vid.title,
                            result,
                            )

    now = datetime.now().strftime("%Y-%m-%d_%hh:%MM")
    failure_path = Path(cache_dir) / f"videos_processed/{now}_failed_downloads.json"
    save_dict(data=failed_downloads, path=failure_path)


def add_transcript_provenance(
    transcript,
    source_result: DownloadResult,
    context: AudioContext,
    src_file: Path,
):
    transcript.provenance = TranscriptProvenance(
        transcript_source=source_result.transcript_source,
        download_strategy=source_result.strategy,
        source_url=context.url,
        source_file=str(src_file),
        language=source_result.language,
        media_format=source_result.media_format,
        transcription_provider=(
            "faster-whisper"
            if source_result.transcript_source
            == TranscriptSource.WHISPER
            else None
        ),
        transcription_model=(
            context.cfg_transcribe.model_size
            if source_result.transcript_source
            == TranscriptSource.WHISPER
            else None
        ),
    )

    return transcript


def audio_transcription(context: AudioContext):
    if app_session.logger is None: 
        app_session.timestamp = datetime.today().strftime("%Y-%m-%d")
        app_session.logger = create_logger(
                name="Audio_Transcript", 
                file_name=f"{app_session.timestamp}_audio_transcript"
            )
    
    source_result = acquire_transcript_source(context)
    if not source_result.success:
        app_session.logger.error(
                    "Transcript source acquisition failed: %s",
                    source_result.error,
                    )
        return None

    source_files = source_result.paths
    if not source_files or not any(src.exists() for src in source_files):
        app_session.logger.error("Source file download failed: %s", 
                                 context.url)
        return None
                    
    n_files = len(source_files)
    
    for idx, src_file in enumerate(source_files):

        app_session.logger.info(
                "[File %s / %s] Start processing source file.",
                idx+1,
                n_files
                )

        match source_result.transcript_source:
            case (
                TranscriptSource.MANUAL_SUBTITLE
                | TranscriptSource.AUTO_SUBTITLE
                ):
                transcript = parse_subtitle(src_file)
        
            case TranscriptSource.WHISPER:
                provider = get_transcription_provider(
                                                context=context,
                                                logger=app_session.logger,
                                                )
                transcript = provider.transcribe(src_file)  

            case _:
                raise RuntimeError(
                    "Unsupported transcript source: "
                    f"{source_result.transcript_source}"
                )

        if transcript is None:
            raise RuntimeError(
                f"No transcript generated for '{src_file}'"
            )

        transcript = add_transcript_provenance(
                                    transcript=transcript,
                                    source_result=source_result,
                                    context=context,
                                    src_file=src_file,
                                    )

        
        trans_dict = transcript.model_dump(mode="json")

        save_dict(
            data=trans_dict,  
            path=Path(f"{src_file.parent}/transcripts/{src_file.name}_trans") 
            )
        
    return transcript



if __name__ == "__main__":
    run_audio_transcription()



# def build_media_filename(
#             lecture_no: str | None,
#             youtube_id: str | None,
#             topic: str,
#             ) -> str:

#     safe_topic = "_".join(topic.replace(",", " ").split())

#     parts = [
#         lecture_no or "NA",
#         safe_topic,
#         youtube_id or "NOID",
#     ]

#     return "_".join(parts)