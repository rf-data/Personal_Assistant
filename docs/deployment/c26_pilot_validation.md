# C26-PILOT-INTEGRATION – neue Offlinevalidierung

27.10.2026. **HOLD. Kein vollständig grüner Gesamtabschluss.** Quellintegration,
Einjob-/Ergebnisvertrag und zahlreiche Regressionen sind nachgewiesen; die
unten beschriebenen Fehler und fehlenden technischen/live Nachweise bleiben offen.
C26-04 bleibt DEFERRED. Keine SSH-/Hetzner-/Coolifyaktion, keine Domain-/Firewall-/
IdPänderung, kein Imagepull/-build/-start, keine produktiven Daten/Jobs/Downloads,
kein GitHubpush und kein Merge.

## Quellbasis und finale Nachläufe

Backendbasis: a8af1d9372eb435d3e1331c33b047d21120d57c2. D/E/F bis
7ffb4ed6fd4d8433edf36fb4851a382b9b9c595d plus hashverifizierte lokale G-/H-Dateien
wurden einmal integriert. Herkunft und Änderungen: [Integrationsmatrix](c26_pilot_gap_analysis.md).
Finale Produktbytes: [Quellmanifest](../../artifacts/c26_pilot_integration/code-manifest.json).
Die gemeinsame Gitverwaltung verweigert index.lock; Lieferung ist ein verifizierter
Gesamtpatch, kein behaupteter Liefercommit. Alle tatsächlichen Änderungen liegen
im persistenten vorgesehenen Pilot-Workspace. Kein fremder Worktree wurde geändert.

| Tatsächlich ausgeführter Lauf | Ergebnis | Dauer | Beleg |
| --- | --- | --- | --- |
| Finale Gate-/Settings-/Collector-/Koordinator-/Pilotverträge | **501 passed**, 0 failed, 0 errors, 0 skipped | 203.278 s | [gates-final.xml](../../artifacts/c26_pilot_integration/gates-final.xml), [gates-final.log](../../artifacts/c26_pilot_integration/gates-final.log) |
| Finale C16-/Runtime-/PDF-/Storage-/Workflowregression | **312 passed**, 1 failed, 0 errors, 0 skipped | 283.673 s | [runtime-final.xml](../../artifacts/c26_pilot_integration/runtime-final.xml), [runtime-final.log](../../artifacts/c26_pilot_integration/runtime-final.log) |
| Native C22-/H-/HTTPS-/Pilot-Composechecks | **89 passed**, 0 failed, 0 errors, 0 skipped | 28.25 s | [compose-final.xml](../../artifacts/c26_pilot_integration/compose-final.xml), [compose-final.log](../../artifacts/c26_pilot_integration/compose-final.log) |
| Pilot-Compose einschließlich separatem UIoverlay | **38 passed**, 0 failed, 0 errors, 0 skipped | 12.943 s | [pilot-ui-compose.xml](../../artifacts/c26_pilot_integration/pilot-ui-compose.xml), [pilot-ui-compose.log](../../artifacts/c26_pilot_integration/pilot-ui-compose.log) |
| Nachlauf nach expliziter Kataloggrößenprüfung | **45 passed**, 0 failed, 0 errors, 0 skipped | 76.317 s | [capacity-final.xml](../../artifacts/c26_pilot_integration/capacity-final.xml), [capacity-final.log](../../artifacts/c26_pilot_integration/capacity-final.log) |
| Separater nativer Capacity-Composefall | **1 passed**, 0 failed, 0 errors, 0 skipped | 2.929 s | [native-capacity-final.xml](../../artifacts/c26_pilot_integration/native-capacity-final.xml), [native-capacity-final.log](../../artifacts/c26_pilot_integration/native-capacity-final.log) |
| Expliziter Ergebnis-/Viewer-/Course-Nachlauf | **1 passed**, 0 failed, 0 errors, 0 skipped | 6.001 s | [result-roles-final.xml](../../artifacts/c26_pilot_integration/result-roles-final.xml), [result-roles-final.log](../../artifacts/c26_pilot_integration/result-roles-final.log) |
| Gate-v1-Nachlauf nach Testzeitpunktkorrektur | **66 passed**, 0 failed, 0 errors, 0 skipped | 25.612 s | [gate-clock-final.xml](../../artifacts/c26_pilot_integration/gate-clock-final.xml), [gate-clock-final.log](../../artifacts/c26_pilot_integration/gate-clock-final.log) |
| Vollständige UI-Standardsuite | **151 bestanden**, 25 erwartete IPC-Skips, 176 ausgeführt | 45,395 s | [UIlog](../../artifacts/c26_pilot_integration/ui-default.log) |
| Genau diese 25 IPC-Fälle auf integriertem Backend | **25 bestanden**, keine Skips; kanonische Streamlit-App, echte Handler/Queue/Prozesse | 284,713 s | [IPC-Log](../../artifacts/c26_pilot_integration/ui-ipc-final.log) |
| Breite zusätzliche Backend-Offlinesuite | 3099 passed, 2 failed, 0 errors, 25 skipped; 3104.631 s | Siehe Rohbeleg | [Extended-Log](../../artifacts/c26_pilot_integration/extended.log) |

