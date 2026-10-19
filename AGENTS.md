# Agent Instructions

These instructions apply to the entire repository.

## Documentation and Branch Lifecycle

These rules apply to future Codex tasks. They authorize cleanup only of temporary
Git artifacts unambiguously created by the current task after verified integration.
They do not authorize cleanup of the existing branches or worktrees inventoried by
MAINT-01, MAINT-02 or MAINT-03; those still require individual approval.

### Durable documentation

Completion and validation reports, technical and architecture decisions, status
documents, inventories and comparable durable project records must be available in
the repository's actual default branch before final completion: `master` for
`rf-data/Personal_Assistant`, `main` for `rf-data/personal-assistant-ui`.

Documents may be authored in the task's worktree. Prefer the existing `docs/`
structure and integrate them through the regular PR/review process before removing
the task branch. Preserve relevant historical evidence, test results and decisions;
branch removal must not discard their only retained copy. Never overwrite documents
belonging to another active task. Temporary logs, caches, test outputs and disposable
task helpers need not be integrated.

### Task lifecycle

1. Use a task-specific branch and worktree when needed; identify every Git artifact
   created by this task separately from pre-existing or shared artifacts.
2. Implement and validate the changes and prepare the durable completion records.
3. Integrate the intended changes and documents into the actual default branch
   through its required PR/review process. Respect required reviews, permissions and
   any task-specific prohibition on merging; never bypass them.
4. Verify the actual local and live Git state: the intended commits and document
   contents are integrated, the corresponding PR is merged, and no intended work
   remains only on the task branch. A completed Codex run or an open PR is not proof
   of integration. Where squash integration changes commit IDs, verify the actual
   integrated changes and documents; do not assume commit or patch equivalence alone
   proves that all intended work was retained.
5. Before cleanup, check that the task worktree contains no uncommitted changes or
   valuable untracked/ignored data, all relevant data is secured, and no other task
   or process uses the worktree or branch. Unknown data or use blocks cleanup.
6. Only after all checks pass, remove exclusively this task's own temporary worktree
   and working branch, including its own temporary remote branch where applicable.
   Recheck exact identities and heads immediately before each action. Use ordinary
   Git operations without force; do not remove another branch merely because it
   points to the same commit.
7. Verify afterward that the actual default branch remains correct, the integrated
   documents are present, and only the approved task-owned Git artifacts disappeared.
   Report what was removed, retained or left pending and why.

A task is fully complete only when its own temporary Git artifacts have been safely
removed or a concrete reason for their necessary retention is documented. If the PR
is unmerged, retain its branch and worktree. If permissions, integration, ownership,
data safety or use are uncertain, retain the artifacts, document the blocker and
report the completion as pending; never claim successful cleanup.

### Safety boundaries

- Never remove primary checkouts, other tasks' artifacts, historical/shared branches
  or worktrees, dirty worktrees, or unknown untracked/ignored contents automatically.
- Preserve user data, virtual environments, persistent artifacts, databases, model
  files, secrets and stashes. Their removal requires a separate explicit instruction.
- No force-push, reset, blanket clean or prune; no forced worktree removal.
- Do not modify open draft PRs or protected active tasks as part of cleanup.
- This lifecycle authorization does not waive MAINT-01/02/03 individual approvals.
  A task-specific instruction to retain artifacts or prohibit deletion takes
  precedence over this general rule.
