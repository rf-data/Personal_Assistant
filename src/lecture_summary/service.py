"""One bounded synchronous invocation, isolated from queues and production stores."""

from src.lecture_summary.models import (
    PROMPT_VERSION,
    TEMPLATE_VERSION,
    Draft,
    Summary,
    cache_key,
)
from src.lecture_summary.sources import collect
from src.lecture_summary.validation import validate


class SummaryService:
    def __init__(self, catalog, storage, provider, *, cache=None, hierarchy=None):
        self.catalog, self.storage, self.provider = catalog, storage, provider
        # Optional existing writable registered directory. No implicit mkdir.
        self.cache = cache
        self.hierarchy = hierarchy
        self.strategy = "hierarchical" if hierarchy is not None else "simple"

    def preflight(self, selection):
        if self.hierarchy is None:
            return None
        from src.lecture_summary.hierarchy import make_plan, public_plan

        evidence, _ = collect(self.catalog, selection, self.storage)
        if not self.cache:
            raise ValueError("Hierarchical mode requires a registered writable cache")
        with self.storage.parent(
            self.cache[0], self.cache[1] + "/.hierarchy-check", write=True
        ):
            pass
        return public_plan(
            make_plan(
                evidence,
                selection,
                self.provider.model,
                self.hierarchy,
                offline=getattr(self.provider, "offline", False),
            )
        )

    def generate(self, selection, *, cancelled=lambda: False):
        if cancelled():
            raise InterruptedError("Summary cancelled before collection")
        selection = type(selection).model_validate_json(selection.model_dump_json())
        if self.hierarchy is not None:
            from src.lecture_summary.hierarchy import generate

            return generate(self, selection, self.hierarchy, cancelled)
        evidence, versions = collect(self.catalog, selection, self.storage)
        key = cache_key(selection, versions, self.provider.model)
        location = None
        if self.cache:
            storage_id, prefix = self.cache
            location = (storage_id, f"{prefix}/{key}.json")
            try:
                cached = Summary.model_validate_json(
                    self.storage.read(*location, maximum=300000)
                )
            except FileNotFoundError:
                cached = None
            if cached is not None:
                status, messages = validate(cached.content, evidence, selection)
                if (
                    cached.summary_id != key
                    or cached.selection != selection
                    or cached.model != self.provider.model
                    or cached.prompt_version != PROMPT_VERSION
                    or cached.template_version != TEMPLATE_VERSION
                    or cached.evidence != evidence
                    or cached.artifact_versions != tuple((v[1], v[2]) for v in versions)
                    or status == "failed"
                    or cached.validation_status != status
                    or cached.validation_messages != messages
                ):
                    raise ValueError(
                        "Summary cache validation failed; no stale result returned"
                    )
                if cancelled():
                    raise InterruptedError("Summary cancelled before cache return")
                return cached
        if cancelled():
            raise InterruptedError("Summary cancelled before model dispatch")
        # No retries, no processing a partially valid model result.
        generated = self.provider.generate(evidence, selection)
        draft = (
            Draft.model_validate_json(generated.model_dump_json())
            if isinstance(generated, Draft)
            else Draft.model_validate(generated)
        )
        if cancelled():
            raise InterruptedError("Summary cancelled after model response")
        # Reopen every source to detect concurrent edits before publication.
        checked_evidence, checked_versions = collect(
            self.catalog, selection, self.storage
        )
        if checked_evidence != evidence or checked_versions != versions:
            raise ValueError("Source changed during generation")
        status, messages = validate(draft, evidence, selection)
        result = Summary(
            summary_id=key,
            selection=selection,
            artifact_versions=tuple((v[1], v[2]) for v in versions),
            model=self.provider.model,
            content=draft,
            evidence=evidence,
            validation_status=status,
            validation_messages=messages,
        )
        if status != "failed":
            from src.lecture_summary.exports import render

            # Exercise both renderers before a result becomes cacheable.
            for latex in (False, True):
                render(result, latex=latex)
        if location and status != "failed":
            try:
                self.storage.create(
                    *location, result.model_dump_json(indent=2).encode()
                )
            except FileExistsError:
                # Concurrent request won. Never overwrite it or silently adopt it.
                other = Summary.model_validate_json(
                    self.storage.read(*location, maximum=300000)
                )
                if other.summary_id != key or other.evidence != evidence:
                    raise ValueError("Concurrent cache publication conflict") from None
        return result