In den finalen gezielten Backend-/Nativegruppen sind **936
unterschiedliche Fälle bestanden**; überlappende Nachläufe sind nicht addiert.
Zusammen mit 176 unterschiedlichen UI-Fällen sind das
**1112 unterschiedliche bestandene gezielte Fälle**,
zusätzlich **ein fehlgeschlagener Fall im finalen Runtimegruppenlauf**.
Ein späterer isolierter Erfolg ersetzt diesen Fehler nicht. Die ursprünglichen
486 Fälle des alten Pakets werden nicht hinzuaddiert. Die breite Suite wird
separat bilanziert: Sie begann vor den letzten Settings-/Ergebnis-/Capacityänderungen;
der betroffene Produktumfang wurde deshalb in den finalen gezielten Gruppen neu geprüft.
Eine finale erfolgreiche vollständige Projektregression wird nicht behauptet.

Runtimegruppenlauf: zwei explizite External-Deselections (native C22-Composeprüfung,
separat bestanden, sowie echter Contentsearch-Loopbackserver, hier nicht ausgeführt).
Capacitynachlauf: eine native Deselection, danach separat bestanden.
UI-Standardskips werden genau einmal durch den 25er-IPC-Lauf ersetzt.
Exakte finale Modulreihenfolgen, Profile, isolierte Roots und Umgebungen:
[Befehlsmanifest](../../artifacts/c26_pilot_integration/commands.json).
[Maschinenlesbare Bilanz](../../artifacts/c26_pilot_integration/validation-summary.json).

## Was die positiven Fälle tatsächlich belegen

- Vorhandene C16-Authentifizierung, Viewer/Operator/Owner-/Coursegrenzen;
  individuelle Backendtoken statt gemeinsamer UIkennung. UI-OIDC-/Claimablauf,
  unbekannte Identität, Authlib-/Session-/Origin-/Cookie-/WebSocketgrenzen synthetisch.
- Ein echter lokaler material_planning-Adapter auf ausschließlich synthetischem
  Manifest; Preview/Bestätigung, ein Job insgesamt, Clientersatz, persistenter
  Status und verifizierte Ergebnisreferenz. Keine Downloads oder echten LLMcalls.
- Neues GET /v1/jobs/{job_id}/result: abgeschlossener Materialplan, 256-KiB-Grenze,
  Größe/Hash/Schema, Auth/Course/Viewer, fehlende/manipulierte/zu große/Symlinkdatei,
  keine Pfadparameter und keine Fehlerdatenlecks. Die existierende UI-Clientklasse
  liest diese Route in einem direkten synthetischen Transporttest.
- V2-Settingsbindung aller vorhandenen API-/Executor-/Storewriter unter dem
  bestehenden Admissionlock. Alte Resumeplanung erlaubt keine driftende Policy;
  false→true allein öffnet nichts. Fehlendes/defektes/gesperrtes Gate bleibt zu.
