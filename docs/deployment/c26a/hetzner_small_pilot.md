# C26-A – Kleiner Hetzner-Pilot und ausstehende Hostfreigabe

20.10.2026 · Ergänzung zu [Workervertrag](worker.md) und [Nachweisen](validation.md).
**`deployment_prepared`; Hostinstallation, Staging und Produktivstart nicht freigegeben.**
Aktuelle Betreiberwahl: [vorhandenes Backend verwenden und über penguin sichern](existing_backend_and_drive.md).
Das folgende neue Containerprofil bleibt ausschließlich eine vorbereitete
Alternative. Keine zusätzliche Instanz und kein neues Image als Standard.
Kein SSHzugriff, keine Hostdiagnose durch den Agenten, keine Images gebaut/gepullt,
keine echten Downloads und keine Änderungen an Coolify oder bestehenden Volumes.

## Betreiberangaben und verbleibende Verifikation

Die folgenden Angaben wurden vom Betreiber gemeldet, nicht unabhängig geprüft:

| Bereich | Gemeldeter Stand | Konsequenz für den Pilot |
| --- | --- | --- |
| Identität | `ubuntu-4gb-nbg1-2`, Ubuntu, Kernel 6.8.0-138-generic, x86_64; lokaler Alias inzwischen `coolify` | Unabhängige Hostkeybestätigung und Codex-SSHfreigabe fehlen |
| Account | Aktuell root; kein bestätigter dedizierter Deployaccount | Kein automatisierter Rootzugriff; Account/UIDrechte gesondert freigeben |
| CPU | Zwei vCPU, AMD EPYC Rome | Ein Worker mit einer CPU; keine Whisper-/großen lokalen LLMjobs |
| RAM | 3,7 GiB gesamt, 2,5 GiB verfügbar beim Diagnosezeitpunkt | Momentaufnahme, keine Zusage freier Kapazität beim Start |
| Swap | 4 GiB, davon 1 GiB belegt | Bereits vorhandene Speicherauslastung beachten; kein Swap für neue Container |
| Disk | 38 GiB ext4, 22 GiB belegt, 15 GiB verfügbar | Mindestens 5 GiB Reserve, vorhandene Belegung geschützt |
| Container | Docker 29.8.2, Compose 5.6.0, overlayfs | Versionsangaben ersetzen keinen Container-/cgroup-/Mounttest |
| Bestand | Coolify 4.4.2, Traefik 3.6 healthy; PostgreSQL 15 und Redis 7 aktiv | Keine Änderung, Mitnutzung oder Migration ihrer Daten/Volumes |

Die aus einer SSHsitzung gemeldeten Hostkeyfingerprints sind noch unabhängig über
einen vertrauenswürdigen Kanal zu bestätigen. Die Angaben erteilen weder Zugriff
noch Installationserlaubnis. VPN bleibt optional; kein öffentlicher HTTP-/UIport.

## Ein Profil im bestehenden Composepaket

Die [kleine Envvorlage](../../../deployment/cs50-worker.hetzner-small.env.example)
parametrisiert dieselbe [Compose-Datei](../../../deployment/cs50-worker.compose.yaml).
Keine zweite Anwendung, Queue, Datenbank oder neue Coolify-Infrastruktur.
Pfade und Image-Digest bleiben leer, bis sie ausdrücklich bestätigt sind.
`C26_LIMITS` bindet eine private 0600-Kopie der
[kleinen Budgetvorlage](../../../deployment/cs50-worker.hetzner-small.limits.json.example).
Alle Mounts verlangen bereits vorhandene Ziele; kein automatisches Anlegen.

| Rolle | CPU / RAM / PIDs | tmpfs | Start und Netz |
| --- | --- | --- | --- |
| Processing | 1 / 1024 MiB / 128 | 128 MiB | `restart: no`, kein Netz, genau ein aktiver Job |
| Operator-CLI | 0,25 / 256 MiB / 64 | 64 MiB | Kurzlebiger manueller Aufruf, kein Netz |
| Downloader | 0,5 / 256 MiB / 64 | 32 MiB | Ein serieller CLIlauf im freigegebenen Egressnetz |

