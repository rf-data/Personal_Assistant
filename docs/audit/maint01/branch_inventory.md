# A. MAINT-01 – Branch Inventory

19.10.2026, Europe/Berlin. **Read-only-Aufnahme vor Anlage des eigenen MAINT-Branches
und -PRs.** Keine Branch-/Worktree-/Dateilöschung, kein Pruning/Reset/Clean,
kein Schließen/Mergen/Rebase eines PRs. [Dokumente](document_inventory.md),
[Cleanup Proposal](cleanup_proposal.md), [vollständige Branchdaten](branches.tsv),
[Worktrees](worktrees.tsv), [gecachte Trackingrefs](cached_tracking_refs.tsv).

## Repositoryidentität und Zählgrenzen

| Repo | Primärcheckout | Tatsächliches GitHub-origin | Default | Live-Default-SHA | Lokale Branches | Live-Branches | Worktrees registriert / gültig |
| --- | --- | --- | --- | --- | --- | --- | --- |
| backend | $WORKSPACE/gmp_compliance | rf-data/Personal_Assistant | master | 4c057ae33d41ba98e227879cc8a51283338e4a0b | 104 | 32 | 36 / 26 |
| ui | $WORKSPACE/personal-assistant-ui | rf-data/personal-assistant-ui | main | 90816a1578bcf67739ee9acaa483c1635aa0c44b | 8 | 1 | 8 / 8 |


`$WORKSPACE` bezeichnet den vom Auftraggeber bereitgestellten Arbeitswurzelpfad;
`$TMP` ausschließlich zuvor registrierte temporäre Worktrees. Es gibt kein lokales
Verzeichnis mit dem exakten Namen `Personal_Assistant`. Die vorhandenen Backend-
Featureworktrees zeigen auf `gmp_compliance/.git`; UIworktrees auf
`personal-assistant-ui/.git`. Identität folgt Remote-URL/Common-Gitdir/Commitgraph,
nicht dem Ordnernamen. Beide Repositories sind nicht shallow und getrennte
Historien; sie werden nicht zusammengeführt. Primäre Checkouts bleiben erhalten.
Die vollständigen (nicht shallow) Defaultgraphen haben getrennte Rootcommits: Backend
`986da32ca2a0675702a29a673958189731fef2ad`, UI `dfda714d9835e4a018abcdcca8cdaf909178f2d9`.

Die Remotes verwenden `https://github.com/rf-data/Personal_Assistant.git` bzw.
`https://github.com/rf-data/personal-assistant-ui.git`, jeweils Fetch und Push.
`git rev-parse --show-toplevel`, `--git-common-dir`, `git remote -v`, `git branch -vv`,
`git worktree list --porcelain`, `git status --short`/Porcelain, `git log`,
`git merge-base`, `rev-list`, `cherry` und Baumvergleiche liefern die Tabellen.
`GIT_OPTIONAL_LOCKS=0` verhindert Status-Refreshschreibzugriffe auf Quellindices.
Keine Env-/Gitcredential-Inhalte gelesen. Die bekannten Rooteinstellungen aus
`.codex/AGENTS.md` bestätigen gmp_compliance und personal-assistant-ui als Primärcheckouts.

GitHub-REST: Branchlisten jeweils mit `per_page=100`, Backend 32/UI 1; PR-Listen
90/7 Einträge, jeweils weniger als eine Seite. Alle 33 Live-Branchheads sind als
Commitobjekte lokal vorhanden; kein Fetch/Prune/Trackingupdate für die Inventur nötig.
`origin/master` ist lokal noch `d654f05`, live `4c057ae`; UI `origin/main`/Primärmain
noch `b2cf9ca`, live `90816a1`. Zwölf gecachte Trackingrefs fehlen im Live-Snapshot,
zwei weichen ab, 30 stimmen. Diese 44 gecachten Refs sind **keine 44 Live-Branches**.
Backend `origin/HEAD` fehlt; UI `origin/HEAD` ist nur der alte symbolische Verweis.

112 lokale Branches + 33 Live-Branches ergeben **145 Tabellenzeilen**, keine
145 unterschiedlichen Branchidentitäten. 44 registrierte Worktrees: 34 gültig,
zehn ungültig/prunable, davon zwei Restverzeichnisse noch vorhanden. In diesen
beiden Roots keine geeigneten Dokumente gefunden; ausgeschlossene Cache-/Venv-
Unterbäume bleiben ununtersucht. Ein neuer eigener MAINT-Branch/Worktree erhöht
die lokalen Zahlen anschließend auf 113/45; der eigene Remote-Branch erhöht Live
auf 34. Diese Deltas sind keine Bereinigung der Aufnahme.

## Klassifikation und Nachweisgrenzen

| Kategorie | Zeilen lokal + remote | Bedeutung |
| --- | --- | --- |
| active | 7 | Defaultbranch oder ausdrücklich laufender C24-06-A-/PM-01-Auftrag |
| merged_clean | 51 | Head ist Vorfahr des Live-Defaults und passender gemergter PR vorhanden |
| merged_with_extra_commits | 41 | PR des Branchnamens gemergt, dieser konkrete Head besitzt graph-eigene Commits |
| open_pr | 14 | Offener PR, einschließlich alter Nicht-Drafts; nicht allein nach Alter verwerfen |
| unmerged_unique_work | 24 | Graph-eigene Commits ohne passenden gemergten PR-Beleg; Aufbewahrung nötig |
| stale_candidate | 8 | Graph vollständig im Default, kein passender gemergter PR; nur Prüf-/Löschkandidat |
| unknown | 0 | Kein belastbarer gemeinsamer Git-Nachweis; in dieser Aufnahme keine Branchzeile |


