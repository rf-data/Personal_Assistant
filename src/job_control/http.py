"""Bounded local JSON HTTP adapter; no file serving, proxy roles or executor."""

import json
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

from pydantic import ValidationError

from src.job_control.controller import AuthenticationError
from src.job_control.store import Conflict, Unavailable


def encode(value):
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    if isinstance(value, (list, tuple)):
        value = [
            v.model_dump(mode="json") if hasattr(v, "model_dump") else v for v in value
        ]
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    ).encode()


class Application:
    def __init__(self, controller):
        self.controller = controller

    def request(self, method, target, headers, body=b""):
        try:
            actor = self.controller.authenticate(headers.get("Authorization"))
            parts = urlsplit(target)
            if (
                parts.scheme
                or parts.netloc
                or len(target) > 2048
                or "%" in parts.path
                or ".." in parts.path
                or "\\" in parts.path
            ):
                raise ValueError("Invalid route")
            route = parts.path.rstrip("/").split("/")
            if route[:2] != ["", "v1"]:
                raise KeyError("Unknown API version/route")
            if len(body) > 32768:
                raise ValueError("Request limit")
            value = json.loads(body) if body else {}
            if not isinstance(value, dict):
                raise ValueError("Expected JSON object")
            query = parse_qs(parts.query, strict_parsing=True) if parts.query else {}
            if any(len(v) != 1 for v in query.values()):
                raise ValueError("Duplicate query parameters")
            query = {k: v[0] for k, v in query.items()}
            if method == "GET" and route[2:] == ["processes"]:
                result = self.controller.processes(actor)
            elif method == "GET" and route[2:] == ["capabilities"]:
                result = {
                    **self.controller.processes(actor),
                    "protocol": "personal_assistant_jobs_v1",
                    "ui_contract": "C14 mapping required",
                }
            elif method == "POST" and route[2:] == ["previews"]:
                result = self.controller.preview(actor, value)
            elif method == "POST" and route[2:] == ["jobs"]:
                result = self.controller.create(
                    actor, value, headers.get("Idempotency-Key")
                )
            elif method == "GET" and route[2:] == ["jobs"]:
                allowed = {"limit", "offset", "process_id", "status", "course_id"}
                if set(query) - allowed:
                    raise ValueError("Unknown history filter")
                result = self.controller.history(
                    actor,
                    **{
                        k: int(v) if k in {"limit", "offset"} else v
                        for k, v in query.items()
                    },
                )
            elif len(route) in {4, 5} and route[2] == "jobs":
                job_id = route[3]
                job = self.controller.get(actor, job_id)
                action = route[4] if len(route) == 5 else None
                if method == "GET" and action is None:
                    result = job
                elif method == "GET" and action == "artifacts":
                    result = job.artifact_refs
                elif method == "GET" and action == "logs":
                    if set(query) - {"cursor", "limit", "query"}:
                        raise ValueError("Unknown log filter")
                    result = self.controller.store.logs(
                        job_id,
                        cursor=int(query.get("cursor", 0)),
                        limit=int(query.get("limit", 100)),
                        query=query.get("query", ""),
                    )
                elif method == "POST" and action == "cancel":
                    if value:
                        raise ValueError("Cancel takes no process/PID parameters")
                    result = self.controller.cancel(actor, job_id)
                elif method == "POST" and action == "start":
                    if value:
                        raise ValueError("Start takes no replacement parameters")
                    result = self.controller.start(actor, job_id)
                else:
                    raise KeyError("Unknown method/action")
            elif method == "GET" and route[2:] == ["metrics"]:
                from src.job_control.metrics import render_metrics

                return (
                    200,
                    render_metrics(
                        self.controller.store,
                        self.controller.settings.worker_ttl,
                        actor.courses,
                    ).encode(),
                    "text/plain; version=0.0.4",
                )
            else:
                raise KeyError("Unknown method/route")
            return (
                (202 if method == "POST" and "jobs" in route else 200),
                encode(result),
                "application/json",
            )
        except AuthenticationError:
            code, status = "unauthenticated", 401
        except PermissionError:
            code, status = "forbidden", 403
        except Conflict:
            code, status = "conflict", 409
        except KeyError:
            code, status = "not_found", 404
        except (ValidationError, ValueError, TypeError):
            code, status = "invalid_request", 422
        except (Unavailable, sqlite3.Error, OSError):
            code, status = "unavailable", 503
        except Exception:
            code, status = "internal_error", 500
        return (
            status,
            encode(
                dict(
                    schema_version=1,
                    error=dict(code=code, message=code.replace("_", " ")),
                )
            ),
            "application/json",
        )


def handler_for(application):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"
        server_version = "PersonalAssistantJobs/1"
        sys_version = ""

        def setup(self):
            self.request.settimeout(3)
            super().setup()

        def log_message(self, *args):
            pass  # Do not log authorization, URLs, arbitrary request text or source bytes.

        def handle_request(self):
            lengths = self.headers.get_all("Content-Length", [])
            if self.headers.get("Transfer-Encoding") or len(lengths) > 1:
                self.send_error(400)
                return
            try:
                length = int(lengths[0]) if lengths else 0
                if not 0 <= length <= 32768:
                    raise ValueError
                if (
                    self.command == "POST"
                    and self.headers.get_content_type() != "application/json"
                ):
                    self.send_error(415)
                    return
                if len(self.headers.get_all("Authorization", [])) != 1:
                    self.send_error(401)
                    return
                body = self.rfile.read(length)
                if len(body) != length:
                    raise ValueError
                status, data, mime = application.request(
                    self.command, self.path, self.headers, body
                )
            except (ValueError, TimeoutError, OSError):
                self.send_error(400)
                return
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(data)

        do_GET = handle_request
        do_POST = handle_request

        def send_error(self, code, message=None, explain=None):
            data = encode(
                dict(
                    schema_version=1,
                    error=dict(code="http_rejected", message="HTTP request rejected"),
                )
            )
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(data)

    return Handler


def serve(controller, port=8016):
    # Deliberately no configurable wildcard/public binding in this local transport.
    with HTTPServer(
        ("127.0.0.1", port), handler_for(Application(controller))
    ) as server:
        server.serve_forever()
