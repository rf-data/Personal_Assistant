# C26 Final Runtime Integration — 23.10.2026

**GO für technisches Review und die drei lesenden Betreiberpakete. NO-GO für
Merge, produktiven Rollenstart, Coolifyumstellung und CS50P-Pilot.**
Die bestehende Draft-PR #157 wird fortgeführt; keine parallele Architektur-PR.

## Aktueller belegter Stand

Backend `e502aa9…` enthält #155; UI `e4be7a2…` enthält #19. Alle relevanten Drafts
sind aktuell offen und konfliktfrei Git-mergebar, ohne eingereichte Reviews oder
CI-Erfolgsbelege. Vollständige SHAs und Testbindungen: [Validierung](validation.v1.json).

Backend: Application / Dockerfile / Builder Deployment server. UI: Application /
Docker Compose, Service `streamlit`. Beide: Manual deployments only, Buildcache
und automatische Build-ARG-Injektion aktiviert, SOURCE_COMMIT Runtime only.
Diese Angaben sind **operator_observed**, nicht länger pauschal unbekannt.
Separate Preview-/Webhook-/API-/sonstige Trigger bleiben **unverified**.
Der Backend-Sleep-Start war ein bewusster Platzhalter; das ist keine versehentliche
Fehlkonfiguration. Konkrete Backend-Dockerfile-/UI-Compose-Pfadfelder und die
Herkunft der laufenden Images bleiben offen. [Inventar](operator_inventory.v1.json).

## Technische Ergebnisse

- Die vorhandene C22-Architektur bleibt: interner Caddy, API mit
  `network_mode: service:api-gateway` auf `127.0.0.1:8016`, genau ein bestehender
  C26-Kapazitätsworker, keine zweite Queue oder UI. [Source-to-Runtime-Matrix](source_assessment.md).
- Die [gesperrte Vorlage](../../../deployment/coolify.runtime-bootstrap.compose.yaml)
  erhält zwei kleine 4.4.7-Kompatibilitätskorrekturen: Label-Liste und einfache
  Bindvariablen mit weiter erforderlichen Pfadwerten in `x-required-paths`.
  Lokales daemonfreies Rendering: ohne Profil null, mit Profil drei Rollen;
  alle sechs leeren Pfade verweigert. Kein Container, Pull oder Build.
  [Versionsbezogener Befund und Abnahmegrenze](coolify_compatibility.md).
- Neue tmpfs-Testroots grenzen den bisherigen Btrfs-/ENOSPC-Befund weiter ein.
  386 bestanden, sechs optionale Fälle übersprungen; der frühere Docker-CLI-Fall
  blieb abgewählt. Zusätzlich 54 gezielte Fälle, drei kritische Kontrollen und
  sechs finale Definitionstests bestanden. UI: 24 Tests + neun Subtests bestanden.
  Fünf übersprungene HTML-Exportfälle wurden gezielt nachgeholt und bestanden;
  der Originaltranscript-Pilot bleibt mangels importiertem Bestand offen.
  Frühere rote Läufe bleiben erhalten. [Diagnose und Unsicherheit](diagnostics.md)
  und aktuelle Laufzahlen stehen in der Validierung. Der ursprüngliche SQLitecode
  ist nicht nachträglich rekonstruierbar; kein allgemeiner Produktfix behauptet.
- Geplante Rollen plus UI: 2.304 MiB. Bei 4 GiB und je 512 MiB OS-/Notfallreserve
  bleiben nur 768 MiB für sämtliche übrigen Dienste. Live-Fit und Buildpeak fehlen;
  im konservativen 1-GiB-Restdienste-Szenario fehlen 256 MiB. [Ressourcenbudget](resources.md).
  Lokales Btrfs, Test-tmpfs und Hetzner-ext4/Worker-Mount werden getrennt bewertet.

## A — Welche technische Arbeit fehlt wirklich?

Realen #148-Coolifydriver für bestätigte Ressourcen-/Image-/Triggerscopes
implementieren und prüfen; dieselbe Backend-Application sicher auf den vorhandenen
Composeverbund adoptieren; gebundene kombinierte Backend-/Gateway-/UI-Images bauen
und abnehmen. Vorhandenen UI-Service `streamlit` mit dem geschützten privaten
Zugriff verbinden, ohne zusätzliches `ui`. Tatsächliche Mount-/Cgroup-/TLS-/VPN-
Abnahme fehlt. Für den unklassifizierten früheren SQLitefehler bleibt eine
begrenzt dokumentierte Unsicherheit; die Btrfs-Umgebung ist nicht repariert.

## B — Welche Betreiberinformationen fehlen?

Drei Pakete reichen: (1) exakte Build-/Repository-/Branch-/Startpfade, UUIDs,
Imagebindung und zusätzliche Trigger; (2) eine echte Queue-/Writerzuordnung,
Controllerconfig/Mountpolicy/Limits sowie RAM-/CPU-/Backup-/Rollbackbelege;
(3) privater DNS-/TLS-/VPN-/OIDC-Bestand und konkret gebundene vorhandene
Quellen-/Rohartefakte. Jeder offene Wert hat einen lesenden Schritt in den
[Betreiberprüfungen](operator_checks.md). Bestätigte Manual-Deploy-/Buildwerte
werden nicht nochmals angefordert.

## C — Was ist der nächste konkrete Schritt?

Die drei lesenden Pakete liefern, zuerst die tatsächlichen Buildpfadfelder und
zusätzlichen Trigger in den bestehenden Coolify-Applications. Danach Restarbeit
an genau diese Werte binden. Nach ausdrücklicher Mergefreigabe
#156 -> #149 -> #148 -> #157, UI #20 abgestimmt separat. Erst anschließend ein
eigenes Bootstrap-/Build-/Rollbackfenster genehmigen und die
[zwölf Abnahmephasen](rollout.md) durchlaufen. [PR-Integrationsmatrix](integration_matrix.md).

Der erste Week-0-Pilot bleibt eine eigene Entscheidung: vorhandene Raw-Artefakte,
konkret gebundene SourceApprovals, frisches C18-/B6-Preflight, ausreichendes
Workerbudget und ausdrückliche Freigabe für genau einen begrenzten Job.
Infrastrukturvorbereitung erzeugt keine Pilot- oder Quellenfreigabe.

Keine Hetzner-/SSH-/Coolifyaktion, kein Deployment oder produktiver API-/Workerstart,
kein Merge/Ready/Auto-Merge, keine neuen Kursdownloads, ZIP-Imports oder Bereinigung.
Bestehende Pilotdaten, Worktrees, Umgebungen, Bundles und Locks bleiben erhalten.
Lokale Arbeitskopie weiterhin wegen des Indexfehlers uncommittet; reguläre Hooks
und GitHub-Git-API sichern die Reviewlieferung. Defaultbranchintegration bleibt
aufgrund des ausdrücklichen Mergeverbots ausstehend.
