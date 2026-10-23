# Lesender Kapazitätsbericht — 23.10.2026

**Lokaler C26-Pilot: NO-GO.** Gemessen wurden 3,797,196,800 freie Bytes
(3.536 GiB). Das vorhandene Budget eines konkret gebundenen
Ein-Material-C18-Batches verlangt 7,539,750,868 Bytes
(7.022 GiB). Zusätzlich fehlen mindestens
**3,742,554,068 Bytes (3.486 GiB)**.
Die Momentaufnahme steht in `capacity.v1.json`; vor jedem Schreiben neu messen.
Dieser lokale Befund ist keine Messung der Hetzner-Produktionskapazität.

## Dateisysteme, Inodes und Grenzen

- Workspace und `/tmp`: dasselbe 32-GB-Blockgerät `/dev/vdc`, Btrfs-Bindmounts,
  insgesamt 33,930,240,000 Bytes. Ein Wechsel
  nach `/tmp` schafft keine zusätzliche Kapazität.
- Auch `/home/robfra/.codex` und `.cache` liegen auf demselben Gerät. Für
  `.codex/thread-writer-locks` wurde keine Datei verändert; die aktuelle Messung
  beweist oder widerlegt die historische ENOSPC-Situation nicht.
- `df -i` und `statvfs` melden für diese Mounts null Gesamtinodes; verfügbare
  Inodes sind deshalb **unknown**, nicht nachgewiesen erschöpft und nicht als
  ausreichend bestätigt.
- Eingebundenes Google Drive: `9p` über `/mnt/chromeos`. Die virtuellen Angaben
  von circa 1 EiB und mehr verfügbaren als gesamten Inodes sind kein plausibler
  Kapazitäts-/Quota-Nachweis. Originale bleiben lesend; kein SQLite-/Jobziel dort.
- `du` war ausschließlich lesend. Teilbereiche von Monitoring und privaten
  Systemverzeichnissen sind nicht lesbar. Keine Rechteänderung oder Nachscan mit
  erhöhten Rechten. Btrfs-COW/Hardlinks verhindern eine verlässliche Gleichsetzung
  von aufsummierten `du`-Werten mit tatsächlich freisetzbaren Bytes.

## Bestehendes Batchbudget

| Bestandteil des einen HTML-Materials | Bytes |
| --- | ---: |
| Verifizierte Discovery-/Overview-Closure | 2,586,580 |
| Rohdatenobergrenze | 1,048,576 |
| Archivinkrement (Raw plus Allowance) | 2,097,152 |
| Kataloginkrement einschließlich Snapshotkopie | 4,683,732 |
| Bestehendes Jobbudget | 2,147,483,648 |
| Reportbudget | 16,777,216 |
| Unveränderte Mindestreserve | 5,368,709,120 |
| **Benötigt frei vor dem Batch** | **7,539,750,868** |

Discovery und Raw sind in den Inkrementen berücksichtigt, nicht nochmals zur
Summe addieren. Quelle: bestehendes `capacity.estimate` und hashvalidierter
neuer Ein-Notes-Batch aus den bestehenden Snapshots, ohne Download oder Dispatch.
Das ist ein kontrolliertes Planungsbudget, keine Messung tatsächlicher
Parserexpansion. Es gibt noch keinen produktiv genehmigten Gesamt-Week-0-Batch;
seine Auswahl, Rohdaten und Grants fehlen. Für eine andere Auswahl erneut den
konkreten Batch schätzen; nicht zehn Archive als C18-Batch unterstellen.

Zum Vergleich verlangt der vorhandene ZIP-Vorabcheck 5 GiB Reserve plus
64 MiB Archiv- und 16 MiB Reportallowance, insgesamt 5,452,595,200 Bytes.
Auch dieses niedrigere Budget ist unterschritten. Ein ZIP-Import ist in diesem
Auftrag unabhängig davon nicht freigegeben. Kein Limit wurde verändert.

## Regenerierbare Caches und geschützte große Artefakte

Gezielter Scan in den lokalen Personal-Assistant-Kopien, ohne `.venv`, `.git`,
Pilot-/Daten-/Monitoringverzeichnisse und ohne Symlinkverfolgung:
**23 Cacheverzeichnisse, 921,600 zugeordnete Bytes**.
Typen ausschließlich `__pycache__`, `.pytest_cache`, `.ruff_cache`.
Vollständige relative Liste: `cache_candidates.v1.json`. Aktive Nutzung wurde
nicht ausgeschlossen; selbst vollständiges Freigeben würde das Defizit praktisch
nicht verändern. `.codex/thread-writer-locks` wurde nicht verändert.

