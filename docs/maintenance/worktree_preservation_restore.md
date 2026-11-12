# Historical worktree preservation and restore protocol

MAINT-WT01B, 2026-11-12. **Design and synthetic validation only.** All existing
worktrees retain `WORKTREE_LIFECYCLE_HOLD`. No production archive or restore
executor is provided. Follow [lifecycle governance](worktree_lifecycle.md) and the
[WT01B assessment](../audit/maint-wt01b/README.md). A machine classification never
authorizes copying, restoration, branch changes or removal.

## Scope, ownership and approval record

One approved source identity per operation: repository full name and numeric ID,
exact absolute worktree path, filesystem device/inode, forward `.git` pointer,
reverse registration `gitdir`, common Git directory, branch ref or detached state,
HEAD, index digest and registry/ref digests. Record UTC observation time, task,
operator, owner, purpose, expected lifecycle and policy versions/digests. A missing,
replaced, symlinked, ambiguous or inconsistent source stops the operation.

This task permits only read-only assessment of actual worktrees and synthetic
backup/restore tests. Future real preservation needs a separate operator decision
containing these concrete fields:

| Approval field | Required decision |
| --- | --- |
| Source | Exact path, branch and HEAD; one source, no basename/glob selection |
| Ownership and nonuse | Named owner, exclusive operator window, services/jobs/other hosts paused by their owners; lease expiry and recheck plan |
| Contents | Include/exclude decision for every tracked change, index state, untracked/ignored artifact and empty directory; unknown contents block |
| External dependencies | Exact privately recorded roots, data custodians, versions, hashes and application snapshot procedure; explicit attestation if none required |
| Destinations | New private archive and separate new restore paths; storage capacity, filesystem features, encryption/key custody, retention and access rules |
| Historical evidence | MAINT-01/02/03 individual records and document-version disposition; no implied release of earlier holds |
| Operations | Separately approve archive writes and restore exercise, tool/version and byte/file/time limits; do not bundle later deletion approval |
| Acceptance | Exact HEAD/tree and byte/mode checks, application smoke test, independent verifier and signed/digest-bound result |

The record must be bound to the reviewed manifest digest. Changed scope, identity,
data, expiry or use invalidates approval. Do not automatically edit original
worktrees, lock their registry entries, stop services or acquire application locks
in this task. An absent lock or zero visible process matches is not a nonuse lease.

## Bounded capture design

1. **Preflight, without writing sources.** Recollect complete live branch/PR
   metadata with provenance; check origin/repository IDs, timestamp, master SHA,
   open/draft head/base dependencies and HEAD reachability. If cached master is
   stale, stop and request a separately authorized reference refresh; do not fetch
   speculatively. Check shallow/promisor history, replace refs, alternates, LFS,
   submodules, nested repositories, sparse checkout, skip-worktree and
   assume-unchanged flags. Missing objects or filter-dependent bytes block closure.
2. **Establish a stable scope.** After owner confirmation of nonuse, collect
   NUL-delimited tracked/index/status and exhaustive untracked/ignored metadata.
   Review index stages and conflicts, permissions, ACLs/xattrs, case/encoding
   collisions, empty directories, hardlinks, symlinks, special files and mounts.
   Do not infer absence from `git status` alone. Record external references from
   reviewed tracked configuration/docs without dumping secrets or data contents.
   Each external root needs an owner decision, not merely an existence check.
3. **Set limits before reading bytes.** Initial proposal per candidate: 200,000
   entries, 512 MiB regular bytes, 64 MiB per file, 8 MiB manifest, 30 seconds for
   metadata and 120 seconds per copy/hash/Git subprocess, 1 GiB bundle. Explicitly
   approve larger history budgets if needed. Reject limit exhaustion; never
   silently truncate. Require free space for bundle, payload, independent restore
   and a separately agreed reserve. Actual ENOSPC/EDQUOT errors still fail closed.
   Do not start background retry loops.
