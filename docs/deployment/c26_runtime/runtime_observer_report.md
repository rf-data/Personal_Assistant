# Bericht A – Runtime Observer (24.10.2026)

**GO für Offline-Review. NO-GO für Livebetrieb, Deployment und Freigabe der Queue.**
Fortsetzung im bestehenden Draft #157, keine zweite Clientbibliothek oder
Gatezustandsmaschine. Keine Host-/Coolify-/SSH-Aktion, kein Containerstart,
Merge/Ready/Auto-Merge, Kursdownload, ZIPimport oder produktiver Job.

## Implementierung und Grenze

[`observe_runtime(binding, plan)`](../../../src/job_control/coolify_observer.py)
verknüpft den vorhandenen `CoolifyReadClient` mit einem unabhängig injizierten
Metadatenadapter. Der Readclient behält seine zwei festen GET-Pfade. Der Observer
prüft Membership, genaue drei Rollen/Services, Image-ID **und** RepoDigest,
unabhängige Buildreceipt/Commitbindung, Entrypoint-/Prozessvertrag, Mounts und
Jobroot-Geräte-/Inodeidentität, tatsächliche Settings je API-/Workerrolle,
Caddy-/Compose-/Settingshashes, private Netzwerke,
Namespaces, fehlende Hostports, API-/Gatewayhealth, Workerheartbeat und vollständige
Trigger-/Writerbelege. Die bestehende `check_snapshot` wird wiederverwendet.
Ein fremder Container mit überlappendem schreibbarem Mount verweigert auch dann,
wenn er zu einer anderen Application gehört. Widersprüche zwischen Inventar,
Container- und Imageabfragen verweigern ebenfalls.

Fehlende Belege, `None`, Fehler oder Drift ergeben `status=NO-GO` und ein explizites
`unverified` mit festen Diagnosecodes. Erfolgreiche Replays heißen ausschließlich
`verified_offline`; **immer** `deployment_permitted=false`,
`production_release=blocked`. Kein `healthy`-Gatebeleg und kein Deploymentpermit.
Zwei Beobachtungen müssen jeweils vollständig/frisch sein; Instanzen, Namespace,
Phase, Deploymentreceipt, Host-/Adapterbindung und Operationscope müssen stabil
bleiben. Ein abgebrochenes Paar bewahrt keine ältere Freigabe.

Der bestehende Sleep-Platzhalter erfüllt diesen Dreirollenvertrag absichtlich
nicht. Die gemeldeten Image-IDs belegen die lokalen Containerreferenzen, weder
Registry-Provenienz noch genehmigte neue Runtimeimages. Keine Queueadoption aus
historischen Pilotroots. Die bestehende Caddy-/Loopback-/Einzelworkerarchitektur
und alle deaktivierten Composeprofile bleiben unverändert.

## Versionierter Scopevertrag

- [`RuntimeScope`, Schema 1](runtime_scope.v1.schema.json): Application und
  geschützte UI, Server/Environment, Repository/Branch/Composeprojekt, genau
  sortierte Rollen und Serviceidentitäten, Backend-/Gatewayrevisionen, immutable
  Image-Refs und separate Image-IDs/Buildreceipts, Command-/Health-/Readinesshashes,
  Caddy-/TLS-/Compose-/Settings-/Persistenzhashes, genaue Mount-/Jobrootidentitäten,
  interne Netz-ID/-Name, expliziter Namespacevertrag und leere Hostportfreigabe,
  vollständige zulässige Triggerakteure und Policyhash.
- [`OperationPlan`, Schema 2](runtime_operation.v2.schema.json): Digest des
  tatsächlichen v1-Gateplans plus vollständiger aktueller und geplanter Scope.
  `bind_gate_plan` prüft dessen API-/SHA-/Image-/Settings-/Persistenzanker gegen
  beide Zustände. `runtime_scope_sha256` ist SHA-256 über das gesamte v2-Dokument.
