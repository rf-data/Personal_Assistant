# C22 Abnahme – 17.10.2026

Ergebnis: lokale Betriebsverträge, Konfigurationsprüfungen und synthetische
Recoverytests bestanden. **Keine Produktionsfreigabe.** Keine Images gepullt,
Dependencies installiert, Server/Datenbanken verändert oder Dienste deployed.
Maschinenlesbar: [c22_report.v1.json](c22_report.v1.json).

| Prüfung | Ergebnis / Grenze |
| --- | --- |
| Backend | 148 verschiedene Tests bestanden, 0 Skip; vier ergänzende Läufe, überlappende Fälle einmal gezählt |
| UI | 123 Tests bestanden, 0 Skip mit expliziten C16-Backendpfaden; initialer Standardlauf übersprang vier optionale Integrationen, danach vollständig ausgeführt |
| Zusätzliches Local-Integration-Profil | 9/9 Prüfpunkte bestanden, 121 tatsächliche Loopback-HTTP-Aufrufe; Streamlit AppTest, kein Browsertest |
| Ruff | alle neuen/geänderten Pythonmodule und Tests bestanden, Formatcheck bestanden |
| Compose 5.0.2 | tatsächliche CLI-Auswertung ohne Daemon: 0 Dienste ohne Profil, 4 Produktionsrollen, 6 mit optionalem Monitoring |
| Rollen/Netze/Mounts | automatisierte Assertions für UID, readonly, Capabilities, Limits, Health, private Netze, fehlende Hostports/Docker-Sockets und identische State-Mounts |
| Verwaltete Prozesse | echte getrennte API-/Workerprozesse, API- und Worker-Neustart, persistierte Idempotenz, tatsächlicher Adapterlauf und sauberer SIGTERM |
| Lokales Volume | unabhängige flock-Handles, rename/fsync, SQLite-WAL und Leser-Sichtbarkeit; keine Zielhostbehauptung |
| Backup/Restore | SQLite-Backup-API, leeres Ziel, Hash-/Artefaktprüfung, Manipulations-/No-Overwrite-Tests, Quarantäne/interrupted erhalten |
| PDF-Provenienz | synthetischer echter fünfstufiger PDF-v2-Workflow gesichert/restauriert; State-Modell/Reporthash, sämtliche Stage-Outputhashes und Receipt-Origin nachgeprüft |
| C16–C19-Regression | Jobauth/Scopes, Queue/Cancel, echte native PDF-Nachfahren, Parent-Death, Timeouts, Cleanup, Workflow-Restart/Resume und C20-B-HTTP-Vertrag bestanden |
| Fehlerumgebungen | fehlender Workspace/Config, offene Rechte, falscher Eigentümer, nicht schreibbar, geänderte Katalogbytes, Quarantäne, wenig freier Speicher; Fault Injection ohne produktive Daten |

Reproduktion mit bereits vorhandener Pythonumgebung, ohne Installation/Sync:

```sh
python -m pytest -q tests/test_deployment_operations.py \
  tests/test_deployment_transport.py tests/test_deployment_pdf_restore.py \
  tests/test_job_control.py tests/test_pdf_job_control.py \
  tests/test_pdf_workflows.py tests/test_cs50_workflows.py tests/test_workflow_http.py
python -m ruff check --no-cache src/job_control/operations.py scripts/deployment.py \
  deployment/gateway_health.py tests/test_deployment_operations.py \
  tests/test_deployment_transport.py tests/test_deployment_pdf_restore.py
# Im UI-Repository, mit explizitem Backend und dessen bestehendem Python:
C16_REPO=/absolute/backend C16_PYTHON=/absolute/backend/.venv/bin/python \
  python -m unittest discover -s tests -v
```

Der protokollierte Backend-Hauptlauf enthält 108 Tests (231.31 s), ergänzender
Operations-/HTTP-Lauf 60 (117.52 s) und abschließender Operations-/PDF-Restorelauf
25 (9.94 s). Nach finaler Ergänzung der fsync-Sicherung wurden alle 26 neuen
C22-Tests nochmals erfolgreich ausgeführt (18.13 s). Test-IDs werden überlappend dedupliziert, nicht die Laufzahlen addiert.
Die UI-Suite mit allen Integrationen lief in 135.612 s. Private XML-/JSON-/Logs
bleiben außerhalb von Git; veröffentlichter Report enthält keine Tokenbytes,
lokalen Workspacepfade oder produktiven Inhalte. Laufzeiten sind lokale
Beobachtungen, keine Serverkapazitätszusage. Die Tests sind selektierte relevante
Regressionen, keine Behauptung eines vollständig grünen historischen Gesamt-Repos.

**Blockierte Abnahmen:**

1. `docker image ls` ist leer. Keine Build-/Image-/Container-Smoketests gestartet,
   weil sie Basisimages/Dependencies benötigen würden. Keine automatischen Pulls.
2. C19 wurde als Linux-Prozesshierarchie getestet; tatsächliche Container-PID-
   Namespaces, cgroups CPU/RAM/PID-Limits, readonly Root-FS und SIGTERM/SIGKILL/OOM
   mit den gewählten Digests sind noch zu prüfen. Auch Gateway-/Prometheus-/Grafana-
   Healthbinaries sind erst dann als runtimeverifiziert einzustufen.
3. UI Authlib fehlt im vorhandenen Lockfile/Environment. Produktionslauncher
   verweigert Start. Geprüfte Dependency-/Imagebereitstellung und Browser-OIDC-
   Login/Logout/Expiry/Viewer/Operator bleiben offen. Keine unsichere Ersatzauth.
4. Interne TLS-Kette, Alias/SAN/CA, Ingress-WebSockets und Secret-Dateimounts müssen
   mit echten freigegebenen Zertifikaten auf isolierter Zielplattform geprüft werden.
5. Zielvolume-Rechte/UID/Locks, Datenträgerquoten, Monitoringruntime und
   Alarmzustellung sind noch nicht geprüft. Optionales Monitoring hat keine
   automatischen Host-Exporter oder Alarmzustellungsdienste.

Die sechs Pflichtdokumente und Templates sind reviewbar. Der nächste konkrete
Schritt ist ein eigener, ausdrücklich freigegebener Image-/Authlib-Bereitstellungs-
und isolierter Containerabnahmelauf mit diesen Gates. Danach manuellen Go-live
aus [operations.md](operations.md) prüfen. Beide PRs getrennt reviewen; kein Merge
oder Rollout durch C22.
