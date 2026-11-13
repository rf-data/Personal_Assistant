# Single worktree deep preflight — MAINT-WT03-B2

**Strict acceptance: BLOCKED. Synthetic development only.** The bounded observation
implementation and tests are available, but the full no-symlink/no-mount guarantee
cannot be established for Git's own administrative file opens. The executable
therefore always returns `complete=false` and `safety_assurance=BLOCKED`. Default
`strict` mode retains exit 1. The explicit `trusted_local_diagnostic` mode adds an
independent diagnostic completion status and exit semantics described below.
A successful narrow observation additionally reports `observation_complete=true`.
Neither mode waives the isolation blocker. No real registered checkout was
inspected during development, testing or measurements.

This extends the design in [fast inventory](fast_inventory_design.md),
[lifecycle governance](worktree_lifecycle.md) and
[preservation/restore](worktree_preservation_restore.md). B2 extends the B1 observer;
the manager, fast inventory, all 164 existing tests and other maintenance designs
remain unchanged. The module reuses `parse_registry()`,
`parse_refs()`, ref validation, the sanitized Git environment and the manager's
`parse_status()`. It never calls either existing `inventory()`.

## Explicit diagnostic operational contract

Select `--mode trusted_local_diagnostic` (API: `mode="trusted_local_diagnostic"`).
Omitting the mode, or selecting `--mode strict`, preserves strict safety BLOCKED
and exit 1 even when observations complete. Both paths use the same observer,
Git allowlist, identity and consistency checks, worker isolation and resource
limits. Diagnostic mode requires explicit `--repository` and `--worktree`; it has
no automatic discovery, real-worktree scan or lifecycle executor.

Trusted-local mode assumes a **non-adversarial local environment**, including the
local interpreter, worker, Git executable and repository metadata. It is **not an
atomic snapshot of a concurrently changing repository**. Endpoint checks detect
some changes, but cannot rule out change-and-revert races, metadata substitution
or root bind-mount aliases. The unconditional `git_metadata_isolation_not_verified`
uncertainty appears even in argument errors and compact failure reports. Completed
observations also retain this blocker in `errors` and the safety dimension. No
completed diagnostic is a completed strict-isolation safety guarantee.

`diagnostic_status` is independent of the existing safety fields:

| Mode / outcome | Diagnostic status | Observation complete | Safety / legacy complete | CLI exit |
| --- | --- | --- | --- | ---: |
| Strict, any result | BLOCKED | true only if observations finished | BLOCKED / false | 1 |
| Diagnostic, all required observations finished | COMPLETED_WITH_LIMITATIONS | true | BLOCKED / false | 0 |
| Diagnostic, observation stopped or report exceeded its limit | INCOMPLETE | false | BLOCKED / false | 1 |
| Diagnostic, invalid request or untrustworthy worker report | BLOCKED | false | BLOCKED / false | 1 |

`--help` exits 0 without observations. CLI argument parsing failures produce a
strict-format BLOCKED report and exit 1, including malformed mode selections.
Exit 0 confirms observation completion only; it never grants removal permission.

The additive schema-version-1 fields are `mode`, `diagnostic_status`,
`environment_assumption`, `atomic_snapshot=false` and `required_observations`.
Required observations are identity, integration, git_status, storage and
consistency. Each begins `NOT_CHECKED` (successful completion not established)
and becomes `COMPLETED` only after its entire observation succeeds. Identity and
consistency finish only after final metadata/pointer and registry/ref/HEAD checks.
Partial results keep their errors, uncertainties and unfinished observations;
the observer stops at the first failure, so later unsupported conditions are
unverified, not asserted absent. WARN can be a completed observation, for example
a dirty checkout, locked registration, divergent branch, symlink or hardlink.
Safety and preservation are not included in diagnostic completion requirements:
safety remains BLOCKED, preservation WARN/NOT_CHECKED with backup and independent
restore NOT_VERIFIED, and actual reclaimable storage NOT_VERIFIED.

The parent parses and validates worker JSON before adopting it. It rejects
duplicate keys, nonfinite numbers, malformed structures, wrong mode/path/baseline
binding, altered safety/lifecycle/preservation fields and inconsistent completion
claims. Completion requires all observation markers, observation payloads,
successful dimensions, matching endpoint snapshots, consistency checks and all
14 expected successful Git operations. A missing observation is never success.
Compact worker failures explicitly retain incomplete observations and unknown
Git counts. An invalid worker report is replaced by a fresh BLOCKED HOLD report;
its claimed safety or completion is never carried forward. This validation checks
the local protocol; it does not authenticate a compromised worker or Git binary.

