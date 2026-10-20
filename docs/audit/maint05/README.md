# MAINT-05 – Autorisierte Git-Sicherung und unabhängiger Restore verifiziert

19.10.2026, Europe/Berlin. **`backup_restore_verified` für alle sechs Kandidaten.**
Ein gemeinsames vollständiges Git-Bundle, sechs getrennte Sicherungsrefidentitäten,
zwei neue private Bare-Testrepositories. **Keine Bestandslöschung oder Freigabe
zur Entfernung; überall `ready_for_removal=false`.**

[Maschinenlesbare Einzelergebnisse](backup_restore_status.tsv),
[integrierte MAINT-04-Grundlage](../maint04/README.md),
[Einzelreviews](../maint04/candidate_reviews.md),
[unveränderte Freigabematrix](../maint04/approval_matrix.tsv) und
[bisheriger Sicherungsplan](../maint04/backup_restore_plan.md).

## Integration und begrenzte erneute Prüfung

PR [#119](https://github.com/rf-data/Personal_Assistant/pull/119) ist tatsächlich
gemergt, Mergecommit `857d8e44944d1680997b0b31b2336540bcb2faad`.
Alle vier MAINT-04-Dokumente auf dem geprüften master
`a4f405bfa7b7f1d04967fd6027587a68604ffadd` sind gitblobidentisch mit dem
PR-Head `37115b2b189f05562f6fd60f3951013ce5a145cc`. Kein bloß geschlossener PR
als Integrationsbeleg; die integrierten Unterlagen wurden verwendet.

Nur die sechs Kandidaten erneut geprüft: lokale bzw. tatsächliche Live-Refs per
`git ls-remote`, unveränderte SHAs, Repo-/Common-Gitdirbindung, vollständig
paginierte offene PR-Heads/-Bases und registrierte Worktreebindungen. Keine neue
PR-/Worktreebindung und kein neuer Nutzungshinweis in diesen Metadaten.
Externe Betreiber-/Prozessnutzung bleibt ungeprüft; daraus folgt keine Nichtnutzung
oder Löschfreigabe. Keine Wiederholung der allgemeinen MAINT-04-Inventur oder
semantischen Dokumentbewertung. Unmittelbar vor Sicherung und beim Restorefortsatz
wurden die Kandidatengates nochmals gelesen, nachher alle sechs SHAs erneut bestätigt.

## Tatsächliche Betreiberfreigabe und Schutz der Ziele

Der Betreiber **robfra** hat in diesem Auftrag alle sechs IDs, ihre vollständige
erreichbare Git-Historie sowie die gemeinsame technische Sicherung ausdrücklich
freigegeben. Die beiden exakten privaten Zielroots wurden vom Betreiber benannt;
sie werden hier nur als `BACKUP_ROOT` und `RECOVERY_ROOT` referenziert.
Die privaten Belege `authorization.json`, `manifest.json`,
`bundle_verification.json` und `restore_verification.json` enthalten die konkrete
Zuordnung. Keine privaten Roots, Bundlebytes, historischen Volltexte oder Secrets
werden in diesen Repositorybericht oder PR-Artefakte übernommen.

Vor Beginn waren **beide Zielroots nicht vorhanden**. Elternpfade wurden mit
`lstat` auf Verzeichnistyp, Symlinks, Eigentümerschaft unter dem Betreiberhome und
fehlende Gruppen-/Fremdschreibrechte geprüft. Neue Eltern/Ziele wurden exklusiv
angelegt; kein bestehender Zielroot akzeptiert, überschrieben oder bereinigt.
Lokale Ausführung als robfra/UID 1000. Neue private Verzeichnisse **0700**, sämtliche
Dateien **0600**; abschließend 25 Verzeichnisse und 28 Dateien geprüft.

Freier Speicher vor Ausführung rund 3,17 GB; 2.344 erreichbare Git-Objekte mit
44.626.969 unkomprimierten Bytes. Vorprüfung verlangte viermal diese Größe plus
64 MiB Reserve (245.616.740 Bytes). Aufbewahrung aller Backup-/Recoverydaten bis
zu einer **gesonderten ausdrücklichen Betreiberentscheidung**; kein Ablaufdatum,
keine automatische Löschung. Untracked/ignorierte/private Arbeitsdateien wurden
nicht erfasst; die Freigabe betrifft ausschließlich die benannte Git-Historie.

## Bundle und Einzelresultate

Datei `BACKUP_ROOT/candidates.bundle`, **3.590.154 Bytes**, SHA256:

```text
2668a65e21076be155238c298a92b771cbbcfc1b3c11e22745f596f5f482fe08
```

Die sechs Sicherungsrefs `refs/maint05-backup/<Candidate-ID>` befinden sich
**ausschließlich** im neu angelegten privaten Verpackungsrepository, nicht im
Quellrepository. Git durfte dessen Originalobjekte während der Bundleerzeugung
lesen; keine dauerhafte Alternatesdatei wurde angelegt. Das Bundle enthält alle
sechs Headidentitäten und **keine Prerequisites**. BR001/107/109/110 besitzen
weiterhin denselben Commit, behalten aber vier gesonderte Entscheidungszeilen.
BR011 und BR111 sind als weitere Commitidentitäten im selben vollständigen Bundle.

| ID | Erwarteter = beobachteter = restaurierter Commit | Freigabe / Bundle | Restore ausgeführt / erfolgreich | Historie (Commits) | Status |
| --- | --- | --- | --- | ---: | --- |
| BR001 | `b3b59b66942e4470475cc41657f4caf515338c67` | Ja / Ja | Ja / Ja | 53 | backup_restore_verified |
| BR011 | `8ba519ed04c04c92573594ebe74b69a3c00aab1b` | Ja / Ja | Ja / Ja | 120 | backup_restore_verified |
| BR107 | `b3b59b66942e4470475cc41657f4caf515338c67` | Ja / Ja | Ja / Ja | 53 | backup_restore_verified |
| BR109 | `b3b59b66942e4470475cc41657f4caf515338c67` | Ja / Ja | Ja / Ja | 53 | backup_restore_verified |
| BR110 | `b3b59b66942e4470475cc41657f4caf515338c67` | Ja / Ja | Ja / Ja | 53 | backup_restore_verified |
| BR111 | `d35c43fb698a5f015e56b067fa9f22ad8c459edf` | Ja / Ja | Ja / Ja | 35 | backup_restore_verified |

Bundle-SHA256 gilt für jede Zeile. Die TSV enthält zusätzlich die vollständigen
Quell-/Restore-Tree-SHAs, Objektzahlen und SHA256 der sortierten erreichbaren
Objektidentitäten. Diese sind je Kandidat identisch. Lokale Originalrefs wurden
in `RECOVERY_ROOT/local.git`, Remote-Originalrefs in `RECOVERY_ROOT/remote.git`
unter ihrem exakten `refs/heads/...`-Namen rekonstruiert. So bleiben die beiden
`add_audio_transcript`-Scopes getrennt wiederherstellbar; keine GitHub-Remote-
Ref wurde angelegt oder verändert.

## Ausgeführter unabhängiger Restore

Beide Bare-Repositories wurden neu und leer mit deaktivierten System-/Global-
Gitkonfigurationen und leerem Template erzeugt. Fetch ausschließlich aus der
Bundledatei in die exakten Originalrefnamen, kein Checkout, Hook oder extrahierter
Code. `GIT_ALLOW_PROTOCOL=file`; keine Download-/Netzwerkquelle für den Restore.

Vorhandenes Bubblewrap blendete während **jedes Restore-Gitkommandos** den ganzen
ursprünglichen Workspace und das Verpackungsrepository mit leeren Mounts aus.
Als persistenter Schreibbereich war ausschließlich der neue Recoveryroot
eingebunden; das Bundle blieb read-only. Die Original-
Objektwurzel war im isolierten Prozess nachweislich nicht vorhanden. Keine
Alternates-Umgebung, keine lokalen/HTTP-Alternatesdateien, keine ursprüngliche
Repositorykonfiguration als Rückgriff. Keine Netzwerknamespace-Isolation behauptet:
deren Vorprüfung war lokal nicht verfügbar; Git erlaubte nur Dateitransport.

In **jedem leeren Testrepository** wurde `git bundle verify` vor dem Fetch
erfolgreich ausgeführt; anschließend `git fsck --full --no-reflogs` mit Exit 0.
Alle sechs Ref-SHAs, Tree-SHAs, Commitzahlen, Objektzahlen und die vollständigen
sortierten erreichbaren Objektmengen wurden mit der Quelle verglichen.
Bundlegröße/SHA256 vor und nach den Restores unverändert. Private Receipts halten
Verify-/Fsckausgaben und tatsächlich ausgeführte Schritte fest. **Bundleverify
allein wurde nicht als erfolgreicher Restore gezählt.**

Der erste isolierte Start scheiterte vor Repositoryanlage beim Öffnen von
`/dev/null`. Die Recoverywurzel war danach weiterhin leer. Die isolierte Geräte-
zuordnung wurde korrigiert; das vorhandene Bundle erneut hashgeprüft und die noch
nicht existierenden Testrepositories angelegt. Kein Teilrepository übernommen,
kein Backup überschrieben und kein Fehler als Erfolg ausgewiesen.
Der private Erstversuchsbeleg bleibt erhalten; die sechs erfolgreichen tatsächlichen
Restores stammen aus dem abschließenden Lauf.

## Schutz, verbleibende Entscheidungen und Dokumentation

Erneuter Vergleich nach Ausführung: lokale Refs/Trackingrefs, Worktree-
Registrierungen, Primär-HEADs/-Status und Stash-IDs in Backend und UI unverändert.
Vier Remote-Kandidaten live erneut SHAidentisch. Keine Änderung aktiver Worktrees,
produktiver Daten, anderer MAINT-Objekte, Draft-PRs oder Bestandsrefs; kein Prune,
Clean, Reset, Force-Push, Stashänderung oder Löschen. Das Verpackungsrepository und
beide Testrepositories samt allen Sicherungsdaten bleiben privat erhalten.

Die historischen Dokument-/Datenrisiken aus MAINT-04 bleiben bestehen:
BR001/107/109/110 je drei dort ausgewiesene Fassungen, BR011 neun, BR111 zwei.
Diese Zahlen sind **übernommene MAINT-04-Befunde**, kein neuer Fachreview.
Eine Git-Historiensicherung ersetzt weder eine Entscheidung über Direktlinks/
Nichtnutzung noch eine Sicherung nichtversionierter Daten. Keine fehlenden
Backupfreigaben mehr; die separate spätere Entscheidung über Erhaltungsbedarf
und eine etwaige Entfernung ist weiterhin **nicht erteilt**.

Nächster Schritt: Betreiber prüft die privaten Bundle-/Restorebelege und entscheidet
gegebenenfalls **pro Candidate-ID** über ein neues ausdrückliches Verfahren.
Auch jetzt bleibt für alle sechs `ready_for_removal=false`. Keine automatische
Folgebereinigung und keine Zusammenlegung späterer Entscheidungen durch das
technisch gemeinsame Bundle.

Dieser Bericht ergänzt nur `docs/audit/maint05/`; MAINT-01/02/03/04 bleiben byte-
unverändert. Dokumentationsintegration über regulären eigenen PR, kein automatischer
Merge. Der eigene neue Dokumentationsbranch bleibt bis zu dessen verifiziertem
Merge erhalten; kein neuer lokaler Arbeitsbranch/Worktree nötig.

Geprüft: sechs IDs/SHAs und getrennte Scopezuordnung, vollständige Bundleheads/
Prerequisitefreiheit, zwei unabhängige Bundleverifikationen, zwei erfolgreiche
Fsckläufe, sechs vollständige Commit-/Tree-/Historien-/Objektvergleiche, Rechte und
unveränderte Quellmetadaten. TSV-/Hash-/ID-, Markdownlink- und Whitespaceprüfung
für die Dokumentation. Keine Anwendungs-/Ruff-/Pytestabnahme behauptet.
