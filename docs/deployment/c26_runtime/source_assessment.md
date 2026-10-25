# Bestehende Betriebsdateien und ungeklärte Startabweichungen

Stand: 23.10.2026. Ausschließlich GitHub-Quellen gelesen; kein Hostzugriff,
kein Containerstart oder Compose-Rendering. Backend-Master `e502aa915ad0e928dbe7e92eacd44fff0152912b`,
UI-Main `e4be7a2fbf5b20beda0db854462dd2d70c2c93ff` sind unverändert.
Pfade, vollständige Quellrefs und SHA-256 stehen in
[technical_sources.v1.json](technical_sources.v1.json).

## Technische Ausgangsbasis: vorhandene Dateien zuerst

| Repository / Datei | Bestehende Funktion / Konsequenz |
| --- | --- |
| Backend `deployment/Dockerfile` | Schlanke Runtime, UID 10001, venv/PATH, Entrypoint `python -m scripts.deployment`; ist noch kein Beleg für das tatsächlich gebaute Image |
| Backend `deployment/compose.yaml` | API teilt mit `network_mode: service:api-gateway` den Gateway-Namespace; C16-Executor ohne Netz, private UI-Anbindung und Healthchecks bereits vorhanden |
| Backend `deployment/Caddyfile` | Interner TLS-Endpunkt 8443 leitet an `127.0.0.1:8016` weiter; kein neuer Transport erforderlich |
| Backend `deployment/cs50-worker.compose.yaml` | Bestehender C26-Kapazitätsworker ersetzt fachlich die C16-Executorrolle; niemals zusätzlich auf demselben Root starten |
| Backend `deployment/coolify.private-https.yaml` | Bestehendes privates UI-Profil mit RemoteAddr-Allowlist; muss an sämtliche tatsächlichen UI-Router gebunden sein |
| Backend `deployment/coolify.public-https.yaml` | Andere, ausdrücklich öffentliche UI-Zugriffsvariante; nicht für diesen privaten Bootstrap auswählen oder zur Fehlerumgehung verwenden |
| UI `docker/DockerFile.UI` | Aktueller geschützter `admin_ui_package.container_runtime`-Entrypoint mit Healthcheck |
| UI `docker/docker-compose.ui.yaml` | Vorhandener Buildservice `streamlit`, Kontext `..`, Dockerfile `docker/DockerFile.UI`; Backend/Auth zunächst deaktiviert, kein Beleg für tatsächliche Coolify-Buildwerte |
| Backend `docker/DockerFile.worker` | Zusätzlich vorhandene Worker-Builddefinition mit `CMD ["sleep", "infinity"]`; konkrete alternative Erklärung für den Sleep-Bestand, noch kein Buildnachweis |

## Wiederverwendungsentscheidung

**Die C22-Transportarchitektur ist auf Quellcodeebene geeignet und bleibt die
bevorzugte Lösung.** Loopback bezeichnet hier absichtlich den gemeinsamen API-/
Gateway-Namespace. Die API benötigt keine Wildcard-Bindung, keinen öffentlichen
Port und keinen anderen Controller. Worker und UI verwenden ihre vorhandenen
Implementierungen; der Kapazitätsworker übernimmt die bestehende Executorrolle.

Die unveränderte vollständige `deployment/compose.yaml` kann nicht einfach neben
den Bestandsressourcen gestartet werden: Sie enthält eine eigene UI und einen
C16-Executor sowie andere Mountziele (`/var/lib/personal-assistant/…`,
`/run/config/controller.json`). Der C26-Workerstack enthält wiederum eine eigene
Executorrolle und weitere CLI-/Downloadprofile. Keine additive Kombination dieser
Stacks, keine zweite UI/Queue/Workerinstanz und keine Datenpfadmigration.

Auch die UI-Servicekeys müssen erhalten und ausdrücklich zugeordnet werden:
`docker/docker-compose.ui.yaml` verwendet `streamlit`, die vorhandenen Backend-
HTTPS-Overlays verwenden `ui`. Ein blindes Zusammenführen legt damit einen
zusätzlichen Service an, statt die bestehende Streamlitrolle anzupassen. Erst die
bestätigte Service-/Ressourcenbindung und ein reviewtes Rendering erlauben eine
spätere Übernahme der vorhandenen HTTPS-Einstellungen; jetzt kein Rename oder
Compose-Merge. Die UI-Grunddatei mit deaktivierter Backend-/Authanbindung allein
ist keine freigegebene private Produktionskonfiguration.

