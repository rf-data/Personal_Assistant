# Gate-Kern und noch fehlender Coolifyadapter

Der vorhandene Kern in #148 wird unverändert verwendet. `admission()` sperrt neue
Requests und Starts unter demselben Lock wie Dispatch. Während `draining` können
bereits angenommene Jobs enden; `deploying` verhindert weitere Dispatches.
`Gate._idle()` fordert terminale Queue, frischen Heartbeat, belegte Executor-/
Gateworkerleases, freie Lifecycle-Locks und keine Quarantäne. Ein beschädigtes
Journal oder Koordinatorverlust öffnet keine Annahme.

`Gate.run()` benötigt eine kurzlebige Freigabe für den vollständigen Plan mit
Current-/Target-SHA und digestgebundenen Images sowie Settings-, Persistence- und
Protected-Resources-Hashes. Vor dem Wechsel werden live Scope/Trigger/Version
erneut geprüft und `Permit.check()` aufgerufen. Danach müssen neue Instanz,
Version und Readiness belegt sein. Erfolg endet `verified`, Annahme **geschlossen**.
`release()` verlangt eine neue Resume-Freigabe und frische Beobachtung. Recovery
bleibt zunächst geschlossen; es gibt kein automatisches Retry/Rollback/Resume.

| Ebene | Aktueller Nachweis |
| --- | --- |
| Gate-Kern | Lokal testbare Implementierung und Regression; noch Draft #148 |
| Coolify-Driver | **unverified / nicht implementiert für diesen Hostbestand** |
| Echte Betreiberfreigaben | Nicht vorgelegt; keine Approval aus Inventur erzeugt |
| Produktive Abnahme | Nicht durchgeführt |

## Notwendiger Adaptervertrag vor Implementierung

1. Genau eine tatsächliche Coolifyressource mit verifiziertem Ressourcen-/Buildtyp
   und stabiler ID zuordnen. Nicht aus dem Containerpräfix ableiten. Keine generische
   beliebige Deploy-URL, kein Shellkommando aus einem Request, keine Suche nach
   einem beweglichen Branchhead als Targetversion.
2. `Driver.observe()` muss echte aktuelle Bestandsdaten liefern: Code-SHA über
   Buildbeleg, tatsächlich laufender RepoDigest/Image-ID, Zielinstanz, Health und
   Readiness aller betroffenen Rollen, identischer Settings-/Mount-/Scopesatz,
   kontrollierte Trigger, gesperrte unabhängige Annahmen und externe Jobs idle.
   Keine erfundenen `Observation`-Werte oder Ergebnisse aus einer alten JSONdatei.
3. Für den vorgeschlagenen Composeverbund ausdrücklich festlegen, ob **eine
   Coolifyressource** API, Worker und Gateway gemeinsam umfasst. Der Kern hat ein
   `resource_id`, eine `role`, ein Imagepaar und eine `container_id`; der Driver
   muss die vollständige Rollen-/Namespaceprüfung zusätzlich selbst belegen.
   Eine geänderte Worker-ID allein beweist keinen erfolgreichen APIwechsel.
4. API und Worker müssen vor und nach der kontrollierten Operation auf die jeweils
   genehmigte gemeinsame Backend-SHA/Digestkombination zeigen. Gatewayimage und
   Caddyfile/TLS-/Netzbindung separat fixieren. Bei Gateway-Neuanlage müssen API
   und Loopback im neuen gemeinsamen Namespace nachgewiesen werden. Keine
   automatische unabhängige Gatewayerneuerung voraussetzen.
5. `single_resource_change=true` darf nur gelten, wenn exakt der genehmigte
   Coolifyressourcenscope betroffen ist und UI/fremde Apps/Datenvolumes unverändert
   bleiben. Wenn Coolify mehrere Ressourcen verändert oder ein allgemeiner
   Redeploy weitere Container außerhalb des Scopes austauscht, muss der Adapter
   geschlossen verweigern. Kein Umbenennen eines Mehrressourcenwechsels zum
   Einzelschritt und keine zweite Gateimplementierung.
6. `Driver.deploy()` muss den noch aktiven Permit unmittelbar vor der genau
   gebundenen Operation prüfen und die gesamte Operation begrenzen/beobachten.
   Der Koordinator läuft außerhalb sämtlicher ersetzter Container. APIzugang zu
   Coolify und etwaige Secrets werden weder UI noch API/Worker gemountet.
