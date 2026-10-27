# C26-PILOT-INTEGRATION – konkrete spätere Coolifysequenz

27.10.2026. **Vorbereiteter Plan, sämtliche Liveänderungen BLOCKED.**
Die C-/L-Schritte der [Betreiberchecks](c26_pilot_operator_checks.md) bleiben
verbindlich und wurden nicht ausgeführt. Für die aktuelle Quellfassung gilt:

1. Reguläres Review des Gesamtpatches einschließlich G/H-Arbeitsstand und neuer
   Runtime-/tmpfs-Korrekturen; keine Ableitung aus #166. Ursache des beobachteten
   SQLite-Quarantäneereignisses klären. Keine Test-/Quarantänegrenze lockern.
2. Produktive Producer-/Build-/Operator-/monotone Witness-/Permitdriverkette
   liefern und testen. Der vorhandene Koordinator ist ausschließlich offline.
   **Solange das fehlt, gibt es keinen zulässigen mutierenden Coolifybefehl.**
3. R01–R12 lesen: UUIDs der beiden vorhandenen Ressourcen, Coolify4.5.0/
   Compose5.6.0-Kompatibilität, vollständige Trigger/Pendingdeployments,
   Netze/Mounts/alte Digests, Demo-/Coolifyrouter und Rückweg belegen.
4. C01/C02: geschützte rückführbare Konfigurations-/Secretquellen sichern und
   sämtliche alternativen Mutationspfade exklusiv sperren. Ohne getesteten
   Rückweg kein Buildtyp-/Command-/Mount-/Domainwechsel.
5. Separaten leeren synthetischen Pilotroot/Katalog/Config/Limits mit UID10001,
   0700/0600, bestätigter Quota/Reserve und leerem Queue-/Gatezustand bereitstellen.
   Cold Bootstrap muss über den reviewten zukünftigen Livevertrag geschehen;
   keine Ersatzqueue auf unbekanntem Mount und kein Kopieren einer Fixturequeue.
6. Backend-Ressource identitätserhaltend auf genehmigten Gesamt-SHA und
   `deployment/c26-pilot.compose.yaml` umstellen. Genau das geprüfte Controlprofil
   auswählen; unveränderte Ausführungsflags false, Workerprofil aus. Keine
   Domain, keine Hostports, keine Änderung an demo/coolify. Exakte Images müssen
   vorab durch unabhängige Buildreceipts und Registrydigests gebunden sein.
7. Bestehende UIressource mit `coolify.ui.compose.yaml`, `coolify.private-https.yaml`
   und `c26-pilot.ui.compose.yaml` über den exklusiven genehmigten Driver umstellen;
   eigener geprüfter UI-main-Digest, genau Profil c26-pilot-ui, vollständige
   OIDC-/HTTPS-/C16-Konfiguration. Noch keine Domain. Kein Direktstart app_ui.py.
8. Nach Liveness und authentifizierter UIreadiness sowie isolierter Image-/
   Container-/Cancelabnahme ausschließlich die genehmigte Adminroute mit
   vollständiger Middlewarebindung vorbereiten/abnehmen. Erst separate Freigabe
   darf Domain/DNS/IdP/TLS aktivieren; IPv4/IPv6 und unabhängige Quelle prüfen.
9. Eigener Config-/Rollen-/Jobgrant: unter geschlossenem Gate auf die explizit
   gebundene genehmigte Zielkonfiguration wechseln; gleiches Configfile für
   API/Worker, alle anderen Opt-ins false. Genau einen Worker aktivieren,
   echten frischen Idle-/Lock-/Instanz-/Scope-/Witnessnachweis führen. Erst
   frischer autorisierter Resume darf Annahme öffnen. Kein Testissuer auf Hetzner.
10. Genau einen material_planning-Job bestätigen, Ergebnis mit zweitem
    authentifiziertem Client nach Schließen des ersten Clients abfragen.
    Ein zweiter Job muss auch nach Abschluss verweigert werden. Cancelnachweis
    bei zu schnellem Plan aus isolierter Containerabnahme verwenden. Danach
    Annahme geschlossen halten; kein Retry oder automatischer Restart.

