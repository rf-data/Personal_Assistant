# PR #174: SQLite FTS5 diagnosis (synthetic only)

Date: 2026-11-08. Source: `rf-data/Personal_Assistant`, commit
`8190fcc805f4b361f1b91b23805e8941691deab2`.

## Decision

The exact SQLite error in the isolated reproduction is
`sqlite3.OperationalError: interrupted`, error code **9**, error name
**SQLITE_INTERRUPT**. The interruption occurs before MATCH. An expired shared
search deadline explains these reproduced failures. The historical traceback
contains only the redacted wrapper, so its original SQLite exception and its
specific failing operation remain **UNKNOWN**.

No product patch is justified by this evidence. Keep the 2-second deadline and
all integrity checks. Do not add retries. Hold release approval on the unresolved
intermittent failure; the successful targeted checks below are bounded synthetic
validation, not proof of the original run's cause or a release acceptance.

## Scope and preservation

Read the repository-wide AGENTS.md in both supplied checkouts. The target was clean
and HEAD matched the specified commit. All experiments used a separate local clone
and archived reference under `/tmp/pr174-fts-lv0bf9db`; no registered worktree or
branch in the shared repository was created. The clone is detached at the source
commit. Only its new report is an intended repository document; product and existing
test sources remain unchanged.

No real CS50P data, historical failure roots, historical approval contents, network,
provider, commit, push, PR action or merge was used. Fresh fixture-generated
synthetic approvals are used only by their normal test pipeline. Diagnostic logs
contain numeric timings, fixed phase labels, exception class/code/name, counts and
allowlisted SQLite message `interrupted`; no bound SQL values, source texts or
approval payloads. Expanded SQLite trace callbacks are not enabled.

The report and diagnostic artifacts remain in `/tmp` for review and reproduction.
The explicit task prohibition on Git integration takes precedence over AGENTS.md's
default-branch document lifecycle: no claim of integration into `master`, PR merge
or shared-artifact cleanup is made. The isolated copy and fresh synthetic roots
are retained as the diagnostic evidence, not removed with the only reproduction.

## Full search path and budget

1. `scripts/cs50_learning_mvp.py:532` performs the first lexical search after index
   activation, before `ready`. Later MVP reporting performs further separate
   searches. An active index alone does not mean MVP retrieval completed.
2. `ContentIndex.search_lexical` validates query/cursor and capacity, takes catalog,
   maintenance and ContentStore connection guards, then establishes
   `deadline = time.monotonic() + QUERY_SECONDS` (`content_index.py:744`, 2.0 s).
3. `_search` validates the active manifest and backend; selects visible sources
   using live ACLs. For each visible source it calls `_export` / `_project_locked`,
   revalidates publication artifacts, blocks, locators and material handoff, creates
   live IndexRecords, and hashes/verifies their complete recordset against the
   manifest. These operations already consume the shared deadline.
4. `IndexFiles.read` loads the bounded private source file with inode/ownership
   protections. Length and SHA-256 are checked. Only verified bytes are passed to
   `_search_partition` (`content_index.py:852`).
5. `content_fts.search_database` checks the backend capability and byte limit,
   connects to an isolated `:memory:` database, deserializes the checked bytes, and
   installs its progress callback every 1,000 SQLite VM instructions. The callback
   interrupts if `time.monotonic() > deadline`.
6. `_check` validates application/user IDs, the exact schema including FTS shadows,
   full `PRAGMA integrity_check`, metadata, row count, every canonical record body
   and text, FTS/records rowid and text equality, and the FTS5 `integrity-check`
   command with rank 1. These checks are retained in all experiments.
7. Only afterward does SQLite set `query_only=ON`, execute the bound MATCH/join/
   bm25/order/limit query and materialize results. The source connection closes in
   `finally`. Scores, match limits, current records, hydration, locators, cursor
   and result size are processed under the original guards. `_search` checks the
   deadline after partition work and again after hydration. Context completion has
   the separate existing response guard (`deadline + 3`), which does not authorize
   successful query work beyond the query deadline.
