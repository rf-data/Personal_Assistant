# C26-D: verbindlicher Operationscope im bestehenden Gate

Status: Implementierung/Offlineprüfung, **HOLD für jeden Produktiveinsatz**.
Keine Livecollector-/Driveraktivierung und keine automatische Journalmigration.

## Entscheidung vor der Umsetzung

Eine zweite Gatezustandsmaschine würde Admission, Drain, Rollback und Recovery
duplizieren. Stattdessen verwendet v2 dieselbe `Gate`-Implementierung aus #148.
Eigene versionierte Plan-/Approval-/Belegtypen und ein eigenes Journalformat
erweitern deren Prüfstellen. Der Operationscope und die vorhandene strenge
Runtime-Evidenzprüfung aus #157 bleiben die Grundlage.

Explizites Settings-Feld `deployment_gate_protocol=c26-gate-v2` verlangt das
Pflichtgate. Default bleibt `c26-gate-v1`. V1-Journal und v1-Hashsemantik bleiben
erhalten; v2 benutzt ein separates versioniertes Journal. Falsche Auswahl,
gleichzeitige Journalversionen, fehlende Pflichtbelege oder beschädigte Historie
sperren. Keine automatische Übernahme bestehender Journale.

Scopehashes beweisen Datenbindung, keine unabhängige Betreiberidentität oder
authentifizierte Livebeobachtung. Diese Umsetzung akzeptiert ausschließlich
explizite synthetische Offlinebelege. Ein positiver Test bleibt HOLD und ist
keine Freigabe eines produktiven mutierenden Drivers.

## Basis, Reihenfolge und Provenienz

Isolierter Worktree `Personal_Assistant-c26d`, Branch
`feat/c26d-operation-gate-v2`. Geprüfter aktueller `master`:
`e68275205fefb7a5f6db42bc45060e505bfcefb5`, Tree
`d63fcfaf5dab63817dc03fefafb5817f53388195`.
#156/#149 sind darin bereits integriert; sie werden nicht erneut übernommen.

Zuerst #148, dann alle sieben Commits von #157, jeweils regulär mit
`cherry-pick -x`. Keine Konflikte, keine Mergecommits, keine einseitig gewählten
Dateiversionen. Store-Setupretry aus master und Gateguard aus #148 sowie beide
Dockerfile-CLIpfade sind erhalten und durch relevante Regression geprüft.

| Quelle | Originalcommit | Übernahme in diesen Branch |
| --- | --- | --- |
| #148 | `f98eedd671c8a9d9eb58a3b957eda1a91713844d` | `adc56c48865d1c058c0ba53be0a50d59bd132d28` |
| #157, 1 | `3e5a1326fbf3642509ea4d3aabe09aae5067688f` | `8bdefaff2ff4ee60f0cd486e80f639d492724a4c` |
| #157, 2 | `40b6aab02ba6a2bcc5c84477bbd150e537525131` | `177e10829a2c0b20492e3ca105d6c098fb8094fe` |
| #157, 3 | `8cde77313cb55f1e06d3281563dcbb8ee797b369` | `e035e2dcc13872868ac2d094d325ecc52dab4630` |
| #157, 4 | `e470d3a9ebaaad5361ed533a7baa2a6dbaf00c28` | `9c2199cf0c61cd54f15971d0af58dc71b3e09522` |
| #157, 5 | `f502fed60c4e676a29752f417841d6a62a8fe458` | `061770f3068763077c1dd93856b5da5b7bb93a89` |
| #157, 6 | `b616e29981870a7365c821106a831f5df8f90b8a` | `db6c7ad992f1f44bbca141f61930c8bd8636bbe9` |
| #157, 7 | `80c31e52f76c1f3f62102b6884752b722f796e7c` | `1984f30b05eae28c17e1b200cb23d44ec08bf957` |

Merge-Bases zum genannten master: #148
`e581e201ef6b3d6c06aca14de845e0687d213b37`, #157
`e502aa915ad0e928dbe7e92eacd44fff0152912b`. Alle eigenen C26-D-Änderungen
folgen auf `1984f30`; Implementierungscommit ist
`ae98536cd4d6b6f317cf5c09a2ae53d3aefb5991`, gefolgt von der ergänzenden
Validierungsdokumentation. Diese Trennung erlaubt später eine gezielte Übernahme nur
der Integration, falls die Original-PRs zuvor integriert werden.

