> Historischer G/H-Quellnachweis aus dem übernommenen Arbeitsstand; keine neue Livefreigabe. Aktuelle Betreiberanweisungen: [C26-Pilotchecks](c26_pilot_operator_checks.md). Neue Testbilanz: [Pilotvalidierung](c26_pilot_validation.md).

# C26-H – Integrationsinventar

25.10.2026. **Produktion HOLD. Kein Deploymentnachweis.**

Basis und ursprünglicher Ziel-HEAD: `778367396cd52526eca59edd41c2367f5e43b897`; Branch `feat/c26h-controlled-integration`, anfangs sauber. Gemeinsamer Vorfahr mit F: `e68275205fefb7a5f6db42bc45060e505bfcefb5`. D ist Vorfahr von E, E von F. Keiner dieser Heads ist Vorfahr der H-Basis; Vorgängeränderungen werden einmal kumulativ übernommen. MAINT-03/03B/04/04B bleiben in der Basis erhalten.

| Komponente | Ursprung / Commit | In Basis? | Abhängigkeiten | API / Vertrag | Tests | Konflikt / Risiko | Technik |
|---|---|---|---|---|---|---|---|
| Operation Gate v2 | D 8b0ba2d4ab5d0cd6fc8dfa69783276efd929666f | Nein | Gate-v1 Vorgänger, Store/Controller/Executor | Gate/PlanV2/ApprovalV2/Journal, admission/dispatch | deployment_gate, deployment_gate_v2 | Keine Textkollision; v1 nicht Ersatz | Kumulativer geprüfter F-Diff |
| Authenticated Collector | E 28e9a608d74270278cf037e35957d0bae08d50b2 | Nein | D, Observer, HTTPX | Capture/BuildReceipt, gepinnte GETs, gate_fixture verweigert authenticated | runtime_collector, coolify_observer/readiness | Live→Offline-Grenze bleibt geschlossen | In F enthalten |
| Independent Coordinator | F 7ffb4ed6fd4d8433edf36fb4851a382b9b9c595d | Nein | D/E, lokaler Testwitness | OfflineCoordinator, SignedGrant, CAS/Epoch, inerter Driver | deployment_coordinator, coordinator_contracts | Kein produktiver Verifier/Witness/Driver | F-Diff ohne Doppelübernahme |
| Readiness / Runner | G 778367396cd52526eca59edd41c2367f5e43b897 plus zehn lokale neue Dateien | Nein | D/E/F für positiven v2-Nachweis | c26g_preflight.check, archivierter Offline-Runner | c26g_readiness (28), c26g_restore (1) | G-Commit enthält G-Arbeit nicht; Hashprovenienz nötig | Nur indexinventarisierte neue G-Dateien kopieren |
| C16 API / Executor | H-Basis 778367396cd52526eca59edd41c2367f5e43b897 | Ja | Settings, SQLite, guardian, Rollenlocks | Application/serve, Controller/Executor | job_control/executor/store_contention, deployment_operations | Exit 1/3, SQLite/Quarantäne offen | F-Hunks in Basis anwenden; keine Whole-File-Ersetzung |
| ContentStore | H-Basis 778367396cd52526eca59edd41c2367f5e43b897 | Ja | private Roots, Blobs, ACL | ContentReadSettings, ContentHTTP, backup/restore | content_store*, c26g_restore | Managed Launcher bindet Settings noch nicht | Bestehenden Loader/HTTP verwenden |
| EvaluationStore / Review | H-Basis 778367396cd52526eca59edd41c2367f5e43b897 | Ja | ContentStore, Reviewlock, Ledger | ReviewSettings, ReviewHTTP, EvaluationStore | evaluation_store, review_http, c26g_restore | Produktiver Verbundbackupadapter fehlt | Launcherbindung; Backup nur Testtechnik |
| Search / Index | H-Basis 778367396cd52526eca59edd41c2367f5e43b897 | Ja | Content, FTS5, getrennte Indexroot | SearchSettings, SearchHTTP, IndexHTTP | content_search*, content_index* | Fachsettings fehlen im Launcher | Vorhandene APIs und Queue behalten |
| Container / Compose | C22 in Basis; Bootstrap in F | Teilweise | UID10001, bestehende Binds, Digests | scripts.deployment, cs50_worker, Composeprofile | deployment_operations, runtime_bootstrap/preflight | G15 Fachbinding, staging/production abgrenzen | Separates deaktiviertes H-Template |
| Health / Logging / Monitoring | C22/C15 in Basis | Ja | Rollenheartbeat, private TLS, Loglimits | health, metrics, Prometheus | monitoring_config, pipeline_metrics | Kein realer Alarm-/Hostnachweis | Bestehende Healthchecks erhalten |
| Backup / Restore / Rollback | C22/C23 in Basis; D/F Rollback | Teilweise | Gestoppte Writer, private neue Roots | operations.backup/restore, content backup, Coordinator rollback | c26g_restore, deployment_operations, coordinator | SQLite-/Hardlink-Crashfenster; kein Liveverbundadapter | Synthetisch prüfen, nicht produktiv erweitern |
| UI / Backend | Backend Basis, UI separat | Teilweise | OIDC, individuelle Bearerbindings, DTOs | C16, content_read_v1, search_v1, review-v1 | https_preflight, Content/Review/Search HTTP | UI-SHA/Browser/IdP separat abnehmen | Kein Eingriff ins UI-Repository |

