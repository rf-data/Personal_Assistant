# ADR C23-01: Raw Sources und Parsed Content dauerhaft speichern

Stand: **17.10.2026**. Status: **vorgeschlagene Entscheidung zur Freigabe vor
C23-02**, keine implementierte Persistenz und keine Produktionsfreigabe.
Backendbasis: `master` `053209ad89fac828c7f47677056c44a624ac1af7`.
UI-Abgleich: `main` `1d57480ea5848399533c52b2862b7f0be5b9890b`, Tree
`0328defab3dad5aec1088b6d2b4867fca646785e`. Der untersuchte lokale UI-Planungstree
ist mit diesem Default-Tree identisch. Der ältere
[C23.0-Status](../planning/status.md) bleibt ein datierter Nachweis.

Verbindlicher Scope sind die drei Akzeptanzkriterien von C23-01 im
[Issue-Entwurf](../planning/issue_plan.v1.json), dazu
[Roadmap](../ROADMAP.md), [Governance D04–D07](../planning/governance.md) und
[Architektur](../architecture.md). Dieses ADR konkretisiert D04; es gibt weder
Schritt B der GitHub-Planung noch D06, Downloads oder ein Deployment frei.

## Problem und Entscheidung

Raw/Parsed sollen ohne Knowledge-Extraktion dauerhaft lesbar und später in C24
durchsuchbar sein. Heute existieren überprüfbare Dateiverträge, aber kein
gemeinsames Source-/Versions-/Rechteregister. Ein Jobabschluss ist keine dauerhafte
Contentveröffentlichung. Ein erfolgreiches Schema ist kein fachliches Qualitätsurteil.

**Empfehlung: Option D mit den bestehenden Dateiverträgen aus C.** Eine eigene
SQLite-Datenbank `content.sqlite3` verwaltet Sourceidentität, Versionen, ACLs,
Importzustand und referenzierte Artefakte. Unveränderliche Originalbytes und
Parsed-JSON-Dateien bleiben in einem privaten, hashadressierten Dateispeicher.
Existierende Artefakte werden nur nach ausdrücklicher Auswahl geprüft und kopiert;
es gibt keine automatische Bestandsübernahme. Die Datenbank ist für Metadaten und
Veröffentlichungszustand autoritativ, Dateien für ihre exakten Nutzdatenbytes.
Beides bildet gemeinsam den Contentbestand. ACLs/Identitätszuordnungen sind
**nicht** vollständig aus Dateien rekonstruierbar.

Die vorhandene C16-Datenbank `jobs.sqlite3` bleibt unverändert die einzige
Jobqueue. C18 bleibt die Orchestrierung. Es gibt weder eine zweite Queue noch einen
Content-Daemon. Eine Importzustandsmaschine verfolgt ausschließlich einen bereits
beauftragten lokalen Import; sie plant keine Jobs. Qdrant/Chroma sind optionale,
abgeleitete Indizes. Kein Contentimport erzeugt Knowledge, Embeddings oder Vektoren.

## Tatsächlicher Bestand: Modelle, Speicher und Schnittstellen

Alle nachfolgenden Aussagen beruhen auf statischer Quellcode-/Vertragsprüfung am
obigen Tree. Dateien in `data/`, private Kataloge, Datenbanken und Secrets wurden
für dieses ADR nicht geöffnet. Ein implementierter Parser beweist daher nicht,
dass seine realen Ausgabedateien aktuell verfügbar sind.

