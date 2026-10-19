# MAINT-01 – Branch-, Worktree- und Dokumentkonsolidierung

19.10.2026. Basis Backend `4c057ae33d41ba98e227879cc8a51283338e4a0b`, UI
`90816a1578bcf67739ee9acaa483c1635aa0c44b`. Kein Merge/Close/Deploy, keine Löschung,
kein Pruning, keine neuen Tools und keine Änderung bestehender Dokumente.

- [A. Branch Inventory](branch_inventory.md): Identität, lokale/live Branches,
  Merge-/Patch-/Treebelege, Worktrees, Stashes und offene PRs.
- [B. Document Inventory](document_inventory.md): Versionstupel, SHA256, Herkunft,
  Duplikate, abweichende Fassungen, sensible Metadaten und Importentscheidung.
- [C. Cleanup Proposal](cleanup_proposal.md): behalten, prüfen, integrieren,
  mögliche spätere Löschkandidaten und benötigte Einzelfreigaben.
- [Provenienzmanifest](import_manifest.md): einziger unveränderter historischer #88-ADR.
- [Ungeklärte Zuordnung](../../_unresolved_imports/maint01/README.md): ausschließlich
  Metadaten, keine private oder unbestätigte Originalkopie.

## Tabellen und Reproduktionsvertrag

UTF-8-/LF-TSV, erste Zeile Spaltennamen, JSONzellen für Listen/Objekte. Leerer
SHA/Status heißt unbekannt oder bewusst nicht gelesen, nie leerer Dateiinhalt.
[Branches](branches.tsv), [Worktrees](worktrees.tsv), [gecachte Trackingrefs](cached_tracking_refs.tsv),
[Dokumentversionen](document_versions.tsv). Ein Datensatz pro Branch/Scope bzw.
Repository/Pfad/SHA-Version; komplette Quellcommits statt Mtime-Vergleichen.
Dokumentzellen `branch_origins` verweisen über stabile B-IDs auf `branches.tsv`
(mit tatsächlichem Repository/Branch/Commit); `worktree_origins` über W-IDs auf
`worktrees.tsv` (mit Quellroot/HEAD). Das vermeidet tausendfach wiederholte
Commit-/Hostwurzelmetadaten, ohne Herkunft oder Hashbindung zu verlieren.
`related_prs` enthält repositorylokale PR-Nummern; aktuelle/merged PR-Belege sind
über die zugeordneten Branchzeilen und deren echte Head-/Merge-SHAs nachvollziehbar.
Keine absoluten privaten Hostpfade oder Inhalte ausgeschlossener Dateien.

Die Aufnahme beginnt vor dem eigenen MAINT-Branch/Worktree/PR. Sie ist ein datierter
Snapshot, kein neuer Hintergrundscanner oder dauerhaft paralleler Planungsspeicher.
Private Ausführungsskripte/Original-APIantworten bleiben außerhalb des Repositories.
Git- und stdlib-Prüfungen wurden ohne Dependencyinstallation ausgeführt.

## Tatsächliche Prüfungen

GitHub-Branch-/PR-Listen, alle Branchheads, ancestry/merge-base, graph-eigene Commits,
Patchäquivalenz und Vergleich mit wirklichem gemergten PR-Tree geprüft. Bytehashes
versionierter und unveränderter geeigneter Worktreedokumente geprüft; untracked/
Env-/Roh-/private Inputs nicht inhaltlich geöffnet. Quelle/Ziel des einzigen Imports
sind byteidentisch. #89-Metadaten werden nicht nochmals kopiert. Historische Berichte
behalten ihre Bytes; keine automatische semantische Zusammenführung.

Abschließend erfolgreich geprüft: 145 Branch-/44 Worktree-/452 Dokumentversions-
und 35 Unresolved-Zeilen, 44 Trackingrefs, eindeutige B-/W-/D-IDs und alle
Quellverknüpfungen. 39 lokale Markdownziele/Anker, UTF-8/LF sowie SHA/Größe der
Übernahme stimmen. Die 34 gültigen Quellworktrees haben dieselben HEADs und
Status-/untracked-Metadaten, sämtliche vorherigen Branch-/Trackingrefs und Stashes
sind unverändert. Acht #89-JSONdateien stimmen weiterhin mit dem integrierten
Defaultbestand überein. Zwölf ausschließlich neue Dokumentationsdateien;
`git diff --check` erfolgreich. Keine Anwendungs-/Ruff-/Pytest-/Browserabnahme behauptet:
Es werden ausschließlich geeignete Dokumentation und Inventarmetadaten hinzugefügt.
Der [historische importierte ADR](../../architecture/human_review_workflow_adr.md)
enthält damalige Statusaussagen; diese werden weder als heutiger Implementierungsstand
noch als neue technische Testerfolge ausgegeben.
