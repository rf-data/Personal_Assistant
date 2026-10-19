# MAINT-04 – Sicherung und Restore ausschließlich nach Einzelgenehmigung

**Plan, null Ausführungen.** Keine Backup-/Recoveryroots sind freigegeben. Die
nachstehenden Befehle sind reviewbare Vorschläge, kein ausführbares Auftragsskript.
Nicht aus TSV generieren oder als Schleife ausführen. Jede ID benötigt Antrag S
und anschließend unabhängig Antrag R aus [den Einzelunterlagen](candidate_reviews.md).

## Minimaler Umfang je Objekt

| ID | Originalref / Scope | Commit | Tree | Vorgeschlagene Backupref | Bundle |
| --- | --- | --- | --- | --- | --- |
| BR001 | `refs/heads/add_audio_transcript` / Branch | `b3b59b66942e4470475cc41657f4caf515338c67` | `d4666e9beccf654753fc2759ec494b8a1fb3e182` | `refs/maint04-backup/BR001` | `BR001.bundle` |
| BR011 | `refs/heads/docs/cs50-archive` / Branch | `8ba519ed04c04c92573594ebe74b69a3c00aab1b` | `02356af525ef9ff6a5dc3ebf99a1e062a363ea50` | `refs/maint04-backup/BR011` | `BR011.bundle` |
| BR107 | `refs/heads/add_audio_transcript` / Remote-Ref | `b3b59b66942e4470475cc41657f4caf515338c67` | `d4666e9beccf654753fc2759ec494b8a1fb3e182` | `refs/maint04-backup/BR107` | `BR107.bundle` |
| BR109 | `refs/heads/add_local_LLM` / Remote-Ref | `b3b59b66942e4470475cc41657f4caf515338c67` | `d4666e9beccf654753fc2759ec494b8a1fb3e182` | `refs/maint04-backup/BR109` | `BR109.bundle` |
| BR110 | `refs/heads/add_organizer` / Remote-Ref | `b3b59b66942e4470475cc41657f4caf515338c67` | `d4666e9beccf654753fc2759ec494b8a1fb3e182` | `refs/maint04-backup/BR110` | `BR110.bundle` |
| BR111 | `refs/heads/add_runpod` / Remote-Ref | `d35c43fb698a5f015e56b067fa9f22ad8c459edf` | `a26235de330eb2c07ca0b7b21fd83c98c92df235` | `refs/maint04-backup/BR111` | `BR111.bundle` |

Je Bundle vollständige erreichbare Historie einschließlich Eltern und Gitblobs,
keine Bereichsausschlüsse oder Thin-Bundle-Voraussetzungen. Separate Belegdatei:
ID, Repo/origin, Scope, Originalref, Commit/Tree, Backupref, erreichbare Commitzahl,
Bundlegröße/SHA256, Gitversion, Verantwortlicher, Zeit, genehmigter privater Root,
Zugriffs-/Retentionbedingungen und Restoreprotokoll. Gemeinsame Objekte erlauben
keine gemeinsame Remove-Entscheidung; BR001/BR107 bleiben getrennt genehmigt.
Ein Bundle ist keine Sicherung von Worktrees, Branchkonfiguration, Index,
untracked/ignorierten Dateien, Credentials oder externen Artefakten.

## Antrag S: Ablauf nach Freigabe

1. Betreiber benennt je ID die exakten **neuen privaten** Backup-/Recoveryziele
   außerhalb beider Repositories, Owner/Scope/Retention und Fenster. Keine
   vermuteten Standardpfade. Per `lstat` alle Eltern/Ziele und private Rechte
   prüfen: keine Symlinks, kein Wiederverwenden/Überschreiben bestehender Ziele.
   Unbekannte Daten oder Eigentümerschaft stoppen. Keine Originaldaten kopieren.
2. Origin/Common-Gitdir, Default-SHA, exakten lokalen oder Live-Remote-SHA,
   PR-Heads/-Bases, Worktrees und bestätigte Nichtnutzung erneut prüfen.
   Commit/Tree muss exakt der einzeln genehmigten Zeile entsprechen; neue
   Abhängigkeit oder Änderung verlangt neue Entscheidung. Backupref muss fehlen.
3. Ausschließlich die eine genehmigte neue Backupref mit erwarteter Abwesenheit
   erstellen; keine Änderung des Originalrefs. Bundle aus genau dieser Ref
   herstellen, privat synchronisieren und Größe/SHA256 protokollieren.
4. `bundle verify` und `bundle list-heads` prüfen. Das ist noch **kein Restoretest**.
   Bundle muss eigenständig sein und genau den vorgesehenen Head enthalten.