## Selection and identity

Both `--repository` (explicit registry repository) and `--worktree` (the single
selected content root) are required. An independent registry anchor prevents a
replacement repository at an old linked-checkout path from adopting its own
registry. The anchor receives metadata reads only. No other registered checkout
receives a content traversal.

Paths must already be absolute and canonical byte paths: no trailing or repeated
separators, dot/dot-dot components, relative paths or filesystem root. Opening
ancestors uses Linux `openat2` with `RESOLVE_BENEATH|RESOLVE_NO_SYMLINKS` and
`O_NOFOLLOW`; symlink aliases are rejected, not resolved into a selection.
Ancestor mounts are allowed when establishing roots; root bind-mount aliasing
remains unverified and contributes to the unconditional safety blocker.

The selected `.git` is a direct directory or bounded regular Git pointer file.
Pointer/common-directory paths cannot contain symlink components. Linked
registrations must have the expected `common/worktrees/<id>` layout and an exact
reverse `gitdir` pointer. Selected and anchor common directories must have the
same canonical bytes and device/inode. Git sees pinned descriptors through
`/proc/self/fd`; these intentional descriptor references are not caller aliases.
Its reported top level must equal the selected path bytes exactly.

Parse the current NUL-delimited registry strictly and require exactly one exact
byte-path match. Reject missing/ambiguous, bare or prunable selection, unborn HEAD,
branch/ref mismatch, HEAD value/kind mismatch and noncanonical registry paths.
A locked selected registration is observed as WARN and retains HOLD. Other locked
or prunable registrations do not cause content visits. Registry administration
(shared `worktrees/<id>` records) is metadata, not checkout content.

## Observations and command policy

A completed narrow observation attempts exactly **14 Git subprocesses plus one
worker**. Partial observations stop early; an interrupted worker's Git count is
unknown (`null`), not a fabricated zero. Operation timings and successful stdout
byte counts are included. Registry/ref snapshots include byte lengths and SHA-256.

| Order | Fixed command tuple or constrained template | Purpose |
| --- | --- | --- |
| 1 | `config --null --list --no-includes` | Reject unsupported configuration before subsequent Git reads |
| 2 | `rev-parse --show-toplevel` | Pinned root identity |
| 3–5 | `worktree list --porcelain -z`; `for-each-ref` as in fast inventory; `rev-parse --verify HEAD` | Registry/local refs/selected HEAD before |
| 6 | `rev-list --left-right --count <HEAD-OID>...<baseline-OID> --` | Local-only ahead/behind and ancestry |
| 7 | `rev-parse --show-object-format` | SHA-1 or SHA-256 blob hashing |
| 8–10 | `ls-files --stage -z`; `ls-files -v -z`; `ls-tree -r -z --full-tree HEAD` | Index, masking flags, HEAD tree |
| 11 | `config --null --list --no-includes` | Executable-bit comparison policy |
| 12–14 | Repeat registry, refs and HEAD | Endpoint consistency |

The ancestry template accepts only two validated full object IDs, obtained from
local metadata. User ref expressions cannot reach Git; the baseline must be a
full `refs/heads/` or `refs/remotes/` name present in the captured map. Ahead zero
means HEAD is an ancestor of the local baseline. Cached remote refs carry no
freshness or hosting assurance. Tags and arbitrary expressions are unsupported.

Commands use no shell. Inherited `GIT_*` variables are removed; system/global
configuration, prompts, transport, replace objects and lazy fetch are disabled.
Hooks, fsmonitor, preload/untracked caches, optional locks, maintenance and GC are
disabled explicitly. No `status`, diff, hash-object, checkout, network or mutation
command is allowlisted. Git receives file descriptors for metadata-only work.
The worker interpreter ignores Python environment/user site customization, skips
site initialization and disables bytecode writes.

