> Historischer G/H-Quellnachweis aus dem übernommenen Arbeitsstand; keine neue Livefreigabe. Aktuelle Betreiberanweisungen: [C26-Pilotchecks](c26_pilot_operator_checks.md). Neue Testbilanz: [Pilotvalidierung](c26_pilot_validation.md).

# C26-H – Validierung, Prozessanalyse und technische Übergabe

25.10.2026. **Produktion HOLD. Technisch vorbereitet, Gitintegration ausstehend.**
Keine echte Serververbindung, kein Deployment, Containerstart, Image-/Modellpull,
Merge oder produktiver Gate-/Datenbankzugriff. Testdatenbanken und Prozesse sind
lokale synthetische Fixtures. Native Dockeraufrufe waren ausschließlich `compose config`.

## Rekonstruierter Stand und Quellen

Zugewiesener Worktree: `/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26h`,
Branch `feat/c26h-controlled-integration`, unveränderter HEAD
`778367396cd52526eca59edd41c2367f5e43b897`. Das Arbeitsverzeichnis enthielt bereits
D/E/F-Import, alle zehn G-Dateien, Launcherbindings, Templates, H-Tests und zwei
H-Berichte. Diese Arbeit wurde erhalten. Der alte 594er-Lauf besitzt einen
vollständigen JUnitreport; der angefangene H-Integrationslauf hatte nur eine
Snapshotankündigung, keinen Ergebnisreport und keinen noch laufenden Testprozess.
Letzterer musste wieder aufgenommen werden. Kein erfolgreicher Baselinelauf wurde
pauschal neu gestartet; gezielte Wiederholungen betreffen geänderte Fixtures,
fehlende Nachweise und die ausdrücklich beauftragte P1/P2-Untersuchung.

D `8b0ba2d4ab5d0cd6fc8dfa69783276efd929666f` ist Vorfahr von E
`28e9a608d74270278cf037e35957d0bae08d50b2`, E von F
`7ffb4ed6fd4d8433edf36fb4851a382b9b9c595d`. Der kumulative Diff vom gemeinsamen
Vorfahren `e68275205fefb7a5f6db42bc45060e505bfcefb5` wurde genau einmal übernommen.
Alle 91 F-Pfade waren beim Import bytegleich; abschließend enthält nur ein
übernommener Test eine ausdrücklich ausgewiesene Importsortierung. Die zehn
G-Pfade stimmen mit Quellarbeitsbaum, Index und ursprünglichem Importmanifest
überein, sind aber **nicht im G-Commit enthalten**. H-HEAD bleibt ebenfalls Basis.
Das ist Arbeitsdateiintegration, keine erzeugte Commitkette D→E→F→G→H.
Vollständige Hashes: [Inventar](c26h_integration_inventory.md) und
[101-Pfad-Provenienz](c26h_source_provenance.json).

## Umgebung und Schutzgrenzen

Interpreter ausschließlich lesend:
`/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c26b6-planning-results/test-env/bin/python`;
Python3.12.12, pytest9.1.1, Pydantic2.14.1, HTTPX0.28.1, PyYAML6.0.3,
PyMuPDF1.27.2.2. Das ist keine neue Installation des exakten Runtime-Locks.
Keine uv-/SDK-/Modellinstallation und kein Imagebuild. Ruff0.16.0 aus vorhandenem
Pre-commit-Cache. Quell-/Testdatenexporte bleiben unter `/tmp/c26h-*` erhalten.

Offlineprozesse verwenden deaktivierte Pluginautoload-/Cache-/Bytecodewrites,
den bestehenden Offlineguard und ausschließlich synthetische neue Roots.
Keine parallelen Prozesslastsuiten in dieser Fortsetzung. Der Guard ist keine
transitive OS-Sandbox; kontrollierte Kindprobes sind Teil des Testvertrags.
Monitoring benötigt zusätzlich lesende echte Gitmetadaten. Seine isolierten
Git-Fixturerepositories sind Testdaten, kein Umgehungsindex für den Projektgit.
Native H-Composeprüfungen verwenden isoliertes Dockerconfig und ein garantiert
nicht vorhandenes Daemonsocket; nur feste `config --format json`-Kommandos.
Coolifyrouterlabels sind dabei ausdrücklich simuliert.

