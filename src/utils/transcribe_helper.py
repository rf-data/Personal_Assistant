## transcribe_helper.py
# import
from src.core.memory import AudioContext
from src.model_transcribe.provider_transcript import FasterWhisperProvider

def get_transcription_provider(context: AudioContext, logger):
    backend = context.cfg_transcribe.backend

    match backend:
        case "faster_whisper":
            return FasterWhisperProvider(
                settings=context.cfg_transcribe,
                logger=logger,
            )

        case "whisper_live":
            raise NotImplementedError(
                "WhisperLive provider is not implemented yet."
            )

        case "cloud_stt":
            raise NotImplementedError(
                "Cloud STT provider is not implemented yet."
            )

        case _:
            raise ValueError(
                f"Unsupported transcription backend: {backend}"
            )