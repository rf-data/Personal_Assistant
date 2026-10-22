# Betrieb und Recovery

Für die C26-Fortsetzung gelten zusätzlich das
[workerbewusste Deployment-Gate](deployment_gate.md) und das
[private HTTPS-Handbuch](https.md). Der Gate-Kern ist offline vorbereitet;
produktiver Driver/Triggerpfad und Erstbootstrap sind nicht freigegeben. Nach
Aktivierung schließt Drain die Annahme dauerhaft, lässt bestehende Jobs auslaufen
und hält auch nach gesundem Containerwechsel bis zu einer separaten Resume-
Freigabe geschlossen. Kein Ersatz für die folgenden C22-Maintenance-/Backupfences.

Voraussetzungen und offene Gates zuerst in [c22_validation.md](c22_validation.md)
prüfen. Kein Befehl hier ist während C22 gegen einen produktiven Server gelaufen.
Der Betreiber verwendet eine private Release-Envdatei und explizite Compose-Datei;
kein generisches `docker compose up` im Repositorywurzelverzeichnis.

```sh
docker compose --env-file /private/release.env -f deployment/compose.yaml \
  --profile private-production config --quiet
# Vor Aktivierung: bereitgestellte Config/Volume im identischen Linux-/UID-Kontext:
python -m scripts.deployment check --config /run/config/controller.json
python -m scripts.deployment probe --config /run/config/controller.json
```

`check` ist read-only, startet keine Jobs und erzeugt keine Datenbank. Es prüft
Pfade/Rechte, Katalogbytes/Hashes, freien Speicher und Quarantäne. `probe` ist
ausdrücklich schreibend: erzeugt einen neuen temporären Unterordner im Workspace,
prüft rename/fsync/flock/SQLite-WAL mit unabhängigen Handles und entfernt diesen
wieder. Den Probe nach Bereitstellung des endgültigen Mounts im Zielcontainer
wiederholen; das ist keine Freigabe eines Netzdateisystems.

Start nach manueller Go-live-Freigabe: Gateway/API zuerst, API-Health prüfen,
Executor starten und Heartbeat prüfen, dann UI/Ingress. Für jede Rolle nur den
vorbereiteten Compose-Service mit `--no-build --pull never` starten. Wegen
`network_mode: service:api-gateway` darf der Gateway zunächst unhealthy sein,
bis die API läuft; API hängt nur von `service_started` ab.

Stop: Ingress schließen und UI stoppen, API stoppen (keine neuen Aufträge), dann
Executor mit SIGTERM stoppen und bis zu 30 s warten; Gateway zuletzt stoppen.
Guardian räumt bekannte Nachfahren auf, bevor terminaler Zustand geschrieben
wird. Kein blindes Killen gespeicherter PIDs, kein automatisches Entfernen von
Lockdateien. Keine `down -v`- oder Cleanupbefehle auf produktiven Verzeichnissen.
Restart-Policy ist `unless-stopped`; sie startet Prozesse, keine fachlichen
Wiederholungen. Bereits persistierte **queued** Jobs können nach Executor-Restart
normal verarbeitet werden. Unterbrochene laufende Jobs werden **nicht** automatisch
neu ausgeführt; ein neuer bestätigter Execute-/Resume-Auftrag ist erforderlich.

