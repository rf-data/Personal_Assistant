# C24-05-B1: Human Review Backend v1

Runtimebasis: Master `d2b5e05e732ef677fe8e8b4ccbb4d76c6d532e60`, C24-05-A/#87
integriert. Architekturvorbereitung [#88](https://github.com/rf-data/Personal_Assistant/pull/88)
am Head `f3fae9ef6d2c919adb12b08242bf84819f2b42f2` und Pilotvorbereitung
[#89](https://github.com/rf-data/Personal_Assistant/pull/89) sind weiterhin offen.
Dieses Paket implementiert deren Backendteil; es ist keine UI- oder Realabnahme.
[Governance/D06/D07](../planning/governance.md) bleibt unverändert maßgeblich.

## Explizite Konfiguration und Least Privilege

Ein neuer absoluter privater Root außerhalb Repository, Job- und Contentroot:

```python
from src.evaluation_store.store import EvaluationStore

EvaluationStore.initialize(explicit_new_root)
# Späteres Öffnen legt weder Root noch Schema an:
store = EvaluationStore(explicit_existing_root)
```

Linux/POSIX, privater Root 0700, DB/Lock 0600, keine Symlinks/Hardlinks. Normales
Öffnen prüft Schemaidentität, DDL, SQLiteintegrität und komplette Revisionskette.
Unbekannte Schemas bleiben gesperrt. Keine automatische Migration oder Anbindung
an C22-/Contentbackup. SQLite übernimmt nach Prozessabbruch seine eigene
DELETE-Journal-Recovery unter exklusivem Reviewlock; keine eigene Replaylogik.

Privates `ReviewSettings`-JSON benötigt explizit `schema_version: 1`, `root`,
vorhandene `content`-Readkonfiguration und `grants`. Der Loader verlangt absolute
Datei, sichere Vorfahren und private reguläre Datei. Keine Credentials in diesem
Dokument oder versionierten Beispiel. APIstart über den bestehenden Einstieg:

```sh
python -m scripts.job_control api --config /private/jobs-config.json \
  --review-config /private/review-config.json
```

`--content-config` bleibt optional für die bisherigen Contentrouten. Review hat
seine ausdrücklich gebundene Contentkonfiguration. Kein zweiter Server oder Login.
`writes_enabled=false`, `real_reviews_enabled=false`, `grants=[]` sind Defaults.
Der Betreiber muss jeden Schreibpfad bewusst mit konkreten Subjects, Dataset-ID
und vollständiger Source-ID-Auswahl konfigurieren. Eine Realfreigabe erfordert
zusätzlich `real_reviews_enabled=true` und `owner_authorization_reference` sowie
die separaten D07-/Source-/Reviewerfreigaben. Die Konfiguration ist ein bewusst
privilegierter Betreibervertrag, kein aus dem JSON beweisbarer Freigabeakt.
Dieses Paket aktiviert keine realen Rechte und trifft keine echte Entscheidung.

Jeder `ReviewGrant` hat `schema_version`, `subject`, `dataset_id`, `source_ids`,
`permissions`. Genau ein Grant je Subject/Dataset; keine Wildcards. Immer zusätzlich
aktuelle Contentownership oder read-Grant **und** Coursezugriff auf alle Sources.

| Recht | Erlaubte Aktion; weitere Bedingung |
| --- | --- |
| `read` | Dataset lesen; Task nur als Assignee oder mit `manage` |
| `manage` | Dataset/Task anlegen, pending/clarification-Task zuweisen |
| `annotate` | Eigene zugewiesene Entwürfe bearbeiten |
| `confirm` | Eigene zugewiesene fachliche Entscheidung mit Beleg |
| `pool` | Separat vollständigen Originalpool einer Query bestätigen |
| `export` | Geprüfte Goldsnapshots erzeugen; ursprünglicher Datasetactor |
| `report` | Vorhandenen A-Evaluator auf expliziten Ergebnissen ausführen/referenzieren |
| `accept` | Manuelle, gebundene Abnahmeentscheidung speichern |

Alle weiteren Rechte setzen `read` voraus. Zuweisung ersetzt kein Recht. Allgemeine
viewer/operator-Rollen und normale Content-read-Grants erteilen keines dieser
Reviewrechte. Auch ein Operator darf fremde Aufgaben nicht ohne Assignment
annotieren/bestätigen. Ein ausdrücklich beauftragter Viewer kann dagegen Reviewer
sein. Das Backend übernimmt Reviewer/Approver ausschließlich vom authentifizierten
Principal; dessen Identity-Unterklasse samt Tokendigest wird niemals gespeichert.
HTTP kann keine Reviewpolicy ändern. Reale Reviewer-/Approverdelegation bedarf der
Betreiberentscheidung; es gibt keinen globalen Administrator.

## Persistenz, Revisionen und Konsistenz

`evaluation.sqlite3`, application_id `0x45564131`, user_version 1. Die konkreten
DDLstrings stehen in `src/evaluation_store/store.py::DDL`. Zwei Tabellen bilden
die Entitäten ab: append-only `events(seq,digest,body)` und transaktionale
`heads(entity,revision,value)`. Entitypfade sind strikt datasetgebunden:
`dataset`, `task/<id>`, `pool/<query>`, `export/<id>`, `evaluate/<id>`, `accept/<id>`.
Task enthält Assignment, Annotation und Entscheidung; jede Änderung ist eine neue
Revision. Originale/komplette ParsedDocuments verbleiben im ContentStore.

Jedes Event bindet Schema, Entity, Vorgängerevent, Vorgängerrevision, Actor,
UTCserverzeit, Grund, Idempotency-Key, Intentdigest, Dataset-/Quellen-/Versionsbindung
und neuen Wert. Kanonisches JSON/SHA256 verwendet vorhandene Contenthilfen. Beim
Öffnen und jeder Transaktion werden Kette, Modelle und exakte Heads geprüft.
Die Kette ist keine Authentizitätsgarantie gegen einen Angreifer mit gleicher UID.
Es gibt keine API für Löschen, Auditumschreibung oder automatische Entsperrung.

Mutationen verlangen `expected_revision` (null bei neuer Entity),
`idempotency_key`, `reason`, `schema_version:1`. CAS erfolgt im gleichen Commit.
Identischer Actor/Entity/Key/Intent liefert denselben Beleg; anderer Intent ist
409. Auch `expected_revision` gehört zum Intent. Keys gelten über alle Aktionen
einer Entity: für Create, Draft und Decision verschiedene Keys verwenden.
Exports/Reports/Abnahmen sind unveränderliche, explizit neue Identitäten.

Taskzustände: pending → in_review → confirmed/rejected/needs_clarification.
Neue Bearbeitung nach Klärung ist eine Revision. Terminale Reviews benötigen
`correction:true`, erwarteten Head und Grund; dann erneut Draft/Confirm. Keine
Umhängung von Source-/Versions-/Regionankern. Andere Quelle verlangt neuen Task.
Die vollständige Taskidentität ist das Paar Dataset-ID/Task-ID.
Workflowbestätigung und Parsingqualität sind unabhängig: Ein bestätigter Review
kann einen Parserfehler oder einen nicht entscheidbaren Befund dokumentieren.

Lockreihenfolge: kurzes Reviewbinding lesen und schließen → Content Maintenance SH
→ Content DB SH → Review EX/SQLtransaktion → Antwortserialisierung/Commit → Freigabe.
Taskhead/Assignment/Binding werden unter der finalen Transaktion erneut gelesen.
Bestehende `_load`-/Projektionsgrenzen validieren Raw-/Receipt-/Plan-/Parser-/Payload-
und SQLblockbindung im selben Contentsnapshot. Interne Aufrufe verwenden dessen
bereits gehaltene DBverbindung, keine rückwärts verschachtelten Locks. Ein
Contentwriter wird während der Aktion Busy; Widerruf vor Guarderwerb sperrt sie.
Keine behauptete Schreibatomizität über zwei Datenbanken. Antworten werden innerhalb
der Guards als begrenzte Bytes serialisiert; spätere Zustellung ist kein dauernder
Rechtebeleg. Neue Aktionen prüfen Rechte erneut.

## Task, Originalansicht und Gold

`TaskSpec`/`Region` binden vorhandene Source/SV/PV/Block-/Parser-IDs, Payload- und
Projektionshash, vollen Text-SHA, Raw-SHA, vorhandenen ContentLocator, exaktes
Unicode-Codepointintervall und gewählte Zeichen. Keine Normalisierung von Emoji,
Combiningzeichen, Operatoren oder CRLF. HTML/PDF werden nicht neu gerendert/geparst.
Die Regionansicht ist ausdrücklich eine **Parsed-Codepointauswahl**. Die Rawroute
liefert unveränderte geprüfte Originalbytes als Download; die Regionansicht benennt
zusätzlich die vorhandene Contentattachmentroute. HTML niemals aktiv ausführen.
Ein PDFdownload ist kein neuer sicherer PDFviewer.

Annotation ist entweder `independent_original` oder `assisted`. Der unabhängige
Modus benötigt kein Ranking. Ein jemals unterstützter Task bleibt markiert und
kann sich nicht durch nachträgliche Umbenennung selbst bestätigen. Dafür ist ein
neuer ausdrücklich unabhängig bearbeiteter Task nötig. Das System erzwingt Belege,
aber kann die Wahrhaftigkeit einer menschlichen Beobachtung nicht aus Bytes beweisen.

Retrieval verwendet direkt A `IndependentReview`/`ContentRelevanceJudgment` mit
Grad 0–3, tatsächlichem Subject, Serverdatum und Beleg. Grad 0 ist bestätigtes
negatives Gold. Parsing verwendet unabhängig erwarteten Vollblocktext, Qualität
correct/partial/incorrect/undetermined, Fehlerkategorien und Kommentar. Nur
Vollblockgold passt zum bestehenden C23-Vergleich. Teilregionen können Retrievalgold
sein; Parsingvollblockgold darf nicht aus einem Teilfenster konstruiert werden.

`unanchored_finding=true` ist ausschließlich bei Parsing erlaubt: Die geprüfte
Region ist dann **Kontext**, die unabhängige Beobachtung in `expected_content`
beschreibt z. B. verlorenen Originaltext ohne gültigen Parsedanker. Solche Befunde
und undetermined-Parsingurteile bleiben in Task/Audit, werden aber weder als
Retrievalgold noch als entscheidbares C23-Gold exportiert. Für vollständig fehlende
Dokumente ohne jeden geprüften Kontextblock ist erst ein verifizierbarer
Originalbefundvertrag erforderlich; keine erfundenen Block-IDs oder Locatoren.
Unbekannte Transcriptzeiten bleiben null; ein vorhandener timed-SRT-Vertrag wird
nicht durch selbst gewählte unknown-Locatoren umgangen.

Parsingtasks benennen ausdrücklich `corpus_entry_id` des vorgesehenen bestehenden
C23-Korpusmanifests. Diese ID wird erhalten, niemals aus einer Task-ID erfunden.
Der Reviewstore prüft Source-/SV-/Raw-/PVbindung; die Zuordnung zum externen
CorpusManifest und dessen Freigabe prüft anschließend weiterhin das vorhandene
C23-Gate. Ein schema-validierter Goldexport ersetzt diesen Korpuscheck nicht.

Poolbestätigung ist eine eigene berechtigte Aktion mit Beleg und Coveragebegründung:
Alle aktuellen Querytasks müssen bestätigt und genau benannt sein; ihre Anker
müssen alle projizierten Originalblöcke abdecken. Diese technische Mindestprüfung
ersetzt nicht die menschliche vollständige Relevanzprüfung dieser Blöcke. Pending,
Rejected und unjudged werden nicht automatisch irrelevant. Neue Taskrevisionen
invalidieren die Poolbindung. Einzelbestätigung setzt nie `pool_complete`.

## Routen und Grenzen

Alle Routen beginnen mit `/v1/evaluation`. Bearerprüfung erfolgt im bestehenden
Gateway vor Dispatch. Bodies sind bestehende streng versionierte Pydantic-DTOs
aus `src/evaluation_store/models.py`; zusätzliche Actor-/Rollenfelder sind verboten.
`D` bezeichnet eine Dataset-ID, `T` eine Task-ID, `S` eine neue Snapshot-ID.

| Methode / Route | Body oder Ergebnis |
| --- | --- |
| GET `/capabilities` | Opt-in-/Schreibstatus; keine privaten Counts |
| POST `/datasets/D` | `CreateDataset`: Auswahl vorhandener PVs, Queries, Retrievalkonfiguration |
| GET `/datasets/D/tasks?offset=0` | Nur sichtbare Aufgaben, feste zehn je Seite, next_offset |
| POST `/datasets/D/tasks` | `CreateTask` mit überprüftem Anker und Assignment |
| GET `/datasets/D/tasks/T` | Taskhead samt Annotation/Review |
| GET `/datasets/D/tasks/T/region` | Parsedregion, Locator und Contentattachmentroute |
| GET `/datasets/D/tasks/T/raw` | Geprüfte unveränderte Originalbytes als Anhang |
| POST `/datasets/D/tasks/T/assign` | `Assignment`, nur pending/clarification |
| POST `/datasets/D/tasks/T/draft` | `Draft`, eigene Annotation; ggf. explizite Korrektur |
| POST `/datasets/D/tasks/T/decision` | `Decision`, bestätigter/unbestätigter fachlicher Befund |
| GET `/datasets/D/tasks/T/revisions?offset=0` | Zehn Auditrevisionen je Seite |
| POST `/datasets/D/pool` | `PoolConfirmation`, Query/Taskheads/Coverage/Beleg |
| POST / GET `/datasets/D/exports/S` | `Mutation` / vorhandener Goldsnapshot |
| POST / GET `/datasets/D/reports/S` | `EvaluationRequest` / A-Bericht mit current-Flag |
| POST / GET `/datasets/D/acceptances/S` | `Acceptance` / manuelle Entscheidung mit current-Flag |

POST akzeptiert keine Queryparameter, GET keinen Body. Keine frei wählbaren
Dateipfade/URLs. Request höchstens 32 KiB, Target 2048 Zeichen, JSONantwort/Rawroute
höchstens 2 MiB. Große Originale verwenden den vorhandenen begrenzten Contentdownload.
Maximal 16 PVs/Queries, 64 Tasks/Dataset, zehn Seiteneinträge, Offset 0–1000,
2000 Codepoints/Beobachtung, 1000 Events/Store, 64 MiB DB, Export 1 MiB kumulierte
Raw/Payload/Projektionsbytes und 2000 Blöcke. Vorhandene Contentlimits gelten
zusätzlich. flock nonblocking, SQLite timeout 0; keine Hintergrundretries/GC.

HTTP 401 unauthenticated, 404 unbekannt/fremd/nicht berechtigt, 409 CAS/Idempotenz/
Bindingkonflikt, 422 ungültiger DTO/Route, 503 busy/unavailable/Integritätsfehler.
Keine SQL-, Dateipfad-, Credential- oder Exceptiontexte im Fehler. Bestehender
HTTPhandler setzt No-Store/Nosniff, Body-/Transportlimits und redigiertes Logging.
Tasklisten enthalten keine globalen Counts. Offsetseiten sind aktuelle autorisierte
Ansichten; bei parallelen Änderungen erneut ab Seite null lesen, kein behaupteter
revisionsstabiler Cursor. Einzelaktionen bleiben CASgesichert.

## Export, Evaluation und manuelle Abnahme

Der Goldexport materialisiert A `ContentRetrievalEvaluationSet` und separat C23
`GoldDataset` ausschließlich aus aktuellen bestätigten Urteilen unter Live-ACL.
Notwendige A `VersionEvidence`-Originalbytes werden nur für den expliziten privaten
Export zusammengesetzt, nie vollständig in der ReviewDB gespeichert. Der Snapshot
speichert Content-/Review-/Poolstand, Digests und Actor. Wiederholtes Lesen desselben
gültigen Stands ergibt identischen Export. Source-/ACLrevision oder Reviewänderung
macht alte Exports stale. Kein Zusammenführen verschiedener Versionen.

Bewusste v1-Grenze: A `pool_scope` bindet auch den Principal. Exports und Evaluation
verlangen deshalb exakt den ursprünglichen Datasetactor einschließlich Course-/
Rollenstand; kein stilles Umschreiben von A-Scopehashes für andere Leser. Andere
berechtigte Reviewer dürfen Aufgaben bearbeiten; Report-/Abnahmereads werden für
deren aktuellen Dataset-/Sourcezugriff separat geprüft.

POST reports führt **nur** den vorhandenen reinen A-Evaluator auf explizit gelieferten
`RetrievalResults` gegen den aktuellen Export aus. Kein Indexbuild, Backendaufruf
oder neue Metrik. Bericht enthält dessen unveränderte `live_authorization=not_checked`
und `real_acceptance=blocked`; der Gatewayguard autorisiert die aktuelle Aktion,
erfindet keine vollständige Sicherheitsabnahme des Retrievalbackends. Gelieferte
SecurityEvidence bleibt verantwortete, hashgebundene Evidenz des Berichtserstellers,
keine automatisch beglaubigte Testausführung. Berichte binden Exportrevision und
aktuellen Quellen-/Reviewstand. Alte Berichte bleiben als stale gekennzeichnet lesbar,
soweit die Quellen weiter zugänglich sind; sie dürfen keine neue Abnahme tragen.

Manuelle Abnahmen accepted/accepted_with_limitations/rejected/not_evaluable binden
Reportdigest/-revision, Dataset-/Korpus-/Version-/Reviewstand, Limitierungen,
Approver, UTCzeit und Begründung. Ein A-release_blocker oder keine evaluierbaren
Queries sperrt positive Abnahme. `accepted` benötigt vollständige bestandene
Sicherheitsbelege; accepted_with_limitations verlangt benannte Grenzen. Ein
bestätigter Leak kann nicht mit einer Limitierung übergangen werden. Ein neuer
Report ersetzt keine alte Entscheidung; neue Snapshot-ID und bewusste Aktion nötig.
Eine gespeicherte fehlgeschlagene Sicherheitsprüfung desselben unveränderlichen
Datasets bleibt auch bei späteren Berichten ohne diesen Befund eine Freigabesperre.
Es gibt keinen API-Override oder automatische Bereinigung dieser Evidenz. Spätere
Remediation benötigt explizit geprüfte neue Dataset-/Konfigurationsbindung.
Keine Entscheidung löst Deployment, Quellenpublikation oder automatische Freigabe aus.

## Implementierungsnachweis und offene Abnahme

Die tatsächlichen gezielten Laufzahlen und synthetischen APIbeispiele werden im
[B1-Validierungsbericht](../cs50/evaluation/human_review_backend_validation.md)
festgehalten. Kein echter Reviewer wurde im Namen des Auftraggebers eingesetzt.
Realpilot, unabhängiges Realgold, UIintegration, Host-/Last-/Backup-/Restoreabnahme
und Schutz gegen privilegierte Dateisystemangreifer bleiben separat offen.