8. Every `sqlite3.Error` in the adapter is mapped to
   `Unavailable('FTS query/database unavailable') from None`. This suppresses the
   displayed SQLite context, not necessarily Python's `__context__` attribute.
   Isolated tests can inspect that attribute without changing public messages.

Builds have a different 900-second budget. Their `_check` during construction and
verification of staged bytes are not additional repeated checks inside one
2-second query. There is one full `_check` per searched source, repeated across
separate requests. There is no validation cache introduced by this diagnosis.

## Instrumentation and limitations

Runtime: Python 3.12.12, SQLite 3.50.4, Pydantic 2.13.4, pytest 9.1.1, Linux x86_64,
4 available CPUs. The existing target virtualenv was read as the interpreter;
`-B` / `PYTHONDONTWRITEBYTECODE=1` prevented bytecode writes there. No installation
or download occurred. `environment.json` records the exact environment.

`harness/fts_probe.py` wraps only FTS connections, not the ContentStore database.
It records native errors from execute/fetch/cursor iteration before redaction.
Phase boundaries are inserted into an in-memory copy of `_check` with its same
statements and checks; monotonic clocks bracket the file read, deserialize,
schema/integrity, record comparison, FTS equality, FTS integrity, and MATCH work.
The original source bytes on disk are not edited. Projection subphases are timed
with wrappers. No sleeps or altered product deadlines are used in elapsed-time
measurements. Wall-clock monotonic durations include scheduling time; they are
host-specific, not capacity or throughput guarantees. Phase timings are rounded
medians from fixed sample counts; medians do not have to sum to the total median.

`pre_partition` includes manifest/ACL work, live export and recordset proof work.
`deserialize` includes the subsequent progress-handler setup. `match_bm25`
includes execute and fetchall, plus the following connection-close boundary.
`post_partition` includes ranking and hydration. `_search` measurement starts
immediately after the deadline is passed in and finishes before the caller uses
the response; input validation and the initial lock acquisition are outside it.

## 171 blocks / 226 records: normal phase profile

A full fresh `lecture_171` stress test passed (82.16 s). Its five searches took
0.5003–0.6463 s. Then eight independent searches of that same newly generated
synthetic source all succeeded. The source SQLite snapshot is 1,724,416 bytes.
The following medians are from those eight diagnostic searches, not cProfile:

| Phase | Median milliseconds |
| --- | ---: |
| Manifest, ACL, live projection and recordset work before source file | 512.977 |
| Index file load | 1.363 |
| Source hash / backend dispatch | 4.988 |
| SQLite deserialize and handler setup | 1.247 |
| Schema / SQLite full integrity checks | 9.896 |
| Backend metadata check | 0.058 |
| Record count / canonical body and text comparison | 17.401 |
| FTS versus records row/text comparison | 1.807 |
| FTS5 integrity command | 8.409 |
| query_only setup | 0.022 |
| MATCH / bm25 and materialization | 0.360 |
| Ranking / hydration / result work | 1.521 |
| **Total** | **559.367** |

Total range: **512.993–737.944 ms**. Budget remaining on adapter entry:
**1.3157–1.5307 s** (median 1.4807 s). `_check`'s combined normal cost is about
38 ms at this size; it does not consume a 2-second budget on this host. The live
projection and its surrounding proof work dominate. Nested projection timers
and `replay.prof` identify `_records`, `_selection` and `_load` as consumers;
cProfile overhead means its times must not be substituted for phase measurements.
There is no evidence here that the FTS5 integrity command is the dominant cause.

## Controlled CPU contention: exact native exception

Six preplanned independent searches used the same fresh synthetic source. The
search process and three short-lived CPU contenders were pinned to one available
CPU. Only this diagnostic process's affinity was changed and restored; all its
contenders were joined. All six searches returned `Unavailable`. This intentionally
reduces compute available to the search; it is not evidence that equivalent load
existed during the historical failure.