- D/E/F/G/H: Admission, Queue, Drain, echte Idle-/Lease-/Guardianlocks, Race-/TOCTOU-,
  einmalige scope-/commit-/imagegebundene Permits, Recovery/Rollback, Crash/Replay,
  unklarer Driverstatus und fehlender Witness. Kein authentifizierter Capture wird
  in eine Fixturefreigabe umgedeutet; sämtliche Driver bleiben inert/offline.
- C22-/H-/Pilotrollen, getrennte Profile, kein Defaultstart, non-root, read-only,
  begrenzte CPU/RAM/Swap/PIDs/Logs/tmpfs, gleiche Queue/Config, private Namespacebindung,
  keine Hostports/Sockets. Native Compose5.0.2 mit nicht existierendem Daemonsocket.
  Routerlabels sind ausdrücklich synthetische Coolify-Stand-ins.
- Katalogbudget wird im vorhandenen CapacityExecutor vor Initialisierung gegen
  hashverifizierte Bytes geprüft; globale C16-Datei-/Gesamtgrenzen bleiben erhalten.
  Ein Capacitybudget ist keine echte Datenträgerquota.

**UI-Grenze:** Die Streamlit-App zeigt bisher Status und Artefaktmetadaten,
noch kein neues Plananzeigewidget. Dafür fehlen ein separat beschreibbares
persistentes UI-Arbeitsverzeichnis und eigener UI-Branch außerhalb des Backendrepos.
Es wurde kein UI-Code ins Backend kopiert. Der direkte Clienttest beweist
keine fertige Browseranzeige und keine echte OIDC-/TLS-/VPN-Abnahme.
Die bestehende AppTest-/IPC-Suite verwendet synthetische Principals und
individuelle C16-Token, kein live angemeldetes IdP-Konto.

UI-Quellstand: main ba34e98…; Produktbaum entspricht e4be7a2…, nur aktuelle
HTTPSdokumentation ergänzt. Für den unveränderten IPC-Harness war eine **saubere
wegwerfbare Git-Testkopie unter /tmp** erforderlich. Sie ist ausschließlich
Validierungsfixture, niemals einziger Arbeitsstand oder Liefercommit.
[Snapshotmanifest](../../artifacts/c26_pilot_integration/ipc-source-snapshot.json).
Die späte Capacitybudget-Ergänzung unterscheidet sich dort in genau
scripts/cs50_worker.py, das dieser IPC-Harness nicht startet; separat 45 Fälle geprüft.
API-/Executor-/Gatecodes sind identisch; kein Test des vollständigen finalen
Snapshotbaums behauptet. [Abgleich](../../artifacts/c26_pilot_integration/ipc-product-comparison.json).

## Rote Vorläufe und weiterhin offene Fehler

1. Neuer Test erwartete fälschlich HTTP400 statt vertraglichem 422 bei fehlender
   expliziter Bestätigung. Assertion korrigiert, keine Produktgrenze gelockert.
   Neuer Test erwartete außerdem phase im Gate.run-Ergebnis statt Status
   verified_offline plus Gate.status.phase; ebenfalls Testvertragskorrektur.
2. Native Erstprüfung: Compose5 liefert Speicherbytes als numerische Strings;
   der neue Prüfer normalisiert sie. Separat tatsächlich entdeckt: unquotierte
   tmpfs-Flowlisten zerlegten Mountoptionen. Vorlagen korrigiert und native
   sowie YAMLregression bestanden. [Erstlog](../../artifacts/c26_pilot_integration/compose-a.log).
3. Ein synthetischer Planungsdurchlauf wurde nach einer **OperationalError**
   korrekt interrupted/quarantined. Der vorhandene Guardian speichert nur die
   Fehlerklasse; SQLitecode und fehlschlagendes Statement sind unbekannt.
   Kein Retry, kein Entfernen des Markers und kein höherer Timeout.
   Spätere Positivläufe beweisen keinen Ursachenfix.
   [Originalbefund](../../artifacts/c26_pilot_integration/workflow-b.xml),
   [redigierte Jobs/Events/Ergebnishash](../../artifacts/c26_pilot_integration/workflow-b-forensics.json).
