# C24-05-A: Retrievalevaluation und unabhängiger Goldvertrag

18.10.2026 · Endgültige Basis `origin/master` `87ea32f5e9e3f4826f6bbd84ed0d28073fc3fb87`.
Branch `feat/c24-05a-retrieval-evaluation`. Beginn auf `30bc6d3` nach #83–#85;
#86/C24-04 wurde während der Arbeit gemergt und vor PR-Erstellung integriert.
Technische Vorbereitung,
keine fachliche Freigabe von C24-05-B oder [C23-06](c23_real_material_evaluation.md).

## Bestandsaufnahme und Ablauf

| Vorhandener Vertrag | Wiederverwendung |
| --- | --- |
| ContentStore | Source, SourceVersion, ParsedDocumentVersion, ParserConfiguration, ContentBlock, ContentLocator, ArtifactReference, Principal und kanonische Hashfunktionen |
| C24-02 | IndexProjectionConfig/Result/Record, exakte Originalfenster mit maximal 2.000 Codepoints, Record-/Parser-/Payload-/Projektionshashes |
| C24-03 | Tatsächliche SearchResultPage/SearchHit mit RecordAnchor, TextWindow, LocatorDTO, Generation und Scores; keine zweite Trefferklasse |
| Transcript-Evaluation | Bestehende Recall-/RR-Arithmetik zentralisiert; die strengeren realen lokalen Transcriptreviewgates in `reviewed_metrics` unverändert |
| `retrieval_metrics.py` | Unbenutzte Stümpfe durch gemeinsame `recall_and_rr` und `graded_ranking` ersetzt; keine Formeln je Backend |
| C23-06 | Herkunfts-/Reviewprinzip und blockierte Realabnahme übernommen. Parsinggold wird nicht als Retrievalrelevanz umgedeutet |

[Modelle](../../../src/model_evaluation/content_retrieval.py),
[Evaluator](../../../src/tools_evaluation/evaluate_retrieval.py),
[CLI](../../../scripts/content_retrieval_evaluation.py): explizite versionierte
Originalbelege + unabhängige Regionen/Reviewpool + vorhandener Ergebnis-DTO →
Hash-/Identitätsprüfung → Regionszuordnung → Query-/Macrometriken → Reportdigest.
Der Runner öffnet weder ContentStore noch Suchinstanz und liest keine Secrets.
Keine Imports, Parser-, Embedding-, LLM- oder Netzwerkaufrufe.

## Eingabe- und Goldvertrag

`ContentRetrievalEvaluationSet` v1 verlangt eine explizite ganzzahlige
`schema_version=1`, Datasetversion, Herkunft `synthetic|real|unknown`, Reviewstatus,
Corpusvollständigkeit/-referenz, bestehende Projektionskonfiguration,
RetrievalConfiguration, Queries, VersionEvidence, Goldurteile und Reviewpools.
`unknown` erhält keine fachlichen Rankingwerte. Ein Dataset hat genau eine Herkunft;
reale und synthetische Metriken werden niemals gemischt.

Query bindet ID/Text und EvaluationScope mit bestehendem Principal, CourseIds und
erlaubten Source-/ParsedVersion-IDs. Actorcourse und Querycourse müssen passen.
Das ist eine **Offline-Scopeerklärung**, keine Authentifizierung oder Grantcapability.
Die aktuelle Suchschnittstelle muss weiterhin ihren C24-03-Guard halten.

VersionEvidence enthält die bestehenden vollständigen Source-/Versions-/Parser-/
Blockmodelle, IndexProjectionResult und ausdrücklich eingebettete Base64bytes mit
ArtifactReference. Exakte Closure: alle Rawmanifestartefakte einschließlich Bilder,
Payload und Originalprojektion. Erneut geprüft werden SHA-256/Größe, Source-/Version-/
Parser-IDs, Status, Konfiguration, vollständige Blocktexte/-reihenfolge, Original-
projektion, Locatoren und Records. Bestehende SRT-Cue-ID-Projektion identisch prüfen;
kein Reparse oder Interpolieren. Hashkonsistenz authentifiziert **keinen Menschen**
und beweist keine fachliche Parserkorrektheit oder historische Receiptgültigkeit.
Reale Eingaben müssen zuvor das vollständige vorhandene B-Gate durchlaufen haben.
Dieses Framework ersetzt weder B-Gate noch ContentStore-Publikation/ACLprüfung.