| Sample | Search elapsed (s) | Budget on adapter entry (s) | Failing operation | Error elapsed (s) | Budget at error (s) |
| --- | ---: | ---: | --- | ---: | ---: |
| 0 | 3.071704 | -1.069773 | execute: PRAGMA integrity_check | 3.071522 | -1.071547 |
| 1 | 2.041830 | +0.041628 | next row: records comparison SELECT | 2.041619 | -0.041625 |
| 2 | 3.198769 | -1.184512 | execute: PRAGMA integrity_check | 3.198526 | -1.198530 |
| 3 | 3.172596 | -1.155672 | execute: PRAGMA integrity_check | 3.172352 | -1.172359 |
| 4 | 3.024365 | -1.018073 | execute: PRAGMA integrity_check | 3.024150 | -1.024155 |
| 5 | 2.859800 | -0.847503 | execute: PRAGMA integrity_check | 2.859580 | -0.859585 |

All errors: **sqlite3.OperationalError**, message **interrupted**, SQLite code
**9**, name **SQLITE_INTERRUPT**. The first sample spends 3.0462 s before the
source-file phase. In sample 1, 41.6 ms remained on backend entry; deserialize,
schema checking and record processing then crossed the deadline. Its failure is
`Cursor.__next__`, not the FTS integrity command. The exact static SELECT is the
rowid/record_id/parsed_version_id/content_type/body/text read ordered by rowid in
`_check`. No MATCH was reached in any of these six samples.

The five samples with negative entry budget do not prove the integrity
check itself is slow: the budget is already exhausted before it starts. The
progress handler next observes this while SQLite executes. Python projection,
canonicalization and file IO do not have asynchronous interruption from SQLite's
VM callback; a deadline violation can therefore be observed after 2 seconds while
still rejecting the request. No request is treated as a successful timeout.

## Scaling of synthetic long sources

Fresh sources use the original stress fixture's repeated 1,200 / 1,800 / 2,800
character paragraph lengths, plus its five base blocks. The fixed sample set for
each successful setup contains the five pipeline searches and three additional
measurement queries. The 171-block row uses the separate eight-query replay above.
The 669-block setup is attempted once, stops at its first search error and is not
retried or resumed; its active index is not misreported as a ready MVP.

| Blocks | Index records | Searches | Median total (s) | Range (s) | MVP setup exit |
| ---: | ---: | ---: | ---: | --- | ---: |
| 5 | 5 | 8 | 0.0175 | 0.0170–0.0220 | 0 |
| 46 | 59 | 8 | 0.1411 | 0.1310–0.2104 | 0 |
| 88 | 115 | 8 | 0.2703 | 0.2456–0.3646 | 0 |
| 171 | 226 | 8 | 0.5594 | 0.5130–0.7379 | 0 |
| 337 | 447 | 8 | 1.7026 | 1.4532–1.9455 | 0 |
| 669 | 890 | 1 | 2.5796 | one failed sample | 2 |

At 669 blocks, without imposed CPU contention, the first full search enters the
adapter after its budget is exhausted and fails during `PRAGMA integrity_check`:
`OperationalError`, 9 / SQLITE_INTERRUPT, error elapsed 2.579372 s, remaining
budget -0.579377 s. Nested live projection costs include `_load` 0.3765 s,
`_selection` 0.7374 s, `_records` 1.2530 s. These alone account for about 2.367 s.
Thus deadline exhaustion can precede SQLite work at larger sizes on this host.
The 337-block margin is already small. No inference of a universal complexity
bound or guaranteed supported capacity is made from this small timing sample.

Independent backend-only profiles for the 226- and 890-record snapshots are
reported in the supplementary measurements below. They are separate backend
benchmarks with their own 2-second budget, not altered end-to-end search semantics.

### Independent file-load / backend profile

All ten independent samples succeeded with complete SQLite/record/FTS checks.
The 890-record snapshot that fails in the full path therefore also passes all
checks when measured on its own. Its index bytes are still bound to the original
synthetic manifest. The failure of the end-to-end search is not proof of
structural corruption.

