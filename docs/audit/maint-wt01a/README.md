# MAINT-WT01A – Worktree Governance & Inventory

2026-11-11. Status: **implementation and inventory delivered; integration pending**.

No existing worktree, registration, ref, branch, archive or external project data was
changed by the inventory. No commit, push, merge or PR was performed. All records
remain `safe_to_remove=false` and `WORKTREE_LIFECYCLE_HOLD`.

## Scope and policy

The assigned worktree is `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-maint-wt01a`,
branch `maint/wt01a-inventory-governance`, unchanged HEAD
`c651e1d83c613de9bfb693380ac9856d72865121`.
The branch and worktree were already present at entry; this task created no new
working branch, remote branch or registered worktree. The assigned checkout and
its uncommitted deliverables must remain for review and later integration.

The parent AGENTS.md is adequate as normative governance and remains unchanged.
The [lifecycle guide](../../maintenance/worktree_lifecycle.md) records its assessment,
classification rules, commands, schema, reproducibility requirements and proposed
future workflow. Existing MAINT evidence and CS50 archives remain unchanged.
Inventory labels do not supersede MAINT-01/02/03 individual approval requirements.

## Inventory evidence and summary

Audit timestamp: `2026-11-11T09:56:37.850698+00:00`. Git `git version 2.39.5`.
Cached origin/master and the live GitHub master snapshot both identify
`c651e1d83c613de9bfb693380ac9856d72865121`. No fetch or tracking-ref update was performed.

| Classification | Worktrees |
| --- | ---: |
| ACTIVE | 55 |
| ARCHIVE | 7 |
| REMOVABLE_CANDIDATE | 41 |
| REVIEW | 7 |
| **Total** | **110** |

The prompt estimated approximately 109 worktrees; the actual registry contains 110.
There are **8 prunable registrations and 8 unavailable Git statuses**, 29 worktrees
with tracked changes, 26 with untracked files and 47 with ignored indicators.
These counts overlap. All 110 have unresolved human gates; none is approved for
removal. ACTIVE is a protective recommendation, not proof of a running process.

Approximate observed apparent bytes: **7,357,094,947**
(about 6.85 GiB), excluding Git storage. Eleven worktrees have incomplete or
unavailable disk metadata: eight unavailable Git identities/paths, plus the primary
checkout (four scan errors), c28-week-0-readiness (special files, nested repositories
and symlinks), and this assigned worktree (three device boundaries). This is a
lower bound on apparent size, not potential freed disk space.

Private generated evidence is retained locally under the ignored directory
`artifacts/maint-wt01a/`:

- `hosting-snapshot.json`: sanitized branch/PR snapshot.
- `initial-inventory/inventory.json` and `.csv`: initial observations, superseded
  after explicitly protecting master checkouts and adopting stdout-only commands.
- `final-audit/inventory.json` and `.csv`: earlier retained observations.
- `stdout-final-audit/inventory.json` and `.csv`: authoritative final observations
  summarized here, captured by the caller from the final stdout-only interface.
- `before.json`, `validation.json`: initial and final Git metadata preservation checks.
- `tests.log`, `independent-tests.log`: synthetic validation logs.

Acquisition used the connected GitHub plugin GET endpoint for
`rf-data/Personal_Assistant`: all-state PR pages of 100 and 45 records, and a
branch page of 59 records (each terminal page below 100). Thus the snapshot contains
145 PRs and 59 live branches, including 11 open draft PRs repository-wide.
Ten open PRs bind to registered worktrees: #72, #88, #89, #157, #158, #160, #161,
#162, #163 and #171. Snapshot completeness is supported by pagination to exhaustion;
no PR bodies, comments, titles, credentials or document contents were retained.
Hosting observation time: `2026-11-11T09:45:55.302Z`.
Snapshot SHA256: `de814e9d2a975d5ab2a447c9747705e18c0601d3c532ceee45bcf08da0b59663`.
Registry SHA256: `dbe0133f0c0c630b8a72ff4dcf05e2dcbf18936030347e0f45f452949fd89ff1`.
Ref-observation SHA256: `a1013caa5306e36702126f4e5b5e58647eb1a6cdfd0097a0df9bd1dde1bdaa13`.

## Risky and ambiguous cases