RetrievalConfiguration bindet Methode, Rankingversion, Backendfingerprint, Generation,
k und Adapter. `configuration_fingerprint` ist SHA-256 des kanonischen Objekts ohne
genau dieses Feld. Backendfingerprint/opaque Generation müssen vom bewusst gewählten
Snapshot stammen; offline wird ihre Bindung verglichen, keine Instanz authentifiziert.
QueryResults bindet Querytext-SHA-256 und Scopefingerprint; RetrievalResults bindet
das vollständige Datasetdigest. Der Projektionsfingerprint wird separat berichtet.

`ContentRelevanceJudgment` v1 bindet Query, stabile Goldziel-ID, Source, SourceVersion,
ParsedVersion, Block, vollständigen Originalregiontext, Unicode-Codepointintervall
`[start,end)`, Block-/Regions-/Raw-SHA-256, bestehenden geprüften ContentLocator und
ganzzahligen Grad 0–3. Höchstens 2.000 Codepoints pro Ziel; größere Regionen **vor dem
Review manuell** zerlegen. Chunkgrenzen definieren kein Gold.

IndependentReview: `pending_review|confirmed|rejected`, Methode, Reviewer, Beleg,
Datum. Bestätigung verlangt alle drei Belege und unabhängige Annotation.
`prediction_preannotation` darf niemals bestätigen. Real/unknown akzeptieren keine
synthetische Bestätigung; synthetische Datasets verlangen ausdrücklich
`synthetic_reference`. Mehrdeutige Quellen benötigen eine Notiz und bleiben offen.
Die Beispielmarker `synthetic-fixture-author` und dessen Datum sind **Testkonstanten**,
keine behaupteten realen Reviewer oder menschlichen Prüfungen. Positive und negative
Regionen sind handgeschriebene Konstanten, niemals aus Hits rückprojiziert.

ReviewPool bindet genau eine Query samt Actor/Course/Source-/Versionscope und
Projektionskonfiguration über `scope_sha256`, eine exakte eindeutige Liste aller
suchbaren Originalblöcke/-texthashes, Abdeckungsnotiz und unabhängige Bestätigung.
`pool_complete=True` erklärt: alle relevanten Ziele dieses begrenzten Querykorpus
sind erfasst. Boolean allein genügt nicht. Fehlender Pool, Pendinggold, unvollständige
Korpusabdeckung oder unbekannte Herkunft verhindern fachliche Werte. Rejectedgold
wird ausgeschlossen, macht darauf treffende ungeprüfte Hits aber nicht negativ.

## Zuordnung und Metriken

1. Originalbytes und vollständige technische Gold-/Hitbindung prüfen. Gleiche
   Source, SourceVersion, ParsedVersion, Block und Texthash im Queryscope verlangen.
2. Goldregion muss vollständig im Recordanker liegen. Excerpts sind höchstens
   512 Codepoints und ersetzen den vollständigen Anker nicht; beide gegen den
   Originalblock prüfen. Keine heuristische Token-/Textähnlichkeit.
3. Enthält ein Hit mehrere disjunkte Ziele, wähle genau eines nach kleinstem
   `(start,end,gold_target_id)`. Wiederholte Chunks wählen dasselbe Ziel, niemals
   ersatzweise ein anderes. Dieser konservative v1-Vertrag kann breite Chunks
   bestrafen, verhindert aber unbegrenzten Kredit.
4. Nur erster gültiger positiver Treffer erhält den Grad. Weitere Treffer Gain 0,
   Ränge unverändert. Bestätigte Goldregionen einschließlich negativer Ziele müssen
   pro Query/ParsedVersion/Block disjunkt sein; vorher teilen oder erneut als ein
   gemeinsames Originalziel reviewen.
5. Teildeckung eines bestätigten Ziels ist ein bekannter Deckungsfehler mit Gain 0.
   Vollständig enthaltenes Grad-0-Gold ist ausdrücklich irrelevant. Ohne bestätigte
   überdeckte/angeschnittene Region bleibt der Hit **unjudged** und verhindert
   fachliche Rankingwerte, selbst bei behaupteter Poolvollständigkeit.