Jeder Schritt hat die Voraussetzungen, Erwartung, HOLD-Kriterien, Seiteneffekte
und Rückwege aus C01–C08/L01–L05. Die neue Composewahl ersetzt nur den dort
früher fehlenden kleinen Rollensatz; kein P0-Livegate wird dadurch aufgehoben.

---

## Historischer Wechselplan und weiterhin gültige Sicherheitsgrenzen

# C26-PILOT – Kontrollierter Wechsel der vorhandenen Ressourcen

**Nicht ausführbar, bis P01–P09 aus der [Lückenanalyse](c26_pilot_gap_analysis.md)
geschlossen und eine eigene Betreiberfreigabe erteilt sind.** Alle Änderungen
tragen `CONTROLLED CHANGE – SEPARATE APPROVAL REQUIRED`; Prüfverkehr/Jobs tragen
`LIVE ACCEPTANCE – SEPARATE APPROVAL REQUIRED`. In diesem Auftrag keine davon ausgeführt.
Ein ausgeschaltetes Auto-Deploy ist nur eine Triggerbremse, kein Deploymentgate.

## Freigabemanifest

Vor einer Änderung aus R01–R12 ein privates, unveränderliches Manifest herstellen:
Ressourcen-UUIDs, Repo/Branch, aktueller und geplanter SHA, Buildtyp/Kontext/Pfade,
Basis-/Runtime-/UI-/Gatewaydigests mit unabhängigen Receipts, Config-/Composehashes,
Rollentopologie, Root-/Mountidentitäten/UID, Netzmitglieder/Namespace, tatsächliche
Health-/Readinessbefehle, individuelle Identitätsreferenzen, Triggerliste,
laufende/pending Deployments, Snapshot-/Wiederherstellungsreferenzen, Zeit und
separate Betreiberentscheidung. Keine Secretwerte darin speichern.

Aktuelle Audit-SHAs aus der Lückenanalyse sind **nicht freigegeben**. Die spätere
Gateintegration verändert den Backend-Zielsha und erfordert erneute Tests und
Buildbelege. Ein Branchname oder lokales Image-IDlabel ersetzt keinen
Registrydigest; ein Image beweist nicht seinen Gitquellstand. Kein Deployment
auf einen beweglichen Branch ohne nachgewiesene exakte Revision.

## Ressourcenbindung

| Ressource | Ist laut Auftrag, noch lesend bestätigen | Geplanter Wechsel nach eigener Freigabe |
| --- | --- | --- |
| Backend `personal_assistant:Worker_1` | `rf-data/Personal_Assistant`, Commit `3b91d39195e0d13fe0442d4594b28e431b0f4236`, Dockerfilebuild, `sleep infinity`, keine laufende C16-API | Dieselbe Ressource kontrolliert auf geprüftes Backendrollenset umstellen: API/Gateway/ein Executor. Schmale vorhandene C22-Images, kein öffentlicher Port. Dediziertes Coolifyoverlay fehlt noch P03 |
| Bestehende UI, UUID noch erfassen | `rf-data/personal-assistant-ui`, Commit `b2cf9ca9ba44ee770dab4d834a6ae8285f34776b`, Compose, `streamlit run app_ui.py`, Auth/Backend disabled, kein Adminrouter | Dieselbe Ressource mit vorhandenem `deployment/coolify.ui.compose.yaml` und privatem Overlay; genehmigter UI-Registrydigest, fester Launcher, individuelle OIDC-/C16-Bindung |

Vor Wechsel des Coolify-Buildtyps bestätigen, dass dieselbe Ressourcenidentität
mit ihren gesicherten Einstellungen rückführbar bleibt. Wenn Coolify diesen
Wechsel nicht sicher unterstützt: **HOLD**, keine spontane neue Ressource oder
Paralleltopologie erzeugen. Alte Container/Mounts/Images/Route behalten, bis der
Rückweg abgenommen ist. Keine produktive Datenmigration und keine Queueadoption.

