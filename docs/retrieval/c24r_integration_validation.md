# C24-R: lokale Integrationsvalidierung

Basis `4c057ae33d41ba98e227879cc8a51283338e4a0b`, ausschließlich synthetische
Fixtures und neue private temporäre Testroots. Kein Produktivsystem, kein
Realmaterial, keine externen Modelle/Dienste. C26 HOLD.

## Nachweisgrenzen

| Nachweis | Tatsächlicher Umfang | Ergebnis |
|---|---|---|
| Search HTTP Application | echte B-Bundles, ContentStore/FTS5 und Gatewayrequest/Reply | 49 bestanden, ein Socketfall blockiert |
| Kontrollierte Indexjobs | echte Queue, Worker/Guardian, Indexbuild, Restart/Retry/Fehler | 19 bestanden |
| Gemeinsame Handlerkette | tatsächlicher HTTP-Handler mit Byte-Streams, echter Worker/FTS5 | bestanden |
| Cancel vor Dispatch und während Indexbuild | aktuelle Rechte, unveränderter Guardian, API-Wiederöffnung, alter Pointer | beide bestanden |
| Tatsächliche Loopbackverbindung | vorhandener Search-Prozessrestarttest und neuer kompletter Job→Search-Test | beide mit EPERM gescheitert, kein Erfolg behauptet |
| Loviscach | Schema/Provenienz/CSV ausschließlich synthetisch; leerer Realpool | reale Qualität nicht evaluierbar |

`test_handler_job_to_search_revocation_and_reopen` führt die gesamte gemeinsame
Kette aus: synthetisches Original → verifiziertes B-Bundle → Source-/Parsedversion →
Katalogpreview → autorisierter C16-Job → echter Worker → atomare Generation →
Search-HTTP-Handler → Source-/Parsed-ID und Generation → Live-ACLwiderruf →
leere Viewersuche → identischer Jobrequest ohne zweite Ausführung →
Wiederöffnung → identische Ownergeneration. Originalinventar bleibt unverändert.
Das ist explizit **kein Socket-Roundtrip**. `test_actual_loopback_job_to_search`
führt dieselbe Kette über den vorhandenen HTTPServer aus, kann hier aber bereits
vor dem Start keinen Socket erstellen. Der separate Search-Test enthält einen
vollständigen API-Prozessrestart über tatsächliches HTTP für erlaubte Umgebungen.

## Profil und Wiederholung

Python 3.12.12, SQLite 3.50.4, Pydantic 2.13.4, Pytest 9.1.1, Ruff 0.16.3.
Die übliche historische Projektvenv ist hier nicht vorhanden. Eine isolierte
Venv unter einem neuen /tmp-Root wurde mit dem vorhandenen 3.12-Interpreter
angelegt. Bereits vorhandene uv-Cachepakete wurden über eine explizite .pth-Datei
eingebunden; keine Installation/Downloads, keine Veränderung des schreibgeschützten
uv-Caches oder anderer Arbeitsbäume. PyMuPDF 2.0 aus vorhandenem Cache wurde
nach einem dokumentierten Collectionfehler ergänzt. Die .pth-Auswahl umfasst die
vorhandenen Basis-/Testdependencies; sie ist keine neue Lockauflösung.

In einer passend provisionierten Umgebung reproduzierbar, ohne Sync/Netz:

```sh
export UV_PROJECT_ENVIRONMENT="$C24R_ENV"
export UV_CACHE_DIR=/tmp/new-c24r-uv-cache
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1
export CS50_TEST_PROFILE=offline
uv run --offline --frozen --no-sync python -m pytest -q -p no:cacheprovider \
  tests/test_content_search_http.py tests/test_content_index_jobs.py \
  tests/test_c24r_integration.py tests/test_gold_candidates.py \
  --basetemp=/tmp/new-c24r-focused-tests
uv run --offline --frozen --no-sync python -m src.tools_evaluation.gold_candidates \
  --dataset docs/evaluation/loviscach/candidates.v1.json
```

Vorhandene .pth-Umgebung direkt oder provisionierte Venv verwenden; rootweites
`uv sync` und optionale SDKdownloads wurden nicht ausgeführt. Lokales HTTP ist
für die beiden Sockettests erforderlich; EPERM ist kein Skip/Pass. Tests oder
Assertionen/Sicherheitslimits wurden dafür nicht geändert.

## Tatsächliche Läufe und Diagnosen

