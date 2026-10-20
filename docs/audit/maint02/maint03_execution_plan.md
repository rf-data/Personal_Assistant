# MAINT-03 – Einzelentscheidungen vor jedem Eingriff

**Vorbereitung, keine Ausführungsfreigabe.** Keine Zeile automatisch aus TSV lesen
und ausführen. Kein Sammelcleanup. Alle vorgeschlagenen Refbefehle sind ausschließlich
für einen neuen ausdrücklich genehmigten MAINT-03-Auftrag dokumentiert; das aktuelle
Verbot für Force-Push/Prune/Löschen bleibt unberührt.

## Konkrete Freigabematrix

[execution_plan.tsv](execution_plan.tsv) enthält 239 eindeutig typisierte Objekte:
147 Branchzeilen, 46 Worktrees, 46 Cache-Refs. 30 reine Graphprüfkandidaten besitzen
einen bedingten Branchrefbefehl; Schutz/offene PRs/attached Worktrees erhalten keinen.
Die sechs ursprünglichen leichter prüfbaren Fälle sind in
[original_stale_candidates.md](original_stale_candidates.md) einzeln identifiziert.
**Kein Remove, kein ready_for_removal=true und kein erstelltes Backup.**

Der Operator muss je ID und unverändertem SHA entscheiden:

1. **Keep** für Primaries, C24-06-A mit UI, dirty/untracked Arbeit, offene PRs,
   PM-01/MAINT-01-Historie, unmerged Unique Work und Stashes bestätigen.
2. Für **Review** Eigentümer, Aufgaben-/Prozess-/Linkbedarf und private/ignorierte
   Daten klären. Verwaiste Registrierung ist keine Freigabe. Fehlende Antwort
   bedeutet Keep, niemals stillschweigende Zustimmung.
3. Für **Archive** (33 treegleiche Zusatzcommitzeilen) fachlichen Erhaltungsumfang
   entscheiden; exakte Commitidentität vor möglichem späterem Refabbau sichern.
   Acht treeverschiedene Zusatzcommitzeilen bleiben Review. Patchgleichheit allein
   ersetzt keine Archiv-/Dokumententscheidung.
4. Nur nach bestandenem frischem Prüflauf, verifizierter privater Sicherung und
   bestätigter Nichtnutzung eine explizite **Remove**-Entscheidung außerhalb dieses
   Snapshots geben: ID, Repo, Typ, voller Ref/Pfad, beobachteter SHA, Sicherungsbeleg,
   Restorebeleg, erlaubter Einzelbefehl, Verantwortlicher und Zeitfenster.
5. Die zehn ungültigen Registrierungen separat entscheiden: Mount/Umbenennung/
   Reparatur oder neuer committed Checkout. Kein Registryabbau als Nebenwirkung
   einer Branchentscheidung. Bestehende Restverzeichnisse nicht überschreiben.

## Private Sicherung vor möglicher Refentfernung

Roots ausschließlich durch den Operator bestimmen. In Befehlen:
`MAINT_BACKEND_REPO=$WORKSPACE/gmp_compliance`,
`MAINT_UI_REPO=$WORKSPACE/personal-assistant-ui`; Pfadaliases gemäß README auflösen.
`MAINT_BACKUP_ROOT` und `MAINT_RECOVERY_ROOT` müssen neue private explizite Roots
außerhalb beider Repositories sein. Nie auf bekannte Arbeitsverzeichnisse richten.
Keine Symlinks, keine Überschreibung, kein pauschaler Verzeichnisexport.

Beispiel **nur** für den genau identifizierten lokalen Kandidaten BR001
`add_audio_transcript` bei unverändertem
`b3b59b66942e4470475cc41657f4caf515338c67`. Vor Umsetzung prüfen, dass BR001 weiterhin
auf diesen Ref verweist. Dies ist keine bereits ausgeführte Sicherung:

```sh
# Eigene neue Backupref; Null-OID verlangt vorherige Abwesenheit.
git -C "$MAINT_BACKEND_REPO" update-ref refs/maint03-backup/BR001 b3b59b66942e4470475cc41657f4caf515338c67 0000000000000000000000000000000000000000
# Vorher per lstat bestätigen: Ziel neu, privat und nicht vorhanden.
git -C "$MAINT_BACKEND_REPO" bundle create "$MAINT_BACKUP_ROOT/BR001.bundle" refs/maint03-backup/BR001
git -C "$MAINT_BACKEND_REPO" bundle verify "$MAINT_BACKUP_ROOT/BR001.bundle"
git -C "$MAINT_BACKEND_REPO" bundle list-heads "$MAINT_BACKUP_ROOT/BR001.bundle"
sha256sum "$MAINT_BACKUP_ROOT/BR001.bundle"
```