| Phase (milliseconds, median of five) | 226 records | 890 records |
| --- | ---: | ---: |
| Index file load | 1.663 | 4.283 |
| File hash / dispatch | 5.093 | 20.649 |
| Deserialize / handler setup | 0.324 | 1.046 |
| Schema / SQLite integrity | 10.216 | 37.585 |
| Backend metadata | 0.052 | 0.074 |
| Records comparison | 16.953 | 68.080 |
| FTS text/row equality | 1.753 | 7.857 |
| FTS5 integrity command | 8.501 | 32.782 |
| query_only setup | 0.020 | 0.037 |
| MATCH / bm25 | 0.362 | 0.440 |
| Post-partition bookkeeping | 0.006 | 0.008 |
| **Total file load / backend only** | **44.909** | **174.741** |

The backend-only total ranges are 43.857–46.790 ms (226 records) and
168.579–189.272 ms (890 records). Index loading and the byte hash are included;
live ContentStore projection and hydration are deliberately outside this
independent backend benchmark. The unchanged complete search still receives
only the remainder of its original 2-second budget.

## Error-category and cause assessment

| Category | Reproduction evidence | Historical run |
| --- | --- | --- |
| SQLITE_INTERRUPT (9) / interrupted | All six controlled failures and the 890-record scaling failure; callback uses the expired shared deadline | **LIKELY**, not recoverable from the supplied redacted traceback |
| SQLITE_BUSY (5) / SQLITE_LOCKED (6), including extended codes | None observed. FTS runs on each connection's private in-memory deserialize snapshot, rather than an on-disk index shared with a writer | **UNKNOWN**, not established or conclusively excluded by that traceback |
| SQLITE_CORRUPT (11), including extended codes | None observed. The same snapshot passes complete checks in successful runs, and the source file remains hash-bound to its manifest | **UNKNOWN**, no historical native code or bytes examined |
| Other SQLite errors | None observed in these failing measurements | **UNKNOWN** for the original traceback |

**CONFIRMED:** the reproduced native exception and failing operations; shared
budget consumption before SQLite; no MATCH in the failures; the dominant measured
normal time is before the backend; larger synthetic sources can exhaust the
same unchanged deadline. The complete 171-block path succeeds on this host when
adequate time remains. A timing failure is not itself evidence of database damage.

**LIKELY:** variation in available CPU / scheduling / live-projection costs pushes
the historical 171-block search over its deadline, after which SQLite's progress
handler interrupts validation. This reproduces the shape of the historical
wrapper, not its uniquely identified cause.

**UNKNOWN:** original native SQLite error and operation; original elapsed phase
budgets and CPU contention; whether a specific avoidable projection cost caused
that run; required capacity under the actual release environment. A single generic
Unavailable trace cannot distinguish those hypotheses.

## Correction decision

There is no demonstrated intrinsic SQLite/FTS integrity defect, faulty MATCH or
unnecessary validation step that can safely be removed. The reproduced deadline
failures under constrained compute are consistent with the existing fail-closed
resource contract. Changing their error label or testing just MATCH would not
correct the lost budget. A timeout increase, omitted checks, unchecked persistent
cache, blanket retries, or moving the deadline after live verification would not
be a minimal evidenced fix and is not proposed.

No product patch or product regression test is supplied. Three deterministic
**diagnostic** tests are supplied outside the repository test suite: using the
unchanged backend, a private backend-local monotonic clock is advanced when schema
integrity, record comparison, or FTS integrity starts. All three demand a genuine
SQLite OperationalError / SQLITE_INTERRUPT in `Unavailable.__context__` and the
unchanged redacted public error with suppressed display context. They use no
sleeps, increase no budget, and prove the mechanism rather than encode a speculative
fix. Existing tamper, projection, isolation and deadline tests remain active in
validation.

The next actionable investigation is a fresh synthetic run in the release test
environment with these same safe phase/code measurements and environment metadata.
Only then select and validate a specific optimization of the measured live path,
preserving all comparisons, current ACL checks, original artifacts and the same
end-to-end deadline. Successful runs here cannot replace that evidence.

## Validation

