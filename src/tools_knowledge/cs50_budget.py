"""A02: durable, shared conservative request reservations; no refunds/retries."""

import fcntl
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

from pydantic import Field, StrictInt, model_validator

from src.tools_knowledge.cs50_checkpoint import (
    CheckpointConflict,
    Contract,
    atomic_json,
    fingerprint,
)


class BudgetExhausted(CheckpointConflict):
    pass


class BudgetIdentity(Contract):
    schema_version: Literal[1] = 1
    scope_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    allowed_jobs: tuple[str, ...]
    max_requests: StrictInt = Field(ge=1)
    max_tokens: StrictInt = Field(ge=1)

    @model_validator(mode="after")
    def unique(self):
        if not self.allowed_jobs or len(set(self.allowed_jobs)) != len(
            self.allowed_jobs
        ):
            raise ValueError("Explicit unique budget jobs required")
        return self

    @property
    def budget_id(self):
        return fingerprint(self.model_dump(mode="json"))


class Attempt(Contract):
    job_id: str
    chunk_id: str
    reserved_tokens: StrictInt = Field(ge=1)
    status: Literal["reserved", "done", "unknown", "failed"] = "reserved"
    usage: dict | None = None


class BudgetState(Contract):
    schema_version: Literal[1] = 1
    identity: BudgetIdentity
    attempts: dict[str, Attempt] = Field(default_factory=dict)

    @model_validator(mode="after")
    def integrity(self):
        if any(
            key != fingerprint([a.job_id, a.chunk_id])
            or a.job_id not in self.identity.allowed_jobs
            for key, a in self.attempts.items()
        ):
            raise ValueError("Foreign/invalid budget attempt identity")
        if (
            len(self.attempts) > self.identity.max_requests
            or self.reserved_tokens > self.identity.max_tokens
        ):
            raise ValueError("Budget receipt exceeds declared caps")
        return self

    @property
    def reserved_tokens(self):
        return sum(a.reserved_tokens for a in self.attempts.values())


class BudgetJournal:
    def __init__(self, directory, identity):
        self.directory = Path(directory).absolute()
        self.identity = BudgetIdentity.model_validate(identity.model_dump())

    @contextmanager
    def locked(self):
        if any(p.is_symlink() for p in (self.directory, *self.directory.parents)):
            raise CheckpointConflict("Symlink budget path forbidden")
        self.directory.mkdir(parents=True, exist_ok=True)
        fd = os.open(
            self.directory / "budget.lock",
            os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW,
            0o600,
        )
        try:
            fcntl.flock(
                fd, fcntl.LOCK_EX
            )  # Short transaction; no network under budget lock.
            contract = self.directory / "budget.contract.v1.json"
            path = self.directory / "budget.v1.json"
            if contract.is_symlink() or path.is_symlink():
                raise CheckpointConflict("Symlink budget receipt forbidden")
            if contract.exists():
                try:
                    identity = BudgetIdentity.model_validate_json(contract.read_bytes())
                    state = BudgetState.model_validate_json(path.read_bytes())
                except (OSError, ValueError) as error:
                    raise CheckpointConflict(
                        "Missing/corrupt budget receipt"
                    ) from error
                if identity != self.identity or state.identity != self.identity:
                    raise CheckpointConflict(
                        "Budget scope/limits conflict; reset forbidden"
                    )
            else:
                if any(p.name != "budget.lock" for p in self.directory.iterdir()):
                    raise CheckpointConflict("Unreceipted budget artifacts")
                state = BudgetState(identity=self.identity)
                atomic_json(contract, self.identity.model_dump(mode="json"))
                atomic_json(path, state.model_dump(mode="json"))
            yield state, path
        finally:
            os.close(fd)

    def reserve(self, job_id, chunk_id, reservation):
        amount = reservation["reserved_tokens"]
        if type(amount) is not int or amount <= 0:
            raise CheckpointConflict("Positive integer token reservation required")
        key = fingerprint([job_id, chunk_id])
        with self.locked() as (state, path):
            if any(
                a.usage
                and type(a.usage.get("total_tokens")) is int
                and a.usage["total_tokens"] > a.reserved_tokens
                for a in state.attempts.values()
            ):
                raise CheckpointConflict(
                    "Provider usage exceeded reserved bound; scope blocked"
                )
            if job_id not in self.identity.allowed_jobs:
                raise CheckpointConflict("Foreign job cannot spend this budget")
            if key in state.attempts:
                raise CheckpointConflict("Attempt already reserved; no automatic retry")
            if (
                len(state.attempts) >= self.identity.max_requests
                or state.reserved_tokens + amount > self.identity.max_tokens
            ):
                raise BudgetExhausted("Persistent request/token budget exhausted")
            attempts = {
                **state.attempts,
                key: Attempt(job_id=job_id, chunk_id=chunk_id, reserved_tokens=amount),
            }
            updated = BudgetState(identity=self.identity, attempts=attempts)
            atomic_json(path, updated.model_dump(mode="json"), replace=True)
        return {**reservation, "budget_id": self.identity.budget_id, "attempt_id": key}

    def finish(self, job_id, chunk_id, *, status, usage=None):
        key = fingerprint([job_id, chunk_id])
        with self.locked() as (state, path):
            attempt = state.attempts.get(key)
            if attempt is None:
                raise CheckpointConflict("Missing durable budget reservation")
            if status not in ("done", "unknown", "failed"):
                raise CheckpointConflict("Invalid budget completion")
            if attempt.status != "reserved":
                if attempt.status == status and attempt.usage == usage:
                    return
                raise CheckpointConflict("Terminal budget attempt conflict")
            if usage is not None and any(
                type(v) is not int or v < 0
                for k, v in usage.items()
                if k in ("prompt_tokens", "completion_tokens", "total_tokens")
            ):
                raise CheckpointConflict("Invalid provider usage")
            overshoot = (
                usage is not None
                and type(usage.get("total_tokens")) is int
                and usage["total_tokens"] > attempt.reserved_tokens
            )
            if overshoot:
                status = "unknown"
            attempts = {
                **state.attempts,
                key: attempt.model_copy(update={"status": status, "usage": usage}),
            }
            updated = BudgetState.model_validate(
                {
                    "identity": self.identity.model_dump(),
                    "attempts": {k: a.model_dump() for k, a in attempts.items()},
                }
            )
            atomic_json(path, updated.model_dump(mode="json"), replace=True)
            if overshoot:
                raise CheckpointConflict(
                    "Provider usage exceeded reserved bound; scope blocked"
                )

    def snapshot(self):
        with self.locked() as (state, _):
            return state
