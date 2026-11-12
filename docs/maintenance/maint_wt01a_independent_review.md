# MAINT-WT01A independent inventory and governance review

2026-11-11. Inventory and governance only. No worktree, branch, archive, stash or
project data was removed, moved, synchronized or pruned. No commit, push, merge or
PR creation is authorized in this task. Integration into `master` therefore remains
pending; this document does not claim completion of the repository lifecycle.

## Policy assessment

The parent `/home/robfra/0_Portfolio_Projekte/AGENTS.md` was read and left unchanged.
It provides a sufficient governance baseline: inventory before creation, reuse only
when clean and task-compatible, task identity records, explicit lifecycle reports,
preservation of ignored/untracked data, reproducibility criteria, exact-path operator
approval before removal, and `WORKTREE_LIFECYCLE_HOLD` when checks cannot be completed.
Its desired capacity is one persistent `master` plus at most four active worktrees;
this is a planning target and does not authorize reducing the existing inventory.

The policy needs an implementation and operational evidence rather than another
policy edit. A future operation still needs ownership, non-use, artifact mapping,
backups and restore evidence, and per-path decisions. The parent commit instruction
is overridden here by the explicit task prohibition on committing. The repository
requirement to integrate durable records remains pending under the same prohibition.

## Existing implementation and historical records

`scripts/repository_audit.py` already inventories Git/document history and redacts
private paths. It is broader than a worktree lifecycle tool, opens selected tracked
document blobs, and assumes usable worktree paths in parts of its traversal. It
does not provide a complete fail-closed worktree inventory with missing-registration
handling, approximate disk usage and the requested lifecycle classifications.

Relevant preserved evidence includes:

- [MAINT-01 inventory](../audit/maint01/README.md).
- [MAINT-02 inventory](../audit/maint02/README.md) and
  [worktree recovery review](../audit/maint02/worktree_recovery.md).
- [MAINT-03 operator decisions](../audit/maint03/operator_decisions.md).
- [MAINT-04 review](../audit/maint04/README.md).
- [MAINT-05 backup and independent restore](../audit/maint05/README.md).

MAINT-05 preserved six specifically authorized Git branch histories. Its successful
bundle/restore evidence does not cover arbitrary current worktree data and does
not authorize removal. Existing application material/archive pipelines serve a
different purpose and must not be used to synchronize or relocate worktree data.
No existing historical document was overwritten by this independent review.

No `graphify-out/graph.json` was present. The graphify skill's targeted-search path
was used for this focused repository inspection; no graph was built or dependency
installed. Graph extraction token usage: zero.

## Lifecycle model

The classification describes the next review priority. None grants removal
permission, proves non-use or certifies restoration.

| Class | Conservative meaning | Next action |
| --- | --- | --- |
| ACTIVE | Primary/current/default checkout, lock, known open PR, local changes, untracked work or commits outside the baseline | Keep and identify the task owner |
| ARCHIVE | Otherwise understood checkout with local ignored artifacts requiring preservation review | Plan preservation; do not move or copy anything automatically |
| REMOVABLE_CANDIDATE | Technical inventory gates pass, including retained ancestry, usable clean checkout, complete fresh hosting observations and no uninspected local data indicators | Review ownership, documents, artifacts and explicit authorization individually |
| REVIEW | Missing, incomplete, inconsistent or ambiguous evidence | Resolve the uncertainty before any action |

Every row keeps `safe_to_remove=false`, a lifecycle hold and pending human gates.
A merged PR alone never establishes safe removal. Squash/rebase merges require
review of actual integrated changes and durable documents, because commit ancestry
may not establish integration. Equally, a branch-name match does not establish that
the current branch tip is the PR's merged tip. Fork PRs need repository identity.

Primary and persistent `master` checkouts are protected. Known activity takes
precedence in the classification; an ACTIVE row can still have missing-path or
observation errors. Inspect those errors independently of the class label.

## Inventory and audit commands

Use Python 3 and Git; no additional packages are needed. Run from the assigned
worktree, naming that exact repository root when invoking from elsewhere:

```bash
python3 scripts/worktree_manager.py inventory --repository "$PWD"
python3 scripts/worktree_manager.py audit --repository "$PWD"
```

