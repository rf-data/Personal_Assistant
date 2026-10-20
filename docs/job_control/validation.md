# C16 – Offline-Nachweise

Umgebung: Python 3.12.12, Pydantic 2.13.4, Pytest 9.1.1, Ruff 0.16.3.
Keine neue Dependency, keine Installation/Downloads und keine Lockfileänderung.

```bash
python -m pytest -q tests/test_job_control.py tests/test_job_executor.py
ruff check src/job_control scripts/job_control.py scripts/job_control_demo.py \
  tests/test_job_control.py tests/test_job_executor.py tests/helpers/job_control_probe.py
ruff format --check src/job_control scripts/job_control.py scripts/job_control_demo.py \
  tests/test_job_control.py tests/test_job_executor.py tests/helpers/job_control_probe.py
python -m scripts.job_control_demo --output /tmp/neue-c16-demo
git diff --check
```

Die Tests verwenden neue private temporäre Verzeichnisse, synthetische Hash-
Kataloge und Tokens. Netzwerkverbindungen im Testprozess und in den echten
Adaptern sind gesperrt. Der echte HTTP-Handler wird mit Byte-Streams geprüft,
ohne TCP-Socket, Browser, API-Schlüssel, Server oder produktive Daten.

Abdeckung: zwei echte Adapter, negative Quality-Gate-Ergebnisse inklusive Report,
feste Registry/Schemas, ungültige Scopes/Prozesse/Parameter, Preview ohne
Runneraufruf im Request, Bestätigung, authentifizierte Viewer-/Operator-/Owner-
Prüfungen, Kursfreigaben einschließlich Metrics/Logs/Artefakten, Idempotenz bei
parallelen Requests und nach Neustart, Statuswechsel, unbekannter Fortschritt,
Queues/Joblimits, Workspacekonflikte und No-Overwrite, Quellenhashes und Symlinks.

Linux-Prozessprüfungen führen ausschließlich feste Repo-Einträge bzw. explizite
synthetische Fault-Probes aus: Exit 7, Timeout, TERM/KILL-Eskalation, laufender
Root mit Kind, bereits beendeter Root mit verwaistem Kind, Parent-death-Cleanup,
echter hart beendeter Executor, Singleton-flock, Reconciliation ohne Retry und
persistente Quarantäne bei nicht bestätigter Ausführungskontrolle. Ein fremder
Kontrollprozess bleibt bei Gruppen-Cleanup unverändert. Tatsächliche RLIMIT-
Werte werden im begrenzten Childprozess geprüft.

Weitere Tests: SQLite-Initialisierung aus parallelen Aufrufern, abgewiesene
unveränderte fremde Datenbank, Logcursor/Bytegrenze, fehlender Worker, laufender
Job über neuen Controller/API-Objektstart, widerrufene Dispatchfreigaben,
versionierter Schema-Snapshot und C15-Namens-/Labelkompatibilität mit einer
ausdrücklich referenzierten veröffentlichten Testfixture.

## Abschlussprüfungen

Basis: aktueller `master` bei `b58f63c`, einschließlich des gemergten C15-Pakets.
**211 Tests bestanden**: 53 C16-Tests, 50 C15-Metrik-/Monitoring-Tests und
108 bestehende Material-/Quality-/Mapping-/Contract-/Inventorytests.
Ruff Check und Ruff Format Check bestanden für alle 16 Pythondateien des Pakets.

```bash
python -m pytest -q tests/test_job_control.py tests/test_job_executor.py \
  tests/test_pipeline_metrics.py tests/test_monitoring_config.py \
  tests/test_cs50_material_quality.py tests/test_cs50_material_processing.py \
  tests/test_cs50_material_mapping.py tests/test_cs50_material_contracts.py \
  tests/test_cs50_material_inventory.py
```

Der separate Worker-CLI-Prozess führt echte Adapterjobs aus; ein neu erzeugtes
API-Objekt liest dabei dieselbe persistente Historie. Der Beispielreport enthält
zwei tatsächlich vollständig ausgeführte synthetische Offlinejobs mit Exit 0,
Zeitpunkten, finalen Logereignissen und SHA-256-Artefaktreferenzen.

Der parallele Starttest zeigte eine SQLite-WAL-Initialisierungsrace. Ein eigener
zeitlich begrenzter Bootstrap-flock serialisiert jetzt Schema-/WAL-Initialisierung;
vier gezielte Wiederholungen von paralleler Initialisierung und echter begrenzter
Jobausführung bestanden. Eine frühere einzelne Kontrollunterbrechung ist keinem
bewiesenen Fehlergrund zugeordnet; sie führte sicher zur persistenten Quarantäne.
Doppelte Wiederholungen sind keine zusätzliche Testabdeckung.

Nicht ausgeführt: produktiver Server-/DB-/Workerzugriff, Netzwerk-/LLM-/Download-
Jobs, echter HTTP-TCP-Listen-/TLS-/Proxytest, Docker-Build/Run/Pull, Coolify oder
Hetzner, Deployment, Migration oder produktiver Secretzugriff. Der lokale
HTTPServer ist keine Produktionsfreigabe. Betrieb und verbleibende Plattform-
grenzen sind in [operations.md](operations.md) und [integration.md](integration.md) beschrieben.
