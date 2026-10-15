"""Material archiving built on the existing CS50 bounded streaming primitive.

Single-writer workspace and serial calls deliberately bound concurrency to one.
All redirects are refused, so no unvalidated redirect target is contacted.
"""

import os
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

import httpx

from src.model_materials.materials import ArtifactReceipt, MaterialResource
from src.tools_lecture.execute_cs50 import (
    CS50Executor,
    ExecutionConflict,
    digest,
    write_state,
)
from src.tools_materials.inventory import capability, official
from src.tools_materials.storage import artifact_root, locate, locked

MIMES = {
    "html": {"text/html", "application/xhtml+xml"},
    "pdf": {"application/pdf"},
    "png": {"image/png"},
    "jpg": {"image/jpeg"},
    "jpeg": {"image/jpeg"},
    "gif": {"image/gif"},
    "webp": {"image/webp"},
    "svg": {"image/svg+xml"},
    "py": {"text/plain", "text/x-python", "application/octet-stream"},
    "sql": {"text/plain", "application/sql", "application/octet-stream"},
    "js": {"text/plain", "text/javascript", "application/javascript"},
    "css": {"text/plain", "text/css"},
    "c": {"text/plain", "text/x-c"},
    "h": {"text/plain", "text/x-c"},
    "txt": {"text/plain"},
    "md": {"text/plain", "text/markdown"},
}


class CheckedTransport(httpx.BaseTransport):
    def __init__(self, inner, binding, max_bytes):
        self.inner, self.binding, self.max_bytes = inner, binding, max_bytes
        self.mime = None

    def handle_request(self, request):
        if str(request.url) != self.binding.original_url or not official(
            str(request.url)
        ):
            raise ExecutionConflict("Unapproved download source/redirect")
        response = self.inner.handle_request(request)
        if response.status_code == 200:
            self.mime = (
                response.headers.get("content-type", "").split(";")[0].lower().strip()
            )
            try:
                if self.mime not in MIMES[self.binding.format]:
                    raise ExecutionConflict("Unexpected or missing Content-Type")
                length = response.headers.get("content-length")
                if length is not None and (
                    int(length) < 0 or int(length) > self.max_bytes
                ):
                    raise ExecutionConflict("Content-Length exceeds limit")
                if response.headers.get("content-encoding", "identity") not in (
                    "identity",
                    "",
                ):
                    raise ExecutionConflict("Compressed transfer not supported")
            except Exception:
                response.close()
                raise
        return response

    def close(self):
        self.inner.close()


