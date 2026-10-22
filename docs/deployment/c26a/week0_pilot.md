# C26-B4 – Kontrollierter CS50P-Week-0-Batch

Aktueller Folgeauftrag: [C26-B5 – Wocheninventur und kontrollierte Planung](complete_week_materials.md).
Für B5 bleiben Codeindex, Python-Dateien und ZIPs ausdrücklich `manual_only`;
die unten dokumentierte historische B4-Auswahl ist keine B5-Downloadfreigabe.

21.10.2026. Basis master `23ebca634ad4a2ecf485d31654d4645b32cfa16b`
(B3/#140 integriert). **Vorbereitet, kein durch Codex ausgeführter Realbatch.**
Die Betreiberangabe zum erfolgreichen B3-Notes-Pilot bleibt ein separater Befund:
71.718 Rawbytes, 237 Blöcke einschließlich 34 Codeblöcken, Gate passed mit
47 informativen Findings, 171 Aggregationseinheiten und 66 Ausschlüssen;
alle 34 Codeblöcke erhalten. Originale, Jobdatenbank und Artefakte dieses Piloten
wurden hier weder geöffnet noch verändert. Keine fachliche oder Knowledgefreigabe.

## Tatsächlicher Week-0-Bestand

Quelle ist ausschließlich das versionierte
[Discoverymanifest](../../course_sources/cs50/manifest.json), ausgewertet mit
`make_plan` und `parser_for`. IDs, URLs und Rollen werden daraus übernommen;
keine Links aus aktuellen Webseiten nachgeladen. Die minimale Exportclosure
enthält wie B2/B3 nur `cs50_python/index.html` und `week_0.html`, gebunden an die
unveränderten dort dokumentierten SHA256. Diese Discoverydateien sind keine
fertigen, freigegebenen HTTP-/Parsed-Bundles für den Batch.

| Material / originale URL | Source-ID | Tatsächlicher Bestand und Behandlung |
| --- | --- | --- |
| Notes: `https://cs50.harvard.edu/python/notes/0/` | `resource:f06e4055b5ef61f0a693c522f1c57880c88edc20c177cfb79fefbffee5b8767a` | Referenz im Repository; erfolgreicher privater B3-Download nur vom Betreiber berichtet. Im **neuen** Batch separat freizugeben und zu beziehen; keine Übernahme aus Pilot 01. |
| Codeindex: `https://cdn.cs50.net/python/2022/x/lectures/0/src0/` | `resource:5f51d97877d3ddbc6699e5c9b484c47b601ce15d1373cfdef065d8fad47b5944` | Zusätzlich versionierter Raw-Snapshot `cs50_python/cdn.html`; dessen Existenz ersetzt weder Downloadfreigabe noch HTTPreceipt. HTML-v2 auf der Indexseite; keine rekursiven Code-Downloads. |
| Problem Set: `https://cs50.harvard.edu/python/psets/0/` | `resource:1200b44f5efad4c2796fe526c66701859159dc235f6c7d947edf25a9935bdf05` | Referenz; die Übersicht ist HTML. Keine automatische Übernahme aller verlinkten Aufgaben. |
| PDFslides: `https://cdn.cs50.net/python/2022/x/lectures/0/lecture0.pdf` | `resource:2b18399f3ce8d176b421afd8f3d4b7352851e4e1dcb990821658f9aebd67a80f` | Nur Referenz, keine PDF-Rohdatei in diesem Bestand. Vorhandenes PDF-v2 unterstützt; Größe und Parserausdehnung ungeprüft. |
| Code-PDF: `https://cdn.cs50.net/python/2022/x/lectures/0/src0.pdf` | `resource:959434ab111dd5b875159fa7508d37955d604cdd6c3acc82f7d3133ea34b3a16` | Nur Referenz; gleicher PDF-/Größen-/Freigabevorbehalt. Kein eigenständiger ausführbarer Codebestand. |

Erster begrenzter Realbatch: die **drei HTML-Quellen**. Optionaler zusätzlicher
Umfang: die beiden PDFs, ausschließlich nach Einzelentscheidung und innerhalb
derselben 1-MiB-Dateigrenze. Der Export nimmt nur explizite IDs, höchstens acht,
aus `cs50_python`, Section `0`, mit vorhandenem unterstütztem Parser an.

Die vorhandene Discovery identifiziert außerdem folgende **nicht übernommene**
Week-0-Referenzen:

- Wochen-/Lecture-Seite `https://cs50.harvard.edu/python/weeks/0/`, Rolle
  `lecture_video`; vorhandener Discovery-Snapshot, kein freigegebener Mediendownload.
- MP3 `https://cdn.cs50.net/python/2022/x/lectures/0/lecture0.mp3` sowie die
  CS50-/YouTube-/MP4-Varianten: getrennte Medienpipeline, hier ausgeschlossen.
- Google-Slides-Link aus dem Snapshot: Format unknown, kein bestätigter Export.
- ZIP `https://cdn.cs50.net/python/2022/x/lectures/0/src0.zip`: kein Archivimport.
- SRT/TXT unter `https://cdn.cs50.net/python/2022/x/lectures/0/lang/en/`:
  `lecture0.srt` und `lecture0.txt`; bestehende getrennte Transcriptverträge,
  kein C18-Materialparser für diese Rollen.
- Fünf Shorts unter `https://cs50.harvard.edu/python/shorts/`:
  `visual_studio_code_for_cs50/`, `functions/`, `variables/`, `return_values/`,
  `side_effects/`. Trotz HTML-URL Rolle short und damit absichtlich keine
  Umklassifikation als HTML-Dokument.
- Der versionierte Snapshot `cs50_python/practice_1.html` betrifft
  `/python/psets/0/indoor/`. Die bestehende Discovery liefert daraus keinen
  eigenständigen gebundenen Materialeintrag für diese Auswahl. Weitere Aufgaben
  und einzelne Dateien hinter dem Codeindex sind nicht vollständig inventarisiert.

Damit ist eine **vollständige fachliche Wochenabdeckung nicht nachgewiesen**.
Es gibt fünf unterstützte gebundene Materialien, davon drei HTML. Keine erfundenen
Source-IDs für fehlende Aufgaben, keine rekursive Linkauflösung oder neue Pipeline.
Aktuelle Erreichbarkeit, MIME, Rawhashes und Inhaltsqualität bleiben ungeprüft.

## Konfiguration und Quellenfreigaben

Es bleiben dieselben C26-Verträge: `Batch`, `CapacityLimits`, `SourceApproval`,
C16 `Identity`/`Settings`/`CatalogEntry`, C18 pro Material genau ein Workflow.
`binding.json` kann im neuen expliziten Auswahlmodus eine Liste bestehender
`MaterialResource`-Objekte enthalten (höchstens acht, Bindingdatei höchstens
64 KiB); der alte Einzelobjektmodus bleibt lesbar.
Die Exportdateihashes binden Auswahl und Helferrevision. Es gibt keinen neuen
Manifesttyp, Scheduler, Import, Knowledge-/ContentStore- oder Indexschritt.

Für **jede gewählte Tabellenzeile** muss der Betreiber in der erzeugten
`approvals.json` tatsächlich ausfüllen und bestätigen:

- Source-ID, Material-ID, Course `cs50_python` und unveränderte originale URL;
- `approval_reference`, Zweck/Nutzung (`usage_reference`), Lizenz-/Zugriffsprüfung
  (`license_review_reference`, `robots_review_reference`);
- Aufbewahrung (`retention_reference`) und Widerruf (`revocation_reference`);
- `download=true` und `process=true`, gegebenenfalls unabhängig bekannter Raw-SHA.

Alle Referenzen beginnen leer, beide Freigaben false. Der frühere Notes-Pilot
erteilt hier keine automatische Freigabe. Fehlende Freigabe bedeutet kein HTTP
für diese Quelle; der Pilot-Preflight verlangt alle ausgewählten Freigaben.
Die unverbindliche Downloader-Vorschau bleibt ohne HTTP und zeigt zusätzlich
`download_approved`; `selected` allein ist kein Ausführungsrecht.

## Ressourcen und Kapazität

| Grenze | B4-Vertrag |
| --- | --- |
| Auswahl | explizit 1–8 unterstützte Materialien aus Week 0 |
| Rohbytes | höchstens 1 MiB **je** Material, höchstens 8 MiB pro Batch |
| Freie Reserve | unverändert 5 GiB, zusätzlich ausgewiesene Allowances |
| Archiv / Katalog | 64 MiB / 128 MiB |
| Gesamter Jobroot / Reports | 512 MiB / 16 MiB, einschließlich Historie |
| Downloads | seriell, mindestens 2 s zwischen neuen Transfers im Template, keine automatischen Retries |
| Processing | ein Worker, `max_parallel=1`, `max_queued=1`; **ein** Source-Ref je expliziter Submission |
| Historie | `max_jobs=3*N`, höchstens 24; keine automatische Löschung |
| Workflow | bestehende 90 s Wandzeit, 60 s CPU; Parser- und Guardianlimits unverändert |

Tatsächlich mit dem vorhandenen `estimate` und dem minimalen Discoveryexport
berechnet: 116.853 Discoverybytes. Drei HTMLs: Rawobergrenze 3.145.728 Bytes,
Archivallowance 6.291.456, Katalogallowance 6.642.015 und insgesamt
**5.935.290.719 Bytes** erforderlicher freier Speicher vor neuem Batch.
Fünf Materialien: Rawobergrenze 5.242.880, Archiv 10.485.760, Katalog 11.070.025,
insgesamt **5.943.913.033 Bytes**. Beide Zahlen enthalten Reserve, Job- und
Reportbudget; sie sind Planungsallowances, kein gemessener Downloadbedarf.
Parserausdehnung und reale Quelldateigrößen bleiben ausdrücklich unbekannt.
Die zuletzt gemeldeten 8,6 GiB müssen vor Ort neu bestätigt werden. Kein Schluss,
dass PDFs, Videos oder ein vollständiger Kurs auf den Datenträger passen.

## Neuen Batch vorbereiten

Nach Review/Merge benötigt der vorhandene Backenddienst einen gesondert
freigegebenen Imageupdate aus derselben Revision wie das neue Bundle. Dockerfile,
Dependencygruppe, vier Bind-Mounts, Standardstart und Restart-Policy bleiben
unverändert. Kein zweiter Container. **Den Root `cs50_pilot_01`, seine Datenbank,
Konfiguration und Artefakte nicht verwenden oder ändern.**

Lokal auf dem geprüften Checkout mit vorhandener Pythonumgebung, neuer expliziter
Bundlepfad außerhalb des Repositories. Keine Netzwerkaktivität:

```sh
set -eu
: "${C26_PYTHON:?Vorhandene Pythonumgebung benennen}"
: "${C26_WEEK0_BUNDLE:?Neuen lokalen Bundlepfad benennen}"
"$C26_PYTHON" -B -m scripts.cs50_pilot export \
  --snapshots "$PWD/docs/course_sources/cs50" --output "$C26_WEEK0_BUNDLE" \
  --resource resource:f06e4055b5ef61f0a693c522f1c57880c88edc20c177cfb79fefbffee5b8767a \
  --resource resource:5f51d97877d3ddbc6699e5c9b484c47b601ce15d1373cfdef065d8fad47b5944 \
  --resource resource:1200b44f5efad4c2796fe526c66701859159dc235f6c7d947edf25a9935bdf05
```

PDFs nur bei ausdrücklich erweitertem Scope mit den beiden Source-IDs aus der
Tabelle als zusätzliche `--resource`-Argumente exportieren. Kein pauschaler
Kursselektor. Für das erste HTML-Trio ist die JSONliste drei Einträge lang.
Helfer und `files.json` niemals aus einem älteren B2-/B3-Worktree zusammenkopieren;
Hashabweichung ist ein Blocker. Das bestehende B3-Bundle unverändert aufbewahren.

Transfer, neue private Ziele und echte Principalbindung nach dem
[B3-Bootstrapablauf](html_pilot.md#betriebsdateien-im-container-erzeugen).
Konkrete **neu zu genehmigende** Zielvorschläge:

```sh
C26_ROOT=/app/data/cs50_pilot_week0_01
C26_POLICY=/app/configuration/c26_week0_01.paths.json
C26_TOKEN=/app/configuration/c26_week0_01.token
```

Neues Bundle ebenfalls an einen neuen, bestätigten Konfigurationspfad übertragen.
Wie im erfolgreichen B3-Setup muss es für UID 1000 lesbar sein. `docker cp`
ohne Archivoption erzeugt im Container normalerweise Root-Ownership; die
privaten 0700/0600-Modi aus dem Export erteilen UID 1000 dann noch keinen Zugriff.
Für **ausschließlich den gerade neu übertragenen** Metadatenordner, nach Prüfung
seines vertrauenswürdig übertragenen `files.json`-Digests, folgende begrenzte
Betreiberübergabe im exklusiven Setupfenster. Der neue Zielname muss mit
`c26_week0_bundle_` beginnen; kein bestehendes B3-Bundle verwenden:

```sh
docker exec --user 0:0 --workdir /app -i "$C26_BACKEND_CONTAINER" \
  /app/.venv/bin/python -B - "$C26_CONTAINER_BUNDLE" <<'C26_BUNDLE_HANDOFF_PY'
import os, stat, sys
from pathlib import Path
from scripts import cs50_pilot as pilot
from src.job_control.catalog import safe_path
def require(condition):
    if not condition:
        raise SystemExit('new_metadata_bundle_handoff_blocked')
p = safe_path(Path(sys.argv[1]))
require(p.parent == Path('/app/configuration'))
require(p.name.startswith('c26_week0_bundle_'))
files = ['manifest.json', 'binding.json', 'cs50_pilot.py', 'files.json']
require({x.name for x in p.iterdir()} == set(files) | {'cs50_python'})
require({x.name for x in (p / 'cs50_python').iterdir()} == {'index.html', 'week_0.html'})
pilot.bundle(p)  # Existing hashes, helper revision and exact selected bindings.
paths = [p / n for n in files + ['cs50_python/index.html', 'cs50_python/week_0.html']]
paths += [p / 'cs50_python', p]  # Handoff root last; no recursive chmod/chown.
for path in paths:
    safe_path(path)
    info = path.stat()
    require(info.st_uid == 0)
    require(path.is_dir() or (stat.S_ISREG(info.st_mode) and info.st_nlink == 1))
    require(stat.S_IMODE(info.st_mode) == (0o700 if path.is_dir() else 0o600))
for path in paths:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        os.fchown(fd, 1000, 1000)
    finally:
        os.close(fd)
print('new_metadata_bundle_handed_to_worker')
C26_BUNDLE_HANDOFF_PY
docker exec --user 1000:1000 --workdir /app "$C26_BACKEND_CONTAINER" \
  /app/.venv/bin/python -B -c \
  'import sys; from pathlib import Path; from scripts.cs50_pilot import bundle; bundle(Path(sys.argv[1])); print("bundle_readable_and_verified")' \
  "$C26_CONTAINER_BUNDLE"
```

Bei bereits korrekter Worker-Ownership nur den letzten Lesetest verwenden.
Ein teilweiser Übergabefehler verlangt eine Betreiberentscheidung, keine
Wiederübernahme unbekannter Dateien. Keine Stammrechte, Inhalte oder alten
Konfigurationen ändern; die Befehle wurden hier nur syntaktisch geprüft.
Wie B3 genau einmal `bootstrap --worker-uid 1000 --worker-gid 1000` als root,
danach `verify-bootstrap` und `init --prepared` als 1000:1000. Die drei oder fünf
SourceApproval-Zeilen vervollständigen. Alle folgenden Befehle in diesem neuen
Root als **1000:1000**, `/app`, mit exportierter Policy. Keine produktiven
C16-/C18-/C23-Stores initialisieren oder adoptieren.

## Plan, Preview, Download, Katalog

Der Preflight benötigt weiterhin einen gestoppten Worker. Vor Beginn muss der
Betreiber bestätigen, dass kein früherer Executor auf diesem Host parallel läuft.
Das neue Root-Lock schützt nur diesen Root; es ist keine globale Workerinventur.
Hier wird kein alter Worker automatisch beendet oder dessen Datenbank geöffnet.

```sh
set -eu
: "${C26_ROOT:?Neuer Week-0-Root fehlt}"
: "${C26_TOKEN:?Neues privates Konfigurationstoken fehlt}"
: "${PA_PERSISTENT_ROOTS_FILE:?Neue Pfadpolicy fehlt}"
/app/.venv/bin/python -B -m scripts.cs50_pilot preflight --root "$C26_ROOT" --phase plan
/app/.venv/bin/python -B -m scripts.cs50_batch plan \
  --manifest "$C26_ROOT/inputs/manifest.json" --course cs50_python \
  --resource resource:f06e4055b5ef61f0a693c522f1c57880c88edc20c177cfb79fefbffee5b8767a \
  --resource resource:5f51d97877d3ddbc6699e5c9b484c47b601ce15d1373cfdef065d8fad47b5944 \
  --resource resource:1200b44f5efad4c2796fe526c66701859159dc235f6c7d947edf25a9935bdf05 \
  --limits "$C26_ROOT/limits.json" --output "$C26_ROOT/batch.json"
/app/.venv/bin/python -B -m scripts.cs50_batch download \
  --batch "$C26_ROOT/batch.json" --archive "$C26_ROOT/archive" \
  --approvals "$C26_ROOT/approvals.json" --limits "$C26_ROOT/limits.json" \
  --output "$C26_ROOT/reports/download-preview.json"
```

Preview kontrollieren: drei ausgewählte und freigegebene Quellen, keine
ausgeführte Übertragung. Bei PDF-Erweiterung dieselben fünf IDs in Export und
`plan` verwenden; die Bindungsprüfung lehnt abweichende Auswahl ab.
Erst nach der tatsächlichen Quellen-/Downloadfreigabe:

```sh
/app/.venv/bin/python -B -m scripts.cs50_pilot preflight --root "$C26_ROOT" --phase download
/app/.venv/bin/python -B -m scripts.cs50_batch download \
  --batch "$C26_ROOT/batch.json" --archive "$C26_ROOT/archive" \
  --approvals "$C26_ROOT/approvals.json" --limits "$C26_ROOT/limits.json" \
  --output "$C26_ROOT/reports/download-attempt-01.json" --confirm
/app/.venv/bin/python -B -m scripts.cs50_pilot preflight --root "$C26_ROOT" --phase download
/app/.venv/bin/python -B -m scripts.cs50_batch seal \
  --batch "$C26_ROOT/batch.json" --archive "$C26_ROOT/archive" \
  --approvals "$C26_ROOT/approvals.json" --limits "$C26_ROOT/limits.json" \
  --output "$C26_ROOT/catalog" --confirm
/app/.venv/bin/python -B -m scripts.cs50_pilot configure --root "$C26_ROOT" --confirm-setup
/app/.venv/bin/python -B -m scripts.cs50_pilot preflight --root "$C26_ROOT" --phase process
```

Alle Rohdateien und originalen HTTPreceipts werden erneut SHA-/Scope-geprüft,
unverändert in neue Katalogbundles übernommen und vollständig gegen die Auswahl
validiert. `configure` verlangt einen vollständigen Katalog; ein Teilkatalog ist
kein stillschweigend vollständiger Pilot. Keine bestehende Publikation überschreiben.
Downloadexit 1 bedeutet mindestens einen Teilfehler: **vor Seal stoppen**.
Unveränderte erfolgreiche Downloads bleiben wiederverwendbar. Nach eigener
Fehler-/Freigabeprüfung darf genau derselbe Downloadbefehl mit `--retry-failed`
und neuem `--output .../download-attempt-02.json` wiederholt werden. Kein neuer
Scope und kein anderer Rawhash unter alter Erwartung; bei Größenüberschreitung
nicht die Grenze anheben. Nach erfolgreicher Prüfung einmalig sealen. Ein
abgebrochenes Seal bleibt ein eigener Konflikt; keinen Teilkatalog zurechteditieren.

## Ein Worker, Jobs nacheinander, Gesamtbericht

Terminal A: genau den vorhandenen `scripts.cs50_worker --config
"$C26_ROOT/controller.json" --limits "$C26_ROOT/limits.json"` wie im B3-Runbook
im Vordergrund starten. Keine zweite Workerinstanz. Terminal B, gleiche UID,
Policy, Root und Token:

```sh
/app/.venv/bin/python -B -m scripts.deployment health \
  --config "$C26_ROOT/controller.json" --role worker
/app/.venv/bin/python -B - "$C26_ROOT/catalog/catalog.json" <<'C26_REFS_PY'
import json, sys
for ref in sorted(json.load(open(sys.argv[1]))['catalog']):
    print(ref)
C26_REFS_PY
```

Jeweils **einen** ausgegebenen Ref bewusst als `C26_REF` setzen. Die CLI bleibt
asynchron; erst nach dessen terminalem Report zum nächsten Ref wechseln.
Es gibt keine automatische Schleife, Hintergrundqueue oder Wiederholung:

```sh
: "${C26_REF:?Einen freigegebenen Source-Ref aus dem neuen Katalog waehlen}"
/app/.venv/bin/python -B -m scripts.cs50_batch workflow execute \
  --config "$C26_ROOT/controller.json" --token-file "$C26_TOKEN" \
  --catalog "$C26_ROOT/catalog/catalog.json" --source-ref "$C26_REF" \
  --limits "$C26_ROOT/limits.json" --confirm
/app/.venv/bin/python -B -m scripts.cs50_batch workflow report \
  --config "$C26_ROOT/controller.json" --token-file "$C26_TOKEN" \
  --catalog "$C26_ROOT/catalog/catalog.json" --source-ref "$C26_REF" \
  --limits "$C26_ROOT/limits.json"
```

Nur `report` wiederholen. Ein fehlgeschlagenes/abgebrochenes Material bleibt
sichtbar; nach Entscheidung können unabhängige übrige Materialien seriell folgen.
Hash-/ACL-/Quarantäne-/Speicherfehler sind dagegen Blocker, keine automatische
Fortsetzungsfreigabe. Reconciliation und ausdrücklich bestätigtes `workflow resume`
für genau einen Ref wie B3. Abgeschlossene Jobs bleiben idempotent; bei echten
Fehlversuchen bleiben Historie und globale Rootbudgets begrenzt.

Gesamtzustand aller ausgewählten Quellen ohne `--source-ref` lesen, zuerst ohne
Outputdatei. Sobald der gewünschte Endzustand vorliegt, bewusst neu speichern:

```sh
/app/.venv/bin/python -B -m scripts.cs50_batch workflow report \
  --config "$C26_ROOT/controller.json" --token-file "$C26_TOKEN" \
  --catalog "$C26_ROOT/catalog/catalog.json" --limits "$C26_ROOT/limits.json" \
  --output "$C26_ROOT/reports/week0-report-01.json"
```

Der bestehende C26-Report erhält `summary`: pro Material Status, Fehler,
Raw-/Workflowreporthash, technische Block-/Code-/Unitzahlen, ausgeschlossene
Block-IDs mit Gründen, Qualitystatus und Findinghäufigkeiten. Qualitäts- und
Handoffbytes werden vor der Zählung gegen die C18-Outputhashes und existierenden
Pydanticverträge geprüft. Codeerhalt vergleicht vollständige Codeblocktexte mit
ihren kanonischen Units; verlorener Code ist ein Fehler. Keine Quelltexte im
neuen Summary. `accounting=null` bedeutet **nicht geprüft**, nicht null Qualität;
`accounted_materials` nennt den tatsächlichen Zählumfang. Synthetische Herkunft
bleibt sichtbar. Keine neue Qualitätsrate oder automatische Freigabe:
`execution_supported=false`, `knowledge_fact_verified=false` bleiben fest.
Exit 1 bei Fehler-/Blocker-/Abbruch-/Stale-Befunden; pending bleibt ein offener,
asynchroner Zustand, kein Erfolg des gesamten Wochenpiloten.

## Vollkursblockaden und verbleibende Abnahme

Diese begrenzte Auswahl ist kein automatischer Vollkursplan. Dafür fehlen
vollständige Sourceinventur einschließlich Aufgaben/Codeeinzeldateien, einzeln
geprüfte Rechte, aktuelle Größen und ausreichend freigegebener Speicher für
Archiv, Katalogduplikate, Parserausdehnung und Versuchshistorie. Medien und
Transcripts brauchen weiterhin ihre getrennten bestehenden Verträge.
Die B4-Auswahl ist absichtlich auf Week 0 und acht Materialien begrenzt;
ein Vollkurs darf nicht durch Entfernen dieser Grenzen stillschweigend entstehen.
Technischer Folgeschritt nach begrenzter Realabnahme: die bereits vorhandenen
Discovery-Week-1–9-Referenzen je Woche prüfen, explizite Teilbatches und neue
freigegebene Roots planen und die Sectionauswahl separat überprüfbar erweitern.
Der vorhandene generische Batchvertrag bleibt dabei die Grundlage; aktuell
startet der Pilothelfer bewusst keine anderen Wochen oder Kursgesamtauswahl.
Keine GC-/Retention-/Drive-Migration, kein ContentStoreimport, keine Embeddings
oder Wissensextraktion. Keine fachliche Freigabe ohne echte menschliche Prüfung.

Hostmounts, Ressourcen, Neustart und reale Materialqualität sind hier
`not_checked`. PRreview, Image-/Bundleupdate, konkrete neue Pfade, Principal,
alle Quellenentscheidungen und das exklusive Betreiberfenster bleiben vor der
Ausführung erforderlich. Die [B4-Validierung](validation.md#c26-b4--week-0-batchvorbereitung)
trennt die synthetischen Nachweise von diesen offenen Realprüfungen.
