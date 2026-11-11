# C26-B – Abschluss- und Freigabebeleg

Aktueller Folgeauftrag: [Worker-aware Gate und neue Offline-Abnahme](c26_gate_validation.md).
Die hier dokumentierten C26-B-PRs #137/#147 und UI #18/#19 sind inzwischen
verifiziert integriert. Die folgenden Lauf-/Fehlversuchs-/Gitbelege bleiben als
historische Evidenz erhalten und behaupten keinen heutigen Produktivstatus.

## Fortsetzung 22.10.2026

**Offline vorbereitet und erneut lokal synthetisch verifiziert;
`production_release_blocked`.** Die aktuelle Statusmatrix, VPN-Entscheidung,
priorisierten Betreiberangaben, gefilterten Hostkommandos sowie Rollout/Rollback
stehen im [aktualisierten führenden Handbuch](https.md). Keine SSH-Verbindung,
Produktionsänderung, echte Secrets, Downloads oder Pilotdatenzugriffe.

### Tatsächliche Integration und Bestand

- Live GitHub: Backend #137 `MERGED`, 20.10.2026 20:14:42 UTC, Merge `59e8d6b`;
  UI #18 `MERGED`, 20:13:43 UTC, Merge `49cf9ee`. Vollständige alte Taskheads
  `c364175` / `4c6c801` sind Vorfahren der aktuellen Default-Heads.
- `ls-remote` und geladene Commitobjekte: Backend-master
  `3b91d39195e0d13fe0442d4594b28e431b0f4236`, UI-main
  `49cf9ee172aa7f46357cf1fef53158fc9ba654e7`. Keine UI-Änderung seit #18;
  Backend #138–145 ergänzt Worker-/Mountpolicy-/Pilot-/Materialverträge.
  HTTPS-Deploymentvorlagen, Preflight und Acceptancehelper waren vor dieser
  Fortsetzung unverändert. C16-Rootprüfung und Guardian reichen jetzt die
  explizite Runtimepolicy weiter; neue Integrationsfälle wurden erneut geprüft.
- Primärcheckouts `gmp_compliance` (`65b3f09`, `feat/c20b-workflow-http`) und
  `personal-assistant-ui` (`b2cf9ca`, `main`) waren sauber, aber keine aktuellen
  Default-Checkouts. Alte C26-B-Worktrees waren sauber. Gemeinsame Trackingrefs
  ließen sich trotz geladenen Objekten lokal nicht ersetzen; sie wurden nicht
  als aktuelle Basis ausgegeben.
- Gesamte registrierte Worktreeinventur nur lesend: Fremde Änderungen u.a. in
  `c2406a`, `c26-integration` (einschließlich Mergekonflikten),
  `c26-integration-review`, `c26b6`, `c26b7`, `completion-audit`, `html-parser`.
  Historische fehlende/prunable Einträge ebenfalls erhalten, kein Prune, Reset,
  Stash oder Auflösen fremder Konflikte. UI-Worktrees ohne Dirtymeldungen.
  Ignorierte wertvolle Daten/Venvs wurden nicht als entbehrlich eingestuft.
- Neue auftragseigene Arbeitskopien: `Personal_Assistant-c26b-vpn` und
  `personal-assistant-ui-c26b-vpn`, jeweils Branch `feat/c26b-private-vpn-review`,
  von den obigen aktuellen Default-Commitobjekten. Kein Cleanup älterer Arbeiten.

### Sicherheitsbefunde und Korrekturen

1. **VPN-CIDR-Vertrag:** Python `is_private` verweigerte Tailscale-CGNAT, ließ aber
   Dokumentations-/Reservenetze zu. Jetzt explizite RFC1918-/CGNAT-/ULA-Teilnetze,
   strikt kanonisch. Einzelne genehmigte Geräteadressen bevorzugen. Das prüft
   Adressform, keine echte VPN-Geräteidentität oder Routingtopologie.
2. **Profil:** Das Private-Overlay setzt jetzt `C26_ACCESS_PROFILE=private-https`;
   der Audit verlangt Gleichheit mit dem CLIprofil, das UI verweigert fehlende/
   unbekannte Profile. Base-Compose allein ist kein freigegebener Betriebsweg.