- Kanonische Serialisierung: vorhandene `models.canonical`, UTF-8-JSON,
  lexikographisch sortierte Objektschlüssel, `separators=(",", ":")`,
  `ensure_ascii=false`, keine NaN/Infinity. Arrayreihenfolge bleibt bedeutend:
  Rollen `api, api-gateway, capacity-worker`, eindeutige Mounts nach Zielpfad,
  eindeutige Triggerakteure sortiert. Unbekannte Felder sind verboten. Keine
  Env-Werte, Tokens, URLs mit Credentials oder Befehlsargumente im Eingabedokument.
- Zukünftige Container-/Deployment-IDs und Beobachtungszeiten gehören ausdrücklich
  nicht in den vorab freizugebenden Operationscope. Sie werden im separaten
  `ObserverBinding` beziehungsweise Beleg spät gebunden.

**Kein stilles Upgrade des #148-Gates.** Dessen v1-Plan/Approval/Permit/Journal
akzeptieren das neue Feld weiterhin nicht. Die belegte Gatewaylücke wird durch
keinen Liveadapter verdeckt: der neue v2-Umschlag ist ein reviewbarer Vertrag,
noch keine vom Gate erzwungene Genehmigung. Der Negativtest weist die Ablehnung
als v1-Plan nach. #148 bleibt unverändert. Vor einem mutierenden Driver braucht
es einen koordinierten, separat geprüften v2-Gate-/Approval-/Permit-/Journalpfad;
die v2-Bindung muss dort vor jedem Seiteneffekt und bei Resume geprüft werden.
Dieser Teil ist offen, nicht als behoben oder als Produktionsschutz ausgegeben.

## Unabhängiger Collector

[`HostCollector`](../../../src/job_control/coolify_observer.py) ist eine kleine,
offline testbare Abfrageorchestrierung mit
[versioniertem, redigiertem Ausgabeschema 1](host_metadata.v1.schema.json).
Kein Defaulttransport, Credentialloader, CLI, Shell, Subprocess, Docker-Socket,
Queuezugriff oder mutierender Aufruf. Vier feste Abfragearten:

| Abfrage | Feste Identität / Grenze |
|---|---|
| `inventory` | Gesamter Host, einschließlich gestoppter Container, vollständig; höchstens 64 eindeutige Mitglieder. Überlauf/Trunkierung muss verweigern. |
| `container` | Nur die drei aus Application **oder** Composeprojekt ermittelten Mitglieder; vollständige 64-Hex-ID. |
| `image` | Nur deren eindeutige lokale `sha256:`-IDs; höchstens drei. |
| `boundary` | Exakt gebundene Application; unabhängige Trigger-, Netzwerk-, TLS-, Writer- und Scopebelege. |

Höchstens acht Abfragen, je höchstens 65.536 Bytes, keine freie URL/Abfrage,
kein Paging, keine Duplikatschlüssel. Top-Level-Feldallowlist; strikte begrenzte
Untermodelle. Kein Env-/Log-/Inspectdump; feste Fehlertexte, die auch bösartige
Adapterexceptions redigieren. Provenienz enthält Version, Host-/Adapter-ID,
Beginnzeitpunkt der Sammlung und ausdrücklich `mode=offline_fixture`. Ganze
Beobachtung höchstens 30 Sekunden alt; Workerheartbeat jünger als zehn Sekunden. Dockerhealth und Anwendungreadiness
sind getrennte Pflichtbelege; der bestehende API-401-Healthprobe allein
belegt keine Betriebsreadiness.

Der Adapter muss bereits selektierte Metadaten liefern. `process_verified`
belegt den tatsächlichen Rollenprozess getrennt vom bloßen Containerstatus.
`verified_build_receipt` muss auf eine unabhängig geprüfte Buildreceipt zeigen;
ein OCI-Label oder Tag reicht nicht. Vollständige Writer-/Triggerinventare sind
nicht aus Compose-Labels oder dem sichtbaren APIeinstieg ableitbar.

