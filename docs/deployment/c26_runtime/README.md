# C26 Runtime Configuration & Bootstrap Finalization — 23.10.2026

**GO für technisches Review und lesende Betreiberinventur. NO-GO für Merge,
Produktionsstart, Aktivierung und Pilot.** Bestehender Draft #157 fortgeführt.
Keine Host-/Coolifyaktion, kein Deployment, Merge/Ready/Auto-Merge, produktiver
Job, Download, ZIPimport oder Cleanup in diesem Auftrag.

## Lieferung und aktueller Stand

- [Deaktivierter Controller](../../../deployment/c26-runtime.controller.json.example):
  neuer Root `/app/runtime-state/c16`, Gate verpflichtend, max_jobs/queued/parallel1,
  Execution/Workflows/PDF/Index/Import false, Identitäten und Katalog leer.
- [Limitsvorlage](../../../deployment/c26-runtime.limits.json.example):
  schema1, Reserve5GiB, Archiv64MiB, Katalog128MiB, Job512MiB, Report16MiB,
  höchstens ein Material. Kein erfundenes enabled-Feld; deaktivierte Bindung.
- [Konfigurations-/Mountplan](runtime_configuration.md) und
  [Offline-Preflight](../../../scripts/c26_runtime_preflight.py): bestehende Modelle,
  keine Queueöffnung/-initialisierung, keine Locks/Heartbeats. Fehlende Queue
  ausdrücklich uninitialized; vorhandene Datei ausdrücklich nicht als gesund
  bestätigt. Image-Digestsyntax ist noch kein Registry-/SHAbeleg.
- [Bestehende Composearchitektur](../../../deployment/coolify.runtime-bootstrap.compose.yaml):
  Caddy + Loopback-API im selben Namespace + genau ein Kapazitätsworker, UI separat.
  Eigener vorgeschlagener Bind `/srv/personal-assistant/runtime/c26-v1`; historische
  Daten für neue Rollen nur RO. APIprofil startet ausschließlich Gateway/API;
  zusätzliches Workerprofil erfordert eigene Freigabe. Defaultcontroller verweigert
  Workerstart. Keine öffentlichen APIports, keine neuen Runtimeabhängigkeiten.
- [Zehnphasiges Betreiber-Runbook mit Kommandos](rollout.md): Inventory, Backup,
  SHA/Image, explizite neue Root-/Store-/Gateprovisionierung, Gateway/API, Health,
  Worker-Healthstart bei held, gesonderte Aktivierung, Einzelbatch, Rollback.

Historische Controller und Limits sowie RAM3,7GiB/Available2,2GiB/Swap4GiB mit
688MiB Belegung sind nun **operator_observed** im [Inventar](operator_inventory.v1.json).
Historische SQLite/Pilotjobs bleiben unverändert. execution=true belegt keinen
laufenden Worker. Neue Mounts/Roots und finale Settings sind **unverified**.

[Budget](resources.md): kleiner Batch konservativ **5,703125 GiB** einschließlich
5GiB Reserve; gemeldete20GiB reichen rechnerisch fürs reine Batchbudget.
Backups/Images/Growth separat. RAM ist eng: etwa717MiB von2,2GiB Available nach
1.536MiB neuer Rollenobergrenzen, nach512MiB Notfallreserve nur205MiB für Peaks.
Keine Lastabnahme, keine Grenze stillschweigend verändert. Lokales Btrfs-/tmpfs
ist kein Hetznerbefund; [SQLite-/ENOSPCdiagnose](diagnostics.md) bleibt offen
abgegrenzt, keine pauschale Heilung durch einen grünen Wiederholungslauf.

## Was noch ausschließlich der Betreiber ausführen muss

1. Exakte Coolify-UUIDs/Buildpfade/Branch/Overrides, zusätzliche Trigger, alle
   Writer/Queues, privaten TLS/VPN/OIDCweg und Ressourcenpeaks lesend belegen.