Both observation paths collect metadata without changing source repositories,
indexes, refs or worktree registrations. Audit returns exit 2 for lifecycle holds;
exit 1 means collection failed. An inventory exit 0 means observations were emitted,
not that any worktree is safe to remove.

The concurrently observed implementation also accepts an explicit report-only
`--output-dir` option, under a new directory in the invoking worktree's `artifacts/`.
It exports JSON and CSV using exclusive file creation and private permissions.
That option writes report files and therefore needs a final design decision against
the task's literal "both must be strictly read-only" constraint. A stdout-only
interface with caller-managed report capture avoids this ambiguity. No export
option was used for the real independent inventory; this reviewer captured stdout
and separately serialized CSV from the same observations.

Hosting metadata is supplied explicitly rather than fetched implicitly:

```bash
python3 scripts/worktree_manager.py inventory \
  --repository "$PWD" \
  --hosting-repository rf-data/Personal_Assistant \
  --hosting-snapshot artifacts/handoff/maint-wt01a/github-hosting-review.json \
  --max-disk-entries 50000 --disk-seconds 1
```

The current metadata-only hosting schema uses `schema_version`, `repository`,
timezone-aware `observed_at`, `complete`, a branch-name-to-SHA `branches` map, and
`pull_requests`. PR entries carry only number, state, draft/merged indicators,
head/base branch and repository identities, and head SHA. Titles, bodies, comments,
diffs, users and credential-bearing remote URLs must not be copied into reports.
Freshness, completeness, repository binding and agreement of live `master` with
cached `origin/master` are separate checks. Missing metadata is not absence evidence.

JSON is authoritative. CSV preserves nested per-worktree structures as JSON cells;
consumers should decode those cells explicitly. CSV scalar formula prefixes are
escaped by the current serializer. Generated observations belong in ignored private
artifact directories, not in tracked documentation or synthetic fixtures.

## Reproducibility and evidence boundaries

A reproducible worktree needs all of the following:

1. Required commits and local changes retained under identified Git objects/refs or
   an approved backup, with provenance and integrity verification.
2. Relevant ignored/untracked data preserved or individually approved for discard.
3. Environment, dependencies, runtime configuration and external artifact bindings
   documented without exposing secrets.
4. An independent restore to an approved fresh destination, with the source hidden
   where practical; hash/object checks and representative validation must succeed.
5. Durable completion records and actual default-branch integration verified.

A clean Git status is insufficient. Disk usage is an approximate lower bound,
excludes shared `.git` storage and symlink targets, may stop at a time/entry budget,
and does not estimate reclaimable disk space. Ignored-directory indicators do not
enumerate every child. Submodules, symlinks and nested repositories require their
own review. A filesystem changing during collection prevents an atomic-snapshot
claim even when HEAD, index and ref checks pass.

The two external paths named in the task were inspected only for availability and
root metadata. The Drive artifact root was present; `/mnt/data` was absent. No child
listing, document reading, checksum scan, copy, restore or archive synchronization
was performed. Availability does not establish that artifacts exist or are backed up.

## Proposed MAINT-WT01B workflow

MAINT-WT01B should prepare per-path decisions and recovery evidence before proposing
any destructive operation. It should:

1. Resolve concurrent source ownership and finalize the read-only report interface;
   review the implementation and integrate code/tests/durable records through the
   normal process under a new authorization. MAINT-WT01A does not commit or create a PR.
2. Obtain complete, fresh hosting metadata with branch/SHA identity and PR head/base
   relationships. Repeat inventory with stable registry/refs and adequate scan budgets.
3. Assign owners and expected lifecycles, identify current users/processes, and
   obtain individual decisions for protected historical MAINT-01/02/03 artifacts.
4. Investigate missing registrations and existing residual directories as recovery
   cases, including mount/path history; do not treat `prunable` as discard approval.
5. Review unique commits, document variants, untracked files and ignored artifacts
   with their owners, using private manifests and explicit external-artifact mappings.
6. Propose exact backup roots, integrity checks, retention and independent restore
   procedures. Obtain scope approval before moving/copying real data or creating archives.
