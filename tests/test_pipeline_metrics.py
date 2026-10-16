"""Synthetic observations test a contract; they are never scraped or deployed."""

import math
import socket

import pytest

from src.core.pipeline_metrics import (
    BUCKETS,
    METRICS,
    PREFIX,
    Sample,
    contract_document,
    render_samples,
    validate_samples,
)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(
        socket, "create_connection", lambda *a, **kw: pytest.fail("network forbidden")
    )


def sample(name="jobs_running", value=1, **labels):
    return Sample(
        PREFIX + name,
        value,
        labels or {"process": "material_parsing", "worker_pool": "cpu"},
    )


def histogram():
    labels = {"process": "material_parsing", "worker_pool": "cpu", "outcome": "success"}
    return [
        *(
            sample("job_duration_seconds_bucket", int(b >= 5), **labels, le=str(b))
            for b in BUCKETS
        ),
        sample("job_duration_seconds_bucket", 1, **labels, le="+Inf"),
        sample("job_duration_seconds_sum", 5.0, **labels),
        sample("job_duration_seconds_count", 1, **labels),
    ]


def test_empty_means_unknown_not_zero():
    assert render_samples([]) == ""
    assert validate_samples([]) == ()


def test_complete_histogram_and_deterministic_rendering():
    data = [sample(), *histogram()]
    text = render_samples(data)
    assert text == render_samples(reversed(data))
    assert "# TYPE personal_assistant_job_duration_seconds histogram" in text
    assert 'le="+Inf"' in text
    assert "run_id" not in text
    buckets = [line for line in text.splitlines() if "_bucket{" in line]
    assert 'le="1"' in buckets[0] and 'le="+Inf"' in buckets[-1]


def test_counter_precision_is_not_rounded():
    assert "123456789" in render_samples([sample("jobs_started_total", 123456789)])


@pytest.mark.parametrize("labels", [{"process": [], "worker_pool": "cpu"}, None])
def test_malformed_label_mapping(labels):
    with pytest.raises(ValueError):
        validate_samples([Sample(PREFIX + "jobs_running", 1, labels)])


@pytest.mark.parametrize(
    "key", ["run_id", "lecture_id", "filename", "url", "exception", "course_id"]
)
def test_high_cardinality_labels_rejected(key):
    with pytest.raises(ValueError, match="Labels"):
        validate_samples(
            [
                sample(
                    **{
                        key: "private-value",
                        "process": "material_parsing",
                        "worker_pool": "cpu",
                    }
                )
            ]
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("process", "arbitrary-process"),
        ("worker_pool", "host-01"),
        ("error_class", "Traceback secret"),
    ],
)
def test_values_are_allowlisted(key, value):
    labels = {"process": "material_parsing", "worker_pool": "cpu"}
    name = "jobs_running"
    if key == "error_class":
        name = "jobs_failed_total"
    labels[key] = value
    with pytest.raises(ValueError, match="Unbounded"):
        validate_samples([sample(name, **labels)])


@pytest.mark.parametrize("value", [math.nan, math.inf, -1, True, "1", 0.25])
def test_bad_counts(value):
    with pytest.raises(ValueError):
        validate_samples([sample(value=value)])


@pytest.mark.parametrize(
    "name",
    ["queue_jobs", "unknown_metric", "jobs_running_bucket", "job_duration_seconds"],
)
def test_unsupported_names(name):
    with pytest.raises(ValueError):
        validate_samples([sample(name)])


def test_histogram_completeness_order_and_bounds():
    data = histogram()
    with pytest.raises(ValueError, match="Incomplete"):
        validate_samples(data[:-1])
    with pytest.raises(ValueError, match="cumulative"):
        validate_samples([Sample(data[0].name, 2, data[0].labels), *data[1:]])
    with pytest.raises(ValueError, match="bound"):
        validate_samples(
            [Sample(data[0].name, 1, {**data[0].labels, "le": "arbitrary"}), *data[1:]]
        )


def test_duplicate_and_sample_budget():
    with pytest.raises(ValueError, match="Duplicate"):
        validate_samples([sample(), sample()])
    with pytest.raises(ValueError, match="limit"):
        validate_samples([sample()] * 2001)


def test_contract_is_finite_and_queue_not_claimed():
    contract = contract_document()
    assert contract["schema_version"] == 1
    assert len(METRICS) == len({m.name for m in METRICS}) == 8
    assert all(m.name.startswith(PREFIX) for m in METRICS)
    assert all(len(values) <= 10 for values in contract["labels"].values())
    assert "no persistent queue" in contract["queue"].lower()
