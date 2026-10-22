# C26-B7: Prüfprotokoll und verbleibende Ausführungsgrenzen

22.10.2026. Basis master `6786b5d67b31125895d94af7b763a1002aeeea7d`, B4/#141 und
B5/#142 integriert. B6/#144 sowie Knowledge-Fix #143 beim GitHub-Livecheck offen,
jeweils `mergeCommit=null`. Kein Merge/Cherry-Pick oder Zugriff auf deren privaten
Arbeitsdaten. Eigener Arbeitsbranch `feat/c26b7-media-last`, eigener B7-Worktree.
[Architektur, Matrix, Fallbackregeln und Realpilot-Runbook](media_last_pilot.md).

## Tatsächlicher Umfang

Kleine versionierte Planungsmodelle, read-only Evidenzadapter für bestehende
B5-/Materialreceipts, deterministische F0–F6-Auswahl und ein neuer Unterbefehl
`scripts.cs50_batch media-plan` in der bestehenden CLI. Vorhandene Discovery-/
Material-/Varianten-/Selection-/Approvalmodelle werden weiterverwendet.
Keine neue Workflowengine oder Medienpipeline. Kein Aufruf der vorhandenen
yt-dlp-, faster-whisper-, ffmpeg- oder Remote-Visualfunktionen.

Verfügbarkeit, Verifikation, technischer Adapter, zweckbezogene Eignung und
fachliche Validierung bleiben getrennt. Eine Remote-URL allein ist kein
Verfügbarkeitsbeleg. Unvollständiges Text-/Visualwissen, fehlende Entscheidungen
und nicht vorhandene Ausführungsadapter werden als Blockaden dokumentiert.
Das bestehende Workerimage übernimmt den Src-/Batchumfang bereits über seine
COPY-Regeln; keine Dependency-, Dockerfile-, Mount-, CMD- oder Restartänderung.

## Umgebung und tatsächlich ausgeführte Tests

Vorhandene Backendvenv: Python 3.12.12, Pytest 9.1.1, Pydantic 2.13.4,
BeautifulSoup 4.15.0, PyMuPDF 1.28.2, SQLite 3.50.4; Ruff 0.16.0.
Kein Installieren/Sync, keine Downloads. Gemeinsames tatsächliches Präfix:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  /home/robfra/0_Portfolio_Projekte/gmp_compliance/.venv/bin/python -m pytest
```

Neue Suite mit diesem Präfix:

```sh
-q -p no:cacheprovider tests/test_cs50_media_plan.py \
  --basetemp=/dev/shm/c26b7-boundaries
```

**38 passed / 0 failed / 0 skipped**, 40,06 s. Die Suite enthält sechs Pfadvarianten.
Zusammen mit der disjunkten Bestandsregression: **495 passed, 3 skipped**.
Vorherige Zwischenläufe:

| Eigenes Basetemp | Ergebnis | Dauer / Befund |
| --- | --- | --- |
| `/dev/shm/c26b7-new` | 18 passed / 1 failed | 36,92 s; neue HTMLfixture erwartete `passed`, bestehender Gate meldet korrekt `passed_with_warnings`; Assertion auf tatsächlichen Warnzustand korrigiert, kein Gate abgeschwächt |
| `/dev/shm/c26b7-final` | 27 passed | 39,70 s; erste Erweiterung um Varianten-/Medienlimits |
| `/dev/shm/c26b7-release` | 29 passed | 52,92 s; Readiness, offene Scopeabdeckung und lokale Wiederverwendung |
| `/dev/shm/c26b7-complete` | 31 passed | 38,96 s; Referenz-/Verfügbarkeitstrennung, Rollenprüfung und Modellzustände |

Diese Läufe überlappen und werden nicht addiert. Nach dem 31er-Lauf wurden
ausdrückliche Evidence-Pfadvalidierung und Audio-vor-Video bei reinem Textbedarf
ergänzt; die ganze neue Suite wurde dafür erneut ausgeführt. Alle neuen Tests
blockieren Socketverbindungen/DNS und `subprocess.Popen`: unbeabsichtigtes
Netzwerk, Whisper oder ffmpeg würde den Test sofort fehlschlagen lassen.

Bestehende Regression mit demselben Präfix:

```sh
-q -p no:cacheprovider \
 tests/test_cs50_pilot.py tests/test_cs50_week_pilot.py \
 tests/test_cs50_multiformat.py tests/test_cs50_batch_worker.py \
 tests/test_cs50_capacity.py tests/test_worker_image_content.py \
 tests/test_official_transcript_import.py tests/test_cs50_discovery.py \
 tests/test_cs50_selection.py tests/test_cs50_timed_selection.py \
 tests/test_cs50_material_quality.py tests/test_cs50_lecture_adapter.py \
 tests/test_cs50_visual_inventory.py --basetemp=/dev/shm/c26b7-regression