**Wichtiger Unterschied:** 33 der 41 `merged_with_extra_commits`-Zeilen haben
exakt denselben Tree wie der zugehörige gemergte PR-Head. Graph-eigene Commit-IDs
sind damit kein Beleg neuer Inhalte oder späterer Änderungen. `git cherry`
zeichnet Patchäquivalenz zusätzlich auf; Treegleichheit ist ein anderer Nachweis.
Die acht übrigen lokalen Zeilen sind nicht treegleich. Alle behalten ihre Kategorie
konservativ, eigene Commitlisten und Sicherungs-/Prüfbedarf. Keine automatische
Löschung aufgrund von PR-Merge, Patch- oder Treegleichheit.

`files_absent_from_default` bedeutet nur „Pfad im Branch, im heutigen Default
nicht vorhanden“; er kann absichtlich historisch entfernt worden sein.
`branch_changes_since_merge_base` erfasst tatsächliche Branchänderungen; ein
Vergleich eines alten Branches zum heutigen Default wäre allein irreführend.
Vollständige SHA/Commitdatum/-titel, lokale/live SHA, PR-Head/Mergesha/-datum,
Mergebase, Ahead/Behind, graph-eigene Commits, Patch-/Treebelege und exklusive
Dateipfade stehen pro Zeile in [branches.tsv](branches.tsv).

## Vollständige Branchübersicht

