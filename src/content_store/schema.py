"""Exact content-v1 DDL. No adoption, upgrade, queue or automatic migration."""

APPLICATION_ID = 0x43323343
VERSION = 1

TABLES = {
    "metadata": """CREATE TABLE metadata (
        id INTEGER PRIMARY KEY CHECK(id=1), identity TEXT NOT NULL CHECK(identity='content-v1'),
        purpose TEXT NOT NULL CHECK(purpose IN ('content','synthetic_test')),
        publication_seq INTEGER NOT NULL CHECK(publication_seq>=0),
        collection_revision INTEGER NOT NULL CHECK(collection_revision>=0))""",
    "sources": """CREATE TABLE sources (
        id TEXT PRIMARY KEY, namespace TEXT NOT NULL, external_id TEXT NOT NULL,
        course_id TEXT NOT NULL, owner TEXT NOT NULL, data TEXT NOT NULL,
        acl_revision INTEGER NOT NULL CHECK(acl_revision>=0),
        state TEXT NOT NULL CHECK(state IN ('registered','tombstoned')),
        publication_seq INTEGER NOT NULL UNIQUE CHECK(publication_seq>0),
        UNIQUE(namespace,external_id))""",
    "source_grants": """CREATE TABLE source_grants (
        source_id TEXT NOT NULL REFERENCES sources(id), subject TEXT NOT NULL,
        permission TEXT NOT NULL CHECK(permission='read'), PRIMARY KEY(source_id,subject,permission))""",
    "artifacts": """CREATE TABLE artifacts (
        sha256 TEXT PRIMARY KEY CHECK(length(sha256)=64 AND sha256 NOT GLOB '*[^0-9a-f]*'),
        size_bytes INTEGER NOT NULL CHECK(size_bytes BETWEEN 0 AND 67108864),
        state TEXT NOT NULL CHECK(state IN ('available','quarantined')))""",
    "processing_runs": """CREATE TABLE processing_runs (
        id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(id),
        actor TEXT NOT NULL, request_key TEXT NOT NULL, fingerprint TEXT NOT NULL,
        slot_id TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('raw','synthetic')),
        state TEXT NOT NULL CHECK(state IN ('preparing','prepared','committed','blocked','rejected')),
        data TEXT NOT NULL, UNIQUE(actor,request_key))""",
    "raw_reservations": """CREATE TABLE raw_reservations (
        source_id TEXT NOT NULL REFERENCES sources(id), sha256 TEXT NOT NULL REFERENCES artifacts(sha256),
        run_id TEXT NOT NULL REFERENCES processing_runs(id), data TEXT NOT NULL,
        PRIMARY KEY(source_id,sha256))""",
    "source_versions": """CREATE TABLE source_versions (
        id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(id),
        variant_key TEXT NOT NULL, manifest_sha256 TEXT NOT NULL,
        state TEXT NOT NULL CHECK(state IN ('verified','quarantined')),
        publication_seq INTEGER NOT NULL UNIQUE CHECK(publication_seq>0),
        data TEXT NOT NULL, UNIQUE(id,source_id), UNIQUE(source_id,variant_key,manifest_sha256))""",
    "source_raw_artifacts": """CREATE TABLE source_raw_artifacts (
        source_version_id TEXT NOT NULL, source_id TEXT NOT NULL,
        role TEXT NOT NULL, ordinal INTEGER NOT NULL CHECK(ordinal>=0),
        sha256 TEXT NOT NULL, data TEXT NOT NULL,
        PRIMARY KEY(source_version_id,role,ordinal),
        FOREIGN KEY(source_version_id,source_id) REFERENCES source_versions(id,source_id),
        FOREIGN KEY(source_id,sha256) REFERENCES raw_reservations(source_id,sha256))""",
    "parser_configs": """CREATE TABLE parser_configs (id TEXT PRIMARY KEY, data TEXT NOT NULL)""",
    "parsed_documents": """CREATE TABLE parsed_documents (
        id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(id), representation_key TEXT NOT NULL,
        UNIQUE(id,source_id), UNIQUE(source_id,representation_key))""",
    "parsed_versions": """CREATE TABLE parsed_versions (
        id TEXT PRIMARY KEY, source_id TEXT NOT NULL, document_id TEXT NOT NULL,
        source_version_id TEXT NOT NULL, slot_id TEXT NOT NULL UNIQUE,
        parser_config_id TEXT NOT NULL REFERENCES parser_configs(id),
        payload_sha256 TEXT NOT NULL REFERENCES artifacts(sha256),
        projection_sha256 TEXT NOT NULL REFERENCES artifacts(sha256),
        state TEXT NOT NULL CHECK(state IN ('published','quarantined','tombstoned')),
        publication_seq INTEGER NOT NULL UNIQUE CHECK(publication_seq>0), data TEXT NOT NULL,
        FOREIGN KEY(document_id,source_id) REFERENCES parsed_documents(id,source_id),
        FOREIGN KEY(source_version_id,source_id) REFERENCES source_versions(id,source_id))""",
    "content_blocks": """CREATE TABLE content_blocks (
        version_id TEXT NOT NULL REFERENCES parsed_versions(id), id TEXT NOT NULL,
        block_order INTEGER NOT NULL CHECK(block_order>=0), text_sha256 TEXT NOT NULL,
        data TEXT NOT NULL, PRIMARY KEY(version_id,id), UNIQUE(version_id,block_order))""",
    "content_locators": """CREATE TABLE content_locators (
        version_id TEXT NOT NULL, block_id TEXT NOT NULL, ordinal INTEGER NOT NULL CHECK(ordinal>=0),
        raw_sha256 TEXT NOT NULL REFERENCES artifacts(sha256),
        time_status TEXT NOT NULL CHECK(time_status IN ('known','unknown','not_applicable')),
        start REAL, end REAL, data TEXT NOT NULL,
        PRIMARY KEY(version_id,block_id,ordinal),
        FOREIGN KEY(version_id,block_id) REFERENCES content_blocks(version_id,id),
        CHECK((time_status='known' AND start IS NOT NULL AND end IS NOT NULL AND start>=0 AND end>=start)
          OR (time_status IN ('unknown','not_applicable') AND start IS NULL AND end IS NULL)))""",
    "artifact_references": """CREATE TABLE artifact_references (
        run_id TEXT NOT NULL REFERENCES processing_runs(id), role TEXT NOT NULL, ordinal INTEGER NOT NULL CHECK(ordinal>=0),
        sha256 TEXT NOT NULL REFERENCES artifacts(sha256),
        version_id TEXT REFERENCES parsed_versions(id), data TEXT NOT NULL,
        PRIMARY KEY(run_id,role,ordinal))""",
}
INDEXES = {
    "active_slot": """CREATE UNIQUE INDEX active_slot ON processing_runs(slot_id)
        WHERE state IN ('preparing','prepared','blocked')""",
}
# Immutable payload records. Mutable status/ACL columns have deliberately narrow APIs.
TRIGGERS = {
    "immutable_store_identity": """CREATE TRIGGER immutable_store_identity BEFORE UPDATE ON metadata
        WHEN NEW.identity != OLD.identity OR NEW.purpose != OLD.purpose OR NEW.id != OLD.id
        BEGIN SELECT RAISE(ABORT,'immutable store identity'); END""",
    "immutable_source_identity": """CREATE TRIGGER immutable_source_identity BEFORE UPDATE ON sources
        WHEN NEW.id != OLD.id OR NEW.namespace != OLD.namespace OR NEW.external_id != OLD.external_id
          OR NEW.course_id != OLD.course_id OR NEW.owner != OLD.owner OR NEW.data != OLD.data
          OR NEW.publication_seq != OLD.publication_seq
        BEGIN SELECT RAISE(ABORT,'immutable source identity'); END""",
    "immutable_artifact_identity": """CREATE TRIGGER immutable_artifact_identity BEFORE UPDATE ON artifacts
        WHEN NEW.sha256 != OLD.sha256 OR NEW.size_bytes != OLD.size_bytes
        BEGIN SELECT RAISE(ABORT,'immutable artifact identity'); END""",
}
for _table in (
    "parser_configs",
    "parsed_documents",
    "source_raw_artifacts",
    "content_blocks",
    "content_locators",
    "artifact_references",
    "raw_reservations",
):
    for _op in ("UPDATE", "DELETE"):
        _name = f"immutable_{_table}_{_op.lower()}"
        TRIGGERS[_name] = (
            f"CREATE TRIGGER {_name} BEFORE {_op} ON {_table} "
            "BEGIN SELECT RAISE(ABORT,'immutable content record'); END"
        )
