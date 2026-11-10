# M2.2a — Verified Lecture Source Handoff

Status: isolated synthetic proof of concept; not a product release or M2.2 real-source acceptance.
Reference: `8190fcc805f4b361f1b91b23805e8941691deab2` (`rf-data/Personal_Assistant`).
Date: 2026-11-08. All changes and executions are in the task-owned `/tmp` copy.

## Decision

Source verification and search readiness are different contracts. A successful FTS
query proves that a selected index can answer a query within its retrieval budget;
it neither proves full lecture coverage nor grants summarization permission.
Summarization consumes ContentStore/ContentReader publication bytes, not search hits.
A separately approved path may use a fully verified publication even when the MVP
source phase is `published` or `index_pending`. Existing `ready` remains unchanged.
Unknown, `preparing`, `publication_pending`, and explicit HOLD phases are rejected.
An accepted phase alone never establishes readiness.

The existing `ContentStore.project_content_for_index` read-only API performs the
same `_project_locked` source verification used by `ContentIndex._export`. Reuse
that API unchanged once per verification. Keep every source-side integrity check;
do not duplicate a reduced verification algorithm. The returned projection has
no activated generation and is not search readiness. Do not initialize/build an
index or execute a search on this path. Its existing conservative record limits
remain; unsupported publications fail closed.

The new contract is opt-in (`--source-contract verified-lecture-source-v1`) and
synthetic-only. It requires `VerifiedBatchApproval`, schema 3, adapter
`verified-lecture-summary-m22a-v1`, a complete M2.1 plan, and the exact
`source_verification_sha256` proposed by planning. Planning never manufactures an
approval. Schema 2 / legacy approvals do not authorize schema 3 processing.
`legacy-ready` remains the default; M1 still requires the original `ready` phase.
The engine and slicing/consolidation algorithms remain M2.1 algorithms. The new
adapter identity is recorded in the outer intent; existing engine input identity
continues to describe the reused M2.1 algorithm. Current code bytes bind both.

## Required checks and retained implementations

| Requirement | Verification / reason |
| --- | --- |
| Explicit selection and ProcessingApproval | `m1.historical_approval`: typed approved status, exact actor/actions, expiry, raw/plan/parser/source scope, approval SHA, historical implementation evidence. This is historical processing authority, not permission for current summary code. |
| Current summary authorization | Schema 3 approval binds current revision and actual Python bytes, identity, config, limits, complete plan and verification digest; FakeLLM only, retries 0. Checked before output-root creation, each request, after each reply, and final release. Approval file must remain byte-identical. |
| Current ACL/course/source scope | ContentStore/Reader real authorization; ACL revision bound to evidence. Recheck real rights and revision for every dispatch, after replies, cache returns and final publication. Any ACL revision change rejects, even if actor still has access. |
| Committed publication | Existing projection `_load`: published parsed row, verified source version, exact row/model identities, parser configuration, committed runs, available artifacts and raw reservations. `mvp.verify_persisted` additionally binds local source evidence and intent. |
| Raw / payload / projection integrity | SHA/size/state validation of all referenced bytes, raw-to-input equality, normalized payload-to-bundle equality, plan/receipt/implementation artifacts; unchanged projection gate cross-checks binding, quality/handoff, aggregation, exclusions, block/locator rows. |
| Reader completeness | Shared M1 traversal reconstructs every projection block through all pages and bounded text windows. Exact order, IDs, type, role, length/hash and text; no duplicates, omissions, truncation or foreign locators. New path also checks DTO/window version IDs, block IDs, exact window progress and complete public locator/structure fields respecting Reader redaction. |
| Version / implementation binding | Exact source/parsed/parser versions, historical parser implementation revision, current full-code hash/revision, raw/payload/projection digests and full source inventory enter approval/verification. Explicit requested version only; no implicit latest version. |
| Source stability | Retain existing exclusive MVP lock from initial inventory through handoff, processing and release. Inventory SHA, current authorized parsed view and ACL revision rechecked during verification, every request/reply and final release (including after final manifest write). Changes reject, never repair/retry. |
| Complete summarization evidence | Unchanged M2.1 planner reconstructs every eligible codepoint exactly once, binds original locators and request hashes, enforces budgets. Checked batch records, shared FakeLLM engine validation, global consolidation and original references retained. Input/citation coverage are distinct; excluded blocks are explicit. |

## Checks intentionally belonging only to retrieval

Index build ownership, activation/generation, FTS database/manifest/schema integrity,
MATCH execution, hit hydration, ranking, query deadline and three retrieval gold
tasks remain mandatory on retrieval paths. A summary never reads those index
artifacts; their validity cannot establish or revoke content integrity by itself.
The separate summary contract does not assert search usability. A pending or failed
index stays pending/failed. This path does not relax ProcessingApproval actions or
convert historical retrieval acceptance into current approval. It merely does not
invoke retrieval actions. `ProcessingApproval` is unchanged, including its three
retrieval tasks and original action tuple.