Die bereits vorbereitete `coolify.runtime-bootstrap.compose.yaml` ist ausschließlich
eine gesperrte Host-Mapping-Variante derselben drei Backendrollen unter Erhalt der
vier gemeldeten Mountziele. Sie bleibt inhaltlich unverändert. Die vorhandene
getrennte UI-Ressource ist später separat mit ihrem bestehenden geschützten
Launcher und den vorhandenen HTTPS-Einstellungen anzubinden. Es wird kein zweiter
Betriebsstack eingeführt. Keine der Dateien jetzt importieren oder aktivieren.

**Wiederverwendung in der realen Coolify-Application bleibt unverified**, bis
maßgebliche Ressourcen-ID/Buildpfade, bestätigte Umstellung der Backend-
Application von Dockerfile auf Compose, gerenderte Namespace-/Netzverträge,
Rollenersatz ohne Überlappung, Mounts, Config/Limits/Queue und Trigger belegt sind.
`coolify.type=application` und die Compose-Labels allein schließen diese Lücke
nicht. Der `/artifacts/…`-Pfad bezeichnet eine gemeldete Deploydatei; er beweist
weder deren Inhalt noch Übereinstimmung mit einer Repositorydatei oder die
tatsächliche Repository-/Branch-/Dockerfileauswahl.

## Startabweichungen: Nachweis und offene Ursache

| Rolle | Quellenbefund | Betreiberbefund | Bewertung |
| --- | --- | --- | --- |
| Backend | `deployment/Dockerfile` besitzt sowohl auf aktuellem Master als auch unter Quellref `3b91d39195e0d13fe0442d4594b28e431b0f4236` denselben Deployment-Entrypoint | Nur `sleep infinity` läuft | Die Wahl genau dieser Dockerfile wird durch den Tag nicht bewiesen; ältere Version allein unter dieser Quellref erklärt keinen Sleep-Default dieser Datei |
| Backend, alternative bestehende Definition | `docker/DockerFile.worker` besitzt auf beiden Quellrefs `CMD ["sleep", "infinity"]`, ohne eigenes explizites ENTRYPOINT | Sleep passt dazu | Plausible separate Sleep-Definition; tatsächliche Buildauswahl und Basisimage-Konfiguration bleiben offen |
| UI | Unter `b2cf9ca9ba44ee770dab4d834a6ae8285f34776b` definiert die Dockerfile direkt den gemeldeten Streamlit-CMD; aktuelle Main-Datei hat den geschützten Launcher | Alter Streamlit-Start | Mit historischem Build vereinbar; eine Startüberschreibung oder andere Buildquelle ist ohne Image-/Buildbeleg nicht ausgeschlossen |

Ein Image-Tag, der wie eine Quell-SHA aussieht, verknüpft noch kein tatsächliches
Image mit diesem Quellstand. Die historische Analyse zeigt vorhandene mögliche
Definitionen, nicht die Laufzeitprovenienz. Die **bewusste Platzhalterabsicht** ist inzwischen vom Betreiber bestätigt.
Ob sie über die vorhandene Sleep-Dockerfile oder eine Startüberschreibung
umgesetzt wurde, bleibt ohne Build-/Imagemetadaten offen.

Die [ergänzten lesenden Betreiberprüfungen](operator_checks.md) vergleichen das
tatsächlich referenzierte Image mit dem Container und dem Coolify-Buildbeleg.
Nur feste Startup-Vektoren bzw. Gleichheitswerte ausgeben, keine vollständigen
Args/Umgebungen/Compose-/Buildlogs. Bei unbekannten Vektoren Ergebnis privat
klassifizieren und lediglich `unverified` melden. Kein Startversuch zur Diagnose.

**GO:** Quellenreview und lesende Inventur. **NO-GO:** Merge, Rollenstart,
Build-/Triggeränderung, neue Container, produktive Jobs oder Gatefreigabe.
Die ursprüngliche rote C18-Regression und fehlende Liveabnahmen bleiben bestehen.

## Konsolidierte Source-to-Runtime-Matrix