| Querymetrik | Zähler / Nenner | Nullfall |
| --- | --- | --- |
| Precision@k | Neu kreditierte positive Ziele / **k**, auch bei kurzer vollständiger Liste | Unvollständiger Pool, unjudged Hits oder Integritätsfehler: `not_evaluable` |
| Recall@k | Verschiedene kreditierte positive Ziele / alle bestätigten positiven Poolziele | Keine positiven Ziele: `not_determinable`, Nenner 0 |
| RR@k | 1 / erster positiver Rang; ohne Treffer 0/1 | Ohne positives Poolziel: `not_determinable` |
| nDCG@k | DCG / IDCG desselben vollständigen bestätigten Pools | IDCG 0: `not_determinable` |

`DCG = sum((2**grade-1)/log2(rank+1))`; ideale Grade absteigend auf k begrenzen.
Nullgain-Ränge nicht komprimieren. Ein vollständiger leerer Ergebnissatz bei
positivem Pool ergibt alle vier Werte 0. Ohne positives Gold kann Precision bei
geprüften negativen Hits/leerem Resultat 0 sein; Recall/MRR/nDCG bleiben unbestimmbar.
Jede Metrik: Status, Zähler, Nenner, Wert, Nullgrund. Macro: Summe der **tatsächlich
evaluierbaren** Querywerte / deren Anzahl; ausgeschlossene Queries/Gründe ausweisen.
Keine fehlenden Werte als 0 zählen. Erste Seite mit weniger als k Hits und Cursor
ist unvollständig: keine Auswertung und kein automatischer weiterer Abruf.

## Locator, Provenienz und Sicherheit

Prüfung: Seite, Zeile, DOM, Zeit, Geometrie, Block-/Rawreferenz, Route, Text und
Codepointgrenze. LocatorDTO muss mit bestehender redigierter C23-04-Projektion
übereinstimmen. Externe Locatoren (`locators_in_structure`) ohne ausdrückliche
Hydrierungsbelege sind v1 `external_locators_not_checked` und verhindern fachliche
Werte; kein HTTPabruf. Pro Query Referenzprüfzahl, feste Fehlercodes und bekannte/
unbekannte/nicht anwendbare Zeiten/Koordinaten. Abwesende Seite/Zeile/DOM/Geometrie
bleibt unknown; not_applicable nur aus expliziter vorhandener Zeitkennzeichnung.
Keine erfundene PDFgeometrie oder TXTzeit. Counts zählen Referenzvorkommen, keine
Goldziele und keine fachliche Parserqualitätsquote. Reviewstatus separat berichten.

SecurityEvidence meldet zwölf Szenarien: unberechtigte Source, fehlender Course,
Revoke, Quarantäne, Tombstone, veraltete Generation, falscher Anker, fremde
Scorebeeinflussung, Cursor/Pagination, Existenz-/Text-/Locatorleak. Jeweils Status
passed/failed/not_checked, Grund und bei Ausführung Belegdigest. Fehlende Belege
werden als `no_executed_scenario_evidence` ergänzt. Dies sind externe Ausführungs-
belege, keine vom reinen Evaluator erneut ausgeführten Sicherheitstests; ein Hash
ist keine Signatur. `live_authorization=not_checked` bleibt explizit im Report.
Jeder bestätigte Leak, jeder fehlgeschlagene Sicherheitsfall und jeder erkannte
Integritätsfehler setzt release_blocker, unabhängig von Rankingwerten. Auch über k
hinaus gelieferte Hits werden technisch geprüft. Keine Sicherheitsgesamtquote.

## Backend, Reports und Verwendung

`c24_search_result_page_v1` verwendet die integrierten lexikalischen und
Vector-DTOs (C24-04-A weiterhin ausschließlich FakeEmbedder/Fake-Transport);
Methode/Ranking/Generation/Score-Sourcebindung müssen passen.
`synthetic_ranking_list_v1` ist ausschließlich synthetisch: derselbe vorhandene DTO
mit lexical/vector/hybrid als Metadaten durchläuft dieselbe Metrikimplementierung.
Kein weiterer Vectorbackend oder Hybridranking wird implementiert. Der integrierte
C24-04-VectorScoreComponent wird direkt im bestehenden Uniontyp verwendet;
Hybrid bleibt ausschließlich synthetisch. Keine Rohscorenormalisierung.

RetrievalEvaluationReport v1: typisierter Body + SHA-256 des kanonischen Bodys,
Dataset-/Resultsdigests, Ursprung/Review/Corpus, Konfiguration/Generation, Query-/
Macrometriken, technische Befunde, Sicherheit und Nullgründe. Query-IDs gehasht;
keine Querytexte, Subjects, Source-/Block-/Gold-IDs, Inhalte, Locatoren oder Uhrzeit.
Datasetversion und externe Securitygründe müssen bewusst nicht sensible Labels sein.
Reale Inputs enthalten volle Belege und bleiben **privat**; nur synthetische Beispiele
versionieren. Keine Signatur-/Anonymisierungsgarantie durch Hashing.