3. **Header:** Doppelte Origin-Header wurden bisher wie fehlende behandelt.
   Jetzt verweigert; WSS braucht genau den genehmigten Origin, normale
   HTTP-Navigation/Callback darf ohne Origin erfolgen. Mehrdeutige
   Traefik-Labelschreibweisen werden ebenfalls abgelehnt.
4. **Launcher:** Alle drei Admin-Einstiege verweigern bei `C26_HTTPS=1` das
   Rendern außerhalb der eingerichteten HTTPS-Laufzeit. Auch der öffentliche
   `run`-Einstieg prüft Produktionseinstellungen. Dies schützt gegen versehentliche
   CLIumgehung, nicht gegen einen Administrator, der Code/Flags selbst verändert.
   Containerentrypoint, keine Ports, exakte Netze/Proxy-IP und Route bleiben Pflicht.
5. **Betrieb:** Aktuelle VPN-/Host-/API-/Netz-/Auto-Deploykonfiguration unbekannt.
   Die alte `sleep infinity`-/fehlende-Scripts-Aussage ist kein heutiger Hostbeleg.
   Kein zweiter Proxy/Gateway/API/Worker ergänzt. Issue #146 fordert ein atomisches
   workerbewusstes Deploymentgate; dieses ist nicht implementiert und gehört
   nicht als scheinbar fertiges Gate in diese HTTPS-Korrektur.

### Erneut tatsächlich ausgeführte Tests

| Abschließender gezielter Lauf | Ergebnis |
| --- | --- |
| Backend `tests/test_https_preflight.py`, echtes Compose-CLI, generierte Labels simuliert | **45 passed**, 27,08 s |
| Backend C26-Integrationssuite + bekannter C18-Snapshotfall | **26 passed, 1 failed**, 141,54 s |
| UI `test_https_security.py` | **11 passed**, 7,91 s |
| UI `test_container_runtime.py` | **9 passed**, 0,08 s |
| UI `test_controller.py`, RAM-Tempdaten | **31 passed**, 4,91 s |
| UI `test_ui.py`, RAM-Tempdaten | **12 passed**, 30,33 s |
| UI `test_deployment.py` | **4 passed**, 0,06 s |
| UI `test_live_client.py`, Authbindung/Rechteentzug/Cache | **17 passed**, 0,21 s |
| UI `test_live_ui.py`, Rechte/Fehler/Bestätigung | **6 passed**, 8,00 s |
| Vorhandener tatsächlicher Owner-/Course-/Viewer-UI-Test gegen aktuelles sauberes Backend | **1 passed**, 17,01 s |
| Echter Browser/TLS/Traefik/OIDC/C16/FTS mit aktuellem Code, RAM-Tempdaten | **16/16 passed** |
| Aktualisiertes UI-Image, isoliert `network=none`, keine Ports, UID 10001 | **5/5 passed** |

Neue strukturierte Rohbelege:
[Browser](c26b_vpn_e2e.v1.json), [Container](c26b_vpn_container.v1.json).
Die alten JSONberichte darunter bleiben unveränderte historische Belege.
Der neue Browserlauf verwendet tatsächliche synthetische RS256-Code-/JWKS-
Anmeldung, falschen State/Nonce, WSS, sichere Cookies, bestätigten Indexjob,
Such-/Quelldetails, APIneustart, Logout und Ablauf. Die vorhandene Test-CA-Ausnahme
im temporären Browser gilt weiter; striktes TLS wird separat positiv/negativ
geprüft. Kein Nachweis echten VPNs, Live-Coolifys, IdPs oder Browsertruststores.

Die C18-Abweichung bleibt unter
`tests/test_workflow_http.py::test_versioned_schema_snapshots_and_original_c16_models`
reproduzierbar. Es ist derselbe bereits am 20.10. auf unverändertem damaligem
master belegte Schema-/Artifactbefund. Keine Anpassung fremder Snapshots zur
Erzeugung einer grünen Gesamtsuite. Gesamtrepository-/Workflow-/Container-
Restart-/OOM-/Sigkillabnahme wurde durch diese gezielten Läufe nicht ersetzt.

