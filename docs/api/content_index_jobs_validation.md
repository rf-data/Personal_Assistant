# DEV-01B: tatsächliche synthetische Validierung

Basis `79d800caf3270de07296b49dc4585c1e01ceb085` (Master, DEV-01A/#124
integriert), 19.10.2026. Bezug: [Issue #115](https://github.com/rf-data/Personal_Assistant/issues/115).
[API/Config/Retryvertrag](content_index_jobs_v1.md),
[JSONschemas](examples/content_index_jobs_v1.schema.json),
[tatsächlicher synthetischer Ergebnisbeleg](examples/content_index_jobs_v1.synthetic.json).
Das Beispiel stammt aus dem erfolgreichen neuen Queue-/Aktivierungstest, enthält
keine privaten Pfade oder Schlüssel und ist keine fachliche Realabnahme.

## Implementierter Umfang

C16 erhält den opt-in Prozess `content_index_build`, einen hashgebundenen
Operator-Katalog und autorisierte Indexstatusrouten. Bestehende Queue,
Preview/Idempotenz/Worker/Guardian, FTS5-Dateiformate und Aktivierung werden
wiederverwendet. Keine neue Queue, Parser, Installation, Migration, automatische
Indizierung oder reale Datenübernahme. Zusätzlich nachgewiesene Bibliothekslücke:
Ownership bereits aktiver Quellen muss vor deren Ersetzung geprüft werden.
Diese Prüfung gilt jetzt vor Build und atomarer Aktivierung.

`index_models.py`, `index_jobs.py`, `index_http.py` ergänzen die bestehenden
C16-Module; `content_index.py` erhält eine kontrollierte Build-ID und die
Ownershipprüfung. Die gespeicherten C16-/Workflow-Schemas enthalten die additive
Artifactart `index_build` und die opt-in Konfiguration. Der ausgeschaltete
Defaultregistry bleibt unverändert. Keine Assertion wurde für die Snapshots entfernt.

## Neue Nachweise

Vorhandene Projektumgebung: Python 3.12.12, Pydantic 2.13.4, SQLite 3.50.4,
Pytest 9.1.1, Ruff 0.16.0. Keine Installation/Downloads. Präfix:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  /home/robfra/0_Portfolio_Projekte/gmp_compliance/.venv/bin/python -m pytest
```

`-q -p no:cacheprovider tests/test_content_index_jobs.py
--basetemp=/tmp/dev01b-release`: **18 passed, 0 failed, 0 skipped, 83,57 s**.
Echte private temporäre Stores, verifiziertes synthetisches B-Bundle, tatsächliche
C16-Queue und Worker, SQLite FTS5 sowie HTTP-Application. Netzwerkconnects und
DNS werden in diesen Tests ausdrücklich abgewiesen.

- Gleichzeitige identische Requestkeys haben einen Gewinner; widersprüchlicher
  Intent bleibt Conflict. Verschiedene Keys sind getrennte serialisierte Jobs.
- Scope-/Ownershipprüfung vor Annahme/Dispatch, Sourcewiderruf vor/nach Aktivierung,
  fremde aktive Sources, Quarantäne/Tombstones und falsche Versionbelege.
- Getrennte Prozesse per SIGKILL **vor und nach** atomarer Aktivierung beendet.
  Ein neuer ausdrücklich bestätigter Retry baut neu oder quittiert die exakt
  aktive alte Generation; keine Stagingadoption oder automatische Wiederholung.
- Tatsächlicher Guardian-Timeout und injiziertes ENOSPC, kontrollierte terminale
  Zustände, persistierter Status nach erneutem Öffnen. Abbruch ist kein Rollback.
- Beschädigte FTSdatei/Receipt, unveränderte alte Build-IDs, Versions-/Antwortlimits,
  gehaltene Contentguards für Status/Inputs/Jobdetails/History.

Entwicklungsläufe: zunächst 8 pass/2 fail (HTTP403 statt erwarteter503 bei
Quarantäne), danach 13 pass/5 fail (vier fehlende Testimporte und einmal ein
C16-Guardian-SQLitefehler mit korrekt fail-closed Quarantäne bei parallelen Läufen).
Der einzelne Fall bestand danach isoliert; sechs Fehler-/Ownershipfälle zusammen
bestanden. Der abschließende **gesamte 18er-Lauf** oben war seriell erfolgreich.
Keine Schutzaussage wird aus den fehlgeschlagenen Entwicklungsläufen abgeleitet.

## Bestehende Verträge

Erster gemeinsamer Regressionstest: **257 passed / 3 failed / 0 skipped**, 402,21 s,
260 Fälle aus Search HTTP, FTS5, C16, Executor, Workflow HTTP, PDFjob, Reviewstore und
Content Read. Die drei Fehler waren Snapshotdifferenzen: eine unnötige zusätzliche
Default-disabled-Prozessangabe und die additive Artifactart in eingebetteten
Workflow-Schemas. Defaultregistry korrigiert, vorhandene versionierte Schemas auf
die tatsächlichen Modelle aktualisiert; Testassertions unverändert.

Nachprüfung mit obigem Präfix und `-q -p no:cacheprovider`:

```text
tests/test_content_search_http.py
tests/test_job_control.py::test_transport_contract_snapshot
tests/test_pdf_job_control.py::test_opt_in_paths_versions_scope_and_revocation
tests/test_workflow_http.py::test_versioned_schema_snapshots_and_original_c16_models
--basetemp=/tmp/dev01b-http-snapshots
```

**53 passed / 0 failed / 0 skipped**, 200,51 s. Für den vorhandenen echten
Loopback-HTTPtest wurde die lokale Netzwerk-Sandbox aufgehoben; kein externer
Dienst wird verwendet. Diese 53 überschneiden den 260er-Lauf, nicht addieren.
Weitere abschließende Ergebnisse stehen im Nachtrag unten.

## Grenzen und Integration

Die unverändert vollständige Liveprüfung kostet I/O und Zeit: 32 Sources,
1.000 Matches, 128 MiB Query-I/O, Query-/Deliveryfristen sowie Workerlimits bleiben
maßgeblich. Kein Durchsatznachweis, keine produktive Betriebsfreigabe. Ein
unbestätigt beendeter Guardian kann C16 quarantänisieren; kein automatisches
Entsperren. Andere private Indexroots brauchen getrennte ausdrückliche Freigaben.

DEV-01C verwendet die gemergten A-Verträge und prüft die optionale B-Capability.
Die neue B-Schnittstelle ist vor Merge dieses PRs **Entwicklungsstand**, kein
bereits integrierter Defaultbranchvertrag. UI-/Backend-PR getrennt prüfen, Backend
zuerst integrieren. Keine PRs automatisch mergen; keine offenen Realabnahmen
schließen. Branch/Worktree bleiben bis tatsächlicher Integration erhalten.

## Nachtrag: zweiter Gesamtlauf und gezielte Nachprüfung

Eine zweite, parallel zur UI-Prüfung innerhalb der Socket-Sandbox gestartete
260er-Suite endete mit **254 passed / 6 failed / 0 skipped**, 719,10 s.
Dies ist ausdrücklich kein grüner Gesamtlauf. Zwei Defaultregistry-Snapshots
benutzten noch das **vor der Korrektur bereits importierte** Modul; die nachfolgend
frisch gestarteten Snapshotprüfungen im erfolgreichen 53er-Lauf bestätigen die
Korrektur. Der Loopback-Test scheiterte an `socket()`/Sandbox-EPERM; derselbe ganze
Search-HTTPbereich besteht im 53er-Lauf außerhalb dieser Socketbeschränkung.

Drei native PDF-Lifecyclefälle scheiterten beim Erreichen/Lesen ihres eigenen
kurzlebigen Testmarkers (`worker-timeout` in Workflow HTTP; `worker-timeout` und
`job-timeout` in PDFjob). Ein Marker existierte bereits, enthielt beim Lesen aber
noch kein vollständiges JSON. Keine Schutzfristen oder Assertions wurden dafür
verändert. Diese Fälle bestanden im ersten Gesamtlauf; sie werden vor Abschluss
nochmals separat seriell geprüft. Kein neuer Fehler wird ohne Nachweis als
historischer Baselinefehler bezeichnet. Die folgenden gezielten Ergebnisse
überlappen alle vorherigen Läufe.

Serielle Nachprüfung: `tests/test_content_index_jobs.py` plus die drei oben
benannten PDF-Nodes, `--basetemp=/tmp/dev01b-lifecycle-final`:
**20 passed / 1 failed / 0 skipped**, 113,03 s. Alle 18 Indexjobfälle und beide
Worker-Timeoutfälle erfolgreich. Einzig der bestehende native PDF-`job-timeout`
erreicht seinen Marker nicht: Der Guardian beendet den Adapter nach den vom
Testprobe vorgegebenen 1,5 s ordnungsgemäß mit `failed/timeout/-SIGTERM`.

Derselbe einzelne unveränderte Node auf einem **unveränderten Gitarchiv von
Master `79d800c`**, gleicher Interpreter und gleiche Optionen, eigener temporärer
Root, `--basetemp=/tmp/dev01b-master-timeout`: **0 passed / 1 failed**, 13,57 s,
identischer `Bounded PDF lifecycle condition not reached` bei `marker.exists`.
Archivumfang: `src tests scripts docs/course_sources docs/job_control
 docs/workflows pyproject.toml`. Primärcheckout nicht verändert. Damit ist dieser
verbleibende Test-/Umgebungsbefund gegen den tatsächlichen unveränderten Master
nachgewiesen; keine Behauptung einer vollständig grünen PDF-/Repositorysuite.
Weder Produktionslimits noch die alten 1,5-s-Probe/Assertions wurden abgeschwächt.

Bei abschließender Prüfung wurde zusätzlich verhindert, dass ein verworfener
Live-Generationsbeleg im Zustand blocked noch eine vermeintlich verifizierte
Generation ausgibt. Ein weiterer Negativtest bindet die Antwort explizit an
`index_generation=null`; bestehende Korruptions-/Guardtests werden mitgeprüft.

Abschließende Statusprüfung: drei Nodes
`test_rejected_live_generation_never_reports_verified_generation`,
`test_corrupt_partition_is_blocked_and_receipt_hashes_checked`,
`test_status_and_generic_job_metadata_hold_live_authorization_guard` aus
`tests/test_content_index_jobs.py`, `--basetemp=/tmp/dev01b-status-final`:
**3 passed / 0 failed / 0 skipped**, 15,12 s. Ein neuer Fall plus zwei bestehende,
keine Addition zu einem angeblich ausgeführten 19er-Gesamtlauf. Insgesamt wurden
alle 19 neuen Indexjobfälle in den beschriebenen Läufen erfolgreich nachgewiesen.

Ruff Check und Format Check für die 14 geänderten/neuen Pythondateien erfolgreich,
`git diff --check` erfolgreich. Alle fünf veröffentlichten Schemas gegen die
aktuellen Pydanticmodelle und den tatsächlichen synthetischen Receipt validiert;
lokale Dokumentationslinks geprüft. Testlogs bleiben außerhalb des Repositories.
Ein eigener synthetischer Masterarchiv-Testroot ist Diagnosematerial, keine
Änderung eines Bestandsworktrees oder einer historischen MAINT-Ref.
