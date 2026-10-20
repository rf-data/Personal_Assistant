"""Versioned execution receipts, not new Knowledge business models (POSIX)."""

import fcntl
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CheckpointConflict(ValueError):
    """Never adopt, overwrite or retry an unverified execution."""


def encoded(value):
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def fingerprint(value):
    return hashlib.sha256(encoded(value)).hexdigest()


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class JobIdentity(Contract):
    schema_version: Literal[1] = 1
    result_schema_version: Literal["ChunkKnowledgeResult_v1"] = (
        "ChunkKnowledgeResult_v1"
    )
    course_id: str
    section_key: str
    lecture_id: str
    resource_id: str
    source_id: str
    raw_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    transcript_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    input_binding_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    chunking: dict
    chunk_plan_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    selected_chunks: tuple[str, ...]
    prompt_version: str
    prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    result_schema_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    evidence_mode: Literal["chunk", "segment_v1"]
    evidence_version: str
    provider: str
    model: str
    execution_mode: Literal["offline", "llm"]
    request_limits: dict

    @property
    def job_id(self):
        return fingerprint(self.model_dump(mode="json"))


Status = Literal[
    "pending", "request_reserved", "in_flight", "prepared", "done", "failed", "unknown"
]
TRANSITIONS = {
    "pending": {"request_reserved", "prepared", "failed"},
    "request_reserved": {"in_flight", "unknown"},
    "in_flight": {"prepared", "failed", "unknown"},
    "prepared": {"done", "unknown"},
    "done": set(),
    "failed": set(),
    "unknown": set(),
}
ARTIFACTS = {
    "provider": "provider.json",
    "result": "result.json",
    "evidence": "evidence.json",
}


class ChunkCheckpoint(Contract):
    status: Status = "pending"
    chunk_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reservation: dict | None = None
    artifacts: dict[str, str] = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def receipt_contract(self):
        if (
            self.status in ("request_reserved", "in_flight")
            and self.reservation is None
        ):
            raise ValueError("Dispatched chunk requires a persistent reservation")
        if self.status in ("prepared", "done"):
            if set(self.artifacts) != set(ARTIFACTS) or any(
                len(h) != 64 or any(c not in "0123456789abcdef" for c in h)
                for h in self.artifacts.values()
            ):
                raise ValueError(
                    "Prepared/done chunk requires all artifact SHA-256 hashes"
                )
        return self


class JobCheckpoint(Contract):
    schema_version: Literal[1] = 1
    job_id: str
    identity: JobIdentity
    chunks: dict[str, ChunkCheckpoint]
    status: Literal["pending", "active", "done", "blocked"] = "pending"

    @model_validator(mode="after")
    def job_contract(self):
        if self.job_id != self.identity.job_id or set(self.chunks) != set(
            self.identity.selected_chunks
        ):
            raise ValueError("Job ID/selected chunks contradict identity")
        if self.status != job_status(self.chunks):
            raise ValueError("Job status contradicts chunk states")
        return self


def job_status(chunks):
    states = {chunk.status for chunk in chunks.values()}
    if not states or states == {"pending"}:
        return "pending"
    if states == {"done"}:
        return "done"
    if states & {"unknown", "failed"}:
        return "blocked"
    return "active"


