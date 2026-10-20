# Betrieb und Migration

## Imagefreigabe und Settings

Prometheus v3.5.0, Grafana 12.1.0 und der bestehende cAdvisor-Digest bleiben gleich.
Für die bisherigen Floating-Tags fehlt eine belastbare Inventur der Installation.
Deshalb sind `ALERTMANAGER_DIGEST`, `NODE_EXPORTER_DIGEST` und
`PORTAINER_DIGEST` zwingende 64-stellige SHA256-Eingaben. Sie müssen zu den
bereits freigegebenen Images/Architekturen gehören. Repository-Namen sind fest.
Die alten Kommentare v0.28.x/v1.9.1 beweisen keine installierte Version.
Kein Image wurde aktualisiert, heruntergeladen oder auf CVEs geprüft.

Betreiberinventur: Image, Digest, Architektur, Freigabegrund, Probe-Kompatibilität.
Nicht einfach den neuesten Tag auflösen. Auch vorhandene exakte Versionstags
können nach separater Freigabe auf ihren Digest festgelegt werden; C15 erfindet
dafür keine Hashwerte.

Die drei freigegebenen Digests über die externe Betreiberkonfiguration exportieren.
`GRAFANA_ADMIN_PASSWORD_FILE` bezeichnet eine externe, für Betreiber/Image-User
lesbare Datei. Kein Secret in Git, CLI-Argumenten oder Reports. Der Validator
liest nur die Digest-/Portwerte, niemals die Passwortdatei.
Compose interpoliert alle drei Digests auch bei inaktiven Profilen.

```bash
python -m scripts.validate_monitoring --check-overrides
docker compose --env-file /dev/null -p personal_assistence -f docker/docker-compose.monitoring.yaml config --quiet
```

Die Variablen müssen bereits exportiert sein. /dev/null verhindert implizites
Laden einer allgemeinen .env. Alternativ eine ausschließlich für Monitoring
bestimmte externe Environment-Datei an Compose übergeben und deren nicht geheime
Digest-/Portwerte vorher mit dem Validator prüfen. Keine dieser Prüfungen startet
Container oder liest Secrets.

Alertmanager bleibt eine einzelne lokale Instanz; Gossip ist deaktiviert.
Für eine produktive HA-Installation müssen Cluster-/Peer-Konfiguration und
Netzgrenzen gesondert geprüft werden. Sein bisher impliziter Storage-Default
wird bewusst nicht mit einem neuen Pfad überschrieben: das bestehende Compose-
command ersetzt die Image-CMD-Defaults. Je nach freigegebenem Image kann die
Silences-Datei unter einem Unterverzeichnis von /alertmanager liegen. Eine
Umstellung auf dessen Wurzel würde trotz identischem Bindpfad alte Silences
nicht mehr laden. C15 migriert dieses Layout nicht.

Optional ändern PROMETHEUS_PORT, ALERTMANAGER_PORT, GRAFANA_PORT,
NODE_EXPORTER_PORT, CADVISOR_PORT, PORTAINER_PORT ausschließlich Portnummern
(1024–65535). Loopback-Bindadresse und Containerports bleiben fest.
Portkollisionen muss der Betreiber prüfen.

## Profile und Target-Discovery

| Profil | Dienst | Grenze |
| --- | --- | --- |
| keines | Prometheus, Alertmanager, Grafana | internes Netz, Loopback, lokale Receiver-Senke |
| host | node-exporter | Host-Root, /proc, /sys |
| containers | cAdvisor | Host-Root, /var/run, Docker- und Geräte-Metadaten |
| admin | Portainer | Socket erlaubt Hostadministration |

Reine Konfigurationsprüfung aller Profile:

```bash
docker compose --env-file /dev/null -p personal_assistence -f docker/docker-compose.monitoring.yaml \
  --profile host --profile containers --profile admin config --quiet
```

Systemmetriken benötigen nach Freigabe den jeweiligen Exporter und das passende
Beispiel aus `monitoring/prometheus/target-examples/` als neue host.json bzw.
containers.json in `monitoring/prometheus/targets/`. Vorhandene Dateien nicht
überschreiben. Beispiel für exklusives Publizieren im Repository:

```python
from pathlib import Path
source = Path("monitoring/prometheus/target-examples/host.json.example")
with Path("monitoring/prometheus/targets/host.json").open("x") as output:
    output.write(source.read_text())
```

File-SD aktualisiert Targets ohne Neustart. Discovery vor Profilabschaltung
bewusst außerhalb des Globs archivieren, sonst meldet TargetDown den konfigurierten
fehlenden Dienst. Ohne Target besteht keine Verfügbarkeitsaussage.
pipeline.json.example bleibt inaktiv, solange kein echter Exporter existiert.

## Persistenz: keine automatische Migration

Pfade bleiben relativ zur bestehenden Compose-Datei im docker-Verzeichnis.
Bestehende Compose-Projektkennung und Container-Namen erhalten.
Keine Daten wurden gelesen, verschoben, gelöscht, initialisiert oder chowned.
Das vorhandene Makefile setzt die Projektkennung `personal_assistence`.
Die Prüfbeispiele verwenden dieselbe Kennung; falls die konkrete Installation
bewusst anders benannt wurde, muss deren tatsächliche Kennung erhalten bleiben.
Die Make-Targets selbst starten/stoppen Container und wurden nicht ausgeführt.

