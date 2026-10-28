"""C26 capacity checks around existing bounded writers; not a disk quota."""

import os
import shutil
import stat
from pathlib import Path
from typing import Literal

import httpx
from pydantic import Field

from src.job_control.catalog import read_file
from src.job_control.models import Contract
from src.job_control.operations import private
from src.tools_materials.quality import _json

MIB = 1024**2


class CapacityLimits(Contract):
    schema_version: Literal[1] = 1
    reserve_bytes: int = Field(default=512 * MIB, strict=True, ge=512 * MIB, le=1024**4)
    archive_bytes: int = Field(default=256 * MIB, strict=True, ge=MIB, le=2 * 1024**3)
    catalog_bytes: int = Field(default=256 * MIB, strict=True, ge=MIB, le=2 * 1024**3)
    job_bytes: int = Field(default=2 * 1024**3, strict=True, ge=MIB, le=2 * 1024**3)
    report_bytes: int = Field(default=16 * MIB, strict=True, ge=MIB, le=64 * MIB)
    max_materials: int = Field(default=32, strict=True, ge=1, le=32)

    def batch_size(self, batch):
        if len(batch.materials) > self.max_materials:
            raise ValueError("Capacity material count exceeded")


def load_limits(path):
    return CapacityLimits.model_validate(_json(read_file(private(Path(path)), 8192)))


def tree_bytes(root, maximum):
    """Stat-only, own explicitly selected root; never follows symlinks."""
    private(root, directory=True)
    size, count = 0, 0

    def inaccessible(error):
        raise error

    for base, dirs, files in os.walk(root, followlinks=False, onerror=inaccessible):
        for name in dirs + files:
            count += 1
            if count > 20000:
                raise ValueError("Capacity entry limit exceeded")
            try:
                info = (Path(base) / name).lstat()
            except FileNotFoundError:
                continue  # An owned writer may atomically publish/remove a temp.
            if stat.S_ISDIR(info.st_mode):
                continue
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("Unsafe capacity entry")
            size += info.st_size
            if size > maximum:
                raise ValueError("Capacity byte budget exceeded")
    return size


def free_space(root, reserve, additional=0):
    if shutil.disk_usage(root).free < reserve + additional:
        raise ValueError("Capacity free-space reserve reached")


def check_capacity(root, maximum, reserve, additional=0):
    free_space(root, reserve, additional)
    used = tree_bytes(root, maximum)
    if used + additional > maximum:
        raise ValueError("Capacity projected byte budget exceeded")
    return used


def estimate(batch, limits):
    limits.batch_size(batch)
    snapshot = sum(len(read_file(batch.input_path(n))) for n in batch.files)
    count = len(batch.materials)
    raw = count * batch.max_bytes
    # Explicit planning allowance, not a promise about PDF decompression size.
    archive = raw + count * MIB
    catalog = count * (snapshot + batch.max_bytes + MIB)
    return dict(
        schema_version=1,
        materials=count,
        raw_upper_bytes=raw,
        discovery_bytes=snapshot,
        archive_increment_allowance_bytes=archive,
        catalog_increment_allowance_bytes=catalog,
        job_budget_bytes=limits.job_bytes,
        report_budget_bytes=limits.report_bytes,
        free_reserve_bytes=limits.reserve_bytes,
        required_free_before_new_batch_bytes=(
            limits.reserve_bytes
            + archive
            + catalog
            + limits.job_bytes
            + limits.report_bytes
        ),
        parser_expansion_is_not_known=True,
        source_lengths_are_not_known=True,
    )


class BudgetStream(httpx.SyncByteStream):
    def __init__(self, stream, root, limits):
        self.stream, self.root, self.limits = stream, root, limits

    def __iter__(self):
        for chunk in self.stream:
            check_capacity(
                self.root,
                self.limits.archive_bytes,
                self.limits.reserve_bytes,
                len(chunk),
            )
            yield chunk

    def close(self):
        self.stream.close()


class CapacityTransport(httpx.BaseTransport):
    def __init__(self, inner, root, limits):
        self.inner, self.root, self.limits = inner, root, limits

    def handle_request(self, request):
        response = self.inner.handle_request(request)
        return httpx.Response(
            response.status_code,
            headers=response.headers,
            stream=BudgetStream(response.stream, self.root, self.limits),
            extensions=response.extensions,
        )

    def close(self):
        self.inner.close()


class TransferBudget(httpx.BaseTransport):
    """Payload budget across all attempts, including failed attempts."""

    def __init__(self, inner, maximum=6 * 1024**2):
        self.inner, self.remaining = inner, maximum

    def handle_request(self, request):
        response = self.inner.handle_request(request)
        owner, stream = self, response.stream

        class Bounded(httpx.SyncByteStream):
            def __iter__(self):
                for block in stream:
                    owner.remaining -= len(block)
                    if owner.remaining < 0:
                        raise ValueError("Per-run transfer budget exceeded")
                    yield block

            def close(self):
                stream.close()

        return httpx.Response(
            response.status_code,
            headers=response.headers,
            stream=Bounded(),
            extensions=response.extensions,
        )

    # batch.obtain owns each short-lived HTTP client, but this shared budget
    # outlives those clients. HTTPTransport pools can be reopened after close.
    def close(self):
        self.inner.close()
