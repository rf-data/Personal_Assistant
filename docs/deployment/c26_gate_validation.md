# C26 – Deployment-Gate: Offline-Abnahme und offene Produktion

22.10.2026. **Gate-Kern implementiert und lokal synthetisch geprüft;
Produktionsstatus `blocked`.** Führende Architektur, konkrete Coolifystrategie,
Betreiberinventur, Bootstrap, Rollout und Recovery:
[deployment_gate.md](deployment_gate.md). VPN/HTTPS/IdP/API bleiben im
[HTTPS-Handbuch](https.md). Maschinenlesbare Zahlen und Quellfingerprints:
[c26_gate_validation.v1.json](c26_gate_validation.v1.json).

## Verifizierter Ausgangsstand

| Repository / Integration | Tatsächlicher Nachweis |
| --- | --- |
| Backend master | `e581e201ef6b3d6c06aca14de845e0687d213b37`, live `ls-remote` und Commitobjekt |
| Backend #137 | gemergt 20.10.2026 20:14:42 UTC, `59e8d6b` |
| Backend #147 | gemergt 22.10.2026 16:31:06 UTC, `e581e20`; geprüfter Taskhead `d0a58f3` ist Vorfahr |
| UI main | `e4be7a2fbf5b20beda0db854462dd2d70c2c93ff`, live `ls-remote` und Commitobjekt |
| UI #18 | gemergt 20.10.2026 20:13:43 UTC, `49cf9ee` |
| UI #19 | gemergt 22.10.2026 16:30:41 UTC, `e4be7a2`; Tree identisch zum Korrekturhead `371befb` |

Issue #146 wurde einschließlich Beschreibung/Kommentare geprüft und bleibt OPEN.
Backend #100, #109–113 sowie UI #14/#15 sind ebenfalls weiterhin offen. Keine
produktive Abnahme aus einem Merge abgeleitet. Bestehende Queue-/Job-/Worker- und
C18-/C22-/C26-Verträge, Docker-/Coolifytemplates und Maintenancefence wurden gelesen.
Kein SSH-Zugriff, keine Host-/Coolify-/DNS-/VPN-/Firewall-/IdP-/Secretänderung,
kein produktiver Job-/Daten-/Volumezugriff und kein automatischer Merge.

## Umsetzung und bewusst verbleibender Blocker

| Modul / Artefakt | Änderung |
| --- | --- |
| `src/job_control/deployment_gate.py` | Präziser Plan-/Approval-/Livebeobachtungsvertrag, Drain-/Wechselsitzung, dauerhafte Annahmesperre, Worker-/Guardian-/Queueprüfung, Audit und separate Recovery-/Resumefreigaben |
| `controller.py`, `store.py` | Atomare Bestätigung neuer Jobs und spätere Queued-Freigabe unter demselben Admission-Lock; bei Pflichtgate keine Queueinitialisierung auf fehlendem Mount |
| `executor.py` | Protokolllease derselben Workerinstanz, Dispatch unter demselben Lock, Gatefehler pausiert neue Starts und lässt bestehende Kinder auslaufen |
| `models.py`, `docs/job_control/contract.v1.json` | Ausschließlich optionales strikt boolesches `deployment_gate_required=false`; Snapshotänderung exakt fünf Zeilen, kein DB-Schemawechsel |
| `operations.py` | Laufzeitlocks nicht mitsichern; neuer isolierter Restore erhält Gatehistorie plus `held`, bleibt inaktiv |
| `scripts/deployment_gate.py` | Private lokale Status-/Initialize-/Planprüfung; niemals losgelöstes Permit oder produktiver Deployaufruf |
| Beide vorhandenen Dockerfiles/-ignore, `worker_image_smoke.py` | Neue CLI im vorhandenen Runtime-Buildkontext, keine neue Rolle/Dependency; fünf sichere CLI-Smokes |
| `tests/test_deployment_gate.py` | Echter C16-Store/Executor, SQLite, Linux-flock, konkurrierende Prozesse, Crash, Recovery und bestehendes vollständiges Backup/Restore; ausschließlich synthetischer Deploymentdriver |
| UI | Nur aktueller Doku-/Merge-/Teststatus ergänzt; Runtime, Lock und Dockerimage unverändert |

