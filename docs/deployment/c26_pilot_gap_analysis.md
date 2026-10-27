# C26-INT-02 – aktueller Lückenstand

27.10.2026. **HOLD; C26-04 bleibt DEFERRED.** Der
[Stabilisierungsbericht](c26_int_02_validation.md) ergänzt die folgenden
historischen Inventare und ersetzt keine damaligen Testresultate.

- Materialveröffentlichung nach hartem Cancel: tatsächliche Hardlinkursache
  eingegrenzt; atomarer No-replace-Fix und deterministischer Gegenbeleg geliefert.
- SQLite: zusätzliches BUSY bei `BEGIN IMMEDIATE` real erfasst und vor dem
  Transaktionskörper begrenzt behandelt. Keine Körper-/Commitwiederholung,
  keine Timeoutsteigerung, keine Quarantänebereinigung. Die drei ursprünglichen
  Fehler werden nicht pauschal als kausal vollständig geschlossen erklärt.
- Planlesung: abgeschlossene Ergebnisse werden auch bei während des Lesens
  entstehender Quarantäne gesperrt. Sichere, authentifizierte Streamlit-Anzeige
  liegt als vollständiger separater UI-Patch vor; tatsächliche Anwendung und
  Tests im UI-Repository stehen wegen Sandboxgrenzen aus.
- Zusätzlicher Such-Cursor-Testzeiteffekt auf unverändertem master und Kandidat
  belegt. Keine Änderungen an C24-R; Nachweise bleiben separat rot dokumentiert.
- Gemeinsame Backend-Gitmetadaten bleiben read-only. Eigener Liefercommit,
  reguläres Review und Defaultbranchintegration stehen aus. Kein Push/Merge
  wurde durch einen Connector oder eine zusätzliche Gitkopie umgangen.

Die bestehenden technischen/live Blocker (produktive Trustkette, Build-/Runtime-
closure, exklusive Trigger, Legacyrückweg, Host-/Netz-/OIDC-/Browserabnahme) bleiben
offen. Kein Teil dieses Auftrags erteilt eine eingeschränkte Hetznerfreigabe.

---

# C26-PILOT-INTEGRATION – aktueller Integrationsbefund

27.10.2026. **Reviewkandidat im Pilot-Workspace; Livebetrieb HOLD.** Die unten
bewahrte ursprüngliche C26-PILOT-Analyse beschreibt die unveränderte Defaultbasis,
nicht mehr den vollständigen Inhalt dieses Kandidaten. Kein Merge erfolgt.

## Verifizierte Basis und Herkunft

Backend-live-master und Ausgangs-HEAD: `a8af1d9372eb435d3e1331c33b047d21120d57c2`.
Lokaler Branch `master` ist dagegen `c1007ef…` und keine geeignete Integrationsbasis.
UI-live-main: `ba34e98c14e66921bf9c515c82a16201bc8baa1a`; Produktcode/Tests/Lock
identisch zum lokal verfügbaren `e4be7a2…`; der Connectorvergleich enthält nur
`docs/c26_https.md`. Keine UI-Produktänderung erforderlich oder vorgenommen.
Das ursprüngliche Paket `1f5328920888c97468a0329efca58cd9b198ffc5` wurde im eigenen
Evidence-Repository gelesen; acht Dokumente und historische Belege übernommen.

**#166:** Merge tatsächlich bestätigt. Sein Head `7783673…` enthält MAINT-Code,
nicht die angekündigte Gatekette. D/E/F sind keine Vorfahren dieses Mergebaums.
Die tatsächlichen G-/H-Dateien liegen im **staged Arbeitsstand** des bestehenden
H-Worktrees; sie sind kein freigegebener H-Commit. Dessen Provenienzmanifest
wurde vollständig gegen SHA-256 der Quelldateien geprüft (keine Abweichung).
Der fremde Worktree wurde ausschließlich gelesen. D/E/F wurden einmal als
kumulativer Diff `e682752… → 7ffb4ed…` nach erfolgreichem `git apply --check`
übernommen; danach die überprüften G-/H-Ergänzungen. Keine doppelte Serienintegration.