4. **Create a new private destination exclusively.** No overwrite, resume,
   synchronization or adoption of an existing path. Check every path component
   with descriptor-relative `openat`/`O_NOFOLLOW`, stable device/inode and ownership;
   retain directory handles. Source, destination and restore roots must be disjoint,
   outside all real worktrees and approved archives, with no symlink, bind-mount
   alias or shared-inode ambiguity. Default directories 0700 and metadata 0600;
   preserve file modes inside the protected payload where required. Verify storage
   access policy and encryption separately. Avoid implicit filesystem traversal.
5. **Preserve Git closure independently.** In the future authorized operation,
   create a standalone bundle containing the exact HEAD and reviewed required
   history/refs, including explicit detached-HEAD handling. Include no implicit
   `--all` grab of unrelated branches or stashes. Never modify real refs merely to
   name a bundle tip. If naming the exact tip cannot be done without mutation,
   design/review a separate exporter first. Verify advertised refs and required
   commit/tree IDs in a new empty object store. No prerequisites, alternates,
   original object paths, promisor fetches or remote availability may be required.
   Record LFS/submodule/external object closure separately; a Git bundle excludes it.
6. **Preserve the filesystem and index intentionally.** A bundle reconstructs
   committed bytes only. Preserve approved tracked working bytes, staged/index
   changes, deletions, renames, untracked/ignored files and necessary metadata in
   explicit namespaces. Retain a SHA-256 of the original index and a private raw
   copy as evidence when authorized; do not blindly install a shared/split index in
   another repository. Export a portable stage/mode/blob mapping and index-object
   closure, and test its reconstruction before claiming staged-state restoration.
   Never rely on a text patch to preserve arbitrary binary/index state.
7. **Copy without dereferencing.** Use held directory descriptors, `O_NOFOLLOW`,
   type/device/link-count checks and before/after `fstat` around bounded streaming
   reads. Source roots and parent chains must remain stable. Reject symlinks,
   nested `.git`, gitlinks, hardlinks, sockets/FIFOs/devices and mount boundaries
   by default; a later approved type-specific format must describe and independently
   test any exception. Never follow a symlink into an external archive. Do not
   open a database or run project code merely to inventory it.
8. **Separate application data.** Active SQLite/WAL/journals, content/job stores,
   material archives, model files, secrets and environments require their own
   approved consistent snapshots and custodians. Raw file copies of a live database
   are insufficient. Preserve quarantine/ACL/provenance semantics. Link dependency
   manifests by SHA-256; do not pull external data into the worktree archive as an
   unreviewed convenience. C23 ContentStore already has a distinct application
   backup protocol; its production execution is outside WT01B.
9. **Commit completion last.** Recompare source identities, HEAD/refs/registry,
   full index and filesystem manifest, including untracked/ignored scope, with the
   preflight observations. A timestamp/stat check alone is insufficient: compare
   bytes/hashes under the owner-controlled stable window. Write and fsync payloads,
   then a canonical manifest, then its trusted external digest/acceptance record;
   fsync containing directories. No complete marker on failure. Re-read the entire
   accepted archive, compare hashes and independently verify exact inventory.

Unknown exclusions, failed reads, races, missing approvals, permissions, checksum
mismatches or timeouts retain `WORKTREE_LIFECYCLE_HOLD`. Retain partial destinations
as private failed evidence; do not automatically delete or retry into them. Do not
mark a partial tree complete. Approval for preservation never permits source cleanup.

## Integrity manifest contract

Use versioned UTF-8 JSON with a documented canonical serialization (sorted keys,
fixed separators, no NaN or duplicate keys). SHA-256 covers exact emitted bytes.
Encode filesystem path bytes losslessly (for example base64 plus display name),
and reject unsupported encodings/collisions before restoration. Display names are
not authority. All payload names are relative to their namespace: reject absolute,
empty, repeated-separator, dot, dot-dot, NUL and `.git` components. Do not use tar
extraction with trust in archive member names or link targets.