```

**457 passed / 0 failed / 3 skipped**, 233,77 s. Die drei bekannten optionalen
Skips: redundante Nicht-root-Bootstrapprüfung unter root (separater UID-Wechseltest
ausgeführt), nativer Docker-Context-Audit ohne Aktivierung und Prüfung eines
gebauten Workerimages ohne bereitgestelltes Image. Keine vollständige
Repositorysuite und keine neue Docker-/Hostabnahme behauptet. Die spätere Änderung
betrifft ausschließlich neue B7-Pfade; bestehende Discovery/B3/B4/B5-Verträge blieben
unverändert. Nicht integrierte B6-Tests wurden nicht als Masterregression ausgegeben.

## Abgedeckte Entscheidungen und Grenzen

- Tatsächlicher synthetischer B5-SRT-Import vor Planprüfung: überlappende Cues,
  Sprache, Dauer, Raw-/Payload-/Receipt-/Batch-/Importerrevision; keine erneute
  Beschaffung oder Verarbeitung bei ausreichendem lokalem Transkript.
- Unbekannte Zweck-Eignung sperrt vor Medien. Technischer Gate-Erfolg gilt nicht
  als semantischer Review. Zweck-/Hashkonflikte und fremde Lecture-IDs werden
  abgewiesen, Schema-/Ressourcenversionen validiert.
- Tatsächlicher synthetischer HTML-v2-Import und vorhandener C10-/Lecturehandoff:
  read-only erneut geprüft; technische Warnungen bleiben sichtbar. Ein Rawmedium
  oder Transkript schließt fehlende visuelle Evidenz nicht automatisch.
- Lokales, ausdrücklich ausgewähltes und hashgebundenes Audio kann F4 vorschlagen;
  bei reinem Textbedarf hat es Vorrang vor lokalem Video. Kein Codec-/Duration-
  oder Transkriptionsnachweis wird aus opaken synthetischen Medienbytes abgeleitet.
- Remoteaudio/-video ohne Genehmigung, zugelassenes Video ohne Reserve, fehlende
  Schätzung, Größen-/Dauerüberschreitung, unfreigegebene Transkription und
  Zeitfensterkonflikte blockieren. Kein Downloaderwechsel nach Zugangssperre oder
  technischem Fehler. Eine unbeteiligte frühere Medienfehlermeldung erzwingt keinen
  Medienbedarf, wenn ausreichende verifizierte lokale Materialien existieren.
- Manipulierte Hashes/Receipts/Payloads, Symlinks und Grantwiderruf stoppen
  Eskalation. Explizite Medienpfade sind relativ/normalisiert, externe Root-/Batch-/
  Planpfade absolut. Keine Verzeichnissuche oder Reparatur bestehender Archive.
- Wiederholte Pläne identisch, Referenz-/Genehmigungs-/Implementierungshashes
  gebunden, alte/manipulierte Vorberichte abgewiesen. CLI-No-Overwrite getestet.
- Aus dem versionierten Week-0-Snapshot sind fünf unterschiedliche Shorts und
  acht Medienvarianten belegt; Google Slides ist getrennte unprozessierte Referenz.
  Short-Scope übernimmt keine ungeprüften Lecturetranskripte. Verifizierte und nur
  referenzierte Transkriptsprachen werden getrennt ausgegeben.

Ruff Check und Format Check für die fünf geänderten/neuen Pythondateien:

```sh
RUFF=/home/robfra/.cache/pre-commit/repokzno83cn/py_env-python3.12/bin/ruff
"$RUFF" check --no-cache src/model_materials/media_plan.py \
  src/tools_materials/media_plan.py src/tools_materials/media_evidence.py \
  scripts/cs50_batch.py tests/test_cs50_media_plan.py
"$RUFF" format --check --no-cache src/model_materials/media_plan.py \
  src/tools_materials/media_plan.py src/tools_materials/media_evidence.py \
  scripts/cs50_batch.py tests/test_cs50_media_plan.py
git diff --check
```

Endgültiger Ruff Check, Format Check, diff check und lokale Dokumentationsziele
sind erfolgreich geprüft. Neue Ruff-Befunde während der Entwicklung waren ein ungenutzter
Import und eine fehlende Importgruppen-Leerzeile; keine Runtime-/Altfehler.

## Nicht ausgeführt und Lifecycle

Keine SSH-Verbindung, Host-/Containeränderung, Build, reale Material-/Media-
Beschaffung, reale Transkription, externe Modelle oder private Originalreads.
Keine unabhängigen Goldreferenzen, fachliche Abnahme oder Vollständigkeitswerte.
Die bekannten separaten Knowledge-Fixbefunde gehören zu #143; die Knowledge-
Gesamtsuite wurde hier nicht erneut ausgeführt oder als erfolgreich ausgewiesen.
Reale Freigaben, Modellcache, Codec-/Dauerprobe, harte Medienprozesslimits,
Receipts/Abbruch/Wiederanlauf und Hostressourcenabnahme bleiben offen.

Dauerhafte Unterlagen werden über einen regulären PR gegen master geliefert.
Kein automatischer Merge. Bis zur nachgewiesenen Integration bleiben eigene
Branches und Worktrees erhalten; keine Bereinigung historischer/anderer Aufgaben
oder MAINT-Bestände. Bereits bei der Worktreeanlage meldete die lokale Umgebung
ENOSPC beim Schreiben gemeinsamer Git-Konfiguration trotz freiem Blockspeicher;
der Worktree wurde angelegt. Git-Updates werden vor Veröffentlichung geprüft;
unklare Ref-/Indexzustände werden erhalten, nicht durch Force/Reset repariert.
