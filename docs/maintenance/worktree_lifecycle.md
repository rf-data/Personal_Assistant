# Read-only worktree lifecycle inventory

MAINT-WT01A introduces `scripts/worktree_manager.py`, using only the Python standard
library and installed Git. Supported operations are **inventory** and **audit**.
Neither operation creates or removes worktrees, updates refs or indexes, fetches,
prunes, archives data, or executes repository hooks, fsmonitor or clean/process
filters. Reports are emitted exclusively to stdout; the tool has no filesystem
output option. Report capture is a separate, explicit caller operation.

## Governance assessment

The parent `/home/robfra/0_Portfolio_Projekte/AGENTS.md` already defines a sufficient
normative lifecycle: reuse before creation, task identity and base recording, one
persistent `master` checkout and at most four active feature/review worktrees unless
approved, preservation of unknown data, exact-path operator approval, reproducibility
checks, and `WORKTREE_LIFECYCLE_HOLD` when evidence is missing. It was inspected and
left unchanged. This implementation supplies repeatable observations and a proposed
review vocabulary; it does not expand that policy's deletion authorization.

Repository `AGENTS.md` additionally requires durable records on actual default
`master` before lifecycle completion and verified integration before any cleanup
of a future task's own temporary artifacts. Existing MAINT-01/02/03 objects still
need individual approval. For WT01A, the explicit prohibition on commits, pushes,
PR creation and merges takes precedence: deliverables stay uncommitted in the
assigned worktree, a handoff patch is retained, and integration remains pending.

The existing [repository audit](../../scripts/repository_audit.py) inventories Git
and document relationships but assumes accessible worktrees, reads selected
document blobs, and does not provide this lifecycle model. Historical
[CS50 cleanup records](../cs50/operations/local_cleanup_inventory.md) and
[MAINT-01 through MAINT-05 evidence](../audit/maint05/README.md) describe earlier
reviews and recovery work. They are historical evidence, not a reusable deletion
approval or an archive executor. No existing general worktree manager was found.
WT01A does not change those scripts, records or archives.

## Commands

From the root of the assigned worktree:

```sh
python3 scripts/worktree_manager.py inventory
python3 scripts/worktree_manager.py audit
```

Both print JSON to stdout without writing a report file. `inventory` exits 0 after
collecting observations, even when some are unavailable. `audit` uses the same
observations and exits **2** when any worktree has a lifecycle hold. A fatal
inventory/input failure exits **1**, with a sanitized error. No removal
approval can be inferred from exit 0. Version 1 leaves human gates unresolved for
every worktree; a nonempty audit therefore normally exits 2.

Select either machine format on stdout:

```sh
python3 scripts/worktree_manager.py inventory \
  --format csv

python3 scripts/worktree_manager.py audit \
  --hosting-repository rf-data/Personal_Assistant \
  --hosting-snapshot artifacts/maint-wt01a/hosting-snapshot.json
```

`--repository` must name a worktree root, not a subdirectory. Inventory and audit
do not create destinations, change permissions or overwrite reports. To capture
evidence, the caller should choose a new, private, ignored artifact directory
**inside the assigned worktree**, check that no parent is a symlink or another
worktree, and use exclusive creation (Python `open(..., "x")` or shell `noclobber`)
with private permissions. Never redirect into another worktree or an external
archive. Preserve partial capture if collection fails.
Generated local WT01A reports and the handoff patch are ignored by Git.

For JSON and CSV representing exactly the same observations, capture one JSON
scan, then serialize its records without another scan. For example, after creating
the JSON using exclusive caller capture:

```sh
python3 - <<'PY'
import json
from pathlib import Path
from scripts.worktree_manager import csv_text
source = Path("artifacts/maint-wt01a/operator-inventory-001/inventory.json")
with source.with_suffix(".csv").open("x", encoding="utf-8", newline="") as stream:
    stream.write(csv_text(json.loads(source.read_text())))
PY
```

Set caller umask 077 before creating reports (directories 0700, files 0600).
This explicit serialization step writes only the selected report; it is not an
inventory/audit operation. Independent JSON/CSV scans can differ as files change.

