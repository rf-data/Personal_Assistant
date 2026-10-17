# C21 – Systemabnahme

Stand: 17.10.2026, Europe/Berlin. Backend-Basis `1c0b30771c02d377445fc58059d19ec605c776ed`
(gemergter C20-B-PR 70). UI-Main `ff08d9e109f556ff95075949d5d096640a9d00eb`
(gemergter C20-PR 3). Der vorhandene unveränderte UI-Testcheckout `d7cb6cb`
hat exakt denselben Tree `7d2bb291c2984d63041f71a44107a69cb7079ccc` wie dieser Main.
Der maschinenlesbare Bericht nennt den tatsächlich verwendeten Checkout-Commit.
Eine nachgewiesene Timing-Annahme im externen Cancel-Testtreiber wurde während
der Abnahme separat korrigiert: [UI-PR 4](https://github.com/rf-data/personal-assistant-ui/pull/4),
Commit `7d34bf3cbf474268db6b0418fcaf938fd75c1d71`, Tree
`23c722123d98d0a0b6e6063c4e6b34d5dee88fc9`. Die erfolgreiche endgültige UI-Suite
verwendet diese Korrektur; die eigentliche Produktansicht bleibt unverändert.

## Bestandsaufnahme und tatsächliche Kette

`app_admin.py → admin_ui_package/workflow_view.py → c16_client.py → urllib →
HTTPServer / job_control.http.handler_for → Application → workflows.http →
workflows.service → C16 Store/Queue → Executor → Guardian → adapter_worker →
C18 engine → material_planning → local_material_import → material_parsing →
quality_evaluation → lecture_material_handoff → WorkflowRunReport → Resume`.

Der C10-Handoff erhält NormalizedDocument, Receipt, Course-/Section-/Lecture-IDs
und Originalprovenienz. Referenzprojektionen und alternative Codeansichten sind
keine zusätzlichen Aggregationseinheiten. Er startet keine Knowledge-Extraktion.
C11 bewertet unabhängige Formelpaare, C13 inventarisiert visuelle Referenzen.
Weder C11 noch C13 ist eine automatische semantische Freigabe im Fünfstufenlauf.

| Bestand | Bereits abgedeckt / Überlappung | C21-Ergänzung |
| --- | --- | --- |
| C10 Material Quality / Handoff | technische Fehler, Provenienz, referenzielle Aggregation | Einbindung im echten Queue-/PDF-Lauf; separate reale HTML-Datei |
| C11 Formel-Evaluation | deterministische synthetische Goldfälle, sichere optionale Äquivalenz | Regression; reale mathematische Goldreferenzen bleiben blockiert |
| C13 Visual Inventory | Bilder, SVG-/Vektorkandidaten, Hash-/Bindingkonflikte | lokale echte HTML-Inventur; Referenzstatus ausdrücklich erhalten |
| C16 Queue / Executor | Auth, Limits, Idempotenz, Logs, Artefakte, Metriken | tatsächlicher HTTP-Handler in eigenem Prozess |
| C18 / C19 | Stage-Reuse, Teilresume, physische native PDF-Cleanup- und Restarttests | Wiederverwendung der vorhandenen Fehlerproben; keine neue Lifecycle-Implementierung |
| C20-B Routertests | vollständige Wire-Hüllen, Confirmations, Owner/Course, stale, Replay | echte HTTP-Sockets und physischer Backend-Serverneustart |
| C20-C UI-AppTest | fünf echte Queue-/Parser-Szenarien, Transport durch Router ersetzt | echte urllib-Requests an eigenen Loopbackserver, gleiche kanonische UI |
| C15 | Metrikvertrag, erlaubte Labels, Registry und Rendering | HTTP-Metrikabruf; Beobachtung der tatsächlichen UI-Lifecycle-Teststores |

Diese Überlappungen bleiben gezielte Regressionen. Es werden keine zusätzlichen
Parser, Workflowentscheidungen, Jobdatenbanken oder UI-Ansichten nachgebaut.
Die Registry gibt standardmäßig nur Planning und Quality frei; Workflow und
PDF-Einzelverarbeitung benötigen bestehende explizite Flags. Downloads, LLM-,
Transkriptions-, Knowledge-, Deployment- und beliebige Shellprozesse bleiben gesperrt.

## Abnahmematrix und Nachweisarten

Ergebnisse stehen in [c21_results.md](c21_results.md) und im JSON-Bericht.
`passed` erfordert eine tatsächlich erfolgreiche Ausführung; `failed` bezeichnet
einen tatsächlichen Fehler. `skipped`, `blocked` und `not tested` sind keine Erfolge.

| ID | Anforderung | Nachweis / Testfall | Testart |
| --- | --- | --- | --- |
| T01 | Capabilities, freigegebene Auswahl, fünfstufige Preview, Checkbox | `c21_ui_tcp`: `tcp_ui_execute_refresh_replay` | AppTest + echter HTTP-/Prozesstest |
| T02 | Execute, Queue, Guardian, natives PDF, Gate, Handoff, Originalreport | derselbe Check, fünf ursprüngliche `completed`-Stufen | AppTest + HTTP + native Prozesse |
| T03 | Status und Artefaktmetadaten | `tcp_artifact_metadata`, C20-B-Run-Hülle mit Hashprüfung im UI-Client | echter HTTP-Test |
| T04 | fünf `skipped / verified_reuse`, gleiche Job-ID, Historie 1 | `tcp_ui_verified_resume` | AppTest + echter HTTP-Test |
| T05 | doppelte Anforderungen, verlorene Antwort, neue Sitzung | `tcp_ui_execute_refresh_replay`; `test_concurrent_submits_lost_response_refresh_and_persistent_key_conflict` | TCP/AppTest und Routerintegration |
| T06 | Backend nicht erreichbar, physischer Neustart, persistierte ID | `tcp_backend_unreachable`, `tcp_backend_process_restart` | echter HTTP-/Prozesstest |
| T07 | veraltete Preview, beschädigtes Artefakt, Stale, Teilresume | `tcp_ui_stale_partial_resume`; bisherige Outputbytes unverändert | AppTest + echter HTTP-Test |
| T08 | Source-Ref, Owner, Course, Viewer | `tcp_invalid_source_owner_course`; UI-Authorization-Szenario | TCP und AppTest/Routerintegration |
| T09 | falsche Hashes, fehlende lokale Eingabe, kein neuer Job | `tcp_changed_hash_missing_input` | echter HTTP-Test mit externer synthetischer Fault Injection |
| T10 | Abbruch während nativer Verarbeitung, Timeout, Executor-Neustart, Resume | UI `test_native_pdf_cancel_timeout_and_executor_restart_are_visible_and_resumable`; Backend `test_http_pdf_cancel_timeout_restart_and_explicit_resume` | AppTest/Router + tatsächliche Prozesse |
| T11 | keine verwaisten PDF-Prozesse, physisches Cleanup vor terminalem Status | `test_real_pdf_worker_cancel_timeouts_parent_death_and_restart` | C19-Prozesstests mit PID-/Gruppennachweisen |
| T12 | C15: Starts, Running, Success, Failure, Cancel, Dauer, Timeout, Prozesslabel | TCP-Metriktext; UI-Teststore-Metriken; `test_pipeline_metrics`, `test_job_control` | tatsächliche Store-Aggregate und Vertrags-/Integrationstests |
| T13 | C10/C11/C13 und bestehende Schnittstellen bleiben kompatibel | explizite `BACKEND_TESTS` in `scripts/c21_acceptance.py` | Offline-Pytest-Regressionen |
| T14 | kanonische UI, Auth, bestätigte Mutationen, Refresh, sichere Fehler | vollständige unveränderte UI-Suite mit externem Backend | unittest / Streamlit AppTest |
| R01 | lokales echtes Material, Original-/Binding-/Parser-/Handoffprüfung | `c21_real_material`: Notes Week 5 aus vorhandenem Manifest | separate technische Realmaterialprüfung |
| R02 | reale Week-0-Slides und Source-Code-PDF | Originalbytes und überprüfte Bindungen erforderlich | blocked, sofern nicht explizit lokal vorhanden |
| R03 | mathematische Rekonstruktion realer Formeln | unabhängige Original-/Gold-/Prediction-Paare | blocked ohne unabhängige Goldannotation |
| M01 | echte Browserabnahme | [Reviewstruktur](c21_review.md) | not tested; AppTest ersetzt keinen Browser |
| M02 | fachliche Vollständigkeit, Bilder, Tabellen, Formeln | [Reviewstruktur](c21_review.md) | not tested bis menschlich geprüft |

Ein bereits bekannter Legacy-TXT-Konflikt wird separat diagnostiziert, nicht
ausgeblendet oder als C21-Erfolg gezählt. Der produktive Transcriptpfad wird hier
nicht umgebaut. Alle Grenzfälle werden im Ergebnisbericht konkret ausgewiesen.

## Lokales Profil

Vorhandene Backend- und UI-Umgebungen verwenden, keine Installation oder Downloads.
Variablen sind bewusst explizit; Backendcheckout enthält diesen PR, UIcheckout den
C20-Code einschließlich der kleinen Korrektur aus UI-PR 4. Bis zu dessen Merge
den angegebenen UI-Commit verwenden. Keine produktiven `.env`-Dateien oder Datenwurzeln übernehmen.

```bash
BACKEND=/pfad/zum/C21-backend-checkout
BACKEND_PYTHON=/pfad/zur/backend-venv/bin/python
UI=/pfad/zum/gemergten/ui-checkout
UI_PYTHON=/pfad/zur/ui-venv/bin/python
cd "$BACKEND"

"$BACKEND_PYTHON" -m scripts.c21_acceptance \
  --ui-repo "$UI" --ui-python "$UI_PYTHON" \
  --output /tmp/neue-c21-abnahme --temp-parent /dev/shm

# Nur den neuen HTTP-/AppTest-Test wiederholen:
"$BACKEND_PYTHON" -m scripts.c21_acceptance --profile tcp \
  --ui-repo "$UI" --ui-python "$UI_PYTHON" \
  --output /tmp/neue-c21-tcp-abnahme --temp-parent /dev/shm
```

Benötigt ist die explizite Erlaubnis der lokalen Ausführungsumgebung, Sockets zu
erzeugen und an `127.0.0.1` zu binden. Die hiesige Sandbox verweigerte schon
`socket.socket()`; der echte HTTP-Test wurde deshalb außerhalb dieser Socket-Sperre
ausgeführt. Keine externe Netzwerkverbindung ist nötig oder erlaubt. Der neue
Treiber lässt nur den eigenen dynamischen Loopbackport zu; der eigene Server
verbietet ausgehende Verbindungen. Bestehende Unit-/Routertests bleiben offline.

Das Full-Profil erzeugt neue private Scratch-Verzeichnisse und führt TCP, Backend-
Regressionen, UI-Suite und Ruff aus. `C16_REPO`/`C16_PYTHON` werden für die optionalen
UI-E2E-Methoden explizit gesetzt. Die tatsächlichen Subtestausgänge bleiben separat
im JSON, ohne sie zur Zahl der unittest-Methoden zu addieren. Ein logischer
Testpoller beschleunigt AppTest-Reruns; Netzwerk-/Prozessfristen laufen auf echter Zeit.

Vor dem Full-Profil wird das bereits installierte optionale SymPy einmal normal
importiert, mit 60-s-Frist und protokollierter Version/CPU-Zeit. Das erzeugt nur die
üblichen Python-Bytecodecaches in der vorhandenen Umgebung; keine Installation,
keine Paket-/Quelländerung. Die kalte SymPy-1.14-Initialisierung brauchte hier
12,816 CPU-Sekunden. Die bestehenden isolierten C11-Worker haben unverändert
2/3 Sekunden Soft-/Hard-CPU-Limit und 512 MiB; sie lesen die vorbereiteten Caches.
Ohne diese Vorbereitung meldeten zehn Tests korrekt Ressourcenabbruch statt der
erwarteten symbolischen Entscheidung. Dieser fehlgeschlagene Erstlauf bleibt als
solcher dokumentiert. Fehlendes SymPy wird weder installiert noch verdeckt; die
bestehenden optionalen Testregeln und `undetermined`-Verträge gelten weiterhin.

## Ressourcen und Bereinigung

- Vorher `df -h /tmp /dev/shm` und verfügbaren Arbeitsspeicher prüfen. Tmpfs ist
  RAM-verbrauchend und kein unbegrenzt großer Ersatz für Plattenspeicher.
- Bei bekanntem Btrfs-ENOSPC/atomic-rename-Problem einen ausreichend freien,
  explizit gewählten Scratch-Parent verwenden. Fehler protokollieren; keine
  Storagegarantien, Parserlimits oder Assertions lockern.
- Suiteaufträge laufen sequenziell mit 900-s-Frist (TCP 240 s). Die unveränderten
  C16-/PDF-Prozess-, Speicher-, Zeit- und Dateilimits gelten weiterhin.
- Nur eigene neue Workspaces und Testprozesse; keine produktiven Dienste oder DBs.
  Eigene Server werden beendet und `wait`-abgeholt, der bestehende Harness stoppt
  seinen Worker. Temporäre Scratchbereiche werden per `TemporaryDirectory` bereinigt.
- Explizites Outputverzeichnis bleibt zur Nachprüfung erhalten, Modus 0700.
  JSON/Markdown/Logs werden exklusiv erstellt. `manifest.json` hasht die erzeugten
  Dateien; der Bericht enthält zusätzlich Loghashes. Keine vorhandene Datei wird
  überschrieben. Echte Zeitwerte/IDs variieren; Verträge, Prüfschritte und Ergebnisse
  sind reproduzierbar, nicht sämtliche Laufzeitbytes.
- Keine pauschale Repositorybereinigung, kein Löschen von Branches oder fremden
  Worktrees. Der C21-Worktree bleibt bis zum Merge offen.

## Separates Realmaterialprofil

Die versionierte HTML-Datei `cs50_python/lecture_5.html` ist ein echtes lokal
gespeichertes Notes-Dokument, kein synthetischer Ersatz für die fehlenden Week-0-PDFs.
Manifest-URL und Quell-SHA müssen übereinstimmen; das vorhandene Materialmodell
liefert die ursprüngliche Course-/Section-/Lecture-Bindung. Neue Artefakte entstehen
ausschließlich in einem separaten neuen lokalen Verzeichnis.

```bash
"$BACKEND_PYTHON" -m scripts.acceptance.c21_real_material \
  --manifest docs/course_sources/cs50/manifest.json \
  --source docs/course_sources/cs50/cs50_python/lecture_5.html \
  --source-url https://cs50.harvard.edu/python/notes/5/ \
  --output /tmp/neue-c21-real-notes5
```

`review.json` und `visual.json` sind die unveränderten bestehenden C10-/C13-
Ausgabeverträge; `summary.json` enthält technische Beobachtungen. Originaldatei,
Parser, Knowledgeobjekte und bestehende Artefakte bleiben unverändert. Die lokale
Artefaktkopie bleibt für die manuelle Nachprüfung erhalten. Keine Bild-URLs werden
aufgerufen und kein Bild-/Formelinhalt wird dadurch semantisch bestätigt.