Grenzen v1: 32 MiB kanonische Dataset-/Resultsbytes insgesamt; je CLI-Input 32 MiB,
100 Queries, 128 Versionen, 2.000 Blöcke je Version, 2.000 Urteile, 504 Artefakte je
Version, 8 MiB Base64text je Artefakt (etwa 6 MiB Bytes), 100 Hits je Query, k 1–100.
Größeres Material bewusst in jeweils vollständig reviewte Auswertungen aufteilen;
kein stilles Sampling/Abschneiden. Kanonisches JSON begrenzt Tiefe auf 64; CLI
verweigert doppelte Schlüssel, nicht endliche Zahlen, ungültiges UTF-8 und Symlinks.

```sh
TASK_PYTHON=/home/robfra/0_Portfolio_Projekte/ai-job-search/.venv/bin/python
PYTHONPATH=/usr/lib/python3/dist-packages "$TASK_PYTHON" -m scripts.content_retrieval_evaluation \
  --dataset "$PWD/docs/cs50/evaluation/c24_05a/dataset.v1.json" \
  --results "$PWD/docs/cs50/evaluation/c24_05a/results.v1.json" \
  --output /tmp/c2405a-my-new-report
```

Absolute reguläre Inputdateien, neuer absoluter Outputdirectory. Kein Überschreiben
oder Löschen. Outputs privat 0600/Directory 0700: report.v1.json, summary.md, zuletzt
manifest.json mit SHA-256 der Dateibytes. Abbruch kann unvollständigen neuen Output
hinterlassen, ersetzt aber nichts. Exit 0: Reporterzeugung ohne Releaseblocker,
**keine fachliche Freigabe**; 1 Releaseblocker; 2 Input-/Outputfehler.

```python
from scripts.content_retrieval_evaluation import read_input
from src.model_evaluation.content_retrieval import (
    ContentRetrievalEvaluationSet, RetrievalResults, EvaluationConfig,
)
from src.tools_evaluation.evaluate_retrieval import evaluate_retrieval

dataset = read_input(explicit_dataset_path, ContentRetrievalEvaluationSet)
results = read_input(explicit_results_path, RetrievalResults)
report = evaluate_retrieval(dataset, results,
                           evaluation_config=EvaluationConfig(schema_version=1))
# JSONschema: ContentRetrievalEvaluationSet.model_json_schema(), ebenso Results/Report.
```

[Dataset](c24_05a/dataset.v1.json), [Rankingliste](c24_05a/results.v1.json),
[tatsächlicher CLI-Report](c24_05a/report.v1.json), [Kurzfassung](c24_05a/summary.md),
[Dateihashes](c24_05a/manifest.json): Grad-3-Ziel auf Rang 4, drei vorherige negative
Ziele. Handberechnung: Precision@4=1/4, Recall@4=1, RR=1/4,
DCG=7/log2(5), IDCG=7, nDCG=0.43067655807339306. Reine Fixturearithmetik,
**keine reale Suchqualitätsmessung**.

## C24-05-B: verbindliche Übergabe

1. Exakte freigegebene Originaldateien, Source-/Course-IDs und Evaluationsrechte
   benennen. Keine private Scanwurzel, kein automatisches Kopieren/Download.
   D06 `data/Harvard` gegen `data/lectures/Harvard` separat lösen; Originale/Receipts
   unverändert. [Governance](../../planning/governance.md) bleibt maßgeblich.
2. Vollständige unveränderte Raw-/Parsed-/Receipt-/Plan-/Parserrevisions-/Bildbundles
   mit damaliger Konfiguration und B-Gate bereitstellen. Revision nicht aus HEAD
   rekonstruieren. Konsistenten Snapshot/Scope vor und nach Sammlung prüfen.
3. Unabhängige Reviewer annotieren Regionen **am Original**, Grad 0–3, Mehrdeutigkeiten,
   Identität/Datum/prüfbare Belege. Vorhersagen/LLMvorschläge bleiben Pending.
4. Vollständigen begrenzten Pool pro Query bestätigen, Versionen/Raw-/Parsed-/Text-
   hashes und alle suchbaren Blöcke erfassen. Negative Ziele ausdrücklich annotieren;
   unjudged Treffer nachreviewen oder Evaluation offenlassen.
