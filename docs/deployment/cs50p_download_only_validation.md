# C26-CS50P-04: Validierung und Übergabe

28.10.2026. **HOLD**. Download-only-Installationskandidat, keine Produktionsfreigabe,
kein reales Deployment. [Exakter Betreiberablauf mit CHANGE/READ-ONLY und Rückbau](cs50p_download_only_operator_guide.md).

## Vorprüfung und gesicherte Ausgangsbasis

Der bereitgestellte Worktree `Personal_Assistant-cs50p-04` war sauber und hatte
Detached HEAD `81db9ed3f5fc7e0c3d6952b438f015ae6521af3c`. Der vom Benutzer genannte
Branch `feat/c26-cs50p-mvp` ist in einem anderen, bereits vorhandenen Worktree
ausgecheckt; er wurde nicht verschoben oder verändert. Lokale Remote-Trackingref
und live über den GitHub-Connector gelesener Featurebranch zeigen auf denselben
Commit. [Gesicherter C26-CS50P-03-Commit](https://github.com/rf-data/Personal_Assistant/commit/81db9ed3f5fc7e0c3d6952b438f015ae6521af3c).
Er enthält den vorherigen Nativecommit `2f2b410` und die vollständige kuratierte
03-Lieferung: 28 gelistete Nutzlastdateien sind getrackt; alle 33 hinterlegten
Sourceprüfsummen und alle 61 Roharchivdateien stimmen nach SHA-256 und Länge.
Die alten lokalen Patchhüllen sind laut 03-Handoff bewusst keine Gitnutzlast;
deren eigentliche Änderungen und Rohbelege sind im gesicherten Commit enthalten.
Erst nach dieser Prüfung begannen die neuen Änderungen.

`artifacts/c26_cs50p_04/baseline-audit.json` hält diesen Befund fest. Die alten
03-Belege wurden nicht aktualisiert; insbesondere deren damaliger Remotestand
ist historische Evidenz. README und bestehende Implementierung/Units bleiben
unverändert. Kein SQLitefix oder Abschwächen einer roten Assertion.

## Audit der bisherigen Installationspläne

| Bisheriger Befund | Umsetzung für den Download-only-Pilot |
| --- | --- |
| 03-/Native-Anleitung installiert eine Native-Unit und beschreibt C16-Approval/Run | Eigene Unit ausschließlich für Download; keine Native-/Workerunit installieren; bekannte Units maskieren, bestehende Instanzen/Unitkonflikte abweisen |
| `useradd`, neue Pfade und einzelne `ln -s` sind keine wiederholbare Routine | Explizite eigene Installationskennung; identische Wiederholung; keine Adoption fremder Ressourcen; Account ohne Zusatzgruppen |
| Getrennte app-/venv-Symlinks erlauben gemischte Versionen | Ein atomarer Releasezeiger umfasst Code, Venv und Specs; flock plus Inaktivitätsprüfung vor Wechsel |
| Absolute Buildpfade im Batch funktionieren nach Kopieren nicht automatisch | Nur Manifestpfad an Release binden, Batchhash neu berechnen, anschließend bestehende `load_batch`-Hashprüfung/Neuplanung und Quellenadmission ausführen |
| `private()` verlangt benutzereigene 0600/0700-Pfade | Specs gehören dem Dienstbenutzer, sind aber im systemd-Dienst schreibgeschützt; Code/Venv bleiben root-eigen |
| Restriktive Root-umask kann Venv für Service unlesbar machen | Neu erzeugte Runtimeverzeichnisse explizit les-/traversierbar setzen, Symlinkziele nicht chmoden; Import/Preflight als Dienstbenutzer vor Releasewechsel |
| Python/venv/CA und vollständiger Wheelclosurebeleg fehlen | Offline `--no-index --only-binary=:all: --require-hashes`, pip check und echter Import/Specpreflight im Installer; fehlendes Paket blockiert |
| Journalpersistenz ist keine Dateireportpersistenz | Reports und Raw/Receipts bleiben auf privaten Hostpfaden; keine globale journald-Konfiguration ändern |
| Alte Runbooks enthalten auch Verarbeitung und unvollständige Rückbaufolgen | Neuer eigenständiger Betreiberablauf, Stop/Status/Journal, manuelles Upgrade/Rollback und datenbewahrendes Uninstall |

Die bestehende doppelte Quellenprüfung (`download` und `process`) bleibt unverändert.
Sie wird nicht als Berechtigung zum Workerstart verwendet. Die beiden bekannten
Worker-Einstiegsskripte werden aus der installierten Scriptkopie ausgeschlossen.
Es entstehen keine Controller, Jobdatenbanken, Native-Enrollments oder Grants.
Kein Login, keine Sudoerserweiterung, keine Docker-/systemd-journal-Gruppe für den
Dienstbenutzer. Eine absichtliche Änderung durch Root liegt außerhalb dieser Grenze.

## Tatsächlich ausgeführte Prüfungen

Lokales Linux: Debian 12, systemd 252; vorhandener Python 3.12.12-Testinterpreter
nur für Tests verwendet, kein deploybares Runtimepaket behauptet.

| Prüfung | Ergebnis / Aussagegrenze |
| --- | --- |
| Finale Offline-Suite | **102 passed, 1 skipped**, 10,32 s; separater User-/Netzwerk-Namespace plus `tests.offline_guard` |
| Isolierter Installationslebenszyklus | Echte Dateischreib-/Rechte-/Hash-/Symlinkoperationen unter neuen `/tmp`-Wurzeln; Hostbefehle wie useradd, systemctl, Venv/pip über aufgezeichneten Testadapter, nicht am Host ausgeführt |
| Erstinstallation/Wiederholung/Upgrade/Rollback/Uninstall/Reinstall | Geprüft; Code-/Venvrechte, atomarer gemeinsamer Zeiger, identische Releases und erhaltene Raw-/Reportbytes; kein start/enable/apt/docker/ssh/userdel in den ausgeführten Adapterbefehlen |
| Fail-closed-Fälle | Aktive Units, fremde Daten/Unit/Masken/Drop-ins/Timer, Symlinks, einzelne Native-Instanzen trotz Template-Maske, Snapshot-/Batch-/Releaseänderungen, gleiche Kennung mit anderen Bytes und unvollständige Runtimevorbereitung blockieren |
| Installierter Einstiegspunkt | `__file__`-Releaseauflösung, versiegelte Specs, echtes flock, Preflight und Download mit synthetischem MockTransport; manipulierte Specs und Installerlock sperren; C16-Aufruf führt zum Testfehler |
| Bestehende Downloadregression | DNS-/Metadata-/IPv6-/Rebinding-/TLS-Namensschutz, Allowlist, Credentials, Redirects, Limits, Fehler/Integrität, atomare Publikation, Wiederverwendung und SIGTERM-Reports über vorhandene Tests erhalten |
| systemd statisch | verify und security offline Exit 0; nur ExecStart/ExecStartPre für die lokale Syntaxfixture auf `/usr/bin/true` umgestellt; keine echte Dienstinstallation/-ausführung, systemd 255 nicht simuliert |
| Frische CPython-3.12-Venv | Tatsächlich angelegt; reale pip-Installation mit leerem Wheelhouse und deaktiviertem Netzwerk scheitert erwartungsgemäß Exit 1 bei fehlendem gepinntem Paket; kein positiver Closurebeleg |
| Syntax/Format | AST/JSON validiert; Ruff check/format erfolgreich; geprüfter Patch vorwärts/rückwärts und bytegleich anwendbar (Übergabebeleg) |

Der Skip ist `test_small_host_compose_render_without_daemon`: explizite externe
Integration nicht freigegeben. Docker wurde nicht aufgerufen. Die 102 grünen Tests
ersetzen weder einen echten Rootinstallationslauf auf Ubuntu 24.04/systemd 255
noch den positiven vollständigen Wheelhouseinstallationsbeleg. Fehlende Wheels
wurden nicht durch Paket-/Hashänderungen kaschiert. Keine neuen Abhängigkeiten.
Die SQLite-Stresssuite wurde nicht als Download-only-Gate umdefiniert oder erneut
zum Bestehen gebracht; der dokumentierte 03-Konkurrenzfehler bleibt offen.

Reproduzierbarer finaler Testbefehl, CHANGE ausschließlich lokale Testartefakte:
`PYTHON` bezeichnet einen bereits geprüften Python-3.12-Testinterpreter. Keine
bestehende Produktionsvenv verwenden oder verändern. `NEW_RESULT.xml` ist neu.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 unshare --user --map-current-user --net PYTHON -m pytest -q -o addopts= -p no:cacheprovider -p tests.offline_guard tests/test_cs50p_download_only_install.py tests/test_cs50p_mvp.py tests/test_cs50_material_download.py tests/test_cs50_capacity.py --junitxml=NEW_RESULT.xml
```

Belege: `artifacts/c26_cs50p_04/final-tests.xml`, `systemd.json`,
`negative-fresh-venv.json`, `baseline-audit.json`, `validation.json` sowie der
Patchanwendungsbeleg in `handoff/package-validation.json`. Frühere Zwischenläufe
sind nicht zur finalen Testzahl hinzuaddiert. Testdaten sind ausschließlich
synthetisch; Schemafixtures mit `official`-Kennzeichnung sind keine realen
Quellenfreigaben und werden nicht als Hostspecs geliefert.

## Offene Gates und Git-Lifecycle

1. Vollständiges unverändertes gepinntes Wheelhouse für Zielarchitektur/CPython 3.12
   beschaffen und positive Neuinstallation inklusive Importen dokumentieren.
2. Echten isolierten Ubuntu-24.04-/systemd-255-Installationslauf durchführen,
   einschließlich UID/Rechten, cgroup-Schutz, Masken, Upgrade und datenbewahrendem
   Rückbau. Die Adaptertests belegen diese Hostintegration ausdrücklich nicht.
3. Betreiberreview des Zielhosts und der konkreten offiziellen Snapshot-/Quellen-
   freigaben; Kapazität neben Coolify prüfen. Erst danach gesonderte manuelle
   Freigabe genau des kleinen Downloadlaufs. SSH-Abbruch/-Neuverbindung und
   Ergebnisabruf sind hier nicht real getestet.
4. Regulärer Commit/PRreview und Integration der Lieferung einschließlich dieser
   dauerhaften Dokumentation nach `master` stehen aus. Lokale Gitverwaltung liegt
   außerhalb der beschreibbaren Wurzeln und ist explizit read-only. Der vom Auftrag
   erlaubte geprüfte Patch wird geliefert; kein Remote-API-Schreibweg als Umgehung.

Damit bleibt der Gesamtstatus **HOLD**, obwohl der Download-only-Kandidat lokal
validiert vorliegt. Kein pauschales C26-Go und kein eigenständiger Produktionsstart.

In dieser Aufgabe wurden keine Gitbranches oder zusätzlichen Gitworktrees erstellt.
Der vom Benutzer bereitgestellte Worktree, Featurebranch und sämtliche fremden/
historischen Gitobjekte bleiben erhalten; nichts gelöscht. Der vorhandene
Detached-Worktree enthält die neue uncommittete Lieferung und muss wegen ausstehender
Integration erhalten bleiben. Nach externer Anwendung regulär reviewen/integreren;
vorher weder diesen Worktree noch die Featurebasis entfernen. Taskcompletion im
Sinn der Repository-Lifecycle-Regel bleibt bis zur Defaultbranchintegration pending.
Temporäre Tests/negative Venv/Systemdfixture unter `/tmp` bleiben als Belege erhalten.
