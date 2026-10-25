# MAINT-05: Validierung und Übergabe

Stand 25.10.2026. Implementierung und synthetische Validierung geliefert;
**Integration nach master und Lifecycleabschluss bleiben ausstehend.**
Kein automatischer Merge erlaubt. Keine reale Archivierung, kein Pilotpush,
keine Branchänderung, keine PR-/Issueschließung und kein Deployment durchgeführt.

## Provenienz und Umgebung

- Vorgegebener bestehender Checkout: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-maint05`.
- Branch: `feat/maint05-worktree-archival`.
- Unveränderter HEAD/Basiscommit: `e68275205fefb7a5f6db42bc45060e505bfcefb5`.
- Lokaler `master`: `c1007efdbac3c1544020f328a3a1347e481797ba`.
- Lokaler Cache `origin/master`: `e68275205fefb7a5f6db42bc45060e505bfcefb5`.
  Diese unterschiedlichen lokalen Referenzen sind keine aktuelle Livebranchprüfung.
- Python **3.12.12**, pytest **9.1.1**, Ruff **0.16.3**, uv **0.9.15**, Git **2.39.5**.
- Ausführung über uv mit dem vorhandenen Python-/pytest-Environment aus MAINT-03,
  ausschließlich lesend verwendet. Keine Installation und keine Änderung dieser Venv.
  `pyproject.toml` lieferte die vorhandene pytest-Konfiguration, pythonpath und addopts.
  Keine Übereinstimmung des gesamten Environments mit `uv.lock` behauptet.
- Die gemeinsame Gitablage liegt außerhalb des freigegebenen Schreibbereichs.
  Keine Probe durch `git add`, Lockanlage, Commit oder sonstigen Metadatenwrite.
  Kein Ersatz-Gitdir und keine Umgehung von Berechtigungsgrenzen.

## Tatsächlich ausgeführte Tests

Abschließender Gesamtlauf nach Freigabe ausschließlich eigener alter synthetischer
Testroots: **97 passed, 0 failed, 0 skipped, 69.95 Sekunden**. 86 neue und 11
bestehende Fälle; wiederholte Läufe werden nicht addiert. Unveränderter finaler
Code-/Teststand. Der temporäre Diagnoseplugin erweitert ausschließlich die
Erfassung von stderr synthetischer Gitkommandos, ohne Rückgabewerte, Fehler oder
Tests zu unterdrücken. Keine automatische Retrylogik.

```bash
PYTHONPATH=.:/tmp/maint05-evidence UV_CACHE_DIR=/tmp/maint05-uv-cache \
  uv run --no-project \
  --python /home/robfra/0_Portfolio_Projekte/Personal_Assistant-maint03/.venv/bin/python \
  -- python -m pytest -p maint05_git_diagnostics \
  tests/test_worktree_archive.py tests/test_repository_audit.py \
  -q --basetemp=/tmp/maint05-pytest-confirmed
```

Finales Log: `/tmp/maint05-evidence/pytest-confirmed.txt`. Ruffcheck und Formatprüfung
bestanden auch am finalen Code. Diagnoseplugin und Logs sind entbehrliche Taskhelfer
in `/tmp`, nicht Bestandteil der Anwendung.

Vorausgehender vollständig bestandener Lauf vor der abschließenden Status-/JSON-Präzisierung:

```bash
UV_CACHE_DIR=/tmp/maint05-uv-cache uv run --no-project \
  --python /home/robfra/0_Portfolio_Projekte/Personal_Assistant-maint03/.venv/bin/python \
  -- python -m pytest tests/test_worktree_archive.py tests/test_repository_audit.py \
  -q --basetemp=/tmp/maint05-pytest-run2
