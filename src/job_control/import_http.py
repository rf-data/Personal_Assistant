"""Authenticated import selection/plan; actual writes stay in the C16 worker."""

import time
from contextlib import ExitStack
from urllib.parse import parse_qs

from src.content_store.errors import (
    ContentStoreError,
    Forbidden,
    IntegrityError,
    NotFound,
)
from src.content_store.http import Reply
from src.content_store.models import canonical, sha256
from src.content_store.reader import ContentReader, ReadFault
from src.content_store.search_http import SearchReply
from src.content_store.store import ContentStore
from src.job_control.catalog import read_file, safe_path
from src.job_control.import_jobs import PROCESS, authorize, inspect, plan, state
from src.job_control.import_models import ImportPreview, ImportReceipt
from src.job_control.models import ContentImportParams
from src.tools_materials.quality import _json


class ImportHTTP:
    def __init__(self, controller, content_settings):
        self.controller, self.content = controller, content_settings

    def _spec(self, ref, actor):
        entry = self.controller.settings.catalog.get(ref)
        if entry is None or entry.kind != "content_import_bundle":
            raise NotFound()
        spec = plan(entry, self.controller.settings.root)
        if spec.content != self.content:
            raise NotFound()
        with ContentStore(spec.content.root)._connection() as db:
            authorize(spec, actor, db)
        return entry, spec

    def request(self, method, parts, body, actor):
        stack = ExitStack()
        try:
            if parts.fragment:
                raise ReadFault(422, "invalid_request")
            enabled = bool(
                self.controller.settings.import_jobs_enabled and self.content
            )
            if parts.path == "/v1/content/import/capabilities":
                if method != "GET" or body or parts.query:
                    raise ReadFault(422, "invalid_request")
                return Reply(
                    200,
                    canonical(
                        dict(
                            schema_version=1,
                            enabled=enabled,
                            process_id=PROCESS,
                            adapters=["material", "srt"],
                            raw_only_pdf=False,
                            real_sources=False,
                            max_inputs_page=10,
                        )
                    ),
                )
            if not enabled:
                raise ReadFault(503, "unavailable")
            if parts.path == "/v1/content/import/result":
                if method != "GET" or body:
                    raise ReadFault(422, "invalid_request")
                query = parse_qs(parts.query, strict_parsing=True, max_num_fields=1)
                if set(query) != {"job_id"} or len(query["job_id"]) != 1:
                    raise ReadFault(422, "invalid_request")
                job = self.controller.get(actor, query["job_id"][0])
                if job.process_id != PROCESS:
                    raise NotFound()
                _, spec = self._spec(job.input_refs[0], actor)
                if not job.artifact_refs:
                    raise ReadFault(409, "publication_not_determined")
                if (
                    len(job.artifact_refs) != 1
                    or job.artifact_refs[0].kind != "content_import"
                ):
                    raise IntegrityError("import receipt kind")
                artifact = job.artifact_refs[0]
                data = read_file(
                    safe_path(
                        self.controller.store.directory(job.job_id),
                        "results/" + job.parameters["output_name"] + ".json",
                    )
                )
                if sha256(data) != artifact.sha256 or len(data) != artifact.size_bytes:
                    raise IntegrityError("import receipt bytes")
                receipt = ImportReceipt.model_validate(_json(data))
                if (
                    receipt.job_id != job.job_id
                    or receipt.source_id != spec.selection.source_id
                ):
                    raise IntegrityError("import receipt identity")
                store = ContentStore(spec.content.root)
                stack.enter_context(store._maintenance())
                db = stack.enter_context(store._connection())
                authorize(spec, actor, db, job_owner=job.initiated_by)
                version, sv = ContentReader(self.content)._parsed(
                    db, receipt.parsed_version_id, actor
                )
                if (
                    version.source_id != receipt.source_id
                    or version.source_version_id != receipt.source_version_id
                    or version.payload.sha256 != receipt.payload_sha256
                ):
                    raise IntegrityError("import receipt publication")
                if receipt.raw_sha256 not in {a.sha256 for a in sv.manifest.artifacts}:
                    raise IntegrityError("import receipt raw")
                result = receipt.model_dump(mode="json")
            elif parts.path == "/v1/content/import/inputs":
                if method != "GET" or body:
                    raise ReadFault(422, "invalid_request")
                query = (
                    parse_qs(parts.query, strict_parsing=True, max_num_fields=1)
                    if parts.query
                    else {}
                )
                if set(query) - {"offset"} or any(len(v) != 1 for v in query.values()):
                    raise ReadFault(422, "invalid_request")
                offset = int(query.get("offset", ["0"])[0])
                if not 0 <= offset <= 1000:
                    raise ReadFault(422, "invalid_request")
                rows = []
                # Metadata only: heavy gate verification is an explicit preview action.
                for ref, entry in self.controller.settings.catalog.items():
                    if entry.kind != "content_import_bundle":
                        continue
                    try:
                        _, spec = self._spec(ref, actor)
                        rows.append(
                            dict(
                                input_ref=ref,
                                source_id=spec.selection.source_id,
                                course_id=spec.selection.course_id,
                                adapter=spec.selection.kind,
                            )
                        )
                    except (ContentStoreError, ValueError, OSError):
                        continue
                rows.sort(key=lambda r: r["input_ref"])
                selected = rows[offset : offset + 10]
                store = ContentStore(self.content.root)
                stack.enter_context(store._maintenance())
                db = stack.enter_context(store._connection())
                for row in selected:
                    _, spec = self._spec(row["input_ref"], actor)
                    authorize(spec, actor, db)
                result = dict(
                    schema_version=1,
                    items=selected,
                    next_offset=offset + 10 if len(rows) > offset + 10 else None,
                )
            elif parts.path == "/v1/content/import/preview":
                if method != "POST" or parts.query:
                    raise ReadFault(422, "invalid_request")
                value = _json(body)
                if (
                    not isinstance(value, dict)
                    or set(value) != {"schema_version", "input_ref", "request_key"}
                    or type(value["schema_version"]) is not int
                    or value["schema_version"] != 1
                ):
                    raise ReadFault(422, "invalid_request")
                entry, spec = self._spec(value["input_ref"], actor)
                info = inspect(entry, spec, actor, value["input_ref"])
                params = dict(
                    schema_version=1,
                    source_ref=value["input_ref"],
                    course_id=info.course_id,
                    state_sha256=info.state_sha256,
                    request_key=value["request_key"],
                    output_name="content-import",
                )
                ContentImportParams.model_validate(params)
                preview = (
                    self.controller.preview(
                        actor,
                        dict(schema_version=1, process_id=PROCESS, parameters=params),
                    )
                    if info.can_import
                    else None
                )
                result = ImportPreview(
                    plan=info, preview=preview, request_key=value["request_key"]
                ).model_dump(mode="json")
                store = ContentStore(spec.content.root)
                stack.enter_context(store._maintenance())
                db = stack.enter_context(store._connection())
                digest, active = state(spec, db, actor)
                if digest != info.state_sha256:
                    raise ReadFault(409, "import_state_changed")
            else:
                raise ReadFault(404, "not_found")
            raw = canonical(result)
            if len(raw) > 262144:
                raise ReadFault(503, "unavailable")
            return SearchReply(
                200, raw, deadline=time.monotonic() + 2, stack=stack.pop_all()
            )
        except ReadFault as error:
            code, status = error.code, error.status
        except (Forbidden, NotFound, PermissionError):
            code, status = "not_found", 404
        except ContentStoreError:
            code, status = "import_blocked", 409
        except (ValueError, TypeError, KeyError, OSError):
            code, status = "invalid_request", 422
        finally:
            stack.close()
        return Reply(
            status,
            canonical(
                dict(
                    schema_version=1,
                    error=dict(code=code, message=code.replace("_", " ")),
                )
            ),
        )