Umgebung: vorhandene Backendvenv Python 3.12.12 und vorhandene C26-UI-Testvenv
mit eingefrorenem Streamlit/Authlib/Playwright; kein Dependency-/Lockupdate.
Lokaler Docker 29.2.1, kein Hetzner-Versionsnachweis. Lokales neues UI-Image:
`c26b-ui:vpn-review-20261022`, Inspect-ID
`sha256:48fdb3dd3e09b04e0fb5c206b0c76f79796b9544e5f262fcd9aba5028613b146`.
Buildinputs unverändert aus UI `docker/c26-build-inputs.json`, Runtimeinstall
aus Cache. Kein Push des Images, kein freigegebener Registrydigest.
Die beiden Build-ARG-Warnungen betreffen absichtlich fehlende Standardwerte;
die tatsächlich übergebenen Werte sind gepinnte Manifeste.

Entwicklungsläufe und Umgebungsgrenze: Auf dem lokalen Projekt-/`/tmp`-Dateisystem
scheitern atomare Ersetzungen mit `ENOSPC`, obwohl `df` etwa 2,3 GiB frei meldet.
Erster Controllerlauf: 31 Tests, 8 Errors mit `os.replace`; erster UIlauf:
12 Tests, 2 Failures/2 Errors. Unveränderter Code besteht beide auf RAM-Tempdaten.
Erster Browserversuch: zwei Stationen bestanden, dann `CalledProcessError` beim
Testcontainerstart; erster Containerversuch brach ebenfalls beim positiven
Dockerstart ab, kein vollständiger Ergebnisbeleg. Wiederholung mit RAM-Tempdaten
bestand vollständig. Erster Imagebuild scheiterte am Ersetzen von Buildx-
Aktivitätsmetadaten; isoliertes `BUILDX_CONFIG` im RAM ermöglichte den Build.
Ruffcache-Ersetzung scheiterte ebenfalls, anschließender Check mit `--no-cache`
bestand. Ein anfänglich ungültiger `RUFF_NO_CACHE=1`-Wert wurde zu `true` korrigiert.
Fehlversuche werden nicht als erfolgreiche Abnahmen gezählt. Kein Zusammenhang
mit produktivem Hetznerstorage behauptet, keine automatische Daten-/Imagebereinigung.

Zusätzlicher bestehender Rollen-E2E: Der erste Lauf brach nach 20,10 s mit
`Bounded test backend response timeout` ab. Der unveränderte Harness startete
danach isoliert mit `ready=true` und sauberem Exit in 5,89 s; die unveränderte
Wiederholung des vollständigen Rollenfalls bestand in 17,01 s. Weder Timeout
noch Assertions wurden erhöht/abgeschwächt. Das ist ein separates lokales
synthetisches Rollen-/C16-Ergebnis, keine echte IdP-/Produktivrollenabnahme.

Reproduktion mit vorhandenen Umgebungen auf einer **lokalen Testmaschine**:

```sh
# Variablen bewusst auf die vorhandenen geprüften Umgebungen/Checkouts setzen.
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$C26_BACKEND_PYTHON" -m pytest -q \
  -p no:cacheprovider tests/test_https_preflight.py
# Im UIcheckout; nur mit freiem Loopbackport 8501 und lokalem Docker:
TMPDIR=/dev/shm "$C26_UI_PYTHON" scripts/acceptance/c26_https.py \
  --backend-repo "$C26_BACKEND_REPO" --backend-python "$C26_BACKEND_PYTHON" \
  --output "$C26_NEW_E2E_REPORT"
TMPDIR=/dev/shm "$C26_UI_PYTHON" scripts/acceptance/c26_container.py \
  --image c26b-ui:vpn-review-20261022 --output "$C26_NEW_CONTAINER_REPORT"
```

Alle eigenen Testcontainer wurden vom jeweiligen Treiber beendet/entfernt;
abschließende Namensabfrage ergab keine verbliebenen `c26b-test-*` oder
`c26b-ui-test-*`. Images/Cache und vorhandene Venvs bleiben erhalten.
Neue Review-PRs dürfen nicht automatisch gemergt oder deployt werden. Dauerhafte
Integration dieser Fortsetzung in master/main bleibt bis Review/Merge ausstehend;
deshalb eigene Branches/Worktrees behalten. Die folgende alte Abschlussdarstellung
ist ausdrücklich historisch und wird nicht als heutiger Merge-/Hoststand ausgegeben.