**Noch kein authentifizierter Livecollector.** Kein Operator wurde um eine
Docker-Socketfreigabe gebeten und keine sichere Anbindung behauptet. Für den
späteren Betrieb außerhalb ersetzbarer Rollen fehlen: zugelassener unabhängiger
Koordinator/Hostdienst, read-only Feldprojektion, Rechte-/Ressourcenallowlist,
Belegsignatur beziehungsweise authentifizierter Transport, Freshness und
Replay-/Vollständigkeitsnachweis. Docker-Zugriff selbst hat weitreichende Rechte;
dieser Vertrag allein begrenzt keinen fremden Socket. Ohne Betreiberentscheidung
wird ausschließlich der Offlineadapter geliefert und geprüft.

## Geänderte Dateien und Nachweise

Neue Bibliothek `src/job_control/coolify_observer.py`, Regressionen
`tests/test_coolify_observer.py`, drei generierte Vertragsschemata, diese beiden
Hauptberichte und `observer_consolidation_validation.v1.json`. Ergänzte Inventare
`operator_inventory.v1.json` und `coolify_resource_binding.v1.json` sowie aktuelle
Verweise in README/Driverplan/-vertrag und Ressourcenmatrix. Keine Runtime-/Lock-/Dependency-/Compose-
oder Gatekernänderung. Tests und genaue lokale Simulationscommits stehen im
[Validierungsbeleg](observer_consolidation_validation.v1.json) und
[Bericht B](draft_consolidation_report.md); historische Läufe werden nicht addiert.

**604 Fälle im breiten integrierten Lauf bestanden, ein offener SRT-Skip;
anschließend 135 finale gezielte Fälle bestanden, keine Skips.** Darunter 66 neue
Observerfälle. Separate #156-/HTML-/UI-Nachweise stehen in Bericht B. Die
Backendumgebung weicht vom Runtime-Lock ab; der Offlineversuch scheiterte am
lokalen uv-Cache-ENOSPC. Keine neue Runtime-/Imageabnahme behauptet.

Die neuen Negativfälle decken falsche Application, zusätzliche Container/Worker,
Gatewaydigest/Caddyänderung, falschen Commit, fehlenden RepoDigest/Buildreceipt,
unbekannte Trigger, anderen Root/Mount/Inode, Namespace/Netzwerk/Hostport,
Heartbeat/Health, Drift und fehlende/widersprüchliche Collectorbelege ab.

## Offene Betreiberbelege und nächste Entwicklung

1. Bestehende bestätigte Buildpfade und Image-IDs sind als `operator_observed`
   ergänzt. `RepoDigests`, unabhängiger Build-SHA, neue Runtimeimages und deren
   Buildreceipts bleiben `unverified`; keine Image-ID als Digestersatz.
2. Vor weiterem Livebetrieb: vollständiges lesendes Trigger-/Actor-/Pending-
   Deploymentinventar einschließlich API/Webhooks/Registry/Scheduler,
   Previewfeatureflag und exklusive Koordination. Manual-only/Previewanzeige None
   schränken die bekannten Trigger ein, beweisen jedoch nicht deren Exklusivität.
3. Neue Root-/Mountidentitäten, genau ein Worker, alle Writer, privater Namespace,
   TLS/VPN/OIDC, Backup/Restore, frisches Disk-/RAM-/Image-/Backupbudget und reale
   Composeadoption getrennt abnehmen. Kein Lasttest durch diese Offlinefälle.
4. Danach Livecollectorvertrauen und v2-Gatepfad implementieren/prüfen; erst danach
   einen einzigen mutierenden, permitpflichtigen Coolify-Driver für den gebundenen
   Scope entwickeln. Keine automatischen Retries, Rollbacks oder Resumes ergänzen.
   Kaltbootstrap und späterer kleiner Pilot brauchen jeweils eigene Freigaben.

Alle eigenen RAM-Kopien und dauerhaft gesicherten Quell-/Testergebnisse bleiben
wegen ausdrücklichen Merge-/Löschverbots erhalten. Dokumente liegen bis zur
regulären Integration in #157; Defaultbranchintegration ist weiterhin ausstehend.
