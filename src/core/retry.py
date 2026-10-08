## retry.py
# import
import logging
import traceback

from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
    before_sleep_log,
)

from src.core.memory import app_session


RETRYABLE_STATUS_CODES = {
    408,  # timeout
    409,  # conflict
    425,  # too early
    429,  # rate limit
}


import logging

from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
    before_sleep_log,
)

logger = logging.getLogger(__name__)


RETRYABLE_STATUS_CODES = {
    408,  # timeout
    409,  # conflict
    425,  # too early
    429,  # rate limit
}


def is_retryable_exception(exc: BaseException) -> bool:
    """
    Return True only for failures that are plausibly transient.
    """

    if isinstance(
        exc,
        (
            TimeoutError,
            ConnectionError,
        ),
    ):
        return True

    status_code = getattr(exc, "status_code", None)

    if status_code in RETRYABLE_STATUS_CODES:
        return True

    if isinstance(status_code, int) and status_code >= 500:
        return True

    # Some libraries wrap the original exception.
    cause = exc.__cause__ or exc.__context__

    if cause is not None and cause is not exc:
        return is_retryable_exception(cause)

    return False


def retry_remote_call(func):
    """
    Default policy for remote APIs / services.
    """
    return retry(
        retry=retry_if_exception(is_retryable_exception),
        stop=stop_after_attempt(4),
        wait=wait_random_exponential(
            multiplier=1,
            min=1,
            max=20,
        ),
        before_sleep=before_sleep_log(
            logger,
            logging.WARNING,
        ),
        reraise=True,
    )(func)


def retry_llm_call(func):
    return retry(
        retry=retry_if_exception(is_retryable_exception),
        stop=stop_after_attempt(4),
        wait=wait_random_exponential(
            multiplier=1,
            min=1,
            max=30,
        ),
        before_sleep=log_before_retry,
        # before_sleep_log(
        #     logger,
        #     logging.WARNING,
        # ),
        reraise=True,
    )(func)


def retry_download(func):
    return retry(
        retry=retry_if_exception(is_retryable_exception),
        stop=stop_after_attempt(3),
        wait=wait_random_exponential(
            multiplier=2,
            min=2,
            max=30,
        ),
        before_sleep=before_sleep_log(
            logger,
            logging.WARNING,
        ),
        reraise=True,
    )(func)


def retry_summary(
    retry_state: RetryCallState,
) -> str:

    exc = retry_state.outcome.exception() if retry_state.outcome else None

    fn_name = getattr(
        retry_state.fn,
        "__qualname__",
        str(retry_state.fn),
    )

    wait_seconds = retry_state.next_action.sleep if retry_state.next_action else 0.0

    return (
        f"function={fn_name} | "
        f"attempt={retry_state.attempt_number} | "
        f"error={type(exc).__name__ if exc else 'unknown'} | "
        f"message={exc} | "
        f"next_wait={wait_seconds:.2f}s"
    )


def format_retry_exception(retry_state: RetryCallState) -> str:
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


def log_before_retry(
    retry_state: RetryCallState,
) -> None:
    message = retry_summary(
        # format_retry_exception(
        retry_state
    )

    # wait_seconds = 0.0

    # if retry_state.next_action is not None:
    #     wait_seconds = (
    #         retry_state.next_action.sleep or 0.0
    #     )

    # fn_name = getattr(
    #     retry_state.fn,
    #     "__qualname__",
    #     str(retry_state.fn),
    # )

    # message = (
    #     "Retry scheduled | "
    #     "function=%s | "
    #     "attempt=%s | "
    #     "next_wait=%.2fs\n%s"
    # )

    # message =
    # (
    #     f"Retry scheduled | "
    #     f"function={fn_name} | "
    #     f"attempt={retry_state.attempt_number} | "
    #     f"next_wait={wait_seconds:.2f}s\n"
    #     f"{exception_text}"
    # )

    if app_session.logger is not None:
        app_session.logger.warning(
            "Retry scheduled | %s",
            message,
            # message
        )

    else:
        print(
            f"Retry scheduled | {message}"
            # message
        )


def my_before_sleep(retry_state):
    if retry_state.attempt_number == 1:
        loglevel = logging.INFO
    else:
        loglevel = logging.WARNING

    traceback_str = format_retry_exception(retry_state)

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
        f"{traceback_str}"
        f"{'=' * 25} TRACEBACK - END {'=' * 25}\n"
    )