- R1: **49 passed, 1 failed**, 55,82 s. Einziger Fehler:
  `test_real_local_http_server_and_process_restart`, bereits `socket.socket()`:
  `PermissionError: [Errno 1] Operation not permitted`.
- R2: **19 passed**, 82,11 s. Echte Prozess-/SIGKILL-/Timeoutproben.
- Neue Integration, erster Lauf: **1 passed, 3 failed**, 11,42 s.
  Zwei eigene Testaufruffehler: nicht existente Methode set_grants statt
  set_source_grants und 403 erwartet ohne vorherige Sourcegrant (korrekt 404).
  Tatsächlichen Storevertrag verwendet und für die Rollenprüfung vorher explizit
  Readgrant gesetzt. Dritter Fehler: Loopback-Socket EPERM.
- Zwischenprüfung: **2 passed, 1 failed, 1 deselected**, 9,98 s; die Grantkorrektur
  war zunächst nicht im betreffenden Testblock eingesetzt. Gezielt korrigiert.
- Abschließende drei Handler-/Cancelfälle: **3 passed, 1 deselected**, 9,80 s.
- Kandidatenentwicklung: **28 passed**, 1,15 s. Nach zusätzlichem
  Zeilen-/Konfigurationscheck **30 passed**, 1,13 s; abschließende Exportnachprüfung
  wird unten festgehalten. Überlappende Läufe nicht addieren.
- Baselinearchiv des unveränderten `4c057ae`: bestehender
  `test_content_http.py::test_http_e2e_after_restart_and_legacy_contract`
  ergibt **1 error**, 2,05 s, identisches Socket-EPERM im Fixture. Fremde Worktrees
  wurden nicht verwendet/verändert. Ein erster Archivierungsaufruf aus /tmp
  scheiterte mangels Git-CWD; anschließend aus dem richtigen Worktree wiederholt.
- Erster gemeinsamer Lauf: **Collection abgebrochen, 2 errors, 2 deselected**,
  3,52 s, fehlendes pymupdf bei Workflow-HTTP/PDF-Jobtests. Keine Fälle bestanden.
  Vorhandenes Cachepaket eingebunden; keine Dependencies heruntergeladen.

Weitere gemeinsame Ergebnisse, Lint-/Schema- und Patchprüfungen folgen im
abschließenden Ergebnisabschnitt; historische DEV-Reports sind keine aktuellen
C24-R-Testergebnisse.

Profilgrenze: `uv run --offline --frozen --no-sync` wurde tatsächlich erfolgreich
für CLI und Kandidatentests ausgeführt. `--no-sync` prüft keine vollständige
Lockinstallation. Der vorhandene Cache weicht bei Pluggy (1.7.0 statt gelocktem
1.6.0) und optionalem PyMuPDF (2.0 statt 1.28.2) vom Rootlock ab. Die übrigen
verwendeten Cachepakete stimmen mit ihren vorhandenen Rootlockeinträgen überein.
Kein vollständig neu synchronisierter Lockprofilnachweis wird behauptet; dafür
muss eine passend provisionierte Offlineumgebung bereitstehen. Kein Lock geändert.

## Abschließende Zusatznachweise

- Kandidaten nach finalem CSV-/Konfigurations-/Zeilencheck plus laufender
  Indexcancel mit atomarer Testmarkierung: **31 passed**, 10,17 s. Tatsächlicher
  Offline-uv-Aufruf, frischer basetemp; 30 Kandidatenvalidatorfälle und ein
  Prozessfall. Keine echte Kandidatenzahl daraus ableiten.
- C23-Materialevaluation und bestehende Formelevaluation:
  **143 passed, 17 skipped, 1 deselected**, 15,16 s. Die optionalen SymPyfälle
  bleiben mangels SymPy übersprungen. `test_versioned_inventory_has_no_confirmed_real_gold`
  wurde bewusst abgewählt, um keine historischen Realinventarwurzeln zu öffnen.
  Alle übrigen Fälle nutzen synthetische/ausdrücklich versionierte Testdaten.
- Exakter Vergleich der drei Search-DTO-Schemas, der Index-DTO-Schemas und des
  Kandidatenschemas gegen die tatsächlichen Pydanticmodelle: erfolgreich.
- Ruff check und format --check für alle **23** geänderten/neuen Pythondateien
  erfolgreich; git diff --check erfolgreich. Neue Review-CSV verwendet LF, damit
  auch ihr vollständiger Lieferpatch frei von Whitespacefehlern bleibt.