**Kein produktiver Coolify-Driver:** Ressourcen-/Buildtyp, tatsächliche Trigger,
externe Jobs/Annahmepfade, Mount-/Queuezuordnung und SHA↔Registrydigest-Bindung
sind unbekannt. Der aktuelle offizielle Deploy-Endpunkt allein belegt keine
SHA-fixierte, atomare Einressourcenoperation im unbekannten Bestand. Der getestete
Driver ersetzt nur eine synthetische Ressourcenmarkierung; er führt kein Docker,
HTTP, Coolify oder SSH aus. Reale Triggerabschirmung und erster Gatebootstrap
bleiben zwingende Betreiber-/Adapteraufgaben. Das Gate ist **noch kein produktiver
Schutz gegen einen bestehenden direkten Coolify-/Webhook-/Git-Trigger**.

## Tatsächlich ausgeführte abschließende Prüfungen

Vorhandene Backendvenv: Python 3.12.12, Pytest 9.1.1, Pydantic 2.13.4. Vorhandene
UI-C26-Testvenv mit eingefrorenem Streamlit/Authlib. Keine neue Dependency, kein
Lockupdate und kein Paket-/Modell-/Realmaterialdownload. Tempdaten liegen im RAM
(`TMPDIR=/dev/shm`, Pytest-Basetemps unter `/dev/shm`). Die Systemeigenschaften
dieser Testmaschine sind kein Nachweis des Hetzner-Mounts.

| Lauf | Pass / Fail / Error / Skip | Dauer |
| --- | --- | --- |
| Abschließende vollständige Gate-Suite | **66 / 0 / 0 / 0** | laut JSON/JUnitbeleg |
| Breiter Lauf: Gate, Runtimeclosure, HTTPS-Preflight, C16, Executor, C22, Import/Index, C18-HTTP | **264 / 1 / 0 / 2** aus 267 Fällen | 277,01 s |
| C26 Batchworker, Runtime-Mountpolicy, integrierte B3–B7-Materialverträge | **83 / 0 / 0 / 0** | 67,65 s |
| UI HTTPS-/OIDC-Sicherheit | **11 / 0 / 0 / 0** | 3,67 s |
| UI Produktionsstartguards | **9 / 0 / 0 / 0** | 0,18 s |
| Tatsächlicher Runtime-CLI-Smoke | **5/5 Module passed** | keine Jobs/Netzverbindung |
| Derselbe C18-Snapshotfall auf unverändertem aktuellem master | **0 / 1 / 0 / 0** | 3,00 s |

Diese Läufe überlappen: der breite Lauf enthielt einen früheren Stand der
Gatefälle. Die abschließende 66er-Suite prüft zusätzlich die späteren engen
Reviewkorrekturen (Diagnosekonkurrenz, zeitliche Freigabegrenze, keine Ersatzqueue,
ungültige Imageverweise/Journale). Zahlen nicht zu einer behaupteten grünen
Gesamtsuite addieren. Die zwei Skips sind der explizite Docker-Buildkontextaudit
und ein nicht bereitgestelltes gebautes Workerimage. Kein aktueller Imagebuild,
kein Container-/Cgroup-/OOM-/SIGKILL-Gesamtnachweis und keine Hosted-CI behauptet.

Die neue Suite belegt insbesondere:

1. Ohne passende aktuelle Betreiberfreigabe keine Driveroperation; ein Pushereignis
   ersetzt diese nicht. Unkontrollierte Trigger, fremde Ressource, veränderte
   Persistenz und nicht gefencete externe Annahme führen zu Ablehnung.
2. Echter laufender Job und jede noch nicht terminale Annahme verhindern den Wechsel;
   zuvor akzeptierte Queuejobs laufen im Drain seriell fertig, neue Jobs/Starts
   scheitern. Keine Cancellation durch das Gate.
3. Zwischen Idleprüfung und Driveraufruf kann auch ein anderer OS-Prozess keinen
   Auftrag committen; bereits berechnete Previews umgehen die Sperre nicht.
4. Fehlender/staler Worker, unbekannte DB, Quarantäne, gehaltene Guardianlocks,
   fehlendes/defektes/zu tief verschachteltes Journal und unsichere Dateirechte
   bleiben gesperrt. Ein Pflichtgate erzeugt bei fehlendem Root/DB keine Ersatzqueue.