| Komponente | Quelle | Commit/PR | Auf Defaultbasis vorhanden | Jetzt im Kandidaten / fehlend | Konflikt | Teststatus |
| --- | --- | --- | --- | --- | --- | --- |
| C16 Auth, Owner, Queue, Guardian | Backend master | a8af1d9 | Ja | Wiederverwendet, keine zweite Queue | Kein Importkonflikt | Runtime/C16 und neue Gesamtregression; siehe Validierung |
| Gate v1 / Admission / Drain / Idle / Recovery | #148, geerbt in D/F | f98eedd; kumulativ adc56c4 | Nein | In Controller, Store, Executor integriert | Kumulativer Patch sauber | Aktueller 516er-Gatelauf bestanden |
| Runtime Observer / Scope / Cold Bootstrap | #157, geerbt in D/F | 80c31e5; kumulative Serie | Nein | Vorhandene Rollenscope-/Readinessverträge integriert | Keine MAINT-Überlappung | Aktueller Gatelauf + native Composechecks |
| Scope v2 / Commit- und Digestbindung | #161 | 8b0ba2d | Nein | Gatezustandsmaschine wiederverwendet, kein v1-Fallback | Kein Importkonflikt | Aktueller Gatelauf bestanden |
| Authentifizierter Read-only Collector | #162 | 28e9a60 | Nein | Gepinnter Client integriert; privater Liveproducer/Buildautorität fehlen | Kein Importkonflikt | Fake-only Negativ-/Timeout-/TLS-/DNSfälle bestanden |
| Unabhängiger Offlinekoordinator / CAS | #163 | 7ffb4ed | Nein | Grants/Claims/Fencing integriert; Liveidentität/Witness/Driver fehlen | Kein Importkonflikt | Offline- und Prozessfälle bestanden; kein Livepermit |
| G-Readiness und Restore | G-Arbeitsdateien via H | Kein G-Liefercommit | Nein | Vorhandene zehn G-Ergänzungen gesichert | Herkunft ausdrücklich Arbeitsstand | G/H-Offlinetests bestanden |
| H-API-/Content-/Review-/Searchbindung | H-Arbeitsdateien | #166 enthält sie nicht | Nein | Vorhandenen Launcher/Loader/Tests übernommen | Keine neue Fach-API | G/H-Offlinetests bestanden |
| Begrenzte Pilotruntime | C22 + bestehender CapacityExecutor | Dieser Kandidat | Teilweise | c26-pilot.compose.yaml, Controller/Limits, UIoverlay und Read-only-Prüfer | Eigenes Profil; nicht mit Gesamtstack kombinieren | Native Compose-/Negativtests; keine Images gestartet |
| tmpfs und Dockerbuildclosure | C22 und übernommene Runtime | Dieser Kandidat | Fehlerhafte Flowlisten | Kommas korrekt quotiert; fehlende Dockerignore-Ausnahme ergänzt | Bewusste Abweichungen von H-Quellhashes | YAML-/native Regression; siehe Validierung |
| HTTPS/OIDC/Session/Rollen/UI | UI main | ba34e98; Produktbaum e4be7a2 | Ja | Unverändert wiederverwendet | Keine UI-Codeübernahme ins Backend | 151 Standardfälle bestanden, 25 IPC separat |
| Autorisierter Einjobvertrag | C16 + Gate v2 + vorhandener Runner | Neue Integrationstests | Getrennte Teile | Synthetisches material_planning und Einjobgrenze verbunden | Ein SQLite-Quarantänebefund offen | Positive/negative Läufe und Fehler getrennt dokumentiert |
| Writer-Settingsbindung bei Admission/Dispatch | Bestehendes v2-Journal | Dieser Kandidat | Nein | Geladene API-/Executor-/Storepolicy an letzten Resumeplan gebunden | Bewusste v2-Härtung, v1 kompatibel | Aktueller 501er-Nachlauf bestanden |
| Kataloggrößenbudget | Vorhandener CapacityExecutor | Dieser Kandidat | Nur C16-Globalgrenzen | Deklariertes Pilotbudget wird vor Workerinitialisierung gegen hashverifizierte Eingaben geprüft | Keine neue Queue/keine Quota behauptet | Separater Capacity-/Worker-Nachlauf |
| Vollständiger Ergebnisinhalt | Bestehende C16-Application/MaterialPlan | Dieser Kandidat | Nur Metadaten | Authentifizierte, hashgeprüfte 256-KiB-Leseroute und echter UI-Client getestet; Streamlitwidget fehlt | Separater persistenter UI-Schreibpfad durch Sandbox blockiert | Backend-/Clientvertrag bestanden; Browseranzeige HOLD |

Die ursprünglichen P01/P03/P04 sind im **lokalen Quellkandidaten** wesentlich
bearbeitet, nicht auf master integriert und nicht live abgenommen. P02 bleibt
technisch offen: authentifizierte produktive Grant-/Producer-/Build-/Witness- und
Driverkette. P05–P08 bleiben Host-/Image-/Access-/Recoveryabnahmen. P09 ist nur
synthetisch getestet. P10/#111/C26-04 bleibt DEFERRED.

Quellnachweise: [H-Importhashes](../../artifacts/c26_pilot_integration/imported-h-files.json),
[H-Provenienz](c26h_source_provenance.json),
[Remoteabfragen](../../artifacts/c26_pilot_integration/remote-evidence.json).
Dateihashes und anwendbarer Gesamtpatch stehen im Handoff, siehe Validierung.

