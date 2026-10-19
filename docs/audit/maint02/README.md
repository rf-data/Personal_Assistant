# MAINT-02 – Verifizierte Bestände, keine Bereinigung

19.10.2026, Europe/Berlin. Dokumentationsstand für eine **später einzeln zu
autorisierende MAINT-03**. **Null bestätigte bzw. ausführungsbereite Löschkandidaten.**
Es wurde kein Branch, Worktree, Stash, Ref oder Datei gelöscht; kein Prune, Reset,
Clean, Rebase, Merge oder Force-Push ausgeführt. Keine Inhalte von Envdateien,
Credentials, untracked Dokumenten oder privaten Daten gelesen. Keine Services,
Deployments oder Datenbanken angefasst.

| Gitbestand vor dem eigenen MAINT-02-Zugang | Backend | UI | Summe |
| --- | ---: | ---: | ---: |
| Lokale Branches | 106 | 8 | 114 |
| Live Remote-Branches | 32 | 1 | 33 |
| Branchzeilen (Scopes getrennt) | 138 | 9 | 147 |
| Registrierte Worktrees | 38 | 8 | 46 |
| Stashes | 2 | 0 | 2 |

36 Worktrees sind gültig, zehn ungültig: acht Pfade fehlen, zwei Restverzeichnisse
existieren. Zehn überlieferte HEADs sind als Commitobjekte vorhanden; fünf besitzen
Commits außerhalb des Defaults, sämtliche zehn bleiben durch vorhandene lokale
Refs erreichbar. Ein neuer Checkout könnte **nur den committed HEAD** rekonstruieren;
keine Wiederherstellung untracked/ignorierter Daten wird behauptet.

| Aktuelle effektive Branchklassifikation | Zeilen |
| --- | ---: |
| `merged_clean` | 50 |
| `merged_with_extra_commits` | 41 |
| `open_pr` | 14 |
| `protected_active` | 12 |
| `stale_candidate` | 7 |
| `unmerged_unique_work` | 23 |

Schutz und offene PRs haben Vorrang. `intrinsic_graph_class` hält darunterliegende
Graphbefunde fest; z. B. bleibt unmerged Arbeit auch in geschützten Zeilen erkennbar.
`unknown=0` bedeutet bekannte Gitgraphen, **nicht** bekannte Betreiberverwendung.
Alle 239 Ausführungstabellenzeilen benötigen für eine spätere Veränderung eine
Einzelentscheidung: 103 Keep, 103 Review, 33 Archive,
0 Remove. Archive ist ein vorgeschlagener Erhaltungsweg, keine ausgeführte Sicherung.

30 Branchzeilen haben ausschließlich die technischen Grundbedingungen
`ahead=0`, keinen angehängten Worktree und keinen erkannten Schutz/offenen PR.
Sie sind eine **Prüfliste**, keine Löschliste: Nutzung, Sicherung und Autorisierung
sind offen. Davon sind sechs aus den ursprünglichen acht Kandidaten; die anderen
zwei sind durch Worktrees zusätzlich gesperrt. Alle 147 Branchzeilen bleiben
hinsichtlich einer Löschung geschützt oder ungeklärt; auch kein Worktree ist
freigegeben. Details und exakte gebundene Befehlsvorschläge stehen in der Tabelle.

## Verifizierte Bezugspunkte

- Backend `rf-data/Personal_Assistant`, live `master`
  `ea4f71461b5af9f4dfad96ba9a895c3b78a5b8f0`, Common-Gitdir
  `$WORKSPACE/gmp_compliance/.git`.
- UI `rf-data/personal-assistant-ui`, live `main`
  `90816a1578bcf67739ee9acaa483c1635aa0c44b`, Common-Gitdir
  `$WORKSPACE/personal-assistant-ui/.git`.
- Beide vollständige unabhängige Gitgraphen, kein shallow Checkout. Alle benötigten
  Liveheads bereits lokal verfügbar; kein Fetch nötig, kein vorhandener Arbeitsref
  oder Trackingref aktualisiert. Lokale Default-/Primärheads sind nicht live Default.
- MAINT-01 #93 und PM-01 #92 sind gemergt; ihre Worktrees/Historien bleiben geschützt.
  PM-02 #94 und Drafts #72/#88/#89 bleiben offen. Ältere offene #6/#9/#10/#11
  sind ebenfalls berücksichtigt. UI: kein offener PR.

## Artefakte und Lesereihenfolge

- [Branches](branches.tsv): 147 eindeutige Repository/Scope/Name-Zeilen, Mergebase,
  Ahead/Behind, Tree, graph-eigene Commits, `git cherry`, tatsächliche PR-Trees,
  historische Dokumentbezüge und Worktree-IDs.
- [Worktrees](worktrees.tsv): 46 Repository/Pfad-Zeilen, HEAD, Index-/Statusmetadaten,
  Schutz und begrenzte Wiederherstellbarkeit.
- [Trackingrefs](tracking_refs.tsv): 46 **gecachte** Refs, separat vom Livebestand.
- [PR-Nachweise](pull_requests.tsv): offene und gemergte PRs beider Repositories;
  geschlossene ungemergte PRs wurden in der Liveabfrage mitgelesen, sind keine
  Integrationsnachweise. PR-Nummern gelten nur innerhalb des Repositorys.
- [Ausführungstabelle](execution_plan.tsv): 239 gebundene Objekte, geforderte
  Einzelfelder, immer `authorization_required=true`, keine Ausführung.
- [Ursprüngliche acht Branchzeilen](original_stale_candidates.md).
- [Worktree-Recovery](worktree_recovery.md), [Delta und Dokumenterhalt](maint01_delta.md).
- [MAINT-03-Ablauf und Sicherung](maint03_execution_plan.md), [Validierung](validation.md).

TSV: UTF-8/LF, Header, JSONzellen für Listen/Objekte. Leere Befehls-/SHAzellen heißen
nicht freigegeben/nicht anwendbar/unbekannt, niemals implizite Zustimmung.
BR/WT/TR sind lokale MAINT-02-IDs; alte B/W/D-IDs verweisen weiter auf
[MAINT-01](../maint01/README.md). Pfadalias `$WORKSPACE` bezeichnet exakt
`/home/robfra/0_Portfolio_Projekte`, `$TMP` exakt `/tmp`; keine Globs oder Scanwurzeln.
Die nach MAINT-01 zusätzlich vorhandenen Worktrees/Branches sind einzeln erfasst.
Der eigene neue Branch/Worktree `docs/maint02-cleanup-verification`/
`$WORKSPACE/Personal_Assistant-maint02` ist absichtlich außerhalb des
Quellsnapshots: lokal +1 Branch/+1 Worktree, bei Veröffentlichung +1 Remote-Branch
und ein eigener PR. Diese Eigenzugänge sind keine Abweichung des Quellbestands.
