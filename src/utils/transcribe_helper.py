## transcribe_helper.py
# import
from src.core.memory import AudioContext
from src.model_transcribe.provider_transcript import FasterWhisperProvider


def get_audio_info(f_path: str):

    cmd = ["ffprobe", "-hide_banner", f_path]

    cmd_sound = ["ffmpeg", f"-i {f_path}", "-af", "volumedetect", "-f null -"]

    return


# Pflanzliche_GIT_AM_000_p2
# ffmpeg \
#   -ss 900 \
#   -i /mnt/chromeos/GoogleDrive/MyDrive/1_Projekte_Datensätze/1_Projekte/00_GMP_Compliance/data/audio/webinar_pflanzen_git_am/Pflanzliche_GIT_AM_000.wav \
#   -c:a pcm_s16le \
#   data/Pflanzliche_GIT_AM_000_p2.wav

# ffmpeg \
#   -i /mnt/chromeos/GoogleDrive/MyDrive/1_Projekte_Datensätze/1_Projekte/00_GMP_Compliance/data/audio/webinar_pflanzen_git_am/Pflanzliche_GIT_AM_000.wav \
#   -t 900 \
#   -c:a pcm_s16le \
#   /home/robfra/0_Portfolio_Projekte/gmp_compliance/data/test_900s.wav

# def get_transcription_provider(context: AudioContext, logger):
#     backend = context.cfg_transcribe.backend

#     match backend:
#         case "faster_whisper":
#             return FasterWhisperProvider(
#                 settings=context.cfg_transcribe,
#                 logger=logger,
#             )

#         case "whisper_live":
#             raise NotImplementedError("WhisperLive provider is not implemented yet.")

#         case "cloud_stt":
#             raise NotImplementedError("Cloud STT provider is not implemented yet.")

#         case _:
#             raise ValueError(f"Unsupported transcription backend: {backend}")