| Repo / Scope | Branch | Head | Kategorie | Ahead / Behind | Offene / gemergte PRs | Worktrees |
| --- | --- | --- | --- | --- | --- | --- |
| backend / local | `add_audio_transcript` | `b3b59b66942e` | stale_candidate | 0 / 159 |  /  | – |
| backend / local | `archive/cs50-2026-10/20574a01a7ca` | `20574a01a7ca` | unmerged_unique_work | 1 / 128 |  /  | – |
| backend / local | `archive/cs50-2026-10/9dbf90341647` | `9dbf90341647` | unmerged_unique_work | 5 / 134 |  /  | – |
| backend / local | `archive/cs50-2026-10/c74c8b72fc83` | `c74c8b72fc83` | unmerged_unique_work | 9 / 134 |  /  | – |
| backend / local | `archive/cs50-2026-10/cdf3f711607b` | `cdf3f711607b` | unmerged_unique_work | 1 / 123 |  /  | – |
| backend / local | `audit/post-merge-fixtures` | `90ce44f39d55` | merged_with_extra_commits | 2 / 128 |  / #21 | – |
| backend / local | `docs/c170-repository-consolidation` | `0cee49607e6f` | unmerged_unique_work | 2 / 45 |  /  | – |
| backend / local | `docs/c170-repository-consolidation-public` | `031d18ef35fb` | merged_with_extra_commits | 1 / 44 |  / #68 | – |
| backend / local | `docs/c230-roadmap-planning` | `7f9fddf6d75f` | merged_clean | 0 / 33 |  / #74 | $WORKSPACE/Personal_Assistant-c230 |
| backend / local | `docs/c24-01-indexing-retrieval` | `b001388e2f05` | merged_clean | 0 / 14 |  / #83 | $WORKSPACE/Personal_Assistant-c2401 |
| backend / local | `docs/cs50-archive` | `8ba519ed04c0` | stale_candidate | 0 / 92 |  /  | – |
| backend / local | `docs/cs50-completion-audit` | `571874524b8b` | stale_candidate | 0 / 116 |  /  | $WORKSPACE/Personal_Assistant-completion-audit |
| backend / local | `docs/cs50-documentation` | `a088213b099c` | merged_with_extra_commits | 2 / 92 |  / #38 | – |
| backend / local | `docs/cs50-final-archive` | `5cc8f9f00703` | unmerged_unique_work | 1 / 100 |  /  | – |
| backend / local | `docs/cs50-material-completion` | `450016eb37a5` | unmerged_unique_work | 11 / 78 |  /  | $WORKSPACE/Personal_Assistant-materials |
| backend / local | `docs/pm01-project-consolidation` | `e06a29c47310` | active | 1 / 0 | #92 /  | $WORKSPACE/Personal_Assistant-pm01 |
| backend / local | `docs/project-consolidation-public-2026-10-15` | `1af7179c3ba4` | merged_with_extra_commits | 1 / 78 |  / #47 | – |
| backend / local | `feat/c10-material-quality` | `2aaacda613be` | merged_with_extra_commits | 1 / 59 |  / #61 | – |
| backend / local | `feat/c11-formula-evaluation` | `467ec82d8ee4` | merged_clean | 0 / 56 |  / #62 | – |
| backend / local | `feat/c12-consolidation-hardening` | `42414387319b` | merged_clean | 0 / 56 |  / #63 | – |
| backend / local | `feat/c13-visual-inventory` | `9dd9c8ad6aaa` | merged_clean | 0 / 56 |  / #64 | – |
| backend / local | `feat/c15-monitoring-hardening` | `e74d3405b716` | merged_clean | 0 / 50 |  / #65 | $WORKSPACE/Personal_Assistant-c15 |
| backend / local | `feat/c16-job-control` | `74578357afe0` | merged_clean | 0 / 48 |  / #66 | $WORKSPACE/Personal_Assistant-c16 |
| backend / local | `feat/c18-offline-workflows` | `d2c07f9b4e9f` | merged_clean | 0 / 46 |  / #67 | $WORKSPACE/Personal_Assistant-c18 |
| backend / local | `feat/c19-pdf-worker-lifecycle` | `b36f72d9a147` | merged_clean | 0 / 42 |  / #69 | – |
| backend / local | `feat/c20b-workflow-http` | `65b3f0915526` | merged_clean | 0 / 40 |  / #70 | $WORKSPACE/gmp_compliance |
| backend / local | `feat/c21-system-acceptance` | `d85bf060c5cc` | merged_clean | 0 / 37 |  / #71 | – |
| backend / local | `feat/c21q-qdrant-transcript-pilot` | `3a42b1675dff` | open_pr | 2 / 36 | #72 /  | $WORKSPACE/Personal_Assistant-c21q |
| backend / local | `feat/c22-operations-readiness` | `f2842788efd4` | merged_clean | 0 / 35 |  / #73 | $WORKSPACE/Personal_Assistant-c22 |
| backend / local | `feat/c23-01-parsed-content-adr` | `50699d331a76` | merged_clean | 0 / 31 |  / #75 | $WORKSPACE/Personal_Assistant-c2301 |
| backend / local | `feat/c23-02a-content-store` | `df41af0b5f36` | merged_clean | 0 / 29 |  / #76 | $WORKSPACE/Personal_Assistant-c2302a |
| backend / local | `feat/c23-02b-content-adapters` | `ba2dcd4a0a74` | merged_clean | 0 / 27 |  / #77 | $WORKSPACE/Personal_Assistant-c2302b |
| backend / local | `feat/c23-02c-recovery-operations` | `f33df74ff09e` | merged_clean | 0 / 25 |  / #78 | $WORKSPACE/Personal_Assistant-c2302c |
| backend / local | `feat/c23-03-reimport-binding` | `42bbd8ae6511` | merged_clean | 0 / 23 |  / #79 | $WORKSPACE/Personal_Assistant-c2303 |
| backend / local | `feat/c23-04-content-read-api` | `ada2f185fd38` | merged_clean | 0 / 23 |  / #80 | $WORKSPACE/Personal_Assistant-c2304 |
| backend / local | `feat/c23-05-txt-unknown-time` | `2e60d1529793` | merged_clean | 0 / 18 |  / #81 | $WORKSPACE/Personal_Assistant-c2305 |
| backend / local | `feat/c23-06-real-material-evaluation` | `351646f0ffa5` | merged_clean | 0 / 16 |  / #82 | $WORKSPACE/Personal_Assistant-c2306 |
| backend / local | `feat/c24-02-deterministic-index-projection` | `7d1b655cf622` | merged_clean | 0 / 12 |  / #84 | $WORKSPACE/Personal_Assistant-c2402 |
| backend / local | `feat/c24-03-sqlite-fts5` | `0f3d9dd1066e` | merged_clean | 0 / 10 |  / #85 | $WORKSPACE/Personal_Assistant-c2403 |
| backend / local | `feat/c24-04-content-vector-adapter` | `12740b76a30d` | merged_clean | 0 / 7 |  / #86 | $WORKSPACE/Personal_Assistant-c2404 |
| backend / local | `feat/c24-05a-retrieval-evaluation` | `5a7d050685c3` | merged_clean | 0 / 5 |  / #87 | $WORKSPACE/Personal_Assistant-c2405a |
| backend / local | `feat/c24-05b-human-review-workflow` | `f3fae9ef6d2c` | open_pr | 1 / 6 | #88 /  | $WORKSPACE/Personal_Assistant-c2405b |
| backend / local | `feat/c24-05b1-review-backend` | `20b8916900b2` | merged_clean | 0 / 3 |  / #90 | $WORKSPACE/Personal_Assistant-c2405b1 |
| backend / local | `feat/c24-05c-real-corpus-pilot` | `a3d253a27c4f` | open_pr | 2 / 4 | #89 /  | $WORKSPACE/Personal_Assistant-c2405c |
| backend / local | `feat/c24-05c2-real-pilot` | `c8894abea7be` | merged_clean | 0 / 1 |  / #91 | $WORKSPACE/Personal_Assistant-c2405c2 |
| backend / local | `feat/c24-06a-local-review` | `4c057ae33d41` | active | 0 / 0 |  /  | $WORKSPACE/Personal_Assistant-c2406a |
| backend / local | `feat/cs50-course-reporting` | `70cbf4df5faa` | merged_with_extra_commits | 8 / 114 |  / #34 | – |
| backend / local | `feat/cs50-course-scheduler` | `3c21a02d1f3c` | merged_with_extra_commits | 7 / 114 |  / #33 | – |
| backend / local | `feat/cs50-discovery-contracts` | `8ed80f3b2dff` | open_pr | 1 / 134 | #6 /  | – |
| backend / local | `feat/cs50-durable-budget` | `c1facec470de` | merged_with_extra_commits | 1 / 114 |  / #27 | – |
| backend / local | `feat/cs50-full-coverage` | `e2bb1f2fc939` | unmerged_unique_work | 4 / 134 |  /  | – |
| backend / local | `feat/cs50-index-cli` | `5f8c557f664e` | merged_with_extra_commits | 6 / 88 |  / #43 | – |
| backend / local | `feat/cs50-knowledge-checkpoints` | `809988be888a` | merged_with_extra_commits | 1 / 116 |  / #26 | – |
| backend / local | `feat/cs50-knowledge-index-mapping` | `38fafd341d5d` | merged_with_extra_commits | 8 / 88 |  / #45 | – |
| backend / local | `feat/cs50-lecture-completion` | `654a3a1ef57f` | merged_with_extra_commits | 6 / 114 |  / #32 | – |
| backend / local | `feat/cs50-lecture-runner` | `838c4c0b2812` | merged_with_extra_commits | 5 / 114 |  / #31 | – |
| backend / local | `feat/cs50-material-code` | `ad734de196d6` | unmerged_unique_work | 6 / 78 |  /  | – |
| backend / local | `feat/cs50-material-contracts` | `8b1f5eb3ce35` | unmerged_unique_work | 2 / 78 |  /  | – |
| backend / local | `feat/cs50-material-download` | `21262d9a486c` | unmerged_unique_work | 3 / 78 |  /  | – |
| backend / local | `feat/cs50-material-html` | `edd917d08adf` | unmerged_unique_work | 4 / 78 |  /  | – |
| backend / local | `feat/cs50-material-inventory` | `fe781d314655` | unmerged_unique_work | 1 / 78 |  /  | – |
| backend / local | `feat/cs50-material-mapping` | `932793c9ec78` | unmerged_unique_work | 8 / 78 |  /  | – |
| backend / local | `feat/cs50-material-pdf` | `78676ea70ab4` | unmerged_unique_work | 5 / 78 |  /  | – |
| backend / local | `feat/cs50-material-processing` | `4536c0388f37` | unmerged_unique_work | 7 / 78 |  /  | – |
| backend / local | `feat/cs50-materials-01-inventory` | `58b3a3462c40` | merged_with_extra_commits | 1 / 78 |  / #48 | – |
| backend / local | `feat/cs50-materials-02-contracts` | `36eb44d56f27` | merged_with_extra_commits | 2 / 78 |  / #49 | – |
| backend / local | `feat/cs50-materials-03-download` | `20fb62bf9e72` | merged_with_extra_commits | 3 / 78 |  / #50 | – |
| backend / local | `feat/cs50-materials-04-html` | `c49fe81e80e7` | merged_with_extra_commits | 4 / 78 |  / #51 | – |
| backend / local | `feat/cs50-materials-05-pdf` | `6de2c954cde9` | merged_with_extra_commits | 5 / 78 |  / #52 | – |
| backend / local | `feat/cs50-materials-06-code` | `7ac05baf2087` | merged_with_extra_commits | 6 / 78 |  / #53 | – |
| backend / local | `feat/cs50-materials-07-processing` | `ac559eb942c5` | merged_with_extra_commits | 7 / 78 |  / #54 | – |
| backend / local | `feat/cs50-materials-08-mapping` | `05047e5f091c` | merged_with_extra_commits | 8 / 78 |  / #55 | – |
| backend / local | `feat/cs50-materials-09-e2e` | `62e0f9f6ad29` | merged_with_extra_commits | 9 / 78 |  / #56 | – |
| backend / local | `feat/cs50-offline-extraction` | `40d441e11c16` | merged_with_extra_commits | 2 / 134 |  / #7 | – |
| backend / local | `feat/cs50-portable-inputs` | `b1696a37d7df` | merged_with_extra_commits | 2 / 114 |  / #28 | – |
| backend / local | `feat/cs50-quality-evaluation-contract` | `e22171583f14` | merged_with_extra_commits | 10 / 114 |  / #36 | – |
| backend / local | `feat/cs50-selection-preview` | `fa3dcd4c9d0d` | merged_with_extra_commits | 3 / 134 |  / #8 | – |
| backend / local | `feat/cs50-six-course-batch` | `33d11e6bdff3` | merged_with_extra_commits | 9 / 114 |  / #35 | – |
| backend / local | `feat/cs50-timed-knowledge` | `e2bb1f2fc939` | merged_with_extra_commits | 4 / 134 |  / #14 | – |
| backend / local | `feat/cs50-transcript-embeddings` | `31f28346d028` | merged_with_extra_commits | 3 / 88 |  / #40 | – |
| backend / local | `feat/cs50-transcript-index-contract` | `471890facd93` | merged_with_extra_commits | 1 / 88 |  / #39 | – |
| backend / local | `feat/cs50-transcript-ingestion` | `e0467a341690` | merged_with_extra_commits | 4 / 88 |  / #41 | – |
| backend / local | `feat/cs50-transcript-retrieval` | `f83abeeb4839` | merged_with_extra_commits | 5 / 88 |  / #42 | – |
| backend / local | `feat/knowledge-transcript-provenance` | `b1933e6ad8f6` | merged_with_extra_commits | 2 / 134 |  / #12 | – |
| backend / local | `feat/official-transcript-import` | `1ba121fdada0` | open_pr | 1 / 134 | #9 /  | – |
| backend / local | `fix/cs50-html-semantics` | `9e7fda602b00` | unmerged_unique_work | 1 / 64 |  /  | $WORKSPACE/Personal_Assistant-html-parser |
| backend / local | `fix/cs50-pdf-v2` | `ddc0ea43f42f` | unmerged_unique_work | 1 / 61 |  /  | $WORKSPACE/Personal_Assistant-pdf-v2 |
| backend / local | `fix/cs50-quality-synthetic-boundaries` | `b4d4ca4e3aa2` | merged_with_extra_commits | 1 / 123 |  / #23 | – |
| backend / local | `fix/knowledge-metadata-forwarding` | `a6d34208859f` | merged_with_extra_commits | 3 / 114 |  / #29 | – |
| backend / local | `fix/knowledge-source-id` | `e46c3f0430d2` | open_pr | 1 / 134 | #10 /  | – |
| backend / local | `fix/knowledge-transcript-metadata-contract` | `dde15bf4434c` | merged_with_extra_commits | 1 / 118 |  / #25 | $WORKSPACE/Personal_Assistant-provenance-models |
| backend / local | `fix/lazy-marvin-import` | `ee309bc9ddf8` | merged_with_extra_commits | 3 / 134 |  / #13 | – |
| backend / local | `fix/math-normalization-import` | `65ba14fda025` | open_pr | 1 / 134 | #11 /  | – |
| backend / local | `fix/optional-knowledge-sdk-imports` | `4315896cfc63` | merged_with_extra_commits | 1 / 120 |  / #24 | – |
| backend / local | `master` | `c1007efdbac3` | active | 0 / 43 |  / #4 | – |
| backend / local | `offline_add` | `c5454badf0cd` | merged_clean | 0 / 155 |  / #5, #3, #2 | – |
| backend / local | `private/project-consolidation-2026-10-15` | `49c19feccfe8` | unmerged_unique_work | 3 / 78 |  /  | – |
| backend / local | `recover-offline-add` | `978472d6528f` | merged_clean | 0 / 187 |  / #1 | – |
| backend / local | `review/cs50-complete` | `a6b49d9eed1d` | stale_candidate | 0 / 103 |  /  | $WORKSPACE/Personal_Assistant-completion |
| backend / local | `test/cs50-completion-integration` | `0bc649c75aa1` | merged_with_extra_commits | 11 / 114 |  / #37 | – |
| backend / local | `test/cs50-index-end-to-end` | `58803e1e8082` | merged_with_extra_commits | 7 / 88 |  / #44 | – |
| backend / local | `test/cs50-material-e2e` | `c2e31dd447c8` | unmerged_unique_work | 9 / 78 |  /  | – |
| backend / local | `test/cs50-worker-profiles` | `4dd8cfcaa1b1` | merged_with_extra_commits | 4 / 114 |  / #30 | – |
| backend / local | `test/portable-cs50-pilot-regression` | `13d435751b7b` | merged_clean | 0 / 123 |  / #22 | – |
| backend / remote | `add_audio_transcript` | `b3b59b66942e` | stale_candidate | 0 / 159 |  /  | – |
| backend / remote | `add_knowledge_db` | `a48f34295db1` | unmerged_unique_work | 1 / 159 |  /  | – |
| backend / remote | `add_local_LLM` | `b3b59b66942e` | stale_candidate | 0 / 159 |  /  | – |
| backend / remote | `add_organizer` | `b3b59b66942e` | stale_candidate | 0 / 159 |  /  | – |
| backend / remote | `add_runpod` | `d35c43fb698a` | stale_candidate | 0 / 177 |  /  | – |
| backend / remote | `codespace-opulent-barnacle-x5p7wpgwp6w6f57w` | `19dc080adac7` | unmerged_unique_work | 1 / 159 |  /  | – |
| backend / remote | `docs/pm01-project-consolidation` | `e06a29c47310` | active | 1 / 0 | #92 /  | $WORKSPACE/Personal_Assistant-pm01 |
| backend / remote | `feat/c21q-qdrant-transcript-pilot` | `3a42b1675dff` | open_pr | 2 / 36 | #72 /  | $WORKSPACE/Personal_Assistant-c21q |
| backend / remote | `feat/c24-05b-human-review-workflow` | `f3fae9ef6d2c` | open_pr | 1 / 6 | #88 /  | $WORKSPACE/Personal_Assistant-c2405b |
| backend / remote | `feat/c24-05c-real-corpus-pilot` | `a3d253a27c4f` | open_pr | 2 / 4 | #89 /  | $WORKSPACE/Personal_Assistant-c2405c |
| backend / remote | `feat/cs50-discovery-contracts` | `7ba2dd844d24` | open_pr | 5 / 134 | #6 /  | – |
| backend / remote | `feat/cs50-full-coverage` | `644917c0733b` | unmerged_unique_work | 14 / 134 |  /  | – |
| backend / remote | `feat/cs50-index-cli` | `5d87b7f4e907` | merged_clean | 0 / 81 |  / #43 | – |
| backend / remote | `feat/cs50-materials-01-inventory` | `09704df1a0d2` | merged_clean | 0 / 77 |  / #48 | – |
| backend / remote | `feat/cs50-materials-02-contracts` | `1a082c5a1740` | merged_clean | 0 / 76 |  / #49 | – |
| backend / remote | `feat/cs50-materials-03-download` | `ff20431721c4` | merged_clean | 0 / 75 |  / #50 | – |
| backend / remote | `feat/cs50-materials-04-html` | `4960609472cf` | merged_clean | 0 / 74 |  / #51 | – |
| backend / remote | `feat/cs50-materials-05-pdf` | `6a2ffe1ae378` | merged_clean | 0 / 73 |  / #52 | – |
| backend / remote | `feat/cs50-materials-06-code` | `e50e85261ffb` | merged_clean | 0 / 72 |  / #53 | – |
| backend / remote | `feat/cs50-materials-07-processing` | `7d6120bbef90` | merged_clean | 0 / 71 |  / #54 | – |
| backend / remote | `feat/cs50-materials-08-mapping` | `a96aee141ae5` | merged_clean | 0 / 70 |  / #55 | – |
| backend / remote | `feat/cs50-materials-09-e2e` | `8a04b0b16c5b` | merged_clean | 0 / 69 |  / #56 | – |
| backend / remote | `feat/cs50-transcript-embeddings` | `69d00cf0e7a8` | merged_clean | 0 / 86 |  / #40 | – |
| backend / remote | `feat/cs50-transcript-ingestion` | `acae6d1bb8e1` | merged_clean | 0 / 83 |  / #41 | – |
| backend / remote | `feat/cs50-transcript-retrieval` | `6f94eaff1717` | merged_clean | 0 / 82 |  / #42 | – |
| backend / remote | `feat/official-transcript-import` | `3d1317347018` | open_pr | 1 / 134 | #9 /  | – |
| backend / remote | `fix/knowledge-source-id` | `9ed643dedf22` | open_pr | 5 / 134 | #10 /  | – |
| backend / remote | `fix/math-normalization-import` | `efed68d08ddb` | open_pr | 1 / 134 | #11 /  | – |
| backend / remote | `improve_wiki_extract` | `19dc080adac7` | unmerged_unique_work | 1 / 159 |  /  | – |
| backend / remote | `master` | `4c057ae33d41` | active | 0 / 0 |  / #4 | – |
| backend / remote | `offline_add` | `c5454badf0cd` | merged_clean | 0 / 155 |  / #5, #3, #2 | – |
| backend / remote | `test/cs50-index-end-to-end` | `3727b94c9ffe` | merged_clean | 0 / 80 |  / #44 | – |
| ui / local | `docs/c230-roadmap-planning` | `f067a0c499f6` | merged_clean | 0 / 3 |  / #6 | $WORKSPACE/personal-assistant-ui-c230 |
| ui / local | `feat/c14-admin-process-control` | `b003a87098c6` | merged_clean | 0 / 14 |  / #1 | $WORKSPACE/personal-assistant-ui-c14 |
| ui / local | `feat/c17-backend-integration` | `9d9ed61a0291` | merged_clean | 0 / 12 |  / #2 | $WORKSPACE/personal-assistant-ui-c17 |
| ui / local | `feat/c20-workflow-management` | `d7cb6cb639d5` | merged_clean | 0 / 9 |  / #3 | $WORKSPACE/personal-assistant-ui-c20 |
| ui / local | `feat/c22-container-readiness` | `07280633e0a3` | merged_clean | 0 / 5 |  / #5 | $WORKSPACE/personal-assistant-ui-c22 |
| ui / local | `feat/c24-05b2-review-ui` | `c18332928593` | merged_clean | 0 / 1 |  / #7 | $WORKSPACE/personal-assistant-ui-c2405b2 |
| ui / local | `fix/c21-workflow-cancel-acceptance` | `7d34bf3cbf47` | merged_clean | 0 / 7 |  / #4 | – |
| ui / local | `main` | `b2cf9ca9ba44` | active | 0 / 15 |  /  | $WORKSPACE/personal-assistant-ui |
| ui / remote | `main` | `90816a1578bc` | active | 0 / 0 |  /  | $WORKSPACE/personal-assistant-ui |

