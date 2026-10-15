# Course materials: verified baseline and prioritized gaps

Baseline: origin/master ad3078f59851fa71d076a8982bcab8b5b700c1a9,
15 October 2026. No live material requests. Six course IDs are unchanged;
cs50x is the actual internal ID. 63 manifest SHA-verified snapshots include
50 weekly overviews, six indexes and seven ancillary pages.

## Integration proof

#39 and #40 occur as master merge commits bbf741f/ff96cbc. The work from
#41–#44 is integrated with rewritten commits acae6d1/6f94eaf/5d87b7f/3727b94
and #45/e6d3667 in ad3078f. Git tree proof is stronger than treating the
historical stacked PR bases as current. #47 is documentation-only and not in
this baseline. No feature changes from private local consolidation are included.

## Reuse assessment

- Discovery models and prepare_cs50: preserve the complete graph and IDs;
  candidate coverage is lecture-resource-list coverage, not recursive notes/code coverage.
- Adapter: 50 SRT bindings/100 tasks, with externally stored dependencies.
  LectureDocument can describe files but cannot hold a structured material graph,
  hash/parser contracts or block/image provenance. Keep additive sidecar contracts.
- CS50Executor: safe_path, digest, sync_directory, write_state, per-source flock,
  exclusive publication and bounded streaming/retries are reusable. Its streaming
  primitive accepts a checked source URL; add a guarded transport for material MIME
  and hosts. Do not change SRT execution behavior or route materials through yt-dlp.
- Official importer and Knowledge binder/chunker/evidence/checkpoints remain the
  transcript path. Material documents need no timestamps and must not masquerade
  as TranscriptDocument or ChunkKnowledgeResult.
- Existing HTMLCleanExtractor supports rich elements but inherits BaseExtractor
  and application/context helpers, and has network capability. extract_html_file
  references app_session without importing it. Do not use that runner for offline imports.
- PDFCleanExtractor uses PyMuPDF, app_session, ParseContext and FeatureEnricher.
  Its _p{page_no}_extracted filename already separates pages; do not claim a proven
  overwrite bug. Keep page-local locations in one versioned normalized document.
- Docling is installed and declared in lecture-worker, but its converter imports
  heavy pipelines and can require OCR/layout/formula assets. Do not initialize it
  for this bounded deterministic path. PyMuPDF is also installed/declared and can
  extract existing text, image bytes and table candidates without model downloads.
- Legacy Visual enrichment is inference-related and outside scope; produce image
  references/uncertainty only. No dedicated safe source-file/archive importer found.
- Qdrant transcript mapping/embedding/ingestion has strict source/hash/schema
  contracts. Keep materials in a distinct read-only mapping contract; no uploads.

## Priorities and proof limits

P0: additive identities/artifacts, controlled raw archiving, exact binding/hash resume,
HTML/code parsing, bounded PDF subprocess and fail-closed unsupported formats.
P1: structure/image provenance and block mapping, mixed-lecture/course/six-scope
synthetic offline demonstrations. P2: real parser quality review, licensed limited
crawl, OCR/slide/ZIP support after independent review.

The [generated snapshot inventory](material_coverage.md) counts candidate nodes,
media variants and raw link/image occurrences separately. Every raw occurrence is
cataloged, including sidebar/footer, fragment, external and platform links; these
are not unique materials. Unknown language/license stays unknown. No license is
inferred from an official hostname. Catalog API output retains the entire graph,
URL, parent, sections, logical lecture IDs, role, format, provenance and capability.
A raw page link without a proven lecture context keeps an empty lecture list.

Missing detail snapshots prevent recursive discovery of code files, notes image
assets and individual problem statements beyond known pages. No live coverage,
license approval, HTTP success, or parsing of all real materials is demonstrated.
A future crawl needs explicit host/path/page/byte/depth/rate/time bounds and license
review, with a new snapshot manifest; it is not enabled here.

Initial targeted test: test_cs50_material_inventory.py, 1 passed, 11.34 seconds.
No dependencies installed/upgraded; baseline full-suite evidence is 510 passed,
six known TXT failures, five skips in a clean checkout. A new final run is required.
