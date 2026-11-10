"""M2.2a synthetic-only verified publication, independent of search activation.

No persisted ready flag or transferable authorization. The batch caller retains
the existing MVP lock and rechecks this evidence at each dispatch and release.
"""

from dataclasses import dataclass
from pathlib import Path

from scripts import cs50_learning_mvp as mvp
from src import cs50_summary_mvp as m1
from src.content_store.models import fingerprint
from src.content_store.store import ContentStore
from src.job_control.models import Principal
from src.model_materials.materials import NormalizedDocument

CONTRACT = "verified-lecture-source-v1"
ADAPTER_VERSION = "verified-lecture-summary-m22a-v1"
PHASES = ("published", "index_pending", "ready")


@dataclass(frozen=True)
class VerifiedSource:
    root: Path
    actor: Principal
    identity: dict
    blocks: tuple
    document: NormalizedDocument
    inventory_sha256: str
    acl_revision: int
    implementation: tuple
    verification_sha256: str

    def recheck(self):
        """Current rights and unchanged evidence; never repair or retry a source."""
        intent = mvp.load(self.root, "intent.json")
        m1.historical_approval(self.root, intent, self.actor)
        store = ContentStore(self.root / "store")
        source = store.get_source(self.identity["source_id"], actor=self.actor)
        view = store.get_parsed_document(
            self.identity["parsed_version_id"], actor=self.actor
        )
        if (
            source.acl_revision != self.acl_revision
            or any(
                getattr(view, key) != self.identity[key]
                for key in (
                    "source_id",
                    "source_version_id",
                    "parsed_version_id",
                    "payload_sha256",
                    "projection_sha256",
                )
            )
            or mvp.implementation_identity() != self.implementation
            or fingerprint(mvp.inventory(self.root)) != self.inventory_sha256
        ):
            raise m1.Hold("summary source authorization/version/bytes changed")


def verify(root, source_id, parsed_version_id, subject):
    """Issue run-local evidence only after all source-side search checks + Reader.

    project_content_for_index is the unchanged scoped verification API used by
    retrieval. It validates the publication, not an FTS index or query result.
    """
    before = fingerprint(mvp.inventory(root))
    intent = mvp.load(root, "intent.json")
    actor = mvp.actor_for(intent, subject)
    if intent["source_origin"] != "synthetic":
        raise m1.Hold("M2.2a is synthetic-only; real-source acceptance pending")
    store = ContentStore(root / "store")
    source = store.get_source(source_id, actor=actor)
    projection = store.project_content_for_index(parsed_version_id, actor=actor)
    identity, blocks, doc = m1._read_verified_source(
        root, source_id, parsed_version_id, subject, phases=PHASES, strict_reader=True
    )
    if doc.binding.source_origin != "synthetic":
        raise m1.Hold("synthetic source binding required")
    reader = m1.ContentReader(
        m1.ContentReadSettings(root=root / "store", cursor_key_file=root / "cursor.key")
    )
    parsed = reader.parsed(parsed_version_id, actor)
    if (
        parsed.implementation_revision != intent["implementation_revision"]
        or parsed.parser_name != intent["parser"]["name"]
        or parsed.parser_version != intent["parser"]["version"]
        or parsed.block_count != len(blocks)
    ):
        raise m1.Hold("reader parser/implementation/block count conflict")
    implementation = mvp.implementation_identity()
    evidence = dict(
        contract=CONTRACT,
        source=identity,
        inventory_sha256=before,
        acl_revision=source.acl_revision,
        implementation=implementation,
        verified_projection_sha256=fingerprint(projection.model_dump(mode="json")),
        blocks_sha256=fingerprint([b.model_dump(mode="json") for b in blocks]),
    )
    result = VerifiedSource(
        root,
        actor,
        identity,
        blocks,
        doc,
        before,
        source.acl_revision,
        implementation,
        fingerprint(evidence),
    )
    result.recheck()
    return result
