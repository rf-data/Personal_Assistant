"""Controlled CS50 SRT execution; no general processing or inference imports.

Receipts are write-ahead records: a prepared hash permits recovery after publication,
never adoption of an arbitrary pre-existing file. POSIX flock serializes executors.
"""

import argparse
import fcntl
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from src.model_transcribe.data_transcribe import TranscriptDocument
from src.tools_transcribe.import_transcript import import_srt


def __getattr__(name):
    """Preserve the existing plan-model re-export without eager settings imports."""
    if name == "CS50AdapterPlan":
        from src.tools_lecture.adapt_cs50 import CS50AdapterPlan

        return CS50AdapterPlan
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class ExecutionConflict(ValueError):
    """Unverified identity, path, provenance or contents; no overwrite permission."""


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            value.update(block)
    return value.hexdigest()


def safe_path(root, path):
    root, path = Path(root).absolute(), Path(path).absolute()
    if ".." in path.parts or not path.is_relative_to(root) or path == root:
        raise ExecutionConflict(f"Path outside explicit artifact root: {path}")
    for parent in (root, *path.parents, path):
        if parent.is_symlink():
            raise ExecutionConflict(f"Symlink forbidden: {parent}")
    return path


def sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_state(path, state):
    """Atomically update executor-owned metadata only, never transcript artifacts."""
    descriptor, temporary = tempfile.mkstemp(prefix=".receipt-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(state, output, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        sync_directory(path.parent)
    finally:
        Path(temporary).unlink(missing_ok=True)


def validate_document(path, binding, raw):
    document = TranscriptDocument.model_validate_json(path.read_bytes())
    provenance = document.provenance
    if (
        document.source != str(binding.raw_srt_path)
        or document.language != binding.language
        or provenance is None
        or provenance.transcript_source.value != "official_subtitle"
        or provenance.source_url != binding.transcript_url
        or provenance.source_file != str(binding.raw_srt_path)
        or provenance.language != binding.language
        or provenance.media_format != "srt"
        or provenance.media_id != binding.media_id
    ):
        raise ExecutionConflict("Transcript provenance contradicts the checked binding")
    expected = import_srt(
        raw,
        language=binding.language,
        original_url=binding.transcript_url,
        preserve_empty_cues=True,
    )
    validate_order(expected)
    if document.segments != expected.segments or document.text != expected.text:
        raise ExecutionConflict(
            "Normalized transcript contradicts original SRT contents"
        )
    return document


def validate_order(document):
    if not any(segment.text.strip() for segment in document.segments):
        raise ValueError("SRT contains no non-empty cues")
    if any(
        following.start < previous.start
        for previous, following in zip(
            document.segments, document.segments[1:], strict=False
        )
    ):
        raise ValueError("SRT cue start timestamps are out of order")


class CS50Executor:
    def __init__(
        self,
        plan,
        *,
        workspace,
        transport=None,
        timeout=15.0,
        max_bytes=8 * 1024 * 1024,
        retries=2,
        total_timeout=60.0,
        sleep=time.sleep,
    ):
        from src.tools_lecture.adapt_cs50 import CS50AdapterPlan

        self.plan = CS50AdapterPlan.model_validate_json(plan.model_dump_json())
        self.workspace = Path(workspace).absolute()
        self.transport, self.sleep = transport, sleep
        if timeout <= 0 or total_timeout <= 0 or max_bytes < 1 or not 0 <= retries <= 3:
            raise ValueError("Invalid timeout/size/retry limits")
        self.timeout, self.max_bytes = timeout, max_bytes
        self.retries, self.total_timeout = retries, total_timeout
        self.courses = {}
        self.bindings = {}
        self.tasks = {}
        for course in self.plan.courses:
            root = course.artifact_root
            root = root if root.is_absolute() else self.workspace / root
            safe_path(self.workspace, root)
            for binding in course.bindings:
                url = urlsplit(binding.transcript_url)
                if (
                    url.scheme != "https"
                    or url.hostname != "cdn.cs50.net"
                    or url.username
                    or url.password
                    or url.port not in (None, 443)
                ):
                    raise ExecutionConflict(
                        "Only checked official CDN HTTPS sources are executable"
                    )
                self.bindings[binding.resource_id] = binding
                self.courses[binding.resource_id] = root
                for path in (binding.raw_srt_path, binding.transcript_json_path):
                    target = path if path.is_absolute() else self.workspace / path
                    safe_path(root, target)
            for task in course.tasks:
                self.tasks[task.task_id] = task
        for task in self.tasks.values():
            if any(dependency not in self.tasks for dependency in task.depends_on):
                raise ExecutionConflict("Missing task dependency")

    def select(self, *, course=None, section=None, max_lectures=1):
        if max_lectures < 1:
            raise ValueError("max_lectures must be positive")
        selected = [
            b
            for b in self.bindings.values()
            if (course is None or b.course_id == course)
            and (section is None or b.section_key == section)
        ]
        if not selected:
            raise ValueError("No matching CS50 lectures")
        return tuple(selected[:max_lectures])

    def target(self, binding, path):
        return safe_path(
            self.courses[binding.resource_id],
            path if path.is_absolute() else self.workspace / path,
        )

    def download(self, binding, temporary):
        deadline = time.monotonic() + self.total_timeout
        with httpx.Client(
            transport=self.transport,
            follow_redirects=False,
            trust_env=False,
            timeout=self.timeout,
        ) as client:
            for attempt in range(self.retries + 1):
                try:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError("Total download timeout exceeded")
                    with client.stream(
                        "GET",
                        binding.transcript_url,
                        timeout=min(self.timeout, remaining),
                    ) as response:
                        if (
                            response.status_code == 429
                            or 500 <= response.status_code < 600
                        ):
                            response.raise_for_status()
                        if response.status_code != 200:
                            raise ValueError(
                                f"SRT download HTTP {response.status_code}; redirects refused"
                            )
                        size = 0
                        with temporary.open("wb") as output:
                            for block in response.iter_bytes(65536):
                                size += len(block)
                                if size > self.max_bytes:
                                    raise ValueError("SRT download exceeds size limit")
                                if time.monotonic() >= deadline:
                                    raise TimeoutError(
                                        "Total download timeout exceeded"
                                    )
                                output.write(block)
                            output.flush()
                            os.fsync(output.fileno())
                        return
                except (httpx.TransportError, httpx.HTTPStatusError, TimeoutError):
                    if attempt == self.retries:
                        raise
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError("Total download timeout exceeded") from None
                    self.sleep(min(2**attempt, remaining))

    def run(self, binding):
        """Execute two actions with per-source persistent receipts and process lock."""
        if self.bindings.get(binding.resource_id) != binding:
            raise ExecutionConflict("Unknown or modified binding")
        raw = self.target(binding, binding.raw_srt_path)
        normalized = self.target(binding, binding.transcript_json_path)
        raw.parent.mkdir(parents=True, exist_ok=True)
        safe_path(self.courses[binding.resource_id], raw)
        receipt = self.target(binding, raw.parent / "execution.v1.json")
        lock = self.target(binding, raw.parent / "execution.lock")
        descriptor = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, "w") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            identity = binding.model_dump(mode="json")
            state = {"schema_version": 1, "binding": identity, "actions": {}}
            if receipt.exists():
                state = json.loads(receipt.read_text(encoding="utf-8"))
                if state.get("schema_version") != 1 or state.get("binding") != identity:
                    raise ExecutionConflict("Receipt identity/provenance conflict")
            actions = state["actions"]
            for task in self.tasks.values():
                if task.resource_id != binding.resource_id:
                    continue
                action = task.task.actions[0].value
                target = raw if action == "download" else normalized
                for dependency in task.depends_on:
                    if actions.get(dependency, {}).get("status") != "done":
                        raise ExecutionConflict(
                            "PARSE_SUBTITLE requires verified DOWNLOAD"
                        )
                record = actions.get(task.task_id)
                if record and record.get("status") in ("prepared", "done"):
                    if not target.exists() or digest(target) != record["sha256"]:
                        if record["status"] == "done" or target.exists():
                            raise ExecutionConflict(
                                "Artifact hash/missing-file conflict"
                            )
                    else:
                        if action == "parse_subtitle":
                            if record.get("input_sha256") != digest(raw):
                                raise ExecutionConflict(
                                    "Transcript input hash conflict"
                                )
                            validate_document(target, binding, raw)
                        record["status"] = "done"
                        write_state(receipt, state)
                        continue
                if target.exists():
                    raise ExecutionConflict("Existing artifact has no verified receipt")
                actions[task.task_id] = {"status": "running", "action": action}
                write_state(receipt, state)
                descriptor, name = tempfile.mkstemp(prefix=".cs50-", dir=target.parent)
                os.close(descriptor)
                temporary = Path(name)
                try:
                    if action == "download":
                        self.download(binding, temporary)
                    elif action == "parse_subtitle":
                        document = import_srt(
                            raw,
                            language=binding.language,
                            original_url=binding.transcript_url,
                            preserve_empty_cues=True,
                        )
                        validate_order(document)
                        # Keep the planned relative source identity, independent of cwd.
                        document.source = str(binding.raw_srt_path)
                        document.provenance.source_file = str(binding.raw_srt_path)
                        document.provenance.media_id = binding.media_id
                        with temporary.open("w", encoding="utf-8") as output:
                            output.write(document.model_dump_json(indent=2) + "\n")
                            output.flush()
                            os.fsync(output.fileno())
                    else:
                        raise ExecutionConflict(f"Unsupported CS50 action {action}")
                    record = {
                        "status": "prepared",
                        "action": action,
                        "sha256": digest(temporary),
                    }
                    if action == "parse_subtitle":
                        record["input_sha256"] = digest(raw)
                    actions[task.task_id] = record
                    write_state(receipt, state)
                    os.link(
                        temporary, target
                    )  # Atomic exclusive publication, no overwrite.
                    sync_directory(target.parent)
                    record["status"] = "done"
                    write_state(receipt, state)
                except Exception as error:
                    # Retain a prepared hash if publication succeeded before interruption.
                    if actions[task.task_id]["status"] != "prepared":
                        actions[task.task_id] = {
                            "status": "failed",
                            "action": action,
                            "error": str(error),
                        }
                        write_state(receipt, state)
                    raise
                finally:
                    temporary.unlink(missing_ok=True)
            return state


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--course")
    parser.add_argument("--section")
    parser.add_argument("--max-lectures", type=int, default=1)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    from src.tools_lecture.adapt_cs50 import CS50AdapterPlan

    plan = CS50AdapterPlan.model_validate_json(args.plan.read_bytes())
    executor = CS50Executor(plan, workspace=Path.cwd())
    bindings = executor.select(
        course=args.course, section=args.section, max_lectures=args.max_lectures
    )
    if args.execute and not args.course:
        parser.error("--execute requires an explicit --course")
    if args.execute:
        for binding in bindings:
            print(json.dumps(executor.run(binding), indent=2))
    else:
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "execution_supported": True,
                    "bindings": [b.model_dump(mode="json") for b in bindings],
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