| Registered worktree basename | Classification | Main uncertainty |
| --- | --- | --- |
| `Personal_Assistant-c21q` | ACTIVE | Open draft PR #72; missing/inaccessible worktree |
| `Personal_Assistant-c22` | REVIEW | Missing/inaccessible Git identity; prunable is not disposal approval |
| `Personal_Assistant-c230` | REVIEW | Missing/inaccessible Git identity; prunable is not disposal approval |
| `Personal_Assistant-c2302a` | REVIEW | Missing/inaccessible Git identity; prunable is not disposal approval |
| `Personal_Assistant-c2302b` | REVIEW | Missing/inaccessible Git identity; prunable is not disposal approval |
| `Personal_Assistant-c24r` | ACTIVE | Commits outside baseline; missing/inaccessible worktree |
| `Personal_Assistant-completion-audit` | REVIEW | Missing/inaccessible Git identity; prunable is not disposal approval |
| `Personal_Assistant-dep01` | REVIEW | Missing/inaccessible Git identity; prunable is not disposal approval |
| `Personal_Assistant-cs50-m2a` | REVIEW | Four symlinks; targets and external artifact mapping unverified |

The seven ARCHIVE recommendations are c26-final-pilot, c26-stabilization,
c26-week0-acceptance, cs50-retrieval-mvp, cs50-summary-mvp, maint03b and maint04
(all have the `Personal_Assistant-` prefix). They have ignored-file indicators;
no ignored data was judged disposable and no archive was created or moved.

`Personal_Assistant` is the primary checkout on a feature branch and is protected.
`Personal_Assistant-master` is the separate persistent master checkout and is also
protected. Dirty/untracked/unique-commit/open-PR worktrees remain ACTIVE even if
other metadata is unavailable. Historical MAINT-02 protection must be reconciled
with its owner before acting on any machine candidate label.

External artifact roots were inspected using top-level metadata only:

- `/mnt/chromeos/GoogleDrive/MyDrive/1_Projekte_Datensätze/1_Projekte/00_GMP_Compliance`
  exists as a directory (mode 0750), with no symlink component observed.
- `/mnt/data` was not present.

Neither root was listed, read recursively, modified, moved or synchronized.
Availability does not prove backup completeness, integrity, retention or restoration.

## Proposed candidates for individual review

The 41 entries below passed the automatic observations at the audit timestamp.
The path prefix is **`/home/robfra/0_Portfolio_Projekte/`**; concatenate the exact
basename in the first column to obtain each absolute registered path.
All have zero observed tracked/untracked/ignored changes, complete bounded disk
metadata without observed symlinks/nested repositories, no matching open PR, and
HEAD ancestry retained in the live-verified origin/master baseline.
Owner/nonuse, historical document retention, external artifacts, environment and
independent restoration remain **not verified**. These are proposals for review,
not proposed immediate deletions. MAINT-01/02 require their existing individual
approval gates regardless of inclusion in this table.

