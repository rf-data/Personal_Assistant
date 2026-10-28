# C26-CS50P-08 architecture and decisions

Status: **HOLD** for real execution. The reviewed implementation is additive to
C07 at `1584a2807c8f9d75604ab17a4ea239d8f4a0882b`. No second general parsing,
transcription or retrieval framework is introduced.

| Existing component | C08 use / boundary |
|---|---|
| `run_lecture_compilation`, `tools_lecture/process_lecture` | Inspected orchestration; not started, since it includes existing execution/media actions. |
| `prepare_cs50.parse_week_page`, `tools_materials.assignments.children` | Reused for official overview, Short and task graph discovery. |
| `WeekInventory`, `WeekMaterial`, `MaterialResource`, `ResourceCandidate` | Existing identities, hierarchy and metadata retained. Inventory v2 explicitly opts into automatic source files; v1 keeps the old source policy. |
| `MaterialDownloader`, `CS50Executor.download`, `PublicHTTPSTransport` | Existing serialized streaming, exact URL, MIME, public DNS pinning/TLS, redirect refusal, timeout, atomic storage and downloadreceipt checks. |
| `AcquisitionLimits`, `TransferBudget`, `CapacityTransport` | Per-file admission and run/archive/disk-reserve checks, including source files. |
| `parse_html` v2, `NormalizedDocument` | Local main-content extraction, DOM locations, inline code, links, math/image warnings, original URL and raw hash. No remote image fetching or rendered JavaScript. |
| `parse_pdf` v2 / bounded `pdf_worker` | Local PDF text, page/bounding-box and image references; existing uncertainty mechanisms. No new OCR, model fetching or visual interpretation. |
| `import_transcript.import_transcript`, `validate_text_source` | TXT/SRT/VTT validation and processing, segments and original times. TXT timestamps remain unknown. |
| `tools_transcribe/process_url`, `process_subtitle` | Inspected media/subtitle acquisition/transcription; network/native dependencies remain outside this adapter. No automatic media acquisition. |
| `parse_code`, `code_structure.inspect_structure` | Lossless local code blocks plus isolated AST metadata and comments. Input code is never imported, executed, built or installed. Syntax/resource uncertainty blocks completion. |
| `code_zip.inspect_zip` | Shared bounded in-memory path/symlink/count/size/ratio/CRC checks; no member extraction to disk. Removed a hash-only dependency on `batch` to keep download-only ZIP inspection independent of C16. |
| `ArtifactReceipt`, SHA-256, `storage` | Raw/download evidence unchanged by processing; existing immutable publication, safe path and integrity primitives reused. |
| C16 / SQLite / controller / queue | Never activated. Existing SQLite-contention HOLD remains. |

Acquisition is `scripts.cs50p_week`: explicit, bounded snapshot discovery and
inventory-hash-bound grants precede all network transfers. An approval still
binds source URL, type, byte ceiling, rights review, purpose and input inventory.
`discover --completion` emits v2; old callers default to v1. New default source
ceilings are omitted from legacy serialization to preserve v1 inventory hashes.
C08 still requires fresh approvals after rediscovery or any inventory change.

Source package selection prefers one official ZIP when offered; otherwise the
actual supported individual source hrefs are required. Alternate indexes/PDFs and
formats remain visible with reasons. Index traversal reads only explicitly supplied
snapshots and direct child file hrefs; it never crawls recursively. Identical source
URLs share an existing raw receipt despite different owner labels, while owner IDs
and provenance remain separate. Distinct URLs with identical bytes retain their
separate source evidence. No external repositories are cloned.

A missing href is MISSING; unsupported/unavailable automatic sources need review.
Only an explicit `mark-manual` decision creates MANUAL_PENDING. Its actual official
context URL is identified as context, not a downloadable file URL. `import-code`
requires a local file, SHA-256 and provenance. Automatic verified source files do
not contribute to manual incompleteness. NOT_APPLICABLE means no offer was found
on an examined page, never an inferred filename download.

Fallback decisions are per lecture/Short: transcript -> subtitles -> audio -> video.
Verified text fulfills that group and prevents selecting media. Invalid/empty text
fails structurally and retains its failed receipt. A lower candidate needs a new
inventory-bound approval; media is not grant-eligible here. External media, large
files, native transcription, rights and technical access need separate review.
No DRM/login/access-control bypass is implemented.

Processing is `tools_materials/week_processing`, a local adapter with separate
roots, locks and output receipts. It invokes reviewed pure/local parsers directly,
not `MaterialProcessor`'s download capability or C16. Outputs bind raw SHA, source,
section, owner, parser configuration and hashes of the adapter/parser/model source
files. HTML tasks retain code and sibling material IDs. Source ZIP member names and
hashes are retained separately; no disk extraction occurs. Reuse checks the raw
receipt and all output hashes and validates existing document/transcript models.
Interrupted output publication resumes only when retained bytes match exactly.
Acquisition receipts are never updated with processing outcomes.

Production `process()` always refuses execution until a separately reviewed host
network/resource-isolation gate exists. The available executable lane is restricted
to synthetic fixtures and tested with network calls forbidden. This is deliberately
an offline-tested processing plan/adapter, not a production worker release. The
operator CLI exposes planning and verification, without an execution escape flag. The existing assignment discovery imports the
pure `dom_path` helper from `parse_html`; the download runtime does not invoke
material parsing or load the native processing runtime.

Resource ceilings: source text/Python 1 MiB, raw ZIP 1 MiB, 64 members, 1 MiB/member,
8 MiB unpacked, ratio 100, shared ZIP inspection deadline 5 seconds. Existing HTML
1 MiB, subtitles 2 MiB, PDF 8 MiB, run transfer 32 MiB, raw archive 64 MiB, output
16 MiB and minimum free reserve 5 GiB remain bounded. Processing uses serial calls,
20 PDF pages, 1,000 HTML/PDF document blocks, 100 image references, 512 MiB PDF-worker memory,
20 seconds per PDF call and the inventory wall budget. Large/complex real slides may
require a separately reviewed policy rather than silently increasing limits.

Completeness independently assesses discovery, verified acquisition, validated
processing and manual obligations. Required identity/parent/type ledgers detect
missing or reparented rows and required-flag downgrades. URLs alone, download
receipts alone, unvalidated status labels or output existence cannot yield
FULLY_COMPLETE. Even a complete synthetic fixture leaves C26 HOLD. C07's acquisition-only FULLY_COMPLETE assertions in its test and runtime smoke
were intentionally changed to HOLD under this stronger report contract; their
acquisition/reuse assertions are retained.
