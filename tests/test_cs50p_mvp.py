"""Synthetic HTTP fixtures only; no external traffic, host changes or real jobs."""

import json
import socket
import ssl
import subprocess
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from test_cs50_batch_worker import offline as offline
from test_cs50_batch_worker import scope as scope
from test_cs50_material_download import binding, worker

from scripts import cs50p_mvp as cli
from src.tools_materials import batch as api
from src.tools_materials import https_transport as net
from src.tools_materials.capacity import CapacityLimits
from src.tools_materials.processing import MaterialProcessor


@pytest.mark.parametrize(
    "ip",
    [
        "127.0.0.1",
        "10.0.0.1",
        "169.254.169.254",
        "100.100.100.200",
        "::1",
        "fe80::1",
        "fc00::1",
        "0.0.0.0",
        "224.0.0.1",
        "::ffff:127.0.0.1",
        "2002:7f00:1::",
    ],
)
def test_dns_private_and_metadata_fail_closed(monkeypatch, ip):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_a, **_k: [
            (socket.AF_INET6 if ":" in ip else socket.AF_INET, 1, 6, "", (ip, 443))
        ],
    )
    with pytest.raises(ValueError):
        net.public_addresses("cs50.harvard.edu")


def test_mixed_dns_and_rebinding_and_original_tls_name(monkeypatch):
    answers = ["93.184.216.34"]
    calls = []
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_a, **_k: [(socket.AF_INET, 1, 6, "", (ip, 443)) for ip in answers],
    )
    transport = net.PublicHTTPSTransport()
    transport.inner.close()
    transport.inner = httpx.MockTransport(
        lambda r: calls.append(r) or httpx.Response(200)
    )
    request = httpx.Request("GET", "https://cs50.harvard.edu/python/notes/0/")
    transport.handle_request(request).close()
    assert calls[0].url.host == answers[0]
    assert calls[0].headers["host"] == "cs50.harvard.edu"
    assert calls[0].extensions["sni_hostname"] == "cs50.harvard.edu"
    answers.append("10.0.0.1")
    with pytest.raises(ValueError):
        transport.handle_request(request)
    assert len(calls) == 1


def test_credentials_are_not_forwarded(monkeypatch):
    monkeypatch.setattr(net, "public_addresses", lambda _: ["93.184.216.34"])
    transport = net.PublicHTTPSTransport()
    transport.inner.close()
    seen = []
    transport.inner = httpx.MockTransport(
        lambda r: seen.append(r) or httpx.Response(200)
    )
    transport.handle_request(
        httpx.Request(
            "GET",
            "https://cs50.harvard.edu/python/",
            headers={
                "Cookie": "synthetic-secret",
                "Authorization": "Bearer synthetic-secret",
            },
        )
    ).close()
    assert "cookie" not in seen[0].headers and "authorization" not in seen[0].headers


@pytest.mark.parametrize(
    "flag",
    [
        "deployment_gate_required",
        "deployment_gate_protocol",
        "execution_enabled",
        "workflows_enabled",
        "max_parallel",
        "max_queued",
    ],
)
def test_worker_cannot_downgrade_gates(monkeypatch, flag):
    settings = SimpleNamespace(
        deployment_gate_required=True,
        deployment_gate_protocol="c26-gate-v2",
        execution_enabled=True,
        workflows_enabled=True,
        max_parallel=1,
        max_queued=1,
        index_jobs_enabled=False,
        import_jobs_enabled=False,
        catalog={},
    )
    setattr(
        settings,
        flag,
        2
        if flag.startswith("max_")
        else "c26-gate-v1"
        if flag.endswith("protocol")
        else False,
    )
    monkeypatch.setattr(
        "src.job_control.operations.preflight", lambda *_a, **_k: settings
    )
    monkeypatch.setattr(
        cli,
        "load_limits",
        lambda _: CapacityLimits(reserve_bytes=5 * 1024**3, job_bytes=512 * 1024**2),
    )
    with pytest.raises(PermissionError):
        cli.check_worker(Path("unused-config"), Path("unused-limits"))


