"""Offline local encoding and additive exact-text offset windows. No model downloads."""

import hashlib
import math
import re


def checked_vectors(vectors, config, expected):
    vectors = [list(map(float, v)) for v in vectors]
    if len(vectors) != expected:
        raise ValueError("Embedding count mismatch")
    for v in vectors:
        if len(v) != config.dimension or not all(math.isfinite(x) for x in v):
            raise ValueError("Invalid embedding dimension or nonfinite values")
        if not math.isclose(sum(x * x for x in v), 1, abs_tol=1e-5):
            raise ValueError("Embedding must be L2-normalized and nonzero")
    return vectors


class FakeEmbedder:
    """Word-hash test features; not a semantic model or a quality measurement."""

    def __init__(self, config):
        if config.provider != "fake":
            raise ValueError("Explicit fake configuration required")
        self.config = config

    def offsets(self, text):
        return [m.span() for m in re.finditer(r"\w+|[^\w\s]", text)]

    def count(self, text):
        return len(self.offsets(text)) + 2

    def encode(self, texts, *, query=False):
        result = []
        for text in texts:
            if self.count(text) > self.config.max_tokens or not text.strip():
                raise ValueError("Empty or oversized embedding input")
            vector = [0.0] * self.config.dimension
            for token in re.findall(r"\w+|[^\w\s]", text.lower()):
                index = int(hashlib.sha256(token.encode()).hexdigest(), 16) % len(
                    vector
                )
                vector[index] += 1
            norm = math.sqrt(sum(x * x for x in vector))
            result.append([x / norm for x in vector])
        return checked_vectors(result, self.config, len(texts))