4. Finale Runtimegruppe: test_completed_pdf_workflow_restore_retains_all_output_hashes_and_origin
   scheitert mit generischem Adapter-**Exit3**, Job failed/internal, kein Ergebnis.
   Kein bestätigter fehlgeschlagener Restore: der vorgelagerte synthetische Workflow
   scheiterte vor backup/restore. Die isolierte unveränderte a8af1d9-Basis und
   der isolierte Kandidat bestehen jeweils denselben unveränderten Fall (12,16/11,08 s).
   Damit ist weder eine Produktregression noch deren Abwesenheit kausal bewiesen.
   Der Gruppenfehler bleibt offen, nicht durch Retry grün gerechnet.
   [Forensik](../../artifacts/c26_pilot_integration/pdf-failure-forensics.json),
   [Basisvergleich](../../artifacts/c26_pilot_integration/pdf-baseline.xml),
   [Kandidatenvergleich](../../artifacts/c26_pilot_integration/pdf-candidate.xml).

Sämtliche roten Logs/XML bleiben erhalten. Es wurden keine Sicherheitsassertionen,
Quarantänen, Joblimits oder Guardianfristen abgeschwächt. Breite Fehler bleiben gesondert erhalten:

5. Breiter Lauf: test_managed_worker_cancel_restart_resume_and_stopped_backup[signal]
   wirft database is locked in Store.all während des Wartens auf Batchabschluss.
   Der spätere gezielte Capacity-/Workerlauf umfasst denselben Fall und besteht;
   es wurde keine SQLite-Ursache behoben. [Forensik](../../artifacts/c26_pilot_integration/extended-worker-forensics.json).
6. Breiter Lauf: test_no_exact_current_approval_no_deployment[change4] verwendete
   time.time()+1000 bereits in der Collection. Als der Test nach mehr als 1000 s
   lief, war dieser Wert keine zukünftige Freigabe mehr und wurde vertragsgemäß
   akzeptiert. Kausal identifizierter Testaufbaufehler: zukünftigen Zeitpunkt nun
   erst beim Testaufruf konstruieren. Der neue Nachlauf prüft den ganzen v1-Gateumfang.
   Keine Änderung an produktiver Approvalprüfung, Laufzeit oder Sicherheitsassertion.

Der breite Originallauf bleibt mit **zwei Fehlern** protokolliert, auch nach
Korrektur seines einen Zeitfixturefehlers. Keine finale komplett grüne
Gesamtprojektsuite und kein kausaler Fix der offenen SQLite-/Exit3-Befunde.

## Installation, statische Prüfung und nicht ausgeführte Bereiche

AST, Runtimeimporte sowie Ruff check/format sind tatsächlich ausgeführt;
[statischer Beleg](../../artifacts/c26_pilot_integration/static-final.json).
Das ist weder vollständiger Import aller optionalen SDKs noch Runtimeimagebeweis.
Vorhandene Python3.12.12-Umgebungen wurden nicht aktualisiert; Backend Pydantic2.13.4,
pytest9.1.1, httpx0.28.1, PyMuPDF1.28.2. Pydantic-settings und returns fehlen in
dieser Backend-Testvenv. UI: vorhandene eigene gepinnte Testvenv.
[Umgebungsbeleg](../../artifacts/c26_pilot_integration/environment.json).

Der ausdrücklich gefrorene Offline-Installationsversuch in neuer /tmp-Testvenv
und neuem Cache verweigert mangels gecachtem typer-Wheel den Abschluss (Exit1).
**Positive vollständige Installation NICHT AUSFÜHRBAR.** Netzwerk ist deaktiviert;
keine bestehenden Venvs/Locks wurden geändert und keine Pakete heruntergeladen.
[Installationslog](../../artifacts/c26_pilot_integration/runtime-install.log).
Direkter Gitremotezugriff scheitert an DNS (Could not resolve host github.com);
Commit-/PR-/Dateiverifikation über lesenden GitHubconnector war erreichbar.

