# Konsistentes Backup und isolierter Restore

Das neue lokale Werkzeug unterstützt **gestoppte, C22-verwaltete** API-/Executor-
Rollen. `scripts/backup_hetzner.sh` bleibt unverändert und wird nicht ausgeführt.
Eine VPS-/Hetzner-Snapshotfunktion wurde weder aufgerufen noch als konsistentes
Applikationsbackup verifiziert. Live-rsync einer SQLite-Datei ist kein Ersatz.

| Daten | Klasse / Aufbewahrung |
| --- | --- |
| `jobs.sqlite3`, WAL/SHM | persistent, privat; immer zusammen im laufenden Workspace; Backup über SQLite-Backup-API, nicht einzelne Livekopie |
| `workflows/**` einschließlich state/requests/runs/Idempotenz | persistent, privat; vollständig in derselben gestoppten Sicherung |
| `jobs/**` Inputs/Results/Receipts/normalisierte Artefakte | persistent, Quellenprovenienz/Hashes erhalten; keine automatische Migration oder Löschung |
| `quarantine` und Recoverymarker | persistent bis bewusster Incidententscheidung; Sicherung erhält sie |
| genehmigter Katalog und Controller-JSON | versionierte private Betriebskonfiguration plus deklarierte Eingabebytes/Hashes |
| Tokenbytes, OIDC-Secrets, TLS-Key, Grafana-Passwort | geheim; getrennt verschlüsselt sichern, niemals in den Workspace legen |
| `.operations.lock`, `.bootstrap.lock`, `worker.lock`, Job-`execution.lock` | temporäre Laufzeitlocks, nach vollständig gestoppten Rollen rekonstruierbar; Backup lässt nur diese konkreten Pfade weg |
| `/tmp` und abgeschlossene `.c22-probe-*` | temporär; eigene Probe räumt ausschließlich ihren Unterordner auf |
| Containerlogs / Prometheus TSDB / Grafana | Logs begrenzt, TSDB rekonstruierbar mit Datenverlust; Grafana-Daten separat sichern, Dashboardquellen in Git |

Standard-Retentionvorschlag zur manuellen Freigabe: 7 tägliche + 4 wöchentliche
verschlüsselte Sicherungen, eine Kopie getrennt vom Host; monatliche Restoreprobe.
Kein Retentionsjob ist installiert. Jobdaten nicht wegen voller Disk automatisch
löschen: zuerst Aufbewahrungsbedarf und referenzierende Workflows prüfen.

Verfahren: Ingress/UI schließen, API und Executor geordnet stoppen. Alle Jobs
müssen terminal (`completed`, `failed`, `cancelled`, `interrupted`) sein und der
Heartbeat 0. Created/queued Jobs vorher bewusst abbrechen/abwickeln. Nach hartem
Workerabbruch erst kontrollierte C19-Reconciliation durchführen; keine DB-Zustände
manuell umschreiben. Alle alten `scripts.job_control`-Prozesse und sonstigen
Schreiber müssen ebenfalls gestoppt sein. Nur neue Launcher halten die gemeinsame
`.operations.lock`; das Werkzeug kann fremde Schreiber nicht zuverlässig erkennen.

```sh
umask 077
python -m scripts.deployment backup --config /private/controller.json \
  --output /new/private/snapshot
python -m scripts.deployment restore --snapshot /new/private/snapshot \
  --output /new/isolated/restored-workspace
```

Die API und Executor halten während ihrer gesamten Laufzeit einen Shared-
Wartungslock. Backup verlangt den exklusiven Lock und lehnt aktive verwaltete
Rollen ab. Anschließend prüft es DB v1/quick_check, Jobmodelle, terminale Zustände,
Heartbeat und C16-Ergebnisartefaktgrößen/-Hashes. Es sichert die SQLite-DB per
Backup-API, alle übrigen Workspace-Dateien einschließlich C18-Provenienz, eine
Configkopie und ausschließlich deklarierte Katalogdateien. Das Sicherungs-DB-
Journal wird zu DELETE normalisiert; die originale DB/WAL wird nicht migriert.

Kopierte Dateien und Verzeichniseinträge werden vor erfolgreicher Rückkehr mit
`fsync` synchronisiert. Ein Host-/Datenträger-Crashtest ist damit nicht ersetzt.

Manifest v1: `schema_version`, `kind=c22-stopped-workspace`, `files` mit relativem
Pfad → `{sha256, bytes}`. Es entsteht zuletzt und listet alle Bundle-Dateien außer
sich selbst. Unvollständige Bundles haben kein gültiges Manifest. Kein vorhandener
Snapshot oder Restorepfad wird überschrieben. Maximal 20.000 Dateien/2 GiB pro
inventarisiertem Baum, Manifest maximal 8 MiB; Symlinks, Hardlinks und Spezialdateien
werden abgelehnt. Für größere Daten eine gesondert getestete Sicherungslösung
freigeben. Alle Backup-/Restoredateien 0600, Verzeichnisse 0700. Das Werkzeug
verschlüsselt nicht; Bundle enthält sensible Inhalte/Identitätshashes und muss
privat transportiert/verschlüsselt werden. Hashes entdecken Integritätsfehler,
sind ohne vertrauenswürdige Signatur keine Manipulationsauthentifizierung.

Restore prüft den vollständigen Bestand und alle Hashes **vor** Erzeugung des
Zielworkspace, validiert Config/Katalog und C16-Artefakte nochmals und kopiert in
einen neuen privaten Pfad. Er startet keinen Prozess, setzt keinen Auftrag fort,
ändert keine Identitäten und entfernt keine Quarantäne. Config und Katalog bleiben
im Bundle für gezielte Operatorbereitstellung. Absolute Katalogbindungen in der
DB bleiben original: bei späterer Aktivierung identische Containerpfade bereitstellen.
Nur den neuen Workspace in die neue Instanz mounten; niemals parallel mit dem
Originalworkspace starten. Private Config bewusst auf den Restore-Mount binden;
keine automatische Pfadumschreibung.

Die lokale synthetische Probe sichert tatsächliche C16-Jobdaten samt ausgeführtem
Artefakt, vergleicht den gespeicherten SHA256 nach Restore und prüft Idempotenz,
Workflowdateien und Erhalt von interrupted/Quarantäne. Weitere C18-/PDF-Recovery-
Tests testen den bestehenden fachlichen Resumevertrag. Kein produktives Backup
und keine Secrets wurden kopiert. Datenträger-Crash während Backup, verschlüsselte
Offsiteübertragung und Zielhostrestore bleiben manuelle Abnahmeschritte.
