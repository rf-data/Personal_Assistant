"""Explicit source/embedding/index steps; default dry-run, no implicit chained actions."""

import argparse
import json
import os
import sys
from contextlib import closing, contextmanager
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def runtime_environment(root):
    """Existing CS50 CLI environment convention, restored after the isolated command."""
    values = {
        "ROOT": str(root),
        "DATA_DIR": str(root / "data"),
        "CHROMA_DIR": str(root / "chroma"),
        "WIKI_EN_API": "https://example.invalid",
        "HEADER_AGENT": "cs50-index",
        "HF_API_KEY": "unused",
        "OPENAI_API_KEY": "offline-unused",
    }
    before = {k: os.environ.get(k) for k in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for k, value in before.items():
            if value is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = value


def client_for(args, *, writing=False):
    endpoint = args.qdrant_url or (
        os.environ.get("QDRANT_URL") if args.qdrant_local is None else None
    )
    if endpoint:
        url = urlsplit(endpoint)
        if (
            not args.allow_remote
            or url.scheme != "https"
            or not url.hostname
            or url.username
            or url.password
            or url.path not in ("", "/")
            or url.query
            or url.fragment
        ):
            raise ValueError(
                "Remote access requires explicit allow-remote and credential-free HTTPS URL"
            )
        key = os.environ.get("QDRANT_API_KEY")
        if not key:
            raise ValueError("Authenticated remote access requires QDRANT_API_KEY")
        from qdrant_client import QdrantClient

        return QdrantClient(
            url=endpoint,
            api_key=key,
            timeout=10,
            cloud_inference=False,
            prefer_grpc=False,
            # The SDK's separate background version probe bypasses the REST
            # client's trust_env policy. Server version is an explicit runbook
            # check; this does not disable TLS certificate verification.
            check_compatibility=False,
            trust_env=False,
            follow_redirects=False,
        )
    if args.qdrant_local is None:
        raise ValueError(
            "An explicit local path or authorized remote endpoint is required"
        )
    path = args.qdrant_local.absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Symlink Qdrant path forbidden")
    if not writing and not path.is_dir():
        raise FileNotFoundError("Read-only index location absent")
    from qdrant_client import QdrantClient

    return QdrantClient(path=str(path))


def engine_for(config):
    from src.tools_rag.cs50_embeddings import FakeEmbedder, LocalEmbedder

    return FakeEmbedder(config) if config.provider == "fake" else LocalEmbedder(config)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=[
            "inventory",
            "validate",
            "download",
            "plan",
            "embed",
            "upload",
            "resume",
            "status",
            "verify",
            "search",
            "retrieve",
            "demo",
        ],
    )
    parser.add_argument(
        "--adapter-plan",
        type=Path,
        default=ROOT / "docs/course_sources/cs50/cs50_lecture_plan.v1.json",
    )
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--course")
    parser.add_argument("--section")
    parser.add_argument("--all-six", action="store_true")
    parser.add_argument("--index-plan", type=Path)
    parser.add_argument("--vectors", type=Path)
    parser.add_argument("--embedding-config", type=Path)
    parser.add_argument("--model-cache", type=Path)
    parser.add_argument("--model-revision")
    parser.add_argument("--candidate-source", type=Path, action="append", default=[])
    parser.add_argument("--fake-embeddings", action="store_true")
    parser.add_argument(
        "--source-origin", choices=["official", "synthetic"], default="official"
    )
    parser.add_argument("--collection", default="cs50_transcript_chunks_v1")
    parser.add_argument("--state-root", type=Path)
    parser.add_argument("--output", type=Path)
    connection = parser.add_mutually_exclusive_group()
    connection.add_argument("--qdrant-local", type=Path)
    connection.add_argument("--qdrant-url")
    parser.add_argument("--allow-remote", action="store_true")
    parser.add_argument("--execute-download", action="store_true")
    parser.add_argument("--license-reviewed", action="store_true")
    parser.add_argument("--write-plan", action="store_true")
    parser.add_argument("--execute-embedding", action="store_true")
    parser.add_argument("--execute-upload", action="store_true")
    parser.add_argument("--create-collection", action="store_true")
    parser.add_argument("--query")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--lecture-id")
    parser.add_argument("--source-id")
    parser.add_argument("--language", default="en")
    parser.add_argument("--score-threshold", type=float)
    args = parser.parse_args(argv)
    if args.candidate_source and args.command != "inventory":
        parser.error("Candidate files belong only to read-only inventory")
    # Operator vocabulary, identical implementation and authorization gates.
    args.command = {"resume": "upload", "verify": "status", "retrieve": "search"}.get(
        args.command, args.command
    )
    active = [
        name
        for name in (
            "execute_download",
            "write_plan",
            "execute_embedding",
            "execute_upload",
        )
        if getattr(args, name)
    ]
    allowed = {
        "download": "execute_download",
        "plan": "write_plan",
        "embed": "execute_embedding",
        "upload": "execute_upload",
    }
    if any(name != allowed.get(args.command) for name in active):
        parser.error(
            "Execution flags belong to separate commands; no implicit chained actions"
        )
    if args.create_collection and args.command != "upload":
        parser.error("Collection creation belongs only to explicit upload")
    if args.command == "demo":
        if args.output is None:
            parser.error("Demo requires an exclusive external --output directory")
    elif args.workspace is None:
        parser.error("Explicit --workspace required")
    try:
        with runtime_environment((args.output or args.workspace).absolute()):
            result = run_command(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as error:
        # Never echo remote auth responses, supplied credentials or validation input.
        print(
            json.dumps(
                {
                    "status": "failed",
                    "stage": args.command,
                    "error_class": type(error).__name__,
                }
            ),
            file=sys.stderr,
        )
        return 1


def run_command(args):
    from src.model_discovery.cs50_index import CollectionContract, EmbeddingConfig
    from src.tools_knowledge.cs50_checkpoint import atomic_json
    from src.tools_lecture.adapt_cs50 import CS50AdapterPlan
    from src.tools_rag.cs50_ingestion import (
        IngestionPlan,
        VectorArtifact,
        build_ingestion_plan,
        checked_artifact_path,
        embed_plan,
        revalidate_plan,
        selected_bindings,
        upsert_plan,
    )
    from src.tools_rag.cs50_orchestration import (
        existing_inputs,
        index_status,
        prepare_sources,
    )

    adapter = CS50AdapterPlan.model_validate_json(args.adapter_plan.read_bytes())
    if args.command == "inventory":
        from src.tools_rag.cs50_pilot import (
            candidate_inventory,
            embedding_environment,
            pilot_review,
            source_inventory,
        )

        inventory = source_inventory(
            adapter,
            workspace=args.workspace,
            course=args.course,
            section=args.section,
            all_six=args.all_six,
        )
        result = pilot_review(
            inventory,
            embedding_environment(cache=args.model_cache, revision=args.model_revision),
            candidates=candidate_inventory(
                args.candidate_source, workspace=args.workspace
            ),
        )
        if args.output is not None:
            output = checked_artifact_path(args.output, adapter, args.workspace)
            output.parent.mkdir(parents=True, exist_ok=True)
            atomic_json(output, result)
        return result
    if args.command == "demo":
        from scripts.cs50_transcript_index_demo import demonstrate

        return demonstrate(
            adapter,
            args.output,
            course=args.course,
            section=args.section,
            all_six=args.all_six,
        )
    if args.command == "download":
        report, _ = prepare_sources(
            adapter,
            workspace=args.workspace,
            course=args.course,
            section=args.section,
            all_six=args.all_six,
            execute_download=args.execute_download,
            license_reviewed=args.license_reviewed,
        )
        return report
    if args.command == "plan":
        from src.core.config_knowledge import KnowledgeSettings

        bindings = selected_bindings(
            adapter, course=args.course, section=args.section, all_six=args.all_six
        )
        if not args.write_plan:
            return {
                "dry_run": True,
                "sources": len(bindings),
                "expected_units": None,
                "reason": "Unit counts require validated imports and a concrete tokenizer; use explicit write-plan",
            }
        if args.output is None:
            raise ValueError("Explicit plan output required")
        if not args.fake_embeddings and args.embedding_config is None:
            raise ValueError(
                "Explicit immutable local embedding configuration required"
            )
        config = (
            EmbeddingConfig.fake()
            if args.fake_embeddings
            else EmbeddingConfig.model_validate_json(args.embedding_config.read_bytes())
        )
        engine = engine_for(config)
        inputs = existing_inputs(
            adapter,
            workspace=args.workspace,
            course=args.course,
            section=args.section,
            all_six=args.all_six,
        )
        plan = build_ingestion_plan(
            adapter,
            inputs,
            KnowledgeSettings(),
            engine,
            workspace=args.workspace,
            course=args.course,
            section=args.section,
            all_six=args.all_six,
            contract=CollectionContract(name=args.collection, embedding=config),
            source_origin=args.source_origin,
        )
        output = checked_artifact_path(args.output, adapter, args.workspace)
        output.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(output, plan.model_dump(mode="json"))
        return {
            "plan_id": plan.plan_id,
            "sources": len(plan.sources),
            "units": len(plan.units),
        }
    if args.index_plan is None:
        raise ValueError("Explicit index plan required")
    plan = IngestionPlan.model_validate_json(args.index_plan.read_bytes())
    revalidate_plan(plan, adapter, workspace=args.workspace)
    if args.command == "validate":
        from src.tools_rag.cs50_ingestion import validate_vectors

        vectors = None
        if args.vectors is not None:
            vectors = validate_vectors(
                VectorArtifact.model_validate_json(args.vectors.read_bytes()), plan
            )
        return {
            "schema_version": 1,
            "status": "validated",
            "plan_id": plan.plan_id,
            "source_count": len(plan.sources),
            "expected_points": len(plan.units),
            "vector_artifact_id": vectors.artifact_id if vectors else None,
            "remote_connected": False,
        }
    if args.command in ("embed", "upload") and (
        args.execute_embedding or args.execute_upload
    ):
        bindings = selected_bindings(
            adapter, course=args.course, section=args.section, all_six=args.all_six
        )
        if {b.source_id for b in bindings} != {
            s.input["source_id"] for s in plan.sources
        }:
            raise ValueError(
                "Explicit execution scope does not match stored ingestion plan"
            )
    if args.fake_embeddings and plan.collection.embedding.provider != "fake":
        raise ValueError(
            "Cannot silently replace the planned local model with fake embeddings"
        )
    if args.command == "embed":
        if not args.execute_embedding:
            return {
                "dry_run": True,
                "expected_units": len(plan.units),
                "embedding": plan.collection.embedding.model_dump(mode="json"),
            }
        if args.vectors is None:
            raise ValueError("Explicit vector output required")
        vectors = embed_plan(
            plan,
            adapter,
            engine_for(plan.collection.embedding),
            workspace=args.workspace,
            destination=args.vectors,
        )
        return {"artifact_id": vectors.artifact_id, "units": len(vectors.vectors)}
    if args.command == "search":
        from src.tools_rag.cs50_retrieval import search_cs50_transcripts

        if args.query is None:
            raise ValueError("Explicit query required")
        with closing(client_for(args)) as client:
            hits = search_cs50_transcripts(
                args.query,
                client,
                plan,
                engine_for(plan.collection.embedding),
                top_k=args.top_k,
                course_id=args.course,
                lecture_id=args.lecture_id,
                source_id=args.source_id,
                language=args.language,
                score_threshold=args.score_threshold,
                adapter=adapter,
                workspace=args.workspace,
            )
        return {
            "hits": [h.model_dump(mode="json") for h in hits],
            "fake_embeddings": plan.collection.embedding.provider == "fake",
        }
    if args.vectors is None or args.state_root is None:
        raise ValueError("Vector artifact and state root required")
    vectors = VectorArtifact.model_validate_json(args.vectors.read_bytes())
    if args.command == "upload" and not args.execute_upload:
        return upsert_plan(
            None,
            plan,
            vectors,
            adapter,
            workspace=args.workspace,
            state_root=args.state_root,
        )
    with closing(client_for(args, writing=args.command == "upload")) as client:
        if args.command == "status":
            return index_status(
                client,
                plan,
                vectors,
                adapter,
                workspace=args.workspace,
                state_root=args.state_root,
            )
        return upsert_plan(
            client,
            plan,
            vectors,
            adapter,
            workspace=args.workspace,
            state_root=args.state_root,
            execute=True,
            allow_create=args.create_collection,
        ).model_dump(mode="json")


if __name__ == "__main__":
    raise SystemExit(main())
