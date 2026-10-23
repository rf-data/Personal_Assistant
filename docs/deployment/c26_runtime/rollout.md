# Spätere genehmigte Abnahme-, Rollout- und Rollbackkette

**Dieses Rezept ist keine Ausführungsfreigabe.** Jetzt sind ausschließlich Review
und die [lesende Inventur](operator_checks.md) erlaubt. Jeder Wechsel bindet
exakte Ressource, SHA/Registrydigest, Settings, Limits, Persistenz, Verantwortlichen
und Zeitfenster. Unknowns bleiben blockierend. Kein Download/ZIP-Import oder
produktiver Job im aktuellen Auftrag.

| Phase | Einstieg | Prüfung und Erfolg | Abbruch / Zustand |
| --- | --- | --- | --- |
| 1 — Betreiberinventur | Vorhandener genehmigter Betreiberzugang | Alle Rollen/Roots/Buildtypen, aktuelle SHAs/Digests, Mounts und Jobs zugeordnet | Unknown oder fremder Writer: kein Rollenstart/keine neue Queue |
| 2 — Triggerkontrolle | Vollständige Trigger-/Rechteinventur | Separat freigegebene Kontrolle aller Auto-/Preview-/Webhook-/Registry-/Scheduler-/manuellen Deploywege; Wartungspfad exklusiv | Unkontrollierter Auslöser/ausstehender Deploy: kein Merge/Bootstrap |
| 3 — Backups/Recovery | Bestätigter Scope und erlaubtes Sicherungsverfahren | Vorhandene vollständige Backups/isolierte Restorebelege, unveränderliche vorige Images, Rettungszugang und RAM/Disk/Inodes ausreichend | Fehlender Scope, Live-SQLite-Blindkopie oder fehlender Rückweg: STOP |
| 4 — Annahme/Dispatch sichern | #148 tatsächlich integriert; bestehende Queue und geschlossene externe Annahmen belegt | Gatezustand lesen; regulär `Gate.run` mit echtem Driver/Freigabe. Erstbootstrap separat manuell geschlossen, siehe unten | Fehlendes Gate/Queue oder alte ungegatete Writer: kein vermeintlicher Gateschutz |
| 5 — Drain | Annahme gesperrt; bestehender Worker noch für Drain zuständig | Queue terminal, Heartbeat frisch, genau ein Gateworker, alle Lifecycle-Locks frei, keine Quarantäne, unabhängige Jobs idle | Timeout/Lock-/Guardianverlust: geschlossen halten, untersuchen, keine Locks löschen |
| 6 — Imagewechsel | Passender Driver, frischer Permit, Backups und genehmigter Scope | Genau eine genehmigte Ressourcenoperation; vorher/nachher live Version, geschützte Ressourcen, Mounts und Namespacebezug beweisen | Mehrressourcenwirkung, abgelaufene Freigabe, Drift oder Koordinatorverlust: Recovery, keine Wiederholung |
| 7 — Rollenstart | Alte Rollen nachweislich beendet, keine Überlappung, Daten unverändert | Interner Gateway gestartet → API im selben Namespace → genau ein C26-Worker; identische Config/Roots/Digests, getrennte Healthchecks | Falscher Mount, fehlende Policy, zweite Workerlease, fehlende Queue oder Kapazität: STOP, kein Auto-Init |
| 8 — Private HTTPS/VPN-Kette | Rollen gesund, Annahmen weiterhin geschlossen | Genehmigtes Gerät → bestehender Traefik → geschützter UI-Launcher; UI → private SAN-/CA-geprüfte API mit individuellem Bearer | Ungültige TLS-/OIDC-/Originbindung oder öffentliche APIroute: geschlossen lassen |
| 9 — Health/Negativtests | Bestätigte Testidentitäten und Geräte | API-auth/Workerheartbeat/TLS/individuelle Readiness sowie Außen-VPN-/fremdes Gerät-/Origin-/WebSocket-/Token-/Owner-/Course-Negativfälle bestanden | Jeder unerwartete Zugang oder bloßes Liveness-Signal statt Readiness: NO-GO |
| 10 — Betriebsfreigabe | Alle Belege und exakte Version genehmigt | Neue explizite Resume-Freigabe + frische Driverbeobachtung; Gate erst dann `open`; Audit sichern | Keine automatische Freigabe aus `verified`, Health oder Merge |
| 11 — Begrenzter Week-0-Pilot | Zusätzliche SourceApprovals/Rawhashes, gebundener Batch und frische Kapazität | Separat genehmigt genau ein bestehendes HTML-Material, ein Job, Parallelität/Queuegrenze 1; Rohdatei → Normalisierung → Quality → Handoff plus Journal | SQLite-/Kapazitäts-/Grant-/Hashfehler, Quarantäne oder unerwartete Ergebnisse: stoppen, keine Folgebatches/Retry |
| 12 — Abnahme oder Rollback | Ausgewerteter Pilot und aktueller Zustand | Explizite Abnahme oder eigene Rollbackfreigabe, wieder Gate/Drain/Versions-/Healthprüfung; Resume erneut separat | Daten/Journal nicht überschreiben; unbekanntes Cleanup verhindert Wiederaufnahme |

## Besonderheit: erster Übergang von Sleep zu Runtime