## Observations and machine formats

JSON schema version 1 records timestamp, Git version, repository/common Git
directory, registry and ref digests, the exact `origin/master` baseline, hosting
metadata provenance, external availability, summary counts, limitations and one
record for each registered worktree. Records include:

- Exact path, branch ref/name or detached flag, registered HEAD, primary/current
  identity, locked and prunable indicators.
- Tracked changes, untracked file paths and ignored-file indicators from NUL
  delimited porcelain. Renames retain source and destination. Sensitive filenames
  are redacted while their counts remain; no diff, credential, document, runtime
  data or ignored-file contents are exported.
- Bounded apparent disk bytes from file metadata, scan completeness, error,
  symlink and mount indicators. `.git` is excluded, directory symlinks are not
  followed, and traversal stays on the starting device. Hardlinks count once per
  worktree. These figures are lower bounds when incomplete, and never reclaimable
  space estimates. Separate worktrees may share storage.
- Local branch availability/head, matching cached remote refs, and separate live
  remote branch availability/head when a hosting snapshot is supplied.
- Ahead/behind counts and ancestry relative to the captured **origin/master**
  object. No fallback to a local branch, commit message or patch similarity.
- PR number, state, merged/draft flags, head/base repository, branch and SHA, and
  match type (`branch`, `branch_and_sha`, `sha_only`). Same branch names in forks
  do not establish local branch identity. A reused local branch with an open PR
  remains protected even if its PR head differs. PR merge state alone is never
  a retention proof.
- Classification, reasons, observation errors, unresolved human gates,
  `reproducible=not_verified`, `safe_to_remove=false` and a lifecycle hold.

CSV contains one row per worktree and the union of its record fields. Nested
values, booleans and nulls use JSON cells. Scalar strings starting with spreadsheet
formula/control prefixes have an apostrophe prepended; JSON retains the exact
value. Non-UTF8 filename bytes use surrogate escapes in JSON and printable escape
sequences in CSV. Keep JSON as the authoritative lossless source. Summary/provenance and
external metadata live in JSON; CSV includes per-worktree evidence only.

Git status suppresses submodule recursion; gitlinks and nested Git markers trigger
review instead. Unavailable paths, status warnings, timeouts, missing objects,
shallow/partial history, identity mismatches and incomplete disk scans are never
treated as clean evidence. Git replace objects are disabled. Git itself reads
tracked files to calculate status, but this tool does not collect their contents.
Filters are disabled to prevent executing repository-defined commands; filtered
files may consequently appear modified, requiring review.

The registry and refs are checked again at the end. Changes revoke candidacy.
This is a point-in-time scan, not an atomic snapshot: file races, other hosts,
open files and active processes cannot be excluded. Absence of a dirty status is
not proof of inactivity. Bounded scans default to 200,000 entries/15 seconds per
worktree; `--max-disk-entries` and `--disk-seconds` can increase those limits.

## Hosting metadata without fetching

The tool is offline. Cached `refs/remotes/` may be stale and never prove live
availability. Optionally supply a sanitized JSON snapshot obtained through an
authorized read-only GitHub connector or equivalent GET requests. Paginate **all**
branches and PRs (all states) to exhaustion; never assert completeness for a
truncated/failed query. Retain the acquisition method, page counts and timestamp
in the accompanying report. No PR bodies, comments, titles, tokens or user profiles
are needed.

The snapshot contract is:

```json
{
  "schema_version": 1,
  "repository": "example/synthetic",
  "observed_at": "2026-11-11T09:00:00+00:00",
  "complete": true,
  "branches": {"master": "1111111111111111111111111111111111111111"},
  "pull_requests": [{
    "number": 1, "state": "closed", "merged": true, "draft": false,
    "head_sha": "1111111111111111111111111111111111111111",
    "head_ref": "feature", "head_repository": "example/synthetic",
    "base_ref": "master", "base_repository": "example/synthetic"
  }]
}
```

