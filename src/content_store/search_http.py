"""Read-only C16 search adapter. Keep the retrieval guard through HTTP delivery."""

import time
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from src.content_store.errors import Busy, ContentStoreError, Forbidden, NotFound
from src.content_store.http import Reply
from src.content_store.models import canonical
from src.content_store.read_models import MAX_PAGE
from src.content_store.reader import ReadFault, private_bytes
from src.content_store.search_models import (
    SearchCapabilities,
    SearchRequest,
    SearchSettings,
)
from src.tools_materials.quality import _json
from src.tools_rag.content_index import ContentIndex, RetrievalFault


def load_search_settings(path):
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("explicit private search configuration required")
    return SearchSettings.model_validate(_json(private_bytes(path, 8192)))


@dataclass
class SearchReply(Reply):
    deadline: float = 0
    stack: ExitStack | None = field(default=None, repr=False)

    def close(self):
        stack, self.stack = self.stack, None
        if stack is not None:
            stack.close()


class SearchHTTP:
    def __init__(self, content, settings=None):
        self.content, self.settings = content, settings

    def _index(self):
        if self.settings is None:
            raise ReadFault(503, "unavailable")
        reader = self.content._reader()
        # Open existing roots only. Reload the private key; never cache authorization,
        # active generations, result pages or cursor acceptance between requests.
        return ContentIndex(
            reader.store,
            self.settings.index_root,
            cursor_key_file=self.content.settings.cursor_key_file,
        )

    def request(self, method, parts, body, actor):
        stack = ExitStack()
        try:
            if parts.query or parts.fragment:
                raise ReadFault(422, "invalid_request")
            if parts.path == "/v1/content/search/capabilities":
                if method != "GET":
                    raise ReadFault(405, "method_not_allowed")
                if body:
                    raise ReadFault(422, "invalid_request")
                try:
                    index = self._index()
                    with index.store._maintenance(), index.store._connection():
                        pass
                    enabled = True
                except (ContentStoreError, ReadFault, OSError, ValueError):
                    enabled = False
                return Reply(
                    200,
                    canonical(
                        SearchCapabilities(
                            enabled=enabled,
                            capabilities=("content_search_lexical_v1",)
                            if enabled
                            else (),
                        ).model_dump(mode="json")
                    ),
                )
            if parts.path != "/v1/content/search":
                raise ReadFault(404, "not_found")
            if method != "POST":
                raise ReadFault(405, "method_not_allowed")
            if len(body) > 32768:
                raise ReadFault(422, "invalid_request")
            request = SearchRequest.model_validate(_json(body))
            if not actor.courses:
                raise ReadFault(403, "search_scope_denied")
            index = self._index()
            page = stack.enter_context(
                index.search_lexical(
                    request.query,
                    actor=actor,
                    course_id=request.course_id,
                    source_ids=request.source_ids,
                    content_types=request.content_types,
                    limit=request.limit,
                    cursor=request.cursor,
                )
            )
            # Serialization consumes the delivery budget too; do not restart the
            # retrieval guard's finite response window after encoding a page.
            deadline = time.monotonic() + 2
            data = canonical(page.model_dump(mode="json"))
            if len(data) > MAX_PAGE:
                raise ReadFault(503, "unavailable")
            return SearchReply(200, data, deadline=deadline, stack=stack.pop_all())
        except RetrievalFault as error:
            code = error.code
            status = 409 if code in {"snapshot_changed", "stale_index"} else 422
        except ReadFault as error:
            status, code = error.status, error.code
        except (Forbidden, NotFound):
            status, code = 404, "not_found"
        except Busy:
            status, code = 503, "busy"
        except (ValidationError, ValueError, TypeError, RecursionError):
            status, code = 422, "invalid_request"
        except (ContentStoreError, OSError):
            status, code = 503, "unavailable"
        finally:
            stack.close()
        allowed = "GET" if parts.path.endswith("/capabilities") else "POST"
        return Reply(
            status,
            canonical(
                dict(
                    schema_version=1,
                    error=dict(code=code, message=code.replace("_", " ")),
                )
            ),
            headers={"Allow": allowed} if status == 405 else {},
        )