| Manifest section | Required evidence |
| --- | --- |
| Identity/provenance | Schema, UTC time/window, repository IDs, source/registry identities, exact HEAD/tree/ref IDs, tool/Git/OS versions, policy and approval-record digests |
| Git payload | Bundle relative path, length and SHA-256, exact advertised ref/tip set, prerequisite-free verification result, object closure and LFS/submodule decisions |
| Filesystem entries | Namespace and path bytes, type, size and SHA-256 for every regular file, mode, required timestamps/uid/gid/ACL/xattrs, directory/empty-directory records, staged/working/untracked/ignored category |
| Index | Raw evidence digest and portable stage/mode/blob mapping; include removed tracked paths and all necessary blob objects |
| Exclusions | Every excluded item/type with owner-approved rationale and reproducibility consequence; unknown never becomes excluded automatically |
| Dependencies | External manifests/digests, environment/lockfiles, package/artifact availability and environment recipe; secret acquisition references, never secret values |
| Limits/results | Agreed limits, actual counts/bytes, full enumeration/read success, source recheck, archive re-read, unresolved gates and explicit completeness state |

Keep the manifest's own digest outside the manifest. Anchor it in a separately
controlled approval/verification record (signature or authenticated private record).
A digest stored beside an editable archive detects accidental corruption but
does not establish authenticity. The verifier must receive the trusted digest
independently; never accept a replacement digest from the archive being verified.
Checksums prove bytes, not ownership, historical relevance or backup completeness.

## Independent restoration and acceptance

Run a separately reviewed verifier in a new private isolated root or host with
no access to the original source, common Git store, alternates, external mounts or
network. Use the trusted manifest digest first, then validate schema, exact entry
set/types, lengths, modes and every SHA-256 before constructing any restoration.
Reject unexpected files, duplicate JSON keys/entries, unsafe names, links, changed
inodes, excessive sizes, unsupported metadata or missing dependency manifests.

Initialize an empty repository with hooks, fsmonitor, inherited Git config,
replace refs and all network protocols disabled. Import only verified bundle
objects; verify the bundle without original prerequisites, run full object checks,
compare exact HEAD/tree and the reviewed advertised tips. Do not restore original
`.git` pointers, registry files or configuration into the new root. Disable external
filters and identify filter-dependent worktree bytes explicitly. No application
autostart. No real checkout or object store is a fallback for missing bytes.

Reconstruct approved staged and working state separately, including deletions and
mode changes, from verified objects/mappings/payloads. Recompute a new full manifest
of the restore and compare exact paths, categories, hashes, modes and necessary
metadata. Reject extra files apart from explicitly allowed newly generated Git
administration. Independently compare NUL-delimited index/status semantics, not
index byte identity. Test content/application behavior only on approved synthetic
data or separately authorized restored application snapshots, preserving their
ACL, quarantine and provenance gates. A filesystem restore and an operational
application restore receive separate acceptance states.

Record verifier identity/version, isolation evidence, source unavailability,
input/manifest digests, exact HEAD/tree, all checks and failures, dependencies,
time and remaining limitations. Accept only after a second reviewer checks the
evidence against the approved source scope. A bundle verification or successful
checkout alone is never a successful complete restoration. Partial restores stay
fenced/private with HOLD and are not reused automatically.

## Synthetic executable evidence and limits

Run from the assigned worktree:

```sh
python3 -m unittest tests.test_worktree_preservation -v
python3 -m unittest tests.test_worktree_manager tests.test_worktree_manager_independent -v
```

[The protocol experiment](../../tests/test_worktree_preservation.py) constructs its
own temporary repository and fabricated committed, ignored and untracked bytes.
It accepts no operator source path and has no CLI archive/restore command. It
demonstrates a standalone bundle, exact regular-file/directory manifest, trusted
SHA-256 anchor, manifest-last capture, independent reader and isolated restore.
The success test makes the original fixture path unavailable before restoring;
the restore uses an empty object store, disables inherited Git configuration and
remote protocols other than local file transport, and rejects alternates.

This experiment uses a single-process temporary fixture. It is **not** a hardened
copy engine: full descriptor-relative traversal, durable fsync/acceptance records,
adversarial concurrent parent swaps, mount namespaces, privilege isolation,
case/encoding portability, ACL/xattr preservation and application snapshots need
separate implementation and validation. It rejects dirty tracked/staged state,
masked indexes, special types, nested repositories and links. Fixture payload
budgets are 100 entries/1 MiB, manifest 64 KiB, subprocess timeout 15 seconds.
Its fixed synthetic bundle ref is not a detached-HEAD production exporter.
No real worktree preservation or operational reproducibility is claimed.
