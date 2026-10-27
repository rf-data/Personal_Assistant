> Historischer G/H-Quellnachweis aus dem übernommenen Arbeitsstand; keine neue Livefreigabe. Aktuelle Betreiberanweisungen: [C26-Pilotchecks](c26_pilot_operator_checks.md). Neue Testbilanz: [Pilotvalidierung](c26_pilot_validation.md).

# C26-G – Readiness- und Integrationsmatrix

Prüfstand 25.10.2026, Europe/Berlin. **Produktion HOLD.** Dies ist eine
Quellcode-/Offlineprüfung, keine Serverabnahme. Die Gate-IDs G01–G26 sind lokale
Referenzen dieses Berichts; sie ersetzen keine vorhandenen Issue-IDs.
[Validierung](c26g_integration_validation.md),
[Entscheidungen](c26g_operator_decisions.md), [Runbook](c26g_runbook.md),
[Go/No-Go](c26g_go_no_go.md).

## Quellen und tatsächlich untersuchte Gitstände

Gelesen: `AGENTS.md`, `docs/ROADMAP.md`, `docs/planning/governance.md`,
C22 `architecture.md`, `configuration.md`, `security.md`, `operations.md`,
`backup_restore.md`, `c22_validation.md`, C26 `https.md`,
`c26_release_readiness_2026_10_23.md`, MAINT-03-/03B-/04-/04B-Validierungen
und Restrisiken. Zusätzlich die versionierten D/E/F-Berichte und Runtimepläne
aus den unten genannten Gitobjekten, die Implementierungen und Tests.
Ältere Dokumente bleiben historische Nachweise; ihre offenen Punkte werden
nicht ungeprüft als aktuell fehlender Code wiederholt.

| Referenz | Lokal tatsächlich beobachtet | Aussagegrenze |
| --- | --- | --- |
| Zugewiesener Branch `feat/c26g-deployment-readiness` | `778367396cd52526eca59edd41c2367f5e43b897`, anfänglich sauber | Bereits vor Auftrag vorhanden; enthält MAINT-03/03B/04/04B-Commits, kein D/E/F |
| `master` | `c1007efdbac3c1544020f328a3a1347e481797ba` | Veralteter lokaler Branch, **keine** aktuelle Releasebasis |
| `origin/master` | `e68275205fefb7a5f6db42bc45060e505bfcefb5` | Lokaler Trackingref, kein heutiger Live-Nachweis |
| `feat/c26d-operation-gate-v2` und gleichnamiger Trackingref | `8b0ba2d4ab5d0cd6fc8dfa69783276efd929666f` | Separater Draftstand; Bericht nennt #161, erbt #148/#157 bereits |
| `feat/c26e-authenticated-runtime-collector` und Trackingref | `28e9a608d74270278cf037e35957d0bae08d50b2` | Separater Draftstand; #162, auf D aufgebaut |
| `feat/c26f-independent-coordinator` und Trackingref | `7ffb4ed6fd4d8433edf36fb4851a382b9b9c595d` | Separater Draftstand auf E; keine Defaultintegration behauptet |
| `audit/c26-operations-preflight` | `ecac8cfa844a7e4da9e0066a2c49c0c49fb3541d` | Separater #160-Bericht, damalige Betreiberangaben sind keine neue Messung |
| UI lokales `main` | `b2cf9ca`, laut lokalem Status 27 Commits hinter Trackingref | Nicht für die UI-Prüfung verwendet |
| UI `origin/main` / geprüfter UI-Code | `e4be7a2fbf5b20beda0db854462dd2d70c2c93ff` | Vorhandenes Gitobjekt mit HTTPS/OIDC und `streamlit[auth]`; kein Liveheadbeweis |
| UI separate C25-Zweige | `feat/dev01c-search-ui` `b6086f9`; `feat/dev02c-source-management` `0226c61` | Gegen den geprüften UI-Default nicht als integriert ausgeben |

