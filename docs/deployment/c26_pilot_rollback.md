# C26-PILOT-INTEGRATION – Recoverygrenze des Kandidaten

27.10.2026. **Keine Serveränderung; damit aktuell keine Server-Rollbackaktion.**
Die folgende ursprüngliche B01–B05-Sequenz bleibt gültig. Gate-/Koordinator-/
Recoverycode ist jetzt im Kandidaten integriert, seine Tests sind synthetisch.
Der produktive Driver, eine unabhängige monotone Witnessbasis und der
vollständige Konfigurations-/Secret-Rückwegnachweis fehlen weiterhin.

Ein beobachteter neuer synthetischer Planungslauf erreichte wegen einer
SQLite-OperationalError den definierten interrupted-/Quarantänezustand.
Sein Root/Marker wurden nicht gelöscht; redigierte Jobs/Events/Ergebnishash
sind dauerhaft gesichert. Spätere Positivläufe ersetzen keine Ursachenanalyse.
Unbestätigter Cleanup, unbekannter Driverstatus oder Journal-/Witnessverlust:
Annahme geschlossen, keine Wiederholung, kein automatisches Resume.

Lokaler Rückweg für Reviewer ist eine **separate neue Basiskopie** mit geprüftem
Patch, niemals Reset/Clean/Prune des gelieferten oder eines fremden Worktrees.
Vollständiger Patch und Dateimanifest werden vorwärts, tatsächlich angewendet,
byteweise und rückwärts gegen a8af1d9 geprüft. Die gemeinsame Gitverwaltung
bleibt schreibgeschützt; Branch/Worktree und Belege bleiben bis Review erhalten.
Keine Löschung eines MAINT-01/02/03-inventarisierten Artefakts ist autorisiert.
C26-04/#111 bleibt bewusst DEFERRED und wird durch synthetische Restoretests
nicht erledigt.

---

## Bestehender Betreiber-Rollbackvertrag

# C26-PILOT – Rückweg und Konfigurationsschutz

**Vorbereitung, kein Restore und kein Deployment ausgeführt.** Ein Rollback ist
`CONTROLLED CHANGE – SEPARATE APPROVAL REQUIRED`. Unbekannter Zustand bleibt HOLD.
Ziel ist der gemeldete funktionierende Verwaltungszustand, keine Behauptung einer
vorhandenen funktionierenden API-/Workerruntime.

## Wiederherstellungsziel

| Bereich | Zu erhaltender Zustand |
| --- | --- |
| Backend | Bestehende Ressourcen-UUID `personal_assistant:Worker_1`, ursprüngliche Repository-/Buildsettings, Commit `3b91d39195e0d13fe0442d4594b28e431b0f4236`, tatsächlicher alter Registrydigest/Image-ID, `sleep infinity`, keine API-/Workerjobs |
| UI | Bestehende Ressourcen-UUID, Commit `b2cf9ca9ba44ee770dab4d834a6ae8285f34776b`, tatsächliche alte Compose-/Command-/Mountsettings, `streamlit run app_ui.py`, Auth und Backend disabled, **keine Adminroute und kein Hostport 8501** |
| Daten | Bestehende Worker- und UI-Bind-Mounts byte-/rechteidentisch unberührt; neue Pilotdaten bleiben getrennt und werden nicht auf Altpfade kopiert |
| Proxy | Bestehende Demo-/Coolifyrouter, Netzzuordnungen, Middlewarelisten und Zertifikatskonfiguration unverändert |
| Trigger | Auto-Deploy weiterhin aus; keine Preview-/Webhook-/API-/Registry-/Schedulermutation versehentlich wieder öffnen |

Die alten SHAs allein genügen nicht. Ein Neubuild des Legacy-Dockerfiles kann
aufgrund beweglicher Basis/Abhängigkeiten abweichen; deshalb altes abrufbares Image
und genaue Konfiguration vor dem ersten Wechsel sichern. Unbekannte Istwerte sind
Blocker, keine mit Vorlagen zu ersetzenden Defaults.

## Minimale Sicherung vor jeder überschreibenden Änderung

C01 im [Betreiberhandbuch](c26_pilot_operator_checks.md) benötigt einen privaten
Sicherungsspeicher außerhalb des Änderungsziels, dessen Zugriff für den Betreiber
ohne Chromebook geprüft ist. Er umfasst exakte Coolify-Ressourcenkonfigurationen,
Buildkontext-/Pfad-/Branch-/Commitbindung, Commands/Entrypoints, Compose/Labels/
Domain-/Netz-/Health-/Restart-/Limitsettings, Mountsource/-target/-mode/-UID,
Deployhistorie/pending Status und deaktivierte Triggerpfade. Zusätzlich sichere
unabhängige Verfügbarkeit notwendiger Secret-/IdP-/Cookieschlüssel/CA-/TLSkeys;
im Reviewmanifest nur Referenzen, keine Werte. Secretinhalte nicht an Codex geben.

Rekonstruktion auf einem isolierten Konfigurationstestziel durchführen: beweisen,
dass fehlende Masked-Secretwerte aus gesicherter Quelle wieder einzubringen sind
und dass alte Images erreichbar bleiben. Eine Coolify-Screenshotserie mit
maskierten Feldern ist keine vollständige Sicherung. Ein `docker inspect`-Dump
ist wegen Secret-/Datenlecks kein zulässiges Reviewartefakt.

