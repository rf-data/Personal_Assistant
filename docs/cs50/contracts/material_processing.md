# Material plan and resume v1

MaterialPlan stores all six original CourseDiscovery graphs and the 653 primary
candidate bindings. Media variants remain in those graphs and the occurrence
catalog, not additional automatically selected downloads. Every logical lecture
assignment is checked against actual main lecture nodes and section membership.
Resource/lecture IDs remain distinct; ai/0 and shared section assignments remain.
Plan filters support source/material, lecture, section, course and explicit six-course
scope. DOWNLOAD and PARSE_DOCUMENT task IDs/dependencies are deterministic sidecars;
these existing ResourceAction names do not invoke the general Lecture runner.

Catalog-only raw snapshot links require explicit classification before planning.
A discovered link never implies licensed, reachable or downloadable content.
Unsupported media/platform/archive types retain reason/status with no tasks.

Raw verification is a separate step from parsing. Receipt histories record
selected/downloaded/verified/parsed/normalized/completed. Parsed is a write-ahead
proof; interruption after any exclusive publication can resume only if exact
binding, parser configuration, raw hash, expected normalized value and image
hashes agree. Completed status is revalidated against bytes and document models,
not existence. Changed parser/config/raw bytes conflict; use a new explicit
workspace/reprocessing generation rather than overwriting a prior generation.

Single workspace writer via flock. No inferred source paths or filename searches.
Artifacts use SHA-derived material/document IDs and portable relative paths.
No destructive repairs, automatic downloads on parse, Knowledge extraction,
embeddings, uploads or legacy runner changes.

## C19: controlled PDF-v2 jobs

C16 optionally exposes `material_parsing` for explicitly approved local PDF receipt
bundles. C18's existing parse stage also accepts bounded PDF-v2 after lifecycle
tests. Both reuse `MaterialProcessor.parse/inspect`; no new parser or receipt model.
Inside the fixed C16 adapter only, the PDF worker inherits the owned job process
group and arms a parent-death signal. Its resource limits never raise inherited
hard limits. Direct parsing and C13 retain their existing standalone worker groups.
Original Raw/Receipt/Normalized/image files are never modified: adapters use a
new private copy and workflows retain earlier generations during explicit resume.
[Input/output contracts, limits, ownership and remaining blocks](../../job_control/pdf_lifecycle.md).

Initial processing tests: 7 passed, 8.09 seconds, including all six graph roundtrip,
653 identities/task uniqueness, missing raw dependency, actual lost publication
acknowledgement/resume, changed config, corruption and unsupported no-write path.