## Tatsächlich ausgeführte Läufe

Zahlen überlappen. Keine Addition zu einer angeblich vollständig grünen Suite.
„Errors“ sind Setupfehler, keine Sammlungsausfälle; alle hier beendeten Läufe
hatten null Collection-Errors.

| Lauf | Passed | Failed | Setup-Errors | Skipped | Deselected | Zeit / Beleg |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Vorher: importierter D/E/F/G/C16-Verbund | 594 | 0 | 0 | 0 | 1 | 253,33 s; `/tmp/c26h-baseline.xml`; erhalten, nicht wiederholt |
| Vorher: vier Launcherregressionen | 0 | 4 | 0 | 0 | 0 | 28,10 s; `/tmp/c26h-launcher-before.xml`, unbekannte CLIparameter |
| Erster fortgesetzter G/H-Verbund | 63 | 1 | 0 | 0 | 0 | 35,45 s; `/tmp/c26h-offline-30eyj7t_/result.xml` |
| P1 kontrollierter Slow-start auf H vor Fix | 0 | 2 | 0 | 0 | 0 | 2,16 s; `/tmp/c26h-p1-negative-before.xml` |
| Dieselben Slow-start-Probes auf unveränderter Basis | 0 | 2 | 0 | 0 | 0 | 1,70 s; `/tmp/c26h-p1-negative-base.xml` |
| Nach Fix: C16-Executor/Controller/SQLite + H-Prozess-/Launcherfälle | **72** | **0** | **0** | **0** | **0** | 67,95 s; `/tmp/c26h-process-group.xml` |
| Zusätzliche Archive-Offlineauswahl einschließlich Git-Monitoring | 380 | 3 | 14 | 0 | 2 | 619,78 s; `/tmp/c26h-offline-lonj9c86/result.xml` |
| Monitoring im echten H-Worktree + betroffener Bootstraptest | **25** | **0** | **0** | **1** | **0** | 2,32 s; `/tmp/c26h-metadata-bootstrap.xml` |
| Native H-Composekonfiguration | **7** | **0** | **0** | **0** | **0** | 5,72 s; `/tmp/c26h-compose.xml` |
| Abschließender G/H-Verbund nach allen Codekorrekturen | **66** | **0** | **0** | **0** | **0** | 57,11 s; `/tmp/c26h-offline-dnhe6mmk/result.xml` |

Die 66 umfassen G29, H-Launcher12, H-Integrations23 und die beiden neuen
Slow-start-Probes. Die sieben nativen H-Composefälle sind separat. Der
Monitoring-Skip ist ausschließlich
`tests/test_monitoring_config.py::test_native_compose_default_and_all_profiles`,
Grund `External integration requires --run-external`. Dieser Monitoring-CLItest
wurde hier nicht ausgeführt; die sieben H-Renderfälle ersetzen ihn nicht.

Der erste H-Fehler war die eigene Testannahme
`test_managed_configuration_fails_closed[public]`: die korrekte private
Dateiablehnung ist `src.content_store.errors.IntegrityError`, nicht ValueError/
OSError. Nur der erwartete konkrete Exceptiontyp wurde ergänzt. Alle negativen
Assertions und die Produktprüfung bleiben erhalten; sämtliche zwölf Launcherfälle
bestehen danach in der 72er-Gruppe und im finalen 66er-Lauf.

Die 17 Monitoringfehler des Archivelaufs sind vollständig auf fehlendes `.git`
zurückgeführt: drei Testfehler und 14 abhängige Setupfehler bei `git ls-files`
beziehungsweise `git check-ignore`, jeweils Exit128, `not a git repository`.
Es sind keine Monitoring-Sicherheitsassertions fehlgeschlagen. Der Runner führt
diese metadatengebundene Datei nun ausdrücklich nicht im Gitarchiv aus; die
vollständige Datei wurde stattdessen lesend im H-Worktree geprüft. Die übrigen
380 abgeschlossenen Fälle wurden nicht erneut ausgeführt. Historischer roter
Archivelauf bleibt sichtbar; kein xfail, pauschaler Skip oder künstlicher Gitindex.