| Beobachtung | Operatorentscheidung |
| --- | --- |
| API ungesund / 401 bei echtem Nutzer | Loopback-/TLS-Health unterscheiden; individuelle Dateibindings und Backend-SHA prüfen; keine Auth abschalten |
| Executor-Heartbeat fehlt | Workspace-/Config-Rechte, freien Platz, Workerlock und Quarantäne prüfen; einzelner Executor pro Workspace |
| Workspace fehlt / Rechte falsch | Start verweigert; freigegebenen Mount wieder bereitstellen, keine leere Ersatzdatenbank erzeugen |
| Worker nach SIGKILL/OOM | C19 wartet auf Lebenszykluslock und markiert laufenden Job interrupted oder quarantänisiert; Zustand prüfen, keine gespeicherte PID signalisieren |
| Quarantäne vorhanden | Workspace einschließlich Marker sichern; Cleanup und Prozesshierarchie auf dem Host bestätigen; gezielte Recovery separat autorisieren; kein Auto-Löschen |
| Workflow unterbrochen | bestehendes Inspect/Run-Report lesen; freigegebene Hashes vergleichen, explizites Resume bestätigen; Provenienz/Previous-Run behalten |
| Niedriger Speicher / ENOSPC | Ingress/Dispatch stoppen, Datenträger erweitern oder freigegebene Retention anwenden; keine DB/WAL/Workflowdateien einzeln löschen |
| CPU/PID/RAM-Limit erreicht | Container-OOM/Exit und C16-Events prüfen, eigenen synthetischen Lastfall wiederholen; Limits nur mit neuer Budgetabnahme ändern |
| UI-Neustart | fachliche Jobs bleiben im Backend; UI-Session neu authentisieren, Historie neu laden; keinen Submit wiederholen, ohne Idempotenzstatus zu lesen |
| Gateway neu erstellt | API ebenfalls neu erstellen, damit sie den neuen Netzwerknamespace teilt; Zertifikat/CA prüfen |

Healthchecks: API prüft SQLite v1/quick_check und die echte lokale 401-Authgrenze,
Executor prüft DB/Heartbeat, Gateway prüft vertrauenswürdiges TLS bis zur gleichen
401-Grenze, UI prüft Streamlit `/_stcore/health`. Health bedeutet Bereitschaft,
nicht erfolgreiche fachliche Extraktion oder autorisierten OIDC-Browserlogin.
Backend-Checks verweigern auch bei <512 MiB frei oder Quarantäne. Unhealthy allein
bewirkt in Compose keinen automatischen Neustart; Alarm/Operator erforderlich.

Logs: `docker compose ... logs --tail 100 api executor api-gateway ui` und begrenzte
C16-Events statt beliebigem Runner-stdout. Keine Umgebungs-/Config-/Header-Dumps
in öffentliche Tickets. Docker json-file je Dienst 3 × 10 MiB; Workflow-/Jobdaten
separat aufbewahren. Keine Zugangsdaten in Caddy-Accesslogs (hier nicht aktiviert).

C15: Queue, Running, Outcomes, Dauerhistogramme, Fehlerklassen und Worker-Heartbeat
stammen aus den bestehenden C16-Aggregaten. `interrupted` ist kein zusätzlicher
Completion-Outcome; dafür C16-Historie und C18-Report prüfen. Timeout erscheint als
Fehlerklasse. Datenträger-/Hostmetriken verlangen separat abgenommenen bestehenden
C15-Hostexporter; C22 mountet weder `/` noch Docker-Socket. Das Profil bindet die
vorhandenen Recording-/Alertregeln ein, aber ohne Alertmanager erfolgt keine
Alarmzustellung. Vor Freigabe promtool, Dashboarddatasource und Alarmrouting testen.

Manueller Go-live: beide PRs reviewen/mergen; Authlib-Lock und echte OIDC-Abnahme
schließen; Imagebereitstellung/Signatur/SBOM prüfen; Zielvolume-Probe und Rechte;
frische Restoreprobe; TLS/Ingress/Firewall; isolierte Container-SIGTERM/SIGKILL/OOM-
und PDF-Cancel-Tests; Auth-/Viewer-/Operator-/Metriktests; Alarmzustellung;
Operator-Rollback und Retention bestätigen. Erst danach Dienste und zuletzt
Ingress bewusst aktivieren. Es gibt keinen automatischen Rollout in C22.

## C26-B HTTPS-Ergänzung

Für den vorhandenen Coolify-Traefik und ausschließlich die bestehende UI gilt
[HTTPS, OIDC, Rollout und Rollback](https.md). Keine Aktivierung des gesamten
C22-Composeprofils für diesen Auftrag. Produktivfreigabe bleibt gesperrt.
