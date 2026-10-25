# MAINT-03B – Restrisiken und MAINT-04

25.10.2026. **Produktionsstatus HOLD. Keine Produktionsfreigabe.**
Dieser Auftrag stabilisiert QA; er ersetzt keine Sicherheits-, Betriebs-,
Browser-, Modell- oder Deploymentabnahme. Ursachen und Einzelresultate stehen in
[Fehleranalyse](maint03b_failure_analysis.md), tatsächliche Gates in
[Validierung](maint03b_validation.md).

## Offene Entscheidungen

1. **Workflowkursvertrag / rotes Extended-Gate:** Der bisherige Schematest bleibt
   sichtbar fehlgeschlagen. Frische Vergleiche unter Pydantic 2.13.4 und 2.14.1
   isolieren denselben zusätzlichen Kursenumwert, keinen Artifactfeldumbau.
   Öffentliche Kursakzeptanz, gespeicherte Workflowreports und CS50-Jobparameter
   müssen zusammen entschieden werden. Ohne diesen Review werden weder Snapshots
   ersetzt noch Modellakzeptanzbereiche geändert.
2. **Publikationscrash / Backup:** Ein harter Abbruch zwischen Link und Unlink
   hinterlässt zwei Namen desselben Inodes. Die Backupablehnung ist korrekt und
   bleibt streng. Ein erfolgreicher Signaltestlauf schließt das Zeitfenster nicht.
   Der neue deterministische Test charakterisiert es, behebt es aber nicht.
   Automatische Restbereinigung braucht einen separaten Sicherheits-/Recoveryauftrag
   mit Eigentums-, Root-, Lock-, Hash-, Nichtnutzungs- und Phasennachweisen.
3. **Optionale Profile:** Die acht Qdrantmodule wurden mangels SDK nicht funktional
   geprüft. Ihre Sammlungssperre ist jetzt explizit; aus fehlenden Paketen werden
   keine Produktfehler und aus Modulskips keine bestandenen Testfälle. Ein kaputtes
   installiertes SDK bleibt ein echter Fehler. Vollständige Worker-/LLM-/DOCX-/
   Media- und Modellprofile bleiben ungeprüft.
4. **Lockbereitstellung:** Neue uv-Gruppen verweisen ausschließlich auf bereits
   gelockte Pakete. Die Paketgraph-/Versions-/Hashgleichheit und drei Exporte sind
   geprüft. Vollständige offline Lockneuberechnung/-prüfung und Neuinstallation
   sind wegen fehlender Cacheeinträge nicht erfolgreich. Die verwendeten zwei
   vorhandenen Interpreter sind genau dokumentiert; es gibt keinen behaupteten
   reproduzierten Worker-/Runtime-Neubau.
5. **Isolationsgrenze:** Die großen gemeinsamen Modellpurges sind entfernt; frische
   Import- und Reihenfolgeprobes laufen in Kindprozessen. Die verbleibende lokale
   ZIP-Testsubstitution aus MAINT-03 bleibt unverändert und wird kontrolliert
   zurückgesetzt. Die autouse-Grenze restauriert außerdem Umaskänderungen direkt aufgerufener CLIs.
   Umask ist ein Prozesszustand: keine Threadparallelisierung von
   Fixtures annehmen. Eventuelle künftige parallele Runs brauchen eigene Prozesse.
6. **Netz-/Toolgrenze:** Der Pytestguard schützt den Hauptprozess und direkte
   Infrastrukturstarts; er ist keine transitive Betriebssystemisolation. Die
   bestehenden isolierten Childprobes nutzen synthetische Daten/eigene Guards.
   Echte Listener, Docker, SSH, Cloud, produktive Daten und Zugangsdaten wurden
   nicht als Testvoraussetzung verwendet. External wurde nur gesammelt.
7. **Git-/Integrationsabschluss:** Gemeinsame Gitdatenbank ist schreibgeschützt;
   lokales Commit und Integration fehlen. Der Auftrag verbietet Merges.
   Berichte/Änderungen bleiben im ausdrücklich zugewiesenen Aufgabenworktree und
   werden als überprüfbarer Patch gesichert. Die Verfügbarkeit in `master` nach
   AGENTS.md bleibt **ausstehend**; kein voll integrierter Abschluss.