Ein anfänglicher direkter Dateiaufruf des H-Runners scheiterte vor Sammlung mit
`ModuleNotFoundError: scripts`; der dokumentierte modulare Aufruf funktioniert.
Dies war ein Einstiegspfadproblem, kein Produkt-/Gatefehler.

## P1 – Signalablauf und nachgewiesene Fixtureursache

Exakte ursprüngliche ID:
`tests/test_job_executor.py::test_real_nonzero_timeout_cancel_and_descendant_groups[cancel-cancelled]`.
Historische Reports: `/tmp/c26g-validation-y5taxwa9/final.xml` und
`process-recheck.xml`. Im ersten Lauf 86 passed/2 failed, im Recheck 1 passed/
1 failed. Der spätere historische Basisvergleich bestand mit zwei Fällen.
Aktuelle isolierte Vorhergegenproben auf exakter H-Ausgangsbasis und H:

| Node | Basis vor Änderung | H vor Änderung |
| --- | --- | --- |
| P1 cancel-cancelled | 1 passed, 1,591 s | 1 passed, 1,923 s |
| P2 background worker | 1 passed, 7,582 s | 1 passed, 9,716 s |

Diese Probes liefen jeweils in eigenen Prozessen, ohne pauschale Retries.
Belege: `/tmp/c26h-process-checks.json`, `c26h-p1-base.xml`, `c26h-p1-h.xml`,
`c26h-p2-base.xml`, `c26h-p2-h.xml`. Basisquellen unter dem in
`/tmp/c26h-process-base-path` gespeicherten neuen Archivroot; nur für die spätere
Vergleichsprobe wurde dort die neue Testdatei ergänzt, kein Basisprodukt geändert.

Der echte Guardian startet eine neue Session/Prozessgruppe, hält den direkten
Child unreaped als Gruppenidentität, sendet TERM, wartet maximal 0,4 s und sendet
anschließend KILL. Subreaper/Parentdeath und bestätigtes Reaping bleiben erhalten.
Ein Root, der schon an TERM stirbt, behält Exit -15, auch wenn anschließend KILL
an dessen Gruppe geht. -9 wird nur garantiert, wenn der bekannte Probeprozess
TERM zu diesem Zeitpunkt tatsächlich ignoriert.

Die alte Testprobe startete Cancel/Timeout nach 0,3 s ab Spawn, ohne Bereitschaft
des Root-/Childhandlers nachzuweisen. Eine kontrollierte Verzögerung von 0,6 s
vor Installation des Root-SIGTERM-Handlers reproduziert auf Basis **und** H beide
Fehler. Gesicherte Signalsequenz ist jeweils `[Gruppe,15]`, `[dieselbe Gruppe,9]`,
Ergebnis -15/cancelled beziehungsweise -15/timeout nach 0,325/0,332 s; PIDreadiness
fehlt. Beleg `/tmp/c26h-p1-race-proof.json`. Das ist ein kausaler
Racebeleg der bestehenden Testfixture, keine ausgebliebene Guardianeskalation.

Korrektur ausschließlich in `tests/helpers/job_control_probe.py`: der Child
bestätigt seinen Ignorehandler; der Root publiziert danach die vollständige
PIDliste atomar. Ein begrenzter `on_started`-Callback wartet auf diese echte
Bereitschaft, bevor die Probe Cancel/Timeout beurteilt. Die bestehende
Supervise-Timeoutverzweigung bleibt getestet. Kein produktiver Guardian,
Signalcode, Gracewert, Prozess- oder Testtimeout wurde geändert.