5. Tatsächlicher Koordinatorprozessverlust hinterlässt `deploying` und geschlossene
   Annahme; eine weitere Koordinatorsitzung ist ausgeschlossen. Pausierter neuer
   Worker verwendet dieselbe Queue, ohne überlappenden Zweitworker.
6. Fehlgeschlagene Health-/Readiness-/Versions-/Instanz-/Scopeprüfung führt zu
   kontrollierter Recovery. Ein bekannter ungesunder UIstand kann mit **neuer**
   genauer Freigabe zurückgerollt werden; danach braucht es wieder Resume.
7. Nach gesundem Wechsel bleibt die Annahme zu. Ablauf der Resume-Freigabe während
   der Liveprobe verhindert Öffnen. Erst neue gültige Freigabe plus frische
   Livebeobachtung, Idle und Journalprüfung erlauben Wiederaufnahme.
8. Der bestehende vollständige C22-Backup-/Restoreweg erhält das Journal und
   hält die isolierte Kopie inaktiv. Synthetische separate Pilotdateien sind
   byteidentisch, bestehende DB-Tabellen/Schemata unverändert. Reale Week-0-Daten
   oder laufende Pilotprozesse wurden nicht ausgelesen.

Der bekannte C18-Fall bleibt
`tests/test_workflow_http.py::test_versioned_schema_snapshots_and_original_c16_models`.
Er ist auch auf einem exakten `git archive` des heutigen master `e581e20` mit
demselben Interpreter reproduziert; keine neue Gateregression. Seine alten
Workflow-/Artifact-Snapshots wurden nicht angepasst. Der neue optionale C16-
Settingsparameter wurde dagegen gezielt in **seinem** bestehenden Snapshot ergänzt.

## Fehlversuche und Umgebungsgrenzen

- Früher Gate-Lauf: 28 bestanden. Erweiterter Entwicklungslauf: 44 bestanden,
  ein Test-`NameError` wegen fehlendem `LOCK`-Import; korrigiert, keine Runtimegrenze
  gelockert. Weitere erfolgreiche Zwischenläufe sind nicht zur Endsumme addiert.
- Erster breiter 152er-Lauf ohne globales RAM-Tmp: 143 bestanden, sieben Failures,
  zwei Fixtureerrors. Darunter der gezielt nachzutragende neue Settings-Snapshot,
  der bekannte C18-Snapshot sowie Import-/Indexfehler auf dem beeinträchtigten
  lokalen Tempdateisystem. Der Importfall scheiterte auch auf unverändertem master;
  mit `TMPDIR=/dev/shm` und korrigiertem neuen Settings-Snapshot besteht die breite
  Auswahl bis auf den bekannten C18-Fall vollständig.
- Ein später 59er-Konkurrenzlauf: 58 bestanden, ein Drain-Test scheiterte beim
  Erreichen der Phase. Das Journal bewies, dass noch kein Drain/Wechsel begonnen
  hatte. Ursache war die nicht blockierende Kollision mit Statusabfragen.
  Begrenzte zweisekündige Koordinatorwartezeit und neue deterministische
  Konkurrenz-/Freigabeablauftests korrigieren dies; abschließende 66er-Suite grün.
- Ein erster Baseline-Export lief irrtümlich mit System-Python 3.11 und dessen
  abweichender tarfile-API; null Tests im daraufhin leeren Export. Danach exakter
  Export mit vorhandenem Python 3.12 und tatsächliche Baselineläufe. Keine Daten
  wurden adoptiert oder tatsächliche Regressionsassertionen abgeschwächt.

Die neue vollständige Browser-/TLS-/OIDC-Wiederholung ist **nicht bestanden**:
erster Versuch bestand die native synthetische TLS-API und Auth-Negativtests,
scheiterte dann am Dockerstart. Ein separater minimaler Start des gepinnten
Traefik-Images (`version`, `network=none`) reproduziert Exit 125 mit
`failed to mount ... overlay ... no space left on device`. Zweiter Versuch
endete vor Backendready: der vorhandene Helfer verwendet für Frozen-Fixtures
im bereinigten Childenvironment weiterhin das betroffene `/tmp` und meldet
`UnverifiedBinding`, im Treiber als `JSONDecodeError` sichtbar. Keine aktuelle
16/16- oder Containerabnahme daraus abgeleitet. Frühere erfolgreiche JSONberichte
bleiben historische Belege. Keine Image-/Volumebereinigung, zweiter Dockerdaemon
oder produktive Umgehung zur Erzeugung eines grünen Ergebnisses.

