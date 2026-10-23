# Coolify 4.4.7: konkreter Driververtrag und Implementierungsgrenze

Stand 23.10.2026. Bestehende Architektur unverändert: Caddy, API im gemeinsamen
Loopback-Namespace, genau ein Kapazitätsworker, eigene C16-Queue, UI separat.
Das ist eine Ergänzung zu [driver_contract.md](driver_contract.md), keine zweite
Gateimplementierung. **GO für lesende Vertragsarbeit, NO-GO für Deployment.**

## 1. Tatsächliche API, auf Version gepinnt

Geprüft: Coolify `v4.4.7`, Commit
`86c21c0d5babfa8c7d65a9c27e5863c629a89c7c`.
[Routen](https://github.com/coollabsio/coolify/blob/86c21c0d5babfa8c7d65a9c27e5863c629a89c7c/routes/api.php#L152),
[Applicationcontroller](https://github.com/coollabsio/coolify/blob/86c21c0d5babfa8c7d65a9c27e5863c629a89c7c/app/Http/Controllers/Api/ApplicationsController.php#L2449),
[Deploymentcontroller](https://github.com/coollabsio/coolify/blob/86c21c0d5babfa8c7d65a9c27e5863c629a89c7c/app/Http/Controllers/Api/DeployController.php#L360).
Quellblob-IDs stehen in der [JSONmatrix](coolify_resource_binding.v1.json).
Keiner dieser Endpunkte wurde auf einer realen Coolifyinstanz aufgerufen.

| Operation unter `/api/v1` | Versionierter Vertrag | Verwendung jetzt |
| --- | --- | --- |
| GET `/applications/{uuid}` | Team-/Viewkontrolle, Settingsrelation, sensible Felder abhängig von Berechtigung verborgen | Exakte UUID, nur explizite harmlose Feldprojektion, ausschließlich MockTransporttests |
| GET `/deployments/applications/{uuid}?skip=0&take=16` | Applicationbezogene History mit Viewkontrolle | Exakte vorher gebundene Deployment-ID muss darin eindeutig vorkommen; alte/fehlende History verweigert, kein automatisches Paging |
| GET `/deployments/{uuid}` | Teamprüfung, konkreter Deploymentdatensatz | Nur dokumentiert; allein kein Application-/Dreirollenscopebeweis |
| GET `/applications/{uuid}/previews` | Team-/Viewkontrolle, Previewliste | Nur dokumentiert; aktive Previewinventur bleibt nötig |
| POST `/deploy` | UUID oder Tags, UUIDlisten möglich, Previewparameter; kein spezifischer Commitparameter im geprüften Controllerpfad | Nicht implementiert/aufgerufen; kein generischer deployender Writer |
| POST `/applications/{uuid}/start` | Queueauftrag mit force/instant_deploy, kein eindeutiger Commit im Request | Nicht implementiert; bewegliche Sourcebindung reicht nicht |
| POST `/applications/{uuid}/rollback` | Pflichtfeld commit, queue_application_deployment mit rollback=true | Nicht implementiert; Commit/Tag beweist keinen vollständigen Dreirollen-Digestrollback |
| PATCH `/applications/{uuid}` | Vorhandene Application ändern, u.a. build_pack, git_commit_sha, Pfade/Commands; instant_deploy möglich | Nicht implementiert/aufgerufen; bereits eine produktive Konfigurationsmutation |

Routen unterscheiden `read`, `deploy`, `write`, teils `read:sensitive`.
Der lesende Caller darf nur passend begrenzte vorhandene Readberechtigung haben,
keinen Root-/Sensitivezugang. Keine Credentials in Runtime/UI/Worker mounten.
Ein generisches GET ist kein Read-only-Vertrag: nur die zwei zugelassenen Pfade
werden vom Client akzeptiert, einschließlich Ablehnung beliebiger URLs/Queries.

`ApplicationsController.removeSensitiveData` verbirgt sogar die numerische
Application-ID. Deshalb leitet der Client keine Zuordnung aus guessed IDs ab,
sondern benutzt die applicationbezogene History. Er entfernt zusätzlich Logs,
Raw-Compose, Webhookfelder, Env-/Konfigurationssnapshots, Commands und alle nicht
freigegebenen Felder. Fehlende Flags bleiben unbekannt, nicht false. Der Client
beweist weder globale Triggerfreiheit noch Hostmitgliedschaft/Health.

## 2. Was jetzt implementiert ist

[src/job_control/coolify_readiness.py](../../../src/job_control/coolify_readiness.py)
enthält einen nicht aktivierten Readclient und unveränderliche Typmodelle.
Origin muss explizit HTTPS ohne Credentials/Pfad/Query sein; Transport ist
zwingend injiziert, es gibt keinen Netzwerkdefault und keine Credentialdatei/CLI.
Kein Redirect, Proxyenv, Retry oder mutierendes Verb; Antwort maximal128KiB,
keine komprimierte Antwort, doppelte JSONschlüssel verweigert, feste redigierte
Fehlermeldungen. Produktionstransport mit korrekter CA/Timeout/Auth müsste später
separat geprüft werden. Keine reale APIverbindung in diesem Auftrag.

`RuntimeBinding` beschreibt einen **belegten Ziel-/Beobachtungsstand**, nicht den
heutigen Sleepbestand. UUIDs/Projekt/Source/Buildpfade, volle Commitbindung,
Settings/Persistenz/geschützte UI/Triggerbeleg/Netz/TLS und drei Rollen mit jeweils
Revision, Registrydigest, separater Image-ID und Mountfingerprint sind erforderlich.
API und Worker teilen Backendimage/SHA/Mounts; UI-UUID muss verschieden sein.
Application-UUIDs sind weiterhin unbekannt, daher gibt es keine vorausgefüllte
produktive Bindingdatei. Alle positiven Beispiele existieren ausschließlich in Tests.

`check_snapshot`/`check_observation_pair` verlangen vollständige Containerliste,
exakt drei eindeutige Rollen, keinen weiteren Writer/Worker, passende Mount-/
Image-/Scopewerte, gesunde/ready Rollen, API→Gateway-Netznamespace, Worker ohne
Netz, aktuellen Workerheartbeat (<10s), vertrauenswürdige TLS-/Netzbindung,
belegte Intake-/Trigger-/Writerkontrolle und Beobachtung höchstens30s alt.
Ein unterbrochenes oder driftendes Paar wird verworfen; keine alte positive
Bewertung darf Recovery oder einen neuen Vorgang freigeben.

**Grenze:** Die Funktionen prüfen lediglich Konsistenz gelieferter typisierter
Belege. Wahrheitsgehalt, Signatur/Transportfrische und Vollständigkeit eines
realen Hostcollectors sind noch nicht implementiert. Ausgabe ist ausdrücklich
`ConsistencyReport`, nie #148 `Observation`; selbst positive Replays melden
`deployment_permitted=false`, `production_release=blocked`. Keine Queue,
Heartbeatdatei, Journal, Container oder zweite Gatezustandsmaschine wird angelegt.

## 3. Kleinste explizite Mehrrollenbindung für #148

Der v1-Kern hat eine Ressourcen-ID/Rolle, ein Backend-Imagepaar/SHApaar und eine
Containeridentität. Er kann eine eindeutig gebundene Application als Scope
verwenden, aber eine gültige Worker-/API-ID allein belegt keine atomare Erneuerung
von Gateway/API/Worker. Der neue Regressionstest zeigt: anderer Gatewaydigest
ändert den vollständigen Rollenfingerprint, während derselbe v1-Backendplan
unverändert bleibt. Dieser Test erklärt die Grenze, er repariert den Kern nicht.

Eine zusätzliche opaque Vereinbarung im bestehenden geschützte-Ressourcen-Hash
wäre theoretisch möglich, ist für diesen Bestand aber **nicht** belegt und würde
dessen aktuelle Bedeutung erweitern. Kein stilles Umdeuten eines UI-/Persistenz-
Fingerprints zur Mehrrollenfreigabe. Kleinster expliziter, separat zu reviewender
Vorschlag: versionierter Plan/Observationvertrag mit `runtime_scope_sha256`.

Der kanonisch gehashte **Operationsscope** umfasst genau eine Backend-Application-
UUID, geschützte UI-/Fremdressourcen, Server/Environment/Projekt, aktuelle und
gewünschte drei Rollen mit SHA/Registrydigest/Image-ID, Mount-/Namespace-/Netz- und
TLSbindung, Limits/Settings, Triggerpolicy und Abnahme-/Rollbackbedingungen.
Laufzeit-Container-/Deployment-IDs und Messzeiten gehören in Livebelege und
zugehörige Requestreceipts, nicht als unbekannte zukünftige IDs in den vorab
freizugebenden Scopehash. Der heutige `RuntimeBinding.digest` ist daher ein
Beobachtungsfingerprint und **kein direkt einsetzbarer künftiger Plan-v2-Hash**.

Planhash und damit Approval müssen den Operationsscope binden; Driver und
Observation müssen denselben Hash, vollständige Rollenbeobachtung und exakte
Mappingsemantik nachweisen. Die eine v1-Container-ID wäre nur der feste APIanker;
Driver prüft weiterhin alle drei Mitglieder vor/nach Wechsel, einschließlich
beabsichtigter Gatewayerneuerung. Keine Behauptung atomarer Composewechsel.

Vor einer Umsetzung sind mindestens folgende Vertragstests nötig: geänderter
Gatewaydigest/anderer Worker/zusätzliche Mitglieder/abweichende Mounts/Netze/
Triggerpolicy ändern Scope und invalidieren alte Approval; fehlender/v1-Scope
verweigert Mehrrollenoperation; Vor-/Nachscope-/Receipt-Drift verweigert; Permit
bindet denselben Scope; alte Journale/Plan-v1-Fingerprints bleiben versioniert
lesbar, aber erteilen keine neue Mehrrollenfreigabe. Tests für bestehenden v1-
Kern bleiben unverändert. **Jetzt keine Änderung an #148-Modellen oder Journalen.**

## 4. Konkrete spätere Driverfunktionen und Lebensdauer

| Funktion | Erforderliche echte Eingänge | Erfolgs-/Fehlervertrag |
| --- | --- | --- |
| `observe_runtime(binding, plan)` | Bestätigte UUIDs/Pfade; zwei frische APIprojektionen; unabhängiger Hostcollector für gesamte Application-Mitglieder, Digest/Image-ID/SHA-Provenienz, Mounts/Locks/Heartbeat/Namespaces; TLS/Authtest und Triggerpolicybeleg | Erst vollständige validierte Livebelege auf gemeinsamem Scope → später echte Gate-Observation. Heute fehlen Collector/Vertrauenskanal und Scope-v2; niemals Replayreport konvertieren |
| `deploy_exact(plan, permit)` | Scope-v2/kurzlebige Approval; eingefrorene feste Source-SHA oder vorab gebundene Compose-/Registryimages; exklusiver Konfigurations-/Triggerpfad; echte eindeutige Requestreceipt | Unmittelbar live erneut prüfen + permit.check; genau eine Applicationoperation, konkrete neue Deployment-ID beobachten. Kein UUIDarray/Tag/Preview/HEAD, kein Retry bei unbekanntem Queueauftrag |
| `observe_completion(receipt)` | Zuordnung Receipt→UUID→Deployment-ID, gebundene Zielversion, alle Rollen/Namespaces/Health/Mounts und unabhängige Gateworkerlease | Erfolg endet Gate verified/geschlossen, nicht aus Coolifystatus finished allein ableiten |
| `rollback_exact(plan, permit)` | Eigene Rollbackfreigabe; kompatibles voriges gesamtes Rollen-/Mount-/TLSmanifest, konkrete verfügbare Digests und Backupbeleg | Ganzer genehmigter Scope ohne alte/neue Writerüberlappung; sonst Recovery geschlossen. Sleep ist nur ruhender Rückweg |

Ein Host-/Managementkoordinator außerhalb aller drei ersetzten Container hält
#148 Owner-/Admission-/Operationsvertrag über den gesamten asynchronen Wechsel.
Coolifytokens nicht in UI/API/Worker. Zusätzliche Deployrechte/Trigger müssen
kontrolliert bleiben, auch nach Queuing. Ein unveränderlicher git_commit_sha-
Feldwert allein löst das Race zu einer parallelen PATCH-/Manualänderung nicht.

Timeout/HTTPunterbrechung nach einem möglichen Auftrag: kein blindes Retry,
keine automatische Cancellation/Rollback/Resume. Gate recovery bleibt geschlossen,
konkrete Receipt/Deployment-/Instanz-/Writerbelege neu erheben. Nach Koordinator-
verlust gelten bestehende #148-Recoveryregeln; frische Recoverfreigabe endet
verified/geschlossen, eigene Resume-Freigabe und Liveprüfung erst anschließend.

## 5. Entscheidung zur vorhandenen Application

**Bedingt wiederverwendbar, noch nicht produktiv nachgewiesen.** Der
[4.4.7-Updatepfad](https://github.com/coollabsio/coolify/blob/86c21c0d5babfa8c7d65a9c27e5863c629a89c7c/app/Http/Controllers/Api/ApplicationsController.php#L3225)
aktualisiert eine vorhandene Application nach UUID und erlaubt build_pack/Pfade.
Für den vorhandenen Dreirollen-Composekandidaten wäre deshalb **Dockerfile →
dockercompose** in derselben Backend-Application nötig, keine zweite Ressource.
Das [Applicationmodell](https://github.com/coollabsio/coolify/blob/86c21c0d5babfa8c7d65a9c27e5863c629a89c7c/app/Models/Application.php#L349)
löscht beim Verlassen von Dockerfile dessen gespeicherte Dockerfile-/Targetfelder.
Umgekehrt entfernt Verlassen von Compose auch Compose-/SERVICE_* Daten.
Ein Buildtypwechsel ist somit keine reversible kosmetische Auswahl: vorher
vollständiger redigierter Konfigurationsbeleg/Backup und eigener Rückweg nötig.

Raw-/Normalparser, exaktes Rendering/Namespace, Pfadvalidierung/UIDs, externe
Netzwerke und Profilwirkung müssen für die tatsächliche Application bestätigt
werden. [Bisherige 4.4.7-Prüfung](coolify_compatibility.md) bleibt gültig;
inaktive Profile verhindern nicht alle Coolifydeploy-Nebenwirkungen.
Die UI kann als bestehende eigenständige Application/Service streamlit bestehen
bleiben; tatsächliche private Verbindung/OIDC und alter Launcher brauchen eine
eigene spätere Abnahme. Kein additives ui-Overlay.

Der Driver kann perspektivisch eine Applicationoperation als einen genehmigten
**Ressourcenscope** koordinieren, aber nie als atomaren Einzelcontainerwechsel
bezeichnen. Aktueller Bestands-/APIbeleg reicht noch nicht zur Implementierung
eines mutierenden Drivers. Same-Application-Adoption daher **requires_operator_confirmation**.

Falls die reale Coolifykonfiguration diese Adoption nicht sicher zulässt: Sleep-
Application unverändert lassen und den Wechsel zurückstellen. Als Entscheidung
wäre ein manuell verwalteter Betrieb **derselben vorhandenen** Composearchitektur
auf demselben Server außerhalb des Coolify-App-Lifecycles prüfbar; Zuständigkeit,
Triggerfence, Proxy-/Netz-/Backupintegration müssten separat genehmigt werden.
Keine neue App/zweite Produktionsressource und keine Alternative jetzt umgesetzt.

## 6. Knappes weiteres Vorgehen

Die [fünf lesenden Pakete](operator_binding_check.md) liefern → echte Bindingdatei
und vertrauenswürdigen Hostcollector spezifizieren → `observe_runtime` und
Scope-v2-Vertrag isoliert testen/reviewen → feste Images/Adoptions-/Rollbackbelege
abnehmen. Nach eigener Mergefreigabe #156→#149→#148→#157; UI#20 separat.
Manueller Erstbootstrap bleibt getrennt: Intake/Writer idle und Backups,
neuen Root/Policy bewusst provisionieren, Store + Gate held, Gateway/API,
Health, einzelner Worker bei held. Keine historischen Queueübernahmen.
Erst neue gemeinsame Settings/Identitäten/Quellenfreigaben und echter Scope-
Driver erlauben separate Resume-/Einzelbatchentscheidung. Kommandos nur im
[bereits vorbereiteten Runbook](rollout.md); nichts davon hier ausgeführt.