Neue Regressionen in `tests/test_c26h_processes.py` verlangen trotz verzögertem
Bootstrap weiterhin -SIGKILL, richtigen Grund, Dauer <5 s, TERM→KILL an genau die
bekannte Gruppe, vollständig verschwundene Root-/Child-PIDs und einen weiterhin
lebenden unabhängigen Testprozess. **Klassifikation: bestehende Fixture-Race,
B/D; sicher korrigiert.** Der ursprüngliche einzelne historische Schedulerablauf
ist nicht vollständig rekonstruierbar; seine kausale Schwachstelle ist bewiesen.

## P2 – Terminalzustand nicht innerhalb der Testfrist

Exakte ID: `tests/test_job_executor.py::test_real_background_worker_cli_and_api_lifecycle`.
Historischer Fehler an `wait_until(ended)`, unveränderte Frist acht Sekunden.
Der POST wurde mit 202 angenommen. Der Worker sollte ohne in-process Executor
queued→dispatching→offline_adapter→completed durchlaufen. Historische SQLitekopie:
`/tmp/c26g-validation-y5taxwa9/worker-forensics.sqlite3`, ausschließlich read-only
abgefragt. Persistierte UTC-Zeiten am 25.10.2026:

| Ereignis | Zeit | Bedeutung |
| --- | --- | --- |
| Annahme queued | 17:52:52,792547 | Eigene synthetische Anfrage |
| Claim dispatching | 17:52:53,189069 | Worker hat Arbeit übernommen |
| Adapter gestartet | 17:52:55,515326 | Kein Beleg eines vor Dispatch blockierten Workers |
| interrupted, Exit -15 | 17:53:01,980926 | `Supervisor interrupted`; nach Testfrist und Cleanup |

Die Adapterdauer beträgt 6,298 s bis zur Unterbrechung. Nach Ablauf von
`wait_until` terminiert das `finally` den CLIworker, dessen Guardian den Payload
beendet und das bestätigte interrupted-Ergebnis protokolliert. Kein natürlicher
Completedzeitpunkt ist erhalten. Daher lässt sich aus diesem Snapshot nicht
entscheiden, ob bloß die Testfrist zu kurz für diese Ausführung war oder eine
vorübergehende Blockade vorlag. Keine belegte Quarantäne, SQLITE_BUSY-Ausnahme
oder dauerhafte Deadlockursache. Transiente SQL-Locks bleiben unbewiesen.

Der Worker pollt zwischen `step()`-Aufrufen mit 0,1 s; Guardianpolling liegt bei
0,03 s. Storeverbindungen besitzen bereits eine begrenzte Zwei-Sekunden-
Vortransaktionsbehandlung bestimmter SQLITE_BUSY-Fälle. Das ist kein allgemeiner
Retry von Transaktionen. Der Planningprozess hat einen eigenen 30-Sekunden-
Laufzeitvertrag; die Testfrist acht Sekunden ist ein separates Testbudget.
Keiner dieser Werte wurde verändert. Die D/F-Gatepfade verlangen hier keine
neue Journal-/Witnessoperation, solange diese synthetische Fixture nicht enrolled
ist. Gemeinsame Datenroots oder eine konkrete Reihenfolge-/Lastursache wurden
nicht nachgewiesen.

P2 bestand isoliert auf Basis und H sowie nach P1-Korrektur in der 72er-Gruppe
mit Controller-/Storecontention-/Executorfällen. **Klassifikation: historischer
nicht reproduzierbarer Prozessfehler, Ursache E offen.** Kein bestätigter
H-Regressionsbeweis, aber auch keine behauptete Ursachenreparatur. Kein Timeout
angehoben, keine Terminalassertion, Cancellation- oder Quarantäneregel gelockert.
Folgeschritte und Freigabegrenze stehen in den verbleibenden Gates.

## Geprüfte und nicht geprüfte Komponenten

Geprüft: D-Admisson/Dispatch/Drain/v2/Recovery, E-MockTransport/Nonce/Pin-/Freshness-
und Capturetrennung, F-Grant/CAS/Epoch/Crash/Lock/Claim und inerter Rollback,
G-Verbundrestore mit neuen Roots, interrupted-Job und Idempotenz, H-Bindungen/
Hardening/negative Konfigurationen, C16-Lifecycle/SQLitecontention, Content-/Blob-/
FTS-/Import-/Index-/Review-/PDFrestore-/Workflow-/Parsing- und Isolationsregressionen.
Der breite Lauf hat diese Komponenten geprüft, aber seine Metadatenfehler bleiben
als tatsächliches rotes Resultat bestehen.