## Security equivalence and limits

For a selected synthetic publication, all existing source-side retrieval validation
is executed by the identical existing verifier, and the original Reader checks
are retained and strengthened. Search-only predicates are inapplicable to the
summary consumer. That supports a bounded synthetic handoff claim, not an
unconditional product-security equivalence claim.

The MVP file lock is cooperative. An arbitrary same-UID writer that ignores locks
could mutate and restore bytes between inventories; code already loaded in memory
also cannot be attested atomically by rehashing files. ACL checking and dispatch
are not one transactional operation. A revocation during an in-flight request
cannot undo that request; post-reply verification prevents subsequent dispatch
and completed-result acceptance. Already dispatched text and raw replies may remain
in private HOLD evidence; revocation does not retroactively erase them. The path
is restricted to FakeLLM and synthetic
sources, with these limitations carried into M2.2 review. No live provider release
is implied. External concurrent writers would need a common lock/lease protocol
or immutable snapshots plus explicitly defined revocation semantics.

Full source-inventory binding is intentionally conservative: unrelated index
changes or a benign ACL update invalidate the summary approval. It costs additional
I/O and repeated code hashing. Reader and projection limits, Linux sealed-file
support and existing wall limits can produce HOLD. No performance optimization,
timeout increase or retry is included. Stage 1/2 ContentStore experiments are
absent; B1, ContentStore and FTS implementation files are unchanged.

FakeLLM excerpts provide mechanical coverage evidence. `unreviewed` remains on
all summaries; semantic correctness, pedagogical quality, licensing and real
material acceptance remain independent requirements.

## Synthetic evidence methodology

The small proof stops the original MVP immediately after successful publication,
before any index exists, then forbids FTS build/query entirely during summary.
The long proof uses 171 blocks with 1,200/1,800/2,800-character synthetic passages,
226 slices and eight batches (7 × 32 + 2). The existing MVP really parses, checks,
publishes and builds its index. A single public FTS call then receives the original
`Unavailable("FTS query/database unavailable")` error via deterministic fault
injection at the public search seam. This is not a native SQLite timeout
reproduction; internal index-build verification may run its existing FTS check.
No failed request is retried and no source state is rewritten by the harness.
Summary planning, generation and cache/restart forbid search and ingestion.
A second process checks the cached result with FakeLLM and network forbidden.

Negative tests corrupt only fresh synthetic roots. For targeted DB corruption,
the harness temporarily drops immutability triggers and restores their exact DDL
before verification, so the test exercises data checks rather than a missing
schema trigger. A consistent synthetic owner-transfer fixture is needed because
the public store intentionally has no owner-transfer API; actual read grants and
revocations use the real `set_source_grants` API. Product code never changes DDL.

Machine-readable results, exact commands and measurements are in the companion
validation report and task delivery evidence. Early development failures are
recorded separately and are not counted as passing validation.

## Transition to M2.2 Real-Source-Acceptance

1. Review this additive contract and its threat model independently; decide whether
   cooperative source locking is sufficient and define ACL revocation semantics.
2. Integrate an approved patch and durable records through the normal review
   process in `master`. This task is explicitly prohibited from committing,
   pushing, updating PRs or merging; integration is pending.
3. Select one explicitly authorized real HTML lecture and exact version. Verify
   source ownership, provenance/license review and original valid ProcessingApproval.
   Retain historical bytes; current implementation needs a separate current summary
   approval. Review and remove the synthetic-only restriction only in that task.
4. Run plan-only verification in an isolated real-source root with no downloads or
   live provider calls. Review the complete plan, exclusions, byte/request budgets,
   raw/payload/projection fingerprints, Reader blocks and original locators.
5. Supply an operator-issued schema 3 approval for those exact bytes and plan, then
   execute FakeLLM-only; require full input coverage, checked consolidation and
   source-stability evidence. Review citation coverage and all references separately.
6. Record summarization acceptance and search acceptance independently. FTS retrieval
   still has the unchanged 2-second contract, gold tasks and no retries. An FTS HOLD
   does not become a successful search or a blanket release.
7. Require explicit human subject-matter review before real-source acceptance.
   Any future live-provider path requires its own approved egress/revocation design.

## Artifact lifecycle

The protected M2.1 checkout and its staged/unstaged/untracked evidence are not edited.
The isolated copy has detached metadata referencing the existing commit via a
read-only object alternate; no new commit, branch, linked worktree or remote was
created. The `/tmp` copy, patch and reports are deliberately retained because they
are the only new delivery copies and integration is prohibited. Default-branch
integration and repository-lifecycle completion remain pending, not falsely done.