5. Gültige Actor-/Course-/Sourceberechtigungen, Grants/Status, feste Generation,
   Backend-/Projektions-/Retrievalkonfiguration, k und Original-Locatoren belegen.
6. Suchlauf und Sicherheitsszenarien pro Methode/Format ausdrücklich autorisieren,
   tatsächlich ausführen und Belege zuordnen. Offlinebelege erteilen keine Rechte.
7. Reale/synthetische Werte getrennt halten. Operator/Reviewer entscheiden begrenzt
   je Methode und Format. Fehlende Belege bleiben blockiert; keine automatische
   Freigabe von C23-06/C24-05-B oder D07.

Out of scope: Embeddings/Qdrant, Vector-/Hybridranking, Search-HTTP/UI/Jobs,
Optimierung, Originalmigration, automatische Goldbestätigung und Deployment.

## Tatsächliche Abnahme

Umgebung: Python 3.12.12, Pydantic 2.13.5, SQLite 3.50.4, vorhandenes System-Pytest
7.2.1 und Ruff 0.16.0. Keine Installation, kein Download. Tatsächliches Präfix:

```sh
PYTHONPATH=/usr/lib/python3/dist-packages PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
PYTHONDONTWRITEBYTECODE=1 \
/home/robfra/0_Portfolio_Projekte/ai-job-search/.venv/bin/python -m pytest
```

Gemeinsame Abnahme auf Ausgangsbasis `30bc6d3` mit diesem Präfix:

```sh
-q --disable-warnings -p no:cacheprovider \
 tests/test_content_retrieval_evaluation.py tests/test_content_retrieval_integration.py \
 tests/test_content_fts.py tests/test_content_index_projection.py \
 tests/test_cs50_material_evaluation.py tests/test_transcript_unknown_time.py \
 --basetemp=/tmp/c2405a-release
```

**217 passed / 0 failed / 0 skipped**, 180,28 s. Davon 65 neue Fälle (60 Modell-/
Metrik-/Review-/Anker-/CLI-/Sicherheitstests, fünf technische Integrationsfälle),
47 unveränderte FTS5-, 41 Projektions-, 38 C23-06- und 26 Unknown-Time-Fälle.
Pytest-7-AST-Warnungen unter Python 3.12 sind keine Skips. Kein Gesamtrepositorylauf.

Die damaligen fünf neuen Integrationsfälle verwenden echte temporäre Stores und FTS5-Dateien:
verifiziertes synthetisches B-Code-/SRT-Bundle → Publikation → C24-02-Projektion →
autorisierte Suche → handgeschriebenes Gold → Report → Wiederöffnung von Store/Index
mit gleichem Reportdigest und unverändertem Contentinventar. Zusätzlich echte
überlappende Recordfenster, Teildeckung, ein Hit über zwei Originalziele sowie
Source-/Courseverweigerung, Grantwiderruf und fehlende Existenz-/Text-/Locatorausgabe.
Das TXTbeispiel importiert eigene TXTbytes und prüft unbekannte Zeiten an einer
synthetischen Contentprojektion; es behauptet keinen existierenden TXT-B-Adapter.
PDFgeometrie wird ausschließlich aus vorhandenen Modellen geprüft, kein nativer
PDFparser in diesem Paket gestartet.

Die unveränderte FTS5-Suite prüft zusätzlich reale lokale Quarantäne/Tombstone-
Sperren, veraltete Generationen, falsche Anker/Metadaten, fremde Score-/Statistik-
beeinflussung und Cursor-/Paginationgrenzen. Der reine Ranking-Beispielreport hat
dennoch alle zwölf Sicherheitsszenarien korrekt `not_checked`: Testcoverage eines
Frameworks ist kein Ausführungsbeleg eines anderen Suchlaufs.

Separater Versuch mit demselben Präfix, `-q --disable-warnings -p no:cacheprovider
tests/test_cs50_retrieval_evaluation.py --basetemp=/tmp/c2405a-legacy`:
**0 ausgeführte Fälle, 1 Collectionfehler**, 0,30 s. Unveränderte Fixture importiert
`test_cs50_ingestion`, das fehlendes `qdrant_client` verlangt. Kein SDK installiert,
keine Verbindung versucht. Diese Legacydatei bleibt **not_checked**. Ihre gemeinsame
Recall-/MRR-Arithmetik und strengen Synthetic-/fehlenden Reviewgates sind zusätzlich
in den neuen SDKfreien Tests tatsächlich geprüft. Keine gesamte grüne Legacy-
Transcript-/SDKregression behauptet.

