# C23: Umsetzung nach Freigabe des Persistenz-ADR

## Aktueller Umsetzungsstand

18.10.2026, Master `d654f05`: C23-02A/B/C (#76–#78), C23-03 (#79) und C23-04
(#80) sind gemergt. Die ursprünglichen Plan-/Testtabellen bleiben als datierter
Plan erhalten; „geplant“ dort ist keine aktuelle Aussage über bereits gemergten Code.
C23-05/#81 ist inzwischen ebenfalls gemergt; Nullzeiten sind technisch unterstützt,
allgemeine TXTpublikation bleibt gesperrt. C23-06 liefert die
[technische Evaluationsvorbereitung](../cs50/evaluation/c23_real_material_evaluation.md),
aber keine fachliche Realabnahme: nur versionierte Fixtures/HTML sind für
technische Prüfungen freigegeben, keine zusätzlichen lokalen Bundles und kein
bestätigtes unabhängiges Gold. D06/D07, C16-Contentpublikation und produktive
C26-Freigaben bleiben separat. Kein Issue-/Project-/Meilensteinstatuswechsel.

## Historischer Planungsstand vom 17.10.2026

Stand **17.10.2026**, Planungsentwurf. Grundlage sind der aktuelle Backendmaster
`053209ad89fac828c7f47677056c44a624ac1af7`, der
[verbindliche Issue-Entwurf](issue_plan.v1.json),
[Governance](governance.md), [ADR](../architecture/parsed_content_persistence_adr.md)
und [Daten-/Schnittstellenvertrag](../architecture/parsed_content_data_model.md).
C23-01 liefert ausschließlich Dokumentation. C23-02 bis C23-06 bleiben **geplant**;
kein Issue-/Project-/Meilensteinstatus wird hier geändert. Die ältere
[Statusaufnahme](status.md) und [Roadmap](../ROADMAP.md) behalten ihren Datumskontext.

## Reihenfolge und Arbeitsgrenzen

1. D04: ADR einschließlich SQLite+Dateien, IDs/Slots, ACLs und Recovery freigeben.
2. **C23-02**: zunächst isolierte Storebibliothek und zwei Contentadapter,
   Offlineimport-/Read-/Snapshot-Vertrag und synthetische Vertragstests.
3. **C23-03**: Wiederholungs-/Parallelitätsabnahme und expliziter Plan für
   Bestandsbindung. Der Pfadkonflikt aus #72 bleibt bis D06 blockiert.
4. **C23-04**: autorisiertes paginiertes GET-API und UI-Vertragsbeispiele;
   kontrollierte C16-Anbindung ohne Veränderung der bestehenden C18-v1-Kette.
5. **C23-05** kann nach D05 unabhängig umgesetzt werden. TXTadapter erst nach
   Verbraucherabnahme und vollständigem Source-/Receipt-/Bindingvertrag gesondert
   freischalten; SRT-v1 bleibt erhalten.
6. **C23-06** nach D07: berechtigter Korpus und unabhängig beurteilte Goldreferenzen.
   Kann parallel zu 2–5 vorbereitet werden; Originalübernahme benötigt zusätzlich
   C23-03 und konkrete Freigabe. Keine automatische Downloadphase.

C24/C25 sind nachfolgende Verbraucher, keine Implementierung in diesen PRs.
C26 übernimmt später die produktive Mount-/Backup-/Container-/Authabnahme.
Ein expliziter Implementierungsauftrag ist kein pauschaler Server-/Datenauftrag.

## Übergabekette mit Ein-/Ausgaben und Fehlerrändern

| Übergang | Input → Output und vorhandene Funktion | Zusätzlich geplante Arbeit | Fehler / Retry / Provenienz |
| --- | --- | --- | --- |
| Discovery → Import | Expliziter lokaler Snapshot/Manifest → `CourseDiscovery`, `ResourceCandidate`, `MaterialPlan` bzw. `CS50AdapterPlan`; `make_plan`, Lectureauswahl/-adapter | C23-02 `SourceRegistration` und Binding-Snapshot aus vorhandenem Graphen | Fehlende/abweichende Kurs-/Section-/Lecture-/Resource-ID sperrt; gleiche Eingaben gleiche IDs, keine URL-/Dateinamensheuristik |
| Materialimport → Parsing | `MaterialResource` + Rawbytes/`ArtifactReceipt` → `NormalizedDocument` + Bilder + completed Receipt; `MaterialDownloader`, `MaterialProcessor` | Adapter nimmt nur explizite fertige Bundles; neue Parserkonfiguration in separatem Arbeitsbundle | Raw-/Receipt-/Parserkonflikt bleibt Fehler. Kein Download oder Reparse als Reparatur, bestehende Hashes/IDs und Originaldateien erhalten |
| Transcriptimport → Prüfung | `CS50TranscriptBinding`, Raw-SRT, Transcript-JSON, Executionreceipt, Adapterplan → geprüftes `TranscriptDocument`; `CS50Executor`, `validate_document`, Binderinvarianten | C23-02 schmaler `cs50_srt_content_v1`-Adapter ohne Knowledgeimports; vollständige Receipt-/Task-/Inputhashprüfung | Exakte Originalpfade und Bindung erforderlich, Cuezeiten/-text mit Original vergleichen. #72 nicht passend → `UnverifiedBinding`; kein alternativer Root |
| Parsing → Quality Gate | Materialbundle → `MaterialReview(report,handoff)`; `prepare_material_handoff`; SRTbundle → Quellen-/Receipt-/Cueprüfung | Gates auf eingefrorenem Stagingbundle wiederholen, technischen Zustand und semantische Warnungen getrennt ablegen | Fehler sperren Parsed-Veröffentlichung; Warnungen bleiben lesbar, kein fachliches Gütesiegel. Raw kann unabhängig gespeichert bleiben |
| Quality Gate → Persistent Storage | Geprüfte Originalpayloads/Artefakte und Projektion → `SourceVersion`, `PublishedVersion`, `content-publication.v1.json` | C23-02 Storemethoden, Slot/Run/Blob/FK/ACL-Protokoll; ursprüngliche Receipt-/Plan-/Sourcebelege vollständig archivieren | Manifest-/Hashfehler blockieren, Atomizität/Recovery gemäß ADR. Erneuter gleicher Import liefert dieselbe Version. APIstatus nur nach SQLcommit |
| Persistent Storage → C24 | Autorisierte `published`-Version und primäre Aggregationsunits mit Version-/Text-/Rawhashes → späterer Indexplan | C24 nutzt paginierte Store-Reads bzw. scoped Export, indexiert pro Version/Indexkonfiguration und dokumentiert Stale; keine Implementierung hier | Indexfehler verändert Content nicht. ACL/Quarantäne live prüfen; Index vollständig daraus wiederaufbaubar. Qdrantadapter nur zeitbasierte SRTs, keine erfundene Universalabbildung |
| C24 / Storage → C25 | Suchtreffer referenzieren ParsedVersion/Block/Textfenster; C23-04 GET liefert Source/Version/Locator | C25 zeigt Raw/Parsed ohne Knowledge, Originaldownload nur über autorisierte IDroute, unbekannte Zeit sichtbar | Treffer mit fehlender Version/fehlenden Rechten nicht ausgeben; keine Dateisystemzugriffe aus UI, kein SSRF-Bildnachladen |

### C16/C18/C20: erste sichere Anbindung

Die initiale Bibliothek läuft explizit offline. Ein kleiner CLI-Einstieg nach
dem vorhandenen `scripts.cs50_*`-Muster nimmt geprüfte lokale Bundles und einen
expliziten privaten Contentroot an. Dry-run ist Standard; Schreiben verlangt
explizites Ausführen. Report exklusiv an neuem Pfad, kein `--force`. Keine
automatische Discovery beliebiger Bestandsverzeichnisse.

C23-04 ergänzt danach einen explizit freigegebenen **C16-Prozessadapter** für
Contentpublikation, zunächst aus bereits geprüftem `material_bundle`-Katalog.
Er nutzt dieselbe Queue/Executor-/Owner-/Coursekontrolle und schreibt eine
kleine `content-publication.v1.json` als bestehendes C16-Ergebnisartefakt.
Artifactmanifest enthält schema_version, source_id, source_version_id,
parsed_version_id, Payload-/Projektionshashes und Gatezustand; es ist kein
Dateipfadbeleg und keine Ausführungsberechtigung. Neue private Contentroot-
Konfiguration nur opt-in mit explizit versioniertem Settingsvertrag, kein
stilles Zusatzfeld in C16-v1 und keine automatische Configmigration.

Transcriptjobs brauchen einen neuen expliziten Katalogvertrag für
Adapterplan/Binding/Raw/Transcript/Receipt. Dieser muss **vor** Freischaltung des
Transcriptprozessadapters streng validiert und gegen die unveränderte
CS50Sourcebindung getestet werden; kein `material_bundle`-Missbrauch. Direkter
Offline-Transcriptimport der Bibliothek ist davon unabhängig.

Die existierende C18-v1-Kette endet weiterhin am Handoff. Ihr geprüfter Output
kann bewusst als neuer freigegebener Kataloginput bereitgestellt werden;
Joboutputs werden nicht automatisch zu vertrauenswürdigen Inputs erklärt.
Eine spätere zusätzliche Storage-Stage verlangt neue Backend-/UI-Output-/Workflow-
Capabilities und Kompatibilitätstests, weil C20-B/C20-C `Output.kind` und Stages
begrenzen. Sie ist **keine Voraussetzung von C23-02** und wird in C23-04 nicht
als schon vorhandene Integration ausgegeben. Kein zweiter Scheduler, kein
automatischer Index-/Knowledgejob am Ende der Kette.

## C23-02: konkreter Implementierungsumfang

Neue Module (gezielt, keine Verlagerung bestehender Pakete):

| Modul | Änderung / Abnahme |
| --- | --- |
| `src/content_store/models.py` | Strenge eingefrorene Pydantic-Hüllen (Schema 1) gemäß Datenmodell; Originalmodelle referenzieren. Fingerprints, Rawmanifest, Projektionsschema, Nullable-Time-/Locatorvertrag; generische Identitynamespaces ohne Änderung der CS50-IDs |
| `src/content_store/errors.py` | Geschlossene Fehlerklassen/Redaktion gemäß Vertrag; keine rohen DB-/Hostpfadtexte für spätere HTTPantworten |
| `src/content_store/artifacts.py` | Expliziter externer Root, sichere Stream-/Dateiöffnung, Limits, SHA, Staging, fsync/exklusive Publikation; vorhandene `safe_path`-/Directorysync-/Publikationsprimitiven nutzen, Originale nicht hardlinken |
| `src/content_store/store.py` | Eigene content-v1-DBidentität/Schema, alle FKs/Unique/Checks, WAL/volle Synchronisation, Source/ACL/Version/Run/Publikationssequenz; kurze Transaktionen und begrenztes Busyverhalten; keine Änderungen an `jobs.sqlite3` |
| `src/content_store/adapters.py` | Whitelist Material-v1 und SRT-v1. Materialgate/Handoff und exakte Units übernehmen; SRT wie bestehender Binder prüfen, `validate_document` nutzen. Keine Knowledge-, LLM-, Embedding- oder Legacyparserimporte |
| `scripts/cs50_content_import.py` | Konventionsgleiche explizite lokale Dry-run-/Import-/Read-/Recovery-Einstiege; vorhandene Reportdateien nicht ersetzen, keine Pfadsuche. Recovery nur bewusst und nach Runlockprüfung |
| `src/content_store/backup.py` | Isolierter, gestoppter Content-Snapshot/Restore in neue Roots, DB-Backup-API und vollständiges Manifest; keine Veränderung des existierenden C22-Werkzeugs oder produktive Migration |
| `tests/test_content_store_*.py` | Kleine selbst erzeugte HTML-/PDF-/SRT-Bundles, Fehler-/Abbruch-/Rechte-/Restorefälle, untenstehende Matrix |

Schema-v1 enthält Source-/SourceVersion-/ParsedDocument-/ParsedVersion-/Blob-/
Rawref-/Parserconfig-/Run-/Block-/Locator-/ArtifactReference-/Granttabellen plus
monotone Publikations- und Collectionrevision. Für Source/Rawversionen ebenfalls
Publikationssequenzen vergeben, damit paginierte Reads nicht nur Parsed-Versionen
stabil begrenzen. DBinitialisierung ausschließlich explizit auf leerem neuem
Root; fremde DBs und unbekannte Versionen zurückweisen, kein Autoschemaupgrade.
Open-for-read erzeugt keine DB/Verzeichnisse und schreibt keinen Heartbeat.

Stopkriterien: irgendeine Originalmutation, falsche bestehende ID/Hash,
unautorisierte Source, unvollständige sichtbar publizierte Version,
automatischer Job-/Index-/LLMstart oder ungeprüfte #72-Bindung. Erst nach
Behebung erneut gezielt testen, kein breit angelegter Architekturumbau.

## C23-03 bis C23-06: Akzeptanz und Abhängigkeiten

| Entwurf | Konkrete Arbeit / betroffene Stellen | Nachweis und Startbedingung |
| --- | --- | --- |
| C23-03 | Storeimports über unterschiedliche Requestkeys, Parserstände und Neustarts absichern; private Importinventare/Übernahmeplan; bestehende `adapt_cs50`, `execute_cs50`- und Binderprüfung unverändert verwenden | C23-02 abgenommen. Gleiche Bytes/Slot → gleiche Version; andere Rawbytes → neue SourceVersion, anderer Parser → neue Parsed-Version; widersprüchliche Outputbytes → Conflict. #72 erst nach D06 und mit Vorher-/Nachherhashes |
| C23-04 | Obige GET-Routen im vorhandenen HTTPserver als eigener Contentbereich, Capability/DTOs; ACL bereits vor Query/Pagination, feste Grenzen, sichere Rawdownloads; kontrollierter C16-Materialadapter | C23-02; Backendtests plus gesonderte UI-DTO-/Clientarbeit im UI-Repository. Alte Job-/Workflowclients funktionieren weiter; kein HTTPpfad als Filesystemparameter |
| C23-05 | `TranscriptSegment`/TXTimport und zeitbasierte Chunker/Evidenceverbraucher nach explizitem Unknown-Time-Vertrag reparieren; Sourceadapter danach TXT erlauben | D05; relevante Reste aus PR #9 neu prüfen, nicht blind übernehmen. TXT start/end null, duration null; SRT/VTTzeiten unverändert; Timedverbraucher lehnen Unknown sauber ab |
| C23-06 | Vollständige berechtigte Raw/Receipt/Normalized-/Binding-Bundles inventarisieren; C10/C13-Rubrik und unabhängige C11-Gold-/Prediction-Paare erstellen | D07; Missingbundles ausdrücklich ausweisen, keine Downloads. Echte und synthetische Ergebnisse getrennt, manueller Reviewer/Releaseumfang benennen; unabhängige Goldreferenzen niemals aus Predictions ableiten |

### Blockiertes Originalbinding #72

C21-Q.1 dokumentiert Originale unter `data/Harvard/...`, während Receipt und
Adapter `data/lectures/Harvard/...` binden. Der aktuelle Defaultpfad existiert
bereits historisch im Adapter, ein neuer Pfadkonstruktionsbug ist nicht belegt.
Die heute auffindbaren Bytes allein legitimieren keine andere Sourcebindung.
Es gibt in C23-01 weder Originalinventur noch Laufzeitfix.

Konkreter D06-Vorschlag bleibt: nach separater Freigabe ein **neues** kanonisches
Workspace mit expliziten Zielpfaden erstellen, Original-/Receipt-/Transcripttripel
exklusiv und byteidentisch kopieren, vorher/nachher SHA/Größe dokumentieren,
vollständigen ursprünglichen Adapter-/Receipt-/SRT-Reparsevalidierungslauf
ausführen. Originale behalten; keine Symlinks, Receipt-/Source-IDänderung oder
Fallbackwurzel. Fehlender vollständiger Beleg → weiterhin blockiert. Ein späterer
Contentimport darf erst das erfolgreich geprüfte Bundle übernehmen; auch die
Sourceversionregistrierung darf den Konflikt nicht als "nur Metadaten" umgehen.

## Test- und Evaluationsplan

Alle automatisierten Tests zunächst offline mit selbst erzeugten Fixtures,
expliziten temporären Roots und ohne produktive Daten/APIkeys. Tests nicht nur
an DTOs durchführen: echte kleine Dateien/Prozesse, SQLite und Restore verwenden.
Keine Downloads/LLM-/Qdrant-/Embeddingaufrufe. Vorhandene optionale Realtests
bleiben als solche gekennzeichnet und werden ohne Eingaben übersprungen.

| ID / Schritt | Synthetischer Testaufbau | Präzises Erfolgskriterium |
| --- | --- | --- |
| T01 / 02 | HTML-v2 mit Liste/TOC/Links, PDF-v2 mit nummeriertem Code/Bildreferenz, gültiges SRT; vorhandene kleine Fixturemuster nutzen | Import und byteidentischer Payload-/Rawexport; alle vorhandenen IDs, Parserconfig, Hashes, Blockorders und vollständige Provenienz erhalten |
| T02 / 02 | Doc mit Page/BBox/DOM, Chapterpfad und bekannten/unknown Zeitlocatorformen | Werte und Konventionen nach Neustart identisch; None nie in 0 umwandeln; unvollständige bekannte Intervalle abweisen |
| T03 / 02 | C10Handoff mit alternativer Codeview/TOC/Link, PDF-Tabellenprojektion | Alle Originalblöcke lesbar, exakte C10-Unitliste einmalig exportiert, keine Verdopplung; Code nicht ausgeführt |
| T04 / 02 | Bildref ohne Bytes; separat deklarierte fehlende/falsche lokale Bilddatei | Ref-only bleibt Warnung; deklarierte fehlende Bytes/SHAkonflikt blockiert Parsed-Veröffentlichung |
| T05 / 02–03 | Gleiche Bytes/Config zweimal, andere Keys; neue Rawbytes; neuer Parser/Adapter; nur andere JSONformatierung oder acquired_at | Keine Dublette im gleichen Slot; echte Input-/Configänderung getrennte Version; gleiche Slot-ID mit anderen Outputbytes → Conflict, kein stilles Reformatieren |
| T06 / 02–03 | Zwei Prozesse gleichzeitig gleicher Slot und verschiedene Slots | Ein Gewinner pro Slot, andere Antwort Busy/identische Version; kein Überschreiben, FK und Blobrefs vollständig; keine lang gehaltene SQLtransaktion während IO |
| T07 / 02 | Gezielt Prozessabbruch nach Reservierung, Manifestcommit, einzelnen Blobinstallationen, vor/nach finalem Commit und vor C16-Result | Vor Commit keine Parsed-Sichtbarkeit; explizite lockgeschützte Recovery, danach genau eine Version; verlorenes Reply idempotent auflösbar |
| T08 / 02 | Dateitrunkierung/Hashfehler, ungültiges Receipt/Plan/Parserbinding, Blob nach Publikation entfernen | Nie falsche Bytes ausliefern; Quarantäne für alle Betroffenen, kein URL-/Pfadfallback; Gatefehler und semantische Warnungen getrennt |
| T09 / 02–04 | Verschiedene Owner und Coursegrants, Viewer/Operator; ACLentzug während Import und zwischen Seiten; identischer Blob in zwei Sources | Keine fremden Inhalte/Counts/Hashpräsenz; Commit und jede Seite autorisieren erneut; Operator ohne Sourceberechtigung bleibt gesperrt |
| T10 / 02 | FKverletzung, fremde/neuere DB, Read auf fehlendem Root, Disk-/Busyfehler injizieren | Fail closed, keine Adoption/Migration, Read erzeugt nichts; bounded Retry, keine Teilpublikation |
| T11 / 02 | Frischen Prozess gegen publizierten Store starten | IDs/ACLs/Blöcke/Originalhashes persistent, keine impliziten Default-/Latestwechsel oder Reparsejobs |
| T12 / 02 | Contentbackup im gestoppten Zustand, Livewriter/Lockkonflikt, beschädigtes/unvollständiges Manifest, Restore in belegten Pfad | Livebackup abweisen; vollständiger geprüfter isolierter Restore erhält ACL/Tombstones/Versionen/Hashes; kein Overwrite/Jobstart |
| T13 / 03 | Explizite synthetische `data/Harvard` vs `data/lectures/Harvard`-Tripel, passend/falsch/fehlend | Falsche historische Ablage bleibt gesperrt; bytegleiche Inhalte ohne passende Bindung genügen nicht; Originale unverändert |
| T14 / 04 | Tatsächlicher lokaler HTTPserver mit GET-DTOs/Capabilities, Traversal/percentkodierte IDs, große Blocks/Replies, alte UI-Verträge | Feste Routen/Fehler/Pagination/Redaktion, keine beliebigen Pfade oder lokale Filelinks; alte C16/C20tests grün; Source-/Versionfilter vor Pagination |
| T15 / 05 | TXTabsätze ohne Zeiten, intakte/fehlerhafte SRT/VTT-Cues, Chunker/Evidence | TXT null; bekannte SRT/VTT-Cues unverändert, Unknown wird von Timedverbrauchern ausdrücklich zurückgewiesen |
| T16 / 06 | Separat freigegebene echte Notes/Slides/Source-PDF-/SRT-Bundles mit unabhängigen Inhaltsbelegen | Byte-/Locatorroundtrip plus manuelle Rubrik, fehlende Seiten/Code/Bilder/Formeln erfassen; reale Ergebnisse getrennt, kein synthetischer Modellqualitätswert |
| T17 / 26 | Späterer Verbundbackup Jobroot+Contentroot, tatsächliches Volume/Container/UID/Lockverhalten und Restore | Gleiche Snapshot-ID, beide Manifeste/Referenzen intakt, keine Altpfadmutation; ausdrückliche Operatorabnahme, kein behaupteter heutiger Nachweis |

C23-02 endet nach T01–T12 mit gezieltem Ruff und den unmittelbar betroffenen
Material-/Transcript-/Storetests. C23-03 ergänzt T05–T09/T13 unter seinen
Wiederholungsbedingungen; C23-04 T14 plus vorhandene HTTP-/UIregression, C23-05
T15, C23-06 T16. Keine pauschale Gesamtsuite als Ersatz für gezielte Abnahmekriterien.
Spätere Testreports nennen Version, Fixtureherkunft, Pass/Fail/Skip, Testkommando
und Laufzeit. Ein Schema-/Hashroundtrip erfüllt nicht die fachliche Rubrik:
manueller Referenzvergleich von Vollständigkeit, Lesereihenfolge, Code, Tabellen,
Formeln/Bildverweisen bleibt erforderlich.

## Offene Freigaben und verbleibende Risiken

| Entscheidung / Risiko | Konkrete Behandlung |
| --- | --- |
| D04: technische Implementierungsfreigabe | SQLite+Dateien, v1-IDs/Slots, ACLs und Crashprotokoll dieses ADR bestätigen; keine grundlegende Speicherfrage auf C23-02 verschieben |
| D05: TXT-Verbraucherkompatibilität | Nullablezeiten nur mit Verbraucherprüfung; kein generelles Durchreichen in Timedindex/Evidence |
| D06/#72: historischer Pfadkonflikt | Separat autorisierte byteidentische Übernahme; ohne vollständiges korrektes Binding blockiert |
| D07: Korpus und unabhängiger Review | Datenrechte/Bundles/Gold/Reviewer und Releaseumfang vor Realübernahme klären |
| Single-Host/SQLite/Dateien | Kein verteilter Writer; Disk/WAL/kurze Locks messen. PostgreSQL erst bei neuem Betriebsbedarf oder belegtem Engpass neu entscheiden |
| Doppelte Blockprojektionen | Originaldatei bleibt Beleg, Projektion trägt eigenen Schema-/Hashstand; Drift muss abgewiesen werden |
| SHA statt Authentizitätsnachweis | Integrität allein beweist keinen Publisher und keine korrekte Extraktion; begründete Sourcezulassung und Fachreview erforderlich |
| Bestehende C16/C18/C20-Grenzen | Kein Storagekind im heutigen DTO; opt-in Adapter/Capability nötig, keine stillen Schemaänderungen |
| Backup/Retention | Contentroot noch nicht von C22 erfasst; isolierter Storetest zuerst, Verbundbetrieb/Retention/Diskbudget mit D10/D11 in C26 freigeben |
| D08/D09/C24 | Volltext und optionale Semantik separat entscheiden, nichts installieren oder als vorhandene Sourceautorität ausgeben |

## Prüfprotokoll C23-01

Diese Prüfung betrifft nur das Dokumentationspaket; sie führt keine Datenbank,
Migration, Anwendungstests, Ruff, Downloads oder Serviceabfragen aus. GitHubzugriffe
sind auf Default-Branch-/PRmetadaten und die ausdrücklich beauftragte Veröffentlichung
dieses Dokumentations-PRs begrenzt; keine externen Inhalts-/Datenbank-/LLM-APIs.

<!-- c23-validation:start -->
Ergebnis am 17.10.2026 gegen die oben genannte Basis:

- **4 Markdown-Dateien**, keine Runtime-/Modell-/Lock-/Plan-JSON-Änderung.
- **54 lokale Markdownverweise einschließlich Anker** geprüft, alle Ziele gültig.
- **24 unterschiedliche bestehende Testdateien** als Belege geprüft; keine
  Anwendungstests für diesen Dokumentationsauftrag ausgeführt.
- **11 geplante Pythonmethoden** aus dem Dokument mit Standardbibliothek-AST
  geparst; Actorargumente und Signaturmenge geprüft, kein Anwendungscode importiert.
- Synthetisches JSONexzerpt geparst; deterministische Source-/SourceVersion-IDs,
  drei SHA256, zwei Bytegrößen und explizite null-Zeiten überprüft.
- Drei zentrale Bestandsinvarianten statisch bestätigt: berechnete Material-
  Dokument-ID, bestehende float-Zeitfelder und separater Parserworkspace.
- Die **3 C23-01-Akzeptanzkriterien** und C23-02–06 gegen den unveränderten
  Issue-Entwurf abgeglichen; `approved=false`, alle sechs Status `Backlog`.
- `git diff --check` erfolgreich. Ruff/Pytest nicht ausgeführt: ausschließlich
  Markdown geändert, kein neuer oder veränderter ausführbarer Pythoncode.

Die lokale Prüfung nutzte ausschließlich Python-Standardbibliothek und Git;
Prüfskript und Dateihashmanifest wurden außerhalb des Repositories unter
`/tmp/c2301-evidence-20261017/` als Arbeitsnachweis aufbewahrt. Linkziele wurden
lokal geprüft, externe URLs nicht abgerufen. Das bestätigt Dokumentkonsistenz,
nicht die zukünftige Storeimplementierung oder die fachliche Parsingqualität.
<!-- c23-validation:end -->

Nachweise und Grenzen sind im PR mit diesen Dokumenten reviewbar. Kein Status aus
`issue_plan.v1.json` wurde angehoben, keine Issues/Projects/Milestones erstellt
oder verändert und kein Produktionsrelease freigegeben.


## Historische Umsetzungsnachträge C23-03 und C23-04

Die folgenden Absätze dokumentieren den jeweiligen damaligen Branchstand vor
der Zusammenführung. Der aktuelle Merge-/Freigabestatus steht oben. Die getrennten
Abnahmeberichte bleiben mit ihren ursprünglichen Basen und Zählungen maßgeblich.

**Umsetzungsnachtrag C23-04, 18.10.2026:** Auf gemergtem A/B/C (`5986da9`)
ist die [autorisierte Read API v1](../api/content_read_v1.md) im bestehenden
HTTPserver implementiert. C23-03/#79 war offen und wird nicht übernommen.
Die folgenden älteren Planungstabellen sind keine aktuelle Implementierungs-
behauptung. C16-Publikation wird als Folgepaket abgegrenzt: der bestehende
Materialkatalog enthält noch keinen vollständigen B-Implementierungsbeleg;
versionierte Katalog-/Prozess-/Receiptarbeit und gemergte Retryabnahme sind
vor Freischaltung erforderlich. Kein Transcriptadapter und keine C18-Änderung.
C23 bleibt offen, D06/D07 und produktive C26-Freigaben bleiben getrennt.
**Umsetzungsnachtrag 18.10.2026:** A/B/C sind über #76–#78 gemergt. C23-03
ergänzt auf `5986da9` die noch fehlende Wiederholungsabnahme, expliziten Retry
nach Operator-Reject und ein rein lesendes Inventar. Ausgangsmatrix, endgültige
Verträge und Testbefunde stehen im
[Quelleninventar](../operations/c23_source_inventory.md). Die folgenden Tabellen
sind der ursprüngliche Plan, keine Behauptung, A/B/C seien weiterhin unimplementiert.
C23 bleibt offen; D06, D07 sowie C23-04/05/06 und produktive Freigaben bleiben
separate Schritte. Keine Änderung von Issue-/Project-/Meilensteinstatus.

### Historischer C23-05-Nachtrag

**C23-05-Nachtrag 18.10.2026:** Auf Master `b2b994a` werden TXTimporte mit
Nullzeiten, Intervallvalidierung und Timed-Guards ergänzt.
[Vertrag und Verbrauchermatrix](../cs50/contracts/official_transcript_unknown_time.md)
und [Offline-Abnahme](../cs50/evaluation/official_transcript_unknown_time.md)
begrenzen den Nachweis. Ein allgemeiner TXT-ContentStore-Adapter bleibt ausstehend:
Verbraucherabnahme ersetzt keinen Source-/Receipt-/Bindingvertrag. C23-04 war
noch offen; keine Abhängigkeit davon oder Änderung von Issue-/Projectstatus.
Vor PR-Erstellung wurde der Branch auf den inzwischen um #80 ergänzten Master
`1254c2c` abgeglichen; der gemeinsame Transcript-/Content-Read-Vertrag ist geprüft.
