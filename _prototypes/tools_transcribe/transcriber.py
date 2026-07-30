## transcribe_video.py
# import

from pathlib import Path
from time import perf_counter

import numpy as np
from faster_whisper import WhisperModel
from tqdm import tqdm
from yt_dlp import YoutubeDL

from src.core.config import parsing_env_vars
from src.utils.dict_helper import save_dict

# from src.utils.general_helper import load_env_vars
from src.utils.text_file_helper import save_text_file

ALLOWED_TYPES = [".mp4", ".mkv", ".webm", ".mp3", ".wav", ".m4a"]


def download_audio(url: str, out_file: str):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_file,
        "noplaylist": True,
        "quiet": False,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

        return ydl.prepare_filename(info)


def get_audio_file(f_path: str = None, url: str = None) -> str:
    data_dir = parsing_env_vars.data_dir

    if f_path:
        return f_path

    if url:
        save_folder = Path(f"{data_dir}/temp/")
        save_path = (
            save_folder / "%(playlist_title)s/%(playlist_index)03d_%(title)s.%(ext)s"
        )
        return download_audio(url, str(save_path))

    raise ValueError("No file or url provided")


def transcribe_video(
    f_path: str = None, url: str = None, lang: str = "eng", model_size: str = "medium"
):
    # load env variables and config
    # load_env_vars()

    data_processed = parsing_env_vars.data_processed
    save_folder = f"{data_processed}/Mathe-Vorkurs 2013"

    f_name = "JLoviscach_YT_001_Grundrech_0_Division"
    info_path = Path(f"{save_folder}/{f_name}")

    audio_file = get_audio_file(f_path=f_path, url=url)

    model = WhisperModel(
        model_size,  # später: "large-v3"
        device="cpu",
        compute_type="int8",
        cpu_threads=6,  # os.cpu_count()
    )

    # print("=" * 50)
    # print("audio_file:", repr(audio_file))
    # print("type:", type(audio_file))
    # print("exists:", Path(audio_file).exists())
    # print("=" * 50)

    start_time = perf_counter()
    segments, info = model.transcribe(
        audio_file,
        language=lang,
        vad_filter=False,
    )

    info_meta = {
        "language": info.language,
        "language_probability": info.language_probability,
        "duration": info.duration,
        "duration_after_vad": info.duration_after_vad,
    }

    # print(f"Detected language '{info.language}' with probability {info.language_probability} %")
    # % (, ))

    # save_dict(data=info, path=info_path)
    # print("Info (type):", type(info))
    # print("INFO (vars):")   # , vars(info))
    # for key, value in vars(info).items():
    #     print(f"{key}: {value}")

    # print("INFO (content):\n", info)

    pbar = tqdm(total=info.duration, desc="Transcribing", unit="audio-sec")

    # info_dict["segments"]
    segs_all = []
    text_all = ""
    for idx, seg in enumerate(segments):
        pbar.update(seg.end - pbar.n)

        #         seg_text = f"""
        # # Segment {idx} [start: {seg.start:.2f} | end: {seg.end:.2f}]

        # {seg.text}

        # """
        text_all += f"{seg.text}\n"

        segs_all.append(
            {
                "seg_id": idx,
                "text": seg.text,
                "seg_start": seg.start,
                "seg_end": seg.end,
            }
        )
        # transcript += seg_text

        # print(, seg.end, seg.text)

    pbar.close()
    runtime = perf_counter() - start_time

    print(f"Audio duration : {info.duration:.1f} s")
    print(f"Runtime        : {runtime:.1f} s")
    print(f"Realtime factor: {runtime / info.duration:.2f}")
    print(f"Speed          : {info.duration / runtime:.2f}x")

    info_meta.update(
        {
            "duration": np.round(info.duration, 1),  # :.1f} s")
            "runtime": np.round(runtime, 1),
        }
    )
    #             # :.1f} s")
    #             "realtime_factor": np.round(runtime/info.duration, 2),      # :.2f}")
    # print(f"Speed          : {info.duration/runtime:.2f}x"

    info_dict = {"meta": info_meta, "segments": segs_all, "text": text_all}

    save_dict(info_dict, info_path)

    save_text_file(data=text_all, file_name=f_name, folder=save_folder)

    return


from openai import OpenAI

client = OpenAI()

audio_file = open("meeting.mp3", "rb")

transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)

print(transcript.text)

"""
from youtube_transcript_api import YouTubeTranscriptApi
video_id = "YOUR_VIDEO_ID"
transcript = YouTubeTranscriptApi.get_transcript(video_id)
text = "\n".join([t['text'] for t in transcript])
print(text[:500])  # preview first 500 chars
"""

'''
summary = client.responses.create(
    model="gpt-5",
    input=f"""
    Summarize meeting.

    Extract:

    - Action items
    - Decisions
    - Risks
    - Deadlines

    {transcript.text}
    """
)
'''

"""
tiny + vad_filter=False + cpu_threads=False + HF_TOKEN=False
Audio: 414.5s
Runtime: 451.0s
Speed: 0.92x realtime


"""

"""
Modell	    Relativgeschwindigkeit
tiny	    ~10-20x schneller
base	    ~5-10x schneller
small	    ~2-4x schneller
medium	    Referenz
large-v3	~2-4x langsamer
"""

if __name__ == "__main__":
    # url="https://www.youtube.com/watch?v=vJcHp9j8U_s&list=PL9txSunocNHiz9j7rR30QWjTVkVGGeTFV"
    # f_path="/home/robfra/0_Portfolio_Projekte/gmp_compliance/data/temp/audio.webm"

    url_list = [
        "https://www.youtube.com/watch?v=3TH4PsR70HA&list=PL9txSunocNHiz9j7rR30QWjTVkVGGeTFV&index=2",
        "https://www.youtube.com/watch?v=KeCd7fs7rtc&list=PL9txSunocNHiz9j7rR30QWjTVkVGGeTFV&index=3",
        "https://www.youtube.com/watch?v=Jkd128gXxHk&list=PL9txSunocNHiz9j7rR30QWjTVkVGGeTFV&index=4",
        "https://www.youtube.com/watch?v=EW7e-v9y2LU&list=PL9txSunocNHiz9j7rR30QWjTVkVGGeTFV&index=5",
    ]

    for idx, url in enumerate(url_list):
        print(f"Start transcribing file # {idx}")

        transcribe_video(
            # f_path=f_path,
            url=url,
            lang="de",
            model_size="small",
        )
        print()
