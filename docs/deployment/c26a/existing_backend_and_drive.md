# C26-A – Bestehendes Backend, Drive-Prüfung und Einquellenpilot

20.10.2026 · Aktuelle Betreiberentscheidung: **vorhandenen Backendcontainer
wiederverwenden**, keine zweite Instanz als Standard. Dieser Nachtrag hat Vorrang
vor dem zuvor vorbereiteten separaten Composeprofil. Status `deployment_prepared`.
Keine SSHverbindung, Host-/Containeränderung, Drivekopie oder reale CS50-Ausführung.
Die Ausführungsumgebung dieses Auftrags ist `penguin`, nicht der Hetzner-Host.

Für den konkreten ersten HTMLpilot gilt die neue
[C26-B2-Schrittfolge](html_pilot.md): ein vorhandenes Source-Binding,
Generator/Preflight und ausdrücklich konfigurierte persistente Mountroots.
Die ursprüngliche lexikalische Sperre für `/app/data` ist dort mit ihrer gezielten
Korrektur und den noch erforderlichen Update-/Betreiberfreigaben dokumentiert.

## Belegte Grundlage und offene tatsächliche Prüfung

Betreiberangaben: laufendes Backend mit `sleep infinity`, Streamlit und
bgutil-ytdlp-POT-Provider als weitere Container; Python unter `/app/.venv/bin/python`,
yt-dlp 2026.08.19, uv/ffmpeg vorhanden, `prepare_cs50`/`execute_cs50` importierbar.
Persistenz unter `/srv/personal-assistant`, Loviscach unter relativem
`data/lectures/loviscach` mit etwa 746 MB. Rund 15 GiB Disk und 2,5 GiB RAM verfügbar
zum Diagnosezeitpunkt. Diese Angaben sind keine eigene Hostabnahme.

Der lokale SSHalias **`coolify`**, Account bisher root, ist inzwischen bestätigt.
Unabhängige Hostkeyverifikation und Codex-SSHfreigabe fehlen weiterhin. Der Betreiber
hat die konkrete Hetznerquelle benannt. Google Drive liegt dagegen auf **`penguin`**;
es ist kein bestätigter Hetzner-Mount. Private absolute lokale Ziel-/Stagingpfade
bleiben außerhalb des versionierten Belegs und werden als Variablen übergeben.

Hier ausschließlich am ausdrücklich benannten lokalen Ziel geprüft: Verzeichnis
vorhanden, selbst kein Symlink, les-/durchsuchbar; `findmnt` meldet **`/mnt/chromeos`,
Typ `9p`**. `os.access(W_OK)` ist im Agentkontext false, ohne Schreibprobe oder
Aussage über andere Betreiberkontexte. Die virtuelle Dateisystemkapazität ist kein
belastbarer Drivequotanachweis. Bei dieser gezielten Prüfung keine Kinddatei gelesen.

**Hetzner-Mountabbildung, Quellinventar/-hashes, Cloudquota/-commit, Containerlimits
und installierte Coderevision bleiben `not_checked`.** Kein SSH und keine
Übertragung. Der Plan lautet Hetzner → privater lokaler Zwischenstand → Google Drive.
Das lokale Workspace-Dateisystem meldete zuletzt rund **6,2 GiB frei**. Das ist
eine Momentaufnahme, keine Freigabe eines Stagingroots. Etwa 746 MB Staging plus
Temp-/Drivecache und gegebenenfalls vollständigen Restore separat budgetieren;
die virtuelle 9p-Kapazität nicht als lokalen oder Cloudspeicher verwenden.

Im Repository geprüft:

- `docker/DockerFile.worker`: Python 3.12, ffmpeg und uv, eingefrorenes
  `lecture-worker`-Extra, `COPY src`/`configuration`, PID1 `sleep infinity`.
  Der untersuchte laufende Altstand kopiert **keine `scripts/`**. Die unten
  dokumentierte C26-B1-Korrektur ergänzt sie im nächsten Imagebuild. Vorhandene
  Modulimporte beweisen weiterhin keinen gestarteten C16-Executor.
- `deployment/Dockerfile` ist das separate minimale C22/C26-Image mit Skripten.
  Es ist eine vorbereitete Alternative, kein Beleg für das laufende Image.
- `scripts/backup_hetzner.sh` hat einen fest eingebauten SSHendpunkt und einen
  ChromeOS-Google-Drive-Zielpfad, kopiert breite Daten-/Logroots und führt auch bei
  `--dry` `mkdir` und SSHprüfungen aus. **Nicht ausführen**, auch nicht zur Vorprüfung.
  Ein deklarierter DVC-gdrive-Remote ist ebenfalls kein nachgewiesener POSIX-Mount.

## Nichtschreibende Diagnose auf dem bestätigten Hetzner-Host

Die folgenden Befehle sind zur manuellen Betreiberdiagnose vorbereitet, hier
**nicht remote ausgeführt**. Variablen müssen konkrete bestätigte Werte enthalten;
keine `.env`, OAuthdatei, SSHkonfiguration oder vollständige Containerkonfiguration
ausgeben. Ergebnisse mit Hostpfaden nur privat übergeben, nicht als Git-Artefakt.

