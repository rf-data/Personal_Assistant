# Transcript-Ingestion: Abschluss und Betriebsgrenzen

Stand 15.10.2026. Geprüfte Basis origin/master
4dcd3c781b089fcc3939d0a7301e60033a418700, inklusive #38 und #27–#37.
Implementierung in einem frischen isolierten Worktree. Keine Änderungen am lokalen
Master, produktiven Artefakten oder vorhandenen Transcript-/Knowledge-Modellen.

## PR-Abhängigkeiten

| PR | Umfang | Basis |
|---|---|---|
| [#39](https://github.com/rf-data/Personal_Assistant/pull/39) | Payload, Point-IDs, Collectionvertrag | master |
| [#40](https://github.com/rf-data/Personal_Assistant/pull/40) | Lokale Embeddings und Originalchunk-Mapping | #39 |
| [#41](https://github.com/rf-data/Personal_Assistant/pull/41) | Plan, Upsert und Resume | #40 |
| [#42](https://github.com/rf-data/Personal_Assistant/pull/42) | Gefiltertes Retrieval | #41 |
| [#43](https://github.com/rf-data/Personal_Assistant/pull/43) | Orchestrierung, CLI, Workerprofil | #42 |
| [#44](https://github.com/rf-data/Personal_Assistant/pull/44) | Vollständige Offline-E2E und Evaluation | #43 |
| Knowledge-Mapping/Abschluss | Read-only Knowledgevertrag, Schema-Readback, finale Dokumentation | #44 |

Die PRs sind bewusst gestapelt und nicht automatisch gemergt. Nach jedem Merge
müssen die Basisbranches der verbleibenden PRs kontrolliert angepasst werden.
GitHub-Publikation wurde jeweils gegen den getesteten lokalen Git-Baum geprüft.

## Technischer Nachweis

Echte vorhandene Discovery-/Selection-/Adapter-, Executor-, Importer-, Binder-,
Chunker-, Evidence-, Consolidation- und Pydantic-Funktionen; Fake-HTTP und eindeutig
markierte Fake-Embeddings; echtes persistiertes lokales Qdrant 1.19.1.
Keine Netzwerkverbindung im E2E-Demopfad. Die Collections werden ausschließlich
in neuen externen temporären Testordnern angelegt.

| Umfang | Abgeschlossene Quelltasks | Eindeutige Points | Prüfung |
|---|---:|---:|---|
| Eine synthetische Lecture | 2 | 2 | SRT/JSON/Bindings, Retrieval und Wiederöffnung |
| Zehn Python-Lectures | 20 | 20 | echter Teilupload-Abbruch, Resume und Filter |
| Sechs Kurse / 50 Lectures | 100 | 100 | alle Originalidentitäten, Abbruch/Resume, keine Duplikate |

Die synthetischen Quellen haben je zwei Originalchunks; dies ist keine Prognose
der Chunkzahl oder Speicherkosten echter 50 Vorlesungen. Abschnitt ai, Woche 0,
Cybersecurity media_id=None und nichtleere Cue-Teilgruppen sind nachgewiesen.
Lost acknowledgement tritt nach tatsächlichen ersten vier Schreibvorgängen auf;
Resume prüft vorhandene Payloads/Vektoren und vervollständigt nur fehlende Points.

## Testmatrix

| Modul | Abdeckung |
|---|---|
| test_cs50_index_contract.py | 13: IDs, JSON, originale Schlüssel, Collectionkonflikte, SDK-freier Import |
| test_cs50_embeddings.py | 8: Unicode/Tokenfenster, Vektoren, Originalzeiten, leere Cues, private Konfiguration |
| test_cs50_ingestion.py | 9: Artefakte/Hashes, echte Upserts, Unterbrechung, stale Sources, Schemafelder, Pfade |
| test_cs50_retrieval.py | 3: echte Filter, Originalabgleich, Konflikte |
| test_cs50_index_cli.py | 4: getrennte Freigaben, Datenschutz, ausführender lokaler CLI-Pfad |
| test_cs50_index_end_to_end.py | 3: vollständige Lecture / Pythonkurs / sechs Kurse |
| test_cs50_retrieval_evaluation.py | 3: source-grounded Vorlage, synthetische Kennzahlensperre, Rechenvertrag |
| test_cs50_knowledge_index_mapping.py | 5: bestehende Modelle, Originalevidence, Hash-/Quellen-/Qualitätskonflikte |
| test_cs50_knowledge_index_checkpoint.py | 1: tatsächlich abgeschlossener originaler Checkpoint und Extraktionskontext |

Gezielter E2E-Lauf: 3 passed in 773,74 s. Mapping: 5 passed in 46,24 s;
zusätzlicher Checkpointnachweis: 1 passed in 29,64 s. Frühere Einzelprüfungen:
Contracts 13/8,60 s, Contracts+Embeddings 20/16,51 s, Ingestion 6/65,86 s,
Readback trotz behauptetem Schreib-Erfolg 1/9,06 s, Retrieval 3/43,43 s,
CLI/Contracts/Embeddings 25/59,63 s. Läufe überschneiden sich; nicht addieren.
Der verstärkte Checkpointnachweis mit explizit nichtleeren Records bestand im
korrigierten isolierten Worker nochmals: 1 passed in 38,38 s.

Vollständige finale Regression: **510 passed, 6 bekannte TXT-Vertragsfehler,
5 skipped, 0 Setupfehler**; 521 gesammelte Tests, **3141,06 s (52:21)**.
Vergleichsbasis 461 passed / 6 failed / 5 skipped: genau 49 zusätzliche bestandene
Tests, keine neue Regression und keine neuen Xfails/Skips. Die sechs Fehler
liegen ausschließlich in test_official_transcript_import.py beim TXT-Pfad mit
unbekannten Zeitstempeln, einschließlich Codierung/Speicherung/importseitiger
Unabhängigkeit. Keine Assertions abgeschwächt und kein TXT-Code verändert.
Die [JUnit-basierte Modulbilanz](../archive/2026-10/transcript_index_regression_report.md)
führt alle Testmodule, sechs Fehler und fünf unveränderten Skip-IDs einzeln auf.

Der erste Gesamtversuch im unvollständigen PYTHONPATH-Aufbau endete mit
495 passed / 21 failed / 5 skipped in 3067,21 s. Neben den sechs TXT-Fehlern
scheiterten 15 isolierte CLI-/Import-/Pilotprüfungen wegen fehlender Abhängigkeiten
unter -I. Alle 15 bestehen im korrigierten Aufbau, ohne funktionale Codeänderung.

## Reproduzierbare Umgebung

Python 3.12.12, Pydantic 2.13.4, pytest 9.1.1, qdrant-client 1.19.1.
Der reguläre Worker blieb unverändert. Die nach Freigabe bereitgestellte isolierte
Qdrant-uv-Umgebung verwendet exakt die bisherigen Root-Lock-Versionen.
Gezielte Tests nutzten zunächst PYTHONPATH mit expliziten bestehenden Umgebungen.
Die Gesamtregression benötigt dagegen auch in Python -I verfügbare Abhängigkeiten:
zwei .pth-Verweise in einer neuen temporären venv verbinden die vorhandenen
SDK-/Worker-Site-Packages, ohne Pakete zu installieren oder vorhandene Umgebungen
zu verändern. Aufbau und isolierter Importnachweis sind im Worker-README erklärt.
Ein tatsächlicher uv run --offline --no-sync mit dieser Umgebung bestätigte
zusätzlich tiktoken-/Settings-/Qdrant-Imports unter Python -I.
Tatsächlicher finaler Testaufruf:

```bash
CS50_TEST_PROFILE=offline "$REGRESSION_WORKER/bin/python" \
  -m pytest tests -q --tb=short --junitxml=/tmp/cs50-index-complete-isolated.xml
```

Das deklarierte [Index-Workerprofil](../../../workers/cs50_index/README.md) hat
einen offline geprüften 43-Paket-Lock. Fresh offline sync scheitert noch am nicht
gecachten exakten grpcio-Wheel-URL. Keine vollständig neu installierte hermetische
Umgebung behauptet; Cachevorbereitung ist eine separate Betriebsanforderung.
Keine neuen optionalen SDK-Testfehler als Erfolg ausgeblendet.
Der erste Gesamtversuch mit ausschließlich PYTHONPATH zeigte fehlendes tiktoken
in isolierten Kindprozessen; auch pydantic_settings war dort nicht verfügbar.
Normale -I-Importprüfungen reproduzierten den Umgebungsfehler und bestätigten
anschließend beide Imports im korrigierten Aufbau. Keine Produktionsmodule
wurden dafür geändert.

## Embeddings und fachliche Evaluation

Bestehende Wahl multilingual-e5-base, 768 Dimensionen, Cosine, L2 und query:/passage:
mit immutable Revision. Keine verfügbaren Modellgewichte und keine echte Inferenz.
CPU-Geschwindigkeit, RAM, semantische Qualität und produktive Durchsatzwerte bleiben
unbekannt. Fake-Konfiguration ist versioniert und kann keine echten E5-Vektoren
vortäuschen. Modell-/Schemawechsel verlangen einen separat angelegten Indexstand.

Die [zehn Fragen](../evaluation/python0_retrieval_questions.v1.json) basieren auf
tatsächlich read-only revalidierten originalen Python-0-SRT-Cues und Hashes.
Sie sind vorgeschlagene Referenzfenster, noch kein manuell bewertetes Gold-Set.
Recall@k/MRR bleiben ohne reale Embeddings und mindestens zehn vollständige,
quellengeprüfte manuelle Relevanzurteile gesperrt. Toy-Arithmetiktests sind keine
gemessene Retrieval-Leistung. Kein LLM-Antwortgenerator implementiert.

## Voraussetzungen und nächster Schritt

1. Gestapelte PRs prüfen, in Abhängigkeitsreihenfolge integrieren und Basen prüfen.
2. Separat autorisiert den exakten Worker-Wheelcache und eine immutable lokale
   Modellrevision bereitstellen. Erst dann den echten lokalen CLI-Inferenz-/Suchpfad
   an einer bereits importierten Lecture prüfen; kein automatischer Modelldownload.
3. Zehn source-grounded Fragen manuell bewerten; Ranking, Quellenkorrektheit und
   fachlichen Nutzen getrennt protokollieren. CPU/RAM/Tokenfenster messen.
4. Echte Downloads erst mit explizitem Scope, --execute-download und geprüften
   Quellen-Lizenzbedingungen. Kein TXT/Audio/Video/Whisper-Fallback.
5. Produktiver Upload erst nach expliziter TLS/Auth-/Collection-/Scopefreigabe;
   --execute-upload ist getrennt vom Download. Namen müssen vorher nachweislich
   frei oder exakt kompatibel sein; es gab hier keine Produktions-DB-Abfrage.

Physische Keyword-Indizes benötigen einen separat geprüften Qdrant-Server >=1.16;
lokaler Clientmodus prüft die Filtersemantik, unterstützt diese Indizes aber nicht.
Multi-Writer-Betrieb ohne gemeinsam benutztes Status-Lock ist nicht abgedeckt.
Knowledge-Indexing ist ausschließlich ein read-only Mappingvertrag, kein Uploadpfad.
Sechs bekannte TXT-Zeitstempel-Vertragsfehler und allgemeine Legacy-Aufgaben bleiben
separat. Keine Änderungen an Prompts, Chunking, Evidence oder produktiven Daten.
