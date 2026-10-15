import pytest
from test_cs50_knowledge_input import context as context
from test_cs50_knowledge_input import imported

from src.model_discovery.cs50_index import EmbeddingConfig
from src.tools_rag.cs50_embeddings import (
    FakeEmbedder,
    checked_vectors,
    map_transcript,
    offset_windows,
)


def test_offsets_unicode_and_no_silent_truncation():
    engine = FakeEmbedder(EmbeddingConfig.fake(max_tokens=8))
    text = "Python print café 🙂 input arguments return functions " * 10
    windows = offset_windows(text, engine)
    assert len(windows) > 2
    assert "".join(text[a:b] for a, b in windows) == text
    assert all(engine.count(text[a:b]) <= 8 for a, b in windows)
    with pytest.raises(ValueError, match="oversized"):
        engine.encode([text])
    assert engine.encode(["Python print"]) == engine.encode(["Python print"])
    assert offset_windows(" \n ", engine) == []


@pytest.mark.parametrize("vector", [[0] * 16, [float("nan")] * 16, [1, 0]])
def test_invalid_vectors(vector):
    with pytest.raises(ValueError):
        checked_vectors([vector], EmbeddingConfig.fake(), 1)


@pytest.mark.parametrize("course", ["cs50_python", "cs50_cybersecurity"])
def test_real_import_chunk_mapping_and_empty_cues(context, tmp_path, course):
    from src.core.config_knowledge import KnowledgeSettings
    from src.tools_lecture.execute_cs50 import digest

    module, _, _, plan = context
    _, input = imported(context, tmp_path, course=course)
    engine = FakeEmbedder(EmbeddingConfig.fake())
    before = digest(input.transcript_json_path)
    chunks = module.build_cs50_knowledge_chunks(
        plan, input, KnowledgeSettings(), workspace=tmp_path
    )
    values = map_transcript(
        plan,
        input,
        KnowledgeSettings(),
        engine,
        workspace=tmp_path,
        source_origin="synthetic",
    )
    assert {v.chunk_id for v in values} == {c.chunk_id for c in chunks}
    assert all(1 not in v.segment_ids and v.section_key == "0" for v in values)
    assert all(
        v.start == 1 and v.end == 6 and v.source_id == input.source_id for v in values
    )
    assert all(v.original_chunk_text == chunks[0].text for v in values)
    assert digest(input.transcript_json_path) == before
    if course == "cs50_cybersecurity":
        assert all(v.media_id is None for v in values)


def test_partial_cue_keeps_real_cue_times(context, tmp_path):
    from src.core.config_knowledge import KnowledgeSettings

    module, _, _, plan = context
    body = (
        b"1\n00:00:01,000 --> 00:00:40,000\n"
        + (b"Python function argument " * 40)
        + b"\n"
    )
    _, input = imported(context, tmp_path, body=body)
    engine = FakeEmbedder(EmbeddingConfig.fake(max_tokens=8))
    values = map_transcript(
        plan, input, KnowledgeSettings(), engine, workspace=tmp_path
    )
    assert len(values) > 10
    assert all(v.segment_ids == (0,) and v.start == 1 and v.end == 40 for v in values)
    assert len({v.point_id for v in values}) == len(values)
    assert "".join(v.text for v in values) == values[0].original_chunk_text
