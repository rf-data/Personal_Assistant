# Normalized material mapping v1

map_material produces exact bounded character windows inside existing typed blocks,
retaining full resource/course/lecture/section/parent binding, raw SHA, parser/version,
document/block IDs, offsets and DOM/page/line positions. Code remains code. Original
image references remain in the normalized document. Math/image/unknown blocks are
not emitted as factual Knowledge units; empty structured tables await an explicitly
evaluated serializer. No timed KnowledgeEvidence or TranscriptChunk is fabricated.

Separate collection contract: cs50_material_blocks_v1; execution_supported=false.
No vector client/embedding model/collection creation/upload is initialized. A future
upload must bind complete immutable embedding config, dimensionality, tokenizer,
normalization and collection metadata, as the existing transcript contract does.
There is no implicit reuse of transcript embeddings or vector schema.

These are unverified source inputs, not Knowledge facts. Schema validation proves
structure and byte locations, not semantic truth. A future Knowledge bridge needs
non-temporal source evidence/quality review and must preserve block/image refs;
existing TranscriptKnowledgeDocument remains unchanged. Mapping is implemented,
Knowledge extraction and material vector upload are deliberately not implemented.

Offline mapping regression passes exact windows, stable IDs, JSON roundtrip,
source preservation, distinct collection and exclusion of unverified visual/math.