| Rolle / Status | Quelle und Dependencies | Einstieg / Zuordnung | Verbleibender Beleg |
| --- | --- | --- | --- |
| Bestandsbackend, bewusster Platzhalter | `docker/DockerFile.worker`: Python 3.12, ffmpeg/git/curl/tmux, `uv sync --extra lecture-worker` mit u. a. Whisper/Docling/OCR/tiktoken; Projektvenv `/app/.venv`, kein gesetzter Runtime-venv-PATH in dieser Dockerfile | `CMD ["sleep", "infinity"]`; passt zum Befund. Application/Dockerfile/Deployment-server sind bestätigt | Tatsächlich gewählte Dockerfile und Base Directory, Image-ID/RepoDigest/Buildrevision/Overrides bleiben offen; kein Startversuch im alten Image |
| Vorgesehene API und genau ein C26-Worker | `deployment/Dockerfile` mit eigener `deployment/runtime/pyproject.toml`/Lock: Pydantic/Settings, httpx, bs4, Typer, dotenv, YAML, returns, tenacity, PyMuPDF. Keine Whisper-/Docling-/OCR-/LLM-Pflicht; tiktoken nicht für diese Offline-Rollen ergänzen | `/opt/venv` im PATH, UID 10001; Deployment-Entrypoint, Workerrolle überschreibt auf `scripts.cs50_worker`; identisches Backendimage | Kombinierter Commit mit #148/#156; #148 ergänzt Gate-CLI-COPY. Gebautes Image und exakte gepinnte Runtimeabhängigkeiten noch nicht geprüft; Testvenv ist kein Imagebeleg |
| Interner Gateway | Eigenes vorhandenes `deployment/gateway.Dockerfile`: geprüftes Python-Basisimage + Caddy-Binary + stdlib-Healthscript, keine Backendvenv nötig | Caddy `run`, bestehendes Caddyfile TLS 8443 -> Namespace-Loopback 8016 | Separates Gatewayimage/Digest, TLS/SAN/CA und realer Namespacebezug; Backendimage allein ist kein Gatewayimage |
| Bestehende UI | `docker/DockerFile.UI` + UI-Lockfile; aktueller geschützter Launcher statt historischer Streamlit-CMD | Bestehende Docker-Compose-Application und Service `streamlit` bleiben erhalten; gezeigter Inhalt entspricht der Repositorydatei | Genaues Compose-Pfadfeld und laufende Buildrevision/Digest fehlen. Grunddatei hat `JOB_BACKEND=disabled`, `ADMIN_AUTH_MODE=disabled` und ist damit keine fertige private C26-Anbindung |

Es werden weiterhin **zwei bestehende Applications** vorgesehen: Backend nach
separat genehmigter Adoption mit drei Diensten, UI mit genau dem vorhandenen
Streamlitservice. Kein neuer User-defined Service oder zusätzlicher C16-Executor.
Die bestehende Dockerfile-Buildstrategie kann nicht allein durch ein anderes CMD
einen Composeverbund mit `service:api-gateway` bereitstellen. Die notwendige
Umstellung ist ein späterer expliziter Betreiberentscheid, kein bestätigter Istwert.

Die schmale Runtime ist quellseitig auf die vorgesehenen HTML-/PDF-/C18-Rollen
ausgerichtet, kein Ersatz für sämtliche Lecture-/Audio-/OCR-Funktionen des alten
Workers. Andere Loviscach-/Pilotwriter müssen vor Ablösung separat zugeordnet
sein. Es werden keine bestehenden Fähigkeiten, Quellen oder Daten migriert.
Die Imagebuild-/Import-/Healthabnahme bleibt technische Restarbeit; keine neuen
Images oder Pakete wurden für diese Prüfung heruntergeladen.

Die bestehende Testumgebung ist außerdem nicht identisch mit dem Image-Lock:
Distributionsmetadaten melden unter anderem Pydantic 2.14.1 statt 2.13.4 und
PyMuPDF 1.27.2.2 statt 1.28.2; für pydantic-settings/returns fehlen dort
Distributionsmetadaten. Das sagt allein nichts über jede Importierbarkeit aus,
belegt aber keine erfolgreiche Installation des Runtimeprofils. Keine Pakete
nachinstallieren oder daraus ungeprüft neue Pins ableiten: Exakt gepinnter
Imagebuild und anschließende Rollen-/Import-/Health-Smokes bleiben erforderlich.

## Runtime-Konfigurationsfinalisierung, nachfolgender Stand

Die neue lesende `scripts.c26_runtime_preflight` wird im vorhandenen Lean-Dockerfile
mitkopiert; keine neue Runtimeabhängigkeit. Diese gezielte Erweiterung ersetzt die
frühere Aussage „keine Produkt-Pythonmodule geändert“ für diesen Folgecommit.
Gate/Store/Executor/HTTP-Kern und Quellrevisionen der anderen Drafts bleiben
unverändert. Neuer eigener Bind `/app/runtime-state`, Root `c16`, historische
Daten nur RO. Worker zusätzliches Profil; normales APIprofil startet ihn nicht.
Historische Controller und konkrete Limits sind jetzt Betreiberbefunde, neue
Root-/Mount-/Settings-/Imagefreigaben bleiben ausstehend. Siehe
[Konfigurationsvertrag](runtime_configuration.md) und [Runbook](rollout.md).