| Bereich | Modelle, Identitäten und vorhandenes IO | Speicher, Version und Herkunft | Wiederverwendung / konkrete Lücke |
| --- | --- | --- | --- |
| `model_discovery` | `CourseDiscovery`, `SectionDiscovery`, `ResourceCandidate`, `Provenance`; `deterministic_id(kind, *parts)` | Course-ID und deterministische Section-/Resource-/Variant-IDs; URL, Fixture, Locator, Kontextpfad; explizite Discovery-/Adapterpläne | CS50-Identität unverändert übernehmen. `CourseId` ist auf sechs Kurse begrenzt: kein allgemeines Source-/ACL-Register, keine aus URLs erratene Gleichheit |
| `model_materials` | `MaterialResource`, `ParserConfig`, `ArtifactReceipt`, `NormalizedDocument`, `Block`, `Location`, `ImageArtifact`, `MaterialQualityReport` | Schema 1; HTML/PDF Parser v1/v2, Code v1; Material-/Dokument-/Block-IDs; Raw-/Normalized-/Bild-SHA256; DOM, Seite, Zeilen, BBox, Warnungen | Nutzdaten und Validierung erhalten. `document_id` ist eine berechnete Property, nicht automatisch im serialisierten JSON. Receipt beschreibt einen Parserstand, kein Versionsregister |
| `tools_materials` | `MaterialDownloader.obtain/validate`, `MaterialProcessor.parse/inspect`, `make_plan`, `prepare_material_handoff` über Lectureadapter; `map_material`, Visualinventur | `<material-hash>/raw/source`, `receipt.v1.json`, `<material-hash>/<document-hash>/normalized.v1.json`, relative Bilder; `.materials.lock`, exklusive Publikation | Pfadsicherheit, Hashprüfung, C10 und Einmalaggregation nutzen. `parse` verweigert Parserwechsel im selben Receipt: neue Parserstände brauchen getrennte Arbeitsbundles. Kein persistenter Sourcekatalog; C10 hat keinen Lock gegen fremde Schreiber |
| `model_transcribe` | `TranscriptDocument`, `TranscriptSegment(seg_id,start,end,text)`, `TranscriptProvenance` | JSON mit Quelle, Sprache, Cues, Text, optionaler Provenienz; `acquired_at` ist zeitabhängig; kein eigenes Schema-/Dokument-ID-/Hashfeld | Original-JSON als Bytes erhalten, Version/Hashes außen ergänzen. `start/end: float` kollidiert mit TXT-`None`; allgemeines Modell allein bestätigt keine Sourcebindung |
| `tools_transcribe` | `import_transcript`, `import_srt/vtt/txt`, `save_imported_transcript`; allgemeine Audio-/URLrunner existieren separat | Lokaler SRT/VTT/TXT-Import, explizite Sprache/URL/Encoding, exklusiver JSON-Export; Subtitlezeiten aus Cues; keine im Dokument gespeicherten Integritätshashes | SRT/VTT-Importer verwenden; TXT bis C23-05 gesperrt. Allgemeine yt-dlp-/Whisperpfade sind keine implizite C23-Freigabe; identischer Reparse kann `acquired_at` ändern |
| `model_parsing` | `DocumentExtract`, `PDFPageExtract`, `BaseLeaf`/Container, `SpanMeta`, Code-/Table-/Image-Metadaten; HTMLnodes; `ParseContext.doc_id/run_id` außerhalb dieses Pakets | Pydantic-Teilbäume, teils Dataclass-Assembler/dict; lokale numerische IDs, Geometrie/Seiten; kein einheitlicher Raw-/Schema-/Parserfingerprint | Formen/Geometrie als künftige Adaptereingänge nutzbar, nicht mit `NormalizedDocument` austauschbar. IDs/Defaults sind keine globale Provenienz; kein bestehendes kanonisches Source-Modell |
| `tools_parsing` | `parse_document`: DIY-PDF oder Docling; `extract_pdf_file` → Postprocessing → `assemble_single_pdf`; weitere HTML/Text/Wiki-Tools | `ParseContext.save_folder/save_name`; Docling schreibt `parsed/<stem>_docling.json` und Markdown mit öffnendem Modus `w`; DIY liefert `Result`/Assemblerausgaben | Kein gemeinsamer exklusiver/hashgebundener Exportvertrag. Nur späterer expliziter Legacyadapter, niemals dynamisches Importieren/Ausführen zur Bestandsinventur; Doclingexport und Markdown nicht doppelt zählen |
| `tools_lecture` | `CS50TranscriptBinding`, Adapter-/Courseplan, `CS50Executor`, `validate_document`; `LectureMaterialHandoff` | Default `data/lectures/Harvard/<course>/cs50-v1/<section>/<lecture-hash>/<resource-hash>/{source.srt,transcript.json,execution.v1.json}`; Source-ID = Subtitle-Resource-ID, verschieden von Lecture-ID; Receipt v1 bindet Task-/Input-/Outputhashes | Exakte Bindings und Reparseprüfung nutzen. Handoff enthält ganzen Materialvertrag, Units, Exclusions, alternative Views. Legacy `LectureResource` verliert Blockidentität; zeitbasierte `KnowledgeEvidence` ist kein allgemeiner Materiallocator |
| `tools_rag` | CS50 `IngestionPlan`, `SourceIndexPlan`, `TranscriptPayload`, `VectorArtifact`; `build_ingestion_plan`, `revalidate_plan`, `verify_hit`, optional `upsert_plan` | Separate Transcriptcollection, Source-/Raw-/Transcript-/Receipt-/Chunk-/Provenienzhashes; Cue-IDs, Zeitintervalle und Zeichenfenster; lokale Pläne/Uploadstatus | Retrievalprovenienz und strenge Sourceprüfung nutzen. Vertrag nur für gebundene zeitbasierte SRTs, kein universeller Contentstore. Legacy-Chroma/SOP-RAG und Knowledgeindex sind davon getrennt |
| `job_control` | `Principal`, `Settings`, `CatalogEntry`, `Job`, `Artifact`, `Store`, Controller/Executor/Guardian | Private SQLite v1 mit `jobs/events/worker`, WAL, `BEGIN IMMEDIATE`, `synchronous=FULL`, Owner/Request-Key; Input-/Resultdateien unter Jobroot; genehmigter Katalog mit Hashes | Rollen-/Course-Prüfung und Prozesskontrolle nutzen. Keine Contenttabellen in dieser DB; `Store` nicht als allgemeine DB-Basisklasse umbauen. Job-/Artifact-ID ist kein fachliches Parsed-Versionsobjekt |
| `workflows` | `Definition`, `Stage`, `Output`, `Workflow`, `State`; `service.inspect/submit`, Engine/Validation | Definition/State Schema 1; `workflows/<id>/state.v1.json` plus Historie; relative Outputrefs mit SHA/Größe; C16-Run-ID, deterministischer DAG und Resume | Bestehende fünfstufige Materialkette bis Handoff verwenden. `Output.kind` hat noch kein Content-Ref; max. 13 Stages/3 Materialien. Kein heutiger Storage-/Indexstage; Erweiterung muss Backend- und UI-Vertrag bewusst versionieren |

