# Deaktivierte Runtime-Konfiguration und eigener Mount

Stand 23.10.2026; Vorschlag, keine Pfad-/Betriebsfreigabe. Vorlagen:
[Controller](../../../deployment/c26-runtime.controller.json.example),
[Limits](../../../deployment/c26-runtime.limits.json.example),
[Offlineprüfung](../../../scripts/c26_runtime_preflight.py).

| Zweck | Vorgeschlagener Hostpfad | Containerpfad / Zugriff |
| --- | --- | --- |
| Neuer persistenter Runtime-Bind | `/srv/personal-assistant/runtime/c26-v1` | `/app/runtime-state`, RW |
| Neuer C16-Jobroot | Unterverzeichnis `c16` im obigen Bind | `/app/runtime-state/c16`, UID 10001, 0700 |
| Controller/Limits/Mountpolicy | `/srv/personal-assistant/configuration/c26-runtime` | `/app/configuration/c26-runtime`, RO, einzelne Dateien 0600 / UID 10001 |
| Historische Daten | bestehender `/srv/personal-assistant/data` | `/app/data`, jetzt nur RO für die neuen Rollen |
| Logs/Cache | bestehende geprüfte Mounts | `/app/logs`, `/app/.cache`, RW nur nach eigener Mountprüfung |

`/app/runtime` enthält bereits die Runtime-Lockdateien des Dockerfiles und wird
bewusst nicht übermountet. Der neue Bind erhält keine historischen Jobs, kein
SQLite und keine Katalogkopie. Es ist dieselbe C16-Queueimplementierung in einem
neuen Root, kein zusätzliches Queue-/Controller-/Transportprodukt. Keine zweite
aktive Runtime neben den genehmigten drei Rollen. Die historischen Controller
unter `cs50_pilot_01` und `cs50_pilot_week0_02` bleiben unverändert; sie sind
**operator_observed**, nicht die neue Betriebsfreigabe.

Der Controller verwendet Settings aus #148: schema 1, `max_jobs=max_queued=
max_parallel=1`, `worker_ttl=10`, Gate verpflichtend. Execution, Workflows, PDF,
Index und Import sind aus; Identitäten und Katalog leer. Ein unbekannter Bearer
wird abgelehnt. Der historische `execution_enabled=true`-Wert beweist keinen
laufenden Worker und wird nicht übernommen. `max_jobs=1` begrenzt gespeicherte
Jobs insgesamt, auch terminale: kein zweiter Batch ohne neue Freigabe, keine
automatische Joblöschung oder Limitsteigerung.

CapacityLimits bleibt schema 1: Reserve 5 GiB, Archiv 64 MiB, Katalog 128 MiB,
Jobroot 512 MiB, Report 16 MiB, höchstens ein Material. Dieses Modell hat kein
`enabled`-Feld. Die Limitsvorlage ist durch die deaktivierte Controllerbindung
und das gesperrte Composeprofil inaktiv; kein erfundenes Schemafeld. Ein Material
kann mehrere bestehende Workflowstufen haben; die konkrete Batchplanung muss
weiterhin `batch_size()` und C18/B6 sowie die Quellenfreigaben bestehen.

## Mountpolicy erst aus dem echten Zielnamespace

`PA_PERSISTENT_ROOTS_FILE=/app/configuration/c26-runtime/persistent-roots.json`
verwendet unverändert `src.runtime_paths`: Repository `/app`, exakt ein Grant
für `/app/runtime-state/c16`, Mountpoint `/app/runtime-state`, Zweck
`job_workspace`, UID 10001. `mount_identity` wird aus `/proc/self/mountinfo`
**im genehmigten Zielcontainer** gewonnen, nicht aus dem Hostgerät geraten.
Device, Mountroot, Dateisystem, Source und writable müssen exakt stimmen.
Ext4/XFS/Btrfs, kein verschachtelter Mount, keine Symlinks, private Rootrechte,
Policy 0600/UID10001 außerhalb des Jobroots. Kein pauschaler `/app/data`-Grant.
Die Erhebung ist Bestandteil der später genehmigten Provisionierung.

## Offline-Preflight ohne Queuezugriff

Nach ausdrücklich genehmigtem Bind/Policy/0700-Root im Zielnamespace:

```sh
python -m scripts.c26_runtime_preflight \
  --config /app/configuration/c26-runtime/controller.json \
  --limits /app/configuration/c26-runtime/limits.json \
  --runtime-mount /app/runtime-state \
  --runtime-image "$C26_RUNTIME_IMAGE" --gateway-image "$C26_GATEWAY_IMAGE"
```

Das Kommando prüft beide bestehenden Modelle, deaktivierte/identitätslose
Ein-Job-Konfiguration, unveränderliche Image-Referenzsyntax nach #148, echte
persistente Mountgrenze, private Rechte, Quarantäne, begrenzte Dateibaumgröße
und freien Platz für Reserve plus volle vier Budgetobergrenzen:
**6.123.683.840 Bytes = 5,703125 GiB**. Es initialisiert keine Queue, baut keinen
Store/Gate/Executor, öffnet SQLite nicht, schreibt keine Locks/Heartbeats und
startet keinen Prozess. Die Tests verbieten `sqlite3.connect` ausdrücklich.

Eine fehlende Queue heißt `uninitialized`; eine vorhandene Datei heißt
`present_unverified`. Beide melden `queue_healthy=false`, niemals Runtime-
Readiness. Valide Digestsyntax beweist weder Registryexistenz noch Build-SHA;
`image_provenance_verified=false` bleibt gesetzt. Der Test mountet nichts.
Ohne echten Mount oder ohne den vorgeschriebenen privaten Policygrant scheitert
die Prüfung. Vor Hostprovisionierung sind nur die isolierten Modell-/Vertragstests
möglich; kein angeblich grüner Produktionspreflight aus lokalen Platzhaltern.

Der konservative Vollbudgetcheck ersetzt weder das artefaktabhängige
`capacity.estimate(batch, limits)` noch Images/Backup/RAM-/B6-Preflight. Die
Kapazitätskontrolle ist keine Dateisystemquota. Historische SQLite-/Btrfsbefunde
stehen unverändert in [Diagnose](diagnostics.md). Das [Runbook](rollout.md)
trennt Provisionierung, Worker-Healthstart und spätere Annahmefreigabe.