8. **Zusätzliche Prozessfälle N02, N03 und N04 (E):** N02 wurde
   im vollständigen Lauf fail-closed blockiert; einzeln bestand derselbe Node.
   N03 scheiterte in der korrigierten breiten Auswahl. Erhaltene synthetische
   SQLite-/Eventdaten belegen einen OperationalError im Resumejob mit Quarantäne,
   aber weder dessen SQLitefehlercode noch die auslösende Operation. Eine gemeinsame
   Ursache ist unbewiesen. Kein ignorierter Marker, größerer Timeout oder
   automatischer Retry. Eigene erhaltene Basetempwurzeln sichern die neuen
   Artefakte; phasenbezogene Reproduktion und ein Review sicherer Diagnostik
   sind vor jeder Guardian-/Persistenzkorrektur erforderlich. N04 erreichte den
   PDF-PID-Marker nicht; gesicherte Daten zeigen einen früheren Adapter-Exit 3
   ohne Quarantäne, aber keinen konkreten Adapterfehler. N05s separate leere
   PID-Markerdatei ist dagegen als bestehende Publikationsrace bewiesen und
   ausschließlich im Testhelper atomar korrigiert. Die breite rote Bilanz wird
   durch spätere Einzelpässe nicht ersetzt.

## Alle 19 MAINT-03-Befunde

Die Einstufung ersetzt die ursprüngliche [Risikomatrix](maint03_risk_matrix.md)
nicht. Teilfortschritt ist ausdrücklich kein vollständiger Befundabschluss.

| ID | Einstufung | MAINT-03B / notwendiger Folgeschritt |
| --- | --- | --- |
| R01 | In MAINT-03 erledigt | Sequenzieller Überschreibschutz unverändert; vier Regressionen erneut bestanden. Konkurrenz-/Symlink-No-Replace bleibt außerhalb dieses Vertrags. |
| R02 | In MAINT-03 erledigt | Schreibfreie Dateiliste unverändert; sechs Regressionen erneut bestanden. Allgemeine ensure_dir-Heuristik nicht umgebaut. |
| R03 | In MAINT-03 erledigt | ZIP-Zielkorrektur unverändert; drei Regressionen erneut bestanden. Keine neue Archivpolicy. |
| R04 | In MAINT-03 erledigt | Iterative zyklusfeste Exceptiontraversierung unverändert; 21 Regressionen erneut bestanden. Retrybudgets unverändert. |
| R05 | Für MAINT-04 geeignet | Nur unnötiger AppSessionimport des Smoke-Workers hier entfernt und mit gesperrten Session-/Settingsimports geprüft. Globale Legacykonfiguration bleibt offen. |
| R06 | Für MAINT-04 geeignet | Fehlende URL-/Medium-/SOP-/UI-Importoberflächen einzeln charakterisieren; keine geratenen Reexports. |
| R07 | Für MAINT-04 geeignet | Echtes synthetisches DOCX im kleinen passenden Profil bereitstellen; Importreparatur erst damit nachweisen. Kein python-docx installiert. |
| R08 | Für MAINT-04 geeignet | **21 gleichnamige Klassen nicht zusammengeführt.** Schema-, Default-, Feld-, Klassenidentitäts- und JSONverträglichkeit zuerst messen. |
| R09 | Für MAINT-04 geeignet | Kleine reine Recordbuilder anhand echter typisierter Inputs, Payload-/Provenienz-/Formelgoldens prüfen; Parserduplikate später. |
| R10 | Separater Sicherheitsauftrag erforderlich | Atomizität, Read-Sideeffects und Fehler-/Loginhalte des Legacy-JSONhelpers benötigen eigenen Kompatibilitäts-/Persistenzvertrag. MAINT-04 kann zunächst charakterisieren. |
| R11 | Bewusst zurückgestellt | Große Knowledge-/Parser-/Reviewmodule nicht parallel zu aktiven C27-Strängen zerlegen. Keine nach Größe begründete Refaktorierung. |
| R12 | Bewusst zurückgestellt | Kein nachgewiesener eager Importzyklus. Frische Prozessimporte statt pauschalem strukturellem Umbau. |
| R13 | Für MAINT-04 geeignet | Sync-/Async-Close mit Cancel-/Exception-/Ressourcenfällen charakterisieren; aclose-Migration separat reviewen, keine versteckten Threads. |
| R14 | Für MAINT-04 geeignet; Teilfortschritt MAINT-03B | Schlanke Testgruppen und Exporte ergänzt; doppelte Workerabhängigkeiten und Root-/Worker-/Runtimeprofilangleichung bleiben offen. Keine Upgrades/Hashänderungen. |
| R15 | Für MAINT-04 geeignet | Gebrochene Legacyhelfer nach Klärung ihrer Aufruferverträge einzeln testen/reparieren; keine erfundene Ersatzsession. |
| R16 | Separater Sicherheitsauftrag erforderlich | Legacy-URL-/Bild-/Archivadapter brauchen explizite Transport-, Trust-, Ressourcen- und Pfadgrenzen. Kein pauschaler SSRF-/Zip-Slip-Nachweis behauptet. |
| R17 | Bewusst zurückgestellt; Teilfortschritt MAINT-03B | Testprofile, SDK-/Skipregeln und Isolationsgrenzen dokumentiert. Vollständige Legacy-API-/Coverageinitiative weiterhin offen. |
| R18 | In MAINT-03B erledigt: Isolationsanteil; Vertragsanteil offen | Globale Testgrenze und sechs private Umaskfixtures restaurieren Zustand; Negativmodus explizit; vier Cachepurges entfernt; Retry nach Identität gewählt, beide Reihenfolgen geprüft. Schemasnapshot braucht gesonderten Vertragsreview. |
| R19 | Separater Sicherheitsauftrag erforderlich | MAINT-03B ergänzt deterministischen Crash-/Fail-closed- und Exceptionkontrolltest. Keine Recoverypolicy oder automatische Linkentfernung implementiert. |