## Worktree- und Stashaufnahme

Kein fehlender Prozess-CWD beweist, dass ein Worktree unbenutzt ist. Beobachtet
wurden nur eigene Prozess-CWD-Metadaten, keine Umgebungsvariablen/Argumente/Tokens.
Bekannte aktive Aufgaben haben Vorrang: C24-06-A-Backend plus detached UIroot,
PM-01/#92 und beide Primärcheckouts bleiben geschützt. Der detached
`Personal_Assistant_C23_Test` gehört nicht automatisch MAINT-01; behalten.

| Repo | Root | Branch / Head | Stand | Untracked / Änderungen | Aktivität / Einschränkung |
| --- | --- | --- | --- | --- | --- |
| backend | $WORKSPACE/gmp_compliance | feat/c20b-workflow-http / 65b3f0915526 | dirty | 1 / 0 | protected primary checkout |
| backend | $WORKSPACE/Personal_Assistant-audit | detached / cdf3f711607b | unknown/invalid | 0 / 0 | gitdir file points to non-existent location |
| backend | $WORKSPACE/Personal_Assistant-c15 | feat/c15-monitoring-hardening / e74d3405b716 | unknown/invalid | 0 / 0 | gitdir file points to non-existent location |
| backend | $WORKSPACE/Personal_Assistant-c16 | feat/c16-job-control / 74578357afe0 | unknown/invalid | 0 / 0 | gitdir file points to non-existent location |
| backend | $WORKSPACE/Personal_Assistant-c18 | feat/c18-offline-workflows / d2c07f9b4e9f | unknown/invalid | 0 / 0 | gitdir file points to non-existent location |
| backend | $WORKSPACE/Personal_Assistant-c21q | feat/c21q-qdrant-transcript-pilot / 3a42b1675dff | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| backend | $WORKSPACE/Personal_Assistant-c22 | feat/c22-operations-readiness / f2842788efd4 | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| backend | $WORKSPACE/Personal_Assistant-c230 | docs/c230-roadmap-planning / 7f9fddf6d75f | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| backend | $WORKSPACE/Personal_Assistant-c2301 | feat/c23-01-parsed-content-adr / 50699d331a76 | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| backend | $WORKSPACE/Personal_Assistant-c2302a | feat/c23-02a-content-store / df41af0b5f36 | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| backend | $WORKSPACE/Personal_Assistant-c2302b | feat/c23-02b-content-adapters / ba2dcd4a0a74 | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| backend | $WORKSPACE/Personal_Assistant-c2302c | feat/c23-02c-recovery-operations / f33df74ff09e | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| backend | $WORKSPACE/Personal_Assistant-c2303 | feat/c23-03-reimport-binding / 42bbd8ae6511 | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| backend | $WORKSPACE/Personal_Assistant-c2304 | feat/c23-04-content-read-api / ada2f185fd38 | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| backend | $WORKSPACE/Personal_Assistant-c2305 | feat/c23-05-txt-unknown-time / 2e60d1529793 | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| backend | $WORKSPACE/Personal_Assistant-c2306 | feat/c23-06-real-material-evaluation / 351646f0ffa5 | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| backend | $WORKSPACE/Personal_Assistant-c2401 | docs/c24-01-indexing-retrieval / b001388e2f05 | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| backend | $WORKSPACE/Personal_Assistant-c2402 | feat/c24-02-deterministic-index-projection / 7d1b655cf622 | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| backend | $WORKSPACE/Personal_Assistant-c2403 | feat/c24-03-sqlite-fts5 / 0f3d9dd1066e | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| backend | $WORKSPACE/Personal_Assistant-c2404 | feat/c24-04-content-vector-adapter / 12740b76a30d | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| backend | $WORKSPACE/Personal_Assistant-c2405a | feat/c24-05a-retrieval-evaluation / 5a7d050685c3 | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| backend | $WORKSPACE/Personal_Assistant-c2405b | feat/c24-05b-human-review-workflow / f3fae9ef6d2c | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| backend | $WORKSPACE/Personal_Assistant-c2405b1 | feat/c24-05b1-review-backend / 20b8916900b2 | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| backend | $WORKSPACE/Personal_Assistant-c2405c | feat/c24-05c-real-corpus-pilot / a3d253a27c4f | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| backend | $WORKSPACE/Personal_Assistant-c2405c2 | feat/c24-05c2-real-pilot / c8894abea7be | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| backend | $WORKSPACE/Personal_Assistant-c2406a | feat/c24-06a-local-review / 4c057ae33d41 | dirty | 5 / 0 | C24-06-A ongoing local task |
| backend | $WORKSPACE/Personal_Assistant-completion | review/cs50-complete / a6b49d9eed1d | unknown/invalid | 0 / 0 | gitdir file points to non-existent location |
| backend | $WORKSPACE/Personal_Assistant-completion-audit | docs/cs50-completion-audit / 571874524b8b | dirty | 2 / 0 | Nutzung vor Entfernung separat bestätigen |
| backend | $WORKSPACE/Personal_Assistant-html-parser | fix/cs50-html-semantics / 9e7fda602b00 | dirty | 0 / 1 | Nutzung vor Entfernung separat bestätigen |
| backend | $WORKSPACE/Personal_Assistant-materials | docs/cs50-material-completion / 450016eb37a5 | unknown/invalid | 0 / 0 | gitdir file points to non-existent location |
| backend | $WORKSPACE/Personal_Assistant-materials-finalcheck | detached / 699be27b0b27 | unknown/invalid | 0 / 0 | gitdir file points to non-existent location |
| backend | $WORKSPACE/Personal_Assistant-pdf-v2 | fix/cs50-pdf-v2 / ddc0ea43f42f | unknown/invalid | 0 / 0 | gitdir file points to non-existent location |
| backend | $WORKSPACE/Personal_Assistant-pm01 | docs/pm01-project-consolidation / e06a29c47310 | clean | 0 / 0 | PM-01 / open PR #92 |
| backend | $WORKSPACE/Personal_Assistant-provenance-models | fix/knowledge-transcript-metadata-contract / dde15bf4434c | unknown/invalid | 0 / 0 | gitdir file points to non-existent location |
| backend | $WORKSPACE/Personal_Assistant_C23_Test | detached / d654f0580f6c | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| backend | $TMP/c20c-backend-master | detached / 1c0b30771c02 | unknown/invalid | 0 / 0 | gitdir file points to non-existent location |
| ui | $WORKSPACE/personal-assistant-ui | main / b2cf9ca9ba44 | clean | 0 / 0 | protected primary checkout |
| ui | $WORKSPACE/personal-assistant-ui-c14 | feat/c14-admin-process-control / b003a87098c6 | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| ui | $WORKSPACE/personal-assistant-ui-c17 | feat/c17-backend-integration / 9d9ed61a0291 | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| ui | $WORKSPACE/personal-assistant-ui-c20 | feat/c20-workflow-management / d7cb6cb639d5 | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| ui | $WORKSPACE/personal-assistant-ui-c22 | feat/c22-container-readiness / 07280633e0a3 | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| ui | $WORKSPACE/personal-assistant-ui-c230 | docs/c230-roadmap-planning / f067a0c499f6 | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| ui | $WORKSPACE/personal-assistant-ui-c2405b2 | feat/c24-05b2-review-ui / c18332928593 | clean | 0 / 0 | Nutzung vor Entfernung separat bestätigen |
| ui | $WORKSPACE/personal-assistant-ui-c2406a | detached / 90816a1578bc | clean | 0 / 0 | C24-06-A live demo UI dependency (detached main) |