class MaterialDownloader:
    def __init__(
        self,
        workspace,
        *,
        transport=None,
        max_bytes=16 * 1024 * 1024,
        timeout=10.0,
        total_timeout=45.0,
        retries=1,
        sleep=time.sleep,
    ):
        self.workspace = artifact_root(workspace)
        self.transport = transport
        if (
            not 1 <= max_bytes <= 64 * 1024 * 1024
            or timeout <= 0
            or total_timeout <= 0
            or not 0 <= retries <= 2
        ):
            raise ValueError("Invalid bounded download configuration")
        self.max_bytes, self.timeout, self.total_timeout = (
            max_bytes,
            timeout,
            total_timeout,
        )
        self.retries, self.sleep = retries, sleep

    def paths(self, binding):
        directory = binding.material_id.split(":")[1]
        return (
            locate(self.workspace, f"{directory}/raw/source"),
            locate(self.workspace, f"{directory}/receipt.v1.json"),
        )

    def validate(self, binding):
        binding = MaterialResource.model_validate_json(binding.model_dump_json())
        raw, path = self.paths(binding)
        if not path.exists():
            raise ExecutionConflict("Missing material receipt")
        receipt = ArtifactReceipt.model_validate_json(path.read_bytes())
        if (
            receipt.binding != binding
            or not receipt.raw_sha256
            or not raw.is_file()
            or digest(raw) != receipt.raw_sha256
        ):
            raise ExecutionConflict("Material identity/raw hash conflict")
        if (
            receipt.status in {"failed", "conflict"}
            and receipt.parser is not None
            and "verified" in receipt.history
        ):
            return receipt
        if receipt.status not in {
            "downloaded",
            "verified",
            "parsed",
            "normalized",
            "completed",
        }:
            raise ExecutionConflict("Material receipt is incomplete")
        return receipt

    def obtain(
        self, binding, *, execute=False, license_reviewed=False, local_file=None
    ):
        binding = MaterialResource.model_validate_json(binding.model_dump_json())
        support, reason = capability(binding.original_url, binding.format)
        if support != "supported":
            raise ValueError(reason)
        if not execute:
            return {
                "status": "selected",
                "material_id": binding.material_id,
                "action": "local_import" if local_file is not None else "download",
                "execute": False,
            }
        if local_file is None and (
            not license_reviewed or binding.license_status != "reviewed"
        ):
            raise ValueError("Explicit license review and execution approval required")
        with locked(self.workspace):
            raw, receipt_path = self.paths(binding)
            raw.parent.mkdir(parents=True, exist_ok=True)
            locate(self.workspace, raw.relative_to(self.workspace))
            if receipt_path.exists():
                old = ArtifactReceipt.model_validate_json(receipt_path.read_bytes())
                if old.binding != binding:
                    raise ExecutionConflict("Material receipt binding conflict")
                if (
                    old.status in {"failed", "conflict"}
                    and old.parser is not None
                    and "verified" in old.history
                ):
                    verified = self.validate(binding)
                    if (
                        local_file is not None
                        and digest(Path(local_file)) != verified.raw_sha256
                    ):
                        raise ExecutionConflict("Local import source changed")
                    return verified
                if old.status in {"verified", "parsed", "normalized", "completed"}:
                    verified = self.validate(binding)
                    if (
                        local_file is not None
                        and digest(Path(local_file)) != verified.raw_sha256
                    ):
                        raise ExecutionConflict("Local import source changed")
                    return verified
                if old.status == "downloaded" and raw.exists():
                    self.validate(binding)
                    verified = old.model_copy(
                        update={
                            "status": "verified",
                            "history": old.history + ("verified",),
                        }
                    )
                    write_state(receipt_path, verified.model_dump(mode="json"))
                    return verified
            if raw.exists():
                raise ExecutionConflict("Existing raw file without verified receipt")
            origin = "local_import" if local_file is not None else "http_download"
            receipt = ArtifactReceipt(
                binding=binding, status="selected", origin=origin, history=("selected",)
            )
            write_state(receipt_path, receipt.model_dump(mode="json"))
            fd, name = tempfile.mkstemp(prefix=".download-", dir=raw.parent)
            os.close(fd)
            temporary = Path(name)
            try:
                mime = None
                if local_file is not None:
                    source = Path(local_file)
                    if (
                        source.is_symlink()
                        or not source.is_file()
                        or source.stat().st_size > self.max_bytes
                    ):
                        raise ValueError("Unsafe or oversized local source")
                    with source.open("rb") as incoming, temporary.open("wb") as out:
                        count = 0
                        while block := incoming.read(65536):
                            count += len(block)
                            if count > self.max_bytes:
                                raise ValueError("Local source exceeds size limit")
                            out.write(block)
                        out.flush()
                        os.fsync(out.fileno())
                    mime = sorted(MIMES[binding.format])[0]
                else:
                    guard = CheckedTransport(
                        self.transport or httpx.HTTPTransport(retries=0),
                        binding,
                        self.max_bytes,
                    )
                    # Reuse exact SRT executor streaming/retry/deadline code, without its SRT-specific plan.
                    transfer = SimpleNamespace(
                        transport=guard,
                        timeout=self.timeout,
                        total_timeout=self.total_timeout,
                        max_bytes=self.max_bytes,
                        retries=self.retries,
                        sleep=self.sleep,
                    )
                    CS50Executor.download(
                        transfer,
                        SimpleNamespace(transcript_url=binding.original_url),
                        temporary,
                    )
                    mime = guard.mime
                if temporary.stat().st_size == 0:
                    raise ValueError("Empty material download/import")
                receipt = receipt.model_copy(
                    update={
                        "raw_sha256": digest(temporary),
                        "mime_type": mime,
                        "status": "downloaded",
                        "history": receipt.history + ("downloaded",),
                    }
                )
                write_state(receipt_path, receipt.model_dump(mode="json"))
                os.link(temporary, raw)
                from src.tools_lecture.execute_cs50 import sync_directory

                sync_directory(raw.parent)
                receipt = receipt.model_copy(
                    update={
                        "status": "verified",
                        "history": receipt.history + ("verified",),
                    }
                )
                write_state(receipt_path, receipt.model_dump(mode="json"))
                return receipt
            except Exception as exc:
                # Preserve write-ahead publication proof if the raw artifact already exists.
                if not raw.exists():
                    receipt = receipt.model_copy(
                        update={
                            "status": "failed",
                            "error": f"{type(exc).__name__}: {exc}",
                            "history": receipt.history + ("failed",),
                        }
                    )
                    write_state(receipt_path, receipt.model_dump(mode="json"))
                raise
            finally:
                temporary.unlink(missing_ok=True)
