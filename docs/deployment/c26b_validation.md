# C26-B – Abschluss- und Freigabebeleg

20.10.2026. `https_deployment_prepared` und **`https_staging_tested` ausschließlich
für isoliertes lokales synthetisches Staging**. Produktivstatus bleibt
**`production_release_blocked`**, kein `production_approved`.
Kein SSH-/Hetzner-/Coolify-/DNS-/ACME-/Port-/Produktivdatenzugriff.
[Ausführbares Betreiberhandbuch, Entscheidungen und Rollback](https.md).

## Implementierte Änderungen und Dateien

| Paket | Repository / Dateien | Wirkung |
| --- | --- | --- |
| B1 | Backend `deployment/coolify.ui.compose.yaml`, `coolify.private-https.yaml`, `coolify.public-https.yaml` | Ersatz ausschließlich der bestehenden UI, Coolify-generierte TLS-Routen, bestehende getrennte Netze, keine Hostports, Non-root, Ressourcen-/Restart-/Loggrenzen |
| B1 | Backend `deployment/c26-https.env.example`, `c26-oidc.secrets.toml.example` | Leere parametrisierbare Pflichtfelder, keine echten Domains, Digests oder Secrets erfunden |
| B1 | Backend `scripts/https_preflight.py`, `tests/test_https_preflight.py` | Offlineprüfung des finalen Coolify-Composeexports, Schutz vor Exposition und Launcher-/Protokollumgehung |
| B2 | UI `pyproject.toml`, `uv.lock`, `docker/c26-build-inputs.json` | Offizielles auth-Extra, Streamlit 1.65.0, Authlib 1.9.1 und transitive Locks; keine bestehende Paketversion verändert; geprüfte Basisimage-Digests |
| B2 | UI `security.py`, `core/environment.py`, `app_admin.py`, `live_app.py` | Bestehende Principalbindung um iat/exp/Maximalalter ergänzen, aktive Fragmente neu prüfen, Logout beendet den Appdurchlauf, geschützten Zustand verwerfen |
| B2 | UI `container_runtime.py`, `https_runtime.py` | Pflichtprüfung vor Start, authentifizierte Readiness, offizieller st.App-Hook derselben App, sichere Cookies, exakter Host/Origin/Proxy, WSS-Kompatibilität und sichere Callbackfehler |
| B3 | Backend `scripts/acceptance/c26_https_server.py`; UI `scripts/acceptance/c26_https.py`, `synthetic_oidc.py`, `c26_container.py` | Reale lokale HTTP/TLS-/Traefik-/Browser-/Code-/JWKS-/C16-/FTS-/Restart-Proben mit ausschließlich synthetischen Daten |
| B3 | UI `tests/test_https_security.py`, `test_container_runtime.py`, aktualisierte bestehende OIDC-Fixtures | Fehlerhafte Claims/Headers/Secrets/Binding, Callbackfehler und Startverweigerung |
| B3 | Bestehende Backend-Deploymentdokumente, `docs/deployment/https.md`; UI `docs/c26_https.md` | Ein führendes Betreiberhandbuch, Abnahmebelege und lokale Testanleitung |

Kein Backendfachmodul, C16-/C18-/C22-/C23-/C24-Datenmodell, Queue, Worker oder
produktiver Store verändert. Backendimage bleibt das bestehende; kein zusätzlicher
produktiver Proxy. Der Testserver verwendet vorhandene Application/Executor- und
synthetische Indexfixtures. Die UI startet weiterhin einmalig `app_admin.py`.

## Ausgeführte Tests und tatsächliche Ergebnisse

