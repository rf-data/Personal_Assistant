"""Opt-in human review capability inside the existing authenticated gateway."""

from pathlib import Path
from urllib.parse import parse_qs

from pydantic import TypeAdapter, ValidationError

from src.content_store.errors import (
    Busy,
    Conflict,
    ContentStoreError,
    Forbidden,
    InvalidInput,
    NotFound,
)
from src.content_store.http import Reply
from src.content_store.models import canonical
from src.content_store.reader import ReadFault, private_bytes
from src.evaluation_store.models import (
    Acceptance,
    Assignment,
    CreateDataset,
    CreateTask,
    Decision,
    Draft,
    EvaluationRequest,
    Mutation,
    PoolConfirmation,
    ReviewSettings,
)
from src.evaluation_store.service import ReviewService
from src.job_control.models import Identifier
from src.tools_materials.quality import _json


def load_review_settings(path):
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("explicit private review configuration required")
    return ReviewSettings.model_validate_json(private_bytes(path, 32768))


class ReviewHTTP:
    def __init__(self, settings=None):
        self.settings = settings
        self.service = None

    def request(self, method, parts, body, actor):
        try:
            if (
                parts.fragment
                or "%" in parts.path
                or "\\" in parts.path
                or ".." in parts.path
            ):
                raise InvalidInput()
            if (
                parts.path == "/v1/evaluation/capabilities"
                and method == "GET"
                and not body
                and not parts.query
            ):
                return Reply(
                    200,
                    canonical(
                        dict(
                            schema_version=1,
                            enabled=self.settings is not None,
                            writes_enabled=bool(
                                self.settings and self.settings.writes_enabled
                            ),
                        )
                    ),
                )
            if self.settings is None:
                return Reply(
                    503,
                    canonical(dict(schema_version=1, error={"code": "unavailable"})),
                )
            route = parts.path.split("/")[3:]
            if len(route) < 2 or route[0] != "datasets":
                raise NotFound()
            did = TypeAdapter(Identifier).validate_python(route[1])
            query = (
                parse_qs(
                    parts.query,
                    strict_parsing=True,
                    max_num_fields=1,
                    keep_blank_values=True,
                )
                if parts.query
                else {}
            )
            if set(query) - {"offset"} or any(len(v) != 1 for v in query.values()):
                raise InvalidInput()
            offset = int(query.get("offset", ["0"])[0])
            if not 0 <= offset <= 1000:
                raise InvalidInput()
            tail = route[2:]
            item = None
            model = None
            if method == "POST" and not tail:
                action, model = "create", CreateDataset
            elif tail == ["tasks"]:
                action, model = (
                    ("task", CreateTask) if method == "POST" else ("list", None)
                )
            elif len(tail) in {2, 3} and tail[0] == "tasks":
                item = TypeAdapter(Identifier).validate_python(tail[1])
                action = tail[2] if len(tail) == 3 else "get"
                model = {
                    "assign": Assignment,
                    "draft": Draft,
                    "decision": Decision,
                }.get(action)
                if action not in {
                    "get",
                    "region",
                    "raw",
                    "revisions",
                    "assign",
                    "draft",
                    "decision",
                }:
                    raise NotFound()
            elif tail == ["pool"]:
                action, model = "pool", PoolConfirmation
            elif len(tail) == 2 and tail[0] in {"exports", "reports", "acceptances"}:
                item = TypeAdapter(Identifier).validate_python(tail[1])
                action, model = {
                    "exports": ("export", Mutation),
                    "reports": ("evaluate", EvaluationRequest),
                    "acceptances": ("accept", Acceptance),
                }[tail[0]]
                if method == "GET":
                    action, model = (
                        {
                            "export": "export_read",
                            "evaluate": "report_read",
                            "accept": "accept_read",
                        }[action],
                        None,
                    )
            else:
                raise NotFound()
            if (model is not None and method != "POST") or (
                model is None and method != "GET"
            ):
                raise InvalidInput()
            if query and action not in {"list", "revisions"}:
                raise InvalidInput()
            if model is None and body:
                raise InvalidInput()
            request = model.model_validate(_json(body)) if model else None
            if self.service is None:
                self.service = ReviewService(self.settings)
            data, mime = self.service.call(
                did, action, actor, request, item=item, offset=offset
            )
            return Reply(
                200,
                data,
                mime,
                {"Content-Disposition": 'attachment; filename="original-source"'}
                if action == "raw"
                else {},
            )
        except (NotFound, Forbidden):
            status, code = 404, "not_found"
        except Conflict:
            status, code = 409, "conflict"
        except (InvalidInput, ValidationError, ValueError, TypeError):
            status, code = 422, "invalid_request"
        except Busy:
            status, code = 503, "busy"
        except (ContentStoreError, ReadFault, OSError):
            status, code = 503, "unavailable"
        return Reply(status, canonical(dict(schema_version=1, error={"code": code})))