Entwicklungsläufe vor dieser Abnahme: `/tmp/c2405a-dev`: 53 passed/4 failed in
16,61 s (falsche Testannahmen: Codezeilenblock/Offset, exakt statt teilweise gedecktes
Intervall und zweiter Originaltextstart); `/tmp/c2405a-dev-second`: 62 passed/0 failed
in 13,13 s. Diese Zahlen nicht addieren. Die korrigierten Fälle und drei zusätzliche
Randfälle sind im 217er-Lauf enthalten. Ein erster manueller Smoke-
Aufruf fehlte am noch nicht angelegten privaten Parentdirectory; der anschließende
Aufruf war erfolgreich. Kein Fehler wurde als bekannte Produktbaseline umetikettiert.

Ruff Check und Format Check für alle acht geänderten/neuen Pythondateien und
`git diff --check` sind abschließende Pflichtprüfungen. Das tatsächlich per CLI
erzeugte Beispiel und eine Wiederholung haben Digest
`24730eb9b74f2641400e5cf3e8872417fa5584b603dd02e214cb476f12a0fee0`.
Versionierte Reports sind die unveränderten CLI-Ausgabebytes; manifest.json bindet
Report und Markdown, Dataset-/Resultsdigests binden die expliziten Inputs.

Nach Merge von #86 wurde der eigene Branch auf Master `87ea32f` aktualisiert.
Beide vorhandenen C24-04-Dokumentationsnachträge blieben erhalten. Der Evaluator
akzeptiert nun direkt den integrierten Vector-DTOvertrag; ein sechster neuer
Integrationsfall verwendet dessen vorhandenen FakeEmbedder/Fake-Transport und
Cosinescorekomponente ohne eigene Backendimplementierung. Hybrid bleibt synthetisch.
Mit demselben tatsächlichen Präfix:

```sh
-q --disable-warnings -p no:cacheprovider \
 tests/test_content_retrieval_evaluation.py tests/test_content_retrieval_integration.py \
 tests/test_content_fts.py tests/test_content_index_projection.py \
 tests/test_cs50_material_evaluation.py tests/test_transcript_unknown_time.py \
 tests/test_content_vectors.py --basetemp=/tmp/c2405a-current
```

**251 passed / 0 failed / 0 skipped**, 276,87 s auf endgültiger Basis:
66 neue Fälle, 47 FTS5-, 41 Projektions-, 38 C23-06-, 26 Unknown-Time- und
33 integrierte Vectorfälle. Dieser Lauf überlappt den 217er-Lauf, nicht addieren.
Kein anschließend geänderter Pythoncode. Ruff Check und Format Check sind für alle
acht Pythondateien erfolgreich; `git diff --check` ebenfalls. Das CLI-Beispiel wurde
auf dieser Basis erneut ausgeführt: gleicher Digest und exakt identische JSON-/
Markdown-/Manifestbytes. 53 lokale Dokumentationsverweise geprüft.

**Implemented:** Modelle, Review-/Poolvertrag, Matching, zentrale Metriken, Offline-
Runner/CLI, redigierter Report, synthetisches Beispiel, B-/FTS5-Roundtrip und
integrierter Vector-DTOadapter.
**Passed:** endgültiger 251er-Lauf und lokale Qualitäts-/Beispielprüfungen.
**Not checked:** SDKgebundene Legacydatei, reale Embedding-/Qdrant-/Hybridabnahme, produktiver
ACLzustand, menschliche Reviewauthentizität und native PDFextraktion.
**Blocked:** reale Retrievalqualität/C24-05-B und C23-06 ohne freigegebene vollständige
Originalbundles, unabhängiges Realgold und vollständigen Reviewpool; D06/D07 bleiben.
**Out of scope:** die oben aufgezählten Betriebs-/Ranking-/UIänderungen.

Nur eigene temporäre synthetische Test-/Beispielroots und erzeugte Caches werden
nach Prüfung entfernt; Logs bleiben außerhalb des Repositories. Der saubere eigene
Worktree bleibt für den offenen PR erhalten; andere Worktrees, Daten und Umgebungen
werden nicht bereinigt. Keine Branchlöschung oder automatische Zusammenführung.
