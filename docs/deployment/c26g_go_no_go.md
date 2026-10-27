> Historischer G/H-Quellnachweis aus dem übernommenen Arbeitsstand; keine neue Livefreigabe. Aktuelle Betreiberanweisungen: [C26-Pilotchecks](c26_pilot_operator_checks.md). Neue Testbilanz: [Pilotvalidierung](c26_pilot_validation.md).

# C26-G – Go/No-Go

Entscheidungsstand **25.10.2026: HOLD für Produktion.**
Freigegeben durch den Auftrag sind ausschließlich lokale Vorbereitung und
synthetische Offlineprüfung. Keine Kosten-, Infrastruktur-, Daten-, Identity-,
Merge-, Deploy-, Driver- oder Produktionsfreigabe wurde daraus abgeleitet.

## Gegenwärtiges Urteil

| Gegenstand | Urteil | Begründung |
| --- | --- | --- |
| Offlineanalyse/Tests/Reviewpaket | Technisch vorbereitet | Ausführbarer Quellenexport, Testguard, deaktivierter Konfigurationscheck und Verbundrestoreprobe vorhanden; genaue Ergebnisse in [Validierung](c26g_integration_validation.md) |
| Produktive Infrastruktur | HOLD | Kein heutiger Host-/TLS-/Port-/VPN-/Mount-/Trigger-/Imagebeleg |
| Admin-/Fachruntime | HOLD | Echte OIDC-/Browserabnahme, individuelle Betreiberbindings und Launcherwiring fehlen |
| Produktive Deploymentsteuerung | HOLD | D/E/F sind Offlineverträge; reale Producer/Build-/Operator-/Witnessautorität, Livevertrag und mutierender Driver fehlen |
| Daten-/Betriebsabnahme | HOLD | Produktiver Verbundrestore/Evaluationadapter, RPO/RTO, Alarmzustellung und Owner nicht bestätigt; MAINT-Prozessrisiken offen |
| Git-/Dokumentenlifecycle | Pending | Gitmetadaten schreibgeschützt; kein Commit/PR/Merge, kein Nachweis der Dokumente in `master`. Geprüfter Patch als Übergabe; ausdrückliches Merge-/Löschverbot |

Ein erfolgreicher Offlinelauf ändert dieses Urteil nicht. „Keine Messung“ ist
kein bestandener Sicherheitstest. Echte Identity-/Host-/Registrybehauptungen
dürfen nicht als synthetische Captures umetikettiert werden. Keine Freigabe
durch Healthchecks, Journalinitialisierung, Leaseablauf oder Recovery.

## Pflichtnachweise für einen späteren begrenzten Versuch

Alle G01–G26 sind in der [Readiness-Matrix](c26g_readiness_matrix.md) erklärt.
Für jeden Eintrag werden genaue Version/Scope, Datum, prüfende Person und eine
redigierte Evidenzreferenz benötigt. Die folgende Liste ist derzeit **offen**:

- [ ] G01: live Quell-/PR-/Review-/CIzustand und kontrollierte Integration.
- [ ] G02/G03/G12: exakte Backend-/UI-/Base-/uvimages, Plattform, Lockinstallation,
  unabhängige Registry-/Build-/Attestationskette und Vorgängerversion.
- [ ] G04/G05: Coolify-Ressourcen-/Buildtyp-/Rendering-/Rückweg- und vollständige
  Trigger-/Akteurs-/Writerinventur, keine alternative Ausführung.
- [ ] G06/G07: Domain/VPN/TLS/IPv4/IPv6/Proxy/Origin/WebSocket, OIDC/Callback/
  Rollen/Scopes/Secretrechte/Sessionablauf/Widerruf; externe Negativbelege.
- [ ] G08/G09: echte lokale Mounts/UID/Device/Inode/Quota/Reserve; genau ein
  Executor, cgroups, PID-/Netzisolation, kontrollierter Stop/Crash/Cancel.
- [ ] G10: unverwechselbare obligatorische v2-Root-/Settingspolicy aller Writer,
  geschlossenes Bootstrap, kein Downgrade/automatische Journalmigration.
- [ ] G11/G13/G14: echte begrenzte Producer/Freshness/Trust-/Operator-/Witness-
  und unabhängige Koordinatorabnahme; separat reviewter Livevertrag/Driver.
- [ ] G15/G25: verwaltetes Content-/Review-/Search-/Import-/Indexwiring und passende
  UI-Revision samt echter Browser-/Berechtigungs-/Fachabnahme.
- [ ] G16–G19: verschlüsseltes getrenntes Verbundbackup, Evaluationadapter,
  neue isolierte Restoreroots, Hash-/Blob-/Ledger-/ACL-/Idempotenzprüfung,
  Secret-/Key-/Witness-Recovery und gemessene RPO/RTO.