GitHub-CLI-Leseversuche scheiterten an `api.github.com`-Verbindungsfehlern;
Connectorversuche lieferten Argumentbindungsfehler. Damit kein aktueller
Live-PR-/Review-/CI-/Merge- oder Defaultheadstatus verfügbar. Es wurde weder
gefetcht noch ein PR verändert. Die im D/E/F-Text genannten Draftzustände sind
historisch; vor späterer Integration erneut live prüfen.

## Implementierte Teilfunktionen und Nachweisklassen

**Quellcode auf der G-Basis:** C16 authentifizierte Queue/Executor/Scopes,
C18/C19 Workflows/PDF-Lebenszyklus, C22 verwaltete Rollen/Startprüfung/Wartungslock,
SQLite-/Workspacebackup und isolierter Restore; C23 ContentStore mit Raw/Parsed,
ACL, Recovery, unveränderlichen Blobs und eigenem Snapshot; C24 FTS5/Generationen,
Content-/Search-HTTP und kontrollierte Index-/Importjobs; persistenter
EvaluationStore und Review-HTTP. Letztere HTTP-/Jobverträge sind inzwischen im
Code vorhanden, obwohl die Roadmap vom 19.10. sie noch als geplant aufführt.
Reale Datenabnahme folgt daraus nicht.

**Nur im separaten D/E/F-Stapel:** Pflichtgate v1/v2, vollständiger
Dreirollenscope, synthetisches Einmalpermit und Journal; streng lesender
authentifizierter Collectorclient; Offlinekoordinator, Fixturegrant, separater
lokaler Witness und inerter Driver. Die historische Aussage „v2 wird nirgends
erzwungen“ trifft auf D/F nicht mehr zu, auf den G-Basiscode aber weiterhin.

**Synthetisch:** positive Runtimebelege, Buildreceipts, Identitäten, Nonces,
Approvalsignaturen, Witnesszustände, Driverwechsel und Restoretests dieses
Auftrags. Auch echte lokale SQLite-/flock-/Prozessoperationen belegen ausschließlich
die jeweilige Testumgebung. Kein Host-/Coolify-/TLS-/Registrybeweis entsteht daraus.

**Nur Betreiber:** tatsächlicher Host und Kosten, aktive Images und Rollen,
Netz-/Mount-/Queuezuordnung, Writer und Trigger, DNS/IdP/TLS, vollständige
Privilegieninventur, Secretbereitstellung, Alarmempfänger, RPO/RTO und Freigaben.
Betreiberbeobachtungen aus #160/#157 bleiben als solche erhalten, ungeprüft.

## Vollständige Gate-Matrix für den beschriebenen Releaseumfang

„Offline erfüllt“ bedeutet bestandener begrenzter Vertrag, niemals Produktions-GO.
Alle produktiven Gates unten sind offen. A = automatisierbarer Nachweis;
M = manuelle Entscheidung; A+M = beides erforderlich.

