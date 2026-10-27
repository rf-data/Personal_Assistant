"""Bounded local JSON HTTP adapter; no file serving, proxy roles or executor."""

import json
import sqlite3
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

from pydantic import ValidationError

from src.job_control.controller import AuthenticationError
from src.job_control.store import Conflict, Quarantined, Unavailable


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
    def __init__(
        self,
        controller,
        *,
        content_settings=None,
        review_settings=None,
        search_settings=None,
    ):
        self.controller = controller
        from src.content_store.http import ContentHTTP

        if content_settings is not None:
            root = controller.settings.root
            if (
                content_settings.root.is_relative_to(root)
                or root.is_relative_to(content_settings.root)
                or content_settings.cursor_key_file.is_relative_to(root)
            ):
                raise ValueError("Content and job configuration must be separate")
        self.content = ContentHTTP(content_settings)
        from src.evaluation_store.http import ReviewHTTP

        if review_settings is not None:
            root = controller.settings.root
            if any(
                p.is_relative_to(root) or root.is_relative_to(p)
                for p in (review_settings.root, review_settings.content.root)
            ):
                raise ValueError("Review, Content and job roots must be separate")
        self.review = ReviewHTTP(review_settings)
        from src.content_store.search_http import SearchHTTP

        if search_settings is not None:
            if content_settings is None:
                raise ValueError("Search requires explicit content configuration")
            index_root = search_settings.index_root
            roots = [controller.settings.root, content_settings.root]
            if review_settings is not None:
                roots.append(review_settings.root)
            if any(
                index_root.is_relative_to(p) or p.is_relative_to(index_root)
                for p in roots
            ):
                raise ValueError("Search index must be separate from managed data")
            if content_settings.cursor_key_file.is_relative_to(index_root):
                raise ValueError("Search cursor key must be outside index data")
        self.search = SearchHTTP(self.content, search_settings)
        from src.job_control.index_http import IndexHTTP

        if controller.settings.index_jobs_enabled and (
            content_settings is None or search_settings is None
        ):
            raise ValueError(
                "Index jobs require the integrated content/search configuration"
            )
        self.index = IndexHTTP(controller, content_settings, search_settings)
        from src.job_control.import_http import ImportHTTP

        if controller.settings.import_jobs_enabled and content_settings is None:
            raise ValueError("Imports require explicit content configuration")
        self.imports = ImportHTTP(controller, content_settings)

    def request(self, method, target, headers, body=b""):
        try:
            actor = self.controller.authenticate(headers.get("Authorization"))
            parts = urlsplit(target)
            if parts.path == "/v1/evaluation" or parts.path.startswith(
                "/v1/evaluation/"
            ):
                if (
                    parts.scheme
                    or parts.netloc
                    or len(target) > 2048
                    or len(body) > 32768
                ):
                    raise ValueError("Invalid route")
                return self.review.request(method, parts, body, actor)
            if parts.path == "/v1/content" or parts.path.startswith("/v1/content/"):
                if (
                    parts.scheme
                    or parts.netloc
                    or len(target) > 2048
                    or len(body) > 32768
                ):
                    raise ValueError("Invalid route")
                if parts.path == "/v1/content/search" or parts.path.startswith(
                    "/v1/content/search/"
                ):
                    return self.search.request(method, parts, body, actor)
                if parts.path == "/v1/content/import" or parts.path.startswith(
                    "/v1/content/import/"
                ):
                    return self.imports.request(method, parts, body, actor)
                if parts.path == "/v1/content/index" or parts.path.startswith(
                    "/v1/content/index/"
                ):
                    return self.index.request(method, parts, body, actor)
                return self.content.request(method, parts, body, actor)
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
            scoped_job = None
            if route[2:3] == ["workflows"]:
                from src.workflows.http import WorkflowHTTP

                workflows = WorkflowHTTP(self.controller)
                action = route[3] if len(route) == 4 else None
                if method == "GET" and len(route) == 6 and route[4] == "runs":
                    if value or set(query) != {"source_ref"}:
                        raise ValueError("Run report requires only source_ref")
                    result = workflows.run_report(
                        actor, route[3], route[5], query["source_ref"]
                    )
                elif (
                    method == "GET"
                    and action == "capabilities"
                    and "source_ref" not in query
                ):
                    if query or value:
                        raise ValueError("Capabilities takes no parameters")
                    result = workflows.capabilities()
                elif method == "POST" and action in {"inspect", "execute", "resume"}:
                    if query:
                        raise ValueError("Workflow POST takes no query")
                    if action == "inspect":
                        result = workflows.read(actor, value)
                    else:
                        result = workflows.submit(
                            actor,
                            value,
                            headers.get("Idempotency-Key"),
                            resume=action == "resume",
                        )
                elif method == "GET" and action:
                    if (
                        value
                        or "source_ref" not in query
                        or set(query) - {"source_ref", "offset", "limit"}
                    ):
                        raise ValueError("Invalid workflow status parameters")
                    result = workflows.read(
                        actor,
                        dict(workflow_id=action, source_ref=query["source_ref"]),
                        offset=int(query.get("offset", 0)),
                        limit=int(query.get("limit", 10)),
                    )
                else:
                    raise KeyError("Unknown workflow method/route")
                data = encode(result)
                if len(data) > 524288:
                    raise Unavailable("Workflow response limit")
                return (
                    202
                    if method == "POST" and action in {"execute", "resume"}
                    else 200,
                    data,
                    "application/json",
                )
            elif method == "GET" and route[2:] == ["processes"]:
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
                if job.process_id in {"content_index_build", "content_import"}:
                    scoped_job = job
                action = route[4] if len(route) == 5 else None
                if method == "GET" and action is None:
                    result = job
                elif method == "GET" and action == "artifacts":
                    result = job.artifact_refs
                elif method == "GET" and action == "result":
                    if query or value:
                        raise ValueError("Planning result takes no parameters")
                    result = self.controller.planning_result(actor, job_id)
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
            from src.content_store.errors import ContentStoreError, Forbidden, NotFound
            from src.job_control.index_jobs import guarded_reply

            try:
                guarded = guarded_reply(
                    self.controller,
                    actor,
                    result,
                    202 if method == "POST" and "jobs" in route else 200,
                    scoped_job=scoped_job,
                )
            except (Forbidden, NotFound):
                raise KeyError("Index job unavailable") from None
            except ContentStoreError:
                raise Unavailable("Index status unavailable") from None
            if guarded is not None:
                return guarded
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
        except Quarantined:
            code, status = "quarantined", 423
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
                response = application.request(
                    self.command, self.path, self.headers, body
                )
                status, data, mime = response
            except (ValueError, TimeoutError, OSError):
                self.send_error(400)
                return
            from src.content_store.errors import ContentStoreError
            from src.content_store.reader import Download

            try:
                deadline = getattr(response, "deadline", time.monotonic() + 15)
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError
                self.connection.settimeout(min(3, remaining))
                self.send_response(status)
                self.send_header("Content-Type", mime)
                self.send_header(
                    "Content-Length",
                    str(data.size if isinstance(data, Download) else len(data)),
                )
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Connection", "close")
                for key, value in getattr(response, "headers", {}).items():
                    self.send_header(key, value)
                self.end_headers()
                if isinstance(data, Download):
                    while chunk := data.stream.read(65536):
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            raise TimeoutError
                        self.connection.settimeout(min(3, remaining))
                        self.wfile.write(chunk)
                else:
                    for offset in range(0, len(data), 65536):
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            raise TimeoutError
                        self.connection.settimeout(min(3, remaining))
                        self.wfile.write(data[offset : offset + 65536])
            except (OSError, TimeoutError):
                self.close_connection = True
            finally:
                if isinstance(data, Download):
                    data.close()
                close = getattr(response, "close", None)
                if close is not None:
                    try:
                        close()
                    except (ContentStoreError, OSError):
                        self.close_connection = True

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


def serve(
    controller,
    port=8016,
    *,
    content_settings=None,
    review_settings=None,
    search_settings=None,
):
    # Deliberately no configurable wildcard/public binding in this local transport.
    with HTTPServer(
        ("127.0.0.1", port),
        handler_for(
            Application(
                controller,
                content_settings=content_settings,
                review_settings=review_settings,
                search_settings=search_settings,
            )
        ),
    ) as server:
        server.serve_forever()