Status compares index mode/blob IDs to descriptor-read working bytes. It hashes
Git's raw `blob <length>\0<payload>` representation in Python, without Git clean,
process, textconv or external diff programs. Comparing HEAD tree entries to the
index supplies staged A/D/M/T; comparing working entries to the index supplies
unstaged changes. Renames are represented as deletion/addition. Conflicted,
masked, sparse and gitlink indexes block completion. `parse_status()` builds the
usual tracked/untracked/ignored aggregates from generated NUL porcelain records.
Its privacy-redacted display strings are supplemented by authoritative lossless
`raw_records` containing the original path bytes in base64.

Ignore support is deliberately bounded: local `.gitignore` and common
`info/exclude`, comments, blank lines, literal components, `*`, `?`, anchoring and
directory patterns. All rules are exclusion-only, so order cannot re-include a
path. Negation, backslash escapes, bracket patterns, `**` and repeated slash
syntax block status rather than being guessed. Nested supported ignore files are
scoped to their directory. Ignored regular/symlink leaves and empty ignored
directories are reported; untracked empty directories are not Git status entries.
These counts are indicators, not Git's directory-collapsed output format.

Filter definitions, configuration includes, external ignore/attribute files,
unsupported extensions, conversion/case settings, sparse policies and explicit
symlink checkout policies are rejected. Nonempty `.gitattributes` blocks status;
symlinked ignore/attribute files block without reading their targets. Empty files
and ordinary raw-byte repositories are supported. No filter-dependent equivalence
or exact universal `git status` compatibility is claimed.

## Storage and preservation

Every content descent/open is descriptor-relative with `RESOLVE_BENEATH`,
`RESOLVE_NO_SYMLINKS` and **`RESOLVE_NO_XDEV`**, including same-device bind mounts.
Directory descriptors remain held. Each entry is lstat'ed; a subsequently opened
file/directory must match its observed signature. Directory signatures are
rechecked around enumeration; tracked regular files around bounded reads.
Symlink targets are recorded with `readlink`, never opened. No FIFO/device/socket
is opened for content. Unknown special files cause skipped content and BLOCKED.

Root `.git` administration is excluded from logical working storage; its checked
entries count separately against the same global entry budget. Other registered
roots beneath the selected root are skipped before descent. Nested `.git` markers
and conservative bare-repository marker sets (`HEAD`, `objects`, `refs`) cause a
recorded skip. Mount boundaries, nested repositories and other skipped content
prevent `observation_complete=true`. Symlinks and hardlinks produce WARN when the
remaining narrow observation succeeds.

`logical_regular_bytes` counts each regular pathname's `st_size`;
`unique_inode_logical_bytes` deduplicates device/inode pairs. Hardlink counts do
not establish where other names reside. Neither measure is physical allocation,
exclusive ownership, compression/deduplication accounting or reclaimable bytes.
`actual_reclaimable_storage` is always **NOT_VERIFIED**.

Repeat the registry, local refs and HEAD and compare their exact bytes. Reopen
both root identities without following links, audit metadata again, and recheck
forward/reverse/common pointers plus selected index, HEAD, config and exclude
bytes. Observed endpoint changes block the observation. This is not an atomic
snapshot or a preservation manifest.

`--evidence-reference` accepts at most 32 nonempty text references, at most 1,024
characters each and within the request budget. References are opaque assertions:
no referenced file is opened, no backup is inferred from a name and no independent
restore is verified. Even an integrated clean branch has preservation WARN,
`backup=NOT_VERIFIED`, `independent_restore=NOT_VERIFIED` and
`references_verified=false`. No backup, archive, restore or cleanup executor exists.

## Bounds, errors and lifecycle

| Bound | Default |
| --- | ---: |
| Per Git subprocess | 3 seconds |
| Worker process wall budget | 12 seconds |
| Overall parent observation deadline | 15 seconds |
| Each Git command's combined stdout/stderr | 1 MiB |
| Aggregate successful Git stdout | 4 MiB |
| Final report/worker combined output | 2 MiB; configurable minimum 4 KiB |
| Total counted filesystem entries | 20,000, including repeated metadata audits |
| Aggregate file/metadata bytes read in Python | 16 MiB |
| Directory depth | 64 per traversal |
| Parent-to-worker request | 16 KiB |

Positive finite limits are required. The parent starts a new worker session and
bounds both output pipes, request writing and wall time. The parent kills the
whole session on timeout/failure and allows only 0.2 seconds for cleanup. A Git
command receives the smaller of its per-command allowance and remaining worker
deadline. It is killed/reaped on timeout/output overflow. The parent deadline
also bounds a stuck filesystem syscall, parsing, hashing and worker serialization;
it does not depend solely on Python traversal checking a clock. Tests stall an
actual worker's `scandir` to demonstrate this distinction.