The supplied repository must match the snapshot and the configured GitHub origin.
Snapshots older than 24 hours or dated in the future cannot establish candidacy.
The live master SHA must equal cached origin/master. Snapshot SHA256 and acquisition
time are recorded. A branch absent from a complete snapshot is distinguished from
unknown availability; a deleted branch's HEAD can still be retained by live master.
Completeness is an assertion by the snapshot producer, not independently verified
by this offline tool. Historical snapshots support historical observations only.

## Conservative classification

Classification order is deliberate. Known activity protects a worktree even when
other observations are unavailable. All labels retain `safe_to_remove=false`.

| Label | Meaning and automatic evidence | Next review |
| --- | --- | --- |
| ACTIVE | Primary/current checkout, a `master` checkout, locked worktree, tracked/untracked work, open PR including draft, or commits outside origin/master | Keep; confirm task ownership and expected lifecycle |
| REVIEW | No known activity above, but a prunable registration, missing/ambiguous observation, unverified hosting/baseline, unretained HEAD, symlinks, submodules or nested repository | Resolve uncertainty before considering archival or removal |
| ARCHIVE | Automatic history/status/hosting checks pass, with ignored-file indicators | Assess retention, backups and reproducibility; no copying or archival is executed |
| REMOVABLE_CANDIDATE | Automatic checks pass, no ignored/untracked/modified data observed, HEAD retained by verified baseline, no open PR found | Proposal for exact-path human review only |

The labels are observations, not a reliable census of currently running tasks.
ACTIVE can include historical unfinished work; REVIEW can include an active task
whose evidence is missing. A prunable registration can therefore be ACTIVE when it
has an open PR or unique commits. None of the 110 WT01A entries receives an
automatic disposal authorization. MAINT-01/02/03 individual approval requirements
continue to apply regardless of classification.

## Reproducibility and a future archive/remove workflow

A reproducible task needs retained exact commits, durable integrated documents,
necessary local and external artifacts with integrity checks, documented dependency
versions/environment and a successful independent restoration. Clean Git status,
a merged PR, a cached remote ref or a bundle check alone cannot establish this.

Proposed future stages, each separately authorized as appropriate:

1. Reinventory exact paths/heads. Bind task ID, owner, branch, base commit, purpose
   and expected lifecycle to each candidate. Exclude primary/default/current
   checkouts and protected tasks; obtain evidence of process/other-host nonuse.
2. Review unique history, draft/open PRs, historical document variants and actual
   integration on live master. Preserve durable records through normal review.
3. Identify local uncommitted/untracked/ignored data and map necessary external
   artifacts. Neither external root's availability proves a backup. Preserve
   stashes, databases, models, environments, secrets and unrelated archives.
4. Prepare a per-path archive manifest with integrity hashes, provenance,
   destination approval, retention/access rules and dependency/environment recipe.
   Unknown data blocks progress. Never synchronize or move archives speculatively.
5. Under separate authorization, secure required data and verify an independent
   restore without the original worktree/object store. Document exact results.
6. Present a concrete per-path decision and obtain required approval. Recheck
   exact identity/head, Git status, ignored data and use immediately before any
   future ordinary operation. Branch decisions are separate from worktree decisions.
7. Verify retained default-branch documents, restore evidence and actual remaining
   registrations/refs. Record removed/retained/pending identities. Any uncertainty
   means `WORKTREE_LIFECYCLE_HOLD`; force removal and blanket cleanup are excluded.

This is a proposal only. Version 1 deliberately has no archive, remove, create,
prune, repair, branch-deletion or synchronization command.

## Validation

```sh
python3 -m unittest tests.test_worktree_manager -v
git --no-optional-locks diff --check
```

Tests create exclusively synthetic repositories/worktrees under temporary
directories. Fixture commits/configuration changes are confined to those fixtures.
They verify classification, missing/dirty/ignored/detached/locked cases, PR and
baseline ambiguity, NUL/rename parsing, metadata preservation, filter suppression,
bounded/symlink disk scans, stdout formats and fail-closed errors. No new dependency
installation or application test environment is required. See the
[WT01A report](../audit/maint-wt01a/README.md) for the actual inventory and handoff.
