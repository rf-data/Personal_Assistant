# C26-B6: tatsächliche Offlinevalidierung

22.10.2026. Ausgangsbasis `6786b5d67b31125895d94af7b763a1002aeeea7d`, Backend-master
mit B4/#141 und B5/#142. Eigener Branch `feat/c26b6-code-zip-import`.
[Vertrag, Materialmatrix und Realpilot-Runbook](code_zip_pilot.md).

## Implementierter Umfang

Opt-in-Erweiterung der vorhandenen Discovery/Materialpläne um direkt belegte
Pythonquellen; bestehende Batch-v1- und SourceApproval-Verträge bleiben erhalten.
Der bestehende `scripts.cs50_batch` erhält `code-inventory` und
`code preview|import|report`. Ein kleiner Offlineadapter verwendet Code-v1,
ArtifactReceipt, Quality Gate und LectureMaterialHandoff. ZIP-Mitglieder werden
begrenzt im Speicher geprüft, ausschließlich über freigegebene bestehende
Quellidentitäten abgebildet und unter hashbasierten Pfaden publiziert.
AST-Projektionen laufen isoliert, niemals als Ausführung des importierten Codes.

Keine neue Queue, kein zweiter Gesamtparser, keine C18-ZIP-Freischaltung, keine
Knowledge-/ContentStore-Publikation. Keine neuen Dependencies, keine Image- oder
Infrastrukturänderung. Das vorhandene Worker-Dockerfile kopiert den benötigten
Skript-/Src-Umfang bereits. Kein Build, Deployment oder Containerzugriff ausgeführt.

## Umgebung und Befehle

Vorhandene Backendvenv: Python **3.12.12**, Pytest **9.1.1**, Pydantic **2.13.4**,
BeautifulSoup **4.15.0**, PyMuPDF **1.28.2**, SQLite **3.50.4**. Ruff **0.16.0**.
Keine Installation, kein Sync und kein Download. Tatsächliches Pytestpräfix:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  /home/robfra/0_Portfolio_Projekte/gmp_compliance/.venv/bin/python -m pytest
```

Gemeinsame Code-/Material-/Discoveryprüfung mit diesem Präfix:

```sh
-q -p no:cacheprovider \
 tests/test_cs50_code_zip.py tests/test_cs50_material_code.py \
 tests/test_cs50_material_contracts.py tests/test_cs50_material_processing.py \
 tests/test_cs50_material_mapping.py tests/test_cs50_material_quality.py \
 tests/test_cs50_lecture_adapter.py tests/test_cs50_discovery.py \
 --basetemp=/dev/shm/c26b6-release
```

**230 passed / 0 failed / 0 skipped**, 77,52 s. Darin 54 neue B6-Fälle und
176 bestehende Code-/Material-/Quality-/Handoff-/Discoveryfälle. Ein erwarteter
stdlib-ZIP-Warnhinweis entsteht beim absichtlichen Erzeugen doppelter Namen;
die Verarbeitung weist das Archiv ab.

Bestehende C26-Regression mit demselben Präfix:

```sh
-q -p no:cacheprovider \
 tests/test_cs50_pilot.py tests/test_cs50_week_pilot.py \
 tests/test_cs50_multiformat.py tests/test_cs50_batch_worker.py \
 tests/test_cs50_capacity.py tests/test_worker_image_content.py \
 --basetemp=/dev/shm/c26b6-c26