## Reproduktion auf einer lokalen Testmaschine

Vorhandene geprüfte Interpreter explizit angeben, neue Basetemps/Ergebnisdateien
wählen; niemals auf dem Produktivhost und keine echten Configs/Pilotroots einsetzen:

```sh
TMPDIR=/dev/shm PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  "$C26_BACKEND_PYTHON" -m pytest -q -p no:cacheprovider \
  tests/test_deployment_gate.py --basetemp="$C26_NEW_GATE_TEST_ROOT"
```

Breiter Lauf zusätzlich mit `tests/test_worker_image_content.py`,
`tests/test_https_preflight.py`, `tests/test_job_control.py`, `tests/test_job_executor.py`,
`tests/test_deployment_operations.py`, `tests/test_deployment_transport.py`,
`tests/test_content_import_jobs.py`, `tests/test_content_index_jobs.py`,
`tests/test_workflow_http.py`. Separater Pilotlauf:
`tests/test_cs50_batch_worker.py`, `tests/test_runtime_paths.py`,
`tests/test_c26_integrated_pipeline.py`. Die UIprüfungen bleiben die bestehenden
Unittestdateien `test_https_security.py` und `test_container_runtime.py`.

## Git, Aufbewahrung und Übergabe

Primärcheckouts `gmp_compliance` und `personal-assistant-ui` blieben sauber und
unverändert. Bestehende fremde Arbeitskopien, Mergekonflikte, Stashes, Venvs,
Snapshots, Daten und Images wurden nicht bereinigt. Die schon bekannte lokale
Git-/Dateisystemschreibstörung verhindert das Ersetzen gemeinsamer Trackingrefs
und teilweise neuer Branchrefs; geladene Commitobjekte und live Remoteheads wurden
stattdessen verifiziert. Kein Trackingref wurde als aktueller Default ausgegeben.

Neue auftragseigene Entwicklungsworktrees: `Personal_Assistant-c26-gate` (detached
auf Backendbasis, mit eigenem Diff) und `personal-assistant-ui-c26-gate` (UIbasis,
nur Dokuänderung). Ein erster regulärer Backendcommit bestand alle Hooks;
sein anschließender Objektimport in das gemeinsame lokale Git scheiterte ebenfalls
an ENOSPC. Deshalb wurden keine zusätzlichen sauberen Reviewworktrees angelegt
und keine erfolgreiche lokale Branch-/Indexaktualisierung behauptet.

Die regulären Commits mit aktiven bestehenden Backendhooks werden stattdessen
in auftragseigenen RAM-Gitmetadaten erstellt und von dort direkt auf die neuen
Reviewbranches `feat/c26-worker-deployment-gate` veröffentlicht. Je Worktree wird
zusätzlich `.review-artifacts/review.bundle` außerhalb des Commits gesichert und
mit Git geprüft; es enthält nur die eigenen neuen Commitobjekte und benötigt den
oben genannten jeweiligen Basiscommit. Das Bundle und die Quellarbeitskopien
bleiben erhalten. RAM-Metadaten sind kein rebootfester Speicher; Remote-PR und
Bundle sichern die tatsächlichen Commits dauerhaft. Ein normaler Import in lokale
Gitobjektspeicher ist nach Behebung der Dateisystemstörung nachzuholen. Keine
Manipulation vorhandener Indizes/Refs, kein Force-Push, Reset oder Prune.

Die Review-PRs bleiben ungemergt, ohne Auto-Merge. Deshalb bleiben die eigenen
Arbeitskopien/Referenzen erhalten; dauerhafte Integration in master/main und
Lifecyclecleanup sind ausdrücklich ausstehend. Alle Produktivinformationen aus
der [Betreiberliste](deployment_gate.md#betreiberinventur-und-späterer-ablauf)
bleiben `operator_action_required`. Reale API, Triggerabschirmung, Erstbootstrap,
Adapterabnahme und VPN-/HTTPS-Go-live bleiben `blocked`/`not_tested`.
