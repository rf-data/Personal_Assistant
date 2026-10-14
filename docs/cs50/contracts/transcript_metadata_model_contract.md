# Gemeinsamer Transcript-Metadatenvertrag der Knowledge-Modelle

Stand: 14. Oktober 2026. Eigenständige Basis origin/master `fa467e6`, nach
Integration des Lazy-Import-PRs #24. Arbeit in einem frischen separaten Worktree.

Als Referenz wurde der frühere #10-Branch mit den hineingemergten #12-Modellen
geprüft. Wiederverwendet wird der kleine gemeinsame Metadaten-/Validatorvertrag,
nicht dessen Pipelineänderungen. Zusätzliche alte Mindestlängen-/Regexregeln
für bislang uneingeschränkte Metadatenstrings werden bewusst nicht übernommen:
Sie wären eine neue, hier nicht erforderliche Kompatibilitätsverschärfung.

## Umfang und Modellstruktur

Nur `src/model_knowledge/data_knowledge.py` wird produktiv geändert.
`TranscriptKnowledgeMetadata` ist eine kleine gemeinsame Pydantic-Basis für
TranscriptKnowledgeDocument, ConsolidatedKnowledgeDocument und
LectureKnowledgeDocument. Alle drei besitzen damit dieselben optionalen Felder:

| Feld | Verhalten |
|---|---|
| language | Explizite Sprache oder None; keine Umrechnung von Sprachcodes. |
| transcript_provenance | Vollständiges bestehendes TranscriptProvenance oder None. |
| transcript_url | Explizite Herkunfts-URL oder None; keine Ableitung aus anderen Feldern. |
| media_id | Explizite Medienidentität oder None; keine Extraktion aus einer URL. |
| course_id / lecture_id | Geprüfte Zuordnung oder None; keine Dateinamenheuristiken. |

`source_id` bleibt ausdrücklich im jeweiligen konkreten Dokumentmodell:
Extraction erlaubt weiterhin fehlende/None-Identität, lehnt aber explizite leere,
rein weiße und nicht-string IDs mit den bisherigen Field-Regeln ab.
Consolidated- und Lecture-Dokumente verlangen weiterhin einen String. Deren
bisheriger schlichter Stringvertrag wird nicht verschärft; bestehende Consumer-
Prüfungen auf eine belastbare nicht leere Quellenidentität bleiben unverändert.
Eine URL, Provenienz oder Kurszuordnung ersetzt keine source_id.

`transcript_metadata()` liefert auf allen drei Modellen dieselben vier
ergänzenden Schlüssel: language, transcript_provenance, course_id, lecture_id.
Die Identitätsfelder source_id, transcript_url und media_id bleiben separat
explizit verfügbar. Damit können zukünftige Konstruktoren geprüfte Identitäten
ausdrücklich und die ergänzenden Metadaten per `**document.transcript_metadata()`
übergeben, ohne doppelte Keywords oder eine vermischte Identitätsableitung.
Diese Trennung entspricht dem vorhandenen Legacy-Testvertrag: Ein Dokument mit
source_id='legacy' hat dennoch vollständig unbekannte ergänzende Metadaten.

Fachliche Zusatzfelder wie Chunks, Evidence, Statements, Formeln, Topics,
VisualCandidates, Entities und Statistiken bleiben unverändert. Source-ID-
Vertrag, Modell-Dumps und JSON-Roundtrips werden separat regressionsgeprüft.

## Konsistenzprüfung ohne Anreicherung

Ein geerbter after-Validator vergleicht ausschließlich vorhandene, vergleichbare
Paare: language mit provenance.language, transcript_url mit
provenance.source_url und media_id mit provenance.media_id. Beide Werte müssen
ungleich None sein; nur dann führt ein Unterschied zu ValidationError mit
`<field> contradicts transcript_provenance`.

Die existierenden Produzenten wurden geprüft: Der offizielle Importer setzt
source_url auf die Original-TXT-/SRT-/VTT-URL; der Legacy-Transkriptpfad setzt
sie auf context.url. Der allgemeine Knowledge-Runner verwendet genau diese
provenance.source_url als transcript_url. Beim Legacy-/Whisper-Fall kann das
also eine Medien-URL sein. Es wird nicht eigenmächtig eine andere Bedeutung
oder eine direkte Download-URL erzwungen. source_file ist ein lokaler Pfad und
wird ausdrücklich nicht mit transcript_url verglichen.

Es gibt keine URL-Normalisierung, Redirect-Auflösung, Sprachalias-Erkennung oder
Ableitung fehlender IDs. Fehlende Gegenwerte bleiben unbekannt. Auch wenn die
Provenienz Sprache, URL oder Media-ID kennt, bleiben entsprechende nicht
deklarierte Dokumentfelder None. TranscriptProvenance und die Herkunftsstrategie
bleiben erhalten; die Quellenmodalität KnowledgeEvidence.source ändert sich nicht.

Die Prüfung greift bei regulärer Konstruktion, model_validate und JSON-Laden.
Die bestehenden Pydantic-Verträge für ungeprüftes model_copy(update=...) und
nachträgliche Feldzuweisungen werden nicht erweitert; Consumer müssen wie
bisher regulär revalidieren. Dieser PR führt keine Migration durch.

## Rückwärtskompatibilität