Weitere beobachtete Größen, ausdrücklich keine Löschfreigabe:

| Verzeichnis/Gruppe | Beobachtete Belegung | Bewertung |
| --- | ---: | --- |
| `.cache/camoufox` | 1,303,429,120 Bytes | Regenerierbare Browserinstallation; Nutzung/Version prüfen, separate Freigabe nötig |
| `.cache/ms-playwright` | 713,211,904 Bytes | Browserartefakte; kein sicher belegtes redundantes Exemplar, separate Freigabe nötig |
| `.cache/uv` | 333,463,552 Bytes | Aktive Testumgebung verweist auf diesen Cache; nicht bereinigen |
| `.cache/pre-commit` | 115,748,864 Bytes | Für Commit-/Pushprüfungen in Gebrauch; erhalten |
| Backend `.git` | 574,820,352 Bytes | Darin circa 500.9 MB Konsolidierungsbelege; Git/Archive/Bundles geschützt |
| UI-C26B `.venv` | 553,209,856 Bytes | Bestehende Pythonumgebung; geschützt und aktuell für UI-Tests verwendet |
| Frühere `c26-final-results` | 179,384,320 Bytes | Mehrfach synthetische Testbäume, circa 49.1/57.7 MB Regression/Kompatibilität; Logs, Diagnose und Bundle aufbewahren |
| Backend-Worktrees | 75 registriert, 10 verwaiste Metadateneinträge | Viele ähnliche Checkouts um 26 MB, aber unterschiedliche Heads/Belege; keine automatische Redundanz- oder Löschannahme |
| UI-Worktrees | 17 registriert | Gemeinsame/historische Artefakte bleiben erhalten |

## Konkreter Bereinigungs- und Kapazitätsplan

1. Eigentümer und aktive Prozesse für jeden Kandidaten klären; Liste privat mit
   Aufbewahrungs-/Reproduktionsbedarf abgleichen. Kein Lock, Worktree, Venv,
   Gitobjekt, Bundle, Quellarchiv, Pilotdatum, DB oder Volume löschen.
2. Optional separat freigeben: die exakt gelisteten Python-/Testcaches nach
   bestätigtem Testende. Gewinn höchstens rund 0.88 MiB, daher nicht als Lösung
   des Batchdefizits planen.
3. Für alte synthetische Testbäume zunächst Logs/JUnit/Fehlerdiagnose/Quellhashes
   dauerhaft sichern und Eigentümerfreigabe für exakt benannte Unterbäume einholen.
   Worktrees, ursprüngliche Rohdaten, Bundles und Archive bleiben ausgenommen.
   Wiederholte Testbäume sind Entwicklungskandidaten, kein bereits bestätigter
   sicherer Löschbestand.
4. Browsercache-/Installationsversionen nur nach bestätigter Nichtnutzung und
   separater Freigabe einzeln bereinigen. Selbst deren nominelle Summe von
   rund 1.88 GiB plus allen kleinen Caches deckt das Ein-Material-Defizit nicht.
5. Bevorzugt zusätzliche lokale Kapazität beziehungsweise ein separat genehmigtes
   geeignetes bestehendes Linux-Ziel bereitstellen: **mindestens 3.486
   GiB zusätzlich zum Messstand**, plus zwischenzeitliches Wachstum. Keine
   automatische Umstellung von Mounts, Speicherlimits oder Reserve.
6. Danach `df -h`, `df -i`, Zielmountzuordnung und den bestehenden Batch-Vorabcheck
   wiederholen. Unknown-Inodes und virtuelle Drivewerte separat klären.
   Erst wenn das exakte Budget samt Reserve auf dem tatsächlichen Ziel vorhanden
   ist, über die weiteren Betreiberfreigaben entscheiden.

Keine Datei gelöscht, verschoben oder bereinigt. Quell-/Pilotdaten und alle
bestehenden Umgebungen bleiben unverändert. Testläufe erzeugen ausschließlich
neue auftragseigene synthetische Prüfdaten und Berichte.