| Lauf | Ergebnis | Aussage / Grenze |
| --- | --- | --- |
| Endgültige Compose-/Exportprüfungen | **24 passed** | Tatsächliche Compose-CLI, beide Profile, 20 unsichere Konfigurationen plus fehlende Pflichtwerte; simulierte Coolifylabels, kein Live-Coolify |
| UI Controller-/Principalregression | **31 passed** | Bestehende Rollen-/Owner-/Konfigurationsverträge |
| UI Produktionsstart/Secrets | **9 passed** | Fehlende Authlib/Secrets, Dateimodus/Owner/Symlink, Callback/Origin, Rollenbindung, fehlformatierte Scopekonfiguration |
| UI HTTPS-/OIDC-Security | **8 passed** | Echte ASGI-Middleware und tatsächliche Authlib-Nonce-/Expiry-Validierung; kein Test-Authersatz |
| Voller bisheriger Backendlauf | **173 passed, 2 failed / 175**, 437,36 s | C22-Transport/Operations, Content-/Search-/Workflow-HTTP und damalige 20 C26-Konfigurationsfälle; kein grüner Gesamtregressionslauf behauptet |
| Gezielte Backendnachprüfung | **1 passed, 1 failed**, 15,29 s | SQLite-Lock im Normalized-Resume-Fall bestand isoliert; Schemasnapshot weiterhin abweichend |
| Unverändertes master-Archiv `449437b` | **1 failed**, 2,93 s | Derselbe Schemasnapshotfehler auf unverändertem Ursprung bestätigt; keine Schema-/Snapshotänderung als Teil von C26-B |
| Volle bisherige UI-Suite | 171 Methoden, fünf Error-Einträge in drei Workflowmethoden, 420,48 s | Bestehender E2E verweigerte den damals uncommitteten Backendworktree; kein Produktfehler daraus abgeleitet |
| Workflow-Nachlauf auf sauberem Backendcommit | Zwei Methoden bestanden; ein nativer Worker-Timeout-Subfall instabil, 124,72 s | Owner/Course/Viewer und normaler Execute/Resume/Cancel/Refresh bestanden |
| Isolierter nativer Workflow-Nachlauf | **1 Methode mit drei Fault-Subfällen bestanden**, 123,97 s | Cancel, Worker-Timeout und Executor-Neustart tatsächlich mit nativen PDF-Prozessen ausgeführt |
| Lokale UI-Dockerbuilds | **passed** | Frozen Runtime-Lock, geprüfte Python-/uv-Manifestdigests, keine Veröffentlichung in einer Registry |
| Isolierter UI-Containerlauf | **5 passed** | Startverweigerung, Non-root/read-only/ohne Netz und Ports, Liveness, sichere fehlende Backend-Readiness und keine Testcredentials in Logs |
| Vollständiger Browser-/TLS-/OIDC-/Job-E2E | **16 passed, zwei vollständige erfolgreiche Läufe** | Reales lokales synthetisches Staging; Einzelbeleg [c26b_e2e.v1.json](c26b_e2e.v1.json) |

Die Regressionsergebnisse sind einzelne tatsächliche Läufe; daraus wird keine
fiktive grüne Gesamtsumme berechnet. Neue Fälle und gezielte Nachprüfungen nach
Änderungen sind getrennt ausgewiesen. Ruff check/format, Git-Diff-Whitespace und
Repository-Commitprüfungen sind Teil der Abschlussprüfung.

### Nachgewiesene E2E-Kette

Gepinnter Traefik-v3.6-Testcontainer auf ausschließlich Loopback und dynamischen
unprivilegierten Ports, kanonische native Streamlit-App, tatsächliche C16-API und
Executor in einem isolierten nativen Backendprozess, temporärer TLS-Test-IdP mit
Codeaustausch/RS256/JWKS. Die separate Containerprobe prüft die tatsächliche UI-
Imagegrenze. Dies ist **kein kompletter Coolify-Stack oder Backendimage-Abnahmelauf**.

Nachgewiesen: echte HTTPS-CA-/SAN-Prüfung plus negative CA-Prüfung; HTTPredirect;
Host-/Origin-/Forwarded-Headerprüfung; Private-Allowlist inklusive verweigertem
X-Forwarded-For-VPN-Bypass; fehlende/ungültige APIanmeldung; unangemeldete UI;
State/Nonce-Negativfälle mit tatsächlich beobachtetem Codeaustausch;
Login/WSS/Secure-/HttpOnly-/Lax-Cookies; ausdrücklich bestätigter Indexjob in der
vorhandenen C16-Queue bis `completed`; echte FTS-Suche und autorisierte Quelldetails;
API-/Executor-Stopp und Neustart auf demselben synthetischen Root mit Session-/
Suchwiederherstellung; tatsächliche Cookieentfernung über `/auth/logout`;
Ablaufsperre in aktiven Fragmenten und nach Refresh; keine Testcredentials in
Prozesslogs. Der Clientzustand wird bei Backendausfall verworfen und bewusst neu
aufgebaut. Keine externen Kurse, LLMs, Downloads oder produktiven Daten.

Der Browser nutzt ausschließlich im temporären Testkontext eine Ausnahme für die
selbst signierte Test-CA. Strikte Zertifikatsverifikation wird separat über reale
TLS-Verbindungen und vom tatsächlichen UI-APIclient ausgeführt. Ein Browser-
Truststore-/Produktivzertifikatsnachweis wird daraus nicht abgeleitet.

Entwicklungszwischenläufe waren zunächst fehlgeschlagen. Dabei wurden unter
anderem Testport-/Dateiformat-/SNI-/Testdatei-UIDfragen, Traefiks `wss`-Header und
Browser-Rerun-/Widget-/Navigationssynchronisierung korrigiert. Der finale Lauf
prüft die Checkbox über normale Tastatureingabe, ohne API-/Session-/Berechtigungs-
Bypass. Ein real beobachteter Callbackfehler wird nun vor dem Fehlerlogger
abgefangen; Logout rendert keine weiteren geschützten Backendansichten.
Diese Zwischenfehler werden nicht als bestandene Testläufe gezählt.

## Sicherheitstestmatrix aus dem Auftrag

