## run_audio_transcription.py
# imports
from pathlib import Path
from datetime import datetime
from yt_dlp.utils import DownloadError

from src.core.config import TranscribeSettings, DownloadSettings, parsing_env_vars
from src.core.memory_transcribe import AudioContext
from src.core.memory import app_session
from src.core.logger import create_logger
from src.model_transcribe.provider_transcript import get_transcription_provider
from src.model_transcribe.data_transcribe import TranscriptSource
from src.model_knowledge.data_knowledge import (
                                            LectureVideo,
                                            LectureResources
                                            )
from src.tools_transcribe.process_url import acquire_transcript_source    # get_audio_file
from src.tools_transcribe.extract_subtitle import parse_subtitle    # get_audio_file


from src.utils.dict_helper import save_dict, load_dict
from src.utils.path_helper import shorten_path


# ave_dict, load_dict

# utils.transcribe_helper import 
# ools_transcribe._dev_transcriber import transcribe_video


# yt-dlp --version
# yt-dlp -v -f "bestaudio/best" "https://www.youtube.com/watch?v=mxVDSdqJIZg"
# https://www.youtube.com/watch?v=1zudtkaEkHw"


# TROUBLESHOOTING:
# (1) 
# 
# (2) yt-dlp -v -F "VIDEO_URL"      # -> other formats available!?
# 
# (3) yt-dlp -f "bestaudio/best" "VIDEO_URL"
#     or yt-dlp -f 140 "VIDEO_URL"                 # -> other audio_quality!? 
# 
# (4) yt-dlp --cookies-from-browser chrome "VIDEO_URL"  # -> use cookies

def run_audio_transcription():
    # from src.core.config import parsing_env_vars
    
    app_session.timestamp = datetime.today().strftime("%Y-%m-%d")
    app_session.logger = create_logger(
                    name="Loviscach", 
                    file_name=f"{app_session.timestamp}_Loviscach"
                )
    # app_session.logger = create_logger()
    html_dir = parsing_env_vars.data_html
    cache_dir = parsing_env_vars.cache_dir
    memory_f_path = Path(cache_dir) / f"videos_processed/JLoviscach_Mathe.json"


    if memory_f_path.exists():
        memory_file = load_dict(memory_f_path)
        # file = memory_file.get("Mathe_1")

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
    
        # f_path = Path(html_dir) / "test_2026-08-13_JLoviscach_Mathe_1/JLoviscach_Mathe_1_info.json"
        # elements = ["link_node", "link"]
        # run_loviscach_url_update(f_path, elements)
    
    files = [
        # "/home/robfra/0_Portfolio_Projekte/gmp_compliance/data/JLoviscach_Mathe_2_lectures.json",
        f"{html_dir}/test_2026-08-13_JLoviscach_Mathe_1/JLoviscach_Mathe_1_lectures.json"
        ]
    # Path(html_dir) / "test_2026-08-15_JLoviscach_Mathe_2/JLoviscach_Mathe_2_lectures.json"
    # "test_2026-08-13_JLoviscach_Mathe_1/JLoviscach_Mathe_1_lectures.json"
    # "test_2026-08-15_JLoviscach_Mathe_2/JLoviscach_Mathe_2_lectures.json"
    
    failed_downloads: list[dict[str, str]] = []

    for f_path in files: 
        lecture = load_dict(f_path, cls=LectureResources)
        videos = lecture.videos     #", [])
        
        app_session.logger.info(
            "[%s] Videos: total=%s, foundation=%s, with_url=%s, foundation_with_url=%s, already_processed=%s",
            shorten_path(f_path, 1),
            len(videos),
            sum(v.kind == "foundation" for v in videos),
            sum(bool(v.youtube_url) for v in videos),
            sum(
                v.kind == "foundation" and bool(v.youtube_url)
                for v in videos
            ),
            len(video_list_clean)
        )
        
        for idx, vid in enumerate(videos):
            url = vid.youtube_url
            vid.title = vid.title if not " " in vid.title else "_".join(vid.title.split())

            # if idx > 1 
            if not url:
                app_session.logger.warning(
                    "[File #%s] Foundation video has no YouTube URL: %s",
                    idx,
                    vid.title,
                )
                continue

            if vid.kind != "foundation":
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

            context = AudioContext(
                            source="youtube",
                            f_name=f"{vid.lecture_no}__{vid.topic}__{vid.youtube_id}",
                            # build_media_filename(
                                                    # vid.lecture_no, 
                                                    # vid.youtube_id,
                                                    # vid.topic
                                                    # ),
                            url=url,    # "https://www.youtube.com/playlist?list=PL9txSunocNHiz9j7rR30QWjTVkVGGeTFV",
                            # "https://www.youtube.com/watch?v=3TH4PsR70HA&list=PL9txSunocNHiz9j7rR30QWjTVkVGGeTFV&index=2",
                            cfg_transcribe=TranscribeSettings(
                                                        model_size="small",
                                                        device="cpu",
                                                        compute_type="int8",
                                                        language="de",
                                                        ),
                            cfg_download=DownloadSettings(
                                                    no_playlist=True,
                                                    playlist_name="Mathe_1_JLoviscach",
                                                    # playlist_items="68-89",
                                                    quiet=False,
                                                    format="bestaudio[ext=m4a]/bestaudio/best"
                                                    )
                            )
            app_session.logger.info(
                    "[File #%s] Start transcribing '%s'",
                    idx,
                    vid.title,
                    )
            
            # else:
            #     continue 
            #     #     raise ValueError("Provided invalid response")
                    
            # app_session.logger.info(
            #                         "[File #%s] Start transcribing '%s'",
            #                         idx,
            #                         url
            #                         )

            result = "success" 

            try:
                transcript = audio_transcription(context)
                if transcript is None:
                    raise RuntimeError(
                        f"No transcript generated for {vid.title}"
                        )

            except DownloadError as exc: 
                result = type(e).__name__ 

                failed_downloads.append(
                                {
                                "url": url,  # vid.url,
                                "error": str(exc)
                                }
                            )
                
            except Exception as e:
                app_session.logger.exception(
                                "[File #%s] Processing failed: '%s'",
                                idx,
                                vid.title
                                )
                result = type(e).__name__    # "error"
                # continue

            # Nur nach erfolgreichem Download + Transkription
            video_list[str(video_id)] = {
                                "title": vid.title,
                                "result": result,
                                }

            # 01.02.1_Modell_und_Wirklichkeit
            # T0AcnvKzTp

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
            # return None


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


