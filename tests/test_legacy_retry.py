"""Retry classification must terminate without contacting a service or sleeping."""

import pytest

from src.core.retry import is_retryable_exception, retry_download


@pytest.mark.parametrize(
    ("error", "expected"),
    [(TimeoutError(), True), (ConnectionError(), True), (ValueError(), False)],
)
def test_builtin_exception_classification(error, expected):
    assert is_retryable_exception(error) is expected


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (408, True),
        (409, True),
        (425, True),
        (429, True),
        (500, True),
        (503, True),
        (400, False),
        (401, False),
        (404, False),
        (None, False),
    ],
)
def test_status_classification(status, expected):
    error = RuntimeError("synthetic")
    error.status_code = status
    assert is_retryable_exception(error) is expected


@pytest.mark.parametrize("attribute", ["__cause__", "__context__"])
def test_wrapped_timeout(attribute):
    error = RuntimeError("wrapper")
    setattr(error, attribute, TimeoutError())
    assert is_retryable_exception(error) is True


def test_explicit_cause_precedes_context():
    error = RuntimeError("wrapper")
    error.__cause__ = ValueError()
    error.__context__ = TimeoutError()
    assert is_retryable_exception(error) is False


@pytest.mark.parametrize("attribute", ["__cause__", "__context__"])
def test_exception_cycle_terminates(attribute):
    first, second = RuntimeError("first"), ValueError("second")
    setattr(first, attribute, second)
    setattr(second, attribute, first)
    assert is_retryable_exception(first) is False


def test_long_exception_chain_terminates():
    error = TimeoutError()
    for _ in range(1500):
        wrapper = RuntimeError()
        wrapper.__cause__ = error
        error = wrapper
    assert is_retryable_exception(error) is True


def test_retryable_exception_inside_cycle_is_retained():
    error, timeout = RuntimeError(), TimeoutError()
    error.__cause__ = timeout
    timeout.__cause__ = error
    assert is_retryable_exception(error) is True


def test_download_attempt_budget_and_reraise():
    calls = []
    error = TimeoutError("offline fixture")

    @retry_download
    def operation():
        calls.append(None)
        raise error

    with pytest.raises(TimeoutError) as caught:
        operation.retry_with(wait=lambda _: 0, sleep=lambda _: None)()
    assert caught.value is error
    assert len(calls) == 3