Results and exact commands are recorded in the companion evidence files. No full
515-test regression is run. No external integration opt-in is enabled.

| Check | Result | Exit |
| --- | --- | ---: |
| Initial instrumented lecture_171 case | 1 passed; 82.16 s | 0 |
| Targeted: test_content_fts.py + test_cs50_learning_mvp.py | 97 passed; 195.59 s | 0 |
| Then affected integration: test_content_retrieval_integration.py + test_cs50_summary_batch_stress.py | 12 passed (6 retrieval, 6 stress); 108.28 s | 0 |
| Final deterministic native-interrupt diagnostics | 3 passed; 0.96 s | 0 |
| Byte comparison of all tracked clone files to pristine commit archive | 1,155 identical; zero changed | 0 |
| Target worktree status, HEAD, diff | clean; specified commit; no diff | 0 |
| Tracked diff and whitespace check in isolated clone | clean; only this new report untracked | 0 |

The initial one-case stress run overlaps the later six-case stress validation and
is not added to the count of distinct repository tests. The 97 + 12 original
repository tests and the 3 standalone mechanism tests are different selections.
The target worktree was observed clean both before and after the work. No live
remote/PR state was queried under the no-network/no-PR-action boundary.

The first version of the standalone diagnostic test connector omitted the SQLite
version attribute needed by the backend metadata check: **1 passed, 2 failed,
exit 1**, 1.15 s. This was a diagnostic harness error, not a product regression.
Adding that attribute produces **3 passed, exit 0**, 1.10 s. Its log is retained
as `deterministic-connector-corrected.log`. A final rerun also limits the fixture
prevalidation to 2 seconds (rather than an unbounded independent validation);
its three tests pass as recorded in `deterministic.log`. The controlled-clock
cases themselves use the same unchanged deterministic deadline in both runs.
A cProfile sample is marked as profiling, not an acceptance test or phase benchmark.
The controlled and scaling failures above are intentional diagnostic observations;
their outer measurement runners exit 0 after recording failures, while the
669-block MVP itself exits 2. They are not counted as successful retrievals.

## Evidence and reproduction

All paths below are relative to `/tmp/pr174-fts-lv0bf9db`:

- `baseline/`: pristine tracked archive; `work/`: independent detached clone.
- `environment.json`: actual test interpreter, SQLite/dependency versions and CPU
  affinity metadata.
- `harness/fts_probe.py`, `run_pytest.py`, `replay.py`, `scale.py`,
  `backend_only.py`: local numeric and error-code instrumentation.
- `harness/test_deadline_diagnostic.py`: deterministic standalone mechanism tests.
- `offline/sitecustomize.py`: network guard used for acceptance validation.
- `baseline-lecture.{json,log}`: complete initial instrumented stress case.
- `replay-idle.{json,log}`, `replay-contention.{json,log}`: predefined normal and
  controlled-competition measurements.
- `scales/metrics.json`, `scale.log`: full-path scaling and per-phase records.
- `backend-only.json`: independent source-load/backend measurements.
- `replay.prof`, `profile-replay.json`, `profile.log`: auxiliary profiler evidence.
- `deterministic-first.log`, `deterministic-connector-corrected.log`,
  `deterministic.log`: diagnostic test development and
  final results, respectively.
- `targeted.{log,xml}`, `integration.{log,xml}`, `exitcodes.json`,
  `commands.json`, `verification.json`: validation and final preservation records.
- `report.patch`: documentation-only patch for later review; no product change.

Use the interpreter recorded in `environment.json`, `PYTHONDONTWRITEBYTECODE=1`,
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, and the isolated clone as working directory.
Set `PYTHONPATH` to `harness:work` for instrumented measurements or `offline:work`
for the uninstrumented tests. The replay and standalone mechanism tests use only
`test-baseline-lecture/test_long_source_run_cache_and0/new-private-mvp`; their
assertions reject a non-synthetic intent or a root outside this task's `/tmp`
directory. Refer to `commands.json` for complete arguments and output locations.
Fresh output/basetemp names are required for reruns so prior evidence is retained.