Vier gültige Worktrees sind dirty: Primärbackend mit untracked `docs/nutrition.txt`;
C24-06-A mit fünf untracked Dateien; Completion-Audit mit zwei untracked Dokumenten;
HTML-Parser mit modifizierter `.gitignore`. Keine dieser Änderungen übernommen
oder überschrieben. [Worktrees.tsv](worktrees.tsv) enthält alle exakten Pfade.

Backend-Stashes (repositoryweit, keinem einzelnen Worktree sicher zugewiesen):

| Repository | Stash-SHA | Commitdatum |
| --- | --- | --- |
| backend | de887a419c73719e00fdbe1c80bfe5e4de9f7d84 | 2026-10-13T20:35:21+02:00 |
| backend | 660622b548f13f98a5aa1246d543409ce00ec0a2 | 2026-07-30T17:53:25+02:00 |


UI hat keine Stashes. Stashinhalte wurden weder angewendet noch kopiert; vor
jeder späteren Bereinigung separat sichern/zuordnen. Ignorierte Bestände wurden
nicht pauschal durchsucht. „Clean“ ist kein Nachweis, dass Venvs, Caches oder
persistente ignorierte Daten entbehrlich sind.

## Bekannte PRs und aktive Arbeiten

| PR | Status | Branch / tatsächlicher PR-Head | Bewertung |
| --- | --- | --- | --- |
| [backend #92](https://github.com/rf-data/Personal_Assistant/pull/92) | open | `docs/pm01-project-consolidation` / `e06a29c47310d347af26b7a8c61e574d0cef172a` | Aktiver separater PM-01-Planungs-PR; nicht in MAINT übernehmen |
| [backend #91](https://github.com/rf-data/Personal_Assistant/pull/91) | closed / merged | `feat/c24-05c2-real-pilot` / `c8894abea7be1554a6f234f551ce92bc6e00bdc9` | Synthetische Integration und #89-Metadaten integriert; Realpilot blockiert |
| [backend #90](https://github.com/rf-data/Personal_Assistant/pull/90) | closed / merged | `feat/c24-05b1-review-backend` / `20b8916900b201d8051e203327a7023e06c64914` | Reviewpersistenz/API integriert; technische Lieferung, keine reale Humanabnahme |
| [backend #89](https://github.com/rf-data/Personal_Assistant/pull/89) | open / Draft | `feat/c24-05c-real-corpus-pilot` / `a3d253a27c4fd7aed37c2a4b9d38aa8a4ed1d81d` | r1/r2-Pilotmetadaten bereits in #91; Source-/Gold-/D06/D07-Gates weiter offen |
| [backend #88](https://github.com/rf-data/Personal_Assistant/pull/88) | open / Draft | `feat/c24-05b-human-review-workflow` / `f3fae9ef6d2c919adb12b08242bf84819f2b42f2` | Architekturhistorie; B1/#90 und UI-B2/#7 liefern inzwischen die Umsetzung |
| [backend #72](https://github.com/rf-data/Personal_Assistant/pull/72) | open / Draft | `feat/c21q-qdrant-transcript-pilot` / `3a42b1675dffe823edc179a347fa97dd1a096fd0` | Qdrant-/Sourcebinding-Gates offen; kein Runtimepfadfix, kein FTS5-Pflichtteil |
| [backend #11](https://github.com/rf-data/Personal_Assistant/pull/11) | open | `fix/math-normalization-import` / `efed68d08ddbd25a7d0404a164cf6d54ce334ab6` | Alten Scope gegen Default prüfen; keine Schließaktion |
| [backend #10](https://github.com/rf-data/Personal_Assistant/pull/10) | open | `fix/knowledge-source-id` / `9ed643dedf220f37a5ebfbf533582c64d563d96d` | Alten Scope gegen Default prüfen; keine Schließaktion |
| [backend #9](https://github.com/rf-data/Personal_Assistant/pull/9) | open | `feat/official-transcript-import` / `3d1317347018fce47f49331fbfea92e4a055a337` | Alten Scope gegen Default prüfen; keine Schließaktion |
| [backend #6](https://github.com/rf-data/Personal_Assistant/pull/6) | open | `feat/cs50-discovery-contracts` / `7ba2dd844d24377eba36ca98b64ea4c2e059cf62` | Alten Scope gegen Default prüfen; keine Schließaktion |
| [ui #7](https://github.com/rf-data/personal-assistant-ui/pull/7) | closed / merged | `feat/c24-05b2-review-ui` / `c1833292859323f5360c2817d7e2ec57bd97bcd4` | B2-Review-UI integriert; keine allgemeine Search UI oder reale Browserfreigabe |


C24-06-A hat im abgefragten Livebestand noch keinen PR; der lokale Auftrag bleibt
aktiv und unangetastet. PM-01/#92 bleibt offen. Eigener MAINT-PR ist ein zusätzlicher
Audit-/Dokumentationsvorgang, keine Änderung dieser offenen Arbeiten.