5. In einem eigens genehmigten neuen leeren privaten Testrepository wiederherstellen,
   ohne Working-Tree-Checkout, Hooks oder extrahierten Code auszuführen. Commit,
   Tree, erreichbare Commitzahl und Objektclosure verifizieren; `git fsck --full`
   protokollieren. Bundle-SHA256 vorher/nachher identisch prüfen.
6. Tatsächlichen Restorebeleg vom Betreiber prüfen lassen. Bei Fehler keine
   Löschung, keine automatische Reparatur oder Ausweitung. Backup-/Testroots
   bleiben nach ihrer eigenen Aufbewahrungsfreigabe erhalten; kein rekursives Clean.

Nur als konkretes, **nicht ausgeführtes** Beispiel für Antrag S von BR001:
`MAINT_BACKEND_REPO` muss das identifizierte Backend bezeichnen.
`MAINT_BACKUP_ROOT` und `MAINT_RECOVERY_ROOT` werden ausschließlich aus der
separaten Betreiberfreigabe gesetzt; sie haben hier bewusst keinen Wert.
Die nachstehend benannten Unterziele müssen davor als neu/privat geprüft sein.

```sh
git -C "$MAINT_BACKEND_REPO" update-ref refs/maint04-backup/BR001 b3b59b66942e4470475cc41657f4caf515338c67 0000000000000000000000000000000000000000
git -C "$MAINT_BACKEND_REPO" bundle create "$MAINT_BACKUP_ROOT/BR001.bundle" refs/maint04-backup/BR001
git -C "$MAINT_BACKEND_REPO" bundle verify "$MAINT_BACKUP_ROOT/BR001.bundle"
git -C "$MAINT_BACKEND_REPO" bundle list-heads "$MAINT_BACKUP_ROOT/BR001.bundle"
sha256sum "$MAINT_BACKUP_ROOT/BR001.bundle"
# Erst nach separater Root-/Restorefreigabe:
git init --bare "$MAINT_RECOVERY_ROOT/BR001.git"
git -C "$MAINT_RECOVERY_ROOT/BR001.git" fetch --no-tags "$MAINT_BACKUP_ROOT/BR001.bundle" refs/maint04-backup/BR001:refs/heads/recovered-BR001
git -C "$MAINT_RECOVERY_ROOT/BR001.git" rev-parse refs/heads/recovered-BR001
git -C "$MAINT_RECOVERY_ROOT/BR001.git" rev-parse 'refs/heads/recovered-BR001^{tree}'
git -C "$MAINT_RECOVERY_ROOT/BR001.git" rev-list --count refs/heads/recovered-BR001
git -C "$MAINT_RECOVERY_ROOT/BR001.git" fsck --full
```

Erwartet BR001: Commit `b3b59b66942e4470475cc41657f4caf515338c67`,
Tree `d4666e9beccf654753fc2759ec494b8a1fb3e182`, 53 erreichbare Commits.
Andere IDs nur nach eigener Genehmigung mit ihren **eigenen** Ref-/Bundle-/Restore-
Namen und vollständigen Commit-/Treebindungen aus obiger Tabelle. BR011: 120,
BR107/109/110: je 53, BR111: 35 erreichbare Commits. SHA256 bleibt überall
**nicht vorhanden**, bis ein reales erlaubtes Bundle erzeugt wurde.

## Antrag R: spätere Löschung und mögliche Wiederanlage

Erst nach abgeschlossenem Antrag S darf der Betreiber separat genau einen Ref zur
Entfernung genehmigen: ID, Repo, Scope, vollständiger Ref und aktueller SHA,
Nichtnutzung, Dokument-/Datenentscheidung, Backup-/Restorebeleg, verantwortliche
Person, Fenster und exakter Einzelbefehl. Die [MAINT-02-Matrix](../maint02/execution_plan.tsv)
enthält historische SHAgesicherte Vorschläge; sie sind weiterhin keine Ausführungsliste.
Lokal nur erwarteten Alt-SHA akzeptieren, remote ausschließlich exakte SHA-Lease
für eine einzelne Löschrefspec; keine pauschale Force-Push-Freigabe. Neue PR-/
Worktreebindung, geänderter SHA oder unklare Berechtigung stoppt jede Aktion.

Eine spätere Wiederanlage ist eine weitere explizite Restoreaktion: geprüfte
Backupobjekte, exakter Commit und ausschließlich zuvor fehlender Originalref
(Null-OID bzw. remote Abwesenheitslease); vorhandene neuere Refs nie überschreiben.
Sie rekonstruiert weder offene PRs noch Branchkonfiguration oder private Dateien.
Kein GC/Prune, kein Stashzugriff und keine `.git/worktrees`-Reparatur als Nebenwirkung.

**Iststand aller sechs IDs:** Antrag S offen; Backupref/Bündel/Restoretest nicht
erstellt; Antrag R offen; null ausgeführte Removebefehle. Die vorgesehenen
Sicherungsrefnamen sind bislang nur Text, keine Gitrefs.