- Vollpatch und drei logische Teilpatches: unabhängige Archive von `4c057ae`,
  Vorwärtscheck/-anwendung, sämtliche finalen Dateihashes, Rückwärtscheck/-anwendung
  und Wiederherstellung der Basis erfolgreich. Reversecheck des aktuellen
  C24-R-Arbeitsbaums ebenfalls erfolgreich. Nach Abschluss der Dokumentation wird
  das Paket mit aktualisiertem Manifest erneut erzeugt und geprüft.

Gemeinsamer Regressionsumfang (direkt derselbe Interpreter, dieselben Offline-
Variablen und -q/-p no:cacheprovider, frischer temporärer basetemp):

```text
tests/test_content_store_models.py tests/test_content_store_store.py
tests/test_content_store_adapters.py tests/test_content_read_contracts.py
tests/test_content_http.py tests/test_content_index_projection.py
tests/test_content_fts.py tests/test_content_vectors.py
tests/test_content_retrieval_evaluation.py tests/test_content_retrieval_integration.py
tests/test_evaluation_store.py tests/test_review_fts_pilot.py
tests/test_content_search_http.py tests/test_content_index_jobs.py
tests/test_c24r_integration.py tests/test_gold_candidates.py
tests/test_job_control.py tests/test_job_executor.py tests/test_cs50_workflows.py
tests/test_workflow_http.py tests/test_pdf_job_control.py
-k 'not test_real_local_http_server_and_process_restart and not test_actual_loopback_job_to_search'
```

Dieser Lauf sammelte vor der letzten zusätzlichen Konfigurationsprüfung 635 Fälle;
die finale separate 31er-Prüfung enthält den später ergänzten 30. Kandidatenfall.
Läufe überlappen; Zahlen nicht zu einer vermeintlichen Gesamtsuite addieren.
Nicht ausgeführt: vollständige Repository-/SDKsuite, produktive APIs, Cloud,
Realimport/-indexierung/-evaluation, Downloads, Deployments und menschliche
Goldfreigabe. Keine Timeout-/Securityänderungen zur Testberuhigung.

## Endergebnis der gemeinsamen Regression

**590 passed, 43 errors, 2 deselected, 0 failed, 0 skipped**, 811,30 s
(13:31). Kein grüner Gesamtlauf: alle 43 Errors entstehen beim Setup der
bestehenden `tests/test_content_http.py`-Fälle an exakt demselben Aufruf
`HTTPServer → socket.socket()`, `PermissionError: [Errno 1] Operation not permitted`.
Dieser Fixturefehler wurde auf dem unveränderten Basisarchiv reproduziert.
Die zwei bewusst abgewählten Search-/Joint-Sockettests waren zuvor separat mit
demselben EPERM gescheitert. Sie sind deshalb weder bestanden noch übersprungen.

Die 590 bestandenen Fälle umfassen sämtliche ausgewählten ContentStore-/
Projektions-/FTS5-/Vektor-/Retrieval-/Review-/Searchadapter-/Indexjob-/Handler-/
C16-/Executor-/C18-/Workflow-HTTP-Adapter-/PDF-Lifecyclefälle. Auch die historisch
problematischen nativen PDF-Timeoutfälle bestehen **in diesem Lauf**, ohne
Änderung an ihren Assertions oder Limits. Die Bezeichnung Workflow-HTTP meint
hier den bestehenden Applicationadapter, keinen erfundenen Socketnachweis.

Fehleraudit: R1-EPERM → tatsächlichen Socketaufruf isoliert → identisches
bestehendes Content-HTTP-Fixture auf `4c057ae` geprüft → Umgebung als Ursache
belegt → keine Sandboxumgehung/Timeoutänderung → hier als Blocker belassen.
Die eigenen Testaufruffehler wurden gemäß tatsächlichem Store-/ACLvertrag
korrigiert und gezielt erneut geprüft. Der PyMuPDF-Collectionfehler wurde durch
Einbindung vorhandener Pakete behoben. Keine bekannte Flake als Pass ausgegeben.

Finaler statischer Nachweis: 23 Pythondateien Ruff/Format erfolgreich, neun neue
C24-R-Markdowndokumente ohne fehlendes lokales Linkziel, Schemas modellidentisch,
vollständiger Patch ohne Whitespacefehler. Das abschließende Lieferprotokoll
`/tmp/c24r-delivery/verification.txt` weist Vorwärts-/Rückwärtsanwendung und alle
**47** finalen Dateihashes nach; `artifacts.sha256` schützt die Lieferdateien.