Nicht ausgeführt: Images bauen/ziehen/starten; echte UID/Mount-/Cgroup-/PID1-/OOM-/
Netz-/Quota-/Speicherabnahme; echter Browser, IdP, TLS/SAN/WSS, VPN/IPv6 und
unabhängige Negativquelle; tatsächlicher Coolify4.5.0-/Compose5.6.0-Effektivbaum;
Registry-/Buildattestation, produktiver Producer/Witness/Operator/Driver und
exklusiver Triggerpfad; echte Backup-/Restore-/Alarmabnahme. Simulierte fehlende
DNS-/TLS-/Secrets-/Timeout-/Build-/Hostmetadaten bleiben echte Negativtests,
keine behauptete Livevalidierung. Kein vollständiger C26-Go-live.

## Sicherung und Lifecycle

Eigene Quellen und Berichte bleiben im persistenten Pilot-Workspace. Vollständiger
Patch, Dateiprüfsummen, tatsächlich angewendeter/reversierter Patchcheck und manuelle
Commit-/Featurepushanleitung liegen lokal unter
artifacts/c26_pilot_integration/handoff/. Dieses Verzeichnis ist bewusst nicht
Teil seines eigenen Patches. Der gemeinsame Index ist read-only; Defaultintegration
und PR bleiben pending. Mergeverbot hat Vorrang. Keine fremden oder MAINT-inventarisierten
Branches/Worktrees, keine Stashes/Volumes/Venvs entfernt. Eigene Testkopien bleiben
als nachvollziehbare Evidence erhalten; keine erfolgreiche Bereinigung behauptet.

---

## Historische Validierung des Betreiberpakets 1f53289

# C26-PILOT – Tatsächliche Offlinevalidierung

27.10.2026. **Reviewfähiges Vorbereitungspaket; Pilotdeployment weiterhin HOLD.
C26 insgesamt HOLD, C26-04 DEFERRED, #111 offen.** Keine Host-/SSH-/Cloud-/Coolify-
APIverbindung, kein Deployment/Restore, keine Firewall-/Domainänderung, keine
produktiven Daten, Downloads oder echten LLMrequests. Synthetische Testjobs in
isolierten lokalen Testumgebungen waren Bestandteil der ausdrücklich verlangten Tests.

## Quellidentität und Isolation

Backend-GitHub-master und lokaler Testcode: `a8af1d9372eb435d3e1331c33b047d21120d57c2`.
Remote nur über GitHubconnector lesend geprüft; kein Branch/PR/Issue verändert.
PR-/Issuezustände und Dateiabwesenheit: [Quellbeleg](../../artifacts/c26_pilot/source-evidence.json).

UI-GitHub-main: `ba34e98c14e66921bf9c515c82a16201bc8baa1a`. Dieses Objekt war im
vorhandenen lokalen UIrepository nicht verfügbar; direktes Gitfetch scheiterte
an gesperrter DNSauflösung. Der lesende GitHubcompare belegt gegenüber lokalem
`e4be7a2fbf5b20beda0db854462dd2d70c2c93ff` genau **eine** geänderte Datei:
`docs/c26_https.md`, +16/-0. Produktcode, Tests, Dockerfiles und Lock sind identisch.
Die aktuelle Dokumentation wurde über den Connector abgerufen, in der **eigenen**
UIarbeitskopie ergänzt und mit dem Remote-Gitblob
`8675783221d015ad5dc7ac6ed3f9b0004b9eed90` exakt abgeglichen.
Lokaler Snapshotcommit `a6940aead778baefe427a5943f03d2ff41a35fec`, Tree
`c34c3039f3039dcd3252da19e79bb19bbeaa0e43`; er wird ausdrücklich **nicht** als
Remote-main-Commit ausgegeben. So wurde der aktuelle main-Inhalt geprüft, ohne
einen veralteten PRbranch zur Produktionsbasis zu erklären.

Die gemeinsame Gitverwaltung des Ausgangsworktrees war read-only. Ein normaler
`git worktree add` konnte deshalb keinen Branchref schreiben. Statt fremde
Metadaten anzupassen, wurden unabhängige lokale Barekopien und eigene Worktrees
im dauerhaft erlaubten Projektverzeichnis angelegt:

| Aufgabe | Eigenes Artefakt unter `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c24r/.pilot-worktrees/` |
| --- | --- |
| Backendmetadaten | `backend.git/` (unabhängiger lokaler Clone, keine Hardlinkschreibkopplung) |
| Lieferworktree | `backend/`, Branch `docs/c26-pilot-package` auf aktuellem master |
| Saubere Kompatibilitätsreferenz | `backend-reference/`, detached `a8af1d9…`, unveränderte tracked Dateien |
| UImetadaten | `ui.git/`, unabhängiger lokaler Clone |
| UIauditworktree | `ui/`, Branch `docs/c26-pilot-ui-main-snapshot`, ausschließlich aktuelles main-Dokument gespiegelt |

Keine fremden Worktrees geändert. Vorhandene Pythoninterpreter wurden nur
ausgeführt, nicht synchronisiert/installiert/aktualisiert; `PYTHONDONTWRITEBYTECODE=1`.
Testprozesse bekamen eine mit `env -i` geleerte Umgebung und explizite harmlose
Testwerte; keine bestehenden `.env`/Secrets kopiert. Keine Dependencyupgrades.

## Ergebnisse

| Lauf | Ergebnis | Dauer | Dauerhafter Beleg |
| --- | --- | --- | --- |
| B0, erster Backendversuch mit basetemp **innerhalb** Repository | 111 passed, 18 failed, 135 errors, 2 deselected | 18,85 s | [Originalausgabe komprimiert](../../artifacts/c26_pilot/backend-tests.log.gz), [Original-JUnit komprimiert](../../artifacts/c26_pilot/backend-junit.xml.gz) |
| B1, gleiche Auswahl mit externem isoliertem synthetischem Testroot | **264 passed**, 2 deselected, keine Skips | 197,02 s | [Ausgabe](../../artifacts/c26_pilot/backend-external-root-tests.log), [JUnit](../../artifacts/c26_pilot/backend-external-root-junit.xml) |
| U1, vollständige UI-Defaultsuite ohne Backendopt-ins | **151 bestanden**, 25 skipped, 176 gesammelt | 26,494 s | [Ausgabe](../../artifacts/c26_pilot/ui-tests.log) |
| U2, genau die 25 backendabhängigen UItests mit synthetischem IPC auf sauberer aktueller Backendbasis | **25 bestanden**, keine Skips | 178,226 s | [Ausgabe](../../artifacts/c26_pilot/ui-backend-tests.log) |
| C1, HTTPS-/Negativ-/Profilchecks mit echtem lokalem `docker compose config`, ohne Daemon | **46 bestanden**, keine Skips | 11,81 s | [Ausgabe](../../artifacts/c26_pilot/compose-tests.log), [JUnit](../../artifacts/c26_pilot/compose-junit.xml) |

B0 ist ein dokumentierter fehlgeschlagener Lauf. `Settings.root` verweigerte
korrekt Ausgaben unter dem Anwendungscheckout ohne explizite Mountautorisierung.
Die Folgefehler stammen aus dieser absichtlich restriktiven Pfadgrenze. B1 änderte
**nur** das Testausgabeziel auf `/tmp/c26-pilot-backend-20261027`; keine Produkt-
oder Testassertion wurde gelockert. Alle 264 ausgewählten Fälle bestanden danach.
Kein behaupteter Produktfix. Die vollständigen B0-Originale bleiben zusätzlich
unkomprimiert im dauerhaften lokalen Ergebnisverzeichnis erhalten.

B1s zwei ausgeschlossene externe Nodes waren
`test_compose_cli_resolves_only_explicit_profiles` (in C1 danach bestanden) und
`test_real_local_http_server_and_process_restart` aus der Contentsearchsuite
(nicht ausgeführt). Skips und Deselections werden nicht zu Erfolgen addiert.
U2 ersetzt genau die 25 U1-Skips, ohne U1 nochmals als neuen Vollerfolg zu zählen.
Über diese finalen Gruppen sind **486 unterschiedliche Tests bestanden**;
B0 wird weder verborgen noch als zusätzlicher Erfolg gezählt.