Git-Schreibgrenze: Normales Staging konnte den bestehenden Index nicht ersetzen.
Ein separater RAM-Index bewies den erwarteten Diff. Für reguläre Commits werden
separate temporäre Gitmetadaten im RAM mit dem vorhandenen Objektbestand als
Read-only-Alternative verwendet; die Backend-Commithooks bleiben aktiv. Neue
Commitobjekte werden anschließend per Git in den dauerhaften Objektbestand
übernommen und in zusätzlichen auftragseigenen Reviewworktrees referenziert
(`Personal_Assistant-c26b-vpn-review`, `personal-assistant-ui-c26b-vpn-review`,
lokale Sicherungsbranches `review/c26b-private-vpn-validated`). Das Backendreview
ist an diesen Branch gebunden. Bei der UI scheiterte die anfängliche HEAD-
Symrefanlage ebenfalls an ENOSPC; derselbe Commit wurde erfolgreich als
detached Reviewworktree ausgecheckt und zusätzlich durch den neuen Branch
gesichert. Die ursprünglichen neuen
`*-c26b-vpn`-Arbeitskopien bleiben mit ihren Änderungen erhalten; sie stehen
weiter auf der Basis und werden nicht als eingecheckt ausgegeben. Keine Reparatur
gemeinsamer Indizes/Trackingrefs, kein Force-Push oder automatischer Merge.

Reviewveröffentlichung: [Backend #147](https://github.com/rf-data/Personal_Assistant/pull/147)
und [UI #19](https://github.com/rf-data/personal-assistant-ui/pull/19), jeweils
`feat/c26b-private-vpn-review` gegen master/main. Getesteter Backendcode
`c8c06fdb3e45e7bb454b8153bd0efe6f194e8199`, UIcode
`371befb298f5acd55bafde8d0a20ee256cfdf229`. Dieser spätere Backendcommit ergänzt
nur den Abschlussbeleg mit Rollenlauf und Veröffentlichung. Er wird in einer
weiteren sauberen auftragseigenen Arbeitskopie `Personal_Assistant-c26b-vpn-final`
(detached, zusätzlicher Sicherungsbranch `review/c26b-private-vpn-final`) erhalten.
Die erste Backendreviewkopie behält die Änderungen dieses Belegs auf ihrem
ursprünglichen Codecommit. Alle eigenen Arbeitskopien bleiben wegen offener
PR-Integration und der lokalen Schreibstörung erhalten. Kein Lifecycle-Cleanup
als abgeschlossen behauptet; alte fremde Branches/Worktrees bleiben unangetastet.

## Historischer Prüfstand 20.10.2026

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

## Reproduktion der Backendprüfungen

Im Backendcheckout mit vorhandener Testumgebung (synthetische lokale Prozesse und
Loopbacksockets erlauben; keine echten Settings oder Kursdaten einbinden):

```sh
set -eu
: "${C16_PYTHON:?Vorhandene Backend-Testumgebung}"
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1
"$C16_PYTHON" -m pytest -q -p no:cacheprovider tests/test_https_preflight.py
"$C16_PYTHON" -m pytest -q -p no:cacheprovider \
  tests/test_deployment_transport.py tests/test_deployment_operations.py \
  tests/test_content_http.py tests/test_content_search_http.py tests/test_workflow_http.py
```

Der ursprüngliche gemeinsame Lauf enthielt dieselben Dateien plus die damals
20 Preflightfälle; heute sind es 24 neue Fälle. Der weiterhin bekannte Fehler heißt
`tests/test_workflow_http.py::test_versioned_schema_snapshots_and_original_c16_models`.
Der isoliert bestandene frühere Lockfehler war
`test_stale_resume_runs_only_required_stages_and_preserves_old_bytes[normalized]`.
Kein Snapshot wurde passend zu dieser Aufgabe umgeschrieben. Vergleichsbasis ist
ein unverändertes `git archive 449437b` mit derselben Pythonumgebung und exakt
obigem Schemasnapshottest.

UI-/Browser-/Containertestbefehle stehen im zugehörigen
[UI-Testnachtrag](https://github.com/rf-data/personal-assistant-ui/blob/feat/c26b-https/docs/c26_https.md).
Die Containerprobe verwendet das lokal gebaute Reviewimage; der maschinenlesbare
Containerbeleg bindet dessen tatsächliche Image-ID. Diese ID ist kein freigegebener
Registrymanifest-Digest und wird nicht als Produktionswert in die Vorlagen gesetzt.