Quellanker: [Materialmodelle](../../src/model_materials/materials.py),
[Materialverarbeitung](../../src/tools_materials/processing.py),
[Transcriptmodelle](../../src/model_transcribe/data_transcribe.py),
[Importer](../../src/tools_transcribe/import_transcript.py),
[Legacyformen](../../src/model_parsing/base_classes_parsing.py),
[Legacyparser](../../src/tools_parsing/parse_document.py),
[Discovery](../../src/model_discovery/cs50.py),
[Lectureadapter](../../src/tools_lecture/adapt_cs50.py),
[Sourcevalidierung](../../src/tools_lecture/execute_cs50.py),
[Handoff](../../src/tools_lecture/material_handoff.py),
[Ingestion](../../src/tools_rag/cs50_ingestion.py),
[Indexpayload](../../src/model_discovery/cs50_index.py),
[Jobstore](../../src/job_control/store.py),
[Workflowmodelle](../../src/workflows/models.py).

### Tests und Knowledge-Abhängigkeiten des Bestands

| Bereich | Vorhandene gezielte Tests / Vertrag | Abgrenzung |
| --- | --- | --- |
| Discovery | `tests/test_cs50_discovery.py`, `test_cs50_selection.py`, `test_cs50_lecture_adapter.py` | Offlinegraph, Auswahl und deterministische Bindings |
| Materialmodelle/-IO | `test_cs50_material_contracts.py`, `test_cs50_material_download.py`, `test_cs50_material_processing.py`, `test_cs50_material_e2e.py` | Bytehashes, Receipt, Resume; keine fachliche Vollständigkeitsgarantie |
| Block-/Visualqualität | `test_cs50_material_html_semantics.py`, `test_cs50_material_pdf_v2.py`, `test_cs50_material_quality.py`, `test_cs50_visual_inventory.py`; [C10](../cs50/contracts/material_quality.md), [C13](../visual_inventory.md) | Strukturen, Referenzen und Warnungen, keine Bild-/Formelsemantik |
| Transcript/Lecture | `test_official_transcript_import.py`, `test_cs50_executor.py`, `test_cs50_portable_input.py`, `test_cs50_knowledge_input.py` | Original-SRT-Reparse, Receipthashes und portable Inputs; bekannte TXT-Lücke bleibt offen |
| Legacyparsing | allgemeine Module vorhanden; keine vergleichbare eigene Receipt-/Versionsroundtrip-Suite im untersuchten Testbestand gefunden | Neue Adapter brauchen explizite Tests, keine pauschale Behauptung eines geprüften Bestands |
| RAG | `test_cs50_index_contract.py`, `test_cs50_ingestion.py`, `test_cs50_retrieval.py`, `test_cs50_embeddings.py` | Synthetische/Fake- und optionale Laufzeitpfade unterscheiden; kein aktueller Realpilotnachweis |
| C16/C18/C20/C22 | `test_job_control.py`, `test_cs50_workflows.py`, `test_workflow_http.py`, `test_deployment_operations.py`, `test_deployment_pdf_restore.py` | Historische technische Nachweise in [C22](../deployment/c22_validation.md); durch C23-01 nicht neu ausgeführt |