| Gate | Iststand / Kompatibilität | Fehlender Nachweis und Verantwortlichkeit | Art |
| --- | --- | --- | --- |
| G01 Releasebasis/Review | G und D/E/F nicht integriert; lokale Defaultrefs divergieren | Betreiber/Reviewer: live Heads, komplette Serien, CI/Reviews, Triggerwirkung; später regulär integrieren | A+M |
| G02 Backend-/Workerimages | Digestpflicht/Frozen-Locks und feste Entrypoints vorhanden; alte `api/Dockerfile` (3.11/FastAPI) ist kein C16-Image | D09: Python 3.12/3.13, uv/Base/Runtime-Digests, reproduzierbarer Build, Plattform, installierte CLI-/Nativepakete | A+M |
| G03 UI-Image/Authlib | Geprüfter UI-Code enthält `streamlit[auth]==1.65.0`; alte C22-Aussage „Authlib fehlt im Lock“ ist überholt | D09: Lockgraph/Authlib im **konkreten Image**, Launcher, Browsertest und Backend-/UI-Paarung | A+M |
| G04 Coolify/Proxy | UI-only- und Dreirollenbootstrap sind verschiedene Ressourcenverträge | D10: reale Version/Renderer, UUID/Server/Environment, Rückweg beim Buildtypwechsel, vollständige generierte Labels | A+M |
| G05 Trigger/Writer | „Manual only“ historisch operator_observed, keine vollständige Sperre | Betreiber: Git/Preview/Webhook/API/Registry/Scheduler/Deploykonten, wartende Deployments und externe Imports vollständig erfassen/sperren | A+M |
| G06 TLS/VPN/Ports | Private HTTPS-Allowlist/Origin/Forwarded-Prüfer vorhanden | SAN/CA/Rotation, echte RemoteAddr/VPN-Routen, IPv4/IPv6, externe Negativtests; historische Ports 8000/6001/6002 ungeklärt | A+M |
| G07 OIDC/Sessions/Secrets | UI-Issuer-/Subject-/Rollenbindung, Sessionalter, Token-Dateien; Backend prüft separat | D10: Issuer/Callback, individuelle Subjects/Scopes, 0600/UID, Login/Logout/Expiry/Widerruf und Cookieverhalten | A+M |
| G08 Zielstorage | Lokale SQLite-WAL/flock/fsync-Verträge; keine Hostabnahme | D10: lokale ext4/xfs/btrfs-Binds, Device/Inode/Namespace, UID10001, Quota/Reserve und Restoreplatz | A+M |
| G09 Queue/Executor | Getrennte API-/Worker-PID-Namespaces; API Loopback im Gateway-Netznamespace, Worker ohne Netzwerk | Genau ein Executor, Leases und alle Writer; echte cgroups/OOM/Stop/Cancel/Parentdeath auf isoliertem Ziel | A+M |
| G10 Pflichtgate D | D erzwingt v2 offline; Legacybootstrap wählt weiterhin v1-Default | Freigegebene v2-Rootpolicy für jeden Writer, geschlossenes Bootstrap, keine automatische Journalmigration | A+M |
| G11 Collector E | GET-/TLS-Pin-/Nonce-/Budget-/Redaktionsvertrag implementiert, Fakeerfolge | Private reale Producer, TLS/Readrechte/Zeit; Coolify serverseitige Freshness bleibt ausdrücklich unverified | A+M |
| G12 Herkunft/Trust | Receipthash/-identität gebunden; keine Registry-/Signaturprüfung implementiert | Unabhängige administrierte Buildautorität, Issuer-/Registry-/Manifest-/Plattformnachweis, Widerruf | A+M |
| G13 Koordinator F | Fixturebetrieb mit Challenge/Grant/CAS/Fencing und inerten Änderungen | Echte Betreiberverifikation ohne Signiermacht im Koordinator, unabhängiger externer Witness, eigener Betrieb außerhalb ersetzter Rollen | A+M |
| G14 Livegate/Driver | E-authenticated Capture wird von `gate_fixture()` abgewiesen; F nur `offline_fixture` | Separat versionierter, reviewter Livevertrag und permitpflichtiger mutierender Ressourcendriver; **kein Flagwechsel** | A+M |
| G15 API-/UI-Fachintegration | `scripts.job_control` unterstützt Content/Review/Search; `scripts.deployment api` reicht keine dieser Settings weiter | Verwalteten Launcher/Mounts/Read-/Review-/Search-/Import-/Indexverträge separat implementieren/prüfen; nicht Wartungslock umgehen | A+M |
| G16 Jobbackup | C22 sichert terminale gestoppte Jobs, Workflows und Artefakte | Reale Writerruhe, Größenlimit, Verschlüsselung, Offsite, Retention, Integritäts-/Restorebeleg | A+M |
| G17 Content-/Blobsicherung | Eigene ContentStore-Snapshot-API vorhanden | Scopeweite Betreiberautorität, konsistente Publikations-/ACL-/Blobprüfung, immutable Originalbytes und Incidentmarker bewahren | A+M |
| G18 Verbundrestore/Evaluation | Neuer gemeinsamer synthetischer Restore; EvaluationStore hat keinen integrierten Backup-/Restore-CLIadapter | Gemeinsamer Stillstand/Checkpoint, vollständige Rootliste, Ledger-/Head-/ACL-/Versions-/Jobreferenzprüfung und Restore in neue Roots | A+M |
| G19 Index/Keys/Secretsrestore | FTS5 abgeleitet; Cursor-/Token-/TLS-/OIDC-Geheimnisse getrennt | Rebuild oder konsistenter Indexrestore, Keyrotation/Cursorinvalidierung; Witness nie blind mit Jobroot aktivieren | A+M |
| G20 Monitoring/Health | C15 Regeln/Metriken, optionales privates Prometheus/Grafana-Profil | Eigene Vieweridentität/Scopes, echte Healthbinaries, Heartbeat/Queue/Quarantäne/Disk/Inodes/Backupalter; anderes Netz im C26-Bootstrap explizit anbinden | A+M |
| G21 Alarmzustellung | Monitoringtemplate enthält keinen Alertmanager und kein Routing | D11: Kanal/Empfänger/Eskalation, ausgelöster Testalarm **und** bestätigte Zustellung/Auflösung | A+M |
| G22 Restart/Crash/Rollback | Offline Fehler bleiben geschlossen; eigene neue Recovery-/Rollback-/Resumegrants | Zielhost stop-before-start, neuer Containerbeleg, kompatibles altes Image/Config/Daten, keine automatischen Retries; bei unklarem Claim HOLD | A+M |
| G23 MAINT-Restbefunde | Schemaimport in MAINT-04B korrigiert; breite Prozessläufe historisch rot | SQLite-lock-/Guardian-/Publikationshardlinkfehler kausal klären; keine Marker-/Timeout-/Hardlinkausnahme | A+M |
| G24 C23/C24 reale Qualität | Framework und technischer Raw→Parsed→Review→FTS5-Pfad vorhanden | D06 Originalpfadstrategie; D07 autorisierter Korpus/Bundles/Reviewer/Gold. Semantik/Qdrant optional und unfreigegeben | A+M |
| G25 C25 UI-Abnahme | Review-UI im geprüften UI-Stand; allgemeine Search-/Source-UI separate Zweige | G15 + abgestimmte UI-Revision, echte Browser-/Rechte-/Deep-Link-/404-/Search-/Importabnahme für vereinbarten Umfang | A+M |
| G26 Betriebsfreigabe | Kein produktiver Schritt dieses Auftrags ausgeführt | D11: benannte Verantwortliche, Kosten/Zeitslot/Rettungszugang/RPO/RTO, vollständige Evidenz und manuelles Go/No-Go | M |

