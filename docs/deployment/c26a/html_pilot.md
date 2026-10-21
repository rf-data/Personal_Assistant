# C26-B2/B3 – Ein HTML-Dokument im bestehenden Backend

21.10.2026. Vorbereitet, **kein ausgeführter Realpilot**. B1/#138 und B2/#139 sind
integriert; B3 basiert auf `d18afa4c8ec45daf02ec5cf51c2edbc3d27244f6`.
Der Betreiber meldet den erfolgreichen Image-Smoke und verifizierte Discovery-
Bundlehashes; die root-owned Mounts blockieren die bisherige Erstinitialisierung.
Der unten ergänzte B3-Bootstrap benötigt einen weiteren kontrollierten Codeupdate.
Keine SSHverbindung, Containeränderung, Bereitstellung oder echter Download
durch Codex. Loviscach und vorhandene Stores bleiben unverändert.

## Quelle und noch auszufüllende Freigabe

Genau eine vorhandene Notes-Resource aus dem versionierten
[CS50-Manifest](../../course_sources/cs50/manifest.json):

| Feld | Bestehender Wert |
| --- | --- |
| Course-ID | `cs50_python` |
| Dokument | HTML, Notes, Section `0` |
| Offizielle URL | `https://cs50.harvard.edu/python/notes/0/` |
| Resource-/Source-ID | `resource:f06e4055b5ef61f0a693c522f1c57880c88edc20c177cfb79fefbffee5b8767a` |
| Material-ID | `material:6b35632313fdf6057809e17cd6bae196630ffb6c4a799eefc7d3193ae452dc14` |

Die ID wird durch bestehende Discovery-/Materialmodelle berechnet, nicht aus einem
Dateinamen erfunden. Herkunft ist der Link „Lecture → Notes“ im vorhandenen
`cs50_python/week_0.html`, SHA256
`8526668d7cffb93fed9e32f66888dd8b77eed2d643b4527dba0df44a5c6f08e0`.
Zusätzlich wird ausschließlich `cs50_python/index.html` benötigt, SHA256
`228fd09a21987bc55147b7c9660c9f496dda49d234ebc1cb620e58fcb2963efe`.
Der Generator exportiert daraus einen gültigen vorhandenen `FixtureManifest` und
`MaterialResource` mit ursprünglichem DOMlocator/Source-Binding. Erst der spätere
`cs50_batch plan` bindet die endgültigen Containerpfade im bestehenden C26-`Batch`.
Es gibt keinen neuen Discovery-, Manifest- oder Parservertrag.

Die zwei alten Discovery-Snapshots sind **nicht** die zu bewertenden aktuellen
Notes-Rohbytes. Aktuelle Erreichbarkeit, HTTPheader und Größe wurden nicht geprüft.
Der Pilot begrenzt die tatsächliche Übertragung auf **1 MiB**, folgt keinen
Redirects und lädt keine eingebetteten Medien nach. Bei Überschreitung oder
abweichender URL/MIME stoppen; keine automatische Quellenumstellung.
Die begründete kleine Auswahl ist keine Zusage über die aktuelle Remotegröße.

Öffentlich referenziert bedeutet keine erteilte Nutzungsfreigabe. Die vorhandene
`license_status` bleibt zunächst `not_assessed`. Der Betreiber muss in der
erzeugten `approvals.json` tatsächliche Belege für Entscheidung, Zweck,
Lizenzprüfung, Robots-/Zugriffsprüfung, Aufbewahrung und Widerruf eintragen sowie
`download` und `process` bewusst bestätigen. Leere Referenzen und false-Flags
blockieren. Einen unabhängigen erwarteten Rawhash nur eintragen, wenn wirklich
bekannt; der Discovery-Snapshot-Hash ist dafür ungeeignet. Keine Goldannotation
oder fachliche Realabnahme wird hier erzeugt.

## Einmalige Voraussetzungen nach Merge

