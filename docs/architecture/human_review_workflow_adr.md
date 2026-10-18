# C24-05-B: Architekturvorbereitung für menschliche Reviews

18.10.2026 · **Entwurf / abhängige Implementierung blockiert**.
Backendbasis: `origin/master` `87ea32f5e9e3f4826f6bbd84ed0d28073fc3fb87`.
Branch: `feat/c24-05b-human-review-workflow`.

## Voraussetzung und tatsächlicher Arbeitsumfang

Der Auftrag verlangt ausdrücklich: Solange C24-05-A nicht gemergt ist, keine davon
abhängige Implementierung auf einer angenommenen API beginnen. Bei Prüfung ist
[PR #87](https://github.com/rf-data/Personal_Assistant/pull/87) offen, nicht gemergt,
Head `5a7d050685c381dffd0574aaff62f704c78e7350`. #83–#86 sind integriert.
Die A-Modelle sind damit **Reviewstand, kein integrierter Mastervertrag**.

Diese Vorarbeit liefert ausschließlich Bestandsaufnahme, Architekturentscheidung,
Berechtigungsgrenzen und eine konkrete Implementierungs-/Abnahmereihenfolge.
Keine Runtime, DBinitialisierung, Migration, neuen Pydanticmodelle, APIrouten,
UIelemente, Testfixtures oder tatsächlichen menschlichen Goldurteile.
Die technische Umsetzung und das im Auftrag definierte UI-End-to-End-Erfolgskriterium
sind **nicht abgeschlossen**. Ein Merge dieses Dokuments würde sie nicht erfüllen.

Maßgeblich bleiben [Indexing-ADR](retrieval_indexing_adr.md),
[C24-Plan](../planning/c24_implementation_plan.md),
[Governance](../planning/governance.md),
[Content-Read-Vertrag](../api/content_read_v1.md) und
[C23-06-Realabnahmegrenzen](../cs50/evaluation/c23_real_material_evaluation.md).

## Tatsächlich geprüfter Bestand

| Komponente | Implementierter Stand und Konsequenz |
| --- | --- |
| `src/content_store/models.py` | Autoritative Source-/Raw-/ParsedVersion-, Parser-, Block- und Locatormodelle. Keine neue Quellenidentität oder Originalkopie im Reviewstore |
| `src/content_store/reader.py`, `http.py` | Autorisierte paginierte redigierte Leseansichten und geprüfte Rawattachments. Kein Review-/Schreibvertrag |
| `src/content_store/store.py::_authorize` | Course plus Owner oder read-Grant; Sourcewrite zusätzlich Operator und Owner. read-Grant erlaubt keine Reviewbestätigung |
| `src/job_control/controller.py::authenticate` | Bestehendes Bearerbinding auf konfigurierte Identity/Principal mit Subject, viewer/operator und Courses. Kein globaler Administrator |
| `src/job_control/http.py::Application` | Ein Gateway; Authentifizierung vor Routing. Content opt-in über separate Konfiguration. Hier später Reviewcapability ergänzen, keinen zweiten Server |
| C24-02/C24-03 | Ein geprüfter Originalankerprojektor und interne autorisierte FTS5-Suche; SearchResultPage bleibt der gemeinsame Ergebnisvertrag. Noch keine Search-HTTP-Capability |
| C24-04/#86 | Integrierter FakeEmbedder/Fake-Transport mit Vector-DTO. Reale Modell-/Qdrant-/Hybridabnahme weiterhin gesperrt |
| C23-06 `material_evaluation.py` | CorpusManifest, GoldReference, GoldDataset, Reviewstatus und Parsingbeobachtungen. Keine menschliche Reviewpersistenz oder UI |
| C24-05-A/#87 | Noch unintegrierter Reviewstand: ContentRetrievalEvaluationSet, ContentRelevanceJudgment, IndependentReview, ReviewPool und RetrievalEvaluationReport. Nach Merge erneut prüfen und direkt verwenden |
| Job-/Workflowstore | Job-/Runidentitäten und Kontrollzustände, keine menschlichen Reviewentscheidungen. Nicht als konkurrierende Review-Queue oder Autorisierung verwenden |

Keine produktiven Content-/Job-/Indexinstanzen geöffnet. Keine privaten Originale
inventarisiert, kopiert oder heruntergeladen. Keine `.env`-/Tokendateien gelesen.

## Trennung der Repositories und UI-Iststand

UI: `rf-data/personal-assistant-ui`, Defaultbranch **main**, geprüfter Head
`1d57480ea5848399533c52b2862b7f0be5b9890b`. Der lokale primäre UIcheckout steht
noch auf `b2cf9ca9ba44ee770dab4d834a6ae8285f34776b` und ist keine aktuelle
Integrationsbasis. Keine Änderung, Aktualisierung oder neue App dort.

Aktuelle versionierte UIquellen wurden am gepinnten GitHubhead read-only geprüft:

- [Architektur](https://github.com/rf-data/personal-assistant-ui/blob/1d57480ea5848399533c52b2862b7f0be5b9890b/docs/admin_architecture.md):
  kanonischer Streamlit-Einstieg `app_admin.py`, vorhandenes `admin_ui_package`;
  Legacyseite `app_admin/F_p0_ingestion_admin.py` und ZIPvorlagen sind kein Routing.
- [C16-Client](https://github.com/rf-data/personal-assistant-ui/blob/1d57480ea5848399533c52b2862b7f0be5b9890b/admin_ui_package/c16_client.py):
  requestlokaler authentifizierter HTTPclient, individuelle UI-/Backend-Subject-
  und Rollenbindung, private serverseitige Tokendatei, keine Redirects/impliziten
  Proxys, begrenzte JSONantworten. Tatsächlicher Job-/Workflowclient, kein Reviewclient.
- [UIsecurity](https://github.com/rf-data/personal-assistant-ui/blob/1d57480ea5848399533c52b2862b7f0be5b9890b/admin_ui_package/security.py),
  `live_config.py` und `live_app.py`: serververifizierte OIDCclaims/Subjectlisten,
  vorhandene Viewer-/Operatorzuordnung, subjectbezogene Pollerzustände. Kein
  Widgetfeld darf Backend-Rechte oder Revieweridentität erzeugen.

Kein Frontendbuild und keine Frontendtests ausgeführt. Es handelt sich um
Streamlit/Python, nicht um eine neu aufzubauende React-/Nodeanwendung.

## Architekturentscheidung vor Implementierung

### Separate Reviewpersistenz

Vorgesehen ist ein eigener privater EvaluationStore mit explizitem absolutem Root
außerhalb Repository, ContentStore und Jobroot. Separate lokale SQLiteDB,
versioniertes Schema und expliziter Initialisierungseinstieg. Normales Öffnen
initialisiert oder migriert nichts; unbekanntes Schema sperrt. Künftige Migrationen
explizit mit geprüftem Backup und Vor-/Nachbedingungen, kein automatisches ALTER.

Fachliche Bereiche: Dataset-/Scopebindung, ReviewTask, Annotation/Urteil,
ReviewRevision/Decision, bewusst erzeugte Export-/Evaluations-/Abnahmesnapshots.
Keine zweite Kopie aller Raw-/Parsedbytes. Speichern nur unveränderliche IDs/Hashes,
Original-Locatoren, erforderliche begrenzte manuelle Annotationen/Korrekturen und
Auditdaten. Neue Workflowhüllen dürfen bestehende Gold-/Metrikmodelle nicht ersetzen.
Konkrete Tabellen, DDL, Constraints und Modellfelder erst nach Merge/Prüfung von A.

Jeder Save ist eine transaktionale neue Revision mit vorheriger Revision, server-
seitigem Subject/UTCzeitpunkt, Begründung, Quellenbindung, Urteil und Digest.
Taskhead/Status nur mittels Compare-and-Swap auf erwartete Revision wechseln;
konkurrierender anderer Intent ergibt kontrollierten Konflikt. Derselbe explizite
Idempotency-Key desselben Actors/Tasks mit gleichem Intent liefert dasselbe Ergebnis;
anderer Intent unter gleichem Key ist ein Konflikt. Kein Upsert bestätigter Urteile.

Append-only-Anwendungsoperationen und Hashketten machen Änderungen nachvollziehbar;
sie sind keine Manipulationssicherheitsgarantie gegen einen Angreifer mit gleicher
Dateisystem-/DBberechtigung. Auditwiederherstellung benötigt einen separat geprüften
Snapshotvertrag. Kein ungeprüfter Anschluss an C22-/Content-Verbundbackup.

### Autorisierung und konsistente Bindung

Bestehendes Gateway authentifiziert den tatsächlichen Principal. Reviewer/Approver
werden daraus serverseitig gebunden, niemals aus `reviewer`, `actor` oder `role`
eines Requestbodys. Zuweisung allein erteilt kein Source-Leserecht. Jede Liste,
Region, Revision, Entscheidung, Evaluation und jeder Export prüft aktuellen Course-
Scope sowie Sourceownership/read-Grant und Quarantäne/Tombstone/Hashzustand erneut.
Unbekannte und fremde Tasks gleich behandeln; keine ungefilterten Gesamtzahlen.

**Offener Review-Schreibvertrag:** Bestehende read-Grants und die allgemeine
Operatorrolle definieren keine fachliche Reviewer-/Approverbefugnis. Vorgeschlagen
ist ein separater serverkonfigurierter Reviewopt-in mit expliziten Subject-/Course-
und Datasetberechtigungen, Sourcezugriff und passender Taskzuweisung. Keine neue
globale Rolle, kein shared Operator-Serviceaccount und keine Rechte aus UIwidgets.
Die konkrete zulässige Kombination von Owner, beauftragtem unabhängigem Reviewer
und Approver muss vor Schreibfreigabe autoritativ festgelegt und getestet werden.
Bis dahin bleiben Reviewwrites **disabled**; kein Fallback auf read-Grant oder
pauschales `role=operator`. Das entspricht der ausdrücklichen Auftragsbedingung.

Lockvorschlag: Taskreferenz zunächst kurz read-only lesen und Lock schließen;
Contentmaintenance/shared → Content-DB/shared → Review-DB/Schreibtransaktion.
Taskhead/Assignment/Scope unter Reviewtransaktion nochmals vergleichen; Contentguard
bis zum Reviewcommit halten. Kein Rückaufruf von gehaltenem Reviewlock in Content,
keine behauptete Zwei-DB-Schreibatomizität. Widerruf vor einem neuen Request sperrt
auch alte Review-/Export-/Reportansichten. Bestehende Locks und nonblocking Busy-
Semantik verwenden, Ressourcen- und Antwortlimits vor APIimplementierung festlegen.

### Status und Korrekturen

Vorgesehene Übergänge: `pending → in_review → confirmed|rejected|needs_clarification`;
Klärung kann mit neuem begründeten Entwurf erneut in_review gehen. Confirmed und
rejected Revisionen bleiben erhalten. Eine Korrektur beginnt eine neue Revision
mit explizitem Verweis auf den bisherigen Head; kein stilles Wiederöffnen/Überschreiben.
Source-/Versions-/Raw-/Parser-/Locatorbindung bleibt unverändert. Andere Version
verlangt einen neuen überprüften Task, keine Revision mit umgebogenem Sourcebezug.

Parsingurteil korrekt/teilweise korrekt/falsch/nicht entscheidbar von Workflowstatus
trennen: Ein confirmed Review kann einen fachlichen Parserfehler bestätigen.
Korrekturtext dient nur als unabhängige Goldbeobachtung/Befund. Nie ParsedDocument
überschreiben. Retrievalgrad 0 ist bestätigt irrelevant, kein fehlendes Urteil.

### Originalansicht und Unabhängigkeit

Originalansicht konsumiert nur autorisierte C23-04-Originalattachments/Locatoren;
Parseransicht bestehende Block-/Text-/Struktur-DTos. Raworiginal und Parsedfenster
klar getrennt beschriften, kein Parsertext als angebliches Original präsentieren.

- HTML inert/escaped darstellen, DOM-/Blockbezug erhalten; keine aktiven Skripte,
  Remoteimages, beliebigen URLs oder `unsafe_allow_html` für Quellmaterial.
- Code exakt inklusive CRLF, Tabs, Einrückung und Unicode; Zeilennummern als separate
  Ansicht, nie Bestandteil der gespeicherten Goldzeichenfolge.
- SRT mit Cue-ID, tatsächlichen Zeiten und überlappenden Intervallen. TXT ohne
  Zeiten bleibt unknown. Koordinaten nicht aus Textoffsets interpolieren.
- PDF nur mit bestehendem sicherem Renderer inline anzeigen; sonst geprüfter
  Originalanhang plus Seiten-/Locatoransicht und sichtbarer Rendererlücke. Keine
  neue PDFpipeline, Geometrie oder erfundene Originaltextansicht.

Regionsauswahl bindet vollständigen vorhandenen Blocktext-SHA, Codepointintervall
und Locator. Vorschau serverseitig gegen Originalanker verifizieren. Browser-
UTF-16-Indizes nicht als Python-Unicode-Codepoints speichern; Emoji/Combining/CRLF-
Grenzen testen. Ohne sichere Selektionskomponente zunächst kontrollierte begrenzte
Codepointauswahl mit exakter Vorschau statt ungeprüfter Offsetübernahme.

Parsinggold und Retrievalgold haben unterschiedliche Zwecke: Ein vom Parser
verlorener Originaltext kann eine unabhängige C23-06-Parsingbeobachtung sein.
Er darf nicht als gültiger C24-05-A-Blockanker fingiert werden, wenn exakte
Parsed-Textdeckung fehlt. Dann Parsingbefund/needs_clarification; keine automatische
Textreparatur oder Rückprojektion aus Suchtreffern.

Goldannotationsmodus zeigt Frage und erlaubten Originalkorpus, **keine Rankings**.
Optional eingeblendete Modell-/Retrievalunterstützung ausdrücklich protokollieren;
keine unabhängige Bestätigung derselben unterstützten Annotation ohne gesonderten
unabhängigen Reviewbeleg. Vorschläge können Pendingentwürfe sein, niemals Reviewer.

### Gateway, UI und Evaluationsübergabe

Optionalen Reviewadapter später in `Application` ergänzen, analog zum Contentopt-in.
Vorgesehener Capabilitybereich `/v1/evaluation` ist **Entwurf**, kein existierender
Endpunkt oder verbindlicher DTO. Benötigte Operationen: Taskliste/-detail, Original-
region, Entwurf, Entscheidung, Revisionen, Goldexport, freigegebener Evaluationslauf,
Report und manuelle Abnahmeentscheidung. Authentifizierung vor Dispatch, feste
redigierte Fehler, Größen-/Paginationlimits, revisionsgebundene Konflikte und
explizite Idempotenz. Keine Hostpfade, frei wählbaren Dateien oder Rohmaterial-
Uploads als Ersatz für autoritative Contentidentitäten.

PR A implementiert Backend nach A-Merge und festgelegtem Schreibvertrag. Erst nach
Integration dieses tatsächlichen Backendvertrags beginnt PR B im **eigenen** aktuellen
UIworktree von `main`. Bestehenden Client/Navigation erweitern: Dashboard,
Parsingvergleich, unabhängige Goldannotation, Revisionen und Ergebnis-/Abnahmeansicht.
Nach Save serverseitigen Zustand neu lesen; kein optimistisches „Bestätigt“ aus
Session-State. Bei ACL-/Capability-/Versionsfehlern Auswahl und alte Originaldaten
verwerfen. Keine UI gegen angenommene Routen, zweite App oder zweite Anmeldung.

Export confirmed Retrievalurteile direkt in die nach Merge geprüften A-Modelle;
Parsingbeobachtungen in vorhandenes C23-06-Gold. Dataset-/Pool-Scope, Quellenhashes,
Reviewhistorie und Provenienz vollständig binden. Ein bestätigter Task allein
beweist keine Poolvollständigkeit. Reviewpool erfordert eigene nachvollziehbare
Bestätigung; Rejected/Pending und nicht mehr zugängliche Quellen bleiben ausgeschlossen.
Keine zweite Precision-/Recall-/MRR-/nDCGimplementierung und kein Reindex durch Review.

EvaluationStore bleibt für Reviewentscheidungen autoritativ. Explizite JSON-/
Markdown-/ggf. CSVexports sind unveränderliche versionierte Snapshots mit gebundenem
Revisions-/Scope-/Quelldigest; kein stilles Überschreiben. Nicht automatisch alle
Originalbytes/A-VersionEvidence in öffentliche Exporte oder Git aufnehmen.
CSVtext gegen Formelinterpretation schützen. Exportimport nur als validierbarer
Snapshot/Entwurf, niemals als Umgehung serverseitiger Reviewerbestätigung.

Abnahmebericht enthält Korpus/Version/Scope, Source-/Parsed-/Parser-/Retrievalbindung,
Generation, Abdeckung, Gold-/Revisionsreferenzen, Parsingbefunde, A-Metriken, technische
Locator-/Provenienz-/Sicherheitsergebnisse, Einschränkungen, offene/gesperrte Prüfungen,
manuelle Entscheidung/Begründung, authentifizierten Approver, UTCzeit und Digest.
accepted/accepted_with_limitations/rejected/not_evaluable beschreibt eine ausdrückliche
Entscheidung mit begrenztem Scope. Bestätigter ACL-/Leakfehler sperrt jede Freigabe;
grüne Tests oder ein confirmed Task geben keine fachliche Abnahme. Synthetische
Abnahme bleibt synthetisch; D06/D07 und Real-CS50-Freigabe bleiben separat.

## Geplante Abnahme und verbleibende Blockaden

| Reihenfolge | Nachweis / Grenze |
| --- | --- |
| 1 | #87 mergen, tatsächlichen Master/A-Vertrag erneut prüfen; dieses Dokument erteilt keinen Mergeauftrag |
| 2 | Expliziten serverseitigen Reviewer-/Approver-Schreibvertrag festlegen; ohne ihn Writes disabled |
| 3 | Backendmodelle/SQLite/Revisionen/HTTP/Export mit bestehendem Auth-/Contentguard implementieren und PR A reviewen |
| 4 | PR A integrieren; UI aus aktuellem main im getrennten Worktree erweitern; tatsächliche DTOs und Clientgrenzen verwenden |
| 5 | Synthetischen E2E-Lauf: verifiziertes B-Bundle → ContentStore → authentifizierte Originalansicht → Annotation → Commit → Neustart → Revision → Goldexport → A-Report → manuelle begrenzte Abnahme |
| 6 | Reale Evaluation erst nach expliziten Originalrechten, vollständigen Bundles, unabhängigem Gold, Poolreview und D06/D07 durchführen; derzeit blocked |

Geplante Tests: explizite Initialisierung/Schema-/Migrationssperren, Transaktions-
abbruch und Wiederöffnung, ungültige Übergänge, CAS-/Idempotenzkonflikte, unveränderliche
bestätigte Revisionen, Korrekturhistorie, fehlendes Schreibrecht, Grantentzug, gesperrte
Versionen, falsche Versions-/Block-/Text-/Locatorbezüge, Unicode/Whitespace/Unknown-Time,
unabhängiger Annotationsmodus, Export-/Importbindung, A-Pool-/Nullmetriken, Leakblocker
und Approverbindung. UI-AppTests am tatsächlichen Gateway plus betroffene Content-
und A-Regressionen; Ruff Check/Format und diff check. Kein Erfolg vor Ausführung.

## Tatsächliche Prüfungen dieser Vorarbeit

Geprüft: GitHub-Mergestatus #83–#87, gepinnte Backend-/UIquellen, bestehende
Authorisierungs-/Originalanzeigeverträge und lokale Dokumentationsverweise.
`git diff --check` erfolgreich; 15 lokale Dokumentationsverweise geprüft.
Keine Pythondatei geändert;
keine Pytest-/Ruff-/UI-/DB-/Migrationstests gestartet und keine entsprechenden
Erfolge behauptet. Kein Browser-/OIDC-/Produktivserverstart oder Dependencydownload.

**Implemented:** ausschließlich dieses Architektur-/Bestandsdokument und Planverweis.
**Blocked:** Reviewbackend durch ungemergtes A; Reviewwrites zusätzlich bis zum
festgelegten Berechtigungsvertrag; Review-UI bis zum integrierten Backendvertrag.
**Not checked:** Runtime, Reviewpersistenz, API, UI, menschliche Originalprüfung und
fachliche Abnahme. **Out of scope dieser Vorarbeit:** sämtliche abhängige Umsetzung.

Keine temporären Datenstores oder UIworktrees erzeugt. Der eigene saubere Backend-
Worktree bleibt für den offenen Dokumentations-PR bestehen. Primäre und andere
Worktrees bleiben unverändert; keine automatische Zusammenführung/Bereinigung.
