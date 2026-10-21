# C26-B2 – Ein HTML-Dokument im bestehenden Backend

21.10.2026. Vorbereitet, **kein ausgeführter Realpilot**. B1/#138 ist auf
`7420df62765aab127f5abeb3e39d355678844148` integriert; der Betreiber meldet den
erfolgreichen Vier-Modul-Smoke im aktualisierten Hetznercontainer. Die folgenden
B2-Funktionen benötigen zusätzlich den hier vorbereiteten Codeupdate.
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

Der derzeitige B1-Container lehnt Ausgaben unter `/app/data` als Repositoryinhalt
ab. B2 korrigiert ausschließlich diese Mountgrenze über `src.runtime_paths`.
Für den imagebasierten Betrieb ist deshalb ein gesondert freizugebender Build/
Redeploy **des bestehenden Backenddienstes aus dem gemergten B2-Commit** nötig.
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
Alle folgenden Befehle im vorhandenen Backend mit **dem vorgesehenen Worker-UID**
ausführen; keine pauschalen chmod-/chown-Reparaturen an bestehenden Mounts.

```sh
/app/.venv/bin/python -B -m scripts.worker_image_smoke
/app/.venv/bin/python -B -m scripts.cs50_pilot --help
```

Erforderliche Entscheidungen vor Rootanlage: tatsächlicher C16-Principal,
neuer direkter Pilotunterordner unter `/app/data`, neue private Policy-/Tokenpfade
unter `/app/configuration`, Zugriffskreis, Retention und Freigabebelege. Keine
vorausgefüllten echten Identitäten oder Tokens. Die gemeldeten 14 GiB müssen
aktuell nachgemessen werden. Reserve 5 GiB **zuzüglich** Transfer-, Katalog-,
Job- und Reportallowance; maximal ein Material und ein laufender Processingjob.

## Discovery-Bundle bereitstellen

Auf dem lokalen geprüften B2-Checkout mit vorhandener Pythonumgebung ausführen.
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

Ab jetzt Shell **im aktualisierten Container**, gleiche explizite Variablen in
jeder verwendeten Shell setzen. `C26_ROOT` muss neu sein und direkt unter
`/app/data` liegen. `C26_POLICY` und `C26_TOKEN` sind neue Dateien direkt unter
`/app/configuration`; `C26_SUBJECT` ist der tatsächlich freigegebene Principal.
Die folgenden Schritte sind Betreiberaktionen nach separater Setupfreigabe:

```sh
set -eu
umask 077
: "${C26_ROOT:?Neuer freigegebener Pilotroot fehlt}"
: "${C26_POLICY:?Neue private Policydatei fehlt}"
: "${C26_TOKEN:?Neue private Tokendatei fehlt}"
: "${C26_SUBJECT:?Tatsaechlicher freigegebener Principal fehlt}"
: "${C26_CONTAINER_BUNDLE:?Geprueftes Discovery-Bundle fehlt}"
cd /app

/app/.venv/bin/python -B -m scripts.cs50_pilot authorize-paths \
  --root "$C26_ROOT" --output "$C26_POLICY" --confirm-setup
export PA_PERSISTENT_ROOTS_FILE="$C26_POLICY"

/app/.venv/bin/python -B - "$C26_TOKEN" <<'C26_TOKEN_PY'
import os, secrets, sys
from pathlib import Path
from src.job_control.catalog import safe_path
p = safe_path(Path(sys.argv[1]))
assert p.parent == Path('/app/configuration')
fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
with os.fdopen(fd, 'w') as stream:
    stream.write(secrets.token_urlsafe(32) + '\n')
    stream.flush()
    os.fsync(stream.fileno())
C26_TOKEN_PY

/app/.venv/bin/python -B -m scripts.cs50_pilot init \
  --bundle "$C26_CONTAINER_BUNDLE" --root "$C26_ROOT" \
  --subject "$C26_SUBJECT" --token-file "$C26_TOKEN" --confirm-setup
```

`authorize-paths` zeichnet die Kernelidentität von `/app/data` auf: Major/Minor,
Dateisystemwurzel, Mountpoint, Dateisystem, Quelle und Schreibstatus. Die private
0600-Policy ist die ausdrückliche Betreiberautorisierung für genau den neuen
Pilotbaum (`material_artifacts`) und dessen `jobs` (`job_workspace`), nicht für
den gesamten Mount. Policy außerhalb beider Schreibroots. Verzeichnisnamen allein
erteilen kein Recht. Kein gemeinsamer Token mit Produktionssystemen nötig.

`init` legt ausschließlich neue private Pilotdateien an; ein bestehender Root
oder fehlgeschlagenes Teilsetup wird nicht übernommen oder bereinigt:

| Datei/Root relativ zu `C26_ROOT` | Vorhandener Vertrag / Erzeugung |
| --- | --- |
| `inputs/manifest.json`, zwei HTMLdateien | Unveränderte Discovery-Snapshots und FixtureManifest |
| `inputs/binding.json` | MaterialResource mit ursprünglicher Provenienz |
| `limits.json` | CapacityLimits, 1 Material, 5-GiB-Reserve, 512-MiB-Jobbudget |
| `identity.json`, `operator.token` | Identity, Operator und nur `cs50_python`; privates Token, nie ausgeben |
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
  --config "$C26_ROOT/controller.json" --token-file "$C26_ROOT/operator.token" \
  --catalog "$C26_ROOT/catalog/catalog.json" \
  --source-ref "$(/app/.venv/bin/python -B -c 'import json,sys; print(next(iter(json.load(open(sys.argv[1]))["catalog"])))' "$C26_ROOT/catalog/catalog.json")" \
  --limits "$C26_ROOT/limits.json" --confirm
/app/.venv/bin/python -B -m scripts.cs50_batch workflow report \
  --config "$C26_ROOT/controller.json" --token-file "$C26_ROOT/operator.token" \
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
im [B2-Prüfvermerk](validation.md#c26-b2--html-pilotvorbereitung).