B2 korrigiert die Mountgrenze über `src.runtime_paths`. B3 ergänzt ausschließlich
die Erstinitialisierung unter root-owned Mount-Stämmen. Für den imagebasierten
Betrieb ist ein gesondert freizugebender Build/Redeploy **des bestehenden
Backenddienstes aus dem gemergten B3-Commit** nötig.
Kein zweiter Worker, kein alternatives Imageprofil und kein Codekopieren nach
`/app/src` als Workaround. Diese Bereitstellung ist hier nicht ausgeführt/freigegeben.
Standardstart `sleep infinity`, Restart-Policy und vorhandene Mounts bleiben erhalten.

Vom Betreiber bestätigt, vor Ort noch abzugleichen:

| Containerziel | Bestehender Host-Bind-Mount |
| --- | --- |
| `/app/data` | `/srv/personal-assistant/data` |
| `/app/logs` | `/srv/personal-assistant/logs` |
| `/app/.cache` | `/srv/personal-assistant/cache` |
| `/app/configuration` | `/srv/personal-assistant/configuration` |

Vor dem Update aktive Jobs kontrolliert stoppen; Coolify-Einstellungen erhalten,
gemergten Commit und neue Image-ID bestätigen. Mit den gefilterten Inspectbefehlen
aus dem [bestehenden Runbook](existing_backend_and_drive.md) Mountquellen,
Containerbenutzer, Limits und Restart-Policy prüfen. Keine Environment-/Secretdumps.
Betrieb als **UID/GID 1000:1000**, nur der ausdrücklich markierte einmalige
Bootstrap als root; keine pauschalen Rechteänderungen an bestehenden Mounts.

```sh
/app/.venv/bin/python -B -m scripts.worker_image_smoke
/app/.venv/bin/python -B -m scripts.cs50_pilot --help
```

Erforderliche Entscheidungen vor Rootanlage: tatsächlicher C16-Principal,
neuer direkter Pilotunterordner unter `/app/data`, neue private Policy-/Tokenpfade
unter `/app/configuration`, Zugriffskreis, Retention und Freigabebelege. Keine
vorausgefüllten echten Identitäten oder Tokens. Die zuletzt gemeldeten 8,6 GiB müssen
aktuell nachgemessen werden. Reserve 5 GiB **zuzüglich** Transfer-, Katalog-,
Job- und Reportallowance; maximal ein Material und ein laufender Processingjob.

## Discovery-Bundle bereitstellen

Auf dem lokalen geprüften aktuellen Checkout mit vorhandener Pythonumgebung ausführen.
`C26_BUNDLE` ist ein ausdrücklich gewähltes neues privates Verzeichnis außerhalb
des Repositories. Kein Download, keine Token- oder Originaldatendatei im Export:

```sh
set -eu
umask 077
: "${C26_PYTHON:?Vorhandene Projekt-Pythonumgebung benennen}"
: "${C26_BUNDLE:?Neuen lokalen Bundlepfad benennen}"
"$C26_PYTHON" -B -m scripts.cs50_pilot export \
  --snapshots "$PWD/docs/course_sources/cs50" --output "$C26_BUNDLE"
```

Das Bundle enthält exakt zwei vorhandene Discovery-HTMLdateien, `manifest.json`,
`binding.json`, den überprüften Helfercode und `files.json` mit exakten SHA256.
Es enthält keine heruntergeladene Notes-Seite. Bundle und aktualisiertes Image
müssen denselben Helfercode besitzen; Versionsabweichungen blockieren.

Der Betreiber überträgt dieses nicht geheime Bundle bewusst über seinen
freigegebenen Weg auf Hetzner. Keine automatische SSHübertragung durch Codex.
Dann **auf Hetzner**, nur für den bestätigten vorhandenen Backendcontainer:

```sh
set -eu
: "${C26_BACKEND_CONTAINER:?Bestaetigter vorhandener Backendcontainer fehlt}"
: "${C26_HOST_BUNDLE:?Bewusst uebertragener Bundleordner auf Hetzner fehlt}"
: "${C26_CONTAINER_BUNDLE:?Neues Bundleziel direkt unter /app/configuration fehlt}"
docker exec "$C26_BACKEND_CONTAINER" test ! -e "$C26_CONTAINER_BUNDLE"
docker cp "$C26_HOST_BUNDLE" "$C26_BACKEND_CONTAINER:$C26_CONTAINER_BUNDLE"
```

Kein Kopieren privater Verzeichnisse, kein Überschreiben bestehender Ziele.
Den ursprünglichen `files.json`-Digest über den vertrauenswürdigen Transferweg
vergleichen; Dateihashes allein authentifizieren keinen unbekannten Absender.

## Betriebsdateien im Container erzeugen

**C26-B3, root-owned Mounts:** `/app/data` und `/app/configuration` dürfen
`root:root`, 0755 bleiben. Der Administrator erstellt ausschließlich einen neuen
direkten Daten-Unterordner mit Präfix `cs50_pilot_` sowie die zwei ausdrücklich
benannten neuen Konfigurationsdateien. Er übergibt nur diese neuen Objekte an
UID/GID 1000:1000. Kein `chmod`, `chown` oder ACL-Update an bestehenden Roots,
keine rekursive Rechteänderung. `authorize-paths` ist weiterhin für vorhandene
schreibberechtigte Worker-Setups verfügbar; **nicht als root ausführen, um den
Workerzugriff zu simulieren**.

Nach Review/Merge muss der Betreiber zuerst den bestehenden Coolify-Backenddienst
mit dem aktualisierten Code neu bereitstellen: gleiches
`docker/DockerFile.worker`, Repositorywurzel als Buildkontext, vorhandene vier
Bind-Mounts, Standardstart `sleep infinity` und bisherige Restart-Policy erhalten.
Keine Dockerfile-/Dependency-/Composeänderung oder zweite Instanz erforderlich:
der vorhandene COPY-Eintrag enthält bereits `scripts/cs50_pilot.py`.
Image-Smoke und `scripts.cs50_pilot bootstrap --help` im aktualisierten Container
prüfen. Codex führt weder Redeploy noch folgende Hostbefehle aus.

Das bisherige Bundle `c26_pilot_bundle_01` und seine fünf geprüften SHA256 bleiben
unverändert erhalten. Der Helfercode hat sich geändert: mit obigem `export` aus
derselben B3-Revision ein **neues** Bundle erzeugen, über den genehmigten Weg an
einen neuen Konfigurationspfad übertragen und dessen Hashes erneut prüfen. Ein
altes Bundle gegen neuen Helfercode blockiert absichtlich. Keine alte Datei oder
`files.json` nachträglich anpassen.

Einmalig **auf dem Host**, im exklusiven Betreiberfenster ohne parallel laufenden
Pilot, nach separater Setupfreigabe. Die folgenden konkreten Zielnamen sind vor
Ausführung ausdrücklich zu genehmigen; existierende Ziele führen zum Abbruch.
`C26_SUBJECT` ist der tatsächlich freigegebene C16-Principal, keine Beispiel-ID:

```sh
set -eu
umask 077
: "${C26_BACKEND_CONTAINER:?Bestaetigter vorhandener Backendcontainer fehlt}"
: "${C26_SUBJECT:?Tatsaechlicher freigegebener Principal fehlt}"
: "${C26_CONTAINER_BUNDLE:?Neues geprueftes B3-Discovery-Bundle fehlt}"
C26_ROOT=/app/data/cs50_pilot_01
C26_POLICY=/app/configuration/c26_pilot_01.paths.json
C26_TOKEN=/app/configuration/c26_pilot_01.token

docker exec --user 0:0 --workdir /app "$C26_BACKEND_CONTAINER" \
  /app/.venv/bin/python -B -m scripts.cs50_pilot bootstrap \
  --root "$C26_ROOT" --policy "$C26_POLICY" --token-file "$C26_TOKEN" \
  --worker-uid 1000 --worker-gid 1000 --confirm-setup

docker exec --user 1000:1000 --workdir /app \
  --env PA_PERSISTENT_ROOTS_FILE="$C26_POLICY" "$C26_BACKEND_CONTAINER" \
  /app/.venv/bin/python -B -m scripts.cs50_pilot verify-bootstrap \
  --root "$C26_ROOT" --token-file "$C26_TOKEN"

docker exec --user 1000:1000 --workdir /app \
  --env PA_PERSISTENT_ROOTS_FILE="$C26_POLICY" "$C26_BACKEND_CONTAINER" \
  /app/.venv/bin/python -B -m scripts.cs50_pilot init --prepared \
  --bundle "$C26_CONTAINER_BUNDLE" --root "$C26_ROOT" \
  --subject "$C26_SUBJECT" --token-file "$C26_TOKEN" --confirm-setup
```

