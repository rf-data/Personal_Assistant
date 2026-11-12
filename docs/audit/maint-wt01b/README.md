# MAINT-WT01B – Preservation & Restore Readiness

2026-11-12. **Assessment and synthetic procedure validation delivered;
real preservation, operational reproducibility and WT01B integration pending.**
All **111 existing registered worktrees** retain `WORKTREE_LIFECYCLE_HOLD` and
`safe_to_remove=false`. No actual worktree data was backed up, copied or restored.
No real worktree/branch/ref/registration/archive was changed or removed.

## Scope and retained task identity

Assigned worktree:
`<PROJECT_ROOT>/Personal_Assistant-maint-wt01b`.
Branch: `maint/wt01b-preservation-readiness`.
Entry and final HEAD: `f209af557e2e521ceaff2e05c2215efff3baf3b0`.
Both task artifacts were present at entry. This run created no real Git branch,
remote branch or registered worktree. Synthetic repositories were temporary fixtures
only. All permanent changes/evidence are inside this assigned worktree.

The parent AGENTS.md, [lifecycle policy](../../maintenance/worktree_lifecycle.md)
and [WT01A report](../maint-wt01a/README.md) were read. Parent policy is unchanged.
The task-specific prohibition on commits, pushes, merges and PR creation takes
precedence over the general completion workflow. No new commit SHA exists.
WT01B documents are not integrated into master; the assigned checkout, branch,
uncommitted files and ignored private evidence must remain for operator review.
This is the concrete reason lifecycle completion/cleanup remains pending.

## Current hosting evidence and completeness

Repository identity is `rf-data/Personal_Assistant`, numeric ID `1235820542`,
node ID `R_kgDOSakf_g`, actual default `master`; configured origin agrees.
The connected GitHub plugin performed read-only REST GETs. Retained fields are
allowlisted repository/branch/PR identities, SHAs, state/draft/merge flags and
timestamps. No PR bodies, comments, titles, credentials, profiles or document
contents were saved in the hosting snapshot.

| Collection | Pagination to exhaustion |
| --- | --- |
| PRs, all states, creation order ascending | 100 + 46 + explicit empty page = **146** |
| Branches with HEAD SHA | 60 + explicit empty page = **60** |
| Repeated PR traversal | 100 + 46; identical retained projections |
| Repeated branch traversal | 60; identical retained projections |

The terminal short pages and additional empty pages establish exhaustion, not a
search-result limit. Repeated repository identity and explicit master checks
agreed. PR numbers and branch names are unique. All PR base repository identities
agree with this repository; all head repository identities are present. All 11
open PRs are drafts, have an existing matching same-repository branch/SHA, and
none is marked merged. Closed historical PRs need not match today's branch SHA;
the observed live-head differences for PRs #2/#3/#4 are historical branch reuse,
not identity errors. Deleted historical head branches are also valid observations.

Snapshot time: **2026-11-12T11:28:53.516Z**. Acquisition provenance records the
verification window and page counts. The initial page reads preceded that window;
the second stable traversal is the timestamped consistency evidence. This is
point-in-time evidence, not an atomic transaction across GitHub endpoints.
Snapshot SHA-256:
`c532762a138ad70524c2787bf93c8affc71d266ea34f825e11e624ce9d857d90`.

Live master and cached origin/master both equal
`f209af557e2e521ceaff2e05c2215efff3baf3b0`. The snapshot was fresh (under 24 hours,
not future-dated) during both audits. A final live master GET at
**2026-11-12T11:38:54.092Z** still agreed. No fetch or tracking-ref update occurred.

## Updated inventory and WT01A comparison

The integrated, unchanged `scripts/worktree_manager.py` was run twice with the
fresh complete snapshot. Both audit commands exited **2**, the expected HOLD
result. Authoritative final inventory time:
**2026-11-12T11:38:52.799950+00:00**. JSON is authoritative; CSV was serialized
from that same JSON, without another scan. Registry/refs were stable during each
audit and hosting verification passed for all records.

| Classification | WT01A | WT01B |
| --- | ---: | ---: |
| ACTIVE | 55 | 55 |
| ARCHIVE | 7 | 7 |
| REMOVABLE_CANDIDATE | 41 | 41 |
| REVIEW | 7 | 8 |
| Total / lifecycle holds | 110 | 111 |

