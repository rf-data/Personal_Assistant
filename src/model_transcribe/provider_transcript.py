## provider_transcript.py
# import
from pathlib import Path
from time import perf_counter

from faster_whisper import WhisperModel
from tqdm import tqdm

from src.core.config import agentic_env_vars
from src.core.memory_transcribe import AudioContext

# from src.core.memory import app_session
from src.model_transcribe.data_transcribe import (
    TranscriptDocument,
    TranscriptSegment,
)
from src.utils.path_helper import shorten_path


class FasterWhisperProvider:
    def __init__(self, settings, logger):
        self.settings = settings
        self.logger = logger

        self.logger.info(
            "Loading FasterWhisper model: "
            "model=%s device=%s compute_type=%s threads=%s",
            settings.model_size,
            settings.device,
            settings.compute_type,
            settings.cpu_threads,
        )

        start = perf_counter()

        self.model = WhisperModel(
            settings.model_size,
            device=settings.device,
            compute_type=settings.compute_type,
            cpu_threads=settings.cpu_threads,
            use_auth_token=agentic_env_vars.hf_api_key or False,
        )

        self.logger.info(
            "FasterWhisper model loaded in %.1fs",
            perf_counter() - start,
        )

    def transcribe(
        self,
        source: Path,
        language: str | None = None,
    ) -> TranscriptDocument:

        if not source.exists():
            raise FileNotFoundError(source)

        self.logger.info("Transcribing: %s", shorten_path(source))

        start_time = perf_counter()

        segments, info = self.model.transcribe(
            str(source),
            language=language or self.settings.language,
            vad_filter=self.settings.vad_filter,
        )

        result_segments: list[TranscriptSegment] = []
        text_parts: list[str] = []

        pbar = tqdm(
            total=info.duration,
            desc="Transcribing",
            unit="audio-sec",
        )

        for idx, segment in enumerate(segments):
            pbar.update(max(0, segment.end - pbar.n))

            text = segment.text.strip()

            result_segments.append(
                TranscriptSegment(
                    seg_id=idx,
                    start=segment.start,
                    end=segment.end,
                    text=text,
                )
            )

            if text:
                text_parts.append(text)

        pbar.close()

        runtime = perf_counter() - start_time

        realtime_factor = runtime / info.duration if info.duration else None

        self.logger.info(
            "Transcription finished: duration=%.1fs runtime=%.1fs RTF=%s",
            info.duration,
            runtime,
            (f"{realtime_factor:.2f}" if realtime_factor is not None else "n/a"),
        )

        return TranscriptDocument(
            source=str(source),
            language=info.language,
            language_probability=info.language_probability,
            duration=info.duration,
            duration_after_vad=info.duration_after_vad,
            runtime=runtime,
            realtime_factor=realtime_factor,
            segments=result_segments,
            text="\n".join(text_parts),
        )


# class WhisperLiveProvider:
#     ...
# class OpenAITranscriptionProvider:
#     ...


def get_transcription_provider(context: AudioContext, logger):
    backend = context.cfg_transcribe.backend

    match backend:
        case "faster_whisper":
            return FasterWhisperProvider(
                settings=context.cfg_transcribe,
                logger=logger,
            )

        case "whisper_live":
            raise NotImplementedError("WhisperLive provider is not implemented yet.")

        case "cloud_stt":
            raise NotImplementedError("Cloud STT provider is not implemented yet.")

        case _:
            raise ValueError(f"Unsupported transcription backend: {backend}")
