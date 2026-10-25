# MAINT-05: Pilot C23-01

Ergebnis vom 25.10.2026: **HOLD – nicht entfernt, kein Push.** Der lokale Zustand
ist ein möglicher späterer Prüfkandidat, aber kein `CANDIDATE_FOR_ARCHIVE` und kein
`ARCHIVE_VERIFIED`, solange der autoritative Branch-/Restorenachweis fehlt.

| Prüfung | Tatsächlicher Befund |
| --- | --- |
| Pfad | `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c2301` |
| Registrierung | Vorhandener verbundener Worktree, kein Detached HEAD |
| Branch | `feat/c23-01-parsed-content-adr`, wie erwartet |
| HEAD und lokaler Branch-SHA | `50699d331a769db3acd9e5e8507ad51b2de1760c` |
| Betreff | `docs: specify C23 parsed content persistence architecture` |
| Versionierte Änderungen | Keine |
| Untracked / ignored / zusätzliche Verzeichnisse | Keine bei der vollständigen lesenden Prüfung |
| Riskante Indexflags / Submodule | Keine erkannt |
| Remote | `origin`: `https://github.com/rf-data/Personal_Assistant.git` |
| Upstream | Nicht konfiguriert |
| Lokales `refs/remotes/origin/feat/c23-01-parsed-content-adr` | Fehlt; keine aktuelle Remoteaussage daraus ableitbar |
| Autoritatives `git ls-remote` | Exit 128, DNS: `Could not resolve host: github.com` |
| Aktueller GitHub-Branch-HEAD | `unknown` / `REMOTE_UNVERIFIED` |
| Ahead / behind | Unbekannt; keine geeigneten lokalen Tracking-/verifizierten Remotereferenzen |
| Commit auf GitHub vorhanden | Ja: separate erfolgreiche GitHub-Commitabfrage mit exaktem SHA |
| PR | [#75](https://github.com/rf-data/Personal_Assistant/pull/75), closed, merged=true, head-SHA identisch |
| PR-Mergecommit laut GitHub | `a2dc080ac5896c9c8032f42bf51ecb5fdb9a71c6` |
| Aktuelle Erreichbarkeit über vorgesehenen Backupbranch | Unbekannt; PR-Merge ist kein Branchbackupnachweis |
| Wiederherstellung | Nicht real getestet; kein verifizierter Archivdatensatz vorhanden |
| Aktivität | Kein positiver Prozess-CWD-Nachweis; Inaktivität dadurch nicht bewiesen |

Belege: [Inventar](maint05_worktree_inventory.md),
[maschinenlesbare Inventur](maint05_inventory_snapshot.json),
[GitHub-Commit-/PR-Metadaten](maint05_pilot_github.json).
Die getrennte [Commitquelle](https://github.com/rf-data/Personal_Assistant/commit/50699d331a769db3acd9e5e8507ad51b2de1760c)
beweist Commitexistenz, keine dauerhafte Referenz des ursprünglichen Branches.
Die positive PR-Abfrage klärt den historischen Mergebezug dieses Piloten; die CLI
führt weiterhin `PR_OR_MERGE_UNVERIFIED`, da sie PRs grundsätzlich nicht selbst abfragt.
Ein lokaler `merge-base --is-ancestor <pilot-head> master` lieferte Exit 1;
die Identität dieses alten Commits mit einer squashintegrierten Änderung wird
nicht behauptet. Das ist keine notwendige Archivvoraussetzung.

## Konkreter späterer Betreiberplan

1. Taskbesitzer und Sitzungen prüfen; alle Writer zuverlässig ausschließen.
   Ohne diesen Nachweis HOLD. Der Pilot erhält hier keine laufende Freigabe.
2. Netzwerk/DNS in einer freigegebenen Betreiberumgebung herstellen. Noch kein
   Push: erst lesen, ob der vorgesehene Branch existiert und welchen SHA er meldet.
3. Bei fehlendem Branch einen Push gesondert freigeben; bei Abweichung Ursache
   prüfen. Kein Überschreiben eines abweichenden Remote-HEAD und kein Force-Push.
4. Nach gegebenenfalls manuellem Push exakten SHA erneut autoritativ prüfen.
5. Frischen CLI-Plan erzeugen und vollständig lesen. Erst danach einzelne
   Archivierung bewusst freigeben. Die CLI prüft unmittelbar vor Entfernung erneut
   und führt zuerst einen Restoreversuch in einem neuen temporären Repository aus.
6. PREPARED- und Abschlussdatensatz außerhalb des Worktrees dauerhaft sichern.
   Remote-Branch dauerhaft erhalten. Keine lokalen oder Remote-Branches löschen.

Lesende manuelle Identitätsprüfung mit Fehlerabbruch:

```bash
MAINT05_TREE=/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c2301
MAINT05_BRANCH=feat/c23-01-parsed-content-adr
git --no-optional-locks -C "$MAINT05_TREE" status \
  --porcelain=v1 --untracked-files=all --ignored=matching
git --no-optional-locks -C "$MAINT05_TREE" branch --show-current
git --no-optional-locks -C "$MAINT05_TREE" log -1 --oneline
MAINT05_LOCAL_SHA=$(git -C "$MAINT05_TREE" rev-parse HEAD) || exit 1
MAINT05_REMOTE_LINE=$(git -C "$MAINT05_TREE" ls-remote --refs origin \
  "refs/heads/$MAINT05_BRANCH") || exit 1
test -n "$MAINT05_REMOTE_LINE" || exit 1
# Exakte vollständige Zeile statt ungeprüftem cut/leerem Erfolg vergleichen:
MAINT05_EXPECTED_LINE=$(printf '%s\t%s' "$MAINT05_LOCAL_SHA" "refs/heads/$MAINT05_BRANCH")
test "$MAINT05_REMOTE_LINE" = "$MAINT05_EXPECTED_LINE" || exit 1
```

Bei vorhandenem sauberen Worktree genügt das nicht als Löschfreigabe: ignored Daten,
Indexflags, parallele Writer und Wiederherstellung gehören weiterhin zum Vertrag.
Der etwaige separat genehmigte Push lautet exakt:

```bash
git -C /home/robfra/0_Portfolio_Projekte/Personal_Assistant-c2301 push -u origin \
  HEAD:refs/heads/feat/c23-01-parsed-content-adr
```

Die vollständigen ausführbaren CLI-Befehle für Plan, bewusste Einzelgenehmigung,
Archivierung und Restore stehen im [Runbook](maint05_operator_runbook.md).
Dort sind die Variablen exakt auf diesen Piloten gesetzt. `archive` bleibt ohne
`--execute` ein Dry-Run. Die eigentliche normale Gitentfernung ist ausschließlich
innerhalb des später separat freigegebenen CLI-Aufrufs vorgesehen, nicht als
ungeprüfter Einzelbefehl in diesem Auftrag.