## Sequenz und Gates

Die genauen UI-Aktionen, Voraussetzungen, Sollwerte und Rückwege pro Schritt
stehen in [C01–C08, L01–L05](c26_pilot_operator_checks.md). Diese Reihenfolge
erlaubt keine abhängigen Schritte nach einem HOLD.

1. **R01–R12, nur lesen:** Ressourcen-/Trigger-/Mount-/Netz-/Buildinventar sowie
   unveränderte Demo-/Coolifyrouter aufnehmen. Offene Deployments und unbekannte
   Trigger sind HOLD. Keine Vollinspect-/Env-/Secret-/Logdumps.
2. **Engineering zuerst:** P01–P04 auf tatsächlicher master/main-Zielbasis
   reviewen und offline validieren. Bestehende Draftserie wiederverwenden.
   Liveproducer, unabhängige Buildautorität, Operatorverifikation, monotone
   Witnessbasis und permitpflichtiger Driver müssen wirksam sein. Ein
   Offline-Testwitness oder gespeicherter Fakecapture ist kein Ersatz.
3. **C01 Sicherung / STOP-Gate:** Private Wiederherstellungskopie der beiden
   Ressourcen, zielbezogenen Proxysettings, Identitäts-/Secretreferenzen und
   notwendigen Schlüssel sicher verfügbar; alte Digests abrufbar. Isolierte
   Konfigurationsrekonstruktion prüfen. Ohne Nachweis **keine** Überschreibung,
   Buildtyp-/Entrypoint-/Mount-/Domain-/Secretänderung. C26-04 bleibt separat.
4. **C02 Triggerexklusivität:** Auto-/Push-/Preview-/PR-/Webhook-/API-/Registry-/
   Scheduler-/Retrypfade, Coolifyadministratoraktionen und laufende Deployments
   vollständig sichern. Nur der genehmigte Gatepfad darf Deployment auslösen.
   Unklare oder parallel auslösbare Mutation → HOLD.
5. **C03 neue private Pilotinputs:** Separater leerer Root und synthetischer
   Katalog, kein Zugriff auf bestehende Daten. UID/Mode/Volume/Quota auf diesem
   neuen Ziel abnehmen. Alle Ausführungsflags false. Keine Defaults autofüllen.
6. **C04 Identitäten/Trust:** OIDC-App mit exaktem Callback, ein Operator,
   eigene Backendidentität, CA/SAN, Secretmounts/Rotation und privater
   Netzwerk-/Egressvertrag. Alle Eingaben aus Sicherheitsmatrix bestätigt.
7. **C05 Backendwechsel mit weiterhin geschlossener Annahme:** Erstbootstrap
   benötigt vollständig bestätigten leeren neuen Pilotroot und exklusiven
   Änderungspfad; `sleep infinity` hat keinen beweiskräftigen Workerheartbeat.
   Fehlender Bestand ist nicht „idle“. Das Gate darf keine leere Ersatzqueue
   an Stelle unbekannten Altzustands erfinden. API/Gateway des geprüften
   Rollensatzes deployen; Executor konfiguriert, ausdrücklich gestoppt halten:
   er startet bei `execution_enabled=false` nicht. API-/Gatewayhealth,
   authentifizierte Readiness und exakte Images prüfen. Das geprüfte Overlay
   muss diesen Stufenstart unterstützen, sonst HOLD.
8. **C06 UIwechsel:** Bestehende UI auf genehmigten Digest, Launcher und private
   APIbindung umstellen; noch keine öffentliche Adminroute. Kein
   `ADMIN_AUTH_MODE=disabled`-Fallback bei Startfehlern. Readiness muss an der
   individuellen Backendidentität und CAprüfung erfolgreich sein.