```

**152 passed / 0 failed / 3 skipped**, 140,57 s. Skips: der unter root redundante
Nicht-root-Bootstrapfall (separater UID-Wechseltest läuft), optionaler nativer
Docker-Context-Audit und Prüfung eines tatsächlich gebauten Workerimages. Kein
gebautes Image bereitgestellt, kein Dockerlauf als erfolgreich ausgegeben.
Diese Suite überlappt die vorherige nicht: zusammen **382 passed, 3 skipped**.

Nach dem gemeinsamen Lauf wurde ausschließlich die kontrollierte Umwandlung von
`zlib.error` bei beschädigten Deflatebytes in einen sicheren Materialfehler ergänzt.
Der neue Angriff wird zusätzlich im bestehenden ZIP-Beschädigungsfall geprüft.
Die ganze neue B6-Datei wurde anschließend mit demselben Präfix und
`-q -p no:cacheprovider tests/test_cs50_code_zip.py
 --basetemp=/dev/shm/c26b6-zip-final` erneut ausgeführt:
**54 passed / 0 failed / 0 skipped**, 44,64 s, derselbe erwartete ZIP-Warnhinweis.
Dieser Lauf überlappt die 54 neuen Fälle und wird nicht addiert.

## Nachgewiesene Grenzen

- Synthetischer ZIP-/Python-Roundtrip über echte Code-v1-Modelle, den bestehenden
  read-only Quality Gate und Handoff; drei Pythonquellen derselben Lecture,
  einschließlich zweier ausdrücklich zugeordneter ZIP-Mitglieder.
- Rawbytes, BOM, Tabs, CRLF, Unicode/Combining-Zeichen, vollständige Zeilen,
  Docstrings, Klassen, Funktionen und Imports; Quellcode mit Seiteneffekt bzw.
  `raise` bleibt unausgeführt. AST-Syntax-/Knoten-/Workerfehler sind keine
  behaupteten fachlichen Rekonstruktionsfehler.
- Unbekannte/nested/binary/ausführbar markierte ZIP-Mitglieder werden ausgewiesen;
  Traverse-/absolute-/Windows-/NULpfade, Symlinks, Spezialdateien, Doppel-/NFC-/
  Casefold-/Dateiverzeichniskollisionen, ZIP64, nicht erlaubte Kompression,
  Verschlüsselung, CRC-/Deflatebeschädigung, Größen-/Count-/Gesamt-/Ratio-Bounds.
- Eigenständige und Mitglieder-Process-Freigaben samt erwarteten Hashes,
  fehlende/widersprüchliche Grants, falsche Original-URLs und fehlende Lecturebindung.
  Keine Downloadgenehmigung aus einer Process-Freigabe abgeleitet.
- Hash-/Receipt-/Handoff-/AST-Manipulation, fremde/teilpublizierte Ziele,
  veränderte Implementierung und entzogene Freigaben bleiben blockiert und
  unverändert. Erfolgreiche Gruppen sind bei Wiederholung byteidentisch;
  fehlgeschlagene Gruppen beeinträchtigen andere Gruppen nicht.
- No-Overwrite, Serialisierung bei Lockkonflikten, private Dateirechte,
  Symlinkabweisung und niedrige Kapazität. Der lokale freie Speicher liegt unter
  der Produktionsreserve; ausschließlich synthetische Fixtures modellieren
  100 GiB freien Platz. Der reale 5-GiB-Guard wurde nicht abgeschwächt.
- Die tatsächliche CLI liest bestehende Batch-/Approval-/Limitsmodelle; Import
  verlangt explizite Bestätigung, Report wiederholt die Prüfung eigener Bytes,
  vorhandene Reportdateien werden nicht ersetzt.
- Versionierter Week-0-Snapshot: 24 direkte Pythonkandidaten, 72 unveränderte
  Queryansichten ohne behauptete Contentgleichheit und zwei ZIP-Referenzvorkommen.
  Bestehende Ressourcen/IDs bleiben erhalten. Keine Raw-Python-/ZIP-Datei aus
  realem oder privatem Bestand wurde importiert oder angefordert.

Ruff Check und Format Check für die acht geänderten/neuen Pythondateien:

```sh
RUFF=/home/robfra/.cache/pre-commit/repokzno83cn/py_env-python3.12/bin/ruff
"$RUFF" check --no-cache src/tools_materials/code_*.py \
  src/tools_materials/batch.py src/tools_materials/processing.py \
  scripts/cs50_batch.py tests/test_cs50_code_zip.py
"$RUFF" format --check --no-cache src/tools_materials/code_*.py \
  src/tools_materials/batch.py src/tools_materials/processing.py \
  scripts/cs50_batch.py tests/test_cs50_code_zip.py
git diff --check
```

Alle erfolgreich. Ein anfänglicher Ruff-Cache-Schreibversuch meldete ENOSPC;
die endgültigen Checks liefen ohne Cache. Kein produktiver Guard wurde angepasst.

## Entwicklungsläufe und bestehende Lücken

Erster neuer Lauf: **40 passed**, 20,55 s. Erweiterter gemeinsamer Entwicklungslauf:
**227 passed / 1 failed**, 87,34 s. Der neue synthetische Gesamtgrößen-Test erzeugte
mit einem 32-KiB-Wiederholungsmuster ein schlecht komprimierbares Archiv oberhalb
der Rawgrenze; seine Vorbedingung war falsch. Ein 16-KiB-Muster erzeugt bei gleicher
9-MiB-Istgröße ein 211.468-Byte-Archiv, das gezielt an der Gesamtgröße abgewiesen
wird. Keine Produktionsgrenze oder Assertion wurde dafür abgeschwächt.
Anschließend **52 passed**, 25,64 s, bevor ZIP64- und die versionierte
Inventurprüfung hinzukamen. Diese Läufe sind keine zusätzlichen Abnahmefälle.

Knowledge-Fix #143 (`fix/c26b5-knowledge-identities`) war beim GitHub-Livecheck
weiterhin offen, `mergeCommit=null`. Er wurde nicht übernommen, gemergt oder
parallel nachimplementiert. Die bestehende Knowledge-Suite und die langlaufende
globale Batch-/Knowledge-Regressionssuite wurden hier nicht erneut ausgeführt;
deren bekannte Befunde gehören zum separaten Fixauftrag. Die oben genannten
betroffenen B6-/C26-/Materialprüfungen haben keine bestehenden Fehler ergeben.
Keine vollständige Repository-, Sicherheits-, Last- oder Realabnahme behauptet.

Ungeprüft bleiben insbesondere echte ZIP-Layouts/Modi/Encoding, aktuelle
Download-/Nutzungsrechte, Originalbereitstellung, reale Ressourcenmessung im
Hetzner-Worker und unabhängige fachliche Goldreviews. Größere Archive und weitere
Kurse/Wochen benötigen einen getrennten Kapazitäts-/Vertragsentscheid.

## Integration und Lifecycle

Dauerhafte Implementierung, Tests, Matrix, Prüfbericht und Runbook werden über
einen regulären PR gegen master geliefert. Der PR bleibt ausdrücklich offen;
kein Merge, Deployment, SSH, realer Download, bestehender Pilot-/Storezugriff oder
Cleanup fremder/historischer Branches/Worktrees. Bis zum nachgewiesenen Merge
bleiben der eigene B6-Branch und Worktree erhalten. Ihre Aufbewahrung ist wegen
der ausstehenden Integration notwendig; Dokumente sind vorher nicht als im
Defaultbranch integriert auszugeben.