## Was wurde geprüft?

| Bereich | Konkrete aktuelle Belege |
| --- | --- |
| Backendauth/Rollen/Owner/Course, Negative Security | `test_job_control.py`, `test_workflow_http.py`, `test_content_search_http.py`, UI Liveclient-/Controller-/HTTPSsuite und U2 |
| UI/OIDC/Sessions/Cookies/Origin/Forwarded/WSS | `test_https_security.py` (11), `test_container_runtime.py` (9); reale Authlib-Nonce-/Expiryprüfung, synthetische ASGIrequests; kein echter Browser/IdP |
| HTTP-/TLS-/Containervorlagen | `test_deployment_operations.py`, `test_https_preflight.py`, UI `test_deployment.py`; echte Compose-CLI, **synthetisch ergänzte Coolifyrouterlabels**, keine Live-TLSverbindung |
| Health/Readiness/fehlende Pflichtinputs | Operations-/Containerguard-/Clienttests; 401health bleibt von authentifizierter Readiness unterschieden |
| Queue/Singleton/Kapazität/Cancel | `test_job_control.py`, `test_job_executor.py`, `test_job_store_contention.py` |
| Echte synthetische Prozessgrenzen/Parent-Death/Timeout/Restart | Executor-/PDFtests, U2; keine realen fachlichen Jobs, keine produktiven Cgroups |
| Resume/Fehlerfälle/Idempotenz/Quarantäne | `test_workflow_http.py`, `test_pdf_job_control.py`, `test_workflow_course_contract.py`, UI-Workflow-IPC |
| Storage-/Sourceberechtigungen/Pfade | `test_runtime_paths.py`, `test_content_store_artifacts.py`, `test_content_read_contracts.py`, `test_content_search_http.py` und Review-/Such-IPC |
| UI-/Backendkompatibilität | 25 Fälle U2: kanonische Streamlit-App → echte Handler/Queue/Executor über IPC, Owner/Viewer/Course, Resume/Cancel, Review/Suche/Revocation |
| Deployment-/Admissiongate, Drain-/Idleraces | **NICHT AUSFÜHRBAR:** entsprechender Code und Tests fehlen auf tatsächlichem master; kein vorgetäuschter Gatepass |

## Reproduktion der ausgeführten Testauswahl

Nur lokale Reviewmaschine, vorhandene geprüfte Interpreter, neue isolierte
Testroots; niemals auf Hetzner. Alle Reportnamen müssen bei einer Wiederholung
neu gewählt werden, damit Originalbelege erhalten bleiben. Folgende Variablen
sind reine Pfadreferenzen, keine Secrets:

```sh
PILOT_BACKEND_PYTHON=/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c24r/.venv/bin/python
PILOT_UI_PYTHON=/home/robfra/0_Portfolio_Projekte/personal-assistant-ui-c26b/.venv/bin/python
PILOT_REFERENCE=/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c24r/.pilot-worktrees/backend-reference
```

B1 aus dem Backend-Lieferworktree; das hier genannte neue Tempziel ist nur ein
Beispiel für eine **neue** Wiederholung, nicht der bereits ausgewertete Root:

```sh
env -i PATH=/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONNOUSERSITE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  "$PILOT_BACKEND_PYTHON" -m pytest -q -o addopts= -p no:cacheprovider \
  -p tests.offline_guard -m 'not external_integration' \
  tests/test_job_control.py tests/test_job_executor.py tests/test_job_store_contention.py \
  tests/test_deployment_operations.py tests/test_deployment_pdf_restore.py \
  tests/test_pdf_job_control.py tests/test_workflow_http.py tests/test_workflow_course_contract.py \
  tests/test_runtime_paths.py tests/test_content_store_artifacts.py \
  tests/test_content_read_contracts.py tests/test_content_search_http.py \
  --basetemp=/tmp/c26-pilot-backend-new-run
```

U1 und U2 aus dem eigenen UIworktree, jeweils separat:

```sh
env -i PATH=/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \
  "$PILOT_UI_PYTHON" -m unittest discover -s tests -v
```

