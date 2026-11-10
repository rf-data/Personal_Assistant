# M2.2a validation record

Reference HEAD: `8190fcc805f4b361f1b91b23805e8941691deab2`.
Architecture, invariant mapping, limitations and M2.2 acceptance steps:
[verified-lecture-source-m22a.md](verified-lecture-source-m22a.md).

## Execution boundary

Only `/tmp/m22a-verified-handoff-k4julser/repo` was edited. The archive was taken
from the exact reference HEAD, without incorporating unrelated dirty M2.1 files.
Relevant existing dirty reports were copied separately into `../context` for
read-only context. The protected original checkout has 1,160 tracked/untracked
nonignored files in the before/after hash inventory. No virtual environment,
real-source workspace, provider configuration, stash, old branch or old worktree
was adopted, modified or removed.

The isolated detached `.git` metadata reads original existing objects through an
alternate; it has no remote and no new branch/commit. No commits, pushes, PR
updates, merges, force operations, cleanup or changes to the protected checkout.
The local preinstalled Python is used read-only; bytecode and pytest cache are
disabled. Test roots and log/evidence outputs are all inside the task-owned `/tmp`
directory. All selected tests are offline; external-integration opt-ins are absent.

## Reproduction

From the isolated repository root, use the existing Python 3.12 environment with
pytest, Pydantic and BeautifulSoup dependencies. The exact interpreter used was
`/home/robfra/0_Portfolio_Projekte/Personal_Assistant-cs50-m2a/.venv/bin/python`.

```bash
python -B -m pytest -p no:cacheprovider \
  tests/test_cs50_summary_readiness.py \
  tests/test_cs50_learning_mvp.py \
  tests/test_cs50_summary_mvp.py \
  tests/test_cs50_summary_batch.py \
  tests/test_cs50_summary_batch_stress.py \
  tests/test_cs50_summary_c27_regression.py \
  tests/test_content_index_projection.py \
  tests/test_content_fts.py \
  tests/test_content_read_contracts.py \
  tests/test_content_store_integrity.py \
  tests/test_content_store_adapters.py \
  --basetemp=/tmp/m22a-verified-handoff-k4julser/final-tests \
  --junitxml=/tmp/m22a-verified-handoff-k4julser/final-results.xml -q
```

Never reuse a directory containing valuable data as pytest `--basetemp`; these
paths are task-created disposable test roots. The final log is `../final-tests.log`.
Lint: `ruff check` and `ruff format --check` on the three affected source files
and the new test module. Patch whitespace: `git diff --check`.

## New contract matrix

| Scenario | Expected outcome |
| --- | --- |
| Fully published source, no index directory, FTS build/query explicitly forbidden | Complete summary; source stays `published`; legacy M1 rejects that source phase. |
| 171 long blocks after one deterministic failed public FTS call | Complete FakeLLM handoff, 226 slices/claims, 8 batches, full original references; source stays `index_pending`. |
| Cache and separate guarded process | Identical report; zero additional FakeLLM calls; no source/output byte changes. |
| Invalid status/actor/actions/expiry/schema/raw/code/digest; schema 2 in new path | HOLD before summary-root creation/dispatch. |
| Invalid historical ProcessingApproval or parser | No summary plan/approval issued. |
| Raw/payload/projection byte corruption | HOLD; no source repair/retry. |
| Missing block, altered locator, missing quality, unpublished/quarantined source, version mismatch | No summary plan. Targeted DB corruption restores exact schema before verification. |
| ACL revoked via real API | Denied before planning or immediately after the first reply; no second dispatch or completed summary. |
| Reader omission, truncated text window, false locator, foreign DTO version | No summary plan. |
| Source/approval/code/version/expiry change after first reply | Exactly one call, then HOLD; no consolidated summary. |
| Source changes during final manifest publication | Final state becomes HOLD; cached completion cannot be accepted. |
| Official origin in new path | Explicit synthetic-only rejection pending M2.2. |

## Development checks (not final acceptance)

