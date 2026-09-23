## record_audio.py
# import
from pathlib import Path
import signal
from datetime import datetime
import subprocess

from src.core.config import folder_env_vars
from src.core.memory_transcribe import AudioContext
from src.core.memory import app_session
from src.core.logger import create_logger

from src.utils.dict_helper import load_dict  # save_dict,
from src.utils.path_helper import ensure_dir


"""
PROCESS FLOW
detect_monitor_source()
        ↓
record_system_audio()
        ↓
prepare_whisper_audio()
"""


def run_audio_recording():

    dict_name = "audio_record"
    # input("Enter name of context_file (no suffix): ")
    dict_path = folder_env_vars.config_dir / f"context_{dict_name}"
    context = load_dict(dict_path, cls=AudioContext)

    app_session.timestamp = datetime.today().strftime("%Y-%m-%d")
    app_session.logger = create_logger(
        name=context.logger_name, file_name=context.logger_f_name
    )

    return audio_recording(context)


def detect_monitor_source() -> str:

    result = subprocess.run(
        ["ffmpeg", "-sources", "pulse"],
        capture_output=True,
        text=True,
        check=True,
    )

    # ffmpeg schreibt solche Informationen teilweise nach stderr
    output = result.stdout + "\n" + result.stderr

    monitor_sources = []

    for line in output.splitlines():
        line = line.strip()

        if ".monitor" not in line:
            continue

        # z. B.
        # "* alsa-sink.monitor [Monitor of PCM Sink] (none)"
        source = line.lstrip("* ").split()[0]
        monitor_sources.append(source)

    if not monitor_sources:
        raise RuntimeError("No PulseAudio monitor source detected.")

    if len(monitor_sources) > 1:
        raise RuntimeError(f"Multiple monitor sources detected: {monitor_sources}")

    return monitor_sources[0]


def start_system_audio_recording(
    output_path: Path, monitor_source: str, segment_time: int
) -> subprocess.Popen:
    """
    Start recording system audio via ffmpeg.

    Returns the running ffmpeg process.
    """

    ensure_dir(output_path)
    # output_path = Path(output_path)
    # output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "pulse",
        "-i",
        monitor_source,
        "-c:a",
        "pcm_s16le",
        "-f",
        "segment",
        "-segment_time",
        str(segment_time),
        "-reset_timestamps",
        "1",
        str(output_path),
    ]

    try:
        process = subprocess.Popen(cmd, stdin=subprocess.DEVNULL)

    except FileNotFoundError as exc:
        raise RuntimeError("ffmpeg is not installed or not available on PATH.") from exc

    return process


def stop_system_audio_recording(
    process: subprocess.Popen,
    timeout: float = 10.0,
) -> None:
    """
    Stop a running ffmpeg recording gracefully.
    """

    if process.poll() is not None:
        return

    process.send_signal(signal.SIGINT)

    try:
        process.wait(timeout=timeout)

    except subprocess.TimeoutExpired:
        process.terminate()

        try:
            process.wait(timeout=5)

        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def fixed_audio_recording(
    output_path: Path,
    monitor_source: str,
    duration: float | None = None,
) -> Path:
    """
    Record system audio from a PulseAudio monitor source via ffmpeg.

    The recording is stored as uncompressed PCM WAV using the
    source's native sample rate and channel layout.

    Args:
        output_path:
            Destination WAV file.
        monitor_source:
            PulseAudio monitor source, e.g. "alsa-sink.monitor".
        duration:
            Optional recording duration in seconds.
            If None, ffmpeg records until interrupted.

    Returns:
        Path to the created WAV file.
    """

    ensure_dir(output_path)

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "pulse",
        "-i",
        monitor_source,
    ]

    if duration is not None:
        if duration <= 0:
            raise ValueError("duration must be > 0")

        cmd.extend(
            [
                "-t",
                str(duration),
            ]
        )

    cmd.extend(
        [
            "-c:a",
            "pcm_s16le",
            str(output_path),
        ]
    )

    try:
        subprocess.run(
            cmd,
            check=True,
        )

    except FileNotFoundError as exc:
        raise RuntimeError("ffmpeg is not installed or not available on PATH.") from exc

    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"ffmpeg failed while recording system audio "
            f"from source '{monitor_source}'."
        ) from exc

    if not output_path.is_file():
        raise FileNotFoundError(f"Audio recording was not created: {output_path}")

    if output_path.stat().st_size == 0:
        raise RuntimeError(f"Audio recording is empty: {output_path}")

    return output_path


def audio_recording(context: AudioContext):

    cfg_recording = context.cfg_recording

    monitor_source = cfg_recording.audio_monitor_source or detect_monitor_source()

    f_name = context.f_name
    # "test_audio_raw"
    data_audio = folder_env_vars.data_html
    save_path = (
        f"/home/robfra/0_Portfolio_Projekte/gmp_compliance/data/{f_name}_%03d.wav"
    )
    # Path(f"/home/robfra/0_Portfolio_Projekte/gmp_compliance/data/{f_name}_2.wav")
    # folder_env_vars.audio_data / ".wav"
    # print(source)

    # if not cfg_recording.start_stop:
    #     fixed_audio_recording(
    #                 output_path=save_path,
    #                 monitor_source=monitor_source,
    #                 duration=cfg_recording.duration
    #                 )
    # else:
    process = start_system_audio_recording(
        output_path=save_path,
        monitor_source=monitor_source,
        segment_time=cfg_recording.segment_duration,
    )

    try:
        input("Recording... press Enter to stop.")

    except KeyboardInterrupt:
        pass

    finally:
        stop_system_audio_recording(process)

    # audio_folder = save_path.parent
    audio_files = [
        f
        for f in data_audio.iterdir()
        if f.stem.startswith(f_name) and f.suffix == save_path.suffix
    ]

    if len(audio_files) == 0:
        # not save_path.is_file():
        raise FileNotFoundError(f"Recording was not created: {save_path}")
    if any(f.stat().st_size == 0 for f in audio_files):
        raise RuntimeError(f"At least one of the recordings is empty: {save_path}")

    return save_path


if __name__ == "__main__":
    # mode = input("Do you want to start a start-stop-recording? [(Y)es | (N)o]:  ")

    # if mode in ("Y", "Yes"):

    # elif mode in ("N", "No"):
    f_path = run_audio_recording()

    print(f"File save in: {f_path}")
