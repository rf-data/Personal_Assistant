"""Pull-only SQLite aggregates following the published C15 contract, if present."""

from src.job_control.registry import PDF_PROCESS, REGISTRY, WORKFLOW_PROCESS

BUCKETS = (1, 5, 15, 60, 300, 900, 1800, 3600)


def render_metrics(store, ttl, courses=None):
    jobs = tuple(
        j
        for j in store.all()
        if courses is None or j.parameters["course_id"] in courses
    )
    samples = []

    def sample(name, value, **labels):
        samples.append(("personal_assistant_" + name, value, labels))

    with store.connection() as db:
        heartbeat = db.execute("SELECT heartbeat FROM worker WHERE id=1").fetchone()
    if heartbeat:
        sample(
            "workers_available", int(store.worker_available(ttl)), worker_pool="default"
        )
    queues = []
    processes = (
        *REGISTRY,
        *(
            p.process_id
            for p in (WORKFLOW_PROCESS, PDF_PROCESS)
            if any(j.process_id == p.process_id for j in jobs)
        ),
    )
    for process in processes:
        labels = dict(process=process, worker_pool="default")
        attempts = [j for j in jobs if j.process_id == process and j.started_at]
        sample("jobs_started_total", len(attempts), **labels)
        running = [j for j in attempts if j.status in {"running", "cancel_requested"}]
        sample("jobs_running", len(running), **labels)
        queues.append(
            (
                labels,
                sum(j.process_id == process and j.status == "queued" for j in jobs),
            )
        )
        if running:
            from datetime import datetime

            sample(
                "job_oldest_running_start_timestamp_seconds",
                min(datetime.fromisoformat(j.started_at).timestamp() for j in running),
                **labels,
            )
        for outcome, status in (
            ("success", "completed"),
            ("failure", "failed"),
            ("cancelled", "cancelled"),
        ):
            rows = [j for j in attempts if j.status == status]
            sample("jobs_completed_total", len(rows), **labels, outcome=outcome)
            durations = [
                j.duration_seconds for j in rows if j.duration_seconds is not None
            ]
            if durations:
                for bound in BUCKETS:
                    sample(
                        "job_duration_seconds_bucket",
                        sum(d <= bound for d in durations),
                        **labels,
                        outcome=outcome,
                        le=str(bound),
                    )
                sample(
                    "job_duration_seconds_bucket",
                    len(durations),
                    **labels,
                    outcome=outcome,
                    le="+Inf",
                )
                sample(
                    "job_duration_seconds_sum",
                    sum(durations),
                    **labels,
                    outcome=outcome,
                )
                sample(
                    "job_duration_seconds_count",
                    len(durations),
                    **labels,
                    outcome=outcome,
                )
        for error in ("input", "timeout", "internal", "other"):
            sample(
                "jobs_failed_total",
                sum(
                    j.status == "failed" and (j.error_class or "other") == error
                    for j in attempts
                ),
                **labels,
                error_class=error,
            )
    try:
        from src.core.pipeline_metrics import Sample, render_samples
    except ImportError:
        # C15 is not merged at C16's starting point. Fixed bounded names/labels
        # below follow its published contract without copying its implementation.
        types = {}
        lines = []
        for name, value, labels in samples:
            family = name
            for suffix in ("_bucket", "_sum", "_count"):
                if name.endswith(suffix):
                    family = name[: -len(suffix)]
                    break
            kind = (
                "histogram"
                if family != name
                else "counter"
                if name.endswith("_total")
                else "gauge"
            )
            if family not in types:
                types[family] = kind
                lines.append(f"# TYPE {family} {kind}")
            text = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
            lines.append(f"{name}{{{text}}} {value}")
        result = "\n".join(lines) + "\n"
    else:
        result = render_samples(
            [Sample(name, value, labels) for name, value, labels in samples]
        )
    # A persistent local queue now exists. This bounded v1 extension is not
    # silently passed off as an existing C15 metric family.
    result += "# TYPE personal_assistant_queue_jobs gauge\n"
    for labels, count in queues:
        text = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        result += f"personal_assistant_queue_jobs{{{text}}} {count}\n"
    return result