```sh
env -i PATH=/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \
  C16_REPO="$PILOT_REFERENCE" C16_PYTHON="$PILOT_BACKEND_PYTHON" \
  REVIEW_BACKEND_REPO="$PILOT_REFERENCE" REVIEW_BACKEND_PYTHON="$PILOT_BACKEND_PYTHON" \
  "$PILOT_UI_PYTHON" -m unittest -v tests.test_c16_e2e tests.test_workflow_e2e \
  tests.test_review_ui tests.test_search_ui
```

C1 aus Backend; absichtlich nur gelesene `config`-Unterbefehle und ein
nicht existierender lokaler Daemonsocket, kein Compose-up/build/pull:

```sh
env -i PATH=/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONNOUSERSITE=1 \
  DOCKER_HOST=unix:///tmp/c26-pilot-no-daemon.sock \
  "$PILOT_BACKEND_PYTHON" -m pytest -q -o addopts= -p no:cacheprovider \
  --run-external tests/test_https_preflight.py \
  tests/test_deployment_operations.py::test_compose_cli_resolves_only_explicit_profiles
```

## Umgebungs- und Aussagegrenzen

Backendinterpreter Python 3.12.12; pytest 9.1.1, Pydantic 2.13.4, httpx 0.28.1,
BeautifulSoup 4.15.0, PyMuPDF 1.28.2. Weitere Paketversionen und **fehlende**
`pydantic-settings`/`returns` in dieser Testvenv:
[Environmentbeleg](../../artifacts/c26_pilot/backend-environment.json).
Deshalb kein exakter vollständiger Runtime-Lock-/Imagebeweis. Die getesteten
Versionen der vorhandenen Runtimepakete entsprechen ihren schmalen Pins.
UIinterpreter Python 3.12.12, Streamlit 1.65.0, Authlib 1.9.1,
Pydantic 2.14.0, pydantic-settings 2.15.0. Keine Installation vorgenommen.
Lokale Compose-CLI v5.0.2; Serverangabe v5.6.0 wurde nicht nachgemessen.

Nicht ausgeführt: Images bauen/ziehen/starten; tatsächlicher Container-/Cgroup-/
OOM-/PID1nachweis; kompletter Browser-/TLS-/VPN-/IPv6test; echter IdP, Secretrotation,
Registry-/Buildprovenienz; Hostmount-/Quota-/Storageprüfung; produktiver
Collector/Koordinator/Driver, Gate-/Drainraceabnahme und vollständige Projektregression.
C22-Restoretests verwendeten ausschließlich neue synthetische Tempdaten und
stellen keine #111-Abnahme dar. Python-Offlineguards sind Testassertionen, keine
OS-Sandbox; existierende Prozessfixtures und verwaltete Sandbox begrenzen Children.

Bei der abschließenden Quellvertragsprüfung zusätzlich festgestellt und im
Wechselplan berücksichtigt: `Executor.__init__` verweigert execution false.
Der C05-Stufenstart umfasst deshalb API/Gateway ohne laufenden Executor;
Workerstart und Health-/Idleprüfung folgen erst in C08 unter geschlossenem Gate.
Keine angeblich gesunde Standby-Workerruntime bei deaktivierter Ausführung.
Die Backend-/UI-Remoteheads wurden zum Abschluss nochmals lesend bestätigt und
sind unverändert. [Maschinenlesbare Laufbilanz](../../artifacts/c26_pilot/validation-summary.json).

Die acht geforderten Dokumente und redigierten Belege werden lokal versioniert;
kein Push, kein PR-/Issuekommentar, kein Merge nach master/main. Gemäß AGENTS.md
bleiben Aufgabenbranches/-worktrees bis späterem regulären Review erhalten;
die ausdrückliche Mergesperre dieses Auftrags hat Vorrang vor einer
Defaultbranchintegration. Artefakte wurden weder bereinigt noch fremde Branches
angefasst. Liefercommit, vollständiger Patch und Reststatus werden im lokalen
Handoff unter `artifacts/handoff/` nach dem Commit verifiziert.