There are still eight prunable registrations, eight unavailable statuses and
eleven incomplete/unavailable disk observations. Final counts: 29 worktrees with
tracked changes, 26 with untracked files and 48 with ignored indicators. Apparent
observed bytes are a lower bound of **7,515,970,999**, excluding Git administration;
this is not a reclaimable-space estimate. In-flight task evidence/caches can change
these sizes and file counts between scans.

The exact prior authoritative private WT01A JSON was read for the comparison.
No prior registered path disappeared. Only one existing classification changed:
WT01A's own checkout moved from ACTIVE to REVIEW. It is no longer the execution
checkout, its tracked/untracked deliverables are integrated, and four observed
symlinks trigger review. It retains ignored evidence/environment artifacts.
The new, already-assigned WT01B checkout is ACTIVE. These observations explain
the totals; no regression in candidate logic is inferred.

GitHub now has one additional branch, `maint/wt01a-inventory-governance`, and
one additional PR, [#175](https://github.com/rf-data/Personal_Assistant/pull/175).
That PR merged at 10:58:25Z on November 12, from head
`09c7a6e99ab089ef1516f54c1bced8cafa5b19bb` to merge
`f209af557e2e521ceaff2e05c2215efff3baf3b0`. WT01A's old master
`c651e1d83c613de9bfb693380ac9856d72865121` is an ancestor of current master;
the manager and WT01A report are present in current master. WT01A's report's
historical "integration pending" statement describes its original handoff time.
WT01B did not perform that integration or change the old evidence.

## Individual candidate decisions

| Candidate | Exact branch | Exact HEAD | Decision |
| --- | --- | --- | --- |
| [c2302c](c2302c.md) | `feat/c23-02c-recovery-operations` | `f33df74ff09eb7d50223776080c6dd3048955a7c` | KEEP / HOLD |
| [c2303](c2303.md) | `feat/c23-03-reimport-binding` | `42bbd8ae65110138bee82542ce02d99ec7d84be3` | KEEP / HOLD |
| [c2304](c2304.md) | `feat/c23-04-content-read-api` | `ada2f185fd387312823f844fe99d9e9a54236e00` | KEEP / HOLD |

The three exact filesystem/registry identities agree, local branches and commit
objects exist, all three HEADs are retained by current master, and no matching
open/draft PR was found. The live candidate branches are absent. PRs #78/#79 match
branch and SHA; #80 matches branch but has final head
`b054a041bcef82d8ab5c7e3bbdb63e40ac689619`. c2304's exact earlier HEAD was checked
directly as an ancestor of that PR head, its merge and the verified baseline.

All candidates still receive the machine label REMOVABLE_CANDIDATE. Expanded
ignored/untracked enumeration, index-flag review, metadata traversal and pointer
checks found no extra artifacts, symlinks, nested Git repositories, gitlinks,
special files, hardlinked regular files, empty directories or mount boundaries.
No candidate was modified. Clean Git status does not discharge any human gate.

MAINT-02/03 WT012–WT014 and BR035–BR037 require individual decisions and still
lack ownership/nonuse, destination, backup, restore and data-disposition evidence.
MAINT-02 lists 11/11/10 historical document variants respectively. Their historical
blob objects remain available; all differ from current default-path versions.
Exact commit ancestry preserves them in history but does not replace an operator's
historical-document decision.

The code explicitly requires an external ContentStore root. Required real data
roots, source archives, database consistency, provenance/ACL records and retained
dependencies are not mapped by an owner. Historical validation references an
external project interpreter; tracked dependency declarations/locks alone do not
prove that historical environment remains reproducible. No external archive was
listed recursively, moved, copied or synchronized. Three visible same-UID CWD
observations produced zero candidate matches; other users/hosts/namespaces, open
files and ownership remain unknown. **Reproducibility is not verified for any
candidate.** No real restore test or backup-existence claim is made.

## Procedure and synthetic validation

The [preservation/restore protocol](../../maintenance/worktree_preservation_restore.md)
defines exact identity/approval binding, a bounded capture, standalone Git object
closure, filesystem/index/external-data manifests, SHA-256 integrity and a trusted
external digest, independent restoration, fail-closed outcomes and acceptance.
It provides no production copy, remove, prune or branch-deletion command.
No update to the existing read-only inventory tooling was necessary.

Validation used Python 3.11 and installed Git, with no dependencies installed or
application services started. **61 distinct synthetic tests passed**:
31 existing manager tests, 10 existing independent manager tests, and 20 new
preservation tests. The original 56-test combined log predates five additional
preservation cases; `preservation-tests-verified.log` validates the final 20-case source.
The manager source and existing tests are unchanged.

The new experiment creates only its own temporary synthetic repositories. Its
success test preserves committed, ignored/untracked bytes, newline filenames,
empty directories and executable modes, then makes the original fixture path
unavailable and restores from a bundle and payload with an empty object store.
The independent reader checks a trusted manifest SHA-256, exact paths/types,
file hashes/modes and duplicate keys. Restore verifies exact filesystem inventory,
HEAD and full Git object checks, without alternates or remote source access.

Failure cases cover altered/missing payloads; incorrect manifest digest; duplicate
JSON keys/paths; incomplete capture; extra payloads; traversal/absolute/.git paths;
symlinked sources/archive roots; nested repos; hardlinks/FIFOs; dirty staged/tracked
state and masked indexes; count/byte limits; mutation during capture; reused
destinations; mode mismatch; repository/HEAD mismatch; missing incremental-bundle
prerequisites; omitted committed files; permission denial; ENOSPC and Git timeout.

This is a single-process reference experiment, not a production archive engine.
Descriptor-relative concurrency hardening, full metadata/index restoration,
mount isolation, durability and application data acceptance remain future work.
Synthetic success never establishes restoration readiness of actual worktrees.

## Evidence, handoff and preservation checks

Private local evidence is ignored by Git under `artifacts/maint-wt01b/` (0700
directory, 0600 files). It includes:

- `hosting-snapshot.json`, `hosting-acquisition.json` and `final-master-check.json`:
  sanitized hosting evidence and final live-master recheck.
- `inventory.json` / `.csv` and authoritative `final-inventory.json` / `.csv`:
  same-scan JSON/CSV pairs; initial and final classification-delta JSON records.
- `candidate-assessment.json` and task-local `assess_candidates.py`: registry,
  index and filesystem metadata, historical/dependency object references and
  limited process metadata; no content archive.
- `before.json`, `validation.json`: registry/refs/stashes, all 103 accessible
  worktree index digests, task HEAD and parent-policy preservation comparison.
- `tests.log`, `preservation-tests-final.log`, `preservation-tests-verified.log`,
  `evidence-sha256.json` and
  `handoff-validation.json`: test, integrity and patch verification evidence.

All durable authored changes are retained in the assigned checkout and in
`artifacts/handoff/maint-wt01b.patch`. The patch excludes private snapshots,
inventory data, temporary helpers and logs. It is checked against the current
authored files using read-only reverse-apply validation; no actual worktree data
is copied into a test checkout. `git status` and `git diff --check` are checked
at handoff. No commit/push/merge/PR was made and no WT01B integration is claimed.

Uncommitted durable changes: `.gitignore`, this report and three individual
assessments, the link in `docs/maintenance/worktree_lifecycle.md`,
`docs/maintenance/worktree_preservation_restore.md`, and
`tests/test_worktree_preservation.py`. Private evidence and the patch remain
ignored. No unrelated pre-existing uncommitted edits were present at entry.
No actual Git artifacts were removed; every pre-existing worktree is retained.

## Proposed next phase and explicit HOLD decisions

Propose, without starting it, a separately authorized **MAINT-WT01C: owner and
dependency closure plus preservation preflight**. Obtain exact-path owners,
confirmed nonuse windows, external artifact and environment recipes, historical
document decisions, and private archive/restore destination approvals for this
three-item sample. Harden and independently review the capture/verification
implementation using synthetic fixtures before approving any real preservation.
Only then consider a separately authorized real preservation/restore exercise.

| Operation | Current decision |
| --- | --- |
| All existing worktrees and branches | KEEP, `WORKTREE_LIFECYCLE_HOLD` |
| Actual archive/copy/synchronization | HOLD; no exact scope/destination/owner approval |
| Actual restore or application recovery | HOLD; no approved roots, dependency closure or independent acceptance |
| Removal, pruning, branch deletion | HOLD; explicitly outside this task; MAINT individual gates remain |
| WT01B commit/push/PR/merge | HOLD under explicit task prohibition |
| WT01B branch/worktree cleanup | HOLD; uncommitted deliverables/private evidence and integration pending |

No downstream phase or unrelated task was initiated. Unknown ownership and
repository/data state remain reasons to retain sources, never to discard them.
