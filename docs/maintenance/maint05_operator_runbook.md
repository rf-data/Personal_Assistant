# MAINT-05: Betreiberanleitung

**Während dieses Auftrags nur Inventur und synthetische Tests.** Die folgenden
Ausführungsbefehle sind für eine spätere ausdrücklich freigegebene Wartung bestimmt.
Reale Worktrees wurden nicht entfernt; kein Push und kein Merge wurden ausgeführt.
Siehe [Sicherheitsvertrag](maint05_archive_safety.md),
[Inventar](maint05_worktree_inventory.md) und [Pilot](maint05_c2301_pilot.md).

## Umgebung und lesende Befehle

Linux, Git mit `worktree list --porcelain -z`, Python 3.12 und Projekt-uv-Profil.
Vom Checkout mit integrierter CLI starten. Der aktuelle MAINT-05-Checkout bleibt bis
zum Review erhalten; sein ursprünglicher HEAD ist `e68275205fefb7a5f6db42bc45060e505bfcefb5`.
Globale Optionen stehen vor dem Unterbefehl. Alle Pfade müssen absolut sein.

```bash
cd /home/robfra/0_Portfolio_Projekte/Personal_Assistant-maint05
MAINT05_REPO=/home/robfra/0_Portfolio_Projekte/Personal_Assistant
MAINT05_TREE=/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c2301
MAINT05_BRANCH=feat/c23-01-parsed-content-adr
uv run --python 3.12 python -m scripts.worktree_archive --help
uv run --python 3.12 python -m scripts.worktree_archive \
  --repo "$MAINT05_REPO" inventory
uv run --python 3.12 python -m scripts.worktree_archive \
  --repo "$MAINT05_REPO" check --worktree "$MAINT05_TREE" \
  --remote origin --backup-branch "$MAINT05_BRANCH"
```

JSON-Ausgaben: `HOLD` und Exitcode 3 bei Blockern/Fehlern; `PLAN_ONLY` und Exitcode 0
für einen prüfbaren Plan. Erfolgreiche Ausführung meldet `ARCHIVED` beziehungsweise
`RESTORED`. Eine Inventur mit mindestens einem HOLD liefert ebenfalls 3.
Syntaxfehler liefert argparse-Exitcode 2. Kein Exitcode ist eine pauschale Löschfreigabe.
Ohne `--execute` liest die CLI ausschließlich Gitzustand. Nur ein ausdrücklich
angefordertes `--save-plan` legt zusätzlich eine neue Datei an, ohne Überschreiben.

Zusätzliche aktive Aufgaben vor jedem Lauf explizit schützen, beispielsweise:

```bash
uv run --python 3.12 python -m scripts.worktree_archive \
  --repo "$MAINT05_REPO" \
  --protect /home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26f \
  --protected-backup-branch release/stable inventory
```

Die vollständige Liste fest geschützter und zusätzlich erkannter Aufgaben steht im
Inventar. Ihre Aufnahme in eine Liste ist keine Erlaubnis, andere Worktrees zu löschen.
PR-/Taskbesitzer müssen separat geprüft werden; die CLI fragt GitHub-PRs nicht ab.

## Backup vorbereiten: ausschließlich bewusste Betreiberaktion

Vorher Remote-URL und Schreibziel prüfen, Änderungen und Zusatzdateien separat
sichern. Die CLI sichert keine Venvs, Datenbanken, Secrets, Stashes oder ignorierten
Artefakte. Weder löschen noch pauschal in Git aufnehmen. Bei unklaren Daten: HOLD.

Nur falls der Betreiber den Push gesondert genehmigt und der Branch vollständig
geprüft ist, kann er diesen Befehl manuell ausführen:

```bash
git -C "$MAINT05_TREE" remote get-url --all origin
git -C "$MAINT05_TREE" push -u origin "HEAD:refs/heads/$MAINT05_BRANCH"
```