Downloader und Processing **nacheinander** betreiben. Während Processing darf nur
die kleine Operator-CLI zusätzlich laufen: zusammen höchstens 1280 MiB konfigurierte
Containerlimits. Das reserviert keinen Speicher und berücksichtigt nicht automatisch
Coolify, Kernelcache oder andere Hostprozesse. Vor dem Pilot aktuellen Hostzustand
prüfen; mindestens 1,5 GiB MemAvailable ist eine vorgeschlagene Startbedingung,
kein gemessener Bedarf oder Beweis ausreichender Kapazität.

`memswap_limit` entspricht jeweils `mem_limit`; laut
[Docker-Ressourcenvertrag](https://docs.docker.com/engine/containers/resource_constraints/)
verhindert dies Container-Swap, sofern der Host die Kontrolle tatsächlich unterstützt.
[tmpfs zählt zum Containerspeicher](https://docs.docker.com/engine/storage/tmpfs/);
sein Budget kommt nicht zusätzlich zum RAMlimit. Die
[Compose-Definition](https://docs.docker.com/reference/compose-file/services/)
wird lokal gerendert; tatsächliche cgroupdurchsetzung bleibt am Ziel zu prüfen.

**1 GiB ist ein Versuchslimit für kleine Materialien.** Bestehendes C16/C18 setzt
768 MiB virtuellen Adressraum pro Workflowprozess und C19 512 MiB pro PDFworker.
Das sind keine RSSwerte; Guardian, Worker, Unterprozesse und tmpfs verbrauchen
zusätzlich Speicher. Deshalb folgt daraus keine 1-GiB-Erfolgsgarantie. Keine
Adressraum-, Parser- oder Zeitlimits erhöht. Erst mit geprüftem Image im separaten
Staging tatsächlichen Peak/cgroupereignisse und Cancel/Cleanup messen. Bei OOM
anhalten, Status/Quarantäne prüfen; keine automatische Wiederholung oder Erhöhung.

## Diskbudgets und schrittweise Mengenplanung

| Grenze der kleinen Budgetdatei | Wert |
| --- | ---: |
| Freiraumreserve pro geprüftem Dateisystem | 5 GiB |
| Maximal ausgewählte Materialien | 3 |
| Raw je Material, bestehender C18-Vertrag | 1 MiB |
| Gesamtes explizites Archivroot | 64 MiB |
| Gesamtes explizites Katalogroot | 128 MiB |
| Gesamtes explizites C16-Jobroot einschließlich temporärer Dateien | 512 MiB |
| Gesamtes explizites Exportroot | 16 MiB |

Die vier Datenbudgets ergeben 720 MiB. Zusätzlich Dockerlogs höchstens 30 MiB pro
Rolle, vorläufig 1 GiB für einen getrennten Pilotsnapshot und 3 GiB für Images/
Buildstaging einplanen. Diese beiden Planungsbeträge müssen nach tatsächlicher
Image-/Snapshotgröße ersetzt werden. 15 GiB gemeldeter Freiraum minus 5 GiB Reserve
ist **keine Downloadfreigabe für zehn GiB**. Andere Dienste können weiter schreiben.
Videos, ASR und komplette Kursdownloads sind nicht Bestandteil dieses kleinen
Profils. Quellengrößen und gesamte CS50-Downloadmenge sind unbekannt.

Der vorhandene `plan`-CLI liefert jetzt `capacity_plan`: Anzahl × Rawlimit,
tatsächliche Snapshotbytes, Kopien je Katalogmaterial und explizite Metadaten-
Planungszuschläge. Das ist eine konservative Zulassungsplanung für diese Auswahl,
keine Vorhersage der entpackten PDFgröße. Pro Material höchstens 20 PDFseiten/
20 Bilder, 1000 Blöcke; native Worker- und Dateilimits bleiben wirksam.
Vor einem neuen Batch genug Platz für Reserve plus dessen Planungszuschläge sowie
Job-/Reportbudget verlangen. Ausgewählte Dateien können bei Größen-/Zeit-/Struktur-
grenzen dennoch abgewiesen werden. Nur bestätigte erfolgreiche Ergebnisse zählen.

Neue C26-Kapazitätsprüfungen umschließen die vorhandenen Writer:

- Download vor dem Start und vor jedem HTTPstreamchunk: Reserve, Archivgröße und
  erwarteter nächster Chunk. Bei Abbruch kein fertiges Raw, bestehender Fehlerreceipt.
- Katalog vor Erstellung: vorhandener Bestand plus geplante neue Kopien prüfen.
- Execute/Resume: Jobrootbudget und Reserve vor neuer Einreichung; Cancel/Report
  bleiben über C22 mit dessen bestehender Mindestreserve nutzbar. Bei Speicherknappheit
  ohne `--output` diagnostizieren, damit kein neuer Export erzwungen wird.
- Worker vor Öffnen und vor Dispatch: Freiraum pro Schleifenschritt, stat-only
  Dateigröße einmal pro Sekunde. Bei Überschreitung verlässt er den bestehenden
  Servepfad mit dessen Childcleanup. Neustart erst nach Operatorprüfung; bestehendes
  Restart-Reconciliation und ausdrückliches C18-Resume, kein automatisches Reparse.
- Export vor neuer Dateipublikation: Reportbudget und Reserve; kein Überschreiben.

**Das sind Stoppschwellen, keine Dateisystemquotas oder atomare Platzreservierung.**
Zwischen Kontrollen können Prozesse und fremde Hostwriter weiter schreiben;
Cleanup/SQLite/Fehlerreceipts benötigen ebenfalls Platz. Ein laufender Job kann
das Größenbudget bis zur nächsten Kontrolle überschreiten. tmpfs wird durch dessen
Mount-/Speicherlimit begrenzt. Harte Diskgrenzen erfordern separat geprüfte
Filesystemquotas oder dedizierte Volumes; nichts davon wird hier eingerichtet.
Verzeichnisinventur ist auf 20.000 Einträge begrenzt, folgt keinen Symlinks und
liest nur Größen. Keine Retention, Löschung, GC oder eigenständige Recovery.

## Manueller Pilot nach gesonderter Freigabe

1. Exakte Host-/Account-/Root-/Image-/Sourcefreigabe unten vervollständigen. Aktuelle
   RAM-/Disk-/Coolifygesundheit mit Betreiber prüfen. Keine Pulls/Downloads als Probe.
2. Nur neue separate private Roots unter dem vorgeschlagenen
   `/srv/personal-assistant` nach expliziter Freigabe anlegen: specs/archive/catalog/
   jobs/exports/config/secrets/backups. Tatsächliche UID/GID/Filesystem prüfen.
   Coolify-, Docker-, PostgreSQL-/Redisroots und bestehende Volumes weder scannen
   noch chownen/übermounten. Die Defaults bestätigen keine freien Hostpfade.
3. Digestgeprüftes Image und Envdatei freigeben; kleine Limitsdatei als 0600 und
   Controller als 0600 bereitstellen, Roots 0700. Controller bleibt bis zur
   ausdrücklichen Aktivierung ohne Schreibrechte und mit Ausführung deaktiviert.
4. Compose lokal/auf freigegebenem Host ausschließlich rendern und prüfen:

   ```sh
   docker compose --env-file "$APPROVED_C26_SMALL_ENV" \
     -f deployment/cs50-worker.compose.yaml --profile processing config
   ```

   Keine Commands dieses Abschnitts wurden auf dem Host ausgeführt. Zuerst kleine
   synthetische HTML-/Code-/PDFquelle mit bestehendem Testtransport bzw. lokalem
   genehmigtem Testbundle verwenden; kein Mock als tatsächlichen Download ausgeben.
5. Für höchstens drei autorisierte echte Materialien vorhandenen
   [CLIablauf](worker.md#cli-ablauf-nach-gesonderter-staging--und-sourcefreigabe) verwenden: Plan samt Kapazitätszahlen
   prüfen → Downloader einmalig, Processing gestoppt → Hash-/Receiptprüfung → neuen
   Katalog versiegeln → Controllerkatalog bewusst prüfen/übernehmen → Worker starten.
   `--limits` oder das gemountete `C26_LIMITS_FILE` verwenden. Fehlende konfigurierte
   Limitsdatei blockiert, kein Rückfall auf generische 512-MiB-Defaults im Container.
6. Erst ein Material ausführen, RAM-/Diskwachstum, Health und echte Ergebnisse
   prüfen; dann die übrigen einzeln. Cancel, kontrollierter Workerstop, Neustart und
   ausdrückliches Resume prüfen. Fremde oder alte Workspaces nicht übernehmen.
7. Worker stoppen, Status/Hashes exportieren und bestehendes C22-Backup/Restore in
   neue Ziele prüfen. Archiv, Spezifikationen, Konfiguration und Exporte benötigen
   zusätzlich getrennte freigegebene Sicherung: C22 erfasst sie nicht vollständig.
   C23 bleibt unbenutzt; kein behaupteter Verbundsnapshot. Wachsende Altbestände
   blockieren den nächsten Batch, bis der Betreiber deren Aufbewahrung entscheidet.

## Konkret auszufüllende Installationsfreigabe

Alle Felder **offen**, sofern oben nur Diagnoseangaben vorliegen:

- Betreiber/Datum/Beleg, exakter SSHalias/-Zielhost, unabhängig bestätigter Hostkey
  samt Vertrauenskanal; ausdrücklich erlaubte SSHaktionen und Zeitfenster.
- Dedizierter Deployaccount und Rechte, Docker-/Coolifyzugriff, geprüfte UID10001-
  Bindung oder ausdrücklich angepasste Identität; kein stiller Rootaccount.
- Exakte neue Hostpfade je Mount, Besitzer, Rechte, freier Zustand/Filesystem;
  geschützte bestehende Dienste/Volumes und zulässiger Probe-/Restorepfad.
- Exakte Python-/uv-/Runtime-Imagereferenzen und Digests, erlaubter Build-/Importweg,
  Imagegrößen und Netz-/Registryrechte; keine pauschale Pullfreigabe.
- Bestätigung der oben angegebenen CPU-/RAM-/PID-/Swap-/tmpfs-/Disklimits,
  aktueller RAM-/Disksnapshot, Alarm-/Abbruchverantwortlicher und Kapazitätsreserve.
- Höchstens drei konkrete Course-/Material-/Source-IDs, URLs, Nutzungs-/Lizenz-/
  Robotsbelege, erlaubte Schritte/Netzziele/Rate und gegebenenfalls erwartete SHA256;
  gültige C16-Principal-/Coursegrants. Synthetische Belege ersetzen diese nicht.
- Exakte Snapshot-/Restoreziele, Zugriff, Speicherbudget, Retention, Widerruf und
  Umgang mit Teilfehlern. Keine automatische Löschung oder Aufräumfreigabe.
- Getrennte Zustimmung zu Installation, synthetischem Hosttest, anschließendem
  begrenztem Realdownload und Start. Keiner dieser Schritte gilt aktuell als erteilt.

Die lokale Bereitstellung erteilt keine fachliche CS50-/Goldabnahme und schließt
C26-/Storage-/Restore-/Go-live-Issues nicht. MAINT bleibt On Hold.