| Exact basename under the prefix above | Branch or detached | Exact HEAD |
| --- | --- | --- |
| `Personal_Assistant-c2302c` | `feat/c23-02c-recovery-operations` | `f33df74ff09eb7d50223776080c6dd3048955a7c` |
| `Personal_Assistant-c2303` | `feat/c23-03-reimport-binding` | `42bbd8ae65110138bee82542ce02d99ec7d84be3` |
| `Personal_Assistant-c2304` | `feat/c23-04-content-read-api` | `ada2f185fd387312823f844fe99d9e9a54236e00` |
| `Personal_Assistant-c2305` | `feat/c23-05-txt-unknown-time` | `2e60d1529793bfb329a3648502cb26b589474c19` |
| `Personal_Assistant-c2306` | `feat/c23-06-real-material-evaluation` | `351646f0ffa545da7e3424e50ab78eb330e69542` |
| `Personal_Assistant-c2401` | `docs/c24-01-indexing-retrieval` | `b001388e2f05472cea2e1054c2713c6c434c9de9` |
| `Personal_Assistant-c2402` | `feat/c24-02-deterministic-index-projection` | `7d1b655cf6228b87edac922e59e4b5fc2c5b80cb` |
| `Personal_Assistant-c2403` | `feat/c24-03-sqlite-fts5` | `0f3d9dd1066eb771629159888fb5ee97c0a75ebf` |
| `Personal_Assistant-c2404` | `feat/c24-04-content-vector-adapter` | `12740b76a30d969b6c09d2be4ad1480a7dd8bdfd` |
| `Personal_Assistant-c2405a` | `feat/c24-05a-retrieval-evaluation` | `5a7d050685c381dffd0574aaff62f704c78e7350` |
| `Personal_Assistant-c2405b1` | `feat/c24-05b1-review-backend` | `20b8916900b201d8051e203327a7023e06c64914` |
| `Personal_Assistant-c2405c2` | `feat/c24-05c2-real-pilot` | `c8894abea7be1554a6f234f551ce92bc6e00bdc9` |
| `Personal_Assistant-c26-release-readiness` | `docs/c26-release-readiness` | `ad4e33b63389c2d5378dfcfd733e144f20f0af2e` |
| `Personal_Assistant-c26a` | `feat/c26a-existing-backend-copy-handoff` | `071a327091bfc66cd6ddb5f1541ca2f89e4b0889` |
| `Personal_Assistant-c26b` | `feat/c26b-https` | `c36417516cd027322388463c10a2391f7fcb225f` |
| `Personal_Assistant-c26b-vpn-final` | `detached` | `d0a58f392530bf4112ef7d7a632c1e5e36e07a20` |
| `Personal_Assistant-c26b1` | `feat/c26b1-worker-image-entrypoints` | `86ad27659212fe6b97d7589f8c5f0519cb84aef0` |
| `Personal_Assistant-c26b2` | `feat/c26b2-single-html-pilot` | `16601e7bbffe8ecc9fb2e9c1a13b454df0281e65` |
| `Personal_Assistant-c26b3` | `feat/c26b3-admin-bootstrap` | `505bea92086746242e357675e43e51d285d41ed0` |
| `Personal_Assistant-c26b4` | `feat/c26b4-week0-batch-pilot` | `05d46133eefcb1d7da37e2867b4e8cc30cb7633c` |
| `Personal_Assistant-c26b5` | `feat/c26b5-multiformat-transcripts` | `81897b7c06d23841f4edbbb3e91df3854221deb2` |
| `Personal_Assistant-c26b5-fix01` | `fix/c26b5-knowledge-identities` | `78a51a9312aafb0483abaf7f97f379ebcf96a315` |
| `Personal_Assistant-c26b6-planning` | `feat/c26b6-course-planning` | `5d4c12bb3ea3acb69bf737e1466acfb12f5830bb` |
| `Personal_Assistant-c26b6-readiness` | `docs/c26b6-rollout-readiness` | `0bb9a5b89e9ab691d1614c0d07590aa53e08c75c` |
| `Personal_Assistant-c26b6-review` | `feat/c26b6-code-zip-reviewed` | `ef0aa1cf59874b6ac461adf2008bad5d0eaf63e8` |
| `Personal_Assistant-c26b7-review` | `feat/c26b7-media-last-reviewed` | `cba3302261be5b5cb0a36fc482250a5268b8ad44` |
| `Personal_Assistant-c27-cs50-server-readiness` | `review/c27-cs50-server-readiness` | `a8af1d9372eb435d3e1331c33b047d21120d57c2` |
| `Personal_Assistant-dev01a` | `feat/dev01a-authorized-search` | `b1c3c9cc292d4abab210a3316952878827cc57f0` |
| `Personal_Assistant-dev01b` | `feat/dev01b-controlled-index-jobs` | `c07ed9a17c703df17a44dfac075603fdbe108907` |
| `Personal_Assistant-dev02b` | `feat/dev02b-controlled-import` | `2af5cec1d8b51b43827dd16f147c57d829d50789` |
| `Personal_Assistant-dev03b` | `feat/dev03b-parsing-evaluation` | `4f12bb7e190c690d08083232db9b29025c70708a` |
| `Personal_Assistant-dev03c` | `feat/dev03c-retrieval-evaluation` | `edf6f05fdc24a33297ce445a54e1a804cb8b0796` |
| `Personal_Assistant-dev03d` | `feat/dev03d-exam-inventory` | `419b9c2ff9572ea7bbe15bb68c5d053dc206fd3d` |
| `Personal_Assistant-dev03e` | `feat/dev03e-local-evaluation` | `08218c0800a47f10fbb260d1d42edb9a2e4a37c4` |
| `Personal_Assistant-dev03e-course` | `feat/dev03e-content-course` | `d6f16d0547b3e2139235a8b1bbfaac17d747e353` |
| `Personal_Assistant-dev03f` | `feat/dev03f-human-review` | `fa8a8830efc12ab54bef9448bcd8c0d985442c8b` |
| `Personal_Assistant-maint01` | `docs/maint01-inventory-consolidation` | `568d3835c880f616a1535458b36779f2b4276038` |
| `Personal_Assistant-maint02` | `docs/maint02-cleanup-verification` | `0308217d2213b7a2d6e39b731ec22f640b8a4a3d` |
| `Personal_Assistant-pm01` | `docs/pm01-project-consolidation` | `e06a29c47310d347af26b7a8c61e574d0cef172a` |
| `Personal_Assistant-pm02` | `docs/pm02-project-operationalization` | `024cab7893701a6cf52c85975682c76869dc2f5e` |
| `Personal_Assistant_C23_Test` | `detached` | `d654f0580f6c5d6aa5698f33dc5c93dec5ba66d5` |

