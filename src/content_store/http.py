"""Content routes inside the authenticated C16 gateway, not another server."""

import re
from dataclasses import dataclass, field
from urllib.parse import parse_qs, unquote_to_bytes

from src.content_store.errors import ContentStoreError, Forbidden, NotFound
from src.content_store.models import canonical
from src.content_store.read_models import MAX_ATTACHMENT, MAX_PAGE, ContentCapabilities
from src.content_store.reader import ContentReader, ReadFault


@dataclass
class Reply:
    status: int
    data: object
    mime: str = "application/json"
    headers: dict[str, str] = field(default_factory=dict)

    def __iter__(self):
        return iter((self.status, self.data, self.mime))


class ContentHTTP:
    def __init__(self, settings=None):
        self.settings = settings
        self.reader = None

    def _reader(self):
        if self.settings is None:
            raise ReadFault(503, "unavailable")
        if self.reader is None:
            try:
                self.reader = ContentReader(self.settings)
            except (ContentStoreError, OSError, ValueError):
                raise ReadFault(503, "unavailable") from None
        return self.reader

    def capabilities(self):
        try:
            reader = self._reader()
            with reader.store._maintenance(), reader.store._connection():
                pass
            enabled = True
        except (ContentStoreError, ReadFault, OSError, ValueError):
            enabled = False
        return ContentCapabilities(
            enabled=enabled, capabilities=("content_read_v1",) if enabled else ()
        )

    @staticmethod
    def _route(path):
        if "\\" in path or re.search(r"%(?![0-9a-fA-F]{2})", path):
            raise ReadFault(400, "invalid_route")
        output = []
        for part in path.split("/")[3:]:
            try:
                value = unquote_to_bytes(part).decode("ascii")
            except (ValueError, UnicodeError):
                raise ReadFault(400, "invalid_route") from None
            if (
                not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_:.-]{0,199}", value)
                or ".." in value
            ):
                raise ReadFault(400, "invalid_route")
            output.append(value)
        return output

    def request(self, method, parts, body, actor):
        try:
            if method != "GET":
                raise ReadFault(405, "method_not_allowed")
            if body:
                raise ReadFault(422, "invalid_request")
            if parts.fragment:
                raise ReadFault(400, "invalid_route")
            route = self._route(parts.path)
            values = (
                parse_qs(
                    parts.query,
                    strict_parsing=True,
                    keep_blank_values=True,
                    max_num_fields=8,
                )
                if parts.query
                else {}
            )
            if any(len(v) != 1 for v in values.values()):
                raise ReadFault(400, "invalid_parameter")
            query = {k: v[0] for k, v in values.items()}
            if route == ["capabilities"]:
                if query:
                    raise ReadFault(400, "invalid_parameter")
                return Reply(
                    200, canonical(self.capabilities().model_dump(mode="json"))
                )
            reader = self._reader()
            attachment = False
            if len(route) == 3 and route[0] == "sources" and route[2] == "status":
                from src.content_store.source_status import status_reply

                return status_reply(reader, route[1], query, actor)
            if route == ["sources"]:
                from src.content_store.source_status import sources_reply

                return sources_reply(reader, query, actor)
            elif len(route) == 2 and route[0] == "sources":
                if query:
                    raise ReadFault(400, "invalid_parameter")
                result = reader.source(route[1], actor)
            elif len(route) == 3 and route[0] == "sources" and route[2] == "versions":
                result = reader.page("versions", (route[1],), query, actor)
            elif (
                len(route) == 5
                and route[0] == "sources"
                and route[2] == "versions"
                and route[4] == "parsed"
            ):
                result = reader.page("parsed_refs", (route[1], route[3]), query, actor)
            elif (
                len(route) == 7
                and route[0] == "sources"
                and route[2] == "versions"
                and route[4] == "raw"
            ):
                if query:
                    raise ReadFault(400, "invalid_parameter")
                if not re.fullmatch(r"[0-9]{1,3}", route[6]):
                    raise ReadFault(400, "invalid_parameter")
                download = reader.download(
                    route[1], route[3], route[5], int(route[6]), actor
                )
                return Reply(
                    200,
                    download,
                    download.mime,
                    {
                        "Content-Disposition": f'attachment; filename="{download.filename}"'
                    },
                )
            elif len(route) == 2 and route[0] == "parsed":
                if query:
                    raise ReadFault(400, "invalid_parameter")
                result = reader.parsed(route[1], actor)
            elif len(route) == 3 and route[0] == "parsed" and route[2] == "blocks":
                result = reader.page("blocks", (route[1],), query, actor)
            elif (
                len(route) == 5
                and route[0] == "parsed"
                and route[2] == "blocks"
                and route[4] in {"text", "structure"}
            ):
                attachment = route[4] == "structure"
                result = reader.block(
                    route[1], route[3], actor, query, structured=attachment
                )
            else:
                raise NotFound()
            data = canonical(result.model_dump(mode="json"))
            if len(data) > (MAX_ATTACHMENT if attachment else MAX_PAGE):
                raise ReadFault(503, "unavailable")
            return Reply(
                200,
                data,
                headers={
                    "Content-Disposition": 'attachment; filename="content-structure.v1.json"'
                }
                if attachment
                else {},
            )
        except ReadFault as error:
            status, code = error.status, error.code
        except (NotFound, Forbidden):
            status, code = 404, "not_found"
        except ContentStoreError:
            status, code = 503, "unavailable"
        except (ValueError, TypeError):
            status, code = 400, "invalid_request"
        except OSError:
            status, code = 503, "unavailable"
        return Reply(
            status,
            canonical(
                dict(
                    schema_version=1,
                    error=dict(code=code, message=code.replace("_", " ")),
                )
            ),
            headers={"Allow": "GET"} if status == 405 else {},
        )