Für andere IDs jeweils eigene explizite Backupref/Datei und Tabellen-SHA verwenden;
keine automatisierte Schleife. Bundleinhalt enthält erreichbare Historie, eventuell
vertrauliche alte Dateien: Scope, Speicherrechte und Aufbewahrung autorisieren.
Bundleverify ist kein Dateisystem-Restoretest. Nach Freigabe in einem neuen leeren
privaten Testrepository wiederherstellen und exakten Commit/Tree prüfen; erst dann
Backupbeleg mit SHA256, Ref/Head, Repoidentität und Restoreprotokoll bestätigen.
Nichtversionierte Dateien und Worktree-/Indexmetadaten benötigen einen separaten
operatorgeführten Sicherungsweg; ein Bundle enthält sie nicht. Kein fremdes
Verzeichnis oder gesamte `.git`-Struktur automatisch kopieren.

## Unmittelbar vor dem einzelnen Refbefehl

- Repository/Origin/Common-Gitdir, lokalen vollständigen Ref und Live-Default erneut
  lesen. Netzwerkfehler ist unbekannt, nicht fehlender Branch. Livebranch über
  `git ls-remote --exit-code --heads origin refs/heads/<exakter-name>` prüfen.
- `merge-base`, `rev-list`, `git cherry`, tatsächlichen gemergten PR-Headtree sowie
  offene PR-Heads/**Bases** neu prüfen. Änderung irgendeines SHA/Abhängigkeit:
  stoppen und neue Entscheidung dokumentieren.
- `GIT_OPTIONAL_LOCKS=0 git -c gc.auto=0 -c core.fsmonitor=false -c core.untrackedCache=false ...`
  für reine Statusprüfungen; keine alten Trackingrefs als Livebeweis.
- Alle Worktreebindungen, Owner-Nichtnutzung und zulässige Inhalte prüfen.
  Lokales `update-ref` umgeht den Worktree-Löschschutz von `git branch -d`;
  deshalb exklusives Betreiberfenster und ausdrücklicher unmittelbar aktueller
  Nichtnutzungsnachweis. Kein automatisches Lockübernehmen oder Zeitablaufrecht.
- Erst dann exakten Einzelbefehl der freigegebenen Zeile verwenden. Jeder lokale
  Refbefehl nennt erwarteten alten SHA (Compare-and-swap). Remoteentfernung nennt
  `--force-with-lease=refs/heads/<name>:<observed-SHA>` und ausschließlich die
  Löschrefspec `:refs/heads/<name>`. Kein `--force` und kein implizites Lease.
  Das ist ausschließlich ein späterer SHA-gesicherter Löschvorschlag, kein Auftrag
  zu einem heutigen Force-Push oder zur Umschreibung von Commits.
- Rollback erfordert geprüfte Backupobjekte. Null-OID schützt lokale Neuanlage
  gegen Überschreiben eines inzwischen entstandenen Refs. Remoteleere Erwartung
  schützt die Wiederanlage gegen vorhandenen neuen Branch. Neuer Konflikt: stoppen,
  keine fremde Arbeit zurücksetzen. Refrestore stellt keine Branchkonfiguration,
  offene PRs oder nichtversionierte Dateien automatisch wieder her.

Die exakten Branch-/Cachebefehle und gebundenen Wiederherstellungsbefehle stehen
je Zeile im TSV. Leeres `cleanup_command` bedeutet **kein derzeit verantwortbarer
konkreter Löschbefehl**. Das betrifft alle Worktrees/Registrierungen und geschützte
Refs. Kein globales `fetch --prune`/`worktree prune`, keine rekursive Löschung,
keine manuellen Eingriffe in `.git/worktrees`, keine Stashänderung.

Git-Spezifikation: [update-ref](https://git-scm.com/docs/git-update-ref) für
SHA-gebundene lokale Refänderung, [push](https://git-scm.com/docs/git-push) für
explizite Lease-Erwartungen und [worktree](https://git-scm.com/docs/git-worktree)
für saubere Entfernung/Reparatur. Diese Referenzen begründen die Syntax,
**keine ausgeführten destruktiven Tests oder Nutzungsgenehmigungen**.

## Nach einem später autorisierten Eingriff

Genau den betroffenen Ref/Pfad und Livezustand erneut prüfen, alte/neue SHAs und
Backupbeleg protokollieren; alle geschützten Refs, Worktree-HEADs/-Status und Stashes
gegen den freigegebenen Vorzustand vergleichen. Bei Abweichung anhalten. Keine
automatischen Folgeeingriffe, kein GC/Prune, kein Zusammenfassen mehrerer
Genehmigungen oder Schließen/Mergen anderer PRs.