class LocalEmbedder:
    def __init__(self, config):
        if config.provider != "local":
            raise ValueError("Explicit local-model configuration required")
        # Legacy loader also uses SentenceTransformer + normalize_embeddings=True,
        # but imports Chroma/app state and allows downloads. Keep those paths intact.
        from sentence_transformers import SentenceTransformer

        self.config = config
        self.model = SentenceTransformer(
            config.model,
            revision=config.revision,
            local_files_only=True,
            device="cpu",
            trust_remote_code=False,
        )
        if (
            self.model.get_sentence_embedding_dimension() != config.dimension
            or self.model.max_seq_length < config.max_tokens
        ):
            raise ValueError(
                "Cached model dimension/token capacity conflicts with contract"
            )
        if not self.model.tokenizer.is_fast:
            raise ValueError("Exact original offsets require a fast tokenizer")

    def offsets(self, text):
        return self.model.tokenizer(
            text,
            add_special_tokens=False,
            return_offsets_mapping=True,
            truncation=False,
        )["offset_mapping"]

    def count(self, text):
        return len(
            self.model.tokenizer(text, add_special_tokens=True, truncation=False)[
                "input_ids"
            ]
        )

    def encode(self, texts, *, query=False):
        prefix = self.config.query_prefix if query else self.config.passage_prefix
        inputs = [prefix + text for text in texts]
        if any(not text.strip() for text in texts) or any(
            self.count(text) > self.config.max_tokens for text in inputs
        ):
            raise ValueError("Empty/oversized model input; no silent truncation")
        vectors = self.model.encode(
            inputs,
            batch_size=self.config.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return checked_vectors(vectors.tolist(), self.config, len(texts))


def offset_windows(text, embedder):
    """Partition exact original character ranges; cue times never interpolated."""
    if not text.strip():
        return []
    config = embedder.config
    ends = sorted(
        {end for start, end in embedder.offsets(text) if 0 <= start < end <= len(text)}
        | {len(text)}
    )
    start, result = 0, []
    while start < len(text):
        candidates = [end for end in ends if end > start]
        lo, hi, best = 0, len(candidates) - 1, None
        while lo <= hi:
            mid = (lo + hi) // 2
            if (
                embedder.count(config.passage_prefix + text[start : candidates[mid]])
                <= config.max_tokens
            ):
                best = candidates[mid]
                lo = mid + 1
            else:
                hi = mid - 1
        if best is None:
            raise ValueError("A tokenizer unit exceeds the explicit embedding limit")
        if text[start:best].strip():
            result.append((start, best))
        start = best
    return result


def chunking_configuration(settings):
    """Complete timed-chunker parameters, not unrelated file/download/LLM settings."""
    return {
        "target_duration": float(settings.target_duration),
        "max_duration": float(settings.max_duration),
        "overlap_segments": int(settings.overlap_segments),
    }


def map_transcript(
    plan,
    input,
    settings,
    embedder,
    *,
    workspace,
    source_origin="official",
    contract=None,
):
    """Revalidate source receipts and reuse the actual unchanged timed chunker."""
    from src.model_discovery.cs50_index import CollectionContract, TranscriptPayload
    from src.tools_knowledge.bind_cs50_transcript import (
        build_cs50_knowledge_chunks,
        load_knowledge_transcript,
        resolve_knowledge_input,
    )
    from src.tools_knowledge.cs50_checkpoint import fingerprint
    from src.tools_lecture.execute_cs50 import digest

    input = resolve_knowledge_input(input, workspace=workspace)
    document = load_knowledge_transcript(plan, input, workspace=workspace)
    chunks = build_cs50_knowledge_chunks(plan, input, settings, workspace=workspace)
    segments = {s.seg_id: s for s in document.segments if s.text.strip()}
    contract = contract or CollectionContract(embedding=embedder.config)
    if contract.embedding != embedder.config:
        raise ValueError("Embedder configuration conflicts with collection contract")
    provenance = input.transcript_provenance.model_dump(mode="json")
    original_provenance_hash = fingerprint(provenance)
    if provenance.get("source_file", "").startswith(("/", "\\")):
        provenance = provenance | {"source_file": None}
    common = {
        k: getattr(input, k)
        for k in (
            "course_id",
            "section_key",
            "lecture_id",
            "resource_id",
            "source_id",
            "media_id",
            "language",
            "raw_sha256",
            "transcript_sha256",
        )
    } | {
        "original_url": input.transcript_url,
        "receipt_sha256": digest(input.receipt_path),
        "input_binding_sha256": fingerprint(input.binding.model_dump(mode="json")),
        "chunk_plan_sha256": fingerprint([c.model_dump(mode="json") for c in chunks]),
        "chunking": chunking_configuration(settings),
        "transcript_provenance": provenance,
        "provenance_sha256": original_provenance_hash,
        "discovery_provenance": tuple(
            p.model_dump(mode="json") for p in input.discovery_provenance
        ),
        "embedding_model": embedder.config.model,
        "embedding_version": embedder.config.version,
        "collection_contract_id": contract.contract_id,
        "source_origin": source_origin,
    }
    payloads = []
    for chunk in chunks:
        spans, offset = [], 0
        for sid in chunk.segment_ids:
            s = segments[sid]
            spans.append((offset, offset + len(s.text), s))
            offset += len(s.text) + 1
        if chunk.text != "\n".join(segments[sid].text for sid in chunk.segment_ids):
            raise ValueError("Chunk text/segment correspondence is not exact")
        windows = offset_windows(chunk.text, embedder)
        for i, (start, end) in enumerate(windows):
            cues = [s for a, b, s in spans if a < end and b > start]
            payloads.append(
                TranscriptPayload(
                    **common,
                    chunk_id=chunk.chunk_id,
                    original_chunk_text=chunk.text,
                    original_chunk_segment_ids=tuple(chunk.segment_ids),
                    original_chunk_start=chunk.start,
                    original_chunk_end=chunk.end,
                    text=chunk.text[start:end],
                    segment_ids=tuple(s.seg_id for s in cues),
                    start=min(s.start for s in cues),
                    end=max(s.end for s in cues),
                    char_start=start,
                    char_end=end,
                    unit_index=i,
                    unit_count=len(windows),
                )
            )
    if not payloads:
        raise ValueError("No content-bearing transcript embedding units")
    return payloads