Nicht ausgeführt: gesamte Repositorysuite, UIrepo-/Browser-/echte OIDC-/TLS-/VPN-
E2E, echte Collectorproducer/Registryattestation, vollständige SDK-/Modellprofile,
Runtimeimagebuild/Lockinstallation, Container-/cgroup-/OOM-/Hostbetrieb,
produktiver EvaluationStore-Verbundadapter, Offsite/RPO/RTO, echte Alarme,
produktiver Witness/Verifier/Driver und irgendein Deployment.

Weitere historische rote G-Probe:
`/tmp/c26g-offline-5b8h0g7z/result.xml` zeigt bei
`tests/test_job_executor.py::test_quality_failure_retains_structured_report`
failed mit Exit3 statt erwartetem Exit1. Der vorhandene 594er-H-Basislauf und
die aktuelle Executorgruppe bestehen diesen Fall. Kein kausaler SQLitebefund
oder Ursachenfix daraus ableitbar; separat von P1/P2 und den älteren
MAINT-Quarantäne-/Hardlinkfällen offenhalten.

## Reproduktion und Paketabschluss

Profile und manuelle Git-/Stagingschritte: [Runbook](c26h_staging_runbook.md).
Gezielte C16-/Launchergruppe:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  "$C26H_PYTHON" -B -m pytest -q -o addopts= -p no:cacheprovider \
  -p tests.offline_guard tests/test_c26h_processes.py tests/test_job_executor.py \
  tests/test_job_control.py tests/test_job_store_contention.py tests/test_c26h_runtime.py
```

Ruff Check und Formatcheck aller 38 geänderten Pythondateien sowie deren
Python3.12-ASTprüfung bestehen. Sämtliche geänderten JSON-/YAMLdateien wurden
geparst; alle zwölf relativen Links der sechs H-Berichte und die
Whitespaceprüfung bestehen ebenfalls. Die sechs H-Berichte sind Inventar,
Integrationsplan, Runtimebootstrap, dieses Validierungsdokument, verbleibende
Gates und Stagingrunbook. Provenienz-JSON ist ihr maschinenlesbarer Anhang.

Gemeinsame Gitmetadaten bleiben schreibgeschützt. Kein Commit/Push/PR/Merge,
kein Umgehungsindex und keine Änderung bestehender Branches. Vollständige
Übergabe unter `/tmp/c26h-delivery/`: Patch relativ zur exakten Basis,
Datei-/Quell-/Patchhashmanifest und NUL-separierte explizite Stagingpfade.
Forward/Reverse-Check, tatsächliche Anwendung in einer neuen Basiskopie und
byteweiser Vergleich aller Ziel-/Basisdateien werden im Paket protokolliert.
Worktree/Branch bleiben wegen fehlender Integration erhalten. Keine Bereinigung
fremder Worktrees, Gitobjekte, Stashes, Umgebungen oder Daten. AGENTS.md-
Defaultbranchintegration bleibt ausstehend; kein vollständig integrierter Abschluss.

## Historische P1-/P2-Tracebacks (vollständig aus JUnit)

Quelle `/tmp/c26g-validation-y5taxwa9/final.xml`; Inhalt unverändert, abschließende Leerzeichen entfernt.
Die Originalreports bleiben unter `/tmp` erhalten; dieser Anhang sichert ihre
wesentlichen Fehlerbelege dauerhaft im vorgesehenen Bericht.

### test_real_nonzero_timeout_cancel_and_descendant_groups[cancel-cancelled]

```text
tmp_path = PosixPath('/tmp/c26g-validation-y5taxwa9/final-data/test_real_nonzero_timeout_canc1')
mode = 'cancel', reason = 'cancelled'

    @pytest.mark.parametrize(
        "mode,reason",
        [
            ("timeout", "timeout"),
            ("cancel", "cancelled"),
            ("exit", None),
            ("orphan_exit", None),
        ],
    )
    def test_real_nonzero_timeout_cancel_and_descendant_groups(tmp_path, mode, reason):
        # An unrelated direct child is outside the probe's process ancestry/group.
        unrelated = subprocess.Popen(
            [sys.executable, "-c", "import time;time.sleep(30)"], start_new_session=True
        )
        try:
            result = subprocess.run(
                [sys.executable, str(PROBE), mode, str(tmp_path)],
                env=clean_environment(),
                capture_output=True,
                timeout=10,
            )
            assert result.returncode == 0, result.stderr
            code, observed, duration = json.loads(
                (tmp_path / "probe-result.json").read_text()
            )
            assert observed == reason and duration < 5
