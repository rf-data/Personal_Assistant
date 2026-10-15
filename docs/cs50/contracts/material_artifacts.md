# Material artifacts v1

Additive `src/model_materials/materials.py` contracts reuse ResourceCandidate and
its course/section/resource/parent/provenance identities verbatim. Source ID aliases
that candidate ID; material ID additionally identifies the selected variant/URL.
Logical lecture IDs remain separately bound, including shared resources. Unknown
language/media identity remains unknown. No transcript or Knowledge model changes.

MaterialResource includes the original discovery candidate. ArtifactReceipt owns
explicit raw/source and normalized references, MIME, SHA256, status, parser config,
errors/history and image hashes. Raw artifacts and parser outputs are separate.
The serializer never contains absolute workspace paths. License defaults to
not_assessed; synthetic origin must be explicit in fixtures and demos.

NormalizedDocument v1 contains typed ordered Block records and ImageArtifact
references with DOM/page/bbox/line provenance. IDs bind source identity, exact raw
hash, complete parser configuration/version and order. Tables/lists retain
structure; math candidates remain uncertain. Raw HTML/embedded original image
bytes are archived without reconstruction. Unfetched external image references
have no fabricated artifact path/hash. No synthetic timestamps are introduced.

This is a parser input layer, not a second course or Knowledge architecture.
Material mapping must use a separate versioned collection contract. Future
Knowledge Evidence needs explicit DOM/page/line references; existing timed
TranscriptChunk/KnowledgeEvidence cannot express those without an additive bridge.

Contract regression: 4 cases (JSON, original keys, URL/language/role conflicts).