```

**97 passed, 0 failed, 0 skipped, 80.96 Sekunden**:
86 neue MAINT-05-Fälle und 11 bestehende Repository-Auditfälle.
Prozessausgabe: `/tmp/maint05-evidence/pytest-run2.txt`.
Nach der kleinen Präzisierung von Ausgabestatus/JSON-Typfehlern hatte ein erneuter
Lauf 94 passed / 3 Fixture-Setupfehler (81.76 s); ein gezielter Nachlauf 5 passed /
1 weiterer Setupfehler (3.94 s). Der Diagnoselauf hatte 86 passed / 2 failed /
9 Setupfehler (79.24 s). Die Diagnose erfasste ausdrücklich `No space left on device`
beim Schreiben synthetischer `.git/config`-/HEAD-Dateien. Auch eine separate
20-Repository-Probe reproduzierte ENOSPC; `df` meldete dennoch etwa 1.9 GiB frei.
Die zwei Diagnose-Failures betrafen synthetische `remote set-url`-Vorbereitungen;
kein Fehler wurde als erfolgreicher Archivnachweis behandelt. Logs:
`pytest-final.txt`, `pytest-retry.txt`, `pytest-diagnostic.txt` unter
`/tmp/maint05-evidence/`. Diese Zwischenläufe waren nicht grün; erst der oben genannte abschließende
Gesamtlauf nach Freigabe eigener Testroots war wieder vollständig erfolgreich.

Vier ausschließlich selbst erzeugte alte synthetische Testroots wurden nach
Prozess-/Pfadprüfung freigegeben (run1, run2, final, retry); sämtliche Logs und
Diagnosefixtures bleiben erhalten. Keine Projektworktrees, Nutzdaten, Venvs oder
fremden temporären Daten bereinigt. Diese Ressourcenstörung wird nicht durch
Wiederholungslogik in der produktiven CLI verdeckt.
Ein vorheriger Entwicklungslauf hatte 74 passed / 2 failed: falsche Annahme über
Gits Namen für das administrative Worktreeverzeichnis sowie durch Push aktualisierter
Trackingref in der Testfixture. Die Fixtures wurden korrigiert; der finale Lauf
prüft den tatsächlichen `--git-path index` und explizit einen veralteten Trackingref.
Keine dieser beiden Testkorrekturen betraf reale Gitdaten.

Abgedeckte Fälle:

| Bereich | Nachweis |
| --- | --- |
| Sauberer Stand | Exakter Remote-HEAD ergibt nur Plan/Kandidat; Indexbytes und Refs bleiben identisch |
| Lokale Daten | Uncommitted, staged, untracked, ignored DB, ignored Verzeichnis, leeres Zusatzverzeichnis blockieren |
| Gitstatus | Fehler des Statuskommandos, abgeschnittenes NUL-Format, fehlerhafter Status, unvollständiges Rename blockieren; Newline/Unicode-Rename korrekt |
| Indexrisiken | assume-unchanged und skip-worktree blockieren verborgene Änderungen |
| Remote | Fehlend, unerreichbar, abweichend, fehlerhafte Antwort; veralteter Trackingref wird nie zum Livebeweis |
| Identität | Detached HEAD, Hauptcheckout, fest/zusätzlich geschützter Pfad, aktueller Kontrollcheckout, fremder Lock, positiver Prozessnachweis |
| Pfade | Leerzeichen im vollständigen Roundtrip; Symlink, Symlink-Eltern, `.git`-Symlink, relative Pfade, `..`, fremdes Repository blockieren |
| Rennen | Remotewechsel vor Ausführung und während Restoreprobe; lokale tracked/untracked/ignored Änderungen nach Plan, während Probe und nach Unlock |
| Planbindung | Remote-URL-, Branch-, HEAD- und Pfadwechsel; manipulierte Pläne; zusätzlich nachträglich geschütztes Backupziel |
| Freigaben | Fehlende/falsche Archivfreigabe, fehlender Writervertrag und fehlende Restorefreigabe blockieren |
| Archivierung | Gewöhnliche Entfernung nur im synthetischen Repo; PREPARED und verifizierter Abschluss getrennt; Refs unverändert; Wiederholung blockiert |
| Restore | Tatsächlicher synthetischer Archiv-/Restore-Roundtrip mit erwarteten Dateiinhalten und SHA |
| Restorekonflikte | Vorhandener Ordner/Datei/Symlink, Branch anderweitig ausgecheckt oder verändert, Remote verändert/unerreichbar, SHA ungültig, PREPARED blockieren |
| Fehler | Fetch-/fsck-/Remove-/Unlockfehler sowie Fehler des Abschlussdatensatzes; vorbereitete Wiederherstellungsdaten bleiben erhalten |
| Exklusivität | Zweiter konkurrierender CLI-Lock wird verweigert; keine erzwungene Lockübernahme |
| Testgrenze | Jeder Git-Subprozess der neuen Tests benötigt `-C` innerhalb seiner Fixture bzw. neuem temporärem Recoveryrepo; negativer Test gegen tatsächlichen Checkout wird vor Gitstart abgewiesen |
| CLI | Standardarchive und Restoreplan schreiben keine Gitdaten; `--execute` ohne vollständige Parameter HOLD; Inventur unterscheidet erfolgreiche/fehlgeschlagene Remotekataloge |

Die Tests beweisen keine atomare Sicherheit gegen unkooperative fremde Writer.
Siehe [Konkurrenzvertrag](maint05_archive_safety.md). Die alte Auditregression
arbeitet ebenfalls ausschließlich mit neuen temporären Repositories.

Weitere tatsächlich bestandene Prüfungen:

```bash
/home/robfra/0_Portfolio_Projekte/Personal_Assistant-maint03/.venv/bin/ruff check \
  scripts/worktree_archive.py tests/test_worktree_archive.py
/home/robfra/0_Portfolio_Projekte/Personal_Assistant-maint03/.venv/bin/ruff format --check \
  scripts/worktree_archive.py tests/test_worktree_archive.py
