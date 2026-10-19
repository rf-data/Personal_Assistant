# Worktree-Metadaten und begrenzte Wiederherstellung

Alle 46 Registrierungen sind in [worktrees.tsv](worktrees.tsv) mit Pfad, Branch/
Detached-HEAD, Schutz, Status und Entscheidung in [execution_plan.tsv](execution_plan.tsv)
erfasst. 36 sind gültig; zehn ursprüngliche ungültige Registrierungen bleiben
ungültig. Kein `prune` und kein `worktree repair/remove` ausgeführt.

| MAINT-02 / MAINT-01 | Exakter Pfadalias | Registrierter HEAD | Dateisystembeobachtung | Ahead Default | Bereits erhaltende lokale Refs |
| --- | --- | --- | --- | ---: | --- |
| WT002 / W0002 | `$WORKSPACE/Personal_Assistant-audit` | `cdf3f711607b8c99783973a3a88ad6925a5d0079` | Restverzeichnis: .ruff_cache, .venv | 1 | `refs/heads/archive/cs50-2026-10/cdf3f711607b` |
| WT003 / W0003 | `$WORKSPACE/Personal_Assistant-c15` | `e74d3405b71668fdd45258b902811e2152b23d0e` | Pfad fehlt | 0 | `refs/heads/docs/c170-repository-consolidation`, `refs/heads/docs/c170-repository-consolidation-public` (weitere in TSV) |
| WT004 / W0004 | `$WORKSPACE/Personal_Assistant-c16` | `74578357afe04194cbc73b7cd6aad120c1f11816` | Pfad fehlt | 0 | `refs/heads/docs/c170-repository-consolidation`, `refs/heads/docs/c170-repository-consolidation-public` (weitere in TSV) |
| WT005 / W0005 | `$WORKSPACE/Personal_Assistant-c18` | `d2c07f9b4e9facdb2ecbb6f3d541ef454524997a` | Pfad fehlt | 0 | `refs/heads/docs/c170-repository-consolidation`, `refs/heads/docs/c170-repository-consolidation-public` (weitere in TSV) |
| WT027 / W0027 | `$WORKSPACE/Personal_Assistant-completion` | `a6b49d9eed1d6a56c1f9bc81cafb7953ccfafa42` | Restverzeichnis: workers | 0 | `refs/heads/docs/c170-repository-consolidation`, `refs/heads/docs/c170-repository-consolidation-public` (weitere in TSV) |
| WT031 / W0030 | `$WORKSPACE/Personal_Assistant-materials` | `450016eb37a50a8cf90f32023557919b5048dc48` | Pfad fehlt | 11 | `refs/heads/docs/cs50-material-completion` |
| WT032 / W0031 | `$WORKSPACE/Personal_Assistant-materials-finalcheck` | `699be27b0b274c24f1b4197658c3cee6ef130b9c` | Pfad fehlt | 10 | `refs/heads/docs/cs50-material-completion` |
| WT033 / W0032 | `$WORKSPACE/Personal_Assistant-pdf-v2` | `ddc0ea43f42f13ef197a89c123f8d79b7ac6be3d` | Pfad fehlt | 1 | `refs/heads/fix/cs50-pdf-v2` |
| WT036 / W0034 | `$WORKSPACE/Personal_Assistant-provenance-models` | `dde15bf4434c4adb5e92755508d38428b9b090b8` | Pfad fehlt | 1 | `refs/heads/fix/knowledge-transcript-metadata-contract` |
| WT038 / W0036 | `$TMP/c20c-backend-master` | `1c0b30771c02d377445fc58059d19ec605c776ed` | Pfad fehlt | 0 | `refs/heads/docs/c230-roadmap-planning`, `refs/heads/docs/c24-01-indexing-retrieval` (weitere in TSV) |

## Tatsächlich geprüft

- Vorhandensein des exakt registrierten Pfads und `.git`-/Common-Gitdir-Zuordnung;
  Primärcheckouts unabhängig zugeordnet. `git worktree list --porcelain` liefert
  Registrierungen, nicht automatisch nutzbare Arbeitsverzeichnisse.
- Bei zehn ungültigen Fällen: erhaltenen Registrierungsindex über explizites
  `--git-dir=<registration>` / `--work-tree=<registered-path>` und
  `diff-index --cached --name-status --no-renames <observed-HEAD>` verglichen.
  Alle zehn Abfragen erfolgreich und ohne gestagte Unterschiede.
- Nur bei den zwei vorhandenen Restwurzeln: unmittelbare Namen/Typ/Modus gelesen,
  keine rekursive Inhaltsprüfung. `.venv`, `.ruff_cache` und `workers` bleiben
  unangetastet. Ein fehlender Pfad könnte auf extern fehlendes Mount/Umbenennung
  zurückgehen; diese Ursachen sind **nicht entschieden**.
- Alle zehn HEAD-Commitobjekte vorhanden und über andere lokale Refs erreichbar;
  fünf HEADs besitzen graph-eigene Commits. Registry/Refs daher nicht als Abfall
  behandeln. Der detached Finalcheck-HEAD wird durch den Material-Branch erhalten.
- Nur sichtbare `/proc`-CWD-Metadaten derselben UID betrachtet; keine argv/env/FDs.
  Kein vollständiger Betreiber-/Prozessnachweis. `not_verified` bleibt auch bei
  null CWD-Treffern maßgeblich.

## Entscheidung je Zustand

1. Primärcheckouts, Backend- und detached UI-C24-06-A, PM-01-/MAINT-01-Historie,
   PM-02 sowie dirty/locked Worktrees: Keep. Kein Umhängen oder neues Checkout dort.
2. Gültig, scheinbar sauber und gemergt: Review. Ignorierte/private Daten wurden
   nicht als entbehrlich bestätigt. Kein Löschbefehl in dieser Phase.
3. Acht fehlende Pfade: Registry und zugehörige Refs behalten, Betreiber zuerst
   nach Verschiebung/Mount/externem Gebrauch fragen. Mögliche committed Rekonstruktion
   nur nach Freigabe in **einem neuen leeren separaten privaten Root**.
4. Zwei vorhandene ungültige Wurzeln: Original und Registrierung erhalten.
   Operator muss Restdaten sichern und frühere Verknüpfung klären. Kein vorschnelles
   `repair` in bestehende Pfade; keine neue `.git`-Datei schreiben.

Die Tabelle liefert pro WT-ID einen genauen späteren
`git worktree add --detach "$MAINT_RECOVERY_ROOT/WTnnn" <observed-SHA>`-Vorschlag.
Dieser wurde **nicht ausgeführt** und rekonstruiert ausschließlich committed Dateien;
er ersetzt weder eine Sicherung vorhandener Restdaten noch einen Nachweis früherer
untracked/ignorierter Arbeit. Vertrauliche historische Gitbytes nicht unkontrolliert
in öffentliche Recoveryroots auschecken. Ziel und Nutzungsrechte zuerst festlegen.

Git 2.39.5 bietet kein dokumentiertes einzelnes `prune <entry>`.
Kein globales Prune und kein manuelles Löschen administrativer Verzeichnisse planen.
Nach einer späteren ownerbestätigten Reparatur kann ein sauberer Worktree gezielt
mit dem dokumentierten Gitworkflow behandelt werden; dafür ist ein eigener neuer
Prüf-/Freigabeschritt nötig. Keine force-Option.
[Git-worktree-Vertrag](https://git-scm.com/docs/git-worktree).
