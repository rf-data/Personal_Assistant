import json

import httpx
import pytest

from src.model_discovery.cs50 import ResourceCandidate
from src.model_materials.materials import MaterialResource
from src.tools_lecture.execute_cs50 import ExecutionConflict
from src.tools_materials.download import MaterialDownloader


def binding(fmt="html", role="notes"):
    r = ResourceCandidate(
        course_id="cs50_python",
        role=role,
        original_url="https://cs50.harvard.edu/python/notes/0/",
        section_keys=("0",),
    )
    return MaterialResource(
        resource=r,
        original_url=str(r.original_url),
        role=role,
        format=fmt,
        license_status="reviewed",
        source_origin="synthetic",
    )


def worker(tmp_path, handler, **kwargs):
    return MaterialDownloader(
        tmp_path / "artifacts",
        transport=httpx.MockTransport(handler),
        sleep=lambda _: None,
        **kwargs,
    )


def test_download_resume_hash_and_no_overwrite(tmp_path):
    calls = []

    def handler(req):
        calls.append(req)
        assert req.headers["accept-encoding"] == "identity"
        return httpx.Response(
            200, content=b"<main>Hello</main>", headers={"content-type": "text/html"}
        )

    w = worker(tmp_path, handler)
    b = binding()
    assert w.obtain(b)["execute"] is False
    assert not w.workspace.exists()
    receipt = w.obtain(b, execute=True, license_reviewed=True)
    assert w.obtain(b, execute=True, license_reviewed=True) == receipt
    assert len(calls) == 1
    raw, path = w.paths(b)
    assert raw.read_bytes() == b"<main>Hello</main>"
    raw.write_bytes(b"corrupt")
    with pytest.raises(ExecutionConflict, match="hash"):
        w.obtain(b, execute=True, license_reviewed=True)
    assert raw.read_bytes() == b"corrupt"


@pytest.mark.parametrize("code,attempts", [(404, 1), (429, 2), (503, 2), (302, 1)])
def test_http_errors_and_bounded_retries(tmp_path, code, attempts):
    calls = []
    w = worker(
        tmp_path, lambda req: calls.append(req) or httpx.Response(code), retries=1
    )
    with pytest.raises((ValueError, httpx.HTTPStatusError)):
        w.obtain(binding(), execute=True, license_reviewed=True)
    assert len(calls) == attempts
    from src.tools_materials.processing import MaterialProcessor

    observed = MaterialProcessor(w.workspace).inspect(binding())
    assert observed.status == "failed" and observed.error
    assert not w.paths(binding())[0].exists()
    assert not list(w.workspace.rglob(".download-*"))


@pytest.mark.parametrize(
    "error", [httpx.ReadTimeout, httpx.ConnectError, httpx.ReadError]
)
def test_transport_failure(tmp_path, error):
    def handler(req):
        raise error("offline simulated interruption")

    w = worker(tmp_path, handler, retries=0)
    with pytest.raises(error):
        w.obtain(binding(), execute=True, license_reviewed=True)
    assert json.loads(w.paths(binding())[1].read_text())["status"] == "failed"


@pytest.mark.parametrize(
    "content,headers",
    [
        (b"", {"content-type": "text/html"}),
        (b"text", {"content-type": "application/pdf"}),
        (b"x" * 20, {"content-type": "text/html"}),
        (b"text", {"content-type": "text/html", "content-length": "999"}),
        (b"text", {}),
    ],
)
def test_size_mime_empty(tmp_path, content, headers):
    w = worker(
        tmp_path,
        lambda r: httpx.Response(200, content=content, headers=headers),
        max_bytes=10,
    )
    with pytest.raises(ValueError):
        w.obtain(binding(), execute=True, license_reviewed=True)
    assert not w.paths(binding())[0].exists()


def test_local_conflict_and_symlink(tmp_path):
    source = tmp_path / "local.html"
    source.write_bytes(b"<main>original</main>")
    w = worker(tmp_path, lambda _: pytest.fail("HTTP forbidden"))
    r = w.obtain(binding(), execute=True, local_file=source)
    assert r.origin == "local_import"
    assert r.mime_type is None
    source.write_bytes(b"changed")
    with pytest.raises(ExecutionConflict):
        w.obtain(binding(), execute=True, local_file=source)
    link = tmp_path / "link"
    link.symlink_to(tmp_path / "artifacts", target_is_directory=True)
    with pytest.raises(ExecutionConflict):
        MaterialDownloader(link / "escape")


def test_unproved_existing_file_and_receipt(tmp_path):
    w = worker(tmp_path, lambda _: pytest.fail("HTTP forbidden"))
    raw, path = w.paths(binding())
    raw.parent.mkdir(parents=True)
    raw.write_bytes(b"existing")
    with pytest.raises(ExecutionConflict, match="without verified"):
        w.obtain(binding(), execute=True, license_reviewed=True)


def test_license_and_unsupported(tmp_path):
    w = worker(tmp_path, lambda _: pytest.fail("HTTP forbidden"))
    with pytest.raises(ValueError, match="license"):
        w.obtain(binding(), execute=True)
    with pytest.raises(ValueError, match="zip"):
        w.obtain(binding("zip"), execute=True, license_reviewed=True)


def test_interrupted_stream_then_resume(tmp_path):
    class Interrupted(httpx.SyncByteStream):
        def __iter__(self):
            yield b"<main>partial"
            raise httpx.ReadError("connection interrupted after bytes")

    w = worker(
        tmp_path,
        lambda r: httpx.Response(
            200, stream=Interrupted(), headers={"content-type": "text/html"}
        ),
        retries=0,
    )
    b = binding()
    with pytest.raises(httpx.ReadError):
        w.obtain(b, execute=True, license_reviewed=True)
    assert not w.paths(b)[0].exists()
    assert not list(w.workspace.rglob(".download-*"))
    w.transport = httpx.MockTransport(
        lambda r: httpx.Response(
            200, content=b"<main>complete</main>", headers={"content-type": "text/html"}
        )
    )
    assert w.obtain(b, execute=True, license_reviewed=True).status == "verified"


def test_resume_after_raw_publication_acknowledgement_loss(tmp_path, monkeypatch):
    import src.tools_materials.download as module

    b = binding()
    w = worker(
        tmp_path,
        lambda r: httpx.Response(
            200, content=b"<main>ok</main>", headers={"content-type": "text/html"}
        ),
    )
    link = module.os.link

    def lose_ack(*args):
        link(*args)
        raise RuntimeError("published; acknowledgement lost")

    monkeypatch.setattr(module.os, "link", lose_ack)
    with pytest.raises(RuntimeError):
        w.obtain(b, execute=True, license_reviewed=True)
    assert w.paths(b)[0].exists()
    monkeypatch.setattr(module.os, "link", link)
    w.transport = httpx.MockTransport(
        lambda _: pytest.fail("resume must not contact HTTP")
    )
    assert w.obtain(b, execute=True, license_reviewed=True).status == "verified"