An unchanged small M2.1 cache regression passed first (1 passed, 4.80 s).
The initial new checks exposed a strict comparator that ignored public Reader
redaction, plus test mutations blocked by immutable DB triggers. The comparator
now follows the existing redaction contract; targeted fault injection restores
all trigger definitions. After that, 10 approval/small-source checks passed in
33.04 s. A preliminary full new-suite run reported 37 passed / 3 failed in
293.18 s: the long summary itself completed with full coverage, but its harness
incorrectly demanded 100/71 item pages rather than respecting the Reader byte
limit (actual 88/83); two ACL fixtures left a WAL open. The harness now verifies
complete bounded pages, closes/checkpoints its own synthetic SQL writes, and
uses the real grant/revoke API afterward. The targeted 13 ACL/publication cases
then passed in 32.53 s. These are development corrections, not retries of any
failed retrieval request. No product check, deadline or immutable-store rule was
weakened in response.

## Final results

The final 171-block proof passed, including cache and a guarded separate process.
It processed **226 requests / claims**, **320,416 of 320,416 original codepoints**,
with **100% input coverage and citation coverage**, no excluded/uncited refs,
and batch sizes **32,32,32,32,32,32,32,2**. Real Reader pages were **88,83** due
to its existing byte bound. FakeLLM generation took **175.553 s**, below the
unchanged **600 s** global and **120 s** per-batch wall budgets; retries stayed 0.
Source phase remained **index_pending**, and its complete inventory stayed equal.
The public FTS attempt/success count was **1/0**, with deterministic original
Unavailable fault injection. The separate small proof forbids every FTS backend
build/query and succeeds with no index directory. Summaries remain **unreviewed**.

Machine-readable proof: task-root `synthetic-handoff-evidence.json`; original
full outputs remain in `final-tests/test_171_long_lecture_after_fa0/`.
`implementation-binding.json` confirms that the schema 3 approval and final intent
bind current actual Python bytes and the same source verification digest.

**423 passed, 0 failures, 0 errors, 0 skipped**, in **1,154.26 s (19:14)**.
The 40 new contract tests and 383 existing regression tests all passed in one final
run. Python 3.12.12, SQLite 3.50.4, pytest 9.1.1, Pydantic 2.13.4, Linux x86_64.
JUnit confirms 423 tests with no skipped cases. `ruff check`, `ruff format --check`
(all four Python files) and `git diff --check` passed.

The protected original HEAD is unchanged at the reference commit. All **1,160**
tracked/untracked nonignored file hashes and the exact staged/unstaged/untracked
Git status match the initial observation (`protected-final.json`). Only two
existing files differ from reference in the isolated copy: the two Summary
modules. Every existing ContentStore, FTS, B1 and other file is byte-identical
(`patch-boundaries.json`). New files are the readiness module, tests and these
two uniquely named reports. Existing M2.1 documentation/evidence is not overwritten.

The full patch applies in a fresh reference-file check tree and passes a read-only
`git apply --check` in the actual protected checkout, including its unrelated dirty
documentation. No patch is applied there. Source and tests are unchanged after the
final test run. The patch, proof, reports, log/XML and preservation records are
packaged in task-root `m22a-delivery.tar.gz`; a source-only implementation patch
is also provided. Apply the full patch or the source-only patch, not both.

**Bounded synthetic handoff verified. Product release, real-source acceptance,
and default-branch integration remain pending.** This is not an unconditional
security-equivalence or semantic-acceptance claim; the architecture records the
cooperative-lock and revocation limitations.

## Retention and pending work

Retain the isolated copy, patch, original synthetic result roots, logs and reports
because this task forbids integration and these are the only delivery copies.
No task-owned linked worktree or branch needs removal. The detached copy metadata
is retained to reproduce implementation-revision checks and patch validation.
Repository-lifecycle completion is pending integration of reviewed changes and
durable records into `master`. M2.2 real-source acceptance and human semantic
review are pending; no real-source approval is inferred from this PoC.