`bootstrap` meldet nur `awaiting_worker_verification`, niemals einen angeblich
startbereiten Job. Die private bestehende Policy-v1 bindet genau diesen Pilotbaum
(`material_artifacts`) und dessen `jobs` (`job_workspace`) an die beobachtete
Kernelmountidentität und **explizite Worker-UID**, nicht an die Admin-UID.
Root erhält 0700, Policy/Token 0600. Alle neuen Dateien werden exklusiv erzeugt,
synchronisiert und nur über ihre eigenen Deskriptoren übergeben. Das Token wird
lokal zufällig erzeugt und nie ausgegeben. Es bleibt ausschließlich unter
`C26_TOKEN`; der neue Ablauf legt keine Tokenkopie unter `/app/data` an.

`bootstrap.json` im neuen Root bindet UID/GID, Root-Inode/Gerät, Policy-/Tokenhash
und die vier Mountidentitäten. Das ist ein Integritätsbeleg, keine Signatur gegen
denselben Worker oder einen privilegierten Angreifer. `verify-bootstrap` prüft
unter der **wirklichen** UID/GID 1000 den unveränderten Beleg, private Ownership,
Mounts, tatsächlichen Schreib-/Traversalzugriff und beide unveränderten C16- und
Material-Pfadprüfungen. Schreibrecht auf den Mount-Stämmen ist dafür unnötig.
Ein UID-/GID-Wechsel, nicht lesbare Mountinformation oder veränderter Mount blockiert.

`init --prepared` akzeptiert ausschließlich den belegten Root mit genau dieser
einen Belegdatei. Ein exklusiv erstellter `.init-claimed`-Ordner verhindert
konkurrierende oder wiederholte Initialisierung und bleibt als Beleg erhalten.
Normales `init` lehnt bestehende Roots weiterhin ab. Bereits vorhandene Ziele,
Teilbootstrap und unterbrochenes `init` werden weder übernommen, überschrieben
noch bereinigt: Belege erhalten und Betreiberentscheidung verlangen. Auch eine
zweite identische Bootstrap-Ausführung ist ein Konflikt. `verify-bootstrap`
ist vor `init` wiederholbar und schreibt nichts; nach `init` die bestehenden
phasenbezogenen Preflights verwenden. Die vier Mount-Stämme, Loviscach-Daten und
andere Stores bleiben unberührt. Keine atomare Mehrdatei-Transaktion behauptet.

Alle folgenden Containerbefehle als **UID/GID 1000:1000** ausführen. Dazu etwa:

```sh
docker exec --user 1000:1000 --workdir /app \
  --env PA_PERSISTENT_ROOTS_FILE="$C26_POLICY" -it "$C26_BACKEND_CONTAINER" /bin/sh
```

In jeder solchen Shell `C26_ROOT`, `C26_TOKEN`, `C26_POLICY` auf dieselben expliziten
Pfade setzen und `PA_PERSISTENT_ROOTS_FILE` beibehalten. Das sind Pfade, keine
Tokenwerte. Bei abweichenden Zielnamen alle Shells bewusst identisch konfigurieren.

Erzeugter Bestand:

| Datei/Root relativ zu `C26_ROOT` | Vorhandener Vertrag / Erzeugung |
| --- | --- |
| `inputs/manifest.json`, zwei HTMLdateien | Unveränderte Discovery-Snapshots und FixtureManifest |
| `inputs/binding.json` | MaterialResource mit ursprünglicher Provenienz |
| `limits.json` | CapacityLimits, 1 Material, 5-GiB-Reserve, 512-MiB-Jobbudget |
| `identity.json` | Identity, Operator und nur `cs50_python`; Tokenhash, kein Klartexttoken |
| `bootstrap.json`, `.init-claimed` | Hash-/Mount-/UID-/GID-Handoff und exklusiver Initialisierungsbeleg; keine Jobdatenbank |
| `approvals.json` | SourceApproval-Formular, absichtlich noch ungültig/unbestätigt |
| `archive`, `reports`, `jobs` | Neue 0700-Verzeichnisse, noch keine SQLiteinitialisierung |
| `batch.json` | Später durch vorhandenes `cs50_batch plan` |
| `catalog/catalog.json` und Bundle | Später genau einmal durch vorhandenes `seal` |
| `controller.json` | Erst nach geprüftem Katalog durch `configure` |

Jetzt die tatsächlichen Quellenentscheidungen in `approvals.json` eintragen,
0600 und Worker-Ownership beibehalten. Keine Beispielbegründungen als echte
Freigabebelege übernehmen. Rechtevergabe an Source/Course und die Pfadfreigabe
sind getrennte Voraussetzungen.

## Ein Batch, Preview, Download und Katalog

Alle Pflichtwerte müssen vor dem ersten Preflight ausgefüllt sein. Die Prüfung
liest nur diesen eigenen Pilotroot, Konfiguration und Kernelmountinformationen.
Sie berührt weder Loviscach noch globale Job-/ContentStores. Ein Blocker beendet
die CLI mit Exit 2 und festem Fehlercode, ohne Token, Quelltext oder private Pfade.

```sh
set -eu
: "${C26_ROOT:?Freigegebener Pilotroot fehlt}"
: "${PA_PERSISTENT_ROOTS_FILE:?Private Pfadpolicy fehlt}"
C26_SOURCE='resource:f06e4055b5ef61f0a693c522f1c57880c88edc20c177cfb79fefbffee5b8767a'

/app/.venv/bin/python -B -m scripts.cs50_pilot preflight --root "$C26_ROOT" --phase plan
/app/.venv/bin/python -B -m scripts.cs50_batch plan \
  --manifest "$C26_ROOT/inputs/manifest.json" --course cs50_python \
  --resource "$C26_SOURCE" --limits "$C26_ROOT/limits.json" --output "$C26_ROOT/batch.json"
/app/.venv/bin/python -B -m scripts.cs50_batch download \
  --batch "$C26_ROOT/batch.json" --archive "$C26_ROOT/archive" \
  --approvals "$C26_ROOT/approvals.json" --limits "$C26_ROOT/limits.json" \
  --output "$C26_ROOT/reports/download-preview.json"
```

Ohne `--confirm` erfolgt **kein HTTP**. Auswahl, URL, maximal 1048576 Rawbytes,
Belege und Budget kontrollieren. Erst nach tatsächlicher Downloadfreigabe:

```sh
/app/.venv/bin/python -B -m scripts.cs50_pilot preflight --root "$C26_ROOT" --phase download
/app/.venv/bin/python -B -m scripts.cs50_batch download \
  --batch "$C26_ROOT/batch.json" --archive "$C26_ROOT/archive" \
  --approvals "$C26_ROOT/approvals.json" --limits "$C26_ROOT/limits.json" \
  --confirm --output "$C26_ROOT/reports/download.json"
/app/.venv/bin/python -B -m scripts.cs50_pilot preflight --root "$C26_ROOT" --phase download
```