#160 (`ecac8cfa844a7e4da9e0066a2c49c0c49fb3541d`) bleibt unabhängige
Betriebsabnahmedokumentation, unverändert und nicht als Codebasis übernommen.
Sein damaliger Blocker „v2 nicht im Gate erzwungen“ wird hier **für den
Offlinevertrag** geschlossen; seine Live-/Infrastruktur-/Adminblocker bleiben.
C27 #158 (`a0d3ebf7f64d44dd843f1848e70dc70a3a3af835`) und UI #21
(`218003222d418acc9e93585cd3367b694cd247e2`) bleiben unverändert.

## Konkrete Änderungen und Gatevertrag

| Ebene | Vorher: #148 plus #157 | Nachher bei ausdrücklichem v2 |
| --- | --- | --- |
| Auswahl | Gate kennt v1; Operationsumschlag separat | Settings `deployment_gate_protocol=c26-gate-v2` plus `deployment_gate_required=true`; v1 bleibt Default |
| Plan | ein Rollen-/Imagepaar, Scopehashes | `PlanV2` enthält vollständigen validierten `OperationPlan`: aktuelle und geplante drei Rollen; identischer Ressourcen-/Jobrootanker |
| Approval | Planhash und Aktions-/Zeitfenster | `ApprovalV2` bindet vollständigen Planhash **und** kanonischen Operationscopehash einschließlich Current/Target; maximal eine Stunde, erneute Prüfung unter Lock |
| Beobachtung | v1-Observation oder separater Observerbericht | `ObservationV2` enthält Rohbelege, Binding und beide Readprojektionen; bestehender Observer wird bei jeder relevanten Prüfung erneut ausgeführt |
| Permit | v1-Objekt mit laufender Prüfung | Sitzung, Plan, Scope, Approval, Driver, vorherige konkrete Container-/Namespace-/Deploymentbindung versiegelt; erneute Beobachtung, Journal-/Idle-/Approvalprüfung; genau ein `claim()` unmittelbar vor synthetischer Änderung |
| Journal | hashverkettetes v1-JSONL | separates v2-JSONL mit Version/Protokoll/Offlinemodus, Scopehash, vollständigem Plan/Approval, Sequenz und Hashkette; kein Mischen/Migrieren |
| Verifikation | neue Instanz/Health/Version | vollständige Targetprüfung, neuer Deploymentbeleg und neue Container-ID jeder geänderten Rolle; Host-/Adapterbindung bleibt gleich |
| Erfolg | verified; geschlossen bis Resume | verified_offline, deployment_permitted=false, production_release=blocked; separate neue Resume-Freigabe bleibt erforderlich |

`src/job_control/deployment_scope.py` enthält die versionierten Hüllen und das
sitzungsgebundene Permit, keine zweite Zustandsmaschine oder neue Clients.
`deployment_gate.py` verwendet weiterhin die bestehenden Admission-/Owner-/
Worker-/Wartungslocks, Drain-, Recovery- und Rollbackpfade. Controller, Executor
und Store reichen die Protokollauswahl an dieselben Guards weiter. C22-Restore
kennt beide Journalnamen und hält auch v2-Kopien geschlossen. Der Diagnose-CLI
wählt die entsprechenden Schemas; er erzeugt niemals ein Permit oder Deployment.
Keine DB-Schemaänderung, neue Dependency, Authänderung oder automatische
Verzeichnismigration. Die C16-Persistent-Root-Policy bleibt unverändert wirksam.

Versionen: Gatehüllen und Journal v2; darin `RuntimeScope` weiter schema v1 und
`OperationPlan` schema v2 aus #157. Integerkennungen sind strikt; unbekannte,
falsch typisierte oder zusätzliche Felder werden verworfen. Die vier
[JSON-Schemas](c26_runtime/gate_plan.v2.schema.json) liegen neben den unveränderten
Scope-/Operation-Schemas. Der vorhandene Settings-Snapshot ergänzt ausschließlich
neun Zeilen für das optionale Protokollfeld; sein schema_version bleibt 1.
JSON-Schema allein beweist weder Hashbindung noch Gültigkeit der Fachvalidatoren.

Kanonisierung verwendet den bestehenden UTF-8-JSON-Vertrag (sortierte Schlüssel,
kompakte Separatoren, keine NaN/Infinity) und SHA-256. Der v1-Settingshash lässt das
neue Feld im v1-Modus weg und bleibt dadurch identisch. Der v2-Plan bindet alle
verschachtelten Scopewerte; jede Änderung erfordert neue Hashes **und eine neue
Betreiberfreigabe**. Ein gültiger alter Approvalbeleg wird nicht umgeschrieben.

