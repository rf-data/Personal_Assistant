# C23-02C: Bestandsprüfung und Betriebsvertrag

Vor Implementierung geprüft, 17.10.2026. Basis Master
`9a1325485f1b2acc7df177b8a137f771190eca97`, A (#76) und B (#77) gemergt.
Maßgeblich: Persistenz-ADR, Datenmodell und Implementierungsdokumentation unter
`docs/architecture/`, C23-Plan/Governance und Roadmap. C23 bleibt offen.

## Abweichungen des A/B-Stands vom geplanten Betriebsvertrag

- content-v1 enthält bereits mutable Quarantänestatus, aber keine Incidenttabelle.
  Unveränderliche Incidentdateien ergänzen den vorhandenen Blob-/DB-Vertrag;
  keine Schemaänderung und keine automatische Migration.
- Ein prepared Run enthält Referenzen, aber keine vollständige Rollen-/Commitabsicht.
  Neue Imports erhalten nach Verifikation einen hashgebundenen Wiederaufnahmebeleg.
  Alte unvollständige Runs ohne diesen Beleg bleiben blockiert; keine Rekonstruktion
  aus ähnlichen Dateien, Sourcepfaden oder vermuteten Parserständen.
- `ContentStore(root)` verweigert nichtleeres WAL. Deshalb benötigt WAL-Recovery
  einen expliziten Klassen-/Root-Einstieg vor normalem Öffnen. SQLite übernimmt
  Recovery, kein eigener Replay. Unklare/beschädigte Journals bleiben gesperrt.
- C22 `src.job_control.operations` besitzt Operationsfence, SQLite-Backup-API,
  manifest-last und neue Restoreziele. Sein verwalteter Bestand kennt Content
  noch nicht. Keine Änderung an C22-Profil, jobs.sqlite3 oder Produktionsbackup.
- Principal kennt keinen globalen Administrator. Ganzstore-Operationen verlangen
  Operator plus Ownership und Course-Scope für **jede** enthaltene Source.
  Keine erfundene Administratorrolle oder Aufweitung durch gemeinsame Hashes.

## Verbindliche Reihenfolge

C22 Operationsfence (nur späterer Verbund) → Content Maintenance → Run → DB.
Stagingbudget wird innerhalb des Runbereichs über einen exklusiven Directorylock
serialisiert; dieser ruft keinen DB-/Runlock auf. DBcode erwirbt keinen Runlock.
Alle Locks nonblocking. Maintenance exklusiv für Recovery/Integrität/Backup,
shared für normale Reads/Writes. Aktive Writer schließen diese Betriebsaktionen
mit Busy aus. Zeitablauf erteilt nie Übernahmerechte.

Neue Recovery darf ausschließlich persistierte, bereits geprüfte Absichten und
identische Hashbytes aus eigenem Staging/Blobstore verwenden. Kein Reparse,
Download, neuer Candidate aus Aufrufer-Dictionaries oder Gate-Fallback.
Quarantäne wird nicht automatisch aufgehoben. Restore erhält die Statusflags.

Die folgenden Abschnitte ergänzen die vorab geprüften Grenzen um implementierte
Signaturen und tatsächliche Offline-Nachweise. Produktionsbetrieb und
Verbundbackup bleiben separat freizugeben.

## Implementierte Schnittstellen

```python
store = ContentStore(explicit_root, read_only=False)
runs = store.inspect_recovery(actor=operator)
result = store.recover_run(run_id, actor=operator)  # action="resume" (Standard)
# Bewusstes Aufgeben, keine Löschung oder Publikation:
result = store.recover_run(run_id, actor=operator, action="reject")
report = store.verify_integrity(actor=operator)  # persistiert Quarantäne/Incidents
# Nichtleeres WAL verhindert normalen Konstruktor; ausschließlich explizit:
report = ContentStore.recover_database(explicit_root, actor=operator)

from src.content_store.backup import backup, restore
manifest = backup(store, new_snapshot_root, actor=operator, snapshot_id=None)
restore(new_snapshot_root, new_empty_root, actor=operator)
# Neues Öffnen: ContentStore(new_empty_root); kein Pfadwechsel oder Autostart.
```

Alle Pfade explizit/absolut/privat außerhalb des Repositories. Keine HTTP-API,
kein neuer CLI-Scheduler. `inspect_recovery` zeigt nur eigene schreibberechtigte
Runs. Resume/Reject verlangen Operator, Ownership, Course und exklusiven Runlock;
Ganzstore-Wartung zusätzlich vollständige Ownership/Scope über alle Sources.
Backup kann einen read-only Storehandle verwenden; Recovery/Quarantäne nicht.

## Dauerhafter Beleg und Zustände

`ProcessingRun.recovery` ist eine optionale JSON-Artefaktreferenz. Sie benötigt
keine DDLänderung: die bestehenden Run-JSONdaten waren bereits mutable.
`operations_models.py` definiert streng versionierte Raw-, Binding- und
Publication-Intents. Nur interne Pfade nach erfolgreicher Stream-/Adapterprüfung
speichern solche Belege mit SHA/Größe/fsync, bevor das Manifest `prepared` wird.
Caller-Dictionaries oder `verified`-Flags können sie nicht veröffentlichen.

Parsed-Intents enthalten Source-/Version-/Stream-/Parserverträge, Original-ID,
konkrete Block-/Locatorprojektion und benannte Archivrefs. Recovery prüft deren
Hash, Run-ID, Requestfingerprint, Slot, Manifest und Sourcebezug erneut. Sie prüft
Receipt/Plan/Revisionsbeleg und bereits gespeicherte Gate-/Handoffdaten nochmals
gegen die unveränderten Payload-/Raw-/Projektionshashes. SRT-Projektionen werden
mit den gespeicherten Segmentmodellen verglichen. **Kein SRT-Reparse**, kein neuer
Materialparser und keine neue Qualityentscheidung: der persistierte Beleg stammt
bereits aus dem erfolgreichen B-Gate. Der abschließende SQLcommit ist derselbe
wie beim normalen Import (`_commit_raw`, `finish_binding`, `finish_publication`).

| Ausgang | Explizite Behandlung | Sichtbarkeit |
| --- | --- | --- |
| `preparing`, kein vollständiger Beleg/Manifest | `blocked`, Grund `recovery_incomplete` | Keine neue Parsed-Version |
| `prepared`/`blocked`, vollständiger Beleg, alle Bytes entweder installiert oder im eigenen Staging | Hash-/Receipt-/Binding-/ACLprüfung, fehlende Blobs ausschließlich aus genau diesem Staging installieren, gleicher finaler Commit | Vollständige Version atomar |
| Fehlende/manipulierte Bytes oder unprüfbare Provenienz | Weiter `blocked`, feste Fehlercodes, vorhandene Belege behalten | Keine Freigabe |
| ACLrevision geändert | `Forbidden`, Run bleibt `blocked` | Keine Veröffentlichung mit alten Rechten |
| `committed`, Response verloren | Artefakte/Version prüfen, `already_committed` und bestehende ID liefern | Bestehende Version unverändert |
| Widersprüchlicher Request/Slot | `Conflict`; Run `rejected` | Kein zweiter Gewinner |
| Explizit `action="reject"` | `rejected` mit `operator_abandoned` | Kein Publish, kein Löschen |

`failed` war im ADR eine fachliche Bezeichnung, aber kein content-v1-SQLzustand.
Der vorhandene terminale Zustand `rejected` bildet das bewusste Aufgeben ab.
Gleicher Requestkey bleibt terminal gebunden. Parsed-Reimport kann nach Reject
einen **neuen expliziten Requestkey** verwenden. Die bisherigen Raw-/Binding-APIs
verwenden intern deterministische Keys; abgelehnte solche Vorgänge können derzeit
nicht unter gleichem Key neu begonnen werden. Kein heimliches Entsperren oder
Überschreiben von Auditdaten; ein erweiterter Retryvertrag bleibt Folgearbeit.

## SQLite-Recovery und Read-only-Grenze

Nur `recover_database` öffnet einen bekannten privaten Root unter exklusivem
Maintenance- und DB-Lock trotz WAL. SQLite validiert die lesbare WAL-Sicht,
Sourcescope und Schema; danach erfolgt der kontrollierte Enginecheckpoint.
Header-/Framegrößen werden plausibilisiert. SQLite muss beim PASSIVE-Checkpoint
**alle physischen Frames** zuordnen und vollständig checkpointen können; sonst
bleibt ein dauerhafter `.content-recovery-required`-Fence. Es gibt keinen eigenen
WAL-Replay, keine manuelle WAL-Löschung und keinen automatischen DBimport.
`integrity_check`, FK-/Modell-/Blobprüfung und TRUNCATE-Checkpoint folgen vor
Aufhebung des Fences. Defekte Blobbezüge werden dabei persistent quarantänisiert.

Ungültige Header, unklare/uncommittete/überallokierte WAL-Enden und Hot-Rollback-
Journals bleiben **gesperrt**, auch wenn eine spätere SQLite-Version Teile davon
vermutlich lesen könnte. Fehlgeschlagene Recoveryversuche/Fences werden nicht
automatisch zurückgesetzt. Vorgehen: Diagnose und Restore eines nachweislich
gültigen Snapshots in einen **neuen** Root; kein manuelles Löschen des Fences.
Insbesondere wird keine umfassende Reparatur beliebiger SQLite-Korruption behauptet.

Normales Öffnen verändert kein WAL und bleibt bei nichtleerem WAL/Journal/Fence
`Unavailable`. `immutable=1` bleibt nur unter DB-Sharedlock, gechecktem Null-WAL/
Null-Journal und Maintenance-Sharedlock zulässig. Writer halten den DB-Exklusivlock
bis Commit/Rollback plus Checkpoint; daher ignorieren Reader keine Writeahead-
Daten. Nach Restore wird WAL ausdrücklich reaktiviert und checkpointed.

## Integrität und Quarantäne

`verify_integrity` prüft unter exklusiver Maintenance die vollständige bekannte
SQL-/Artefaktclosure: SQLiteintegrität/FKs, strenge Modelle, Source-/ACLidentität,
Parser-/Schema-/Slot-/Versionsbeziehungen, Rawmanifest/FKs, SQLblöcke/-Texthashes
und Locatorprojektionen gegen die unveränderliche Projektion. Alle registrierten
Blobs werden auf Größe/SHA und private reguläre Inodes geprüft; Runmanifeste,
Intents und eigenes Staging werden zugeordnet. Unbekanntes/unsicheres Staging
wird gemeldet, nicht übernommen oder gelöscht.

Für beschädigte Bytes werden `artifacts.state`, betroffene SourceVersionen und
alle davon abhängigen/den Blob nutzenden Parsed-Versionen persistent quarantänisiert.
Das berücksichtigt geteilte Raw-/Bild-/Receipt-/Projektionshashes. Andere Versionen
bleiben lesbar. Byte-Restore allein hebt Quarantäne niemals auf. Eine automatische
Wiederfreigabe-/In-place-Reparatur-API ist **nicht implementiert**. Snapshot/Restore
erhält die Flags. Sind Metadaten widersprüchlich und die Schadensclosure unklar,
bleibt der gesamte Store hinter einem dauerhaften Fence; keine erratene Teilfreigabe.

`incidents/<uuid>.json` enthält feste Fehlercodes, betroffene Hashes/Version-/Run-IDs,
keine kompletten Texte, Tokens oder Hostpfade. Incidentdatei wird vor dem
Quarantänecommit unveränderlich synchronisiert; ein DBfehler kann daher einen
Incident ohne abgeschlossenes Statusupdate hinterlassen. Reads reparieren nichts.

## Snapshotformat und Restore

`backup(store, destination, *, actor, snapshot_id=None)` verlangt einen neuen bzw.
leeren privaten, separaten Zielroot. Exklusive Maintenance schließt Writer aus;
aktive Imports/Reader führen nonblocking zu `Busy`. SQLite-Backup-API sichert die
bekannte DB mit FULL-Synchronisation in eine eigenständige DELETE-Journal-Datei.
Kopiert werden ausschließlich katalogisierte Blobs, Staging der bekannten Runs
und die dedizierten Incidentdateien. Keine fremden Rootdateien, Credentials,
Runtime-/Kernel-Locks oder benachbarte Jobdatenbanken.

`manifest.json` wird **zuletzt** exklusiv per atomarer Linkpublikation veröffentlicht.
Ein abgebrochener Snapshot hat kein gültiges Manifest und ist kein Backup.
Format `SnapshotManifest`: `snapshot` plus SHA256 von dessen kanonischem JSON.
Snapshot: Schema 1, kind `content-snapshot-v1`, UUID-Snapshot-ID, DBidentität
`content-v1`/Version 1, Storepurpose, Publikations-/Collectionrevision und sortierte
Dateiliste mit erlaubtem Relativpfad, SHA256 und Größe. Kein Selbsthashkreis;
keine Signatur/Authentizitätsbehauptung gegen einen Angreifer mit gleicher UID.
Leere Runtimeverzeichnisse sind Struktur, keine Datenartefakte.

Restore verifiziert zuerst Manifest/SHA, **exakte** Dateiinventarliste und sämtliche
Bytes, DBschema/FKs/Integrität, Source-/ACLscope und Referenzclosure. Erst danach
wird ein neuer leerer Contentroot angelegt. Ein Restorefence sperrt ihn bis alle
Dateien erneut kopiert/geprüft, private Runlocks neu angelegt, WAL eingerichtet
und die Datenbank erneut validiert wurden. Ein unterbrochener Restore bleibt
unbenutzbar; kein normales Öffnen kann teilweise kopierte Versionen freigeben.
Nichtterminale Runs und Quarantäne-/Tombstone-/ACLzustände bleiben unverändert;
keine automatische Fortsetzung, Sourcepfadumschreibung oder Umschaltung.

Fehlende/defekte referenzierte Bytes verhindern ein erfolgreiches Backup, auch
wenn sie bereits quarantänisiert sind. Ein Quarantänestatus mit wieder vorhandenen
korrekten Bytes wird dagegen unverändert gesichert. Ungeprüfte Teilbytes eines
`preparing` Runs können als Stagingbeleg gesichert werden, werden aber dadurch
nicht zu gültigen Raw-/Parsed-Daten.

## Konkrete Ressourcenlimits

| Grenze | Verhalten |
| --- | --- |
| Artefakt/JSON 64 MiB, JSONtiefe 64, Blöcke 50.000, Bilder 500 | A/B-Grenzen unverändert; Intents ebenfalls höchstens 64 MiB |
| 32 aktive `preparing`/`prepared`/`blocked` Runs | Neue Reservierung `Busy`; keine automatische Slotübernahme |
| 512 MiB Staging, 20.000 Stagingeinträge | Serialisierter Directorylock vor Stage/Gateverifikation, sonst `Busy`/`Unavailable` |
| 20.000 katalogisierte Artefakte/Sources bzw. Incidentdateien | Neue Aufnahme gesperrt; kein automatisches Löschen |
| 2 GiB katalogisierte Blobbytes / Snapshotgesamtgröße | Kapazitätsprüfung; verwaiste installierte Bytes werden nicht automatisch gesammelt |
| 200.000 Metadatenzeilen, 1.000 Grants je Source | Neue Reservierung/Publikation begrenzt; Integritäts-/Snapshotprüfungen darüber gesperrt |
| 1 MiB freier Sicherheitsraum plus erwartete Bytes | Vor Stage/Incident/Snapshot/Restore prüfen; echte ENOSPC-Fehler ebenfalls kontrolliert |
| Snapshotmanifest 8 MiB, SQLite-Backupdeadline 15 s | Kein unbegrenztes SQLite-Backup-Retry; abgebrochene Snapshots nicht freigegeben |
| flock nonblocking, SQLitebusy höchstens 2 s | Kontrollierte Busy/Unavailable; kein unendliches Warten oder Hintergrundretry |

Limits können bewusst früher als das Dateisystem limitieren. Das ist keine
Durchsatz-/Lastfreigabe. Die feste Diskreserve ersetzt keine Betriebskapazitäts-
planung; Datei-/SQLatomizität bleibt getrennt. Keine GC/Retention in diesem Paket.

## C22/C26-Übergabe

C22s bestehende Operationsfence/Backupmodule bleiben unverändert. C26-04 muss alle
Job- und Contentwriter stoppen, dann zuerst C22 Operationsfence, anschließend
Content Maintenance exklusiv nehmen. Beide geprüften Snapshots erhalten dieselbe
explizite Snapshot-ID; ein äußeres Verbundmanifest wird erst nach Erfolg beider
Teilmanifeste veröffentlicht. Writer erst nach vollständig validiertem Snapshot
bzw. kontrollierter Freigabe wieder starten. Kein umgekehrter Lockaufruf aus Content
in C22. Der aktuelle Contentbackup-Einstieg erwirbt seine Maintenance selbst;
ein Verbundwrapper hält außen nur die C22-Fence und ruft ihn dann auf, er darf
keinen zweiten Content-Exklusivlock verschachteln. Neue Restore-Roots getrennt
prüfen und erst mit C26-Freigabe als Gesamtsystem aktivieren. Keine Migration von
jobs.sqlite3 und keine automatische C16-/C18-/C20-Anbindung.

C23-03: historischer #72-Pfadbestand weiterhin D06-gesperrt; Wiederholungs-/
Parallelitätsabnahme und tatsächlicher Korpus müssen diesen begrenzten Vertrag
berücksichtigen. C23-04: autorisierte paginierte/redigierte Reads separat, keine
HTTPfreigabe der hier internen Source-/Run-/Bytebelege. C26-04: Verbundsnapshot,
Kapazitäts-/Dateisystem-/Restoreabnahme auf ausdrücklich freigegebenem Host;
kein produktiver Go-live durch diesen PR.

## Tatsächliche Abnahme

Umgebung: Python **3.12.12**, Pydantic **2.13.5**, SQLite **3.50.4**,
BeautifulSoup **4.15.0**, vorhandenes System-Pytest **7.2.1**, Ruff **0.16.0**.
Projektvenv/Pytest 9 und PyMuPDF waren nicht lokal nutzbar; vorhandene Umgebung
`ai-job-search/.venv` plus System-Pytest verwendet. Keine Downloads/Installationen.
Pytest-7-AST-Warnungen unter Python 3.12 sind keine übersprungenen Prüfungen.

| Abschließender Lauf | Pass / Fail / Skip | Bezug |
| --- | --- | --- |
| Gemeinsame C-/A-/B-Suite | **171 / 0 / 0**, 223,50 s | 51 damalige neue Betriebsfälle plus alle 120 A/B-Fälle |
| Nach abschließender Zuordnung beschädigter Recoverybelege: Integrität + Backup | **26 / 0 / 0**, 67,17 s | 16 Integritätsfälle inklusive zwei zusätzlicher Intentfälle, zehn Backupfälle; Überschneidung mit gemeinsamer Suite, **nicht addieren** |
| Material-/Discovery-/Lecture-/Executor-/Transcript-/C16-/C22-Regression | **221 / 8 / 2**, 99,74 s | C16 36 passed, C22 24 passed; keine Gesamtrepositorysuite |
| Unverändertes Masterarchiv: Transcriptimport + HTMLsemantik | **48 / 8 / 1**, 4,88 s | Genau dieselben acht Fehler, keine neuen als Altfehler klassifiziert |
| Ruff Check / Format Check / diff check | **erfolgreich** | 25 Pythondateien, 19 lokale Dokumentationsziele |

Nach dem gemeinsamen Lauf wurde ausschließlich die Quarantäneattribution für
Recovery-Intentblobs ergänzt und die explizite Integritätsinspektion bereits
quarantänisierter, byteidentisch zurückgebrachter Belege korrigiert. Recovery
selbst verlangt weiterhin einen verfügbaren Katalogref. Der betroffene ganze
Integritäts-/Backupbereich wurde danach erneut geprüft; die beiden zusätzlichen
Fälle wurden nicht als Teil eines ausgeführten 173er-Gesamtlaufs ausgegeben.

Die acht bestehenden Fehler: sechs TXT-Importfälle (`start/end=None` gegenüber
float) aus `test_official_transcript_import.py` und beide Wrapperfälle von
`test_cs50_material_html_semantics.py::test_code_preserves_exact_whitespace_quotes_entities_and_unicode`
(`héllo` → `h√©llo`). Baseline ist ein unveränderter Gitarchiv-Snapshot von
`9a1325485f1b2acc7df177b8a137f771190eca97`. Optionale echte HTML-/SRT-Bestände fehlen:
zwei Regression-Skips, ein HTML-Skip im kleineren Baselinelauf. PyMuPDF-Parser-
prüfungen wurden **nicht ausgeführt**, nicht als zusätzliche Skips gezählt.
Keine vollständige grüne Regression behauptet, keine TXT-/HTMLparseränderung.

Gemeinsames tatsächliches Pytest-Präfix (pro Lauf Logumleitung außerhalb des Repos):

```sh
PYTHONPATH=/usr/lib/python3/dist-packages PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /home/robfra/0_Portfolio_Projekte/ai-job-search/.venv/bin/python -m pytest
```

Gemeinsame Abnahme mit diesem Präfix:

```sh
-q --disable-warnings \
 tests/test_content_store_recovery.py tests/test_content_store_concurrency.py \
 tests/test_content_store_integrity.py tests/test_content_store_backup.py \
 tests/test_content_store_limits.py tests/test_content_store_models.py \
 tests/test_content_store_artifacts.py tests/test_content_store_store.py \
 tests/test_content_store_adapters.py --basetemp=/tmp/c2302c-release
```

Abschließende gezielte Nachprüfung:
`tests/test_content_store_integrity.py tests/test_content_store_backup.py
 -q --disable-warnings --basetemp=/tmp/c2302c-quarantine-release`.

Regression:
`tests/test_cs50_material_contracts.py tests/test_cs50_material_html.py
 tests/test_cs50_material_html_semantics.py tests/test_cs50_material_code.py
 tests/test_cs50_material_mapping.py tests/test_cs50_discovery.py
 tests/test_cs50_lecture_adapter.py tests/test_cs50_executor.py
 tests/test_official_transcript_import.py tests/test_job_control.py
 tests/test_deployment_operations.py -q --disable-warnings
 --basetemp=/tmp/c2302c-regression`.

Baseline: `git archive HEAD src tests docs/course_sources scripts deployment
 pyproject.toml uv.lock` auf unverändertem Ausgangsbranch in eigenen
`/tmp/c2302c-baseline`-Root; dort dieselben Optionen für
`tests/test_official_transcript_import.py tests/test_cs50_material_html_semantics.py`
mit `--basetemp=/tmp/c2302c-baseline-tests`.

Ruff `check` und `format --check` jeweils für `src/content_store`,
`tests/content_operations_support.py`, `tests/content_store_process.py`,
`tests/test_content_store_*.py`, `tests/content_adapter_support.py` und
`tests/content_store_support.py`; anschließend `git diff --check`.

| Pflichtmatrix | Tatsächlicher Nachweis |
| --- | --- |
| T01 | Separate Prozesse wirklich per SIGKILL beendet: partielles Staging, prepared Raw/Binding/Parsed, nach Blobinstallation, vor SQLarbeit, nach Metadateninsert unmittelbar vor Commit, nach erfolgreichem Commit/Responseverlust; vollständige Belege resumierbar, unvollständige bleiben blockiert, explizites Reject, ACLänderung, SRT ohne Reparse |
| T02 | Echtes von SQLite erzeugtes WAL nach beendetem Prozess, normales Öffnen gesperrt und WALbytes unverändert, explizite Engine-Recovery, manipulierte Header/Framechecksums bleiben gesperrt, Scope-/Aktivitätschecks |
| T03 | Echte überlappende Prozesse: gleicher/verschiedener Slot, gleiche/konträre Keys, Reader mit bestehender Version während prepared Import, Backup-/Recovery-Busy, keine zwei Gewinner |
| T04 | Fehlende/manipulierte Raw-, Payload-, Projektions-, Receipt-, Bild- und Intentblobs, gemeinsame Rawversionen, Persistenz nach Wiederöffnung, keine Freigabe durch Dateiersatz; Metadatenwiderspruch/Fence und unowned Staging |
| T05 | HTML + SRT einschließlich ACLgrant, Originalraw/JSON/Receipt nach Restore in separatem Prozess, Quarantäne/Tombstone, prepared-Belege erhalten und anschließend ausdrücklich resumierbar; defektes Manifest/DB/Blob, Extras/Symlinks, No-Overwrite, Backupabbruch und Restorefence |
| T06 | Echte ENOSPC-Fehler injiziert, Staging-/Aktivrun-/Backupgrößenlimits, große Deklaration, DB-/Maintenance-Lock nonblocking, unbekanntes Schema, nicht berechtigte Actors, keine Sourcepfadfallbacks |

Entwicklungsläufe enthielten korrigierte neue Defekte (u. a. Row-Vergleich bei
integrity_check, Testimportbindung, Metadatenschadensinjektion, leeres
Snapshot-Staginglayout und Quarantäneinspektion). Ein Zwischenlauf hatte 167 pass/
2 fail, eine frühere gezielte Prüfung 21 pass/4 fail; diese sind **keine**
Baseline-/Abnahmeresultate. Die korrigierten Fälle sind in den oben genannten
abschließenden Läufen nachgewiesen. Vollständige lokale Logs bleiben außerhalb
des Repositories erhalten; Testroots/Gitarchiv und erzeugte Caches werden nach
Abnahme entfernt. Der C-Worktree bleibt für den offenen PR bestehen.
