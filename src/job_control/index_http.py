"""Scoped index status and approved inputs in the existing C16 gateway."""

import time
from contextlib import ExitStack
from urllib.parse import parse_qs

from src.content_store.errors import ContentStoreError, Forbidden, NotFound
from src.content_store.http import Reply
from src.content_store.models import canonical
from src.content_store.read_models import MAX_PAGE
from src.content_store.reader import ReadFault
from src.content_store.search_http import SearchReply
from src.job_control.index_jobs import input_view, plan, status
from src.job_control.store import Unavailable


class IndexHTTP:
    def __init__(self, controller, content_settings, search_settings):
        self.controller = controller
        self.content, self.search = content_settings, search_settings

    def _plan(self, ref):
        entry = self.controller.settings.catalog.get(ref)
        if entry is None or entry.kind != "index_bundle":
            raise NotFound()
        spec = plan(entry, self.controller.settings.root)
        if spec.content != self.content or spec.search != self.search:
            raise NotFound()
        return spec

    def request(self, method, parts, body, actor):
        stack = ExitStack()
        try:
            if method != "GET":
                raise ReadFault(405, "method_not_allowed")
            if body or parts.fragment:
                raise ReadFault(422, "invalid_request")
            enabled = bool(
                self.controller.settings.index_jobs_enabled
                and self.content
                and self.search
            )
            if parts.path == "/v1/content/index/capabilities":
                if parts.query:
                    raise ReadFault(422, "invalid_request")
                return Reply(
                    200,
                    canonical(
                        dict(
                            schema_version=1,
                            enabled=enabled,
                            process_id="content_index_build",
                            max_inputs_page=10,
                            max_jobs_page=20,
                            max_versions=32,
                            retry_policy="explicit_new_request_only",
                        )
                    ),
                )
            if not enabled:
                raise ReadFault(503, "unavailable")
            query = (
                parse_qs(
                    parts.query,
                    strict_parsing=True,
                    keep_blank_values=True,
                    max_num_fields=3,
                )
                if parts.query
                else {}
            )
            if any(len(v) != 1 for v in query.values()) or set(query) - {
                "input_ref",
                "offset",
                "limit",
            }:
                raise ReadFault(422, "invalid_request")
            query = {k: v[0] for k, v in query.items()}
            if any(
                not v.isascii() or not v.isdecimal()
                for k, v in query.items()
                if k in {"offset", "limit"}
            ):
                raise ReadFault(422, "invalid_request")
            offset, limit = int(query.get("offset", 0)), int(query.get("limit", 10))
            if not 0 <= offset <= 1000 or not 1 <= limit <= 20:
                raise ReadFault(422, "invalid_request")
            if parts.path == "/v1/content/index/inputs":
                if "input_ref" in query or limit > 10:
                    raise ReadFault(422, "invalid_request")
                from src.content_store.store import ContentStore
                from src.tools_rag.content_index import ContentIndex

                index = ContentIndex(
                    ContentStore(self.content.root),
                    self.search.index_root,
                    cursor_key_file=self.content.cursor_key_file,
                )
                stack.enter_context(index.files.lock(".content-index-catalog.lock"))
                stack.enter_context(index.store._maintenance())
                stack.enter_context(index.store._connection())
                items = []
                for ref, entry in self.controller.settings.catalog.items():
                    if entry.kind != "index_bundle":
                        continue
                    try:
                        items.append(input_view(ref, self._plan(ref), actor))
                    except (ContentStoreError, ValueError, OSError):
                        continue
                items.sort(key=lambda x: x.input_ref)
                page = dict(
                    schema_version=1,
                    items=[
                        x.model_dump(mode="json")
                        for x in items[offset : offset + limit]
                    ],
                    next_offset=offset + limit if len(items) > offset + limit else None,
                )
            elif parts.path == "/v1/content/index/status":
                ref = query.get("input_ref")
                if not ref:
                    raise ReadFault(422, "invalid_request")
                self._plan(ref)
                answer = stack.enter_context(
                    status(self.controller, ref, actor, offset=offset, limit=limit)
                )
                page = answer.model_dump(mode="json")
            else:
                raise NotFound()
            deadline = time.monotonic() + 2
            raw = canonical(page)
            if len(raw) > MAX_PAGE:
                raise ReadFault(503, "unavailable")
            return SearchReply(200, raw, deadline=deadline, stack=stack.pop_all())
        except ReadFault as error:
            code, status_code = error.code, error.status
        except (Forbidden, NotFound, PermissionError, KeyError):
            code, status_code = "not_found", 404
        except (ValueError, TypeError):
            code, status_code = "invalid_request", 422
        except (ContentStoreError, Unavailable, OSError):
            code, status_code = "unavailable", 503
        finally:
            stack.close()
        return Reply(
            status_code,
            canonical(
                dict(
                    schema_version=1,
                    error=dict(code=code, message=code.replace("_", " ")),
                )
            ),
            headers={"Allow": "GET"} if status_code == 405 else {},
        )