Die letzte schreibfreie Prüfung meldet `archive.status=verified`, Bytezahl,
Raw-SHA256, exakten Receipt-SHA256 und `origin=http_download`. Diese Werte mit
`download.json` vergleichen. Kein Qualitätsurteil aus dem Hash ableiten.
Fehler/429/Redirect/Größenkonflikte zuerst untersuchen; kein automatischer Retry.
Danach dieselbe Quelle einmal versiegeln und die gebundene Konfiguration erzeugen:

```sh
/app/.venv/bin/python -B -m scripts.cs50_batch seal \
  --batch "$C26_ROOT/batch.json" --archive "$C26_ROOT/archive" \
  --approvals "$C26_ROOT/approvals.json" --limits "$C26_ROOT/limits.json" \
  --confirm --output "$C26_ROOT/catalog"
/app/.venv/bin/python -B -m scripts.cs50_pilot configure --root "$C26_ROOT" --confirm-setup
/app/.venv/bin/python -B -m scripts.cs50_pilot preflight --root "$C26_ROOT" --phase process
```

Der Katalog muss genau einen Eintrag enthalten. Originaler HTTP-Receipt und Raw
werden hashidentisch in dessen Bundle übernommen. `configure` verwendet genau
diesen Katalog, den bestätigten Principal und dessen Tokenhash; es überschreibt
keine bestehende Konfiguration und adoptiert keine vorhandene Jobdatenbank.
C16/C18 behalten Schema, Authentifizierung, Gate und Idempotenz.

## Einen Processingjob starten und prüfen

**Terminal A**, im vorhandenen Container unter `/app`, mit derselben Policy und demselben UID:

```sh
: "${C26_ROOT:?Pilotroot fehlt}"
: "${PA_PERSISTENT_ROOTS_FILE:?Pfadpolicy fehlt}"
/app/.venv/bin/python -B -m scripts.cs50_worker \
  --config "$C26_ROOT/controller.json" --limits "$C26_ROOT/limits.json"
```

Im Vordergrund laufen lassen. **Terminal B**, erneut dieselben beiden Variablen
setzen. Keine zweite Backendinstanz, kein zweiter Executor:

```sh
/app/.venv/bin/python -B -m scripts.deployment health \
  --config "$C26_ROOT/controller.json" --role worker
/app/.venv/bin/python -B -m scripts.cs50_batch workflow execute \
  --config "$C26_ROOT/controller.json" --token-file "$C26_TOKEN" \
  --catalog "$C26_ROOT/catalog/catalog.json" \
  --source-ref "$(/app/.venv/bin/python -B -c 'import json,sys; print(next(iter(json.load(open(sys.argv[1]))["catalog"])))' "$C26_ROOT/catalog/catalog.json")" \
  --limits "$C26_ROOT/limits.json" --confirm
/app/.venv/bin/python -B -m scripts.cs50_batch workflow report \
  --config "$C26_ROOT/controller.json" --token-file "$C26_TOKEN" \
  --catalog "$C26_ROOT/catalog/catalog.json" --limits "$C26_ROOT/limits.json"
```

`execute` ist asynchron; `report` ohne `--output` bis zum terminalen Zustand
wiederholen, keine weiteren Execute-Aufrufe als Polling. Erst bei `completed`
denselben Report mit neuem `--output "$C26_ROOT/reports/result.json"` speichern.
Genau ein C16-Job und fünf C18-Stufen: Plan, lokaler Import, HTML-v2, Quality Gate,
Handoff. Technische Blocker offenlassen; kein C23-Publish, Index, Video, Whisper
oder LLMschritt. Worker- und Parserlimits ersetzen keine aktuell bestätigten
Containerressourcenlimits; vorhandene Einstellungen vor Ausführung abgleichen.

Reportdateihashes überprüfen, ohne Originaltext auszugeben:

```sh
/app/.venv/bin/python -B - "$C26_ROOT" <<'C26_OUTPUT_PY'
import json, sys
from pathlib import Path
from src.job_control.catalog import read_file, safe_path
from src.tools_materials.batch import sha
root = Path(sys.argv[1])
report = json.loads(read_file(root / 'reports/result.json'))
assert len(report['workflows']) == 1
workflow = report['workflows'][0]
assert workflow['job']['status'] == workflow['report']['status'] == 'completed'
assert len(workflow['report']['stages']) == 5
for ref in workflow['report']['output_refs']:
    data = read_file(safe_path(root / 'jobs', ref['path']))
    assert len(data) == ref['size_bytes'] and sha(data) == ref['sha256']
print('completed_and_output_hashes_verified')
C26_OUTPUT_PY
```

## Kontrollierter Wiederanlauf und Grenzen des Preflight

Worker im eigenen Vordergrundterminal mit Ctrl-C kontrolliert beenden und Ende
abwarten; keine gespeicherte PID zum Killen verwenden. Für einen tatsächlich
unterbrochenen Job hält C16/C18 Zustand und bereits committete Artefakte auf dem
bestätigten Datenmount. Erst denselben Worker mit derselben Konfiguration/Policy
neu starten und Restart-Reconciliation sowie Report lesen. Danach ausdrücklich
`workflow resume` statt `workflow execute`, mit demselben einen `--source-ref`
und `--confirm`. Bereits abgeschlossene Workflows erzeugen keinen zweiten Job.
Fehlgeschlagene/unterbrochene Versuche bleiben erhalten; maximal drei historische
Jobs im isolierten Pilot, weiterhin ein laufender Job. Kein automatischer Retry.

Ein Containerrestart ist ein eigenes Wartungsereignis und wurde nicht getestet.
`sleep infinity` startet einen Execworker nicht erneut. Die Policyvariable muss
auch nach einer neuen Shell/Containerbereitstellung explizit gesetzt werden.
Geänderte Mountidentitäten oder Quarantäne sperren; keine Fences/Lockdateien
löschen, keine WALdateien abschneiden, keine Roots neu initialisieren.

Das Preflight verlangt einen **gestoppten** Worker. Es prüft vorhandene Locks
nonblocking und ausschließlich lesend, erstellt keine fehlenden Lockdateien und
öffnet keine Storeklasse. Bei vorhandenem DBbestand nur schema-v1, ohne nichtleeres
WAL/Journal, unter vorhandenen Operations-/Worker-/Bootstraplocks eine immutable
Read-only-Sicht. Laufende/queued Jobs, unbekannte Schemas und fremde Jobs blockieren.
Status eines laufenden Piloten daher über das bestehende `workflow report`, nicht
durch wiederholte schreibende Initialisierung prüfen.

Die Prüfung ist eine Momentaufnahme, keine Reservierung oder globale Capability.
Die vorhandenen Writer prüfen Rechte, Hashes, Mountpolicy und Budgets erneut.
Root-/Same-UID-Manipulation oder paralleles administratives Remounten ist keine
hier gelöste Isolation; Setup/Policyänderungen benötigen ein kontrolliertes
Betreiberfenster. Policydatei nicht in einen autorisierten Schreibroot verschieben.
Nur ext4/xfs/btrfs-Bind-Mounts; tmpfs, Overlay, fehlende/unklare Mountinformationen,
Symlinks, Traversal und verschachtelte Mounts bleiben gesperrt. Andere Dateisysteme
benötigen separate Prüfung. Keine Loviscach- oder globale Storeinventur.
Der Mountelternordner muss root- oder Worker-owned sein und darf nicht für Gruppe
oder andere schreibbar sein; alle vorhandenen Komponenten im freigegebenen
Schreibbaum benötigen private Worker-Ownership. Abweichende Rechte bleiben ein
Blocker, kein Anlass für automatische chmod-/chown-Änderungen.

Die tatsächlichen lokalen Tests und verbleibenden Host-/Freigabeblockaden stehen
im [B2-Prüfvermerk](validation.md#c26-b2--html-pilotvorbereitung) und im
[B3-Prüfvermerk](validation.md#c26-b3--administrative-erstinitialisierung-und-workerübergabe).
