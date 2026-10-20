# DEV-02B – Controlled source import

20.10.2026. Base: master `7a4f2be` (DEV-02A #126 integrated). This package
adds execution to the existing C16 queue and C23 verified publication adapter.
It does not introduce a source registry, database, scheduler or parser.

## Actual handoff and supported inputs

Operator-approved hash catalog → explicit import preview → C16 confirmed job →
C16 pinned input snapshot → real C23 `VerifiedPublicationCandidate` → existing
raw reservation / SourceVersion / atomic ParsedVersion publication → hash-bound
redacted job receipt → existing Content Read → separately confirmed DEV-01B
index job → existing FTS5 search.

Prepared PDF-v2, HTML-v2, code and SRT bundles are supported. **Raw PDF alone is
not an import bundle.** C18/C19 normalization remains a separate existing step;
this endpoint never reparses, downloads, executes source code or extracts knowledge.
TXT/VTT are unsupported here. Unknown-time contracts are unchanged.

The gateway currently admits only explicitly synthetic-origin bundles. Real source
release is not represented by a new boolean: the necessary D07 source-specific
release contract is still absent. Official bundles remain usable through their
existing separately authorized offline adapter, not through this MVP gateway.
Historical SRT source-path mismatches remain rejected (D06); no fallback or migration.

## Private operator configuration

`Settings.import_jobs_enabled` defaults to false. Execution additionally requires
existing `execution_enabled`, a live worker, operator identity and course scope.
Use the same private C16 settings for API and worker, and pass the existing
`--content-config` to API startup. Existing `--search-config` is needed only for
search/index functions. No new environment credentials or startup service.

An entry of `CatalogEntry.kind=content_import_bundle` has `roles={"import":
"import.v1.json"}`. Its hash-pinned files include the spec and the **entire explicit
bundle closure**, not just raw/payload: unchanged receipt, original material/adapter
plan, implementation attestation, any prior quality report and referenced images.
The private spec is `ContentImportPlan`: existing `ContentReadSettings`, existing
`InventorySelection` and explicit `allowed_subjects` (1–32 unique backend subjects).
Only those operators may initialize that Source; existing sources also require
current write ownership/ACL. UI widgets never grant rights.

Bundle workspace and all selected paths must lie within that approved input root
and every role must be declared. The workspace may be a child directory so canonical
relative raw paths and original provenance remain intact. Input root, ContentStore,
key and C16 job root must be separate. ContentStore must already be initialized;
there is no implicit root creation/recovery. Spec ContentReadSettings must equal the
actual served Content settings.

The existing C16 limits apply unchanged: 128 declared files, 8 MiB per file,
32 MiB per bundle. Runtime: 180 s wall, 120 s CPU, 768 MiB address space,
64 MiB output file, 64 descriptors, 32 processes (kernel UID limit). Large prepared
PDF bundles can therefore be rejected despite being acceptable to the offline C23
adapter. No limit is raised to accommodate a test. C23 staging/capacity limits and
receipt/hash/schema/quality gates remain authoritative.

## HTTP contract

All routes use existing C16 authentication. Bounded JSON is limited to 256 KiB;
no host paths, raw text, private receipts or tokens appear in import responses.
Source/subject authorization is retained through response delivery (2 s budget),
including generic C16 job/history/log/artifact metadata.

| Action | Route / payload | Result |
| --- | --- | --- |
| Capabilities | `GET /v1/content/import/capabilities` | schema 1, enabled, adapter names and explicit unsupported capabilities |
| Selection | `GET /v1/content/import/inputs?offset=0` | at most 10 currently authorized input/source/course/adapter refs, next_offset; no global count |
| Preview | `POST /v1/content/import/preview` with schema_version=1, input_ref, request_key | ImportPreview: actual C23-verified ImportInfo and existing C16 Preview, or explicit recovery decision and null Preview |
| Confirm | existing `POST /v1/jobs`, confirmed=true, start=true, returned Preview; Idempotency-Key equals preview request_key | persisted existing C16 Job |
| Observe/cancel | existing C16 jobs/history/logs/artifacts/cancel | current owner-authorized lifecycle |
| Published result | `GET /v1/content/import/result?job_id=…` | verified ImportReceipt bound to current published version and original raw hash |

Request keys are 16–64 ASCII identifier characters. Input references come only from
the operator catalog; the browser cannot supply paths, arbitrary payloads or a
`verified` flag. Preview returns the exact adapter/parser/config/implementation
revision, expected SourceVersion/ParsedVersion IDs, raw/payload hashes, current
source-state digest, existing version, limits and operator decision. The expected
IDs use the existing C23 identity functions; they are not a publication claim.

Input bytes are hash checked and copied to a private temporary snapshot **before**
any gate can follow payload references. Gates only see declared snapshot files.
C16 confirmation reruns verification; worker snapshots again and reruns the real
C23 gate. The source-local state fingerprint binds source state/ACL revision,
versions and processing runs, excluding unrelated sources. Stale state is rejected;
C23 transactional publication and live ACL verification remain the final fence.

404 hides unapproved/fremd subjects, revoked/tombstoned sources and unavailable
published versions. 409 reports blocked input/recovery or undetermined publication;
422 rejects malformed requests, missing/hash-changed/oversized files; existing C16
confirmation can return 409 conflict or 503 verification unavailable. Diagnostics
are fixed redacted codes, not exception text. An HTTP failure is never success.

## Idempotency, interruption and recovery

Same actor/key/intent returns the same C16 job, including terminal failure. A key
cannot confirm a different plan. Another explicit key with the same valid bundle
uses existing C23 semantic idempotency and returns the existing ParsedVersion;
`created=false` means no duplicate parsed publication.

Cancellation and timeout use the existing guardian, process-group cleanup and
persisted C16 status. Unknown cleanup keeps the existing C16 quarantine fence.
There is no automatic rerun or lock takeover. A job error/interruption does not
prove that no ContentStore commit occurred.

Before parsed commit, complete/incomplete prepared Content runs remain subject to
existing C23 recovery. Preview reports `content_recovery_required`, `can_import=false`
and no executable preview. An operator must inspect/recover/reject through the
existing recovery interface before a new explicit plan; the HTTP worker does not
adopt staging or invent a retry intent. After commit with response loss, current
preview can identify the already published version and a new explicit request can
return it idempotently. A job without its verified result receipt responds
`publication_not_determined` (409), rather than asserting rollback.

Original raw/payload/receipts/IDs are preserved byte-for-byte. UI output is a redacted
receipt; unchanged provenance artifacts remain in the existing private ContentStore.
Index input selection must be separately preapproved and becomes visible only after
its exact version exists. Publication never builds/activates an index.

## Offline evidence and remaining integration

See `tests/test_content_import_jobs.py`: actual C16 subprocesses, four format gates,
raw/payload roundtrips, SIGKILL before commit and after completed commit, real guardian
timeout, cancellation, duplicate keys, ACL/role changes, integrity/type/evidence
failures and explicit FTS5 search/restart. All files/roots are owned synthetic test
data. PDF test validates a prepared PDF-v2 bundle, not a new native PDF parser.

The Streamlit package is a separate dependent UI PR. No real import, live service,
external request, product deployment or fachliche Realabnahme is performed here.
Durable documentation awaits regular PR integration. Keep this task's branch and
worktree while the PR is unmerged; no historical/MAINT artifacts are cleanup targets.

## Validation record

Python 3.12.12, Pydantic 2.13.4, SQLite 3.50.4, Pytest 9.1.1,
Ruff 0.16.0 from existing environments; no dependency installation.

Actual command prefix (existing backend environment):

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  /home/robfra/0_Portfolio_Projekte/gmp_compliance/.venv/bin/python -m pytest \
  -q -p no:cacheprovider
```

The first new-file collection failed due to a test-helper re-export removed by
linting (zero tests executed). Intermediate development runs: 5 passed/1 failed
(54.44 s), 7 passed/2 failed (65.00 s), 8 passed/2 failed (78.33 s). Corrected the
probe's before/after-transaction placement, stale-plan error mapping and test helper
imports. A targeted two-case development run failed on incorrect test expectations:
quarantined versions are intentionally hidden with 404, and exclusive maintenance
uses the existing artifact lock. Assertions now verify those actual contracts.
The two errors were also present in the broader run started before correction.

The corrected 18-case import suite passed **18/0/0**, 173.44 s
(`tests/test_content_import_jobs.py --basetemp=/tmp/dev02b-import-final`). It includes
actual process faults and verifies unchanged raw/payload bytes for all four formats.
A subsequent worker-state recheck immediately after bundle verification has its own
final rerun below. Overlapping runs are never added as independent case counts.

Broader targeted regression (same prefix, `/tmp/dev02b-release`):
`tests/test_content_import_jobs.py tests/test_content_index_jobs.py
 tests/test_source_management.py tests/test_job_control.py tests/test_workflow_http.py`.
**117 passed / 3 failed / 0 skipped**, 473.32 s. Two failures were the corrected
new test expectations above; the third was an existing workflow HTTP schema snapshot
whose embedded Artifact enum needed the new `content_import` output kind. Both
versioned snapshots were updated from the actual existing models, without changing
workflow runtime or assertions. All 19 index-job, 11 source-management and 36 C16
regression cases passed, and the other 36 workflow HTTP cases (including native PDF
execution/cancel/timeout/restart) passed. The corrected schema check is recorded below;
this is not presented as an executed fully green 120-case rerun.

Final worker-state rerun: **18 passed / 0 failed / 0 skipped**, 119.94 s
(`tests/test_content_import_jobs.py --basetemp=/tmp/dev02b-state-final`).
Final schema rerun: **2 passed / 0 failed / 0 skipped**, 2.78 s
(`tests/test_workflow_http.py::test_versioned_schema_snapshots_and_original_c16_models
 tests/test_job_control.py::test_transport_contract_snapshot
 --basetemp=/tmp/dev02b-schema-final`). Ruff check and format check for all
22 checked job-control/test files and diff check pass. Existing A HTTP/read validation
is separately documented in `source_management_v1.md`; no counts are added together.

UI synthetic AppTest against this implementation independently passed all six
new cases (92.88 s), including real C16 worker/ContentStore publication, separate
index activation, FTS5 search, process restart, Sourcegrant revocation and identity
change. The separate UI PR documents the exact test environment and limitations.

## PR / Project / lifecycle status

DEV-02A [#126](https://github.com/rf-data/Personal_Assistant/pull/126) is merged at
`7a4f2be`. All seven intended file blobs (including durable documentation) were
compared with actual `origin/master` and match exactly. Its remote branch was already
absent. No open PR referenced its head/base; all process CWDs were readable, with
zero users of the task-own A worktree. Only 77 identified task-generated pyc/Ruff
cache files remained, no uncommitted/untracked work. Normal `git worktree remove`
and `git branch -d` removed exclusively `Personal_Assistant-dev02a` and
`feat/dev02a-source-management`. Default master stayed `7a4f2be` and integrated docs
remain present. No historical/MAINT branch, primary checkout or other task changed.

DEV-02B [#127](https://github.com/rf-data/Personal_Assistant/pull/127) is open.
Dependent UI [#17](https://github.com/rf-data/personal-assistant-ui/pull/17) is Draft.
Their branches/worktrees remain because regular integration is pending; durable
records are part of those PRs, not claimed integrated into default branches yet.

Live Project #1 was checked before and after each insertion. #126 already existed;
#127 and UI #17 were absent and each added once. Final live inventory contains each
PR exactly once. #126 was already Done through the existing project lifecycle;
#127/#17 are Backlog. No field/status/workflow or Issue closure was performed.
Existing C23 #98, C28 #102, C24 index #115 and UI C25 #9–#13 remain referenced,
without creating duplicates or closing broader/real acceptance work.