git --no-optional-locks diff --check
```

Ruff meldete `All checks passed`, Formatprüfung `2 files already formatted`.
Da sämtliche Lieferdateien neu/untracked sind, prüft zusätzlich die Patchvalidierung
deren vollständigen Inhalt einschließlich Whitespaces; `git diff --check` allein
würde neue Dateien nicht abdecken.
Keine vollständige Anwendungs-/SDK-/Deploymentregression ausgeführt: ausschließlich
neue isolierte CLI plus bestehender Auditpfad, ohne Änderungen am Anwendungscode.

## Reale lesende Inventur

84 Registrierungen, alle erfolgreich lokal gelesen. 18 dirty, 30 mit Zusatzdateirisiken,
8 Detached-HEADs, 15 explizit geschützt; Klassen überschneiden sich. Zwei riskante
Indexeinträge in c26-integration. Kein Kandidat und kein ARCHIVE_VERIFIED.
Autoritatives Gitremote nicht erreichbar: DNS-Fehler, Exit 128. Deshalb alle 84
`REMOTE_UNVERIFIED`, keine falsche Einstufung als erfolgreich oder fehlend.
Getrennte erfolgreiche GitHub-Abfragen belegen zehn offene Draft-PRs und für
C23-01 Commitexistenz sowie gemergten PR #75. Sie ersetzen keine aktuelle exakte
`ls-remote`-Prüfung des Backupbranches. C23-01 bleibt HOLD.

Quellen und Einzelbefunde: [Inventar](maint05_worktree_inventory.md),
[Inventursnapshot](maint05_inventory_snapshot.json),
[PR-Snapshot](maint05_pr_snapshot.json), [Pilot](maint05_c2301_pilot.md).

## Nachweis unveränderter realer Gitdaten

Vor Implementierung wurde eine lesende Ausgangsaufnahme angelegt; nach Tests und
Inventur dieselben Felder erneut erhoben. Der vollständige Vorher-/Nachherbeleg ist
[maint05_state_verification.json](maint05_state_verification.json).

- Registrierungen und ihre HEAD-/Branchangaben: identischer SHA-256-Fingerprint
  `36ac09b05ae7e0338ec1c9cc1493a19e323fa81285bccf55427d5f1c8a222035`.
- Sämtliche lokalen/Remote-Trackingrefs (`git show-ref`): identischer Fingerprint
  `976dd9e8aaee34bcf55b92af55225b420f3273025f64546cc7c4fd6a6d6ffb92`.
- HEAD- und tatsächliche Indexbytes aller 84 Worktrees unverändert.
- Statusausgaben der 83 fremden Worktrees unverändert, einschließlich Namen der
  untracked/ignored Einträge. Nur MAINT-05 hat die vorgesehenen neuen Dateien.
- Private/ignored Dateiinhalte wurden bewusst nicht gelesen oder gehasht. Der
  Statusvergleich ist kein Inhaltsbackup dieser Daten. Die Schreibgrenze und der
  Testsubprozessvertrag verhindern eigene Zugriffe auf fremde Worktrees.

## Patch, Manifest und Integrationsstatus

Elf beabsichtigte neue Dateien: CLI, Regressionstest und neun Dokument-/Belegdateien
unter `docs/maintenance/maint05_*`. Bestehende Projektdateien unverändert.
Vollständige Übergabe unter `/tmp/maint05-delivery/maint05.patch`, zugehöriges
`manifest.json` mit Basis/Branch, Einzeldatei-SHAs und Patch-SHA sowie
`verification.json` mit dem Prüfresultat. Diese temporären Übergabeartefakte sind
nicht Teil des Patches; so entstehen keine selbstreferenziellen Hashes.

Der Patch wird ausschließlich aus diesen elf Dateien erstellt. Prüfung mit
`git apply --check --whitespace=error-all`, tatsächlichem `git apply` in einem neuen
synthetischen Repository, SHA-Abgleich aller Dateien und erneutem Apply-Check auf
bereits angewendete Dateien (muss scheitern). 17 relative Dokumentlinks wurden auf vorhandene Ziele geprüft. Ein anfänglicher
strenger Patchcheck erkannte eine zusätzliche Leerzeile am Dateiende der generierten
Inventurdokumentation; diese wurde entfernt und die Prüfung wiederholt bestanden. Die bestehende `*.json`-Ignore-Regel erfasst vier neue Belegdateien. Sie sind
ausdrücklich im Patch/Manifest enthalten; das Runbook nennt ein genau auf diese vier
Pfade begrenztes `git add -f`. Keine Ignore-Regel wurde verändert.
Das externe Manifest macht den vollständigen
Lieferinhalt einschließlich der Dokumente nachvollziehbar.

Keine neuen echten Branches oder Worktrees in diesem Lauf erzeugt. Der vom Betreiber
vorgegebene MAINT-05-Branch und -Worktree waren bereits vorhanden und bleiben erhalten:
Code und Dokumente sind uncommitted, Review-/Defaultbranchintegration steht aus,
und diese Aufgabe verbietet automatische Merges. Alle 83 übrigen Worktrees und
sämtliche vorhandenen Branches bleiben ebenfalls erhalten. Kein Cleanup autorisiert
oder vorgenommen. Temporäre synthetische Testrepos/Logs liegen ausschließlich unter
`/tmp`; sie sind keine realen Projektworktrees.

[Exakte Commit-/Pushbefehle und spätere Pilotfreigabe](maint05_operator_runbook.md).
Vollständiger Lifecycleabschluss erst nach regulärem Review und nachgewiesener
Integration sämtlicher beabsichtigter Dokumente nach **master**. Diese Lieferung
behauptet keine solche Integration.
