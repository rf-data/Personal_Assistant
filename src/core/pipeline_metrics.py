"""Metrics v1: bounded aggregate samples, no exporter, I/O or worker imports.

This is a future controller boundary. Empty observations emit no measurements.
Unknown state must be omitted; it must never be converted to zero/success.
"""

import math
from collections import defaultdict
from dataclasses import dataclass
from itertools import islice

VERSION = 1
PROCESSES = frozenset(
    {
        "course_discovery",
        "material_planning",
        "material_download",
        "material_parsing",
        "audio_transcription",
        "visual_analysis",
        "visual_enrichment",
        "quality_evaluation",
        "knowledge_extraction",
        "knowledge_consolidation",
        "cs50_offline_workflow",
    }
)
POOLS = frozenset({"default", "cpu", "io", "llm"})
ERRORS = frozenset(
    {"validation", "input", "timeout", "provider", "storage", "internal", "other"}
)
OUTCOMES = frozenset({"success", "failure", "cancelled"})
VOCABULARY = {
    "process": PROCESSES,
    "stage": PROCESSES,
    "worker_pool": POOLS,
    "error_class": ERRORS,
    "outcome": OUTCOMES,
}
BUCKETS = (1, 5, 15, 60, 300, 900, 1800, 3600)


@dataclass(frozen=True)
class Metric:
    name: str
    type: str
    labels: tuple[str, ...]
    help: str


PREFIX = "personal_assistant_"
METRICS = tuple(
    Metric(PREFIX + name, kind, labels, help)
    for name, kind, labels, help in (
        (
            "workers_available",
            "gauge",
            ("worker_pool",),
            "Live ready workers; omit if unknown.",
        ),
        (
            "jobs_started_total",
            "counter",
            ("process", "worker_pool"),
            "Actual dispatch attempts started.",
        ),
        (
            "jobs_completed_total",
            "counter",
            ("process", "worker_pool", "outcome"),
            "Confirmed terminal attempts, including failure and cancellation.",
        ),
        (
            "jobs_failed_total",
            "counter",
            ("process", "worker_pool", "error_class"),
            "Confirmed failed attempts by bounded error class.",
        ),
        (
            "jobs_running",
            "gauge",
            ("process", "worker_pool"),
            "Current running attempts; excludes queued and unknown states.",
        ),
        (
            "job_oldest_running_start_timestamp_seconds",
            "gauge",
            ("process", "worker_pool"),
            "Unix start time of oldest confirmed running attempt; omit when none.",
        ),
        (
            "job_duration_seconds",
            "histogram",
            ("process", "worker_pool", "outcome"),
            "Elapsed time of confirmed terminal attempts.",
        ),
        (
            "pipeline_stage_duration_seconds",
            "histogram",
            ("process", "worker_pool", "stage"),
            "Completed stage wall time; not job duration.",
        ),
    )
)
REGISTRY = {metric.name: metric for metric in METRICS}


@dataclass(frozen=True)
class Sample:
    name: str
    value: float
    labels: dict[str, str]


def contract_document():
    return {
        "schema_version": VERSION,
        "labels": {k: sorted(v) for k, v in VOCABULARY.items()},
        "histogram_buckets_seconds": [*BUCKETS, "+Inf"],
        "max_samples_per_scrape": 2000,
        "metrics": [vars(metric) for metric in METRICS],
        "queue": "Not supplied: no persistent queue service verified.",
    }


def validate_samples(samples):
    """Reject foreign labels rather than dropping them and merging time series."""
    samples = tuple(islice(samples, 2001))
    if len(samples) > 2000:
        raise ValueError("Sample limit exceeded")
    seen = set()
    histograms = defaultdict(dict)
    for sample in samples:
        if not isinstance(sample, Sample):
            raise ValueError("Expected a Sample")
        if not isinstance(sample.name, str) or not isinstance(sample.labels, dict):
            raise ValueError("Expected a metric name and label mapping")
        name = sample.name
        suffix = ""
        if name not in REGISTRY:
            for ending in ("_bucket", "_sum", "_count"):
                if name.endswith(ending):
                    name, suffix = name[: -len(ending)], ending
                    break
        metric = REGISTRY.get(name)
        if metric is None or (metric.type == "histogram") != bool(suffix):
            raise ValueError("Unknown metric or histogram suffix")
        expected = set(metric.labels) | ({"le"} if suffix == "_bucket" else set())
        if set(sample.labels) != expected:
            raise ValueError("Labels contradict bounded schema")
        for key, value in sample.labels.items():
            if not isinstance(value, str):
                raise ValueError("Label values must be strings")
            if key != "le" and value not in VOCABULARY[key]:
                raise ValueError("Unbounded label value")
        value = sample.value
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError("Expected a finite nonnegative observation")
        if (
            suffix not in {"_sum"}
            and not name.endswith("timestamp_seconds")
            and value != int(value)
        ):
            raise ValueError("Counts must be integers")
        identity = (sample.name, tuple(sorted(sample.labels.items())))
        if identity in seen:
            raise ValueError("Duplicate time series")
        seen.add(identity)
        if suffix:
            key = (name, tuple((k, sample.labels[k]) for k in metric.labels))
            bound = sample.labels.get("le", suffix)
            if suffix == "_bucket" and bound not in {
                *(str(b) for b in BUCKETS),
                "+Inf",
            }:
                raise ValueError("Unsupported histogram bound")
            histograms[key][bound] = value
    for values in histograms.values():
        bounds = [*(str(b) for b in BUCKETS), "+Inf"]
        if set(values) != {*bounds, "_sum", "_count"}:
            raise ValueError("Incomplete histogram")
        counts = [values[b] for b in bounds]
        if counts != sorted(counts) or counts[-1] != values["_count"]:
            raise ValueError("Invalid cumulative histogram")
        if values["_count"] == 0 and values["_sum"] != 0:
            raise ValueError("Empty histogram cannot have a nonzero sum")
    return samples


def render_samples(samples):
    """Prometheus text format 0.0.4 for already aggregated real observations.

    Authentication, counters across restarts, concurrent snapshots and HTTP
    hosting are intentionally the responsibility of the future controller.
    """
    samples = validate_samples(samples)
    lines = []
    for metric in METRICS:
        selected = sorted(
            (
                s
                for s in samples
                if s.name == metric.name or s.name.startswith(metric.name + "_")
            ),
            key=lambda s: (
                tuple(sorted((k, v) for k, v in s.labels.items() if k != "le")),
                s.name,
                float(s.labels["le"]) if "le" in s.labels else 0,
            ),
        )
        if not selected:
            continue
        lines.extend(
            (
                f"# HELP {metric.name} {metric.help}",
                f"# TYPE {metric.name} {metric.type}",
            )
        )
        for sample in selected:
            labels = ",".join(f'{k}="{v}"' for k, v in sorted(sample.labels.items()))
            value = (
                str(sample.value)
                if isinstance(sample.value, int)
                else repr(sample.value)
            )
            lines.append(f"{sample.name}{{{labels}}} {value}")
    return "\n".join(lines) + ("\n" if lines else "")