7. `Gate.run()` für Deploy erwartet `open`, Erfolg endet `verified`. Mehrere
   inkompatible Rollenwechsel dürfen deshalb nicht durch zwischenzeitliches
   Resume aneinandergereiht werden. Entweder nachgewiesener einzelner
   Ressourcenscope mit kohärenter Operation oder ein separat reviewter Ablauf mit
   belegter Zwischenversionskompatibilität; andernfalls Implementierungsblocker.
8. Alle Alternativtrigger einschließlich Auto-/Preview-/Git-/Webhook-/Registry-/
   Scheduler- und manueller Deployrechte vor Beobachtung/Wechsel prüfen. Ein
   deaktiviertes einzelnes Auto-Deploy-Feld reicht nicht als exklusiver Triggerpfad.

Die Labels melden für Backend und UI `coolify.type=application` als
Betreiberbefund. Backend/Dockerfile und UI/Docker-Compose sind nun zusätzlich
bestätigt, beide mit Manual deployments only. Maßgebliche Ressourcen-ID, genaue
Buildpfade, zusätzliche Trigger und sichere API-/Wechselwirkung fehlen weiterhin.
Deshalb werden weder Coolify-Endpunkte geraten noch ein deployender Adapter
implementiert. Aktuelle [Coolify-Compose-Dokumentation](https://coolify.io/docs/applications/builds/docker-compose)
unterscheidet Git-Application und User-defined Service; ihre Automationen sind
nicht identisch. Verhalten der installierten Version 4.4.7 bleibt zu bestätigen.

## Erstbootstrap und Rollbackgrenze

Ein alter ungegateter Container ist nicht durch den noch uninitialisierten Kern
geschützt. Erstbootstrap ist eine eigene genehmigte Wartungsoperation. Hier wird
ausdrücklich ein **neuer, separater** Root provisioniert; keine historischen
Pilotqueues übernehmen. Zuerst Annahmen sperren, alle Writer idle belegen,
Backups/Images/Mountpolicy prüfen. Eine eigene leere-Root-Freigabe erlaubt dem
Betreiber genau einmal `Store(new_root, deployment_gate_required=True)` und
anschließend `Gate.initialize()`. Ohne dieses ausdrückliche Provisionieren
verweigern API/Worker weiterhin eine fehlende Queue. Gate initialisiert seine
Journale auf `held`, erzeugt aber selbst keine C16-Datenbank. Teilfehler bleiben
gesperrt und dürfen nicht durch Löschen von Locks oder Auto-Init umgangen werden.

Das [Runbook](rollout.md) bindet die Reihenfolge und Kommandos. Für den ersten
Worker-Healthstart muss execution bewusst in einer separaten identitätslosen
Stagingconfig aktiviert werden, API bleibt deaktiviert und Gate held. Diese
Übergangsconfig ist keine abschließende Readiness. Nach eigener Aktivierungs-
freigabe alle Rollen auf gemeinsame finale Settings binden. `Gate.release` aus
held benötigt Current=Target der nun gestarteten Runtime, frische Livebeobachtung
und eigene Resume-Freigabe. `Gate.run(deploy)` aus einem unbekannten/Sleepzustand
ist kein Ersatz. Ohne realen reviewten Driver/Koordinator bleibt die Freigabe
blockiert; die Gate-CLI hat absichtlich keinen Resume-/Deploybefehl.

Das alte gemeldete Sleep-Image ist kein nachgewiesener gatefähiger Runtime-
Rollbacktarget. Es kann nach eigener Freigabe den früheren **ruhenden Zustand**
wiederherstellen; nicht zugleich API/Worker-Readiness oder ein Resume liefern.
Neuere Definition-v2-Jobs nicht mit dem alten Image verarbeiten. Normaler
Gate-Rollback benötigt ein geprüftes kompatibles SHA/Digestpaar und eigene
Rollbackfreigabe; Restore kopiert ausschließlich in einen separaten Zielroot und
wird niemals automatisch aktiviert. Quarantäne und Journal beibehalten.

## Konkrete 4.4.7-Grenze

Die [versionsbezogene Prüfung](coolify_compatibility.md) zeigt einen vorhandenen
Raw-Compose-Pfad. Er ersetzt noch keinen Driver: Coolify kann selbst im Rawpfad
Images pullen, alte Container stoppen und Hilfsnetze/Labels bearbeiten. Der
exakte Scope und diese Nebenwirkungen müssen im Plan gebunden werden. Ein
inaktives Profil macht einen Coolify-Deployaufruf nicht sicher. Die bestätigte
Manual-Deploy-Einstellung senkt die Erwartung eines normalen Git-Autodeploys,
schließt separate Deployrechte und Hooks aber nicht aus.