9. **C07 ausschließlich Adminroute:** Private DNS-/TLS-/IdP-/Proxykonfiguration
   exakt nach Sicherheitsmatrix. IPmiddleware an **jeden** generierten Admin-
   HTTPSrouter anfügen, bestehende Middlewareliste erhalten. Kein globales
   Traefik-/Demo-/Coolifyrouting ändern. Bei erforderlichen globalen Änderungen
   HOLD und neue Review, keine pauschale Freigabe.
10. **L01–L04:** Zuerst Container-/Auth-/VPN-/HTTPS-/WSSnegative und getrennte
    Quellen prüfen; auf dem Livepilot Ausführung weiterhin aus und Executor
    gestoppt. Worker-/Jobfehlertests nur am isolierten L04-Ziel ausführen.
    Fehler → Annahme geschlossen,
    kein neuer Job und kein automatischer Rollback/Retry.
11. **C08 / L05 eigener Jobgrant:** Nur nach separater Ausführungsfreigabe
    `execution_enabled=true` in der freigegebenen Zielkonfiguration; nötiger
    Rollenwechsel selbst wiederum vollständig gegatet. Jetzt genau einen
    Executor starten, während das integrierte Admissiongate weiterhin geschlossen
    bleibt. Frischen Workerheartbeat, echte Idle-/Kindprozessfreiheit,
    alle Rollen und authentifizierte UIreadiness prüfen. Erst danach einmaliger
    frischer Resumegrant nach Ziel-/Scope-/Instanz-/Witnessprüfung. Dann ein
    bestätigter synthetischer Job. Kein Auto-Resume durch bloße Health-Rückkehr.

## Jeder spätere Containerwechsel

Atomar neue Create-/Confirm-/Start-/Resumeannahmen schließen und alle Dispatch-
writer an denselben Gate-/Root-/Witnessvertrag binden. Bereits angenommene Arbeit
kontrolliert auslaufen lassen. Queue, Running/Cancel_requested, echte Kindprozesse,
Guardian-/Worker-/Executionlocks, Heartbeats und unbekannte Quarantänen prüfen.
Konfigurationsänderung `execution_enabled=false` in einer Datei alleine stoppt
keine bereits geladene API und ist **kein** atomarer Drain.

Aktiver/unklarer Job oder fehlender Lock-/Heartbeat-/Identitätsbeleg blockiert
den Wechsel. Exklusive Koordinatorsitzung über Idleprüfung, einmaligen Permitclaim,
Mutation und Nachprüfung halten. Unmittelbar vor Mutation alle Scopes/Receipts/
Freigaben frisch validieren. Kein Zeitfenster mit offenen Annahmen zwischen
Idleprobe und Deploy. Gilt für UIwechsel ebenfalls, weil UI Jobannahmen auslöst.

Nach Wechsel: tatsächlicher Registrydigest, freigegebener Gitstand, neue
Instanzidentität, alle Healthchecks und authentifizierte Readiness; kein
offenes/pending Fremddeployment, keine neuen unexpected Netzmitglieder/Mounts.
Erst separate Resumeentscheidung kann Annahmen wieder öffnen. Diese produktive
Kette ist auf der aktuellen Auditbasis nicht vorhanden; manuelles Klicken auf
Deploy nach Blick auf eine leere UI erfüllt sie nicht.

## Abbruch / Teilfehler

Fehlende Genehmigung, Scope-/Digest-/Config-/Instanzdrift, Race, verlorener Lock,
stale Evidence, unklare Mutation oder fehlender Health-/Readinessnachweis:
Gate geschlossen, unbekannten Zustand dokumentieren, keine automatischen
Wiederholungen, kein zweiter Driver. Wenn Driverergebnis unklar ist, tatsächliche
Ressourcenidentität erst lesend neu feststellen; niemals blind erneut deployen.

Kontrollierter Rückweg ausschließlich nach [Rollbackplan](c26_pilot_rollback.md)
und eigener Freigabe. Ohne sichere Konfigurationswiederherstellung bleibt auch
ein vermeintlich einfacher Image-Rollback blockiert. Kein automatisches
„Rollback succeeded → admission open“.