Kein Force. Bei abweichendem Remote-HEAD zunächst Ursache klären. Niemals `master`,
`main` oder einen weiteren geschützten Branch als Archivziel wählen. Anschließend
muss `check` frisch `exact_remote_head: true` melden. Ein erfolgreicher Push genügt
nicht. Bei Netzwerkfehlern keine leere SHA als Erfolg behandeln.

## Einzelne Archivierung planen und später freigeben

Zuerst mit Taskbesitzern klären, dass der ausgewählte Worktree nicht aktiv ist.
Alle Writer außerhalb der CLI tatsächlich stilllegen. Wenn dies unklar bleibt,
nicht fortfahren. Keine laufende Codex-Sitzung durch diese Anleitung verändern.
Aufbewahrung des Backupbranches auf GitHub und Sicherung der Datensätze vereinbaren.

Ein eigenes dauerhaft gesichertes Verzeichnis wählen, außerhalb aller zu entfernenden
Worktrees und außerhalb `.git`. Der folgende Name ist ein Beispiel für diesen Host;
bereits vorhandene Dateien werden nicht ersetzt. Für jeden neuen Plan neue Namen nutzen.

```bash
MAINT05_RECORDS=/home/robfra/maint05-archive-records
mkdir -p "$MAINT05_RECORDS"
uv run --python 3.12 python -m scripts.worktree_archive \
  --repo "$MAINT05_REPO" archive --worktree "$MAINT05_TREE" \
  --remote origin --backup-branch "$MAINT05_BRANCH" \
  --save-plan "$MAINT05_RECORDS/c2301-plan-01.json"
```

Plan vollständig lesen. Nur `CANDIDATE_FOR_ARCHIVE` ohne Blocker ist prüfbar.
Die `approval`-Zeile bindet den SHA und übrigen Sicherheitszustand. Der Text wird
bewusst vom Betreiber übertragen; nicht aus einer ungelesenen Datei automatisch
in einen Ausführungsaufruf übernehmen. Nach eigenständiger Freigabe:

```bash
read -r -p 'Geprüften vollständigen ARCHIVE-Approvaltext eingeben: ' MAINT05_APPROVAL
uv run --python 3.12 python -m scripts.worktree_archive \
  --repo "$MAINT05_REPO" archive --worktree "$MAINT05_TREE" \
  --remote origin --backup-branch "$MAINT05_BRANCH" \
  --plan "$MAINT05_RECORDS/c2301-plan-01.json" \
  --receipt "$MAINT05_RECORDS/c2301-receipt-01.json" \
  --execute --approve "$MAINT05_APPROVAL" \
  --exclusive-writers ALL_WRITERS_STOPPED
```

Dieser Aufruf führt nach erneuten Prüfungen und Wiederherstellungsprobe das normale
`git worktree remove` aus. Kein Batchmodus, keine Branchlöschung. Nach Erfolg beide
Datensätze sichern: PREPARED und `.completed.json`. Branch und Remote unverändert
prüfen. Keine Lockdateien zur vermeintlichen Bereinigung löschen.

## Restore planen und freigeben

Den abgeschlossenen Datensatz verwenden. Ursprünglicher Pfad ist darin dokumentiert;
ein anderer expliziter freier Zielpfad ist möglich. Ein vorhandenes Verzeichnis,
abweichender lokaler Branch oder ein bereits ausgecheckter Branch führt zu HOLD.

```bash
uv run --python 3.12 python -m scripts.worktree_archive \
  --repo "$MAINT05_REPO" restore \
  --record "$MAINT05_RECORDS/c2301-receipt-01.json.completed.json" \
  --target "$MAINT05_TREE"
read -r -p 'Geprüften vollständigen RESTORE-Approvaltext eingeben: ' MAINT05_RESTORE_APPROVAL
uv run --python 3.12 python -m scripts.worktree_archive \
  --repo "$MAINT05_REPO" restore \
  --record "$MAINT05_RECORDS/c2301-receipt-01.json.completed.json" \
  --target "$MAINT05_TREE" --execute \
  --approve "$MAINT05_RESTORE_APPROVAL" \
  --exclusive-writers ALL_WRITERS_STOPPED
```