Alle ergänzenden Metadaten sind optional mit Default None. Bei Extraction sind
die bereits nullable transcript_url/media_id jetzt ebenfalls ohne explizite
Angabe zulässig. Source-ID-Defaults und -Pflichtfelder bleiben je Modell erhalten.
Alte JSONs ohne neue Metadaten bleiben lesbar; gültige deklarierte Werte gehen
nicht verloren. Widersprüchliche explizite Werte werden beim Laden nun bewusst
abgewiesen. Es gibt keine stillen Korrekturen.

Tests umfassen alle fünf TranscriptSource-Strategien auf allen drei Modellen,
konsistente vollständige Metadaten, fehlende Werte auf beiden Seiten,
Nicht-Anreicherung aus Provenienz, unveränderte ID-Regeln sowie model_dump-
und JSON-Roundtrips. Die neun bestehenden Konfliktfälle werden jeweils sowohl
über normale Validierung als auch über JSON-Laden geprüft.

## Getrennte Übergabe an PR #26

An Extraction-Runner und semantischer Consolidation wurde nichts geändert.
Zwei bestehende Integrationstests müssen deshalb weiterhin fehlschlagen:

1. `test_real_extraction_and_deterministic_and_semantic_contracts`: Der allgemeine
   Extraction-Runner übergibt language, transcript_provenance und course_id noch
   nicht; er liefert weiterhin None. Nach dessen Korrektur sind die semantischen
   Konstruktoren des nicht leeren Ergebniszweigs zu prüfen.
2. `test_semantic_no_statements_branch_preserves_explicit_assignment_and_media`:
   Der semantische Leerzweig gibt die nun unterstützten Metadaten sowie media_id
   weiterhin nicht an LectureKnowledgeDocument weiter.

Konkreter Folge-PR: ausschließlich die geprüften Transcript-Metadaten im
allgemeinen Runner weiterreichen und beide semantischen Ergebnis-Konstruktoren
ergänzen. source_id/transcript_url/media_id ausdrücklich aus dem geprüften
Eingang erhalten; die vier ergänzenden Felder über transcript_metadata(). Eine
lecture_id nur aus einem tatsächlich geprüften Kontext übernehmen. Keine ID aus
Dateinamen oder URLs neu herleiten. Beide Integrationstests unverändert grün
machen, ohne LLM-Aufrufe oder neue Modelländerungen. Die deterministische
Consolidation reicht die betreffenden Felder bereits weiter und bleibt hier
unverändert.

## Reproduktion

Reguläre bestehende uv-Worker-Umgebung, Python 3.12.12 / pytest 9.1.1 /
Pydantic 2.13.4, --offline --no-sync. UV_PROJECT_ENVIRONMENT zeigt auf deren
installierte .venv; Code und Fixtures liegen im frischen Worktree. Keine
Dependency- oder SDK-Installation.

```bash
uv run --offline --no-sync python -m pytest tests/test_knowledge_transcript_provenance.py -q
uv run --offline --no-sync python -m pytest \
  tests/test_knowledge_source_id.py tests/test_cs50_knowledge_input.py \
  tests/test_cs50_knowledge_pilot.py tests/test_cs50_precise_evidence.py \
  tests/test_consolidation_math_import.py tests/test_lazy_marvin_import.py \
  tests/test_cs50_quality.py -q
uv run --offline --no-sync python -m pytest tests -q --tb=short
```

Keine künstlichen Skips oder geänderten Pipeline-Assertions verbergen die
Folge-PR-Arbeit. Keine Änderungen an Discovery, Selection, Executor, Importer,
Runner, Prompts, Evidence-Verarbeitung oder Consolidation-Funktionen. Keine
API-/LLM-/Marvin-/Whisper-Aufrufe, Downloads oder produktiven Datenänderungen.

## Tatsächlich ausgeführte Ergebnisse

| Lauf | Ergebnis | Laufzeit |
|---|---|---|
| Unveränderte Provenienztests auf master | 5 passed, 14 failed | 2,06 s |
| Erweiterter Provenienz-/Modelltestlauf | 39 passed, 2 failed | 1,12 s |
| Geforderte Regressionen plus Lazy-Import und Quality | 89 passed, 2 skipped | 110,32 s |
| Vollständige Suite, 387 Fälle | 374 passed, 9 failed, 0 errors, 4 skipped | 349,90 s |

Die beiden Provenienzfehler sind genau die oben benannten unveränderten
Weitergabetests für PR #26. Die übrigen Fehler sind sechs bekannte TXT-Import-
Fälle (None-Zeitstempel gegenüber float-Segmentmodell) und ein optionaler
OpenAI-SDK-Smoke-Test (SDK fehlt). Keine dieser Gruppen wurde geändert. Die
vier bereits bestehenden Skips betreffen optionale Originalpilot-/installierte
Marvin-Integrationseingänge; keine neuen Skip- oder Xfail-Markierungen wurden
eingeführt.

Ruff-Lint beider Python-Dateien, Formatprüfung der Testdatei und
git diff --check bestanden. Das große bestehende Datenmodellmodul wurde
außerhalb seines Importblocks und der betroffenen Modellabschnitte nicht
neu formatiert. Alle Ergebnisse stammen aus der tatsächlich installierten
uv-Umgebung, ohne API-Freigabe oder zusätzliche Downloads.
