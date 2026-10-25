# MAINT-05: Sicherheitsvertrag

Stand: 25.10.2026. Auftrag: audit + implementation + synthetic validation.
**Keine reale Archivierung freigegeben oder ausgeführt.** Issue [#165](https://github.com/rf-data/Personal_Assistant/issues/165).

## Nachweisstufen

| Aussage | Erforderlicher Nachweis | Was daraus nicht folgt |
| --- | --- | --- |
| Commit existiert auf GitHub | GitHub-Commitabfrage oder erfolgreicher Abruf aus dem richtigen Repository | Ein dauerhafter Branch referenziert ihn |
| Commit über Backupbranch erreichbar | Autoritatives `ls-remote` plus nachgewiesene Abstammung bzw. isolierter Fetch | Branch-HEAD ist identisch |
| Exakte HEAD-Gleichheit | Erfolgreiches `ls-remote` für genau `refs/heads/<branch>` und vollständiger SHA-Vergleich | Lokale Zusatzdateien sind gesichert |
| Keine zusätzlichen ungesicherten Dateien | Vollständiger Status einschließlich ignored/untracked, zusätzliche `ls-files`-Prüfungen, keine riskanten Indexflags/Submodule | Fremde Writer bleiben während der Entfernung inaktiv |
| Wiederherstellung nachgewiesen | Neuer isolierter Fetch, SHA-Prüfung, `fsck --full`, vollständiger Checkout des gesicherten Commits | Remote-Branch wird künftig nie gelöscht |

Ein Merge nach master ist keine Voraussetzung. Ein expliziter eigener Remote-Branch
kann den vollständigen Commitgraphen referenzieren. Dauerhafte Aufbewahrung dieses
Branches und der Archivdatensätze bleibt eine Betreiberpflicht. GitHub-PR-Metadaten,
lokales `origin/...`, früherer Push oder Commitexistenz ersetzen keinen aktuellen
`ls-remote`-Nachweis. Ein Fehler/Timeout ist `unverified`, erfolgreiche leere Ausgabe
für die exakte Referenz ist `missing`. Ahead/behind gegenüber einem lokalen
Trackingref wird getrennt von einem autoritativ beobachteten Remote-SHA ausgewiesen.
Bei fehlenden lokalen Objekten bleiben Remote-Abstammung und Zähler unbekannt.

## Klassifizierung

Mehrere Klassen können gleichzeitig gelten:

| Klasse | Bedeutung |
| --- | --- |
| `PROTECTED_ACTIVE` | Primärcheckout, fest geschützter Name, aktuelles Kontrollworktree, expliziter `--protect`-Pfad, Worktree-Lock oder positiver Prozess-CWD-Nachweis |
| `DIRTY` | Änderungen an versionierten Dateien, einschließlich gestagter Änderungen/Konflikte |
| `UNTRACKED_OR_IGNORED_RISK` | Zusätzliche untracked/ignored Pfade, auch leere Verzeichnisse; keine pauschale Ausnahme für Caches oder Venvs |
| `DETACHED_HEAD` | Keine eindeutige lokale Branchidentität; diese Version entfernt solche Worktrees grundsätzlich nicht |
| `REMOTE_MISSING` | Erfolgreiche autoritative Abfrage, Backupref fehlt |
| `REMOTE_MISMATCH` | Autoritatives Branch-HEAD weicht vom lokalen HEAD ab |
| `REMOTE_UNVERIFIED` | Remote, Ref oder vollständige Antwort nicht nachgewiesen |
| `PR_OR_MERGE_UNVERIFIED` | CLI führt keine automatische GitHub-/Taskfreigabe durch; separates Betreiberreview nötig |
| `CANDIDATE_FOR_ARCHIVE` | Technische Vorprüfung erlaubt eine spätere Prüfung; weder Operatorfreigabe noch Entfernung oder Restorebeweis |
| `ARCHIVE_VERIFIED` | Ausschließlich erfolgreicher Ausführungspfad: frischer Remote-/Statusnachweis, isolierter Wiederherstellungstest, Freigabe, normale Entfernung und bestätigte Nachbedingungen |

`check` und `archive` ohne `--execute` können niemals `ARCHIVE_VERIFIED` vergeben.
`PR_OR_MERGE_UNVERIFIED` verbietet keine Archivierung allein wegen fehlendem Merge.
Der Betreiber muss aber Taskbesitzer, offene PRs und laufende Sitzungen geprüft haben,
bevor er eine Freigabe erteilt. Die CLI authentifiziert keine Betreiberidentität;
der exakte Approvaltext ist eine bewusste lokale Bestätigung, keine Signatur.

## Ablauf der Implementierung

1. Exakter absoluter, registrierter Pfad ohne Symlinkkomponenten; gleicher gemeinsamer
   Gitdir, passende Branch-/HEAD-Identität. Primärcheckout und bekannte aktive Namen
   sind fest geschützt. Zusätzliche Pfade mit `--protect`, zusätzliche Backupbranches
   mit `--protected-backup-branch` schützen. `master` und `main` sind immer gesperrt.
2. Vollständiges NUL-Statusformat, untracked und ignored Verzeichnisse separat.
   `ls-files -v` blockiert assume-unchanged/skip-worktree und andere nicht normale
   Indexeinträge. Submodule benötigen einen gesonderten Vertrag und blockieren.
   Gitstatus-/Parsingfehler führen zu HOLD. Keine privaten Dateiinhalte werden gelesen.
3. Benannter Remote wird einmalig zu einer eindeutigen URL aufgelöst; Backupref ist
   explizit. URL, Pfadinode, Branch, SHA, Status und Backupref gehen in den Planhash ein.
   Die Inventur darf pro URL einen gemeinsamen `ls-remote --heads`-Snapshot verwenden.
   `check` und jede Ausführungsprüfung benutzen frische exakte Einzelabfragen.
4. Ausführung verlangt gespeicherten geeigneten Plan, `--execute`, exakten
   `ARCHIVE <planhash>` und `--exclusive-writers ALL_WRITERS_STOPPED`.
5. Gemeinsamer nicht blockierender `flock` im Gitdir verhindert parallele Aufrufe
   dieser CLI. Die Lockdatei bleibt erhalten, damit kein Unlink einen zweiten
   Lockinode ermöglicht. Fremde Gitwerkzeuge beachten diesen Lock nicht.
6. Neue komplette Prüfung, dann temporärer `git worktree lock` mit eigenem Grund.
   Wiederherstellungsprobe ausschließlich in einem neuen temporären Repository:
   Fetch des Backupbranches, SHA-Abgleich, Objektprüfung und vollständiger Checkout.
   Dies bestätigt Gitinhalte, nicht die Verfügbarkeit externer LFS-/Submoduldaten.
7. Ein neuer unveränderlicher PREPARED-Datensatz wird vor der Entfernung geschrieben
   und mit Datei-/Verzeichnis-fsync gesichert. Er liegt außerhalb des Zielworktrees
   und der Gitmetadaten. Er enthält ursprünglichen Pfad/Branch, gesicherten SHA,
   Remote-URL/-Ref, Wiederherstellungsbeleg und Restoreanweisung.
8. Nur eigenen Worktree-Lock freigeben. Danach Status, HEAD, Branch, Pfadidentität,
   Remote-URL und exakten Remote-SHA erneut prüfen. Ausschließlich gewöhnliches
   `git worktree remove <exakter-pfad>`; keine Force-/Clean-/Prune-Alternative.
9. Fehlenden Pfad und fehlende Registrierung nachprüfen. Erst dann separaten neuen
   Datensatz `<receipt>.completed.json` mit `ARCHIVED`/`ARCHIVE_VERIFIED` schreiben.
   Lokale und Remote-Branches werden von der Archivierung nicht verändert.

## Konkurrenz und Fehlergrenzen

**Keine garantierte atomare Sicherheit gegenüber fremden Prozessen.** Worktree-Locks
sperren administrative Gitoperationen, keine Editoren, Hintergrundjobs oder direkten
Dateischreibzugriffe. `/proc/*/cwd` ist nur positive Evidenz, kein vollständiges
Sitzungsinventar. Prozesse können trotz anderem CWD offene Dateien schreiben.
Zwischen letzter Prüfung und `worktree remove` bleibt ein Zeitfenster. Insbesondere
ignored Dateien können von Git bei normaler Entfernung mit entfernt werden. Daher
muss der Betreiber ALLE Writer tatsächlich ausschließen, einschließlich IDE,
Terminals, Codex, Jobs und Hintergrunddienste. Ist das nicht zuverlässig möglich:
**HOLD**, auch bei technisch sauberem Plan. Die CLI stoppt keine Sitzung selbst.

Ein Remote-Branch kann ebenfalls nach der letzten Abfrage verändert werden. Die
CLI reserviert ihn nicht serverseitig. Betreiberseitige unveränderliche Aufbewahrung
und zusätzliche Backups bleiben sinnvoll; die CLI pusht oder schützt keine Branches.
Ein nachträglich manipuliertes Repository/Config, privilegierte Angreifer oder
unzuverlässige Dateisystem-/fsync-Semantik sind keine abgedeckte Vertrauensgrenze.

Ein Fehler während Fetch/Prüfung/Entfernung führt zu HOLD. Nach unklarem Ausgang
nie automatisch wiederholen. Bei PREPARED ohne Abschlussdatensatz zuerst tatsächliche
Registrierung, Pfad, Remote-SHA und eigene Lockidentität prüfen. Der Restorebefehl
akzeptiert nur einen verifiziert abgeschlossenen Datensatz; eine manuelle
Rekonstruktion aus PREPARED braucht eine neue Betreiberentscheidung. Ein fremder
oder verlorener Worktree-Lock wird nicht automatisch entsperrt. Temporäre
Recovery-Repositories enthalten nur neu erzeugte synthetische Gitdaten.

## Konventionen und Scope

Vor Implementierung geprüft: `scripts/repository_audit.py`, dessen Regressionstests,
`src/utils/general_helper.py`, bestehende argparse-Skripte und `pyproject.toml`.
Es gibt keine vorhandene sichere Archiv-/Restorefunktion. Die bestehende Audit-CLI
bleibt unverändert; ihr Runner ohne Timeout/Fehlerdetails und ihr zeilenbasiertes
Worktreeparsing genügen diesem Löschvertrag nicht. Die neue CLI verwendet dasselbe
argparse-/JSON-/pytest-Muster und nur die Standardbibliothek. Die Dokumenterstellung
verwendet die vorhandene `repository_audit.safe_name`-Redaktionsregel.

Keine Push-/Branchlösch-/Merge-/Deploymentfunktion implementiert. Restore ist eine
separat freizugebende lokale Schreiboperation: expliziter freier Zielpfad,
autoritative erneute SHA-Prüfung, Fetch ohne Remote-Trackingaktualisierung,
keine Änderung bestehender Branches. Ein fehlender Originalbranch kann neu
angelegt werden; ein abweichender oder anderweitig ausgecheckter Branch blockiert.