## Tatsächliche Gitbeobachtung

- `feat/c26d-operation-gate-v2`: `8b0ba2d4ab5d0cd6fc8dfa69783276efd929666f`
- `feat/c26e-authenticated-runtime-collector`: `28e9a608d74270278cf037e35957d0bae08d50b2`
- `feat/c26f-independent-coordinator`: `7ffb4ed6fd4d8433edf36fb4851a382b9b9c595d`
- `feat/c26g-deployment-readiness`: `778367396cd52526eca59edd41c2367f5e43b897`
- `master`: `c1007efdbac3c1544020f328a3a1347e481797ba`
- `origin/master`: `e68275205fefb7a5f6db42bc45060e505bfcefb5`

GitHub-Connector GET `/branches?per_page=100` bestätigt die vier D/E/F/G-Heads live identisch. Live-master: `ec5e90696a54fcbd2f8b4ccfcc1f3e1ec61d56c0` (abgefragt am 25.10.2026); lokale Defaultrefs sind veraltet. Shell-ls-remote scheitert an DNS; einzelne URL-encoded Branchnamen am Connectorpfadvalidator. Collection-GET erfolgreich. Keine Remoteänderung, kein fetch. G-Berichte wurden aus seinem lokal inventarisierten Index/Arbeitsbaum gelesen; keine Behauptung, sie seien Teil des G-Commits.

## Abschließender Arbeitsdateistand

Die einmalige F-Differenz umfasst 91 Pfade; D und E sind nachweislich F-Vorfahren.
Beim Import stimmten alle 91 Dateien SHA-256/byteweise mit ihrem F-Quellobjekt
überein. Abschließend bleiben 90 unverändert; nur
`tests/test_c26_runtime_bootstrap.py` erhält eine lokale Importsortierung für
Ruff I001. Quellhash und finaler H-Hash werden getrennt ausgewiesen. Die späteren MAINT-Dateien der H-Basis wurden nicht ersetzt. Die zehn
G-Dateien stimmen jeweils mit dem ursprünglichen Importmanifest, dem weiterhin
unveränderten G-Arbeitsbaum und dessen Indexblob überein. **Keine dieser zehn
Dateien ist im G-HEAD enthalten.** Keine doppelte D-/E-/F-Übernahme.

H-HEAD bleibt die Ausgangsbasis. Weder ein lokaler Integrationscommit noch eine
Commitkette D→E→F→G→H wurde erzeugt. Eine erfolgreiche Arbeitsdateiübernahme ist
kein Git-/Defaultbranch-Integrationsnachweis. Der oben vermerkte Liveabruf gehört
zum vorherigen Lauf; die Fortsetzung hat keine neuen Remoteabfragen vorgenommen.
Lokale Referenzen und fremde Arbeitsbäume bleiben erhalten.

Vollständige 101-Pfad-Provenienz mit Quell- und Arbeitsdateihashes:
[Source-Provenienz](c26h_source_provenance.json). Prüfungen und Paketabschluss:
[Validierung](c26h_validation.md). Eigene H-Änderungen ergänzen Launcherbindings,
deaktivierte Backend-/UI-Overlays, drei Fachsettingsvorlagen, Preflight/Runner,
H-Regressionen und eine begrenzte Reparatur ausschließlich der C16-Testprobe.

## Zehn übernommene lokale G-Dateien

Quelle jeweils: `Personal_Assistant-c26g`, neuer Indexeintrag gleich Arbeitsdatei;
Quellbasis `778367396cd52526eca59edd41c2367f5e43b897`, kein eigener G-Quellcommit.

| Datei | SHA-256, Quelle = H-Arbeitsdatei |
| --- | --- |
| `deployment/c26g.staging.controller.json.example` | `62bd45021cef11f0c3daa8496fc810fe0f2fccb615d89ca8945b3311206c7f4e` |
| `docs/deployment/c26g_go_no_go.md` | `10b0a144c3f52088f8a2900c2d0c093628468b0b4ab0846b48f1aa66614b3c03` |
| `docs/deployment/c26g_integration_validation.md` | `523fee61960836244dca8979041d4a007de8977fc404f2cf92d927e61bfa995c` |
| `docs/deployment/c26g_operator_decisions.md` | `53b7e3378898ad03932f6418b9084b5dd308d29fe8b360b5601d8ab67a1a7c16` |
| `docs/deployment/c26g_readiness_matrix.md` | `991da768b28f984c6a3ae22e19ce6f54b0935820db6005c992b9c8e53b39ce7b` |
| `docs/deployment/c26g_runbook.md` | `b225a77ad40d1e7fca1dc6394b7cbd6be6b5a2b7974e4361a6533b5da69fa8fd` |
| `scripts/c26g_offline_validation.py` | `c06169d990a7e8f8f14428755499116fd07d8b30dda746e3451d184cdd163b2d` |
| `scripts/c26g_preflight.py` | `f508fad6b6972ddaaa1db96d948e3571b3cf0e0d45d65c8c792c668e60ecad52` |
| `tests/test_c26g_readiness.py` | `c7b901383de38351d13145ca7b9ab438a7e05c83c56be53cf1580466329590b3` |
| `tests/test_c26g_restore.py` | `25fa9bb1a0aa66a8df9d8ba88a179689b62fa6cd27f61c209922197a3545f034` |
