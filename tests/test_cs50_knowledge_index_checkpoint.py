from test_cs50_ingestion import context as context
from test_cs50_ingestion import index_case as index_case


def test_actual_completed_checkpoint_metadata_and_artifacts(index_case, tmp_path):
    from test_cs50_lecture_runner import fake_factory

    from src.model_knowledge.data_knowledge import TranscriptKnowledgeDocument
    from src.tools_knowledge.complete_cs50_lecture import complete_lecture
    from src.tools_knowledge.run_cs50_lecture import (
        LectureRunConfig,
        lecture_budget,
        prepare_lecture,
        run_lecture,
    )
    from src.tools_lecture.execute_cs50 import digest
    from src.tools_rag.cs50_knowledge_index import (
        KnowledgeMappingContext,
        map_knowledge_document,
    )

    adapter, workspace, input, _, plan, _ = index_case
    job = prepare_lecture(
        adapter,
        input,
        workspace=workspace,
        config=LectureRunConfig(max_requests=100, token_budget=1000000),
    )
    budget = lecture_budget([job], tmp_path / "budget")
    directory = tmp_path / "knowledge"
    run_lecture(job, directory, budget, provider_factory=fake_factory([]))
    complete_lecture(job, directory, budget)
    result_file = directory / "completion/extraction.json"
    document = TranscriptKnowledgeDocument.model_validate_json(result_file.read_bytes())
    receipt = directory / "checkpoint/checkpoint.v1.json"
    metadata = KnowledgeMappingContext(
        quality_status="synthetic",
        result_file_sha256=digest(result_file),
        extraction_receipt_sha256=digest(receipt),
    )
    records = map_knowledge_document(
        document,
        plan,
        adapter,
        metadata,
        workspace=workspace,
        result_file=result_file,
        extraction_receipt=receipt,
    )
    assert records
    assert all(
        r.extraction_context_verified
        and r.prompt_version == job.identity.prompt_version
        and r.extraction_model == job.identity.model
        for r in records
    )
    assert all(
        r.context.execution_mode == "offline" and r.quality_status == "synthetic"
        for r in records
    )
