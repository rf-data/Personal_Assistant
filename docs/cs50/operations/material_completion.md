# Complete Course Materials: implementation and release status

Baseline: origin/master ad3078f59851fa71d076a8982bcab8b5b700c1a9,
15 October 2026. #39–#45 were confirmed merged through GitHub and the actual
master code tree. No automatic merges, actual course material/model downloads,
LLM/API execution, embedding inference, Qdrant uploads or production-data changes.
Existing Discovery/Selection/Lecture/Transcript/Knowledge/index algorithms remain
unchanged; the executor SRT-plan import is now delayed until actual SRT construction/CLI use. Materials are an additive input layer, not a parallel Knowledge model.

## Review stack

| Stage | PR | Scope | Base |
|---|---|---|---|
| 1 | [#48](https://github.com/rf-data/Personal_Assistant/pull/48) | snapshot catalog/gap analysis | master |
| 2 | [#49](https://github.com/rf-data/Personal_Assistant/pull/49) | resource/normalized artifact contracts | #48 |
| 3 | [#50](https://github.com/rf-data/Personal_Assistant/pull/50) | guarded existing downloader/receipts | #49 |
| 4 | [#51](https://github.com/rf-data/Personal_Assistant/pull/51) | HTML/notes/assignments | #50 |
| 5 | [#52](https://github.com/rf-data/Personal_Assistant/pull/52) | bounded PDF/slides/images | #51 |
| 6 | [#53](https://github.com/rf-data/Personal_Assistant/pull/53) | source file import | #52 |
| 7 | [#54](https://github.com/rf-data/Personal_Assistant/pull/54) | processing plan/status/resume | #53 |
| 8 | [#55](https://github.com/rf-data/Personal_Assistant/pull/55) | isolated future Knowledge/index mapping | #54 |
| 9 | [#56](https://github.com/rf-data/Personal_Assistant/pull/56) | CLI and six-course offline E2E | #55 |
| 10 | completion follow-up | manuals, coverage, regression and verified boundary fixes | #56 |

All PR trees were constructed from the tested final additive files. Public stage-9
source tree equals local implementation c2e31dd exactly. There are no private
local infrastructure reports or unrelated operational inventories in this stack.
Review in order and control bases after integration; nothing is automatically merged.

## Snapshot coverage

653 primary Discovery candidates, 700 preserved media variants, 6,674 raw snapshot
link/image occurrences (8,027 catalog rows). Raw occurrences include navigation,
fragments, third-party tools and browser-rewritten references, not unique materials.
100 browser-local/inline occurrences are explicitly blocked as remote downloads;
raw source attributes remain available. Unproven original remote image URLs remain
unknown rather than being fabricated from saved browser paths.

| Course | Sections/main lectures | Candidate offers | HTML parser route | PDF parser route | Separate path/unsupported | Blocked | SRT/TXT offers |
|---|---:|---:|---:|---:|---:|---:|---|
| cs50x | 12 | 233 | 35 | 22 | 160 | 16 | 36/36 |
| cs50_python | 10 | 145 | 30 | 20 | 85 | 10 | 10/10 |
| cs50_sql | 7 | 77 | 21 | 14 | 42 | 0 | 7/7 |
| cs50_ai | 7 | 77 | 28 | 7 | 42 | 0 | 7/7 |
| cs50_web | 9 | 77 | 15 | 9 | 53 | 0 | 9/9 |
| cs50_cybersecurity | 5 | 44 | 12 | 6 | 21 | 5 | 5/5 |
| Total | 50 | 653 | 141 | 78 | 403 | 31 | 74/74 |

Counts are route eligibility, not HTTP success or selected bulk downloads.
SRT/TXT totals include three CS50x language versions; the existing timed Knowledge
path selects the 50 English main-lecture SRTs. VTT offers remain zero. HDR/SDR,
resolution/language variants remain verbatim in the complete Discovery graph.
There are no directly discovered individual source-text files in these primary
candidate lists; code indexes/PDFs/ZIPs need separate detail inventory before
claiming file coverage. ZIP (44 offers) and Keynote .key (23 offers), native PPT/PPTX,
private/external resources and unsupported media retain reasons, not fake success.

No new real materials were downloaded, raw-imported or persisted as normalized
production artifacts. Five existing notes/assignment snapshots were parsed read-only
in tests (cs50x one, Python two, AI two). Other real PDFs/images/code files have not
been fetched or professionally quality-reviewed. Synthetic E2E covers one mixed
lecture (4 materials), ten Python lectures (13), and all six/50 lectures (53), with
three additional explicitly synthetic materials in the first lecture. It does not
simulate successful retrieval for every known link. Remote image references remain
unfetched; embedded image byte extraction is tested separately.

## Provenance and technical boundaries

The complete graph retains original course/section/lecture/resource/parent IDs,
URLs, language and variants. Artifact and block IDs bind exact raw/config hashes.
DOM/page/bbox/line/character locations never become guessed timestamps. Existing
transcript evidence is not repurposed for untimed materials. Raw bytes are immutable;
receipts and exact expected publication hashes permit interruption recovery.
Unknown/corrupt/stale files are conflicts, never silently repaired or adopted.

Parser version/config changes require a new explicit processing workspace; output
is not overwritten. Implementers must bump parser versions for behavior/backend
changes; no automatic binary/library-version fingerprinting is claimed. Failed raw-download receipts are visible as failed status with their stored HTTP/
transport reason; this observation does not authorize parsing an unverified source.
The planned
stages describe the material path, not general Legacy ResourceTask execution.

Partial HTML boilerplate/layout, PDF reading order/table overlap/code classification,
unverified math, missing OCR and unknown live licenses/availability are explicit.
The normalized material index contract is read-only, distinct from transcript
collections; embedding and upload are not implemented or released. Knowledge
extraction from non-temporal blocks needs a future explicit evidence bridge and
semantic/educational evaluation. No current Knowledge schema was changed.

## Verified boundary follow-ups

A failing Fake-HTTP regression showed HTTPX requested gzip/deflate while the guard
refused compressed responses. The guard now explicitly requests identity encoding;
the same regression passes, without changing CS50Executor or its SRT path.

Snapshot inspection found 99 browser-local/inline image occurrences and one anchor.
Catalog retains raw attributes and blocks them as remote sources. HTML parsing
preserves raw image references in block data and leaves original remote URLs unknown
for browser-local paths. This prevents a saved-browser path from appearing as a
proven official asset URL. No files were fetched to guess missing URLs.

Local imports retain explicit format but leave MIME unknown instead of choosing
an arbitrary allowed HTTP Content-Type. Syntax is checked by the selected parser;
HTTP imports retain the actual validated response MIME.

A PATH-only SDK-guarded material CLI import exposed inherited application/API-key
settings through the executor’s top-level SRT adapter import. Only that import was
moved into its constructor/CLI uses. The existing module.CS50AdapterPlan re-export is retained lazily; a targeted
regression exposed that compatibility dependency, which was corrected without
changing old assertions. Material help/imports now need no settings or
keys; actual SRT construction uses the same model and algorithms. Existing executor,
adapter, binding and lazy-import regressions were rerun.

A four-case failing regression also showed that failed raw-download status had
been obscured by missing-artifact verification. Read-only inspection now returns
the checked failed receipt/error; parse still requires actual raw verification.

Full regression and final follow-up results are recorded in the linked
[test matrix](../evaluation/material_tests.md); known TXT failures remain separate.

## Remaining approvals and next operation

1. Review/integrate this explicitly stacked implementation; no automatic merge.
2. Review license/terms, exact URLs and scope of one real CS50-Python lecture:
   Notes HTML + slides PDF + one publicly linked assignment or source index.
3. Run the documented one-resource download preview. Release --execute-download
   separately with a reviewed plan; then release local parse separately. Review
   actual content, DOM/page/code/image fidelity and hashes before widening scope.
4. A bounded additional crawl/detail inventory, asset retrieval, native slides/ZIP
   support and real parser gold evaluation need separate review. No live completeness
   claim until checked snapshots and reachability/license evidence exist.
5. Material Knowledge/embeddings/productive index upload require separate explicit
   schema/model/quality/collection approvals. Keep six legacy TXT timestamp failures
   outside this material implementation; no weakened assertions or migration.

The next real operation is a controlled multi-material Python week-0 pilot after
these manual releases, not an unattended six-course download.
