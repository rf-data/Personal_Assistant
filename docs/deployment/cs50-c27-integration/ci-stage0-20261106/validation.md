> **Status update — 2026-11-06:** The three CI files were subsequently
> applied to the Stage-0 review worktree. The validator, 13 unittest
> methods, package checks, and Ruff 0.16.0 formatting check were
> successfully repeated locally. The original report below records
> Codex's earlier handoff state. A hosted GitHub Actions run remains
> pending.

---

# C27-14: Self-contained Stage-0 CI — prepared, target placement pending

Date: 2026-11-06. Repository: rf-data/Personal_Assistant, PR #171.

The supplied review worktree is outside this session's writable filesystem roots.
No files were written there. The implementation is available under `files/` next
to this report and in `C27-14-ci-only.patch`. That additive patch passes
`git apply --check` against the unchanged target. Placement in the target and any
live execution remain pending. No integration or completion is claimed.

## Exact intended repository additions

1. `.github/workflows/c27-stage0.yml`
2. `ci/c27-stage0/validate.py`
3. `ci/c27-stage0/tests/test_validate.py`

The optional tests file supplies negative integrity cases. No other repository
addition is intended. This report, the additive delivery patch, hash inventories
and independent local test clone are task artifacts under `/tmp`, retained for
handoff. They are not part of the repository patch and are not durable storage.

## Implementation

The workflow runs for pull requests targeting master, including draft PRs; event
types are opened, synchronize, reopened, ready_for_review and converted_to_draft.
There is no draft skip or source-branch restriction. It uses ubuntu-24.04,
Python 3.12, contents:read, full-SHA action pins, the actual PR head SHA,
fetch-depth:0 and persist-credentials:false. Checkout clean:false avoids implicit
reset/clean behavior. There are no package installations, custom secrets or
deployments. Checkout/setup-python use the normal automatic GitHub token.

The validator checks the complete seven-file Review-v2 package, pins SHA256SUMS
itself and the manifest and patch separately, checks six product hashes/lengths/
non-executable modes, all 40 unchanged prerequisites, both deferred profile paths
and absence of the 55 Stage-1 overlay paths. Python product and prerequisite files
are compiled without importing third-party dependencies or writing bytecode.

It obtains base a8af1d9372eb435d3e1331c33b047d21120d57c2 from Git, checks ancestry,
exports that base to a temporary directory, validates preconditions and applies
the exact existing v2 patch there. All six resulting product hashes and the 40
prerequisites are then checked again. No second worktree is registered or needed.

Smoke tests execute unchanged AST-selected production function bodies and their
actual constants/stdlib dependency closure. They cover valid/rejected static source
bytes, ZIP inventory/content/hash, malformed/traversing/symlink ZIP members and
real Linux renameat2 publication, no replacement, temporary cleanup and movement
between directories. They do not certify complete module imports or full runtime
behavior. No fake Pydantic/BeautifulSoup/HTTPX modules are injected.

## Executed validation

- Read target AGENTS.md and .pre-commit-config.yaml.
- Confirmed review/c27-stage0-20261105, exact expected HEAD and clean index/worktree.
- Read-only GitHub metadata: PR #171 open, Draft, unmerged, base master, expected
  head d55e1f733bf7ba0fe9d818fc51bfcb12128522f4 and expected base.
- Validator against actual unchanged review HEAD: PASS using Python 3.12.12,
  `python3.12 -I -S -B .../validate.py --root <review> --expected-head <full SHA>`.
- 13 unittest methods against disposable fixtures copied from review: PASS,
  including independent corruption of all 6 products, all 40 prerequisites and
  all 7 package files, rewritten manifest/checksums, missing/executable files,
  file/parent symlinks, both deferred profiles and dangling links, Stage-1 overlay,
  unsafe paths and wrong PR head.
- Created independent local clone using `git clone --no-local --single-branch
  --no-tags --branch review/c27-stage0-20261105 <review> <temporary clone>`.
  It has no object alternates, virtual environment, SOURCE contents or R18 helper.
  Copied only the three intended CI additions into it.
- Executed workflow-equivalent commands in that clone with Python 3.12.12:
  `python3.12 -I -S -B ci/c27-stage0/validate.py --root . --expected-head <full SHA>`
  and `python3.12 -I -S -B -m unittest discover -s ci/c27-stage0/tests -v`.
  Both PASS; all 13 tests passed in 0.527 seconds. Positive validator checks include
  actual patch application, all integrity checks and real renameat2 smoke.
- Syntax: ast.parse and compile on both new Python files: PASS, no bytecode written.
- Ruff 0.16.3 format --check with target pyproject.toml: PASS, 2 files formatted.
  Only new Python files were formatted; the original hash-bound patch was untouched.
- Ruff 0.16.3 check with target configuration: PASS.
- Actionlint 1.7.12: PASS.
- PyYAML BaseLoader parse plus assertions on event/branch/draft behavior,
  permissions, runner, Python, action SHA pins and checkout settings: PASS.
- Additive CI-only patch `git apply --check` against target: PASS, no application.
- All three delivered files byte-match the successfully tested clone copies.
- Final target comparison: all 13 original files byte-equal to the blobs in
  d55e1f733bf7ba0fe9d818fc51bfcb12128522f4, with empty index and clean worktree.
  Exact original hashes are in original-13-sha256.json; delivered hashes are in
  ci-files-sha256.json.

## Not executed and remaining limits

No real GitHub Actions run, action download/bootstrap, hosted ubuntu-24.04 run or
repository Actions-policy check was performed. Execution is expected after the
workflow is actually included in a PR update: synchronize is enabled for drafts.
Merely creating local files does not generate a workflow event. Live execution
still depends on Actions being enabled and the repository permitting pinned
actions. Python setup may download the interpreter; validation itself installs
no packages and uses no network calls.

The historical review_integrity_v2.py runner was not executed: it requires SOURCE,
v1/combined candidates and external artifacts that are absent in a fresh checkout.
Its bytes and recorded results are integrity-checked, not presented as a new run.
Full Pydantic acquisition model imports, BeautifulSoup HTML/transcript validation,
full runtime/dependency tests, host/semantic acceptance and B1 diagnostics were
not executed. The smoke tests cover selected production bodies only. Ruff used
the locally available 0.16.3, not pre-commit's configured 0.16.0; the full
pre-commit suite was not run or downloaded.

The SOURCE checkout was not modified. Its existing dirty/untracked data was left
untouched. No commits, pushes, PR changes, merges, resets, Git cleans or worktree
cleanup were performed. Original branches/worktrees remain. The temporary clone
and delivery artifacts are retained for inspection and handoff; no task integration
has occurred. PR #171 remains Draft; SQLite B1 remains open; Stage 1 is separate.

## References checked

- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request
- https://github.com/actions/checkout/tree/11bd71901bbe5b1630ceea73d27597364c9af683
- https://raw.githubusercontent.com/actions/setup-python/a26af69be951a213d495a4c3e4e4022e16d87065/action.yml

The action inputs and SHAs were read from their pinned upstream versions.
