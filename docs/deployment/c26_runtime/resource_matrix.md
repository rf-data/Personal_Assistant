# Build- und Coolify-Ressourcenmatrix — 23.10.2026

Jede Zelle nennt Wert und Status. JSON mit Quellen, Eingabestaaten und Quellfingerprints:
[coolify_resource_binding.v1.json](coolify_resource_binding.v1.json).
`requires_operator_confirmation` verlangt eine konkrete lesende Betreiberangabe;
`unverified` bezeichnet einen nicht belegten Zusammenhang. Repositorybefund beweist
keine produktive Auswahl. Namen/Composeprojekte sind keine bestätigten Application-UUIDs.

| Merkmal | Backend | UI | Nachweis |
| --- | --- | --- | --- |
| Ressourcenname | personal-assistantworker-1 — `operator_observed` | personal-assistant-uimain-a8xzljz4fq52vt1yt43nheg5 — `operator_observed` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Application-UUID | offen — `requires_operator_confirmation` | offen — `requires_operator_confirmation` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Coolify-Typ | application — `operator_observed` | application — `operator_observed` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Projekt | personal-assistant — `operator_observed` | personal-assistant — `operator_observed` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Environment | production — `operator_observed` | production — `operator_observed` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Tatsächliches Repository | offen — `requires_operator_confirmation` | offen — `requires_operator_confirmation` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Tatsächlicher Branch | offen — `requires_operator_confirmation` | offen — `requires_operator_confirmation` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Build strategy | Dockerfile — `operator_observed` | Docker Compose — `operator_observed` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Builder | Deployment server — `operator_observed` | offen — `requires_operator_confirmation` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Base Directory | offen — `requires_operator_confirmation` | offen — `requires_operator_confirmation` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Dockerfile-Pfad | offen — `requires_operator_confirmation` | docker/DockerFile.UI — `verified_from_repository` | Backendauswahl offen; UI-Repository build.context/build.dockerfile belegt |
| Repository-Compose-Pfad | offen — `requires_operator_confirmation` | offen — `requires_operator_confirmation` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Custom Build Command | offen — `requires_operator_confirmation` | offen — `requires_operator_confirmation` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Custom Start Command | offen — `requires_operator_confirmation` | offen — `requires_operator_confirmation` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Beobachteter Start | ["sleep", "infinity"] — `operator_observed` | streamlit run app_ui.py --server.address=0.0.0.0 --server.port=8501 --server.headless=true — `operator_observed` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Git-Autodeploy | Manual deployments only — `operator_observed` | Manual deployments only — `operator_observed` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Weitere Trigger | offen — `unverified` | offen — `unverified` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Gemeldete Imagereferenz / Tag | syboxap8mpf8lgjzpjdsqm0z:3b91d39195e0d13fe0442d4594b28e431b0f4236 — `operator_observed` | a8xzljz4fq52vt1yt43nheg5_streamlit:b2cf9ca9ba44ee770dab4d834a6ae8285f34776b — `operator_observed` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Lokale Image-ID | offen — `requires_operator_confirmation` | offen — `requires_operator_confirmation` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Registry-RepoDigests | offen — `requires_operator_confirmation` | offen — `requires_operator_confirmation` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Bewiesene Build-SHA | offen — `unverified` | offen — `unverified` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Compose-Projekt | syboxap8mpf8lgjzpjdsqm0z — `operator_observed` | a8xzljz4fq52vt1yt43nheg5 — `operator_observed` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Compose-Service | syboxap8mpf8lgjzpjdsqm0z-20261022T151524 — `operator_observed` | streamlit — `operator_observed` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |
| Generierte Compose-Datei | /artifacts/iigfhsmrpfmntn9h7jxyed8z/docker-compose.yaml — `operator_observed` | /artifacts/fhz5foowb3446edib5gnftbx/docker/docker-compose.ui.yaml — `operator_observed` | Betreiberauftrag; offene Auswahlfelder: [fünf Prüfpakete](operator_binding_check.md) |

## Technische Auswahl, nicht produktiver Befund

- `deployment/Dockerfile`: Lean-C22-Runtime, PYTHON_IMAGE und UV_IMAGE erforderlich, `/opt/venv`, UID10001, ENTRYPOINT `python -m scripts.deployment`; #148 ergänzt Gate-CLI.
- `docker/DockerFile.worker`: schwerere lecture-worker-Extras, unpinned Python/uv-Auswahl, CMD `sleep infinity`. Passt zum gemeldeten Platzhalter, ist aber nicht als ausgewählte Coolifydatei bewiesen. Keine Extrasinstallation in diesem Auftrag.
- `deployment/compose.yaml`: vorhandene Caddy/API-Namespacekopplung; vollständiger Stack enthält weitere Rollen/UI. Nicht zusätzlich starten. `cs50-worker.compose.yaml` bietet weitere getrennte Profile, die nicht zum Bootstrap addiert werden.
- `coolify.runtime-bootstrap.compose.yaml`: vorhandene drei Rollen, neuer eigener Runtime-Bind, getrennte API-/Workerprofile, keine öffentliche APIroute. `Caddyfile` leitet internes TLS auf Loopback8016 weiter.
- `coolify.private-https.yaml`/`public-https.yaml`: UI-Service heißt dort `ui`; reale UI und UI-Repo verwenden `streamlit`. Blindes Überlagern würde eine zweite UI riskieren.
- UI `DockerFile.UI` nutzt den geschützten Launcher; tatsächlich gemeldeter direkter Streamlitstart ist abweichend. Repo-Compose verwendet weiterhin JOB_BACKEND/ADMIN_AUTH_MODE disabled.
- In beiden geprüften Gitbäumen fehlen GitHub-Workflowdateien. Das beweist weder fehlende externe Checks noch deaktivierte Coolify-Webhooks.

Image-ID (`sha256:…`, lokale Konfiguration), Tag und Registry-RepoDigest (`name@sha256:…`, Registrymanifest) bleiben getrennte Belege. SOURCE_COMMIT Runtime only und ein SHA-artiger Tag beweisen die Build-SHA nicht. Ohne RepoDigest keine Ersetzung durch die Image-ID.

Dieselbe Application ist im Quellmodell grundsätzlich umstellbar, aber nicht live abgenommen.
[Entscheidung und kleinste Gate-Erweiterung](coolify_driver_plan.md). Kein Save/Load/Deploy ausgeführt.
