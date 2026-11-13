# Fast registry and ref inventory (MAINT-WT03-A)

This standalone observation tier reads Git's worktree registry and local/cached
remote refs. It is suitable for a quick registry census before a separately
authorized, exact-path review. It never establishes cleanliness, integration,
reproducibility, inactivity, preservation or removal eligibility. It does not
replace the [existing lifecycle inventory](worktree_lifecycle.md) or
[preservation/restore protocol](worktree_preservation_restore.md).

Every returned registration, including bare, detached, locked, prunable and
duplicate-HEAD registrations, contains these unconditional fields:

```json
{"safe_to_remove": false, "lifecycle_hold": "WORKTREE_LIFECYCLE_HOLD"}
```

The report also sets `removal_approval_sufficient=false`. No classification or
removal candidate is produced. Exit 0 never grants removal approval.

## Collection algorithm

The successful path makes exactly five sequential Git subprocess calls, all
using the single explicit repository argument:

1. `rev-parse --show-toplevel`: require the exact lexical absolute root (one
   terminating newline removed by exact comparison). Subdirectories and aliases
   that Git canonicalizes differently fail closed.
2. `worktree list --porcelain -z`: capture and strictly parse the initial registry.
3. `for-each-ref --sort=refname
   --format=%(refname)%00%(objectname)%00%(symref)%00 refs/heads/ refs/remotes/`:
   capture local and cached remote refs. The command emits NUL fields and a final
   LF for each row. Git ref names cannot contain LF; names are decoded losslessly.
4. Repeat the registry command and parse the complete result.
5. Repeat the ref command and parse the complete result.

Check each registry/refs pair for absent registered branches, branch/HEAD
mismatches and unborn zero HEADs. Validate symbolic-ref targets that Git actually
emits. Compare the exact before/after registry bytes and exact before/after ref
bytes; retain SHA-256 and byte length for each successful capture. No retries or
automatic repair occur. Missing `origin/master` alone is not an error: no baseline
or integration claim is made. A detached registration needs no local branch.

The number of subprocesses does not grow with worktree count. Parsing, comparison
and memory grow with registry/ref output size. Duplicate HEADs are aggregated in
`duplicate_heads`; individual worktrees remain separate. The tool neither opens
registered paths in Python nor runs per-worktree Git commands. Git itself may
read pointer metadata/existence to report prunable registrations and internally
enumerates the administrative registry and refs. This is not a checkout/content
traversal. The tool does not call `status`, `ls-files`, `rev-list`, `disk_usage`,
`walk`, `scandir`, recursive globbing, archive inspection or any network command.

## Bounds and failure behavior

Default limits are 5 seconds per command, 20 seconds for inventory collection
including parsing/finalization, and 8 MiB combined stdout/stderr per command.
Limits must be positive and finite. Commands run serially. A selector reads both
pipes without deadlock; at most one extra byte is read to detect output overflow.
No spool files are created. Each call receives the smaller of its command budget
and the remaining collection budget. Parsing checks the deadline per registry/ref
record. Hashing, splitting and other individual Python operations are bounded by
the output cap, but are not preemptible halfway through an operation.

On timeout/output overflow the direct child is killed and reaped, allowing at
most 0.2 seconds for cleanup. OS scheduling, process creation and uninterruptible
kernel I/O cannot provide a strict realtime upper bound. The collection deadline
does not bound JSON rendering or a caller's blocked stdout/report capture.
Operators needing a deadline for the entire CLI must also bound the caller.

Any nonzero Git exit, any stderr (even with exit 0), malformed/truncated output,
duplicate path/ref, unsupported registry field, invalid ref/OID, observation
change, failed consistency check or exhausted budget prevents `complete=true`.
Diagnostics contain fixed codes, never raw Git stderr or arbitrary exception
messages. Each operation records seconds, error code and, for successful command
reads, stdout bytes. Global errors identify the failed operation. Row errors
identify branch/HEAD issues; other failures invalidate `observation_complete` for
all retained rows through the global `complete=false` result.