- [ ] G20/G21: echte Health-/Metrik-/Disk-/Backup-/Gate-/Queuebeobachtung sowie
  ausgelöster, zugestellter, bestätigter und aufgelöster Alarm.
- [ ] G22/G23: genehmigter getesteter Rückwärtsscope, Crash-/Unknown-HOLD und
  getrenntes Resume; kausale Behandlung der offenen MAINT-Prozessbefunde.
- [ ] G24/G26: D06/D07-Umfang/Rechte/Reviewer sowie D09/D10/D11, Kosten,
  Betriebs-/Incident-/Backup-/Rollbackowner und Rettungszugang bestätigt.

Optionaler E5/Qdrant/Hybrid-/Mediaumfang darf ausdrücklich ausgeschlossen werden;
dann darf der Release diese Fähigkeiten nicht behaupten oder aktivieren.
Obligatorische Sicherheits-/Trust-/Restore-/Alarmgates sind dadurch nicht abwählbar.
Ein reduzierter Fachumfang benötigt eigene nachvollziehbare Akzeptanzgrenzen.

## Sofortige Abbruchkriterien

Unbekannter Writer/Trigger/Root/Mount/Scope, nicht gebundener Digest/Receipt,
falscher Issuer/SAN/Origin, unsichere Auth-/TLSausnahme, fehlender Witness oder
veraltete Evidenz: kein Start/Claim. Journal-/Ledger-/Blobmanipulation, fehlender
Backupbeleg, unbestätigter Cleanup, Quarantäne, unbekannter Claim-/Driverausgang
oder ausbleibender Alarm: geschlossen bleiben, Zustand sichern, manuelle
Reconciliation. Keine automatische Wiederholung, Link-/Lock-/Markerbereinigung
oder zweite Queue als Ersatz.

## Reihenfolge des späteren tatsächlichen Versuchs

1. Betreiberinventur, Mandat und D09/D10/D11 sowie Release-/Datenumfang klären;
   aktive Trigger/Writer und Rettungszugang bestätigen.
2. Quell-/MAINT-/D/E/F-/UIstände regulär reviewen und später kontrolliert integrieren;
   keine geerbten Serien doppelt übernehmen. Offlineregression mit exakten Images
   und bereits genehmigten Dependencies reproduzieren.
3. Fehlendes Launcherwiring/Verbundbackup und Trust-/Livevertragsbausteine als
   eigene begrenzte Aufgaben liefern; bekannte Prozessfehler gezielt klären.
4. Genehmigtes isoliertes Staging: Producer, Buildautorität, Betreiberverifier,
   externer monotoner Witness und Koordinator unabhängig bereitstellen/abnehmen.
5. Images/TLS/OIDC/VPN/Mounts/Quota/Secrets prüfen; konsistentes Vorabbackup,
   vollständigen Restore und Rückweg auf neuen synthetischen Roots testen.
6. Separat genehmigten Driver bei geschlossenen Annahmen testen; Gateway/API,
   genau ein Executor, UI; Scope-/Instanz-/Health-/Auth-/Browser-/Fachsmokes.
7. Alarmzustellung, kontrollierten Fehler, Recovery/Rollback und neues separates
   Resume abnehmen; alle Pflichtbelege dokumentieren.
8. Benannter Betreiber entscheidet über den **neuen**, exakten produktiven
   Scope. Ohne ausdrückliches späteres Mandat bleibt Produktion HOLD.

## Entscheidungsbogen für eine spätere Freigabe

| Feld | Derzeitiger Eintrag |
| --- | --- |
| Entscheidende Person / Vertretung | nicht benannt |
| Datum / Zeitfenster / Ablauf der Freigabe | offen |
| Host/Server/Environment/Ressource | privat zu bestätigen |
| Backend-/UIrevision, Base-/uv-/Runtimedigests, Plattform | offen |
| Current-/Targetscopehash, Jobroot/Settingsbindung | offen |
| Erlaubte Aktion und Daten-/Funktionsumfang | ausschließlich Offlinevorbereitung dieses Auftrags |
| Pflichtgatebelege / verbleibende Einschränkungen | Matrix; produktive Nachweise offen |
| Backup-/Restore-/Rollback-/Alarmreferenzen und RPO/RTO | offen |
| Zuständigkeiten / Rettungszugang | offen |
| Separate Autorisierung für Mutation/Recovery/Rollback/Resume | nicht erteilt |
| Manuelle Entscheidung | **HOLD** |

Dieser Bogen ist kein Operatorgrant, keine Signatur und kein ausführbares Permit.
Keine Worktrees/Branches entfernt. Für einen späteren Review bleiben alle
vorbestehenden Artefakte und die lokalen synthetischen Ergebnisse erhalten.