---

## Historische Analyse des Betreiberpakets 1f53289

# C26-PILOT – Integrationsbefund und fehlende Nachweise

Stand 27.10.2026, GitHub nur lesend abgefragt. Backend `master`:
[`a8af1d9372eb435d3e1331c33b047d21120d57c2`](https://github.com/rf-data/Personal_Assistant/commit/a8af1d9372eb435d3e1331c33b047d21120d57c2).
UI `main`:
[`ba34e98c14e66921bf9c515c82a16201bc8baa1a`](https://github.com/rf-data/personal-assistant-ui/commit/ba34e98c14e66921bf9c515c82a16201bc8baa1a).
Das sind Auditbasen, **keine freigegebenen Deploy-SHAs**.
Maschinenlesbarer Abrufbeleg: [source-evidence.json](../../artifacts/c26_pilot/source-evidence.json).

## PR-Zustand ist nicht Dateiverfügbarkeit

| PR | Livezustand | Head / Merge | Tatsächlicher Befund |
| --- | --- | --- | --- |
| [#148](https://github.com/rf-data/Personal_Assistant/pull/148) | open, draft, nicht gemergt | `f98eedd671c8a9d9eb58a3b957eda1a91713844d` | Gate v1 fehlt in master |
| [#157](https://github.com/rf-data/Personal_Assistant/pull/157) | open, draft, nicht gemergt | `80c31e52f76c1f3f62102b6884752b722f796e7c` | Scope/Observer fehlen in master |
| [#161](https://github.com/rf-data/Personal_Assistant/pull/161) | open, draft, nicht gemergt | `8b0ba2d4ab5d0cd6fc8dfa69783276efd929666f` | Erbt #148/#157 und bindet v2; fehlt in master |
| [#162](https://github.com/rf-data/Personal_Assistant/pull/162) | open, draft, nicht gemergt | `28e9a608d74270278cf037e35957d0bae08d50b2` | Auf #161 gestapelt; Collector fehlt in master |
| [#163](https://github.com/rf-data/Personal_Assistant/pull/163) | open, draft, nicht gemergt | `7ffb4ed6fd4d8433edf36fb4851a382b9b9c595d` | Auf #162 gestapelt; Offlinekoordinator fehlt in master |
| [#166](https://github.com/rf-data/Personal_Assistant/pull/166) | closed, merged, 25.10.2026 | Merge `a8af1d9`; Head `7783673` | Titel/Body kündigen D/E/F/G/H an; tatsächlicher Diff enthält 59 andere Dateien, insbesondere MAINT-/Parsing-/Workflowkorrekturen |

Der `#166`-Head `778367396cd52526eca59edd41c2367f5e43b897` trägt im lokalen
Commitobjekt den Betreff `fix(maint04b): restore workflow schema boundary`.
Weder Mergebaum noch Head enthalten `src/job_control/deployment_gate.py`,
`runtime_collector.py`, `deployment_coordinator.py`, `coolify_readiness.py` oder
`scripts/deployment_gate.py`; auch ihre Tests fehlen. `Settings` enthält keine
Gate-/Koordinatorflags. Der #163-Head ist kein Vorfahr dieser master-Basis.
Ein `merge_commit_sha` bei einem **offenen** PR ist kein Mergenachweis.

Abhängigkeit zur späteren technischen Integration: geeignete bestehende Serie
#161 (einschließlich #148/#157) → #162 → #163 prüfen, anschließend tatsächliche
Readiness-/Runtimebindings und erforderliche H-Integration neu reviewen.
Die geerbten Reihen nicht doppelt mergen. Kein automatischer Merge, kein
Cherry-pick in diesem Paket und keine Ableitung einer Livefreigabe aus Drafttests.
Auch der Offlinekoordinator aus #163 liefert laut Vertrag nur einen inerten
Driver und Testwitness, keine produktive Betreiber-/Witness-/Driververtrauensbasis.

## Komponentenmatrix

„Getestet“ meint ausschließlich die aktuellen Läufe in
[Validierung](c26_pilot_validation.md), nicht historische PR-Zahlen.
„Serverbereit“ verlangt zusätzlich echte Image-/Konfigurations-/Hostevidenz.

| Komponente | In master/main vorhanden? | Getestet? | Serverbereit? | Fehlender Nachweis |
| --- | --- | --- | --- | --- |
| C16 individuelle Backendauth, Viewer/Operator, Course/Owner | Ja, Backend | Aktuelle C16-Suite | Nein | Echte individuelle Identitäts-/Rollenbindung, Widerruf |
| UI-OIDC, Claims/Session, unbekannte Benutzer ablehnen | Ja, UI | Aktuelle UI-Suite | Nein | Gewählter IdP, Callback, echter Browser, Logout/Expiry |
| Origin, Forwarded-Header, sichere Cookies, WebSockets | Ja, UI + HTTPSoverlays | ASGI-/Guardtests aktuell | Nein | Traefikpfad, VPN/IPv4/IPv6, TLS/WSS live |
| C22 API-/Workerentrypoint | Ja | Operations-/Executortests | Nein | Tatsächliche Container, Namespace, Startupclosure |
| C22 Non-root, Health, read-only, Limits | Ja, Vorlagen | Statische YAML-/Locktests | Nein | #109: gebaute Images, OOM/PIDs/Restart/Cancel im Container |
| Authentifizierte Readiness | UI `ready` prüft C16 capabilities; API nur Handler | UI-/Handlertests | Nein | Kein universeller `/ready`-Endpoint; Versions-/Instanz-/Idlenachweis fehlt |
| Begrenzte Queue, Singleton, Cancel/Guardian | Ja | Executor-/Queue-/Contentiontests | Nein | Host-/Cgroup-/PID1-/Drainraces im Zielcontainer |
| Persistente Mountpolicy, Kataloghashes/Storage-/Source-ACL | Ja | Pfad-/Storage-/Securitytests | Nein | Endgültige Mountidentitäten und UID/fsync/WAL/Quota |
| Gate v1 #148 / Scope #157 / Gate v2 #161 | Nein | Fehlende Tests nicht ausführbar | Nein | Technische Integration, alle Writer, atomarer Drain/Idle |
| Runtimecollector #162 | Nein | Fehlende Tests nicht ausführbar | Nein | Integration, privater Producer, TLS/Freshness, Buildautorität |
| Offlinekoordinator #163 | Nein | Fehlende Tests nicht ausführbar | Nein | Integration plus produktiver Witness, Operatorauth, Driver |
| Angekündigte C26-H-Integration #166 | Nein hinsichtlich angekündigter Gatekette | Nicht nachweisbar | Nein | Tatsächlicher integrierter Code-/Testbaum statt PR-Titel |
| Coolify-Backendressource als drei Rollen | Nein, kein dediziertes Coolifyoverlay | Nicht vorhanden | Nein | Resource-/Netz-/Triggerbindung und geprüftes Rollenset |
| UI-Coolifyimage/-overlay | Ja, `coolify.ui.compose.yaml` | UI + statische Verträge | Nein | Reviewdigest, Route/Middleware, OIDC/CA/privates Netz |
| Konsistenter Backup-/Restorepfad | C22-/Content-Funktionen vorhanden | Nur synthetisch | Nein, separat | #111 bleibt DEFERRED, kein Zielrestore |

## Konkrete Restarbeiten

| ID | Priorität | Fehlende Arbeit / akzeptierbarer Abschluss |
| --- | --- | --- |
| P01 | P0 | Fehlenden Gatebaum technisch integrieren; neue Tests auf tatsächlicher Zielbasis, unveränderte C16-Queue |
| P02 | P0 | Produktive Collector-/Build-/Operator-/Witness-/Driverkette und exklusiver Triggerpfad; unklarer Driverstatus sperrt Resume |
| P03 | P0 | Für vorhandene Backendressource geprüftes Compose mit API/Gateway/Executor; eigener Pilotroot, keine zweite Queue; C22-Gesamtstack nur Referenz |
| P04 | P0 | Geprüftes Pilotoverlay für Ressourcen, `restart: no`, Swapbudget, Quota; gerenderte/effective Konfiguration und Images abnehmen |
| P05 | P0 | Exakte Hostmounts, `/app/.cache` versus `/app/cache`, Schreibrechte und Storageidentitäten ohne Altbestandsänderung bestätigen |
| P06 | P0 | IdP-/Subject-/Backendbindung, CA/SAN, Proxy/VPN/IPv6 und unabhängige Negativtests abnehmen (#110) |
| P07 | P0 | Wiederherstellbare Coolify-/Routing-/Secretkonfiguration und unveränderliche alte Images sichern; ohne Rückwegnachweis Änderung blockieren |
| P08 | P0 | #109 im isolierten Container: SIGTERM/KILL/OOM, Parent-Death, Health/Readiness, Limits, Queue und Abbruch nachweisen |
| P09 | P0 | Frischer synthetischer Minikatalog, `max_jobs=1`, alle weiteren Opt-ins false, keine produktiven Mounts |
| P10 | vor Voll-C26 | #111 vollständig: endgültiges Storage, unabhängiges Backup und isolierter konsistenter Restore aller relevanten Stores/Config/Secrets |

Wegen P01–P08 kann eine bloße Konfigurations-/Deploymentfreigabe den Pilot **noch
nicht** startklar machen. Dieses Paket benennt den Widerspruch; es erfindet keine
fehlende Produktionsimplementierung und löst HOLD nicht durch Dokumentation auf.