Materialmodelle/C10 und der lokale Transcriptimport brauchen keine
Knowledge-Extraktion. Der bestehende Binder
[`bind_cs50_transcript.py`](../../src/tools_knowledge/bind_cs50_transcript.py)
prüft Receipts und Originalbindung lesend, importiert jedoch Knowledge-Modelle
und `find_knowledge` auf Modulebene. C23 übernimmt seine **Prüfinvarianten**, nicht
diese Importabhängigkeit: ein schmaler Contentadapter nutzt `CS50TranscriptBinding`,
`validate_document`, sichere Pfade und dieselben Task-/Receipthashchecks.
Kein Umbau der Knowledgepipeline ist dafür erforderlich. Das neue Paket darf
`model_knowledge`, LLM-/Embedding-/Chroma-/Doclingrunner nicht importieren.

### UI-Schnittstelle und verfügbare Ausgaben

Im separaten UI-Tree existieren `admin_ui_package/c16_client.py`,
`workflow_contract.py`, `workflow_state.py`, `workflow_view.py`. Der Client
verwendet feste authentifizierte Routen, begrenzte Antworten, keine Redirects
und individuelle Backend-Subjects; DTOs werden streng validiert. Er liest keine
Backenddateien. Es gibt dort noch keinen Source-/Parsed-/Search-Vertrag.
[UI-Client am geprüften Main](https://github.com/rf-data/personal-assistant-ui/blob/1d57480ea5848399533c52b2862b7f0be5b9890b/admin_ui_package/c16_client.py).
Die UI erhält C23-04-Lese-DTOs separat, ohne Backendmodelle oder DB zu importieren.
Alte C20-DTOs dürfen neue Storageoutputs nicht stillschweigend akzeptieren.

Im versionierten Repository verfügbar sind synthetische C10-Beispielreports,
kleine HTML-/PDF-Fixtures, C11s synthetischer Goldsatz und technische
Abnahmeberichte. Reale Week-0-Notes-/Slides-/Source-PDF-Bundles wurden hier nicht
als vorhanden bestätigt; C23-06 muss vollständige berechtigte Tripel liefern.
Der Originalpfadkonflikt aus [Draft #72](https://github.com/rf-data/Personal_Assistant/pull/72)
bleibt unverified: `data/Harvard/...` ist nicht die vereinbarte Bindung
`data/lectures/Harvard/...`. Die historische Ablage-/Bereitstellungsabweichung
hat keinen nachgewiesenen aktuellen Konstruktorfehler; Verursacher/Zeitpunkt
sind unbekannt. Keine Pfadsuche, Symlinks oder Receiptumschreibung als Reparatur.

## Vergleich der Speicheroptionen

Bewertung für den vorhandenen Single-Host-Vertrag, ohne neue Benchmarks oder
Installationen. JSONB meint in B Parsed-Nutzdaten in PostgreSQL; Rawbytes bleiben
auch dort separat. Ein Objectstore in A wäre ein zusätzlicher Dienst, kein
bereits existierender Bestandteil.

| Kriterium | A: PostgreSQL + Dateien/Objectstore | B: PostgreSQL + Parsed-JSONB | C: Dateien autoritativ + abgeleiteter Index | D: separate SQLite + Dateien |
| --- | --- | --- | --- | --- |
| Modellwiederverwendung | Bestehende JSONbytes direkt referenzierbar | Bestehende Struktur importierbar; JSONB erhält keine ursprüngliche Bytekodierung | Höchste Wiederverwendung vorhandener Bundles | Bestehende JSONbytes plus kleine neue Registerhüllen |
| Integrität / Transaktionen | FKs/SQL; Datei-/DB-Grenze bleibt | Parsedinhalt und Metadaten gemeinsam transaktional; Rawgrenze bleibt; Original-JSON zusätzlich nötig für Bytehash | Einzeldateien atomar, keine gemeinsame ACL-/Versions-/Publikationstransaktion | FKs/Checks/SQL; Datei-/DB-Grenze bleibt und braucht untenstehendes Protokoll |
| Idempotenz / Versionen | Unique Keys/Versionstabellen neu entwerfen | Ebenso; JSONB allein löst Identität nicht | Zusätzliche Manifeste, Sperren und Transaktionslog nötig | Unique Slot/Manifestfingerprints; einzelner Writer genügt zunächst |
| Abfragen / Volltext | SQL und serverseitiger Volltext gut ausbaubar | SQL/JSONB-Abfragen, Volltext; zusätzliche Indizes/Writekosten | Einfache Metadaten, Querabfragen sonst Scans oder abgeleiteter Suchindex | SQL-Metadaten/Blockprojektionen; FTS5 nur Kandidat nach Compile-/Sprachtests in C24 |
| Wachstum / Performance | Mehrere Writer/Hosts möglich; Betrieb und Messung nötig | Große JSON-Dokumente/Indizes vergrößern DB und Sicherung; keine angenommene Geschwindigkeitsgarantie | Viele Dateien/Scans, globales Rechte-/Statusfilter teuer | Begrenzte Schreibparallelität; große Payloads außerhalb DB; Blocktextprojektion kostet zusätzlichen Platz |
| Bestandsübernahme | Expliziter geprüfter Import erforderlich | Konvertierung und Bytehashtrennung zusätzlich | Bestehende Pfadprobleme bleiben ohne Import ungelöst | Expliziter Import; kein Umschreiben bestehender Receipts |
| Backup / Restore | DB und Blobs konsistent sichern; zusätzlicher Dienst/Objectstore | Größeres DBbackup; Raw-/Original-JSON weiter gemeinsam sichern | Dateisnapshot einfacher, aber Index/ACL-Zustand darf nicht verlorengehen | Gestoppter Verbundsnapshot via SQLite-Backup-API plus Manifest/Blobs |
| Hetzner Single Host | Zusätzlicher Server, Zugangsdaten, Updates, Ressourcen | Gleicher Betriebsbedarf; größere zentrale DB | Kein Dienst, aber komplexe Eigenentwicklung für das Register | Standardbibliothek, kein zusätzlicher Server; lokales Volume bleibt Voraussetzung |
| Wartung | DBbetrieb, Restore-/Versionskompetenz zusätzlich | Dazu DBinhalt-/JSONB-Schemaversionen | Wenig DBbetrieb, mehr selbstgebautes Konsistenz-/Indexprotokoll | DBschema und Backup pflegen; WAL/Disk/Lockfehler explizit behandeln |
| Neue Quelltypen | Register/Adapter erweiterbar | Flexible Nutzdaten, dennoch Typschema/Gates nötig | Neue Manifeste/Adapter nötig | Typisierte Adapter und locatorfähige Projektionen, gleicher Blob-/Registervertrag |
| C16/C18/C20 | Separater Store, neue Stage/DTOs nötig | Ebenso | Stage/DTOs und belastbare Veröffentlichung trotzdem nötig | Separater Store/Stage/DTOs; keine gemeinsame Queue-DB |
| C24 | Separat versionierter Indexconsumer | Volltext im DBdienst möglich, Vektoren weiterhin abgeleitet | Index muss bei jedem Treffer Quelle/ACL/Version bestätigen | Wiederaufbaubarer Index aus veröffentlichten Blockprojektionen; Autorität bleibt Contentstore |

A ist die vorgesehene **spätere Alternative** bei Mehrhostbetrieb oder belegter
Writer-/Queryüberlastung. B wird zunächst verworfen: zusätzliche Dienste und
doppelte Bytehaltung bei noch nicht nachgewiesenem JSONB-Abfragebedarf. C allein
wird verworfen: ein vollständig abgeleiteter Index reicht für ACLs, belastbare
Quellenidentität und globale Veröffentlichung nicht. D ist kein Ersatz für
PostgreSQL unter beliebiger Last: genau ein lokales POSIX-Dateisystem, ein Host,
kurze SQL-Schreibtransaktionen. Keine NFS-/Netzwerk-WAL- oder Mehrhostfreigabe.

Keine Leistungswerte werden behauptet. C23-02 misst Imports/DBgröße/Locks mit
kleinen und begrenzten größeren synthetischen Sätzen. Wiederholte Busyfehler
innerhalb des festgelegten Budgets oder geplante mehrere Hosts lösen ein neues
ADR aus, keine automatische Backendumschaltung. C24 entscheidet Volltexttechnik
und Sprachverhalten separat. Neue Quelldateitypen ändern den Adaptervertrag,
nicht die Unveränderlichkeit der vorhandenen Nutzdaten.

## Speicher- und Konsistenzvertrag

Das [Datenmodell](parsed_content_data_model.md) definiert Identitäten, Tabellen,
API und Fehler; der [Umsetzungsplan](../planning/c23_implementation_plan.md)
ordnet die Implementierung zu. Geplantes privates Root, außerhalb des Repos und
getrennt von C16-Root und Katalog:

```text
<content_root>/content.sqlite3        # eigene Schema-ID content-v1, nicht jobs-v1
<content_root>/blobs/sha256/ab/<sha>  # unveränderliche Bytes, keine Originalpfad-Aliasse
<content_root>/staging/<run_id>/     # begrenzt, privat; vor Veröffentlichung unsichtbar
<content_root>/.content-maintenance.lock
<content_root>/locks/<run_id>.lock
```

Root 0700, Dateien 0600, kontrollierte UID/GID und explizite Rootkonfiguration;
keine produktiven Pfade werden durch dieses ADR angelegt. Blobs liegen auf
demselben lokalen Dateisystem wie Staging. Keine Hardlinks zu Originalen;
die kurzlebige exklusive Linkpublikation aus `publish_bytes` muss nach Abschluss
wieder genau einen Link hinterlassen. Pfadkomponenten/Symlinks/Spezialdateien
abweisen. SHA256 wird über Originalbytes gerechnet, niemals über neu formatiertes
JSON. Metadaten und deterministische Projektionen haben eigene Hashdomänen.

### Veröffentlichung eines Imports

1. Actor/Scopes und explizites registriertes Bundle prüfen. Shared-Wartungslock
   und Runlock halten. Kurze SQL-Transaktion reserviert den eindeutigen Importslot
   und `ProcessingRun(preparing)` mit zufälliger Attempt-ID. Kein Jobstart.
2. Nur explizite Originalpfade öffnen, erwartete Größe/Hashes prüfen und Bytes
   in eigene Stagingdateien kopieren; neue C23-Artefaktgrenzen vor Allokation
   anwenden. Aus den kopierten Bytes einen isolierten Bundle-Snapshot mit den
   **ursprünglichen relativen Bindings** erstellen und Gate erneut ausführen.
   Originale ruhen oder ändern sich: Hashabweichung sperrt; kein TOCTOU-Vertrauen
   auf einen früher gespeicherten Report. Gate, Originalbinding und Projektion
   müssen denselben Snapshot meinen.
3. Geprüften Artefaktmanifesthash samt Blob-Refs in kurzem SQL-Commit als
   `prepared` speichern. Diese Refs schützen Blobs auch vor einer späteren GC.
   Datenbank-FKs und alle Identitätsbindungen validieren.
4. Stagingbytes `fsync`, Blobdateien exklusiv unter SHA installieren, vorhandene
   Dateien über offenen sicheren Handle vollständig nachhashen und Größe prüfen,
   dann Verzeichnisse synchronisieren. Nichts überschreiben. Beschädigter bereits
   vorhandener Blob ist ein Incident, keine Einladung zum Ersetzen.
5. Letzte SQL-Transaktion mit `BEGIN IMMEDIATE`: Actor/ACLrevision erneut prüfen,
   alle Artefaktrefs und gespeicherten Snapshotbelege bestätigen, Blöcke/Locatoren/
   Projektionen einfügen, `ParsedDocumentVersion=published`, monotonen
   `publication_seq` und Run `committed` gemeinsam setzen. `foreign_keys=ON`,
   WAL, `synchronous=FULL`; ein globaler CAS auf veröffentlichte Defaults ist
   nicht nötig, da C23 keine implizite "aktuelle" Version wählt.
6. Erst nach Commit Erfolg ausgeben und eigene Stagingreste kontrolliert
   entfernen. Ein verlorenes Erfolgs-Reply wird mit demselben Schlüssel erneut
   gelesen. C16 vermerkt die Content-Ref danach in seinem eigenen Jobresultat;
   es gibt keine verteilte Transaktion über beide SQLite-Dateien.

Dateiinstallation und SQL sind **keine** gemeinsame atomare Transaktion. Atomar
ist allein die Sichtbarkeit aller Metadaten einer fertigen Parsed-Version.
Runlock und Shared-Wartungslock bleiben von 1 bis 6 gehalten. GC/Restore benötigen
den exklusiven Wartungslock; sie können keinen Blob zwischen Prüfung und Commit
entfernen. Dateien dürfen ausschließlich über diesen Store geschrieben werden;
unkoordinierte Hostmanipulation bleibt ein Incident. Zugriffe prüfen Dateigröße
und Hash vor vollständiger Auslieferung erneut.

### Zustände, Fehler und Recovery

Source ist `registered` oder `tombstoned`; SourceVersion wird erst nach geprüfter
Rawpublikation `verified`. Raw kann ohne Parser persistieren. Parsed-Versionen
sind vor dem finalen Commit unsichtbar. Runzustand und Contentzustand bleiben
getrennt, ohne automatische Fortsetzung eines C16-Jobs.

| Ereignis / Zustand | Sichtbarkeit und konkrete Behandlung |
| --- | --- |
| `preparing`, Abbruch vor Manifest | Keine Parsed-Version. Nach belegtem Prozessende Runlock exklusiv übernehmen, eigene Stagingbytes prüfen oder Run `failed` markieren; neuer expliziter Versuch, keine Dateiadoption |
| `prepared`, Abbruch vor/während Blobinstallation | Keine Parsed-Version. Manifest und vorhandene Blobs nachprüfen, fehlende Bytes ausschließlich aus geprüftem Staging nachinstallieren; sonst `blocked`/neu explizit importieren |
| Blobs vorhanden, finaler SQL-Commit fehlt | `prepared`-Refs erhalten. Explizite Recovery wiederholt Gate/ACL/Hashprüfung und den letzten Commit; verwaiste unregistrierte Blobs separat inventarisieren, nicht veröffentlichen |
| Commit erfolgreich, Antwort/Jobresultat fehlt | Bereits veröffentlichte ID/Hashes liefern; C16-Wiederholung bindet dieselbe Ref, kein neuer Inhalt. Jobfehler darf committed Content nicht löschen |
| Gleicher Slot parallel | Unique Constraint und Runlock; zweiter Versuch erhält `Busy` oder nach Prüfung dieselbe Veröffentlichung. Keine zwei Gewinner, keine Vollkopie in einer langen SQL-Transaktion |
| Gleiche Rawbytes, neuer Parser | Gleiche SourceVersion, anderer Parser-/Adapterfingerprint und Parsed-Version; altes Receipt bleibt erhalten; Parserarbeitsbundles getrennt |
| Derselbe Slot, andere Nutzdaten/Projektion | `Conflict`; keine automatische neue Version oder Überschreibung. Auch nur geändertes `acquired_at` kann diesen Konflikt verursachen; bestehendes geprüftes Outputbundle wiederverwenden oder tatsächliche Importkonfiguration/version explizit ändern |
| Fehlender/defekter publizierter Blob | Betroffene Versionen `quarantined`; Zugriffe fehlschlagen, C24-Treffer sperren. Reparatur nur byteidentisch aus geprüftem Backup mit anschließendem vollständigem Gate; niemals durch Reparse ersetzen |
| DB-/FK-/Schemafehler, Disk voll | Fail closed, SQLrollback; vorhandene Publikationen nicht überschreiben. Fremde/neuere DB nicht adoptieren oder automatisch migrieren; Staging/Incidentbelege behalten |
| ACL während Import geändert | Vor Commit nochmals prüfen, sonst `Forbidden`; keine Veröffentlichung mit veraltetem Scope |
| Prozess hängt / Lease wirkt alt | Zeitablauf allein beweist kein Prozessende. Recovery nur mit erlangtem Runlock; kein automatischer Doppelschreiber |

Recovery ist ein späterer expliziter lokaler Diagnose-/Fortsetzungsbefehl, kein
selbsttätiger Watcher. Runereignisse protokollieren Zustand/Fehlercode und IDs,
keine Tokens, kompletten Texte oder absoluten Originalpfade in HTTPantworten.

### Retention und Restore

Standard ist Aufbewahrung ohne automatische Löschung. Owner/Operator darf eine
Quelle bewusst tombstonen; sie verschwindet aus allen fachlichen Reads und
Indexexporten. DB-FKs sind restriktiv, kein `ON DELETE CASCADE` für Artefaktbytes.
Eine spätere physische Löschung verlangt freigegebenen Retentionsplan, Audit,
Prüfung aller Source-/Version-/Run-/Annotationrefs, gestoppte Schreiber und
exklusiven Wartungslock. Geteilte Blobs erst löschen, wenn **keine** Referenz und
kein `prepared`-Import sie benötigt. Quarantäne ist keine automatische Löschung.
Indexbestände werden separat ungültig gemacht; verlorene C16-Jobreferenzen werden
als unaufgelöst angezeigt, niemals still neu zugeordnet.

[C22-Backup](../deployment/backup_restore.md) deckt den neuen Contentroot derzeit
**nicht** ab. C23-02 braucht zunächst einen isolierten Content-Snapshotvertrag:
Schreiber stoppen, exklusiven Contentlock halten, SQLite-Backup-API verwenden,
alle referenzierten Blobs und relevante Run-/Stagingbelege mit SHA/Größe sichern;
vollständiges Manifest zuletzt exklusiv schreiben und synchronisieren. ACLs,
Aliasbindungen, Tombstones und Quarantäne gehören ins Backup, Secrets separat.

Ein späterer C26-Verbundsnapshot stoppt API/Executor/alle Contentwriter und nimmt
Locks immer in Reihenfolge **C22-Operationslock → Content-Wartungslock**.
Keine umgekehrte verschachtelte Lockaufnahme. Job- und Contentbackup erhalten
dieselbe Snapshot-ID, werden aber erst nach Prüfung beider Manifeste als Bundle
freigegeben. Restore ausschließlich in neue isolierte Roots, DBintegrität/FKs,
sämtliche Hashes, Version-/Block-/ACLbezüge und Job-Refs prüfen. Nichtterminale
Runs bleiben für explizite Recovery gesperrt. Kein Auto-Start, keine Reindexierung,
keine absolute Pfadumschreibung; Originalbindings bleiben Auditdaten.

## Folgen, Grenzen und Freigaben

Neue Arbeit sind kleine fachliche Register-/Versionshüllen, eine Contentprojektion,
ein Store und zwei Adapter. Vorhandene Parser und Nutzdatenmodelle werden nicht
ersetzt. SQLprojektion und Dateiinhalt verdoppeln gegebenenfalls Blocktext;
Projektionen müssen hashgebunden und wiederaufbaubar sein. SHA beweist Integrität,
keine Authentizität oder fachliche Richtigkeit. Lokale Administratoren mit
Volumezugriff liegen außerhalb der API-ACL-Sicherheitsgrenze.

Vor C23-02 ausdrücklich freigeben: **D04**, dieses ADR inklusive SQLite+Dateien,
Identitäts-/Slotvertrag, ACLregel und Konsistenzprotokoll. Das ist eine
Implementierungsfreigabe für isolierte Offlinearbeit, keine Host-/Datenfreigabe.
Vor Originalübernahme zusätzlich **D06** (konkretes Vorgehen zu #72) und **D07**
(berechtigter Korpus); vor TXT **D05**. D08 entscheidet C24-Volltext, D09–D11
Dependencies/Images, Zielhost, Retention, Betrieb/Restore und Release. Ein Merge
dieses Dokumentations-PRs allein führt keine dieser Aktionen aus.

## Prüfung dieses ADR

Nur statische Prüfung: Quellmodelle und Funktionssignaturen gelesen, UI-Tree
abgeglichen, lokale Markdownziele/Anker und referenzierte Testdateien geprüft,
Python-Signaturentwurf per AST geparst, synthetisches JSON-Beispiel samt IDs und
Text-/Payloadhashes geprüft, C23-Akzeptanzabdeckung und unveränderten Planstatus
kontrolliert, `git diff --check`. Konkrete Ergebnisse stehen im
[Prüfprotokoll des Umsetzungsplans](../planning/c23_implementation_plan.md#prüfprotokoll-c23-01).
Keine Datenbank erstellt, kein Anwendungstest-/Ruff-Erfolg behauptet, keine
Originaldatei geändert und keine fachliche oder produktive Abnahme durchgeführt.