## Vollständigkeit, Zeit und Recovery

Alle Rollen werden auf Service, Revision, RepoDigest, lokale Image-ID,
unabhängigen Buildreceipt, Commandhash, tatsächliche Settings, Mounts und
Jobrootidentität geprüft. Hinzu kommen Caddy/TLS, Ressourcen-/Server-/Environment-
IDs, Netzmitgliedschaft und Namespace, komplette Host-/Writerinventur,
Health-/Readinessvertrag sowie Triggerpolicy und vollständiges Akteursinventar.
Unbekannte Werte bleiben NO-GO. Der Koordinator prüft seinen lokalen Jobroot
zusätzlich gegen genehmigten Source-/Destinationpfad und Device/Inode.

Runtimebelege dürfen höchstens 30 Sekunden alt und nicht aus der Zukunft sein;
Workerheartbeat bleibt gemäß #157 jünger als zehn Sekunden. Der lokale
Gateworker muss seine bestehenden Leases halten und gemäß Settings frisch sein.
Neue Instanzen werden erst nach erneutem vollständigem Targetnachweis akzeptiert.
Bei ausdrücklich genehmigtem Rollback darf der **bekannt ungesunde** Currentzustand
Health/Ready=false haben; unknown ist auch dann verboten. Identität, Trigger,
Heartbeat und sämtliche übrigen Nachweise werden nie erlassen. Target, Recovery
und Resume müssen gesund und bereit sein.

Unvollständiger Lauf bleibt draining/deploying/verifying oder recovery,
Admissions geschlossen. Beschädigtes/vollgelaufenes Journal lässt auch Recovery
fail-closed scheitern: kein Reparieren, Abschneiden oder Wiederöffnen. Bei gültiger
Historie verlangt Recovery denselben Operationsplan und neue Recover-Freigabe;
danach bleibt verified geschlossen. Rollback ist eine neue umgekehrte Operation
mit eigener Freigabe, kein automatischer Retry. Resume ist nochmals separat.
Initiales Resume aus held verlangt identischen vollständigen Current-/Targetscope.

Journalgrenzen bleiben 1 MiB/1024 Events; Plan-/Approvaldateien im CLI maximal
64 KiB, v2-Beobachtung maximal 256 KiB, gebundener Gateplan maximal 64 KiB.
Mehr Scope bedeutet weniger Events innerhalb derselben Grenze. Keine stille
Rotation oder Kapazitätsausweitung. Teilwrites und fsync-Fehler erteilen kein Permit.
Die Hashkette erkennt Beschädigung, **authentifiziert aber keinen privilegierten
Dateibesitzer**. Zurückspielen einer ganzen alten gültigen Journaldatei durch
den vertrauenswürdigen Rootbesitzer benötigt später einen unabhängigen
monotonen/signierten Kontrollnachweis; dies wird nicht als gelöst ausgegeben.

## V1-Kompatibilität und Umgehungsgrenze

V1-Eingaben, Legacydefaults, Journalbytes und Hashsemantik bleiben verfügbar.
Kein automatisches v2-Bootstrap bei Controller-/Workerstart. Ein fehlendes
v2-Journal muss explizit initialisiert werden und öffnet dabei nichts. V2-Plan
oder Approval werden nie als v1 akzeptiert. Zwei Journalversionen, eine falsche
Konfiguration oder die Rückstufung eines v2-Jobroots auf v1 sperren Admission,
Dispatch und Gateoperationen; auch bei abgeschaltetem Pflichtflag.

**V1 ist nicht für die spätere produktive Dreirollen-v2-Runtime freigegeben.**
Die bisherigen deaktivierten Runtimevorlagen bleiben Legacy-/Offlinevorbereitung.
Ein anderer leerer Root oder ein privilegierter Austausch der Konfiguration lässt
sich durch einen lokalen Journalmarker allein nicht verhindern. Vor produktiver
Freigabe müssen der vertrauenswürdige Launcher und alle Writer nachweislich auf
v2, denselben Root und dieselbe geprüfte Konfiguration festgelegt werden. Keine
Sicherheitsbehauptung gegen beliebigen Pythoncode im Koordinatorprozess oder einen
Rootadministrator. Ein Driver ist vertrauenswürdiger Adapter und muss `claim()`
vor der einzigen Mutation ausführen; das Permit ist keine OS-Sandbox. Es existiert
weiterhin kein produktiver mutierender Driver.

## Sicherheitsmatrix