>           assert code == (
                7 if mode == "exit" else 0 if mode == "orphan_exit" else -signal.SIGKILL
            )
E           assert -15 == -9

tests/test_job_executor.py:63: AssertionError
```

### test_real_background_worker_cli_and_api_lifecycle

```text
setup = namespace(settings=Settings(schema_version=1, root=PosixPath('/tmp/c26g-validation-y5taxwa9/final-data/test_real_backg...n object at 0x7f6415732f00>, tmp=PosixPath('/tmp/c26g-validation-y5taxwa9/final-data/test_real_background_worker_cl0'))

    def test_real_background_worker_cli_and_api_lifecycle(setup):
        config = setup.tmp / "worker-config.json"
        config.write_text(setup.settings.model_dump_json())
        child = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "scripts.job_control",
                "worker",
                "--config",
                str(config),
            ],
            cwd=REPOSITORY,
            env=clean_environment(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        try:
            wait_until(
                lambda: setup.controller.store.worker_available(setup.settings.worker_ttl)
            )
            from test_job_control import request_data

            from scripts.job_control_demo import DEMO_TOKEN

            body = request_data(setup)
            headers = {
                "Authorization": "Bearer " + DEMO_TOKEN,
                "Idempotency-Key": "background_worker_request_0",
            }
            app = Application(setup.controller)
            status, raw, _ = app.request(
                "POST", "/v1/jobs", headers, json.dumps(body).encode()
            )
            assert status == 202
            job_id = json.loads(raw)["job_id"]
            # No in-process Executor.step: the separate CLI worker must do all work.
            app = Application(Controller(setup.settings))

            def ended():
                code, raw, _ = app.request("GET", "/v1/jobs/" + job_id, headers)
                assert code == 200
                return json.loads(raw)["status"] in {"completed", "failed", "interrupted"}

>           wait_until(ended)

tests/test_job_executor.py:354:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

predicate = <function test_real_background_worker_cli_and_api_lifecycle.<locals>.ended at 0x7f641551a0c0>
timeout = 8

    def wait_until(predicate, timeout=8):
        until = time.monotonic() + timeout
        while time.monotonic() < until:
            if predicate():
                return
            time.sleep(0.02)
>       pytest.fail("Bounded process condition not reached")
E       Failed: Bounded process condition not reached

tests/test_job_executor.py:34: Failed
```


## Nebenläufiger gemeinsamer Git-Zustand

Alle beim Wiederaufnehmen vorhandenen Referenzen und Worktreeeinträge sowie
Stashes bleiben unverändert. Im gemeinsamen Git ist während dieser Fortsetzung
zusätzlich `feat/c24r-retrieval_completion` mit
`4c057ae33d41ba98e227879cc8a51283338e4a0b` und Worktree
`/home/robfra/0_Portfolio_Projekte/Personal_Assistant-c24r` aufgetaucht. Diese
Artefakte wurden nicht durch C26-H angelegt, bearbeitet oder entfernt.
Deshalb wird keine vollständige Identität der gesamten Vorher-/Nachherliste
behauptet. Die gepinnten H-/D/E/F/G-/Defaultheads und die zehn G-Quellhashes
sind weiterhin unverändert. Keine Rücksetzung fremder Nebenläufigkeit.

## Vollständige Änderungsliste relativ zur H-Ausgangsbasis

90 Dateien; 38 Pythondateien. Der kumulative Quellimport zählt auch
Pfade, die bereits bytegleich in der H-Basis lagen; das Paket enthält dagegen
genau alle tatsächlich geänderten oder neuen Pfade relativ zu HEAD.

| Datei | Herkunft / H-Anteil |
| --- | --- |
| `deployment/Dockerfile` | Kumulativer F-Import einschließlich D/E |
| `deployment/Dockerfile.dockerignore` | Kumulativer F-Import einschließlich D/E |
| `deployment/c26-runtime.controller.json.example` | Kumulativer F-Import einschließlich D/E |
| `deployment/c26-runtime.limits.json.example` | Kumulativer F-Import einschließlich D/E |
| `deployment/c26g.staging.controller.json.example` | G: neuer lokaler Index-/Arbeitsdateistand ohne G-Commit |
| `deployment/c26h.staging.compose.yaml` | C26-H |
| `deployment/c26h.staging.content.json.example` | C26-H |
| `deployment/c26h.staging.review.json.example` | C26-H |
| `deployment/c26h.staging.search.json.example` | C26-H |
| `deployment/c26h.staging.ui.compose.yaml` | C26-H |
| `deployment/coolify.runtime-bootstrap.compose.yaml` | Kumulativer F-Import einschließlich D/E |
| `docker/DockerFile.worker` | Kumulativer F-Import einschließlich D/E |
| `docker/DockerFile.worker.dockerignore` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/architecture.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/c26_gate_validation.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/c26_runtime/README.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/c26_runtime/coolify_compatibility.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/c26_runtime/coolify_driver_plan.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/c26_runtime/deployment_trigger_audit.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/c26_runtime/diagnostics.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/c26_runtime/draft_consolidation_report.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/c26_runtime/driver_contract.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/c26_runtime/integration_matrix.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/c26_runtime/operator_binding_check.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/c26_runtime/operator_checks.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/c26_runtime/resource_matrix.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/c26_runtime/resources.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/c26_runtime/rollout.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/c26_runtime/runtime_configuration.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/c26_runtime/runtime_observer_report.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/c26_runtime/source_assessment.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/c26b_validation.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/c26d_gate_v2.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/c26e_runtime_collector.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/c26f_deployment_coordinator.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/c26g_go_no_go.md` | G: neuer lokaler Index-/Arbeitsdateistand ohne G-Commit |
| `docs/deployment/c26g_integration_validation.md` | G: neuer lokaler Index-/Arbeitsdateistand ohne G-Commit |
| `docs/deployment/c26g_operator_decisions.md` | G: neuer lokaler Index-/Arbeitsdateistand ohne G-Commit |
| `docs/deployment/c26g_readiness_matrix.md` | G: neuer lokaler Index-/Arbeitsdateistand ohne G-Commit |
| `docs/deployment/c26g_runbook.md` | G: neuer lokaler Index-/Arbeitsdateistand ohne G-Commit |
| `docs/deployment/c26h_integration_inventory.md` | C26-H |
| `docs/deployment/c26h_integration_plan.md` | C26-H |
| `docs/deployment/c26h_remaining_gates.md` | C26-H |
| `docs/deployment/c26h_runtime_bootstrap.md` | C26-H |
| `docs/deployment/c26h_staging_runbook.md` | C26-H |
| `docs/deployment/c26h_validation.md` | C26-H |
| `docs/deployment/configuration.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/deployment_gate.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/https.md` | Kumulativer F-Import einschließlich D/E |
| `docs/deployment/operations.md` | Kumulativer F-Import einschließlich D/E |
| `docs/job_control/contract.v1.json` | Kumulativer F-Import einschließlich D/E |
| `scripts/c26_runtime_preflight.py` | Kumulativer F-Import einschließlich D/E |
| `scripts/c26g_offline_validation.py` | G: neuer lokaler Index-/Arbeitsdateistand ohne G-Commit |
| `scripts/c26g_preflight.py` | G: neuer lokaler Index-/Arbeitsdateistand ohne G-Commit |
| `scripts/c26h_offline_validation.py` | C26-H |
| `scripts/c26h_preflight.py` | C26-H |
| `scripts/deployment.py` | C26-H |
| `scripts/deployment_gate.py` | Kumulativer F-Import einschließlich D/E |
| `scripts/worker_image_smoke.py` | Kumulativer F-Import einschließlich D/E |
| `src/job_control/controller.py` | Kumulativer F-Import einschließlich D/E |
| `src/job_control/coolify_observer.py` | Kumulativer F-Import einschließlich D/E |
| `src/job_control/coolify_readiness.py` | Kumulativer F-Import einschließlich D/E |
| `src/job_control/coordinator_contracts.py` | Kumulativer F-Import einschließlich D/E |
| `src/job_control/coordinator_state.py` | Kumulativer F-Import einschließlich D/E |
| `src/job_control/deployment_coordinator.py` | Kumulativer F-Import einschließlich D/E |
| `src/job_control/deployment_gate.py` | Kumulativer F-Import einschließlich D/E |
| `src/job_control/deployment_scope.py` | Kumulativer F-Import einschließlich D/E |
| `src/job_control/executor.py` | Kumulativer F-Import einschließlich D/E |
| `src/job_control/models.py` | Kumulativer F-Import einschließlich D/E |
| `src/job_control/operations.py` | Kumulativer F-Import einschließlich D/E |
| `src/job_control/runtime_collector.py` | Kumulativer F-Import einschließlich D/E |
| `src/job_control/store.py` | Kumulativer F-Import einschließlich D/E |
| `tests/fixtures/c26e/public-test-leaf.pem` | Kumulativer F-Import einschließlich D/E |
| `tests/helpers/job_control_probe.py` | C26-H |
| `tests/test_c26_runtime_bootstrap.py` | Kumulativer F-Import einschließlich D/E; H: Importsortierung |
| `tests/test_c26_runtime_preflight.py` | Kumulativer F-Import einschließlich D/E |
| `tests/test_c26g_readiness.py` | G: neuer lokaler Index-/Arbeitsdateistand ohne G-Commit |
| `tests/test_c26g_restore.py` | G: neuer lokaler Index-/Arbeitsdateistand ohne G-Commit |
| `tests/test_c26h_compose.py` | C26-H |
| `tests/test_c26h_integration.py` | C26-H |
| `tests/test_c26h_processes.py` | C26-H |
| `tests/test_c26h_runtime.py` | C26-H |
| `tests/test_coolify_observer.py` | Kumulativer F-Import einschließlich D/E |
| `tests/test_coolify_readiness.py` | Kumulativer F-Import einschließlich D/E |
| `tests/test_coordinator_contracts.py` | Kumulativer F-Import einschließlich D/E |
| `tests/test_deployment_coordinator.py` | Kumulativer F-Import einschließlich D/E |
| `tests/test_deployment_gate.py` | Kumulativer F-Import einschließlich D/E |
| `tests/test_deployment_gate_v2.py` | Kumulativer F-Import einschließlich D/E |
| `tests/test_deployment_transport.py` | Kumulativer F-Import einschließlich D/E |
| `tests/test_runtime_collector.py` | Kumulativer F-Import einschließlich D/E |


## Schlussprüfung des Übergabepakets

Vollständiger Patch einschließlich aller neuen/unversionierten Dateien; keine
Index-/Refmutation. Vorwärtsprüfung und tatsächliche Anwendung auf einer neuen
Archivkopie der exakten H-Basis, SHA-256-/Byte-/Modusvergleich aller Zielpfade,
Prüfung unveränderter übriger Basisdateien sowie Rückwärtsprüfung und tatsächliche
Rückkehr zum identischen Basistree sind Bestandteil des Paketmanifests.
Alle sechs dauerhaften H-Berichte und der Provenienzanhang sind enthalten.
Der Patch ersetzt weder Commit, Review, Defaultbranchintegration noch eine
Produktionsfreigabe. Branch/Worktree und eigene Test-/Forensikartefakte bleiben
wegen des Integrationsblockers erhalten.
