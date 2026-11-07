"""Private local run history: immutable raw/results/reviews, atomic mutable status."""

import fcntl
import json
import os
import re
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path
from time import time_ns
from typing import Any
from uuid import uuid4

from src.c27_learning_summary.export import public_result, public_reviews
from src.c27_learning_summary.models import Review, SummaryResult
from src.content_store.artifacts import DIR_FLAGS, FILE_FLAGS, _open_directory, _private
from src.content_store.models import sha256

RUN = re.compile(r"^[a-f0-9]{32}$")


def _read_at(directory: int, name: str) -> bytes:
    fd = os.open(name, FILE_FLAGS, dir_fd=directory)
    try:
        _private(fd)
        with os.fdopen(fd, "rb", closefd=False) as stream:
            return stream.read()
    finally:
        os.close(fd)


def _write_at(directory: int, name: str, encoded: bytes) -> None:
    # Validate existing entries without following links; never repair unsafe data.
    try:
        _read_at(directory, name)
    except FileNotFoundError:
        pass
    temporary = f".{name}.{uuid4().hex}.tmp"
    fd = os.open(
        temporary,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
        dir_fd=directory,
    )
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, name, src_dir_fd=directory, dst_dir_fd=directory)
        os.fsync(directory)
    finally:
        try:
            os.unlink(temporary, dir_fd=directory)
        except FileNotFoundError:
            pass


def _json_at(directory: int, name: str, data: Any) -> None:
    _write_at(
        directory,
        name,
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        ).encode(),
    )


class SummaryStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root).absolute()
        if ".." in self.root.parts or self.root == Path("/"):
            raise ValueError("Explicit store directory required")
        # Create missing parents through descriptors, rejecting links at every step.
        fd = os.open("/", DIR_FLAGS)
        try:
            for part in self.root.parts[1:]:
                try:
                    os.mkdir(part, 0o700, dir_fd=fd)
                except FileExistsError:
                    pass
                child = os.open(part, DIR_FLAGS, dir_fd=fd)
                os.close(fd)
                fd = child
            info = _private(fd, directory=True)
            self.identity = (info.st_dev, info.st_ino)
        finally:
            os.close(fd)
        with self.directory("runs", create=True) as fd:
            info = os.fstat(fd)
            self.runs_identity = (info.st_dev, info.st_ino)

    @contextmanager
    def directory(self, relative: str = "", *, create: bool = False) -> Iterator[int]:
        parts = relative.split("/") if relative else []
        if any(
            not re.fullmatch(r"[A-Za-z0-9_.-]+", p) or p in {".", ".."} for p in parts
        ):
            raise ValueError("Invalid store directory")
        fd = _open_directory(self.root)
        try:
            info = _private(fd, directory=True)
            if (info.st_dev, info.st_ino) != self.identity:
                raise ValueError("Store root identity changed")
            for index, part in enumerate(parts):
                if create:
                    try:
                        os.mkdir(part, 0o700, dir_fd=fd)
                    except FileExistsError:
                        pass
                child = os.open(part, DIR_FLAGS, dir_fd=fd)
                try:
                    info = _private(child, directory=True)
                    if index == 0 and part == "runs" and hasattr(self, "runs_identity"):
                        if (info.st_dev, info.st_ino) != self.runs_identity:
                            raise ValueError("Store runs identity changed")
                except BaseException:
                    os.close(child)
                    raise
                os.close(fd)
                fd = child
            yield fd
        finally:
            os.close(fd)

    def _location(self, run_id: str, relative: str) -> tuple[str, str]:
        self.run_path(run_id)
        path = Path(relative)
        if (
            path.is_absolute()
            or not path.name
            or any(p in {".", ".."} for p in path.parts)
        ):
            raise ValueError("Invalid store file")
        return f"runs/{run_id}" + (
            f"/{path.parent}" if path.parent != Path(".") else ""
        ), path.name

    def read(self, run_id: str, relative: str) -> bytes:
        directory, name = self._location(run_id, relative)
        with self.directory(directory) as fd:
            return _read_at(fd, name)

    def write(self, run_id: str, relative: str, data: Any) -> None:
        directory, name = self._location(run_id, relative)
        with self.directory(directory) as fd:
            _json_at(fd, name, data)

    def publish(self, run_id: str, name: str, data: bytes) -> None:
        directory, name = self._location(run_id, name)
        with self.directory(directory) as fd:
            try:
                if _read_at(fd, name) != data:
                    raise ValueError("Existing export differs")
            except FileNotFoundError:
                _write_at(fd, name, data)

    def _run_ids(self) -> list[str]:
        with self.directory("runs") as fd:
            names = sorted(os.listdir(fd))
        if any(not RUN.fullmatch(n) for n in names):
            raise ValueError("Invalid run directory identity")
        return names

    def run_path(self, run_id: str) -> Path:
        if not RUN.fullmatch(run_id):
            raise ValueError("Invalid run ID")
        return self.root / "runs" / run_id

    @contextmanager
    def exclusive(self) -> Iterator[None]:
        with self.directory() as directory:
            fd = os.open(
                ".run.lock",
                os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                0o600,
                dir_fd=directory,
            )
        try:
            _private(fd)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError(
                    "A local summary/review is already running"
                ) from None
            # Owning the lock proves no cooperating run still owns these states.
            with ExitStack() as stack:
                # Validate all recovery targets before changing any state.
                targets = []
                for run_id in self._run_ids():
                    directory = stack.enter_context(self.directory(f"runs/{run_id}"))
                    state = json.loads(_read_at(directory, "state.json"))
                    targets.append((directory, state))
                for directory, state in targets:
                    if state["status"] == "running":
                        state.update(
                            status="interrupted", error="previous_process_ended"
                        )
                        _json_at(directory, "state.json", state)
            yield
        finally:
            os.close(fd)

    def begin(self, cache_key: str, inputs: dict[str, Any]) -> str:
        run_id = uuid4().hex
        with self.directory("runs") as fd:
            os.mkdir(run_id, 0o700, dir_fd=fd)
        for name in ("raw", "sections", "reviews"):
            with self.directory(f"runs/{run_id}/{name}", create=True):
                pass
        self.write(run_id, "input.json", inputs)
        self.write(
            run_id,
            "state.json",
            dict(
                run_id=run_id,
                cache_key=cache_key,
                status="running",
                started_ns=time_ns(),
            ),
        )
        return run_id

    def state(self, run_id: str) -> dict[str, Any]:
        state: dict[str, Any] = json.loads(self.read(run_id, "state.json"))
        return state

    def finish(self, run_id: str, status: str, **fields: Any) -> None:
        state = self.state(run_id)
        state.update(status=status, ended_ns=time_ns(), **fields)
        self.write(run_id, "state.json", state)

    def result(self, run_id: str) -> SummaryResult:
        state = self.state(run_id)
        raw = self.read(run_id, "result.json")
        if state["status"] != "completed" or sha256(raw) != state.get("result_sha256"):
            raise ValueError("Result not complete or integrity check failed")
        try:
            result = SummaryResult.model_validate_json(raw)
        except ValueError:
            raise ValueError("Stored result validation failed") from None
        if result.run_id != run_id or state["cache_key"] != result.cache_key:
            raise ValueError("Result identity mismatch")
        return result

    def history(self) -> list[dict[str, Any]]:
        return sorted(
            (self.state(run_id) for run_id in self._run_ids()),
            key=lambda s: s["started_ns"],
            reverse=True,
        )

    def cached(self, key: str) -> SummaryResult | None:
        for state in self.history():
            if state["cache_key"] == key and state["status"] == "completed":
                result = self.result(state["run_id"])
                if result.state == "ready_for_review":
                    return result
        return None

    def save_review(self, review: Review) -> dict[str, Any]:
        # Includes reviews in the same local exclusive writer boundary.
        review = Review.model_validate_json(review.model_dump_json())
        with self.exclusive():
            result = self.result(review.run_id)
            ids = {c.claim_id for c in result.claims}
            ratings = {r.claim_id: r for r in review.claims}
            if len(ratings) != len(review.claims) or not set(ratings) <= ids:
                raise ValueError("Unknown or duplicate claim review")
            if review.decision == "approved" and (
                result.state != "ready_for_review"
                or set(ratings) != ids
                or not ids
                or any(r.rating != "correct" or r.recheck for r in ratings.values())
            ):
                raise ValueError(
                    "Approval requires all claims correct, no rechecks and no validation conflicts"
                )
            event = dict(
                review_id=uuid4().hex,
                saved_ns=time_ns(),
                result_sha256=self.state(review.run_id)["result_sha256"],
                review=review.model_dump(mode="json"),
            )
            self.write(
                review.run_id,
                f"reviews/{event['saved_ns']}-{event['review_id']}.json",
                event,
            )
            return event

    def reviews(self, run_id: str) -> list[dict[str, Any]]:
        result_sha = self.state(run_id).get("result_sha256")
        events = []
        with self.directory(f"runs/{run_id}/reviews") as fd:
            names = sorted(n for n in os.listdir(fd) if n.endswith(".json"))
        for name in names:
            event = json.loads(self.read(run_id, f"reviews/{name}"))
            try:
                review = Review.model_validate(event["review"])
            except ValueError:
                raise ValueError("Stored review validation failed") from None
            if review.run_id != run_id or event["result_sha256"] != result_sha:
                raise ValueError("Review/result binding mismatch")
            events.append(event)
        return events

    def export_json(self, run_id: str) -> str:
        reviews = public_reviews(self.reviews(run_id))
        return json.dumps(
            dict(
                export_schema_version=2,
                result=public_result(self.result(run_id)).model_dump(mode="json"),
                reviews=reviews,
                review_status=reviews[-1]["review"]["decision"]
                if reviews
                else "unreviewed",
            ),
            ensure_ascii=False,
            indent=2,
        )