def atomic_json(path, value, *, replace=False):
    """fsync + exclusive hardlink publication; replace only locked receipt state."""
    path = Path(path)
    if path.is_symlink():
        raise CheckpointConflict("Symlink artifact/receipt forbidden")
    fd, name = tempfile.mkstemp(prefix=".checkpoint-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded(value))
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            os.replace(temporary, path)
        else:
            os.link(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        temporary.unlink(missing_ok=True)


class CheckpointStore:
    """Use only inside locked(); lock covers validation, dispatch and publication."""

    def __init__(self, directory, identity, chunks):
        self.directory = Path(directory).absolute()
        self.identity = JobIdentity.model_validate(identity.model_dump(mode="json"))
        self.chunk_hashes = {
            c.chunk_id: fingerprint(c.model_dump(mode="json")) for c in chunks
        }
        if (
            not self.identity.selected_chunks
            or len(chunks) != len(self.chunk_hashes)
            or tuple(self.chunk_hashes) != self.identity.selected_chunks
        ):
            raise CheckpointConflict("Selected chunk plan contradicts identity")
        self.state = None
        self.active = False

    @contextmanager
    def locked(self):
        if any(p.is_symlink() for p in (self.directory, *self.directory.parents)):
            raise CheckpointConflict("Symlink checkpoint path forbidden")
        self.directory.mkdir(parents=True, exist_ok=True)
        lock = self.directory / "checkpoint.lock"
        fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise CheckpointConflict(
                    "Checkpoint already locked by another worker"
                ) from error
            self.active = True
            self._load()
            yield self
        finally:
            self.active = False
            os.close(fd)

    def _load(self):
        receipt = self.directory / "checkpoint.v1.json"
        if receipt.exists() or receipt.is_symlink():
            try:
                if receipt.is_symlink():
                    raise ValueError("symlink")
                self.state = JobCheckpoint.model_validate_json(receipt.read_bytes())
            except (OSError, ValueError) as error:
                raise CheckpointConflict("Invalid checkpoint JSON/schema") from error
            if (
                self.state.identity != self.identity
                or self.state.job_id != self.identity.job_id
                or {k: v.chunk_sha256 for k, v in self.state.chunks.items()}
                != self.chunk_hashes
            ):
                raise CheckpointConflict(
                    "Checkpoint source/configuration/chunk identity conflict"
                )
        else:
            if any(p.name != "checkpoint.lock" for p in self.directory.iterdir()):
                raise CheckpointConflict(
                    "Artifacts exist without checkpoint; adoption forbidden"
                )
            self.state = JobCheckpoint(
                job_id=self.identity.job_id,
                identity=self.identity,
                chunks={
                    k: ChunkCheckpoint(chunk_sha256=v)
                    for k, v in self.chunk_hashes.items()
                },
            )
            atomic_json(receipt, self.state.model_dump(mode="json"))
        for chunk_id, state in self.state.chunks.items():
            if state.status in ("request_reserved", "in_flight"):
                self.transition(chunk_id, "unknown")

    def transition(self, chunk_id, status, **fields):
        if not self.active:
            raise CheckpointConflict("Checkpoint mutation requires held job lock")
        old = self.state.chunks[chunk_id]
        if status not in TRANSITIONS[old.status]:
            raise CheckpointConflict(
                f"Forbidden checkpoint transition {old.status} -> {status}"
            )
        if (
            status == "prepared"
            and self.identity.execution_mode == "llm"
            and old.reservation is None
        ):
            raise CheckpointConflict(
                "LLM result requires a durable request reservation"
            )
        new = ChunkCheckpoint.model_validate(
            {**old.model_dump(), **fields, "status": status}
        )
        updated = dict(self.state.chunks, **{chunk_id: new})
        state = self.state.model_copy(
            update={"chunks": updated, "status": job_status(updated)}
        )
        atomic_json(
            self.directory / "checkpoint.v1.json",
            state.model_dump(mode="json"),
            replace=True,
        )
        self.state = state

    def reserve(self, chunk_id, reservation):
        """A02 hook: persist attempt/budget receipt before any API dispatch."""
        self.transition(chunk_id, "request_reserved", reservation=reservation)
        self.transition(chunk_id, "in_flight")

    def _artifact_dir(self, chunk_id):
        path = self.directory / fingerprint(chunk_id)
        if path.is_symlink():
            raise CheckpointConflict("Symlink chunk artifact directory forbidden")
        return path

    def reuse(self, chunk_id, validate):
        if not self.active:
            raise CheckpointConflict("Reuse requires held job lock")
        state = self.state.chunks[chunk_id]
        if state.status == "pending":
            if self._artifact_dir(chunk_id).exists():
                raise CheckpointConflict("Unreceipted chunk artifacts")
            return None
        if state.status not in ("prepared", "done"):
            raise CheckpointConflict(
                f"Chunk {chunk_id} is {state.status}; automatic retry forbidden"
            )
        if set(state.artifacts) != set(ARTIFACTS):
            raise CheckpointConflict("Incomplete artifact receipt")
        values = {}
        for key, filename in ARTIFACTS.items():
            path = self._artifact_dir(chunk_id) / filename
            try:
                if path.is_symlink():
                    raise ValueError("symlink")
                body = path.read_bytes()
                if hashlib.sha256(body).hexdigest() != state.artifacts[key]:
                    raise ValueError("hash")
                values[key] = json.loads(body)
            except (OSError, ValueError) as error:
                raise CheckpointConflict(
                    f"Missing/corrupt {key} artifact; no retry"
                ) from error
        try:
            result = validate(values)
        except (ValueError, TypeError, KeyError) as error:
            raise CheckpointConflict("Artifact/evidence validation failed") from error
        if state.status == "prepared":
            self.transition(chunk_id, "done")
        return result, values, state.metadata

    def complete(self, chunk_id, values, metadata, validate):
        if not self.active:
            raise CheckpointConflict("Publication requires held job lock")
        if set(values) != set(ARTIFACTS):
            raise CheckpointConflict("All three artifacts required")
        validate(values)
        hashes = {k: hashlib.sha256(encoded(v)).hexdigest() for k, v in values.items()}
        self.transition(chunk_id, "prepared", artifacts=hashes, metadata=metadata)
        directory = self._artifact_dir(chunk_id)
        directory.mkdir(exist_ok=False)
        for key, filename in ARTIFACTS.items():
            atomic_json(directory / filename, values[key])
        self.transition(chunk_id, "done")

    def interrupted(self, chunk_id):
        """No retry: dispatch/reservation errors conservatively remain uncertain."""
        status = self.state.chunks[chunk_id].status
        if status in ("in_flight", "request_reserved"):
            self.transition(chunk_id, "unknown")
        elif status == "pending":
            self.transition(chunk_id, "failed")