**Hartes STOP-Gate:** Ohne bestätigte Sicherung und nachgewiesenen Rückweg bleiben
Buildtyp-, Entrypoint-, Ressourcen-, Netz-, Domain-, Secret-, Mount-, Rechte- und
Configüberschreibungen blockiert. Keine Betreiberfreigabe in diesem Paket kann
diese fehlende technische Voraussetzung implizit ersetzen. Keine produktive
Datenmigration, kein In-place-Restore, kein rekursives Rechteanpassen, kein
Volumelöschen oder Altimagepruning.

Diese begrenzte Konfigurationssicherung ersetzt nicht #111. Es fehlt weiterhin
der vollständige konsistente Restore von Queue/ContentStore/EvaluationStore,
Indexgeneration/Rebuildstrategie, Katalog/Config und getrennten Secrets auf
endgültigem Zielstorage. Neue Pilotdaten müssen daher vollständig reproduzierbar
und verwerfbar bleiben. Relevant sind auch Gate-/Witness-/Enrollmentcheckpoint
und ihre monotone Absicherung; ein zurückkopiertes altes Journal darf nicht öffnen.

## Kontrollierter Rückweg

| ID / Klasse | Voraussetzung | Exakte Aktion | Erwartung | HOLD | Seiteneffekt | Rückweg |
| --- | --- | --- | --- | --- | --- | --- |
| B01 READ-ONLY CHECK | Störung, kein neuer Job | Coolify: beide inventarisierten Ressourcen → Deployments; aktuellen Digest/Instanz und Status mit Freigabemanifest vergleichen; nur gefilterte Inventur R02/R03 | Tatsächlicher Teilzustand bekannt | Unbekannte UUID/Instanz, laufende Fremdmutation | Nur Lesezugriff | Kein Eingriff |
| B02 CONTROLLED CHANGE – SEPARATE APPROVAL REQUIRED | Funktionierender integrierter Gate-/Stopvertrag, eigene Incidentfreigabe | Im genehmigten Koordinator Annahme schließen und Drain anfordern; UI keine weiteren Startbestätigungen; aktiven Job über seine Owner-Cancel-Aktion abbrechen falls separat autorisiert | Keine neue Annahme; bestätigtes Prozessende oder Quarantäne | Kein Gate, unbekannter Prozess, unbestätigtes Cleanup | Job kann abgebrochen werden | Geschlossen halten; nie Marker löschen |
| B03 CONTROLLED CHANGE – SEPARATE APPROVAL REQUIRED | C01 erfüllt, B01/B02 klar, Zielzustand bekannt | Nur neu angelegte `admin.franke-data.dev`-Route am inventarisierten UIservice aus Domain-/Custom-Labelsettings entfernen, vorherige exakte Listen aus Sicherung wieder einsetzen; getrennt genehmigte DNSänderung zurücknehmen | Adminroute weg; Demo/Coolify unverändert | Rückbau benötigt globale Proxyänderung oder verliert Verwaltungszugang | Adminbrowser getrennt | Geprüfte vorherige Routenkopie, keine Auth-disabled-Adminroute |
| B04 CONTROLLED CHANGE – SEPARATE APPROVAL REQUIRED | Kein aktiver/unklarer Job, Genehmigung für alte Image-/Configkombination, exklusiver Driverpermit | Vorhandene UIressource mit gesichertem alten Compose/Image/Command wiederherstellen; Backendressource auf gesicherten alten Buildtyp/Image/Command `sleep infinity`; Mounts ausschließlich alte unveränderte Zuordnung | Genau ursprünglicher Verwaltungszustand, keine API/Executorjobs, Auto-Deploy aus | Alter Digest/Secret/Config fehlt, Gate-/Witnessverlust, Restprozess | Serviceunterbrechung, Pilotruntime beendet | Annahme geschlossen lassen, Betreiber eskalieren; kein zweiter Versuch bei unklarem Driverstatus |
| B05 LIVE ACCEPTANCE – SEPARATE APPROVAL REQUIRED | B03/B04 nachweislich fertig | R02–R10 erneut; im genehmigten Browser Demo/Coolify prüfen und Adminroute negativ prüfen | Altzustand und Verwaltungszugang bestätigt; keine Hostports/Startjobs | Unerwartete Route, PID, Mount oder Digest | Prüfverkehr | Änderungen geschlossen halten, neue Incidententscheidung |

Falls noch kein wirksamer produktiver Gate-/Driverpfad existiert, ist B02/B04
nicht automatisch ausführbar. Vor dem Erstwechsel muss genau dieser Rückweg
technisch bewiesen sein; der unveränderte `sleep infinity`-Bestand braucht keinen
vorsorglichen Restart. Bei reiner Vorbereitung ohne Serveränderungen ist der
Rückweg: **keine Serveraktion**.

Neue Pilotroots und Belege nach einem Fehler erhalten, Zugang einschränken und
untersuchen; keine Löschung als „Rollback“. Gate-/Grant-/Witness-/Lock-/SQLite-
Dateien niemals manuell editieren oder zurücksetzen. Altimages/Configs nur über
verifizierten einmaligen Rollbackpermit wechseln; neuer Resumegrant bleibt separat.