for _table, _columns in {
    "source_versions": (
        "id",
        "source_id",
        "variant_key",
        "manifest_sha256",
        "publication_seq",
        "data",
    ),
    "parsed_versions": (
        "id",
        "source_id",
        "document_id",
        "source_version_id",
        "slot_id",
        "parser_config_id",
        "payload_sha256",
        "projection_sha256",
        "publication_seq",
        "data",
    ),
}.items():
    _name = f"immutable_{_table}_data"
    TRIGGERS[_name] = (
        f"CREATE TRIGGER {_name} BEFORE UPDATE ON {_table} "
        "WHEN " + " OR ".join(f"NEW.{c} != OLD.{c}" for c in _columns) + " "
        "BEGIN SELECT RAISE(ABORT,'immutable version payload'); END"
    )
    _delete = f"immutable_{_table}_delete"
    TRIGGERS[_delete] = (
        f"CREATE TRIGGER {_delete} BEFORE DELETE ON {_table} "
        "BEGIN SELECT RAISE(ABORT,'immutable version record'); END"
    )


def expected_schema():
    return {
        **{("table", name): sql for name, sql in TABLES.items()},
        **{("index", name): sql for name, sql in INDEXES.items()},
        **{("trigger", name): sql for name, sql in TRIGGERS.items()},
    }