## Wichtige Konfigurationsgrenzen

`deployment/compose.yaml` (C22), `deployment/cs50-worker.compose.yaml` und der
Draft `deployment/coolify.runtime-bootstrap.compose.yaml` **nicht kombinieren**:
sonst drohen zusätzliche Executor/Queues. Die UI-only-Datei darf nur an die
genehmigte API-Ressource gekoppelt werden. Für C26 gilt zunächst der private
VPN-Pfad, keine stillschweigende Umschaltung auf das vorhandene öffentliche Profil.

Die neue [deaktivierte G-Vorlage](../../deployment/c26g.staging.controller.json.example)
setzt v2 ausdrücklich und lässt alle Ausführungsflags/Identitäten/Kataloge aus.
Der G-Basiscode verwirft sie korrekt, weil er v2 nicht implementiert. Nur die
isolierte Verbundkopie versteht sie. Das ist ein testbarer Stagingvertrag, kein
produktionsfähiges Konfigurationspaket und kein Bootstrapbefehl.

`coordinator_test_required` bleibt aus/default: ein lokaler F-Testwitness darf
niemals als produktive Witnessfreigabe eingebaut werden. Bei aktivierter fachlicher
Runtime sind neue Settings/Scopes/Freigaben und eigene Tests erforderlich; die
G-Stagingprüfung verlangt weiterhin vollständig deaktivierte Einstellungen.