JSON is printed even for a partial observation, with exit **1**. Invalid CLI input
exits **2**. Exit **0** means only the narrow metadata observation completed.
`summary.registered` counts the retained initial rows, not a complete census when
`complete=false`; an empty partial report never proves zero registrations. A
malformed initial registry is not partially trusted. Later failure retains the
parsed initial registry; registrations introduced after it may be absent from
the partial report. Consumers must reject an incomplete result as a census.

`subprocess_count` counts attempted command launches, including an OS launch
failure. Benchmark instrumentation separately counts actual `Popen` calls; all
successful actual observations make five calls. Mocked simulations make zero
actual calls and five logical attempts. Individual command output is capped, but
the full Python report can occupy several times that cap due to decoded strings,
before/after arrays, dictionaries and JSON expansion. Child Git RSS is not capped.

## Encoding and privacy

Registry parsing uses NUL record/field separators, never line splitting. Each
path has an `os.fsdecode` representation and `path_bytes_base64`. Base64 is the
authoritative cross-platform representation of original filesystem bytes.
`ensure_ascii=True` preserves surrogate escapes in portable UTF-8 JSON and
escapes control characters. Tabs, newlines, quotes, backslashes, trailing spaces
and non-UTF8 Linux bytes survive round trips. Ref names use filesystem decoding
too; OIDs must be 40- or 64-character lowercase hex. Branch refs are full names.

Lock/prunable presence is retained, but arbitrary reasons are omitted to avoid
exporting private free text. Worktree paths and branch names may themselves be
sensitive. Reports are stdout-only; the tool has no output path, archive, cleanup
or removal option. A separately authorized caller should capture reports privately
and exclusively inside an approved workspace, without overwriting evidence.

## Security boundaries and remaining uncertainty

Only three exact command tuples are allowlisted. Git receives no user-supplied
subcommand/ref expression and runs without a shell. Inherited `GIT_*` overrides
are discarded. System/global Git configuration is disabled. Optional locks,
hooks, fsmonitor, automatic maintenance/GC, lazy fetch, replace objects, prompts
and transport protocols are disabled. No object expansion or content/filter
operation is requested. Repository configuration remains necessary for Git to
interpret its metadata; configuration includes and object-store layouts are not
independently sandboxed or authenticated by this Python tool.

This is an endpoint comparison, not an atomic snapshot. Change-and-revert races,
repository/parent replacement, symlink/bind-mount aliasing, administrative metadata
tampering and activity on another host are not excluded. Registry HEADs/paths
are Git-reported values: forward/reverse pointer identity, indexes, actual commit
object existence/type, reachability and checkout contents are not verified.
Git may omit dangling symbolic refs from `for-each-ref` without a warning; this
tool covers Git's emitted namespace, not a filesystem-level ref integrity audit.
An emitted malformed record or warning fails closed, and a missing registered
branch is always an error. Cached remote refs remain potentially stale.

Consequently, even a complete report is never sufficient for removal approval.
All previous exact-path approval, ownership/nonuse, historical-document,
artifact/dependency, backup and independent-restoration gates remain unresolved.

## Validation and later integration

All execution evidence in this task uses tiny, self-created repositories under
the private workspace. The 100/200-record cases simulate metadata and create no
checkout trees. See [test results](../../test_results.log),
[benchmark measurements](../../benchmark_results.json),
[assessment](../../assessment.md) and [handoff](../../handoff.md).

For later review, add the script/tests/docs through the normal controlled change.
Keep the existing manager and its tests intact. Rerun the four named test modules
with `TMPDIR` inside a newly created private workspace directory. The new test
module's `--benchmark` mode prints reproducible measurements to stdout. Python
3.11 and installed Git with porcelain `-z` support suffice; no dependencies.

After separate authorization for a specific repository, the command shape is:

```sh
python3 scripts/worktree_fast_inventory.py \
  --repository /exact/authorized/worktree/root \
  --subprocess-seconds 5 --deadline-seconds 20
```

Do not use the above shape against production as part of this development task.
A future consumer must check exit status, `complete`, consistency fields and
holds. It may use the result to scope another controlled review; it must never
wire exit 0 or matching HEADs to archive/remove/prune/branch-deletion behavior.