| Fall | Lokaler Nachweis | Produktivgrenze |
| --- | --- | --- |
| 1 HTTPS/Proxy | Echte Traefik-/CA-/Redirectprobe, Exportaudit | Live-DNS/ACME/Proxyversion `not_tested` |
| 2 Fehlende/ungültige Auth | Real HTTPS API 401, UI-Anmeldesperre | Tatsächliche Betreiberidentität `not_tested` |
| 3 Sessionablauf | Browser/aktive Fragmente/Refresh, numerische Claims | IdP-Claims/Clock-Synchronisation `not_tested` |
| 4 State/Nonce | Echter lokaler Code-/JWKS-Flow mit falschen Werten | Gewählter externer IdP `not_tested` |
| 5 Rechteentzug | Bestehende ACL-/UI-Principaltests, APIauthfehler verwerfen Zustand | Sofortiger IdP-Widerruf braucht Tokenentzug/Neustart, kein Backchannel-Logout behauptet |
| 6 Source/Course/Owner | Bestehende C16-/Content-/Search-/Workflowtests inkl UI | Echte Betreibergrants `not_tested` |
| 7 Direkter Backendzugriff | Reale TLS-Authverweigerung | Öffentliche Nichterreichbarkeit des Zielhosts `not_tested` |
| 8 Proxyheader | Reale Traefik-Sanitierung, untrusted Peer/Mehrfachheader im ASGItest | Globale EntryPoint-Trustflags `not_tested` |
| 9 Host/Origin | Reale HTTP-Negativproben plus ASGI-/WSS-Grenze | Live-Domainroute `not_tested` |
| 10 WebSocket | Echter Browser-WSS inklusive Login und Recovery | Zielhost-/VPN-Reconnect `not_tested` |
| 11 Secrets fehlen | Unit- und realer Containerstart verweigert | Echte Secrets nie gelesen/erzeugt |
| 12 Ungültiger Produktionsstart | Guard-/Container-/Exportprüfung | Zielhoststart `not_tested` |
| 13 Versehentliche Veröffentlichung | Composeaudit verweigert Ports, Rollen, zusätzliche Router/Protokolle und Launcherumgehung | Live-Netzmitglieder/Firewall `not_tested` |
| 14 Backendneustart | Reale lokale Prozesse, persistenter Testroot, Browser-Recovery | Produktiver Restart/Hostreboot `not_tested` |

## Verbleibende Betreiberentscheidungen und Freigaben

Empfehlung: zunächst **Private HTTPS mit VPN und OIDC**. Bestätigen:
Profil/VPN-CIDRs, eigene Domain/DNS, IdP/Issuer/Subjects/Claims, individuelle Rollen/
Courses/Sourcegrants, sichere Secretbereitstellung, tatsächliche Backendrolle und
Revision mit vorhandener privater HTTPS-API, Netze/Proxy-IP, bestehende UI-Ressource
und Buildtyp, Zertifikat/ACME, RAM/Diskbudget, redigierte Proxylogs, Alarmziel und
Backup-/Rollbackbeleg. Ein `sleep infinity`-Container allein erfüllt den APIvertrag
nicht; keine zweite Instanz oder TLS-Downgrade als Ausweg.

Exakte spätere Offlinebefehle, Domain-/Portzuordnung in Coolify, Start/Update,
Health/Readiness und Wiederherstellung der vorherigen UI-Routen stehen im
[einzigen führenden Handbuch](https.md). Diese Schritte bleiben gesperrt bis zur
separaten expliziten Betreiberfreigabe. Kein Freigabecheck setzt automatisch
`production_approved`. Keine echte Alarmzustellung oder Zielhost-Restore/Last-/
OOM-/Zertifikatserneuerung durchgeführt. Kein Image-/Volumecleanup.

## GitHub, Integration und Aufbewahrung

Project #1 und bestehende C26-Issues geprüft; #100/#109/#110/#112/#113 und UI #14
bleiben offen, MAINT On Hold. B1/B3 im Backendreview, B2/B3 im UIreview; gemeinsam
integrieren, ohne automatischen Merge. Eigene Branches jeweils `feat/c26b-https`,
Worktrees `Personal_Assistant-c26b` und `personal-assistant-ui-c26b`.
Primäre Checkouts `gmp_compliance` und `personal-assistant-ui` unverändert.

Dokumente sind bis Review noch nicht in master/main integriert. Deshalb bleiben
beide eigenen Branches und Worktrees einschließlich der Testvenv erhalten;
Lebenszyklusabschluss bleibt ausdrücklich ausstehend. Nur die eindeutig selbst
angelegten lokalen Testcontainer/-prozesse und temporären synthetischen Testroots
werden vom Testtreiber beendet/entfernt. Lokale Reviewimages bleiben erhalten.

Maschinenlesbarer [Abschlussstatus](c26b_report.v1.json) und
[Containerbeleg](c26b_container.v1.json) ergänzen diesen Bericht.

Review-PRs: [Backend #137](https://github.com/rf-data/Personal_Assistant/pull/137)
und [UI #18](https://github.com/rf-data/personal-assistant-ui/pull/18). Beide offen
und ungemergt; keine Produktivfreigabe. Getesteter Code: Backend `1d8776c`,
UI `af69212`; spätere Änderungen ergänzen ausschließlich Dokumentationsverweise.