7. Only in a separately authorized future operation, recheck exact paths, branch/HEAD
   identities, live integration, clean/secured data and non-use immediately before
   ordinary non-force Git operations. Verify retained defaults/documents afterward.

The target of five persistent/active worktrees is a future capacity decision, not
an automatic selection rule. No actual removal command is implemented or executed
by this independent review.

## Independent inventory observations using partial hosting metadata

This section preserves the earlier partial-metadata run. Subsequent complete
hosting observations are reconciled below and in the
[task report](../audit/maint-wt01a/README.md). The partial run's classification
counts are historical evidence and must not replace the complete audit summary.

Snapshot time: **2026-11-11 09:51:11 UTC** (10:51:11 Europe/Berlin). The assigned
branch is `maint/wt01a-inventory-governance`, with unchanged HEAD
`c651e1d83c613de9bfb693380ac9856d72865121`. Comparison baseline is the cached
`origin/master` at that same SHA; no fetch was performed. The GitHub connector
confirmed the actual repository default branch name as `master`.

| Observation | Count |
| --- | ---: |
| Registered worktrees | 110 |
| ACTIVE | 55 |
| ARCHIVE | 0 |
| REMOVABLE_CANDIDATE | 0 |
| REVIEW | 55 |
| Lifecycle holds / safe to remove | 110 / 0 |
| Prunable registrations / unavailable Git status | 8 / 8 |
| With tracked changes | 29 |
| With untracked files | 26 |
| With ignored-file indicators | 47 |
| Incomplete disk metadata, including unusable paths | 13 |

The status categories overlap. This is a point-in-time inventory of registrations,
not 110 verified usable checkout directories. The lower-bound apparent size is
6,918,968,006 bytes (about 6.44 GiB), excluding shared `.git` storage and skipped
content. It is neither an archive size nor an estimate of recoverable capacity.

There are 31 registered heads with commits outside the cached baseline and 79
heads reachable from that baseline. Reachability does not prove preservation of
untracked/ignored data or historical documentation variants. Eight detached HEADs
need identity/retention review. Ten worktrees match known open PRs; their owners and
draft-review context must be preserved.

The eight prunable registrations are listed below for **recovery review only**.
Each name is relative to `/home/robfra/0_Portfolio_Projekte/`; the full exact path,
branch, SHA and observation errors are retained in the private JSON and CSV.

| Registered path name | Registered HEAD prefix | Relevant ambiguity |
| --- | --- | --- |
| Personal_Assistant-c21q | `3a42b1675dff` | Missing/inaccessible path; known open draft PR #72 |
| Personal_Assistant-c22 | `f2842788efd4` | Missing/inaccessible path |
| Personal_Assistant-c230 | `7f9fddf6d75f` | Missing/inaccessible path |
| Personal_Assistant-c2302a | `df41af0b5f36` | Missing/inaccessible path |
| Personal_Assistant-c2302b | `ba2dcd4a0a74` | Missing/inaccessible path |
| Personal_Assistant-c24r | `714e716876b2` | Path cannot establish a usable Git checkout; commits outside baseline |
| Personal_Assistant-completion-audit | `571874524b8b` | Missing/inaccessible path |
| Personal_Assistant-dep01 | `a8af1d9372eb` | Path cannot establish a usable Git checkout |

**Proposed removal candidates in this partial-metadata run: none.** Prunable records are not
removal candidates, and the 55 REVIEW records are not a deletion shortlist.
ARCHIVE remains zero because incomplete hosting/baseline evidence takes precedence
over recommending an artifact-preservation action.

Hosting evidence covers 44 selected PRs: the 11 returned by an open-PR search,
30 recent merged PRs and historical #92/#93/#119. Search completeness was not proven,
so the snapshot deliberately sets `complete=false` and contains no live branch map.
The local `gh api` metadata request failed; its raw diagnostic was withheld.
Cached tracking refs must not be presented as live branch availability.

Private evidence is retained under `artifacts/handoff/maint-wt01a/`:

- `before.json`: pre-inventory refs/registry/index hashes and parent-policy hash.
- `github-prs.json` and `github-hosting-review.json`: sanitized, partial PR metadata.
- `worktree_manager.review_snapshot.py`: frozen reviewed source for reproducibility,
  SHA256 `32f518677ad92f21c91eda9e0044906d810e3e052139bd6bec0c64132e89335e`.
- `inventory-final-review.json` and `inventory-final-review.csv`: authoritative
  machine-readable observations from that frozen source.
- `inventory-review.json` and `.csv`: earlier retained observation, before concurrent
  persistent-default classification protection changed ACTIVE/REVIEW from 54/56.
- `read-only-review-verification.json`: unchanged refs, registry, parent policy and
  all 110 index hashes at the independent verification checkpoint.

Reports and metadata are private local evidence, excluded by the task-specific
ignore rule. They contain path/status metadata, not file contents or credentials.
No archive is created, copied, synchronized or claimed restored by these reports.

## Validation and remaining ownership question

The subsequent independent GET acquisition exhausted the supported collection
pages: 59 branches, 100 PRs on page 1 and 45 on the terminal page 2. Its branch map
and all 145 sanitized PR records match the concurrently provided complete snapshot
exactly. This removes the earlier independent run's hosting-coverage uncertainty.
The complete independent snapshot is `hosting-complete-review.json`, SHA256
`7ec4229a6d3e68482bd39ed03d3ba663c14bf4878235cac1a9b3b1c6cfcbb815`.

The independent complete audit at **2026-11-11 09:56:17 UTC** confirms:

| Classification | Count |
| --- | ---: |
| ACTIVE | 55 |
| ARCHIVE | 7 |
| REMOVABLE_CANDIDATE | 41 |
| REVIEW | 7 |
| Total / lifecycle holds / safe to remove | 110 / 110 / 0 |

The [main task report](../audit/maint-wt01a/README.md) lists all 41 exact candidate
identities and the recommended MAINT-WT01B scope. They are technical review
candidates with unresolved human gates. They are not authorized for removal.
The seven ARCHIVE recommendations retain ignored artifacts for preservation review.
The independent audit's more restrictive two-second disk budget produced 13
incomplete estimates and a lower bound of 6,584,516,201 apparent bytes. Different
budgets and changing local report files explain why byte estimates differ between
runs; the classification counts agree with the complete task audit.

Complete independent evidence is retained as `audit-complete-review.json` and
`audit-complete-review.csv`; audit returned exit 2 for the 110 holds. Source was
frozen as `worktree_manager.complete_review_snapshot.py`, SHA256
`d65c4f13e35425270a7cef8c1c6f6a2577376db07680bb45d21f7d656aed6cd7`.
CSV consumers with large JSON cells may need to raise their parser's default field
size limit; both independent CSV reports were checked for 110 records and zero
`safe_to_remove` claims.

The initial 27 tests in `tests/test_worktree_manager.py` and ten additional independent
tests in `tests/test_worktree_manager_independent.py` passed against the reviewed
implementation. A later combined run passed **41 tests** after concurrent additions
expanded the primary suite to 31 tests. Tests use temporary synthetic repositories
and worktrees only.
They cover input preservation, missing registrations, status/ancestry failures,
dirty/untracked/ignored data, odd filenames, static symlinks, bounded disk scans,
metadata privacy, hosting completeness/freshness, export isolation and CSV handling.
No full application regression or graph extraction is claimed.

The independent reviewer observed concurrent edits to `scripts/worktree_manager.py`,
`.gitignore` and `tests/test_worktree_manager.py` during this run. An asynchronous
ownership question was raised. Those edits were preserved, not replaced. The
independent tests and this document use distinct paths. Final source ownership,
strict-read-only interface acceptance and task completion remain pending. Retain
the assigned worktree and branch; there is no merged PR or integration authorization.

The independent handoff snapshot is
`artifacts/handoff/maint-wt01a/review-handoff.patch`, with file and patch hashes in
`review-handoff-manifest.json` beside it. It captures all observed source, test,
ignore-rule and durable documentation changes without staging or committing them.
The task-owned independent evidence stays in this permanently provided worktree.
No new real working branch or registered worktree was created by this reviewer;
temporary synthetic test repositories were confined to their disposable fixtures.