```sh
set -eu
: "${C26_BACKEND_CONTAINER:?Exakter bestehender Containername fehlt}"
hostname
docker inspect --format 'id={{.Id}} image={{.Image}} user={{.Config.User}} working_dir={{.Config.WorkingDir}} running={{.State.Running}}' "$C26_BACKEND_CONTAINER"
docker inspect --format '{{range .Mounts}}{{printf "%s\t%s\t%s\trw=%t\n" .Type .Source .Destination .RW}}{{end}}' "$C26_BACKEND_CONTAINER"
docker inspect --format 'memory={{.HostConfig.Memory}} memory_swap={{.HostConfig.MemorySwap}} nano_cpus={{.HostConfig.NanoCpus}} cpu_quota={{.HostConfig.CpuQuota}} cpu_period={{.HostConfig.CpuPeriod}} cpuset={{.HostConfig.CpusetCpus}} pids={{.HostConfig.PidsLimit}} restart={{.HostConfig.RestartPolicy.Name}} network={{.HostConfig.NetworkMode}}' "$C26_BACKEND_CONTAINER"
docker top "$C26_BACKEND_CONTAINER" -eo pid,comm
command -v rsync || true
```

In einer frischen Shell mit `set -e` ausführen, damit fehlgeschlagene Prüfungen
abbrechen. Keine `.Mounts`-Quelle vor bestätigter Identität übernehmen. Keine
Mountoptionen/Environment-/Label-Gesamtdumps oder Prozessargumente ausgeben:
diese könnten Tokens enthalten. Für Streamlit/Provider die gleichen gefilterten
Inspectbefehle nur mit deren jeweils bestätigtem Namen wiederholen. Prüfen:
getrennte Container, getrennte beschreibbare Mounts, keine konkurrierenden Writer
auf den Pilotroot und kein zusätzlicher UI-/Providerdienst im Backend.

Lokale Mountprüfung auf **`penguin`** mit dem benannten Datenpfad als Variable:

```sh
set -eu
: "${C26_LOCAL_DRIVE_DATA:?Bestaetigter lokaler Drive-Datenpfad fehlt}"
test -d "$C26_LOCAL_DRIVE_DATA"
test ! -L "$C26_LOCAL_DRIVE_DATA"
mountpoint -q -- /mnt/chromeos || { echo 'blocked_local_drive_mount'; exit 2; }
findmnt --target "$C26_LOCAL_DRIVE_DATA" --noheadings --output TARGET,FSTYPE
df -B1 --output=size,used,avail -- "$C26_LOCAL_DRIVE_DATA"
command -v rsync || true
command -v rclone || true
```

Das Unterverzeichnis ist nicht selbst ein Mountpunkt; die lokale Integration läuft
hier über `/mnt/chromeos`. Bei fehlender Integration abbrechen. Account/Ordner-ID,
Zugriffskreis und Cloudquota separat privat bestätigen; `df` kann synthetische Werte
liefern. Keine Konfigurations-/Secretdumps oder Cloudverbindung auf Verdacht.
**Kein Drive-Mount wird auf Hetzner eingerichtet.**

Zusätzliche kleine Komponentenprüfung, ausschließlich nach erlaubtem Read-only-
`docker exec`; sie installiert nichts und startet keinen Job:

```sh
docker exec -i --workdir /app "$C26_BACKEND_CONTAINER" /app/.venv/bin/python -B - <<'PY'
import importlib.metadata as metadata
import json
import shutil
from pathlib import Path
packages = {}
for name in ('yt-dlp', 'httpx', 'pydantic', 'PyMuPDF'):
    try:
        packages[name] = metadata.version(name)
    except metadata.PackageNotFoundError:
        packages[name] = None
files = ('src/tools_lecture/prepare_cs50.py', 'src/tools_lecture/execute_cs50.py',
         'src/tools_materials/batch.py', 'src/tools_materials/processing.py',
         'scripts/cs50_batch.py', 'scripts/cs50_worker.py', 'scripts/deployment.py')
print(json.dumps({'packages': packages,
                  'tools': {n: shutil.which(n) is not None for n in ('uv', 'ffmpeg')},
                  'files': {n: (Path('/app') / n).is_file() for n in files}}))
PY
```

