> Historischer G/H-Quellnachweis aus dem übernommenen Arbeitsstand; keine neue Livefreigabe. Aktuelle Betreiberanweisungen: [C26-Pilotchecks](c26_pilot_operator_checks.md). Neue Testbilanz: [Pilotvalidierung](c26_pilot_validation.md).

# C26-H – Laufzeitbindung und deaktivierter Bootstrap

25.10.2026. **Produktion HOLD. Keine Start-, Deployment- oder Live-Gatefreigabe.**
Quellen: [Inventar](c26h_integration_inventory.md), Abnahme: [Validierung](c26h_validation.md).

## Implementierter Umfang

Die D/E/F-Quellen wurden einmal kumulativ übernommen; G ergänzt ausschließlich
seine zehn lokalen Readiness-Dateien. Bestehende C16-Controller, Executor,
ContentStore, EvaluationStore, Search-/Index-API und Queue bleiben maßgeblich.
Es gibt keine zusätzliche Queue, keine neue Datenbankmigration und keinen neuen
Deploymentdriver. Details und Quellhashes stehen im Inventar.

`scripts.deployment` akzeptiert für `api`, `check` und `health --role api` die
expliziten Parameter `--content-config`, `--review-config`, `--search-config`.
Die vorhandenen privaten, versionierten Loader werden verwendet. Review muss
inhaltlich dieselben Contentsettings besitzen; Review/Search ohne Content und
überlappende Runtime-/Content-/Review-/Indexroots werden durch die bestehenden
Application-Verträge abgelehnt. Ein Worker akzeptiert diese API-Parameter nicht.
Aufrufe ohne Fachsettings bleiben für den bisherigen C16-Umfang kompatibel;
aktivierte Import-/Indexfunktionen müssen ihre bestehenden Abhängigkeiten erfüllen.

`check` konstruiert die Application nur zur Bindungsprüfung, ohne Controller-/
Storeinitialisierung. Die Regression vergleicht sämtliche vorhandenen Dateibytes
vor und nach dem Aufruf. `api` übergibt genau diese Settings an den vorhandenen
HTTP-Server und behält den gemeinsamen Wartungslock. Die Tests öffnen dafür
keinen Listener: `serve` wird durch einen prüfenden Testadapter ersetzt.
Private Modi, Symlinks, Versionen, fehlende Dateien und falsche Bindungen bleiben
Negativfälle; ContentStore-Integritätsfehler sind erwartete Ablehnungen.

## Ausschließlich neue Staging-Überlagerungen

| Datei | Funktion |
| --- | --- |
| `deployment/c26h.staging.compose.yaml` | Überlagert F-Backendbootstrap; API-/Healthcommands binden die drei Fachkonfigurationen. Eigener Projektname. |
| `deployment/c26h.staging.ui.compose.yaml` | Eigener UI-Stagingname, explizites inaktives Profil, `pull_policy: never`, `restart: no`. |
| `deployment/c26h.staging.content.json.example` | Eigene Contentroot und nur externe Cursor-Key-Dateireferenz. |
| `deployment/c26h.staging.review.json.example` | Eigene Reviewroot, dieselbe Contentbindung, Schreiben/reale Reviews deaktiviert, keine Grants. |
| `deployment/c26h.staging.search.json.example` | Eigene Indexroot. |
| `deployment/c26g.staging.controller.json.example` | Bytegleich aus G; obligatorisches v2, alle Ausführungsflags false, leere Identitäten/Kataloge. |

Die Backendüberlagerung benötigt `coolify.runtime-bootstrap.compose.yaml`;
die UI benötigt `coolify.ui.compose.yaml` und `coolify.private-https.yaml`.
Templates sind keine auf einen Host angewendete Konfiguration. Ohne explizite
Profile enthält das effektive Modell keine ausgewählten Rollen. Das ist eine
geprüfte Inaktivitätsgrenze, kein gestarteter Bootstrap.

Backendrollen verwenden UID/GID10001, readonly Root-FS, Cap-Drop, no-new-privileges,
begrenzte CPU/RAM/PIDs/Logs, feste Image-Digests, `pull_policy: never`,
`restart: no`, bestehende Bindmounts mit `create_host_path: false` und getrennte
Inputs/Schreibbereiche. Die API teilt den Gateway-Netznamespace; der Capacityworker
hat `network_mode: none`. Kein Docker-Socket und keine privilegierte Rolle.
Der UI-Container bleibt separat; sein vorhandener Vertrag fordert private HTTPS,
OIDC, individuelle spätere Tokenbindings und private externe Secretmounts.

`scripts.c26h_preflight` validiert normalisiertes effektives Compose-JSON und die
vier Settingsdokumente ohne Host-/Store-/Credentialzugriff. Es prüft H-Commands
zuerst exakt und projiziert anschließend nur die bewusst geänderten Felder auf
den weiterhin strengen G-Vertrag. Eingaben werden nicht verändert. Zusätzlich:
exakte Mountmengen, getrennte Quellen, begrenzte Ressourcen/Logs, persistente
Rootpolicy, deaktivierte Reviewrechte und feste Root-/Keyreferenzen.
Die CLI gibt bei ungültigem Input nur einen festen Refusalstatus aus.

Ein positiver Check liefert immer `production_release: HOLD` und
`deployment_permitted: false`. Die einzige lokal geschlossene G15-Teillücke ist
die Launcherbindung. Tatsächliche UID/Mounts, Storeinitialisierung, UI-Abnahme und
sämtliche Live-/Trustgates bleiben offen.

## Keine automatische Vertrauenskette

Der authentifizierte E-Collector ist ein begrenzter lesender Vertrag.
`Capture.gate_fixture()` verweigert `authenticated_read_only`; solche Captures
werden nicht zu D/F-Offlinebeweisen oder produktiven Permits umetikettiert.
Der gemeinsame H-Test prüft diese Ablehnung ausdrücklich.

D/F benutzen weiter `offline_fixture`, Fixtureissuer, einen Witness vom Typ
`local_test_only` und einen inerten Driver. Ein positiver Koordinatorlauf oder
synthetischer Rollback ist keine Autorität zur Containeränderung. Admission
bleibt ohne passenden Zustand geschlossen. Kein Livegrant, produktiver Verifier,
unabhängiger externer Witness oder mutierender Driver wurde ergänzt.

Der G-Verbundrestore verwendet echte synthetische Content-/Jobbackupfunktionen
und eine nur testweise SQLite-Sicherung des Reviewledgers unter dessen vorhandenem
Lock. Er ist ausdrücklich kein produktiver EvaluationStore-Verbundbackupadapter.
Ein Restore aktiviert nichts und ersetzt keinen vorhandenen Zielroot.