def test_download_lock_prevents_competing_invocation(scope, download_args):
    import fcntl

    with (download_args.archive / ".mvp-download.lock").open("w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result, code = cli.download(download_args, transport=scope["transport"])
        assert code == 2 and result["status"] == "blocked" and not scope["calls"]


@pytest.mark.parametrize(
    "url",
    [
        "http://cs50.harvard.edu/python/",
        "https://example.org/",
        "https://cs50.harvard.edu@127.0.0.1/",
        "https://cs50.harvard.edu/python/?token=secret",
        "https://cs50.harvard.edu:444/python/",
    ],
)
def test_unapproved_url_before_dns(url, monkeypatch):
    monkeypatch.setattr(net, "public_addresses", lambda _: pytest.fail("DNS forbidden"))
    transport = net.PublicHTTPSTransport()
    with pytest.raises(ValueError):
        transport.handle_request(httpx.Request("GET", url))
    transport.close()


@pytest.mark.parametrize("status", [301, 302, 307, 308, 403, 404, 429, 500])
def test_redirect_and_http_errors_never_publish(tmp_path, status):
    calls = []
    w = worker(
        tmp_path,
        lambda r: (
            calls.append(r)
            or httpx.Response(
                status, headers={"Location": "http://169.254.169.254/latest/meta-data/"}
            )
        ),
        retries=0,
    )
    with pytest.raises((ValueError, httpx.HTTPError)):
        w.obtain(binding(), execute=True, license_reviewed=True)
    assert len(calls) == 1 and not w.paths(binding())[0].exists()


@pytest.mark.parametrize(
    "case", ["short", "oversize", "hash", "timeout", "partial", "badpdf"]
)
def test_corruption_limits_and_interruptions(tmp_path, case):
    class Partial(httpx.SyncByteStream):
        def __iter__(self):
            yield b"partial"
            raise httpx.ReadError("synthetic-token-should-never-be-logged")

    def response(_r):
        if case == "timeout":
            raise httpx.ReadTimeout("synthetic-token-should-never-be-logged")
        if case == "partial":
            return httpx.Response(
                200, stream=Partial(), headers={"Content-Type": "text/html"}
            )
        return httpx.Response(
            200,
            content=b"not-a-pdf" if case == "badpdf" else b"<main>synthetic</main>",
            headers={
                "Content-Type": "application/pdf" if case == "badpdf" else "text/html",
                **({"Content-Length": "99"} if case == "short" else {}),
            },
        )

    w = worker(
        tmp_path, response, retries=0, max_bytes=10 if case == "oversize" else 1024
    )
    b = binding("pdf") if case == "badpdf" else binding()
    with pytest.raises((ValueError, httpx.HTTPError)):
        w.obtain(
            b,
            execute=True,
            license_reviewed=True,
            expected_sha256="f" * 64 if case == "hash" else None,
        )
    assert not w.paths(b)[0].exists()
    assert not list(w.workspace.rglob(".download-*"))
    assert "synthetic-token" not in w.paths(b)[1].read_text()


def test_bounded_backoff(tmp_path):
    sleeps, calls = [], []
    w = worker(tmp_path, lambda r: calls.append(r) or httpx.Response(429), retries=2)
    w.sleep = sleeps.append
    with pytest.raises(httpx.HTTPStatusError):
        w.obtain(binding(), execute=True, license_reviewed=True)
    assert len(calls) == 3 and sleeps == [1, 2]


def test_budget_includes_failed_attempts():
    transport = cli.TransferBudget(
        httpx.MockTransport(lambda r: httpx.Response(200, content=b"1234")), maximum=6
    )
    with httpx.Client(transport=transport) as client:
        assert client.get("https://cs50.harvard.edu/python/").content == b"1234"
        with pytest.raises(ValueError, match="budget"):
            client.get("https://cs50.harvard.edu/python/")


@pytest.fixture
def download_args(scope, monkeypatch):
    monkeypatch.setattr(
        "src.tools_materials.capacity.shutil.disk_usage",
        lambda _: SimpleNamespace(free=100 * 1024**3),
    )
    batch = api.plan(
        scope["batch"].manifest,
        ["cs50_python"],
        [next(b.source_id for b in scope["batch"].materials if b.format == "html")],
        synthetic=True,
    )
    scope["batch"] = batch
    root = scope["tmp"]
    api.output(
        root / "batch.json",
        dict(
            batch=batch.model_dump(mode="json"),
            sha256=api.fingerprint(batch.model_dump(mode="json")),
        ),
    )
    limits = CapacityLimits(
        reserve_bytes=5 * 1024**3,
        archive_bytes=64 * 1024**2,
        job_bytes=512 * 1024**2,
        max_materials=3,
    )
    api.output(root / "limits.json", limits.model_dump(mode="json"))
    api.output(root / "approvals.json", scope["approvals"].model_dump(mode="json"))
    reports = root / "reports"
    reports.mkdir(mode=0o700)
    return SimpleNamespace(
        batch=root / "batch.json",
        limits=root / "limits.json",
        approvals=root / "approvals.json",
        reports=reports,
        archive=scope["archive"],
        confirm=True,
        retry_failed=False,
    )


def test_e2e_download_inventory_parse_results_and_reuse(scope, download_args):
    report, code = cli.download(download_args, transport=scope["transport"])
    assert code == 0 and report["status"] == "completed"
    b = api.reviewed(scope["batch"].materials[0])
    parser = MaterialProcessor(download_args.archive)
    parsed = parser.parse(b, execute=True)
    assert parsed.status == "completed"
    assert parser.inspect(b).normalized_sha256 == parsed.normalized_sha256
    again, code = cli.download(download_args, transport=scope["transport"])
    assert code == 0 and again["materials"][0]["reused"]
    assert len(scope["calls"]) == 1
    documents = [
        json.loads(p.read_text()) for p in download_args.reports.glob("*.json")
    ]
    assert len(documents) == 2 and all(
        d["finished_at"] and d["materials"][0]["bytes"] > 0 for d in documents
    )


def test_cancel_persists_report_requires_explicit_retry(scope, download_args):
    def interrupt(_r):
        raise KeyboardInterrupt

    result, code = cli.download(download_args, transport=httpx.MockTransport(interrupt))
    assert code == 130 and result["status"] == "interrupted"
    assert (
        result["sources"][0]["original_url"] == scope["batch"].materials[0].original_url
    )
    assert not list(download_args.archive.rglob(".download-*"))
    result, code = cli.download(download_args, transport=scope["transport"])
    assert code == 2 and result["status"] == "blocked" and not scope["calls"]
    download_args.retry_failed = True
    assert cli.download(download_args, transport=scope["transport"])[1] == 0


def test_cli_sigterm_and_fresh_invocation(scope, download_args, monkeypatch, capsys):
    import os
    import signal

    def interrupted(_request):
        os.kill(os.getpid(), signal.SIGTERM)
        pytest.fail("SIGTERM must interrupt")

    monkeypatch.setattr(
        cli, "PublicHTTPSTransport", lambda: httpx.MockTransport(interrupted)
    )
    args = ["download"]
    for name in ("batch", "archive", "approvals", "limits", "reports"):
        args += ["--" + name, str(getattr(download_args, name))]
    assert cli.main([*args, "--confirm"]) == 130
    assert json.loads(capsys.readouterr().out)["status"] == "interrupted"
    monkeypatch.setattr(cli, "PublicHTTPSTransport", lambda: scope["transport"])
    assert cli.main([*args, "--confirm"]) == 2
    capsys.readouterr()
    assert cli.main([*args, "--confirm", "--retry-failed"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "completed"


def test_filename_is_never_used(tmp_path):
    w = worker(
        tmp_path,
        lambda r: httpx.Response(
            200,
            content=b"<main>fixture</main>",
            headers={
                "Content-Type": "text/html",
                "Content-Disposition": 'attachment; filename="../../escape"',
            },
        ),
    )
    w.obtain(binding(), execute=True, license_reviewed=True)
    assert not (tmp_path / "escape").exists()
    assert w.paths(binding())[0].name == "source"


def test_tls_verification_rejects_self_signed_certificate(tmp_path):
    key, cert = tmp_path / "synthetic.key", tmp_path / "synthetic.crt"
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-days",
            "1",
            "-subj",
            "/CN=cs50.harvard.edu",
            "-keyout",
            str(key),
            "-out",
            str(cert),
        ],
        check=True,
        capture_output=True,
    )
    transport = net.PublicHTTPSTransport()
    context = transport.inner._pool._ssl_context
    assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
    server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_context.load_cert_chain(cert, key)
    cin, cout, sin, sout = [ssl.MemoryBIO() for _ in range(4)]
    client = context.wrap_bio(cin, cout, server_hostname="cs50.harvard.edu")
    server = server_context.wrap_bio(sin, sout, server_side=True)
    with pytest.raises(ssl.SSLCertVerificationError):
        for _ in range(10):
            for peer, outgoing, incoming in ((client, cout, sin), (server, sout, cin)):
                try:
                    peer.do_handshake()
                except ssl.SSLWantReadError:
                    pass
                incoming.write(outgoing.read())
        pytest.fail("Untrusted certificate accepted")
    transport.close()


def test_systemd_resource_and_network_policy():
    root = Path(__file__).resolve().parents[1] / "deployment/cs50p-mvp"
    for name in ("download", "worker"):
        text = (root / f"cs50p-{name}.service").read_text()
        assert "User=cs50p" in text and "Restart=no" in text
        assert "MemoryMax=" in text and "CPUQuota=" in text and "TasksMax=" in text
        assert "NoNewPrivileges=yes" in text and "KillMode=control-group" in text
        assert "[Install]" not in text
    assert "PrivateNetwork=yes" in (root / "cs50p-worker.service").read_text()
    assert (
        json.loads((root / "controller.json.example").read_text())[
            "deployment_gate_required"
        ]
        is True
    )


def test_native_worker_missing_admission_never_bootstraps_queue(
    tmp_path, monkeypatch, private_umask
):
    from src.job_control.models import Settings

    monkeypatch.setattr(
        "src.tools_materials.capacity.shutil.disk_usage",
        lambda _: SimpleNamespace(free=100 * 1024**3),
    )
    jobs = tmp_path / "jobs"
    jobs.mkdir(mode=0o700)
    settings = Settings(
        root=jobs,
        execution_enabled=True,
        workflows_enabled=True,
        deployment_gate_required=True,
        deployment_gate_protocol="c26-gate-v2",
        max_parallel=1,
        max_queued=1,
    )
    config, limits = tmp_path / "controller.json", tmp_path / "limits.json"
    api.output(config, settings.model_dump(mode="json"))
    api.output(
        limits,
        CapacityLimits(reserve_bytes=5 * 1024**3, job_bytes=512 * 1024**2).model_dump(
            mode="json"
        ),
    )
    assert cli.main(["worker", "--config", str(config), "--limits", str(limits)]) == 2
    assert not (jobs / "jobs.sqlite3").exists()
    assert not list(jobs.glob("deployment-gate*"))