| Nachweis | Offlineergebnis | Verbleibende Grenze |
| --- | --- | --- |
| Fehlender/unvollständiger Scope; Version/Modus/zusätzliche Felder | bestanden, keine Änderung | Authentische Livequelle fehlt |
| Plan-/Scopehash, Änderung nach Approval, Rollen-/Image-/Buildkonflikt | bestanden, keine Änderung | echte Registry-/Buildreceiptkette fehlt |
| Settings, Mount/Jobroot, Netzwerk, Health/Readiness, Trigger | vorhandene Observernegative plus Gateintegration bestanden | vollständige Liveinventur/Namespaceprüfung offen |
| Veraltete Beobachtung/Heartbeat, abgelaufene Approval | bestanden, keine Änderung | vertrauenswürdige Collectorzeit und frische Wiederholung offen |
| Kopiertes/reaktiviertes/geändertes Permit, Wiederverwendung einer Approval-ID | bestanden | gesamtes Journalrollback durch privilegierten Besitzer siehe oben |
| Konkurrenz von Gate und Resume; doppelte Claimversuche | bestanden; höchstens eine Claim, keine Freigabe | Livekoordinator-Lifecycle/Authentifizierung offen |
| Torn Journal, Hash-/Versionsfehler, doppelte JSONschlüssel, Kurzwrite/fsync | bestanden, geschlossen | reale Datenträger-/Hostausfallabnahme offen |
| Teilfehler, neue Instanz/Deploymentbeleg, Recovery/Rollback/Resume | bestanden, getrennte Freigaben | echter Driver mit Ressourcenscope fehlt |
| C22-Backup/Restore v1 und v2, unveränderte Ursprungsdatei | bestanden, nur neue lokale Testfixtures | produktiver Backup-/Restoretest nicht durchgeführt |
| V1-Default/Hash/Schemas, v2-Downgrade, bestehende C16-/C22-Grenzen | bestanden | Produktionspolicy muss v1 ausdrücklich ausschließen |
| Produktive Betriebsabnahme | **OFFEN / HOLD** | #160 Infrastruktur-, Admin-, Trigger-, Backup- und Rollenabnahme |

## Tatsächlich ausgeführte Validierung

Vorhandene Umgebung:
`../Personal_Assistant-c26b6-planning-results/test-env/bin/python`, Python 3.12.12,
SQLite 3.50.4, pytest 9.1.1, Pydantic 2.14.1/core 2.50.1, HTTPX 0.28.1,
PyYAML 6.0.3 und PyMuPDF 1.27.2.2. Abweichung vom Runtime-Lock:
Pydantic 2.13.4/core 2.46.4 und PyMuPDF 1.28.2 sind dort vorgesehen.
Keine neue Installation, kein uv sync, kein Dockerdownload. Ruff 0.16.0 aus
vorhandenem Pre-commit-Cache. Keine Behauptung eines exakten Runtime-Imagebelegs.

Alle pytest-Läufe mit `PYTHONDONTWRITEBYTECODE=1`,
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `-B -m pytest -q -p no:cacheprovider` und jeweils
eigenem neuen `/tmp/c26d-*`-Basetemp. Gate-/Queue-Unitfixtures sperren Netzwerkzugriffe; SQLite und flock arbeiten nur
auf neu erzeugten synthetischen lokalen Roots. Die gesonderten Transporttests
starten ausschließlich eine testeigene Loopback-API und synthetische lokale Worker.

| Lauf | Ergebnis |
| --- | --- |
| Früher gezielter #148/#157-Baseline-/Integrationslauf | 238 passed; später im erweiterten Lauf enthalten |
| Erweiterte relevante Regression: `test_deployment_gate`, `test_coolify_observer`, `test_coolify_readiness`, `test_c26_runtime_preflight`, `test_c26_runtime_bootstrap`, `test_job_control`, `test_job_executor`, `test_job_store_contention`, `test_deployment_operations`, `test_https_preflight` | **365 passed**, 99,21 s; keine Skips |
| Finale C26-D-Tests: `tests/test_deployment_gate_v2.py` | **61 passed**, 19,54 s; keine Skips |
| Persistent-Root-Grenzen: `tests/test_runtime_paths.py` | **34 passed** im ergänzenden Grenzlauf |
| Lokaler C16-/C26-Transport: `tests/test_deployment_transport.py` | **2 passed**, 17,16 s; isolierte Loopback-Fixtures, außerhalb der Sandbox |