For an initial MAINT-WT01B review sample, prefer c2302c, c2303 and c2304 after
confirming ownership; their exact identities are in the table. Keep MAINT-01/02
and all protected tasks outside that initial sample. A small sample tests the
preservation and restoration procedure without implying approval of the other 38.

## Validation and preservation

`python3 -m unittest tests.test_worktree_manager -v` passes **31 synthetic tests**.
They check metadata preservation for both operations, default/primary protection,
missing worktrees, ignored and private data, unique commits, draft/fork PRs, stale
and malformed hosting data, disabled filters/fsmonitor, unusual/non-UTF8 paths,
bounded scans, error sanitization, CSV and stdout format preservation.
No new dependency was installed. Python 3.11.2 and Git 2.39.5 were available;
the application environment was not required. No full application-suite validation
is claimed for this isolated standard-library tool.

An additional `tests/test_worktree_manager_independent.py` appeared untracked
during this task. Its synthetic-only source was inspected and its 10 tests passed.
Its origin/ownership is unverified; it remains untouched, is not counted among the
31 authored tests and is excluded from the task handoff patch. The separately
appearing `docs/maintenance/maint_wt01a_independent_review.md`, its private evidence
under `artifacts/handoff/maint-wt01a/`, and a concurrent additional .gitignore hunk
are also retained unchanged and excluded from the authored patch. That independent
review uses a deliberately partial hosting snapshot and frozen earlier source; its
different historical classifications do not supersede the complete-snapshot audit
reported here. Concurrent source ownership must be reconciled at integration.

The final checks confirm unchanged registry bytes, ref IDs, stash IDs, index digests and
parent-policy digest against `before.json`; exact results are retained in
`validation.json`. No changes to other worktrees are intended or authorized. The final audit exited 2
for the 110 expected lifecycle holds. Both operations now emit only stdout; JSON/CSV
report files were created by explicit exclusive caller capture, not by the tool.
`git status` and `git diff --check` are checked at handoff. A patch containing
only the authored files is retained at `artifacts/handoff/maint-wt01a.patch` and
verified by applying it to an isolated synthetic checkout and comparing bytes.

## Recommended MAINT-WT01B scope

1. Reinventory and obtain owners/expected lifecycle for active and historical tasks.
   Reconcile the 110 registrations with the target of one persistent master and
   at most four active feature/review worktrees; do not infer nonuse from a label.
2. Investigate the eight prunable/inaccessible registrations as recovery cases,
   keeping draft #72 and unique history protected. Review symlinks, nested repos,
   mounts and permission boundaries without following or changing external data.
3. For a small exact-path sample, map ignored/untracked and external artifacts,
   document dependency/environment recipes, historical document retention and
   actual default-branch integration. Design per-path integrity/restore manifests.
4. Prepare concrete archive/restore and subsequent removal decision records.
   Any archive writes, restoration exercise or eventual removal needs the proper
   separate authorization; no removal capability should be enabled by classification
   alone. MAINT-WT01B should begin with review/preparation, not bulk cleanup.

Integration of this code and durable documentation into actual `master` is pending
because this task expressly prohibits commits, pushes, merges and PR creation.
No new commit SHA exists. The initial HEAD above remains unchanged; `.gitignore`,
the new manager, its authored tests and both WT01A documents remain uncommitted.
The assigned branch/worktree and all evidence are retained. No cleanup was
performed, no branch was deleted and no claim of default-branch integration is made.
