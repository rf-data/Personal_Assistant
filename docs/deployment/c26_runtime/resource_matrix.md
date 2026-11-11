# Build- und Coolify-Ressourcenmatrix — 24.10.2026

Jede Zelle nennt Wert und Status. JSON mit Quellen, Eingabestaaten und Quellfingerprints:
[coolify_resource_binding.v1.json](coolify_resource_binding.v1.json).
`requires_operator_confirmation` verlangt eine konkrete lesende Betreiberangabe;
`unverified` bezeichnet einen nicht belegten Zusammenhang. Repositorybefund beweist
keine produktive Auswahl. Die Application-UUIDs wurden jetzt ausdrücklich vom Betreiber benannt; sie werden
nicht aus Namen/Composeprojekten abgeleitet.

| Merkmal | Backend | UI | Nachweis |
| --- | --- | --- | --- |
| Ressourcenname | personal-assistantworker-1 — `operator_observed` | personal-assistant-uimain-a8xzljz4fq52vt1yt43nheg5 — `operator_observed` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Application-UUID | syboxap8mpf8lgjzpjdsqm0z — `operator_observed` | a8xzljz4fq52vt1yt43nheg5 — `operator_observed` | Direkte Coolify-Betreiberergänzung |
| Coolify-Typ | application — `operator_observed` | application — `operator_observed` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Projekt | personal-assistant — `operator_observed` | personal-assistant — `operator_observed` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Environment | production — `operator_observed` | production — `operator_observed` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Tatsächliches Repository | rf-data/Personal_Assistant — `operator_observed` | rf-data/personal-assistant-ui — `operator_observed` | Betreiberauftrag Runtime Observer, 24.10.2026; Image-ID stimmt mit lokaler Containerreferenz überein, kein Build-/Registrybeweis |
| Tatsächlicher Branch | master — `operator_observed` | main — `operator_observed` | Betreiberauftrag Runtime Observer, 24.10.2026; Image-ID stimmt mit lokaler Containerreferenz überein, kein Build-/Registrybeweis |
| Build strategy | Dockerfile — `operator_observed` | Docker Compose — `operator_observed` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Builder | Deployment server — `operator_observed` | offen — `requires_operator_confirmation` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Base Directory | / — `operator_observed` | / — `operator_observed` | Betreiberauftrag Runtime Observer, 24.10.2026; Image-ID stimmt mit lokaler Containerreferenz überein, kein Build-/Registrybeweis |
| Dockerfile-Pfad | /docker/DockerFile.worker — `operator_observed` | docker/DockerFile.UI — `verified_from_repository` | Betreiberauftrag Runtime Observer, 24.10.2026; Image-ID stimmt mit lokaler Containerreferenz überein, kein Build-/Registrybeweis |
| Repository-Compose-Pfad | nicht als aktive Dockerfile-Application-Composeauswahl bestätigt | /docker/docker-compose.ui.yaml — `operator_observed` | Betreiberauftrag Runtime Observer, 24.10.2026; Image-ID stimmt mit lokaler Containerreferenz überein, kein Build-/Registrybeweis |
| Custom Build Command | offen — `requires_operator_confirmation` | offen — `requires_operator_confirmation` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Custom Start Command | offen — `requires_operator_confirmation` | offen — `requires_operator_confirmation` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Beobachteter Start | ["sleep", "infinity"] — `operator_observed` | streamlit run app_ui.py --server.address=0.0.0.0 --server.port=8501 --server.headless=true — `operator_observed` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Git-Autodeploy | Manual deployments only — `operator_observed` | Manual deployments only — `operator_observed` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Preview Deployments, Anzeige | None — `operator_observed` | None — `operator_observed` | Kein Nachweis eines deaktivierten Featureflags |
| Deployment-APIeinstieg vorhanden | ja — `operator_observed` | ja — `operator_observed` | Nur relatives Muster, keine vollständigen URLs; keine Aufrufe |
| APIberechtigte Akteure / tatsächliche Nutzung | offen — `unverified` | offen — `unverified` | Endpunktexistenz beweist weder Berechtigung noch Ausführung |
| Weitere Trigger | offen — `unverified` | offen — `unverified` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Gemeldete Imagereferenz / Tag | syboxap8mpf8lgjzpjdsqm0z:3b91d39195e0d13fe0442d4594b28e431b0f4236 — `operator_observed` | a8xzljz4fq52vt1yt43nheg5_streamlit:b2cf9ca9ba44ee770dab4d834a6ae8285f34776b — `operator_observed` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Lokale Image-ID | sha256:671b8e9bbf92afa6e5968d90a5e1d026a6539eb6b31ec3b94f16f1fc1e6c7f36 — `operator_observed` | sha256:4fd15dc9fc0135a22e85e23a028a018592c35288022f1d4d992ffa70fd9bb237 — `operator_observed` | Betreiberauftrag Runtime Observer, 24.10.2026; Image-ID stimmt mit lokaler Containerreferenz überein, kein Build-/Registrybeweis |
| Registry-RepoDigests | offen — `requires_operator_confirmation` | offen — `requires_operator_confirmation` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Bewiesene Build-SHA | offen — `unverified` | offen — `unverified` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Compose-Projekt | syboxap8mpf8lgjzpjdsqm0z — `operator_observed` | a8xzljz4fq52vt1yt43nheg5 — `operator_observed` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Compose-Service | syboxap8mpf8lgjzpjdsqm0z-20261022T151524 — `operator_observed` | streamlit — `operator_observed` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Generierte Compose-Datei | /artifacts/iigfhsmrpfmntn9h7jxyed8z/docker-compose.yaml — `operator_observed` | /artifacts/fhz5foowb3446edib5gnftbx/docker/docker-compose.ui.yaml — `operator_observed` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |

## Technische Auswahl, nicht produktiver Befund

- `deployment/Dockerfile`: Lean-C22-Runtime, PYTHON_IMAGE und UV_IMAGE erforderlich, `/opt/venv`, UID10001, ENTRYPOINT `python -m scripts.deployment`; #148 ergänzt Gate-CLI.
- `docker/DockerFile.worker`: schwerere lecture-worker-Extras, unpinned Python/uv-Auswahl, CMD `sleep infinity`. Die Auswahl dieses Pfades ist jetzt operator_observed; unabhängige Build-/Registryprovenienz fehlt. Keine Extrasinstallation in diesem Auftrag.
- `deployment/compose.yaml`: vorhandene Caddy/API-Namespacekopplung; vollständiger Stack enthält weitere Rollen/UI. Nicht zusätzlich starten. `cs50-worker.compose.yaml` bietet weitere getrennte Profile, die nicht zum Bootstrap addiert werden.
- `coolify.runtime-bootstrap.compose.yaml`: vorhandene drei Rollen, neuer eigener Runtime-Bind, getrennte API-/Workerprofile, keine öffentliche APIroute. `Caddyfile` leitet internes TLS auf Loopback8016 weiter.
- `coolify.private-https.yaml`/`public-https.yaml`: UI-Service heißt dort `ui`; reale UI und UI-Repo verwenden `streamlit`. Blindes Überlagern würde eine zweite UI riskieren.
- UI `DockerFile.UI` nutzt den geschützten Launcher; tatsächlich gemeldeter direkter Streamlitstart ist abweichend. Repo-Compose verwendet weiterhin JOB_BACKEND/ADMIN_AUTH_MODE disabled.
- In beiden geprüften Gitbäumen fehlen GitHub-Workflowdateien. Das beweist weder fehlende externe Checks noch deaktivierte Coolify-Webhooks.

Image-ID (`sha256:…`, lokale Konfiguration), Tag und Registry-RepoDigest (`name@sha256:…`, Registrymanifest) bleiben getrennte Belege. SOURCE_COMMIT Runtime only und ein SHA-artiger Tag beweisen die Build-SHA nicht. Ohne RepoDigest keine Ersetzung durch die Image-ID.

Dieselbe Application ist im Quellmodell grundsätzlich umstellbar, aber nicht live abgenommen.
[Entscheidung und kleinste Gate-Erweiterung](coolify_driver_plan.md). Kein Save/Load/Deploy ausgeführt.

## Aktueller Triggernachtrag

Die [Triggerprüfung](deployment_trigger_audit.md) trennt Gitquellen, registrierte
Actions-Metadaten, Berechtigungen und Ausführung. Backend: ein aktiver dynamischer
Dependency-Graph-Workflow und ein historischer fehlgeschlagener Run; UI: keine
registrierten Workflows/Runs. Daraus folgt kein belegter Coolifydeploy. Preview
None bedeutet angezeigter Bestand, nicht automatisch deaktivierte Previewfunktion.
Der zusätzliche Trigger-Scope bleibt unverified und fail-closed.