| Alter Hostpfad → Containerpfad | Neuer Pfad | Risiko / Migration |
| --- | --- | --- |
| monitoring/prometheus/data → /prometheus | identisch | keine Pfadmigration; TSDB/Retention unverändert |
| monitoring/grafana/data → /var/lib/grafana | identisch | Benutzer, Dashboards und SQLite bleiben |
| monitoring/alertmanager/data → /alertmanager | identisch | Silences bleiben; bisheriger Image-Default für Storage bleibt unverändert |
| monitoring/portainer/data → /data | identisch | Profilabschaltung löscht nichts |
| monitoring/prometheus.yaml → /etc/prometheus/prometheus.yaml | identisch, read-only | Konfigurationsversion sichern |
| monitoring/prometheus/rules → /etc/prometheus/rules | identisch, read-only | Regeln prüfen; keine Zeitreihendaten migrieren |
| monitoring/alertmanager/config → /etc/alertmanager | identisch, read-only | private Receiver vor Übernahme getrennt sichern |
| Grafana-Provisioning/Dashboards | neue read-only Configmounts | UID-Konflikte pa-system-v1/pa-pipeline-v1/pa-prometheus vorab prüfen |
| /proc, /sys, /, /var/run, /var/lib/docker, /dev/disk | bestehende Ziele unverändert, nun Profile | keine Datenmigration, Sichtbarkeit bewusst freigeben |
| /dev/kmsg | entfällt | kein Datenspeicher, keine Migration; Kernelereignisse fehlen bewusst |

Vier Daten-Binds verwenden create_host_path=false. Fehlende Pfade führen zum
Fehler statt zur Anlage eines leeren root-eigenen Ersatzverzeichnisses.
Neue Entwicklungsablagen bewusst vorbereiten. Bestehende Daten niemals pauschal
rekursiv umberechtigen. Notwendige Schreibrechte: Prometheus/Alertmanager
65534:65534, Grafana 472:0, Portainer root. Configs für diese UIDs lesbar halten.
Keine Standard-Secretdatei wird angelegt. Root-Dateisystem read-only, temporäre
Schreibzugriffe auf begrenztes /tmp, Daten nur in bisherigen Binds.

Bestehende Grafana-Konten werden durch Bootstrap-Passwortdateien nicht rotiert.
Provisionierte Dashboards sind im UI nicht editierbar.
disableDeletion=true verhindert automatische Dashboard-Löschung bei entfernter
Provisioning-Datei. Keine vorhandenen Dashboards/Datasources werden gelöscht;
UID-Konflikte vor Anwendung bewusst auflösen.
Beide bisherigen Rule-Endungen .yaml und .yml bleiben aktiv, nun mit absoluten
Containerpfaden. Zusätzliche lokale Regeln müssen vor Übernahme auf Namens-
konflikte und gültige PromQL geprüft werden; sie werden nicht automatisch gelöscht.
Die neue Datasource ist nicht als organisationsweiter Default markiert;
beide Dashboards verwenden ihre UID ausdrücklich. Eine vorhandene Default-
Datasource wird damit nicht absichtlich umgestellt.

Vor späterer Anwendung: konsistente Backups aller vier Datenablagen und privaten
Configs; Images/UIDs/Probes in Staging prüfen; TSDB-/Grafana-Kompatibilität und
Ressourcenlimits testen. Limits sind lokale Ausgangswerte, keine gemessene
Kapazitätsplanung. Retention bleibt unverändert. Rollback stellt vorherige
Configs und freigegebene Images wieder her; ein Datenbank-Downgrade darf nicht
vorausgesetzt werden. Keine automatische Migration/Bereinigung/Volume-Löschung;
`down -v` ist ausgeschlossen.

## Konfigurierbare Alarmempfänger

Default local-only sendet nichts. Eine private Alertmanager-Konfiguration kann
außerhalb des Repositorys liegen und denselben Containerpfad read-only ersetzen.
Unaktiviertes Beispiel ohne tatsächlichen Empfänger:

```yaml
route:
  receiver: ops-webhook
receivers:
  - name: ops-webhook
    webhook_configs:
      - url_file: /run/secrets/alert_webhook_url
        send_resolved: true
        max_alerts: 20
```

URL-Datei als separates Compose-Secret einbinden; niemals einchecken/loggen.
Mit dem zum freigegebenen Digest passenden amtool check-config prüfen.
Das interne Netz sperrt allgemeinen Egress. Ein privates Compose-Override kann
**nur Alertmanager** zusätzlich an ein kontrolliertes Benachrichtigungsnetz
anbinden. Ziel-/TLS-Freigaben, Timeouts, Testempfänger und Secretmanagement sind
separat nötig. Kein automatisches Environment-Templating im YAML wird angenommen.

## Loki und Logs

Auskommentierte Loki-/Promtail-Fragmente waren kein funktionsfähiges Profil.
Persistenz, Authentifizierung und Retention waren nicht geprüft.
Promtail ist seit 02.03.2026 EOL; neue Aktivierung ist nicht empfohlen.
[Offizielle Alloy-Migration](https://grafana.com/docs/alloy/latest/set-up/migrate/from-promtail/).

Empfohlener eigener Schritt: geprüfte Loki-/Alloy-Images, Alloy liest nur ein
dediziertes read-only Pipeline-Logverzeichnis, ohne Socket/Host-Root/pauschales
/var/log. Rotation, Leserechte, Position-Cursor, Secretredaktion vor Versand,
begrenzte Labels und Retention testen. Loki benötigt autorisierten privaten
Ingress und persistente Chunks/Index.
[Loki besitzt keine eingebaute Authentifizierung](https://grafana.com/docs/loki/latest/operations/authentication/).
RAM-/Speicherbedarf und Image-Kompatibilität separat messen; ein zusätzlicher
Stack ist nicht ressourcenfrei. C15 ergänzt deshalb kein ungeprüftes Logging-
Profil und verändert Python-Logging nicht pauschal.