Dateipräsenz allein bestätigt keine Revision oder Funktionsfähigkeit. Image-ID,
Deploymentbeleg und exakte installierte Coderevision privat zuordnen; danach erst
die bestätigten Module mit `--help`/synthetischer Probe prüfen. Fehlende Skripte
blockieren die untenstehenden Befehle. Keine spontane Installation, `uv sync`,
Codekopie, Gitpull im Container oder Imageänderung. Ein vorhandener freigegebener
Codemount kann nach bestätigter Revision genügen; er wird nicht vorausgesetzt.
Die [Docker-Inspect-Dokumentation](https://docs.docker.com/reference/cli/docker/container/inspect/)
beschreibt die gefilterte Ausgabe; kein Inspectresultat des Zielhosts liegt hier vor.

## Architekturvergleich und Ressourcen

| Variante | Zusätzliche Disk | Trennung / Risiko | Entscheidung |
| --- | --- | --- | --- |
| Bestehendes Backend | Keine zusätzliche Imageschicht; Pilotdaten/Temp bleiben erforderlich | Gemeinsame Limits, Mounts und Netz; Execjob wird nicht automatisch neu gestartet; verfügbare Revision offen | Betreiberwahl für den ersten kontrollierten Einzelpilot, nach Diagnose |
| Weiterer Worker mit exakt gleichem Image | Geteilte unveränderliche Layer; eigener Writable-Layer/Logs/Daten | Bessere Prozess-/Ressourcen-/Netztrennung, benötigt neue Container-/Mountfreigabe | Nur spätere Alternative, hier nicht starten |
| Reduziertes C22/C26-Image | Zusätzliche, tatsächlich noch ungemessene Image-/Buildbytes | Engere Abhängigkeiten und expliziter Workerstart, aber Build/Pull/Installation nötig | Vorbereitetes Composepaket, aktuell kein Standard und kein Build |

Die gemeldeten 3,49 GB virtuellen Imagebytes, gemeinsamen Layer, 3,57 GB BuildKit-
Cache und 5,0 GB unter `/var/lib/docker` sind unterschiedliche Messgrößen. Nicht
addieren oder daraus eine Löschmenge ableiten. Ältere Images/Cache bleiben erhalten.
746 MB Loviscach müssen für einen Rawpilot von höchstens 1 MiB nicht vorab gelöscht
werden. Vollkurs-, Audio-/Videovolumen ist unbekannt und nicht pauschal freigegeben.

Vorschlag bleibt: ein aktiver Job, 5 GiB Diskreserve, bestehende C16-Limits
90 s Wall / 60 s CPU / 768 MiB virtueller Workflowadressraum; PDF zusätzlich
10 s / 512 MiB und höchstens 20 Seiten/20 Bilder. Die [kleine Budgetdatei](../../../deployment/cs50-worker.hetzner-small.limits.json.example)
begrenzt Dateibestände; im Erstpilot wird trotzdem **genau eine** Quelle ausgewählt.
Keine Container-CPU-/RAMbegrenzung lässt sich durch `docker exec` pro Job setzen.
Das vorbereitete 1-CPU-/1-GiB-Containerprofil ist im bestehenden Container erst
wirksam, wenn dessen tatsächlich bestätigte Limits dem entsprechen. Änderungen
daran sind gesondert freizugeben und betreffen alle Backendprozesse. Adressraum ist
kein aggregiertes RSSlimit. Fehlende Begrenzung offen berichten, nicht als aktiv ausgeben.

## Loviscach: Hetzner → penguin → Drive, keine Entfernung

**Aktuell keine Übertragung und keine Bestandsöffnung auf Hetzner.** Vor Übernahme:

1. Exakte Hostquelle aus der bestätigten Mountabbildung bestimmen. Quellinventar
   ausschließlich darunter: relative Namen, regulärer Typ, Größe, SHA256,
   Dateianzahl/Gesamtsumme, Bytegleichheiten und Dateistatistik vor/nach Lesen.
   Symlinks, Spezialdateien, wechselnde Bytes oder unbekannte Unter-Mounts blockieren.
   Private Manifeste versionieren; keine Namen, Texte oder private Pfade ins Git.
2. Neuen privaten lokalen Staging-/Belegroot außerhalb von Git und Drive benennen,
   vorhandene Elternrechte und ausreichenden Speicher bestätigen. Kein solcher
   Root ist bisher freigegeben oder angelegt. Drivekonto/Ordner-ID und neuen Zielunterordner
   bestätigen. Vorhandene Ziele inventarisieren: gleiche Namen/abweichende Hashes,
   Byte-Duplikate, Unicode-/Casekollisionen und mehrfach gleich benannte Driveobjekte
   getrennt behandeln. Nichts zusammenführen/überschreiben; Konflikte blockieren.
3. Writerfreiheit und Quellstabilität bestätigen. Sourcebindungen, Raw-/Parsed-
   Artefakte, Receipts, C18-Zustände/Kataloge, C23-Versionen, DVCbezüge und bestehende
   Review-/Indexreferenzen ausschließlich über ausdrücklich freigegebene Metadaten
   erfassen. Fehlende Prüfrechte bleiben Blocker. Ein Cloudbackup ändert keine IDs
   oder Pfade und macht Originalreferenzen nicht entbehrlich.
4. Privaten Manifest-/Logroot, Cloudlese-/Schreibrechte, Datenumfang, Zugriff,
   Retention, Bandbreite, Mount-/VFS-Cachebudget und mindestens 5 GiB lokalen
   Restfreiraum ausdrücklich freigeben. 746 MB ist eine gemeldete Größenordnung,
   kein geprüftes Inventar; Cache und spätere Verifikationsdownloads zusätzlich planen.
5. **Erster Kopierschritt Hetzner → lokaler Stagingroot**, erst nach bestätigtem
   Hostkey sowie SSH-/Inventur-/Rootanlagefreigabe. Das neue
   [nur lesende Inventarskript](../../../scripts/c26_copy_inventory.py) verwendet
   ausschließlich stdlib; relative Namen, SHA256, Größen und Verzeichnisliste,
   höchstens 20.000 Einträge/2 GiB. Es lehnt Symlinks, Spezialdateien, Unter-Mounts
   und beobachtete Änderungen ab, schreibt keine Quelldatei und ist kein Snapshot.
   Writerfreiheit und Vorher-/Nachhervergleich bleiben notwendig. Code-/Skriptrevision
   vor Remoteausführung prüfen. Alle folgenden Befehle laufen auf **penguin**:

   ```sh
   set -euo pipefail
   set -o noclobber
   umask 077
   : "${C26_LOCAL_STAGE:?Neuer freigegebener privater lokaler Stagingroot fehlt}"
   : "${C26_COPY_EVIDENCE:?Neuer freigegebener privater Belegroot fehlt}"
   test ! -e "$C26_LOCAL_STAGE" && test ! -L "$C26_LOCAL_STAGE"
   test ! -e "$C26_COPY_EVIDENCE" && test ! -L "$C26_COPY_EVIDENCE"
   # Nur nach ausdruecklicher Freigabe dieser Rootanlage und Remoteinventur:
   mkdir -m 700 -- "$C26_LOCAL_STAGE" "$C26_COPY_EVIDENCE"
   ssh -o StrictHostKeyChecking=yes coolify \
     python3 -B - /srv/personal-assistant/data/lectures/loviscach \
     < scripts/c26_copy_inventory.py > "$C26_COPY_EVIDENCE/source-before.json"
   rsync --recursive --protect-args --ignore-existing --no-links --no-specials --no-devices \
     --dry-run --itemize-changes -e 'ssh -o StrictHostKeyChecking=yes' \
     coolify:/srv/personal-assistant/data/lectures/loviscach/ "$C26_LOCAL_STAGE/"
   ```

   Die identische Kopieraktion ohne `--dry-run` benötigt eine **eigene Freigabe der
   ersten Übertragung**. rsync/Python müssen schon vorhanden sein; keine Installation.
   Kein `move`, `sync`, `--delete` oder `--remove-source-files`.
   `--ignore-existing` bewahrt Konflikte, bestätigt aber keine Gleichheit. Das
   [rsync-Handbuch](https://download.samba.org/pub/rsync/rsync.1.html) unterscheidet
   Vorschau, Übertragung und Prüfsummen; der Exitcode ersetzt nicht die Abnahme.
6. Quelle erneut inventarisieren und den lokalen Zwischenstand unabhängig hashen:

   ```sh
   set -euo pipefail
   set -o noclobber
   : "${C26_LOCAL_STAGE:?}" "${C26_COPY_EVIDENCE:?}"
   ssh -o StrictHostKeyChecking=yes coolify \
     python3 -B - /srv/personal-assistant/data/lectures/loviscach \
     < scripts/c26_copy_inventory.py > "$C26_COPY_EVIDENCE/source-after.json"
   python3 -B scripts/c26_copy_inventory.py "$C26_LOCAL_STAGE" \
     > "$C26_COPY_EVIDENCE/stage.json"
   cmp -- "$C26_COPY_EVIDENCE/source-before.json" "$C26_COPY_EVIDENCE/source-after.json"
   cmp -- "$C26_COPY_EVIDENCE/source-before.json" "$C26_COPY_EVIDENCE/stage.json"
   ```

   Nur bei Exit 0 aller Inventaraufrufe und identischen kanonischen Manifesten ist
   die erste Kopie verifiziert: alle Namen, Verzeichnisse, Größen und SHA256,
   einschließlich fehlender/zusätzlicher Dateien. Private Belege 0600 behalten.
   Abgebrochene/fehlerhafte Inventare niemals als gleichwertige Erfolge zählen.
7. **Zweiter Kopierschritt penguin → Drive**, nach gesonderter Cloudkopie- und
   Zielanlagefreigabe. Alle Zielpfadkomponenten ohne Symlinks prüfen; Ziel muss ein
   neues Unterverzeichnis des bestätigten lokalen Drive-Datenpfads sein. Keine
   vorhandenen Ziele übernehmen. Vorher Konflikte/Quota/Mountidentität erneut prüfen:

   ```sh
   set -euo pipefail
   : "${C26_LOCAL_STAGE:?}" "${C26_COPY_EVIDENCE:?}"
   : "${C26_LOCAL_DRIVE_DATA:?}" "${C26_NEW_DRIVE_TARGET:?}"
   mountpoint -q -- /mnt/chromeos || exit 2
   test ! -e "$C26_NEW_DRIVE_TARGET" && test ! -L "$C26_NEW_DRIVE_TARGET"
   # Nur nach Upload-/Zielanlagefreigabe und bestaetigter Unterordnung:
   mkdir -- "$C26_NEW_DRIVE_TARGET"
   rsync --recursive --ignore-existing --no-links --no-specials --no-devices \
     --dry-run --itemize-changes -- "$C26_LOCAL_STAGE/" "$C26_NEW_DRIVE_TARGET/"
   ```

   Nach bestätigter Vorschau dieselbe Auswahl ohne `--dry-run` kopieren. Hetzner und
   Staging bleiben erhalten. Danach Staging unter neuem Belegnamen erneut hashen,
   Driveziel mit demselben Skript inventarisieren und mit dem unveränderten
   Quellmanifest vergleichen. Drive-ACLs sind separat zu prüfen; POSIXmodi des
   Mounts allein garantieren keinen privaten Cloudzugriff.
8. Cloudcommit/Synchronisationsabschluss bestätigen. Zusätzlich unabhängige
   Byteprüfung **über den Provider**, nicht nur denselben gecachten 9p-/Drive-Mount.
   Bei bereits vorhandenem ausdrücklich freigegebenem rclone-Remote wäre möglich:

   ```sh
   : "${C26_LOCAL_STAGE:?}"
   : "${C26_APPROVED_DRIVE_REMOTE_TARGET:?Exakter bestaetigter Remote-Unterordner fehlt}"
   rclone check "$C26_LOCAL_STAGE" "$C26_APPROVED_DRIVE_REMOTE_TARGET" \
     --download --checkers 1
   ```

   [rclone check --download](https://rclone.org/commands/rclone_check/) liest die
   Remoteinhalte zum Vergleich und ändert Quelle/Ziel nicht. Kein `--one-way`,
   damit zusätzliche Zieldateien auffallen. Das ist ein gesondert zu erlaubender
   Cloudread mit Netzwerkvolumen; keine Annahme vorhandener Konfiguration.
   Ohne unabhängigen Providerread bleibt `verification_pending`. Ein frisch
   autorisierter Restore in ein neues privates Ziel mit identischen SHA256 und
   geprüfter Referenzclosure ist zusätzlich vor einer Löschentscheidung nötig.
9. Erst dann separat entscheiden, ob bestimmte lokale Kopien überhaupt entbehrlich
   sind. Aktive Raw-/Workflow-/ContentStorebezüge blockieren die Entfernung oder
   verlangen einen eigenen genehmigten Referenz-/Migrationsvertrag. **Keine lokale
   Löschung durch C26-A**, auch nicht nach erfolgreichem Backup. Quelle bleibt erhalten.

Die Cloud ist ein Backupziel, kein Live-Root für SQLite, Queue oder C23. Ein reines
Dateibackup ersetzt keinen konsistenten C22-/C23-Snapshot aktiver Datenbanken.

## Unterstützte CS50-Wege, keine pauschale Gesamtkursfähigkeit

| Material | Tatsächlicher Einstieg / Grenze |
| --- | --- |
| Offizielles SRT | `src.tools_lecture.execute_cs50 --plan … --course … --section … --max-lectures 1 --execute`: CDN-SRTdownload und Normalisierung, persistierte Actions/Hashes im `execution.v1.json`; kein HTML-/PDF-/Videodownloader. CLI führt beide Actions zusammen aus; kein separat queued Downloadjob und kein C18-Materialworkflow |
| HTML | `scripts.cs50_materials`/`scripts.cs50_batch` mit MaterialDownloader und HTML-v2; explizites geprüftes Discoverymanifest/Sourcebinding erforderlich, kein unbegrenzter Crawler |
| PDF | MaterialDownloader + PDF-v2/C19/C18; vorhandene Byte-/Seiten-/Bild-/Zeitlimits, keine allgemeine OCRgarantie |
| Code | Vorhandener code-v1 für freigegebene direkte Textdateien wie py/c/h/sql/js/css/txt/md; keine Ausführung des extrahierten Codes, keine pauschale ZIP-/Repositoriumübernahme |
| Audio/Video | Discovery erkennt Varianten; andere yt-dlp-/ffmpeg-/Transkriptionsmodule existieren. Das beweist weder Pipelineintegration noch Download-/ASR-/LLMfreigabe. Im C26-Materialworkflow weiterhin unsupported |

`prepare_cs50` liest explizite lokale Index-/Week-Snapshots und entdeckt Links;
Importierbarkeit bedeutet keine Live-Entdeckung oder End-to-End-Verarbeitung.
yt-dlp/ffmpeg sind für den hier empfohlenen HTML-Erstpilot nicht erforderlich.

## Exakte Pilotfolge im vorhandenen Container – erst nach Freigabe

Empfehlung: **eine konkrete HTML-Notesquelle**, deren Course/Resource-ID/URL der
Betreiber ausdrücklich benennt und freigibt. Kein Gesamtkurs, kein Video, kein LLM.
Ein Download ist hier ein persistiert belegter synchroner CLI-Schritt; C16 besitzt
keinen aktivierten queued `material_download`-Prozess. Ein Processingjob ist der
vorhandene C16-/C18-Workflow. Diese Unterscheidung nicht als zwei Queuejobs ausgeben.

Voraussetzungen: Skripte und freigegebene Revision im Container nachgewiesen,
Source-/Lizenz-/Robots-/Netzfreigabe, private Limits-/Controller-/Tokendateien und
explizite neue Pilotunterroots **innerhalb vorhandener persistenter Bind-Mounts**.
Keine Datenablage nur im Writable-Layer. Keine Wiederverwendung des Loviscachroots
als C26-Archiv/Jobroot; keine bestehenden Stores initialisieren oder umschreiben.
Fehlende Voraussetzungen blockieren; keine neue Instanz als automatischer Ersatz.

Alle nachstehenden Variablen bezeichnen bestätigte **Containerpfade** bzw. den
bestätigten Container/Account, keine neu geratenen Hostpfade. Freie Budgets und
Existenz/Privatrechte der Elternroots vorher prüfen. Befehle bisher nicht ausgeführt:

```sh
: "${C26_BACKEND_CONTAINER:?}" "${C26_UID_GID:?}"
: "${C26_MANIFEST:?}" "${C26_COURSE:?}" "${C26_RESOURCE:?}"
: "${C26_BATCH_FILE:?}" "${C26_LIMITS:?}" "${C26_APPROVALS:?}"
: "${C26_ARCHIVE:?}" "${C26_EXPORTS:?}" "${C26_NEW_CATALOG_DIR:?}"
: "${C26_CONFIG:?}" "${C26_TOKEN_FILE:?}"
c26existing() {
  docker exec --user "$C26_UID_GID" --workdir /app "$C26_BACKEND_CONTAINER" \
    /app/.venv/bin/python -B -m "$@"
}
# 1. Nur Metadatenplan, neuer Ausgabename; genau eine Resource auswählen.
c26existing scripts.cs50_batch plan --manifest "$C26_MANIFEST" \
  --course "$C26_COURSE" --resource "$C26_RESOURCE" \
  --limits "$C26_LIMITS" --output "$C26_BATCH_FILE"
# 2. Betreiber prüft eine Zeile, genaue URL, erwarteten SHA (falls vorhanden),
#    Kapazitaetsplan und genau diese Sourcefreigabe; dann Vorschau ohne HTTP.
c26existing scripts.cs50_batch download --batch "$C26_BATCH_FILE" \
  --archive "$C26_ARCHIVE" --limits "$C26_LIMITS"
# 3. Nur nach Downloadfreigabe, max. 1 MiB Raw, kein automatischer Retry.
c26existing scripts.cs50_batch download --batch "$C26_BATCH_FILE" \
  --archive "$C26_ARCHIVE" --approvals "$C26_APPROVALS" \
  --limits "$C26_LIMITS" --confirm --output "$C26_EXPORTS/download-r1.json"
# 4. Raw-/Receipt-SHA kontrollieren, genau ein neues Katalogfragment versiegeln.
c26existing scripts.cs50_batch seal --batch "$C26_BATCH_FILE" \
  --archive "$C26_ARCHIVE" --approvals "$C26_APPROVALS" \
  --limits "$C26_LIMITS" --confirm --output "$C26_NEW_CATALOG_DIR"
```

Danach übernimmt der Betreiber bewusst genau den versiegelten Eintrag in eine
freigegebene Controllerrevision mit echtem Principal/Coursegrant und
`max_parallel=1`, `execution_enabled=true`, `workflows_enabled=true`.
Keine Tokenwerte in Kommandos oder Logs. Bestehenden Worker am selben Root zuerst
identifizieren; kein zweiter Executor. In **einer separaten bestätigten Konsole**
den einzigen Worker im vorhandenen Container im Vordergrund betreiben:

```sh
: "${C26_BACKEND_CONTAINER:?}" "${C26_UID_GID:?}" "${C26_CONFIG:?}" "${C26_LIMITS:?}"
docker exec -it --user "$C26_UID_GID" --workdir /app "$C26_BACKEND_CONTAINER" \
  /app/.venv/bin/python -B -m scripts.cs50_worker \
  --config "$C26_CONFIG" --limits "$C26_LIMITS"
```

In der Operator-Konsole genau einen Ref einreichen und dessen Status lesen:

```sh
: "${C26_SOURCE_REF:?Exakten Ref erst aus dem versiegelten Katalog uebernehmen}"
c26existing scripts.cs50_batch workflow execute --config "$C26_CONFIG" \
  --token-file "$C26_TOKEN_FILE" --catalog "$C26_NEW_CATALOG_DIR/catalog.json" \
  --source-ref "$C26_SOURCE_REF" --limits "$C26_LIMITS" --confirm
c26existing scripts.cs50_batch workflow report --config "$C26_CONFIG" \
  --token-file "$C26_TOKEN_FILE" --catalog "$C26_NEW_CATALOG_DIR/catalog.json" \
  --source-ref "$C26_SOURCE_REF" --limits "$C26_LIMITS"
```

Cancel/Wiederaufnahme verwenden denselben Befehl mit `workflow cancel` bzw.
`workflow resume` und ausdrücklichem `--confirm`. Worker über dessen eigene Konsole
geordnet beenden, nicht den Backend-/UI-/Providercontainer stoppen. Nach einem
tatsächlichen Containerneustart startet ein Execworker laut
[Docker-Exec-Vertrag](https://docs.docker.com/reference/cli/docker/container/exec/)
**nicht automatisch** neu. C16/C18 persistieren nur auf dem bestätigten Bind-Mount;
manuell denselben Worker mit identischen Roots starten, Restart-Reconciliation
lesen, dann bewusst Resume. Ein echter Containerneustarttest bedarf eines eigenen
Wartungsfensters und ist hier nicht freigegeben. Keine detach-/PIDdatei-Killlösung.

Erfolg erst bei persistiertem `completed`, geprüften Raw-/Receipt-/Outputhashes,
NormalizedDocument-Provenienz und unveränderten Originalen. Kontrollierten Cancel/
Workerneustart/Resume zunächst synthetisch, danach nur freigegebenen Einzelpilot
prüfen. Auf Loviscach-Gold, fachliche Realabnahme oder automatische Bereinigung
lässt sich daraus nichts übertragen.

## Noch benötigte konkrete Entscheidungen

Unabhängige Hostkeyverifikation und SSH-/Read-only-Hostfreigabe oder gefilterte
Betreiberdiagnose; Containername und Mountabbildung; Drive-Remote/Ordner-ID/Quota
und unabhängiger Verifyweg;
private Inventar-/Restoreziele, Quellstabilität und Referenzprüfrechte; gesonderte
Cloudkopie-/Cloudreadfreigabe und später gegebenenfalls eigene Löschentscheidung;
installierte Coderevision/fehlende Skriptbereitstellung; bestehende Ressourcenlimits
und eine konkret autorisierte CS50-HTMLquelle samt Pilotroots/Principal.
Bis dahin: **lokales Driveverzeichnis metadatenseitig erreichbar, Cloudpersistenz
`not_checked`, Übernahme `awaiting_copy_authorization`,
Realpilot `blocked`, lokale Loviscach-Löschung `not_authorized`.**

## C26-B1 – Skripte im vorhandenen Worker-Image

21.10.2026. Der Betreiber bestätigt für den bestehenden Coolify-Backenddienst
**Dockerfile `docker/DockerFile.worker`, Build-Kontext Repositorywurzel**
(Base Directory `/`). Keine eigene SSH-/Coolifyprüfung und keine Serveränderung.
Der Fehler liegt im Imageinhalt, nicht in fehlendem yt-dlp: Das bisherige
Dockerfile kopiert die vorhandenen C26-Skripte nicht.

Die Korrektur kopiert ausschließlich `cs50_batch.py`, `cs50_worker.py`,
`cs50_material_quality.py`, `deployment.py`, `cs50_materials.py` und
`cs50_workflow.py` sowie den neuen Prüfeinstieg `worker_image_smoke.py`.
Die beiden zusätzlichen Material-/Workflow-CLIs gehören bereits zum integrierten
C22/C26-Laufzeitumfang. Andere Skripte, insbesondere Backup-/Cleanup-/Demo- und
LLMprogramme, werden nicht übernommen.
Demo-Unterbefehle mit zusätzlichen Entwicklungsdateien gehören nicht zum
Workerumfang. Katalog-/Snapshotmanifeste, Pilotkonfiguration, Limits und Tokenfiles
müssen wie bisher ausdrücklich über die bestätigten privaten Mounts bereitstehen;
der Standardpfad unter `docs/course_sources` ist kein im Image enthaltener Korpus.

`docker/DockerFile.worker.dockerignore` begrenzt den **Root-Build-Kontext** auf
Lock-/Projektdateien, Laufzeit-Pythoncode, diese sieben Skripte und die vier
bisherigen YAML-Konfigurationen. `_dev*`, Bytecode, Umgebungsdateien und
Schlüsseldateien bleiben ausgeschlossen, ebenso `data`, `logs`, `.git`, `.venv`,
Dokumente und das nicht für den Worker benötigte HTMLmaterial unter `src`.
Die bisherige `docker/.dockerignore` schützt einen Build aus der Repositorywurzel
nicht. Docker unterstützt die verwendete
[Dockerfile-spezifische Ausschlussdatei](https://docs.docker.com/build/concepts/context/).
Andere Dockerfiles erhalten durch diese Änderung keinen neuen Build-Kontext.

Jeder künftige Build startet automatisch:

```sh
/app/.venv/bin/python -B -m scripts.worker_image_smoke
```

Der Prüfer verlangt alle sechs Laufzeitdateien und startet die vier angeforderten
Module jeweils mit `--help`, demselben Interpreter, 30-s-Deadline und bereinigter
Umgebung ohne Credentials oder produktive Konfigurationsvariablen. Exit 0 und
Argparse-Ausgabe sind erforderlich; Fehlerausgaben werden nicht weitergereicht.
Der Dockerfile-Schritt verwendet
[`RUN --network=none`](https://docs.docker.com/reference/dockerfile/).
Er startet keine Jobs und benötigt keine Datenmounts. Fehlende Imports blockieren
den Build. Dies ersetzt weder einen Processingtest noch eine Hostabnahme.

`uv sync --frozen --no-default-groups --extra lecture-worker --no-editable`
bleibt unverändert. Basis plus Extra reichen für die geprüften C26-Importpfade;
keine Dependencyänderung, kein erneutes Installieren von yt-dlp im Container.
`WORKDIR /app`, Standardstart **`sleep infinity`**, bestehende Bind-Mounts und
Restart-Policy bleiben unverändert. Ein Execworker startet nach einem Restart
weiterhin nicht automatisch neu. Die bisher beweglichen Python-/uv-/APTquellen
sind unverändert: der eingefrorene Pythonlock ist keine Zusage bitidentischer
Gesamtimages bei beliebigen späteren Neubuilds.

### Spätere manuelle Coolify-Neubereitstellung

**Nur nach Merge und gesonderter Betreiberfreigabe ausführen.** Hier weder
Build auf Hetzner noch Redeploy durchgeführt. Auf ausreichenden freien Platz für
neue Layer und Buildcache zusätzlich zur vereinbarten 5-GiB-Reserve achten;
alte Images, Volumes und Caches nicht als Nebenwirkung löschen.

1. Den gemergten Commit auswählen und die bestehende Coolify-Anwendung beibehalten:
   Dockerfile `docker/DockerFile.worker`, Base Directory `/`, bisheriger Startbefehl,
   Restart-Policy, Ports, Benutzer und Ressourcenlimits. Vorher Image-ID und
   gefilterte Mountabbildung mit den obigen Diagnosebefehlen privat festhalten.
   Insbesondere `/srv/personal-assistant` und die bestehenden Containerziele nicht
   umbenennen. Ein Codemount über `/app` oder `/app/scripts` kann die neuen Dateien
   verdecken und muss vor Freigabe geklärt werden.
2. Im bestätigten Wartungsfenster aktive Jobs kontrolliert beenden und den
   **bestehenden** Backenddienst über Coolify aus diesem Commit neu bereitstellen.
   Der Build muss die vier `passed`-Checks liefern; bei Fehler keine manuelle
   Skriptkopie, Installation oder zweite Backendinstanz als Ersatz.
3. Den tatsächlich neu bereitgestellten Container und seine Image-ID bestätigen.
   Mit den gefilterten Inspectbefehlen Mounts, Limits und Restart-Policy gegen den
   Vorzustand vergleichen. Loviscach, Streamlit und POT-Provider unverändert lassen.
4. Im aktualisierten Container folgende reine CLI-Prüfungen ausführen:

```sh
set -eu
: "${C26_BACKEND_CONTAINER:?Bestaetigter aktualisierter Backendcontainer fehlt}"
docker exec --workdir /app "$C26_BACKEND_CONTAINER" /app/.venv/bin/python -B -m scripts.worker_image_smoke
docker exec --workdir /app "$C26_BACKEND_CONTAINER" /app/.venv/bin/python -B -m scripts.cs50_batch --help
docker exec --workdir /app "$C26_BACKEND_CONTAINER" /app/.venv/bin/python -B -m scripts.cs50_worker --help
docker exec --workdir /app "$C26_BACKEND_CONTAINER" /app/.venv/bin/python -B -m scripts.cs50_material_quality --help
docker exec --workdir /app "$C26_BACKEND_CONTAINER" /app/.venv/bin/python -B -m scripts.deployment --help
```

Erwartet: Prüfer Exit 0, viermal `status=passed`; einzelne CLIs Exit 0 und Hilfe.
Keine `.env` oder vollständige Containerkonfiguration ausgeben. Dies bestätigt die
Skriptintegration, nicht die fachliche Qualität oder einen bereits laufenden Job.
Danach erst den oben dokumentierten Einquellenpilot separat freigeben: konkrete
Source/URL und Rechte, explizite private persistente Roots, Principal/Katalog,
verifizierte Mounts und ein aktiver Worker mit bestätigten Ressourcenlimits.
Downloadvorschau vor Ausführung, ein Download und ein Processingjob mit SHA-/Receipt-
und Statusprüfung, kontrollierter Wiederanlauf mit identischen Roots. Keine
pauschale Video-/Audiofreigabe, LLMnutzung oder Drivekopie durch dieses Imageupdate.

### Lokale Imageprüfung auf einem ausreichend großen Buildhost

Die folgenden Befehle sind zusätzlich reproduzierbar, benötigen aber ausreichenden
lokalen Speicher sowie freigegebenen Zugriff auf die bisherigen Basis-/APT-/PyPI-
Buildquellen. Kein Build auf einem fremden Dockerkontext:

```sh
# Aus der Repositorywurzel, mit vorher bestaetigtem lokalem Dockerdaemon.
docker build --file docker/DockerFile.worker --tag personal-assistant-worker:c26b1 .
# Mit vorhandener Testumgebung; keine automatische Dependencyinstallation.
C26_WORKER_TEST_IMAGE=personal-assistant-worker:c26b1 \
  "$C26_PYTHON" -m pytest -q -p no:cacheprovider \
  tests/test_worker_image_content.py::test_built_worker_image
```

Der optionale Imagetest startet ausschließlich einen neuen kurzlebigen
Prüfcontainer: ohne Netzwerk/Pull/Hostmounts, read-only, ohne Capabilities, mit
1 CPU/1 GiB/128 PIDs. Er verändert keinen bestehenden Container. Der tatsächliche
lokale Ausführungsstand einschließlich der nicht ausgeführten Vollimageprüfung
steht im [B1-Prüfvermerk](validation.md#c26-b1--worker-image-integration).