Restore prüft den Backupref erneut, lädt Objekte ohne Branchüberschreiben und prüft
den tatsächlich ausgecheckten SHA. Er überschreibt keinen vorhandenen Zielpfad.
Bei Fehlern im Checkout bleibt entstandener Zustand zur Untersuchung erhalten.
PREPARED allein darf nicht automatisch zum Abschlussdatensatz umetikettiert werden.

## Wiederholbare Offlineprüfung

```bash
uv run --python 3.12 python -m pytest \
  tests/test_worktree_archive.py tests/test_repository_audit.py
uv run --python 3.12 ruff check scripts/worktree_archive.py tests/test_worktree_archive.py
uv run --python 3.12 ruff format --check scripts/worktree_archive.py tests/test_worktree_archive.py
```

Tests verwenden ausschließlich neue temporäre Gitrepos/Bare-Remotes. Die zusätzlichen
MAINT-05-Tests sperren jeden Git-Subprozess außerhalb ihrer temporären Roots.
Die tatsächliche lokale Ausführungsumgebung und Ergebnisse stehen im
[Validierungsbericht](maint05_validation.md).

## Übergabe ohne Git-Schreibrecht

Die Sandbox erlaubt keine Schreibzugriffe auf die gemeinsame `.git`-Ablage. Deshalb
keine lokalen Commits, Pushes, PR-Erstellung oder Umgehung über andere Metadaten.
Der geprüfte Patch und sein Manifest werden separat unter `/tmp/maint05-delivery/`
bereitgestellt. Sie enthalten sämtliche beabsichtigten neuen Code-/Test-/Dokumentdateien.
Das Manifest nennt Basiscommit, SHA-256 jedes Inputs und des Patches.

Der Betreiber prüft Manifest und Patch, dann im bestehenden MAINT-05-Worktree:

```bash
cd /home/robfra/0_Portfolio_Projekte/Personal_Assistant-maint05
git --no-optional-locks status --short
git branch --show-current
git rev-parse HEAD
# Erwartet: feat/maint05-worktree-archival, Basis e68275205fefb7a5f6db42bc45060e505bfcefb5.
# Nur die im geprüften Manifest genannten Pfade hinzufügen:
git add -- scripts/worktree_archive.py tests/test_worktree_archive.py \
  docs/maintenance/maint05_archive_safety.md \
  docs/maintenance/maint05_c2301_pilot.md \
  docs/maintenance/maint05_operator_runbook.md \
  docs/maintenance/maint05_validation.md \
  docs/maintenance/maint05_worktree_inventory.md
# Die bestehende globale *.json-Regel erfordert für genau diese vier Belegdateien:
git add -f -- docs/maintenance/maint05_inventory_snapshot.json \
  docs/maintenance/maint05_pilot_github.json \
  docs/maintenance/maint05_pr_snapshot.json \
  docs/maintenance/maint05_state_verification.json
git diff --cached --check
git diff --cached --stat
git commit -m "feat(maint05): audit worktrees and guard explicit archival"
git push -u origin HEAD:refs/heads/feat/maint05-worktree-archival
```

Der Push ist eine spätere Betreiberaktion und aktualisiert nur den eigenen
MAINT-05-Branch. Er ist keine Pilotbackupfreigabe. Anschließend regulären Review-PR
gegen `master` vorbereiten. Kein automatischer Merge. Dokumente müssen nach Review
in der tatsächlichen Defaultbranch `master` vorhanden sein, bevor vollständiger
Lifecycleabschluss behauptet werden kann. Worktree und Branch bis dahin erhalten.
Keine vorbestehenden Git-Artefakte aus MAINT-01/02/03 löschen.