Kernel-uninterruptible I/O and OS scheduling prevent a hard realtime guarantee;
kill is requested within the userspace budget, but the kernel may defer exit.
No portable total RSS cap is claimed. The caller must separately bound a blocked
stdout consumer. Source reads can update atime; byte contents, refs, modes,
mtime/ctime, inode and hardlink metadata remain the verified read-only contract.

Invalid arguments, unsupported kernels/architectures, unsafe roots, inaccessible
metadata, malformed/truncated output, warnings on stderr, nonzero Git exits,
missing baseline/objects, skipped entries, changing metadata, timeouts and limits
all emit sanitized fixed diagnostic codes and no optimistic completeness claim.
On output overflow the detailed report is replaced by a compact HOLD report;
unknown observations/counts remain unknown. No truncated report is accepted.

Every report, including argument/worker failures, contains:

```json
{"safe_to_remove":false,"lifecycle_hold":"WORKTREE_LIFECYCLE_HOLD","removal_approval_sufficient":false,"lifecycle_decision":"WORKTREE_LIFECYCLE_HOLD"}
```

Observation dimensions use only PASS, WARN, BLOCKED, NOT_CHECKED. PASS means that
named narrow observation succeeded; it grants no lifecycle permission. The
separate safety dimension is always BLOCKED in this version. No removal candidate
is emitted. `observation_complete=true` and diagnostic exit 0 cannot be substituted
for `complete`, safety assurance, preservation verification or human approval.

## Unresolved security boundary and integration

**Strict acceptance remains BLOCKED.** Git opens shared config/ref/object/registry
metadata itself. Static metadata audits and before/after reads cannot force those
opens through the scanner's `openat2` policy, exclude concurrent substitutions,
or prove absent root bind-mount aliases. Git registry operations may stat pointer
metadata to classify registrations. Endpoint comparison cannot detect
change-and-revert races or all mid-read filesystem changes. No process/other-host
nonuse, owner-controlled quiescence, namespace isolation, ownership authentication,
full object integrity, ACL/xattr preservation or independent restoration is
established. The implementation is not a sandbox for hostile Git metadata.

A later stage must establish and test OS-enforced isolation of Git's metadata
access and an approved stable source identity/window before lifting this blocker.
Do not integrate this as a production preflight, removal gate, backup verifier or
reclaimable-storage estimator. It is reviewable synthetic development evidence.
No real repository is an acceptable fallback for further development testing.

Any integration belongs to a later task through the normal controlled process.
No commits, pushes, PRs or merges were performed. B2 changes only deep-preflight,
this design, the assessment/log/handoff and a new diagnostic test module.
Reproduce validation with installed Python/Git, a workspace-local TMPDIR and:

```sh
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/private/workspace/temporary-directory python3 -m unittest \
  tests.test_worktree_manager tests.test_worktree_manager_independent \
  tests.test_worktree_preservation tests.test_worktree_fast_inventory \
  tests.test_worktree_deep_preflight tests.test_worktree_deep_preflight_diagnostic -v
```

For an explicitly self-created synthetic fixture only, the command shape is:

```sh
python3 -B scripts/worktree_deep_preflight.py \
  --repository /private/synthetic/main --worktree /private/synthetic/selected \
  --baseline refs/heads/master --evidence-reference synthetic-review-record
```

It returns exit 1 with safety BLOCKED even if the narrow observation completes.
For the same explicitly self-created synthetic fixture, add
`--mode trusted_local_diagnostic` to receive exit 0 only on
`COMPLETED_WITH_LIMITATIONS`. Missing baselines, unsupported behavior, changed
endpoints, worker/Git timeouts and all resource-limit failures remain nonzero.

Linux x86-64/aarch64 with usable `openat2`, `/proc/self/fd`, Python 3.11+ and Git
with NUL worktree porcelain support are required. No dependencies are installed.
See [assessment](../../assessment.md), [test evidence](../../test_results.log),
[B1 historical measurements](../../benchmark_results.json) and [handoff](../../handoff.md).
B1 timings are not B2 measurements; no new benchmark or large fixture is needed.