Die vier finalen disjunkten Testgruppen ergeben **462 bestandene Fälle**.
Der erste ergänzende Grenzlauf ergab 34 passed und zwei Transportfehler:
`socket.socket()` wurde von der Codex-Sandbox mit `PermissionError: [Errno 1]
Operation not permitted` verweigert, bevor API/Worker gestartet wurden. Nur diese
zwei Fälle wurden mit genehmigter Sandboxausnahme erneut ausgeführt; danach grün.
Kein Produktiv- oder externer Netzwerkzugriff, keine Installation oder Bereinigung. Frühere
Läufe werden nicht addiert. In der Entwicklung wurden eine falsche Erwartung an
die weiterhin gültige verschachtelte Scopeversion 1 und eine doppelte
Fixture-Leasefreigabe im Restoretest korrigiert; keine offenen Testfehler.
Reguläre Pre-commit-Prüfungen und Commit-Hooks bestanden mit bestehendem
Pre-commit 4.6.2 aus `../ai-job-search/.venv`: Whitespace/EOF/JSON/AST/
Debugstatements/Dateigröße/Ruffformat. YAML-/TOML-Hooks ohne betroffene Dateien
übersprungen; keine übersprungenen pytest-Fälle. Ruffcheck und Formatcheck für
alle elf betroffenen Pythondateien ebenfalls bestanden. Details siehe
[Validierungsmanifest](c26d_validation.v2.json).

Nicht durchgeführt: vollständige Projekt-/UI-Regression, neue Imagebuilds,
exakte Runtime-Lockinstallation, Livecollector-/Driver-/Operatorprüfung,
Produktivjournal/-queue/-DBoperationen, Serververbindung, Browserabnahme oder
Deployment. Kein erneutes ENOSPC. Der verfügbare Plattenplatz wurde nur gelesen;
keine Bereinigung vorhandener Dateien, Worktrees, Branches, Caches oder Umgebungen.

## Empfehlung für spätere Integration und verbleibende Blocker

1. Aktuellen master und die genannten drei Basisstände im Review erneut prüfen.
   Inhaltliche Reihenfolge bleibt **master → #148 → #157 → C26-D**.
2. Dieser Draft enthält schon die gesamten beiden unveränderten Quellserien mit
   Herkunftstrailern plus die separate Integration. Bevorzugt als konsolidierten
   Reviewkandidaten bewerten. Nach eigener Merge-/Triggerfreigabe kann **entweder**
   diese konsolidierte Serie integriert werden **oder** zuerst #148, dann #157
   und anschließend nur die C26-D-Folgeänderung auf aktualisierter Basis.
   Die vollen Serien nicht nochmals blind hintereinander mergen. Original-PRs
   bleiben jetzt unverändert offen; keine Schließung/Ready-/Mergeaktion erfolgt.
3. #160 separat gegen diesen Bericht aktualisieren/reviewen: nur der
   Offline-Gatebindungsblocker entfällt. Kein Infrastruktur- oder Runtime-GO.
4. Vor jedem Livecollector: authentifizierte und redigierte Host-/Coolifyquellen,
   ganze Trigger-/Writerinventur, unverwechselbare Host-/Adapterbindung,
   gesicherte Zeit/Freshness und Registry-/Buildprovenienz nachweisen.
5. Vor Koordinator/Driver: unabhängiger langlebiger Koordinator außerhalb des
   ersetzten Composeverbunds, echte Betreiberidentität und Aktionsautorisierung,
   unveränderliche v2-Konfigurations-/Rootpolicy für sämtliche Writer,
   Replay-/Journalrollbackstrategie und Umgang mit Ausfällen nach Claim prüfen.
   Ein positiver Offlinereport ist niemals ein ausführbares Livepermit.
6. Danach separat genehmigter Driver: genau ein genehmigter Ressourcenscope,
   erneute Evidenz unmittelbar vor dem Seiteneffekt, einmaliges Claim,
   Buildreceipt-/Deployment-/Instanzprüfung, Fehler/Unklarheit bleiben geschlossen.
   Keine automatischen Retries, Rollbacks, Resumes oder alternativen Trigger.
7. Vollständige Betriebsabnahme aus #160 einschließlich Netzwerk/TLS/OIDC,
   Rollen, Queue, Restore und Betreiberfreigabe bleibt erforderlich. **HOLD**.

Die eigene Branch-/Worktreekopie und die Dokumente bleiben für das Draftreview
bewahrt. Keine Integration dieser Dokumente in master und keine Bereinigung
behauptet; die ausdrückliche Merge-/Löschsperre dieses Auftrags hat Vorrang vor dem
allgemeinen Repository-Lifecycle. Alle bestehenden Arbeitsstände bleiben erhalten.
