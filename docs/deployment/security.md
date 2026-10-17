# Sicherheitsvertrag

Nur privater Single-Host-Betrieb. Alle Dienste UID/GID 10001, readonly Root-FS,
`cap_drop: ALL`, `no-new-privileges`, begrenzter noexec/nosuid/nodev-Tmpfs,
CPU/RAM/PID-Limits und rotierte Docker-Logs. Keine Host-PID-/Host-Netz-Freigabe,
kein Docker-Socket, kein privileged, keine Host-Exporter im C22-Profil.
Ein Container-Escape oder kompromittierter Host ist damit nicht ausgeschlossen;
Hostupdates, Firewall und Datenträgerverschlüsselung gehören zum Betrieb.

Die einzigen vorgesehenen öffentlichen Ports sind 443 am separat verwalteten
Ingress und ein eingeschränkter administrativer SSH-Zugang. Das Template selbst
veröffentlicht **keinen** Port. UI 8501 und API-TLS 8443 sind Docker-intern, C16
8016 bleibt Loopback im Gateway-Netzwerknamespace. Private TLS-Schlüssel werden
nur in den Gateway gemountet; die UI erhält nur die CA. Zertifikatsprüfung bleibt
aktiv (`SSL_CERT_FILE` erweitert den expliziten Vertrauensvertrag der UI).
Gateway-Zertifikat/Docker-Alias müssen übereinstimmen; keine IP-/Hostname-Ausnahme.
Caddy-Admin-API und automatisches ACME sind deaktiviert. Die Gateway-Laufzeit ist
vor Go-live mit dem gewählten Image/Caddyfile zu testen.

Der externe Proxy terminiert Browser-TLS und transportiert Streamlit-WebSockets.
Keine vertrauenswürdige Identität aus frei gelieferten Proxyheadern ableiten.
Streamlit prüft OIDC; die bestehende UI prüft `is_logged_in`, exakten Issuer und
Subject-Allowlisten. Viewer dürfen lesen, Operatoren nur mit eigener Backend-
Identität Jobs bestätigen/steuern. Der Backendvertrag validiert Rolle und
Kurs-Scopes erneut. Keine gemeinsame Operatoridentität für alle UI-Nutzer.
UI-Demo/Test-Auth ist im Production Template nicht erlaubt. XSRF-/CORS-Schutz
bleiben aktiv. Browserlogin, Redirect, Abmeldung und abgelaufene Identität sind
noch keine lokal nachgewiesene OIDC-Abnahme.

Secrets: individuelle zufällige Bearerdateien (32–256 URL-sichere Zeichen),
OIDC-Clientsecret, Cookie-Secret, TLS-Key und Grafana-Passwort außerhalb von Git,
Image, stdout und Reports. Dateibindings verlangen bereits vorhandene 0600-Dateien
im Eigentum der jeweiligen Dienst-UID. Compose-Dateibinds erzwingen diese Rechte
nicht selbst: der Betreiber stellt sie bereit; UI-/Backend-Launcher prüfen ihre
eigenen geschützten Eingaben. Keine automatischen `chmod/chown` bestehender Daten.
Konfigurationshashes von Tokens und Subject-Listen sind ebenfalls private Daten.

Rotation: UI-Ingress schließen, API/Executor geordnet stoppen; neue individuelle
Tokens in separaten Dateien erzeugen, Backend-SHA256 und UI-Bindings konsistent
ersetzen, Konfiguration prüfen, API/Executor/UI neu starten, alte Werte sperren.
Die UI liest Tokenbytes pro Request; der Backend-Identitätssatz ist beim Start
geladen. Ein Dateibind kann nach atomarem Host-Dateiaustausch einen alten Inode
behalten: Container neu erstellen oder nachweislich neu binden. Bei kompromittierter
Identität außerdem offene Streamlit-Sessions beenden und OIDC/Cookie-Secrets nach
Incidententscheidung rotieren. Kein unsicherer Parallelbetrieb alter/new Tokens.

`/v1/metrics` verlangt ebenfalls Bearerauth. Eigener Viewer mit bewusst gewählten
Kurs-Scopes; dessen Aggregation sieht nur erlaubte Kurse. Prometheus liest eine
private Token-Datei und prüft TLS/Servername. Keine Job-ID-, PID-, URL-, Subject-
oder Pfadlabels ergänzen. C15-Dashboards werden wiederverwendet. Prometheus und
Grafana veröffentlichen keine Ports. Grafana benötigt ein individuelles
Adminpasswort; Prometheus ist im privaten Netz ohne eigene HTTP-Auth erreichbar.
Daher keinen öffentlichen Proxy dorthin hängen; Fernzugriff nur über separat
authentisierten Tunnel/Proxy. UI und Monitoring im gemeinsamen privaten Netz
sind eine dokumentierte Vertrauensgrenze, keine gegenseitige Sandbox.

Coolify darf Standard-Compose verwalten, aber keine Dockerzugriffsrechte an die UI
weiterreichen. Auto-Deploy/Webhooks bleiben aus. Ingress/Firewall/IdP-Konfiguration
sowie digestspezifische Imageprüfung sind manuelle Go-live-Voraussetzungen.

Referenzen: [Compose-Dienste](https://docs.docker.com/reference/compose-file/services/),
[Caddy-Optionen](https://caddyserver.com/docs/caddyfile/options),
[Streamlit-OIDC](https://docs.streamlit.io/develop/concepts/connections/authentication).
Diese Dokumentation beschreibt den Vertrag; sie ersetzt keine Laufzeitabnahme.