`Gate.initialize` benötigt bereits eine gültige bestehende C16-Datenbank.
Ein unbekannter Pilotroot und eine Datei mit nur Mountpolicy-Schlüsseln sind
kein Ersatz. Ohne nachgewiesene Queue endet die Vorbereitung hier; eine neue
leere Queue braucht eine spätere ausdrückliche Provisionierungsfreigabe für
einen getrennten unbenutzten Root. Der aktuelle Auftrag erteilt sie nicht.

Das bisherige Sleep-Image hält keine nachgewiesene Gateworkerlease. Die erste
Umstellung kann daher nicht so dargestellt werden, als schütze bereits ein
laufender `Gate.run` alte Writer. Zuerst separat genehmigter Wartungs-/Annahmestopp
aller echten Writer, bestätigter Idle und Backup. Danach bewusstes Gatebootstrap
auf dem bestätigten bestehenden Root mit initial `held`, Code-/Imagewechsel und
Start der gatefähigen Rollen ohne Überlappung. Der vorhandene `initialize`-Befehl
ist schreibend und darf nicht als Inventur oder Probe ausgeführt werden.

Erst nach neuer Betriebsbeobachtung, gleichem Current/Target beim Bootstrapplan
und eigener Resume-Freigabe kann `release` öffnen. Ohne tatsächlichen Driver kann
diese Produktionsfreigabe heute nicht ausgeführt werden. Test-Fake-Driver sind
ausschließlich Offlineprüfmittel.

## Lesende Prüfkommandos nach separat freigegebenem Rollenstart

Nur in der bereits bestätigten Runtimeumgebung, mit deren vorhandenen Pfaden;
keine Installation, keine Secretinhalte und kein Workerstart durch diese Befehle:

```sh
: "${C26_RUNTIME_PYTHON:?Vorhandene passende Runtimeumgebung}"
: "${C26_CONFIG:?Bestaetigte private Settingsdatei}"
"$C26_RUNTIME_PYTHON" -m scripts.deployment check --config "$C26_CONFIG"
"$C26_RUNTIME_PYTHON" -m scripts.deployment health --role api --config "$C26_CONFIG" --port 8016
"$C26_RUNTIME_PYTHON" -m scripts.deployment health --role worker --config "$C26_CONFIG"
"$C26_RUNTIME_PYTHON" -m scripts.deployment_gate status --config "$C26_CONFIG"
```

Die bestehenden Startbefehle stehen exakt in der Composevorlage. API-Health
prüft absichtlich 401 für eine ungültige Probeidentität und SQLiteintegrität;
das beweist noch keine berechtigte UI-Verbindung. Gateway-Health prüft
vertrauenswürdiges TLS und dieselbe Authgrenze. Worker-Health prüft frischen
Heartbeat, nicht sämtliche externen Writer. UI `container_runtime health` ist
Liveness, `ready` zusätzlich individuelle HTTPS-C16-Readiness. Keine dieser
Prüfungen öffnet das Gate.

Die Browser-/Netz-Negativrezepte in [HTTPS](../https.md) weiterverwenden: außerhalb
VPN mit korrektem SNI, gefälschtem Forwarded-Header und alten/entzogenen Geräten
keinen UI-/API-/WSS-Zugang. TLSfehler nicht als bestandene Zugriffssperre zählen.
Öffentliche Backendports müssen unerreichbar sein; 401 auf einem öffentlichen
Port wäre nicht ausreichend. IPv4/IPv6 und alle erzeugten UI-Router prüfen.

## Rollback und dauerhafte Wiederaufnahme

Bei Fehler Gate und externe Annahmen geschlossen halten. Den wirklich laufenden
Container-/Namespace-/Imagezustand feststellen; keinen Deploy blind wiederholen.
Nur ein neuer gebundener Rollbackplan mit eigener Freigabe und kompatibler
Version darf den regulären Gatepfad verwenden. Recovery bleibt nach Prüfung
zunächst `verified`, anschließend braucht es eine separate Resume-Freigabe.

Der vorher gemeldete Image-Tag mit `sleep infinity` erlaubt allenfalls einen
separat genehmigten Rückweg in den früheren ruhenden Zustand: keine API-/Worker-
Readiness behaupten und kein Jobresume auf diesem alten Image. Tatsächliche alte
Image-ID/Verfügbarkeit zuerst sichern; ein Tag allein ist kein zuverlässiger
Rollbackbeleg. Definition-v2-Outputs und neuere Jobs nicht auf alten Code
zurückschreiben oder von ihm verarbeiten lassen.

Ein notwendiger Restore erfolgt in ein separates geprüftes Ziel, ohne Überschreiben
vorhandener CS50-/Loviscach-/Pilotdaten. Der bisherige Root samt Journals bleibt
erhalten. Auch ein erfolgreiches C22-Restore aktiviert keine Dienste und öffnet
keine Annahmen. Änderungen von Config, Root, Mountpolicy, Namespace oder Image
verlangen neue Belege und Freigaben; kein gespeicherter PID wird für Signale benutzt.

Vor dem genehmigten Rollenstart außerdem die lokale Dateisystemsemantik im
bestätigten Zielmount abnehmen: ein **separat erlaubter** synthetischer
Rename/Fsync/flock/SQLite-WAL-Probe in einem isolierten neuen Testunterverzeichnis.
Das vorhandene `scripts.deployment probe` ist schreibend und gehört ausdrücklich
nicht zur heutigen lesenden Inventur. Die aktuelle lokale ENOSPC-Diagnose ist
kein Beleg gegen das gemeldete Hetzner-ext4, ersetzt dessen Abnahme aber auch nicht.