2. Nach separater Review-/Mergefreigabe #156 → #149 → #148 → #157 integrieren,
   UI #20 separat; kombinierte tatsächliche Versionen und gebaute Backend-/Gateway-
   Images per SHA/Registrydigest abnehmen. Kein normaler Merge als Deployfreigabe.
3. Vollständiges Backup/isolierten Restore, ruhenden Sleep-Rückweg und kontrollierte
   Adoption derselben Backend-Application freigeben. Kein zweiter Compose-/UIstack.
4. Eigenen Runtime-Bind/0700-Root und private Config/Limits/Mountpolicy ausdrücklich
   provisionieren. Offlineprüfung; danach bestehendem Store einmalig die leere
   Queue und dem Gate initial held anlegen lassen. Teilfehler geschlossen erhalten.
5. Nur Gateway und API starten, Namespace/Mount/TLS/401 und Gate held prüfen.
6. Separat den einen Worker-Healthstart mit execution=true in identitätsloser
   Stagingconfig freigeben. API bleibt false, Gate held, Queue leer. Heartbeat,
   Einzigkeit und RAM prüfen. Damit sind die drei Prozesse startbar, keine Jobs.
7. Erst nach eigener finaler Settings-/Identitäts-/Katalog-/Quellenfreigabe alle
   Rollen an dieselbe aktive Config binden, nochmals Live-/Negativchecks und neue
   Resume-Freigabe. Ein-Material-/Ein-Job-Pilot separat; keine automatischen Folgejobs.

**Zusätzlicher technischer Restpunkt:** Die Schritte sind noch nicht allein durch
Betreiberfreigaben vollständig: der reale reviewte #148-Driver/Koordinator für
Livebeobachtung des tatsächlichen Coolify-Ressourcenscopes fehlt weiterhin.
Ohne ihn kann `Gate.release` nicht sicher freigeben; die CLI prüft Pläne, führt
aber keinen Resume aus. Keine Fake-Observation als Ersatz. Erst echten Scope
liefern, Adapter binden/reviewen und abnehmen. Bootstrap selbst ist eine eigene
manuell geschlossene Wartungsoperation, kein vorgetäuschter Gate.run von Sleep.

## Validierung und Aufbewahrung

**137 finale Vertragsfälle bestanden**, keine Skips. Im breiten Lauf 345 Fälle
bestanden; zwei testinterne Erwartungen im neuen Bootstrapfall wurden danach
korrigiert, ohne Produktfix. Läufe überlappen, rote Belege bleiben erhalten.
Reguläre Hooks, Ruff, JSON-/Link- und zwölf Shellsyntaxprüfungen bestanden.
Aktuelle Tests und genaue Quellenbindung stehen in
[runtime_configuration_validation.v1.json](runtime_configuration_validation.v1.json),
frühere Läufe bleiben in [validation.v1.json](validation.v1.json) erhalten.
[Source-to-Runtime](source_assessment.md), [Coolify4.4.7-Grenzen](coolify_compatibility.md),
[Driververtrag](driver_contract.md), [PRmatrix](integration_matrix.md) und
[lesende Betreiberpakete](operator_checks.md) bleiben Teil der Reviewlieferung.
Alle fünf PRs erneut offen/Draft/konfliktfrei, abgefragte Reviews/Status/PR-Workflows
leer; fehlende Checks sind kein CI-Erfolg. Master e502aa9, UI-Main e4be7a2 unverändert.

Code/Unterlagen bleiben im Draft, nicht im Defaultbranch integriert: ausdrückliches
Mergeverbot. Lokaler Indexfehler bleibt unangetastet; reguläre Hooks und geprüfte
GitHub-Git-API-Folgecommits sichern die Lieferung. Bestehende Worktrees/Branches,
Venvs/Bundles/Quellarchive/Pilotdaten/Locks bleiben erhalten; kein Cleanup.
