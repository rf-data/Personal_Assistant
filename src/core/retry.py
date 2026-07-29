## retry.py
# import
import logging
import traceback

from tenacity import RetryCallState

from src.core.memory import app_session


def log_retry(retry_state: RetryCallState) -> str:
    """
    Gibt den vollständigen Traceback der Exception als String zurück.
    """

    if retry_state.outcome is None:
        return "No outcome available."

    exc = retry_state.outcome.exception()

    if exc is None:
        return "No exception available."

    tb = "".join(
        traceback.format_exception(
            type(exc),
            exc,
            exc.__traceback__,
        )
    )

    return f"Exception: {type(exc).__name__}\nMessage: {exc}\n\n{tb}"


def my_before_sleep(retry_state):
    if retry_state.attempt_number < 1:
        loglevel = logging.INFO
    else:
        loglevel = logging.WARNING

    traceback_str = log_retry(retry_state)

    app_session.logger.log(
        loglevel,
        "Retrying %s: attempt %s ended with: %s\nTraceback:\n%s",
        retry_state.fn,
        retry_state.attempt_number,
        retry_state.outcome,
        traceback_str,
    )

    print(
        f"Retrying {retry_state.fn} "
        f"attempt {retry_state.attempt_number} "
        f"ended with: {retry_state.outcome}"
        f"{'=' * 25} TRACEBACK - START {'=' * 25}"
        "traceback_str"
        f"{'=' * 25} TRACEBACK - END {'=' * 25}\n"
    )