def audio_transcription(context: AudioContext):
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

    
    # provider = get_transcription_provider(
    #                             context=context,
    #                             logger=app_session.logger,
    #                             )
    provider = get_transcription_provider(
                                    context=context,
                                    logger=app_session.logger,
                                    )
                        
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
        
            # case :
            #     transcript = parse_subtitle(src_file)   
                # source_result.paths[0])
        
            case TranscriptSource.WHISPER:
                transcript = provider.transcribe(src_file)  
                # source_result.paths[0])

            case _:
                raise RuntimeError(
                    "Unsupported transcript source: "
                    f"{source_result.transcript_source}"
                )

        if transcript is None:
            raise RuntimeError(
                f"No transcript generated for '{src_file}'"
            )
        # transcript = provider.transcribe(source=audio_file) # , context)

        trans_dict = transcript.model_dump(mode="json")
        # print(trans_dict)

        
        # save_path = f"{src_file.parent}/{context.f_name or 'tba'}"
                # (
                # Path(parsing_env_vars.data_transcripts)
                # FIXME: change to 'data_audio'
                # / (context.f_name or "tba")
                # or str(audio_file).lsplit('.')[0]}"      
                # context.f_name
                # FIXME: change to audio_file.rsplit('.')[0] 
                # )

        # LectureVideo(
        #                         title=safe_title,
        #                         lecture_no=lecture_no,
        #                         topic=topic,
        #                         section=None,
        #                         kind=infer_video_kind(lecture_no),
        #                         source_url=href,
        #                         youtube_url=youtube_url,
        #                         youtube_id=youtube_id,
        #                         duration=None,

        # save_dict(
        #         data=trans_dict, 
        #         path=Path(save_path)
        #         )


        save_dict(
            data=trans_dict,    # trans_doc.model_dump(mode="json"),
            path=Path(f"{src_file.parent}/transcripts/{src_file.stem}_trans") 
            )
        
    return transcript



if __name__ == "__main__":
    run_audio_transcription()

    # print(transcript.text[:100], "\n")
    