## Konkreter Vorschlag MAINT-04

Zuerst den Workflowkursvertrag in einem kleinen eigenständigen Review klären;
der rote Snapshot darf nicht durch ein breites Legacyrefactoring verdeckt werden.
Dabei `Definition`, `Workflow`, `WorkflowParams`, ACL/Katalog, beide Snapshots,
bekannte CS50-JSONdaten und explizite Nicht-CS50-/Unbekannt-Kursfälle gemeinsam
charakterisieren. Gewünschte Abweichungen müssen vor Snapshotänderungen feststehen.

Danach eine Kompatibilitätsmatrix der beiden Parsingmodellfamilien aus
`core.config` und `core.config_parsing` erstellen: alle 21 Namen, Felder,
Defaults/Defaultfactories, required/nullability, Literal-/Enumwerte, Validatoren,
Aliases, JSON-/Schemaserialisierung, Pfad-/Enumroundtrips und alte Importpfade.
Die beiden bereits bekannten Abweichungen bei `ParsePDFSettings` und
`ParseSettings` erhalten eigene Goldens. Frische Prozessimporte verhindern
Klassenidentitätsverwechslungen; blockierte Env-/Session-/SDKimports belegen
saubere Grenzen. Keine Credentials, Originalconfigs oder globale Modulcachepurges.

Erst nach dieser Charakterisierung über kanonische Modelle oder Adapter
entscheiden. SDKfreie Konfigurationsübergabe als Migrationsentwurf dokumentieren;
öffentliche Namen, gespeicherte Defaults und historische JSONdaten bis zu einer
expliziten Migration erhalten. Als kleines davon getrenntes Paket R07/R15 mit
minimalen echten synthetischen DOCX-/Dateifixtures bearbeiten. Optional danach
R09s reine Recordbuilder extrahieren; keine gesamte Parser-/Knowledgekette umbauen.

R19 sollte unabhängig einen Recovery-/Sicherheitsentwurf erhalten. Abnahme:
Phasenabbrüche vor/nach Link, Directorysync und Unlink; konkurrierender Writer,
falsche UID/Modi/Hashes, fremde zusätzliche Links, aktive Locks sowie
wiederholtes Recovery. Unklare Zustände weiter ablehnen und als Evidenz erhalten.
Ein solcher Auftrag darf keine produktiven Bestände automatisch bereinigen.

MAINT-04 bezeichnet hier den nächsten **Code-/QA-Auftrag**. Historische
`docs/audit/maint04`-Cleanupakten und MAINT-01/02/03-Einzelgenehmigungen bleiben
unverändert. Freigabe für Integration, externe Tests und spätere Gitbereinigung
muss den jeweiligen Auftrag und AGENTS.md respektieren.
