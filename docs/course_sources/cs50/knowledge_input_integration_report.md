# PR 5: Explizite CS50-Transcript→Knowledge-Eingabebindung

## Ergebnis und tatsächlich verwendete Quelle

Der lokale, bereits erfolgreich importierte Originalpilot CS50 Python, Woche `0`,
wurde anhand des unveränderten Adapterplans und seines `execution.v1.json` erneut
geprüft. Kein Download oder erneuter produktiver Import war erforderlich.
Das neue Eingabemanifest liegt in
`cs50_python_week0_knowledge_input.v1.json`; es dokumentiert diesen lokalen
Artefaktstand ausdrücklich, nicht einen universell übertragbaren Testdatensatz.

| Schritt | Ergebnis / tatsächlich verwendete Funktion |
| --- | --- |
| Plan und sechs Kursverträge | echter `CS50AdapterPlan.model_validate_json`; 50 getrennte SRT-/Lecture-Bindungen |
| Erfolgreiche Ausführungsbelege | `bind_cs50_knowledge_input`: genau die beiden geplanten Task-IDs, beide `done`, richtige Aktion/Version/Bindung |
| Inhaltsintegrität | echte SHA-256-Prüfung beider Dateien und des gespeicherten Import-Eingangshashes |
| Normalisiertes Transcript | echtes `validate_document`, `TranscriptDocument.model_validate_json` und erneuter `import_srt`-Inhaltsvergleich |
| Zeitbasierte Chunks | unverändertes `find_knowledge.build_transcript_chunks` mit `KnowledgeSettings` |
| Evidence-Bindung | echtes `attach_chunk_provenance` und `validate_extraction`, ohne LLM-Ergebnisse zu vertrauen |
| Ergebnisdokument | echter `TranscriptKnowledgeDocument`-Konstruktor mit expliziten Identitäten; JSON-Datei-Roundtrip |
| Consolidation | regulärer Import und tatsächliches `consolidate_knowledge`, einschließlich Formel-Normalisierung |
| Consolidation-JSON | echtes `ConsolidatedKnowledgeDocument` mit Datei-Roundtrip |
| Marvin/Whisper/HTTP | keine Initialisierung oder Aufrufe; zusätzlicher frischer Subprozess lehnt bereits Importversuche ab |

Der Originalpilot enthält 2228 Cues, darunter zwei leere Cues. Roh-SHA-256:
`719c9905c3908594dd459224b78d5ac9f5cfbc6e06b4dadd67d9f1ea98ecac2c`.
Normalisiertes JSON am geprüften lokalen Stand:
`d2326bfd6b24f288ca9fa6a3921643ddbc61439d418e1950de75b0099444f5c4`.
Die geprüfte `media_id` ist `JP7ITIXGpHk`; sie stammt aus der bestehenden Bindung,
nicht aus dem SRT-Dateinamen. Bei Cybersecurity Woche `0` bleibt sie `None`.

Der echte Chunker erzeugt für diesen einzelnen Pilot 157 Chunks. Nur der erste
Chunk wurde mit einer **synthetischen Aussage und einer synthetischen Formel**
verbunden und konsolidiert. Diese Inhalte sind Testdaten, keine aus dem Vortrag
extrahierten fachlichen Behauptungen. Erste Chunk-ID `chunk_0000`, Segment-IDs
`[0,2,3,4,5,6,7,8,9]`, unveränderte Start-/Endzeit `0.0` / `45.65` Sekunden.
Die übrigen Chunks wurden weder extrahiert noch konsolidiert; kein vollständiger
Kursbestand wurde verarbeitet.

## Neue API und Manifest

`src/tools_knowledge/bind_cs50_transcript.py` bietet:

* `bind_cs50_knowledge_input(plan, binding, workspace=...)`: liest explizite Pfade,
  fordert erfolgreich abgeschlossene Download-/Importbelege, prüft Version,
  vollständige Bindung, Hashes, Sprache, Original-URL, Provenienz und SRT-Inhalte.
  `prepared`, `running`, `failed`, fehlende Belege oder Dateien werden abgewiesen.
* `CS50KnowledgeInput` / `CS50KnowledgeInputManifest`: separate Version-1-Modelle
  für course/section/lecture/resource/source IDs, `media_id`, URL, Sprache,
  vollständige `TranscriptProvenance`, HTML-Provenienz, explizite Artefakt-/Belegpfade
  und beide SHA-256. Identitäten werden gegen die vollständige ursprüngliche
  `CS50TranscriptBinding` validiert. Doppelte Quellen sind nicht zulässig.
* `load_knowledge_transcript`: revalidiert ein geladenes Manifest gegen Plan,
  Beleg und tatsächliche Artefakte; ein JSON-Roundtrip allein ist keine Freigabe.
* `build_cs50_knowledge_chunks`: revalidiert den Eingang, behält originale Segment-
  IDs und Zeiten und ruft den echten zeitbasierten Chunker auf. Positive Zieldauer
  und mindestens ein Überlappungssegment sind Voraussetzung dieses neuen Pfads.
* `build_cs50_knowledge_document`: übernimmt explizite Identitäten, prüft nochmals
  Artefakthashes, Herkunft und die tatsächlichen Segment-/Text-/Zeitreferenzen der
  Chunks, bindet bereitgestellte Ergebnisse über die vorhandene Evidence-Funktion
  und konstruiert regulär das vorhandene Knowledge-Ergebnismodell. Vorhandene
  Visual-Candidate-Metadaten werden über `make_visual_candidate` erhalten, ohne
  visuelle Verarbeitung zu starten. Unbekannte oder
  doppelte Ergebnis-Chunk-IDs werden abgewiesen. Ergebnisobjekte werden kopiert.
* `save_knowledge_manifest`: validiert und speichert exklusiv; kein Überschreiben.

Es gibt keine rekursive Suche, Dateinamens-ID-Ableitung, Video-ID-Erfindung,
ResourceTask-Ausführung, Extraktionsaufforderung oder automatisch gestartete
Consolidation. Der neue Manifest-Einstieg erzeugt ausschließlich ein Manifest
für genau einen explizit gewählten Kursabschnitt:

```bash
uv run --offline --no-sync python -m scripts.report_cs50_knowledge_input \
  --plan docs/course_sources/cs50/cs50_lecture_plan.v1.json \
  --course cs50_python --section 0 \
  --output /tmp/cs50-python-0-knowledge-input.v1.json
```

Dieser Befehl braucht bereits erfolgreich importierte Artefakte. Er schreibt nur
an einen neuen Manifestpfad außerhalb der Quellartefaktwurzeln. Das gespeicherte
Beispiel wurde damit tatsächlich erzeugt; Quellen, Belege und Transcript-JSON
wurden dabei nicht verändert.

## Stille Cues und Identitätsverträge

Leere SRT-Cues bleiben unverändert im `TranscriptDocument`. Nur für den neuen
CS50-Knowledge-Pfad wird eine lokale Kopie mit nicht leeren Segmenten an den
unveränderten Chunker gegeben. Es erfolgt weder Renummerierung noch Deduplication
oder Zeiterfindung. Leere Cue-IDs können dadurch keine inhaltliche Evidence erhalten.
Musik-/Sprecherhinweise mit tatsächlichem Text sind keine leeren Cues.

Chunk-IDs bleiben die vorhandenen lokalen `chunk_0000`-IDs, nicht global über alle
Vorlesungen eindeutig. Ihre Quellenidentität ist das zugehörige Dokument mit
expliziter `source_id`. `KnowledgeEvidence.source="transcript"` bleibt die
Modalität; `TranscriptProvenance.transcript_source="official_subtitle"` bleibt die
Herkunftsstrategie. Diese Felder werden nicht gegenseitig ersetzt.

## Notwendige minimale Korrekturen am tatsächlichen Arbeitsbaum

Die früheren Berichte beschreiben Korrekturen, die im aktuellen Arbeitsbaum und
in der Grundlage PR 4 nicht vollständig enthalten waren. Für echte Modulimporte
und persistente Ergebnisse waren folgende unmittelbar nachgewiesenen Ergänzungen
nötig:

1. `TranscriptKnowledgeDocument`: optionales, nicht leeres `source_id`, Sprache,
   vollständige Transcript-Provenienz sowie geprüfte Kurs-/Lecture-ID.
2. `ConsolidatedKnowledgeDocument`: optionale Sprache, Transcript-Provenienz,
   Kurs-/Lecture-ID und `media_id`; deterministische Consolidation reicht sie
   unverändert weiter. Fehlende Quellenidentität scheitert vor Verarbeitung,
   ohne URL-/Dateinamen-Fallback.
3. Consolidation importiert `normalize_math_text` aus `latex_helper`, seinem
   tatsächlichen Definitionsmodul.
4. `find_knowledge`: der vorhandene Marvin-Funktionsvertrag wird erst beim
   tatsächlichen Extraktionsaufruf dekoriert. Instruktionen, Schema-Name,
   Parameter und Rückgabetyp bleiben erhalten; `lru_cache` hält die dekorierte
   Funktion. Der Chunking- und Evidence-Code bleibt unverändert.

Dies sind optionale rückwärtskompatible Felder, keine neuen Lecture-/Transcript-
Modelle und keine Migration. Alte Knowledge-JSONs ohne Metadaten bleiben ladbar;
Consolidation verlangt wie dokumentiert eine explizite Quellenidentität.
Bestehende Legacy-Aufrufe mit Identität funktionieren weiterhin. Allgemeiner Runner,
Loviscach, Discovery, Selection, Download und zeitbasierter Chunking-Algorithmus
bleiben unverändert. Neue optionale Felder können bei einer erneuten Serialisierung
als `null` erscheinen; bestehende Dateien werden nicht umgeschrieben.

`section_key` und `resource_id`, Roh-/JSON-Hashes sowie HTML-Provenienz bleiben
zusätzlich im Manifest, weil bestehende Knowledge-Ergebnisdokumente sie nicht direkt
abbilden. `source_id` entspricht weiterhin der SRT-`resource_id`, niemals der
logischen `lecture_id`. Vollständige Import-Provenienz einschließlich Original-
Importzeitpunkt bleibt in beiden Ergebnisdokumenten erhalten.

## Testabdeckung und verbleibende Grenzen

Offline-Tests verwenden echte Module und Modelle, Fake-HTTP nur für kleine
synthetische temporäre Artefakte. Der echte Pilot wird ausschließlich gelesen.
Der Sechs-Kurse-Test prüft alle 50 **geplanten** Bindungen; er importiert/verarbeitet
nicht sämtliche Quellen. Nicht lokal erfolgreich ausgeführte Vorlesungen bleiben
für diesen Knowledge-Pfad ausdrücklich nicht zugelassen.

Der synchrone Importtest verwendet einen frischen Interpreter, temporäre Settings,
einen 30-Sekunden-Timeout, Socket-Sperren und einen Importwächter für Marvin,
Whisper und yt-dlp. Es gibt keine Ersatzmodule für Zielcode, Chunker, Pydantic-
Modelle, Evidence oder Formel-Consolidation.

Die Integration ist bewusst eine explizite neue API. Der vorhandene allgemeine
Knowledge-Runner wird nicht automatisch darauf umgestellt; seine bisherigen
Dateinamenheuristiken und LLM-Konfiguration sind kein zugelassener CS50-Einstieg.
Produktive LLM-/semantische Consolidation und Runner-Dispatch bleiben ein separat
zu aktivierender späterer Schritt. SDK-/SQLite-Initialisierung wurde nicht getestet
oder gestartet. POSIX-/Settings-Voraussetzungen des vorhandenen Executors bleiben.

### Separater TXT-Blocker — unverändert

`tests/test_official_transcript_import.py`: **33 bestanden, 6 fehlgeschlagen**.
Der bestehende TXT-Importer erzeugt unbekannte Zeiten `start=None, end=None`,
während `TranscriptSegment` aktuell `float` verlangt. Betroffen sind:

* `test_txt_unknown_timestamps_paragraphs_and_unicode`
* `test_explicit_encoding[cp1252]`
* `test_explicit_encoding[utf-16]`
* `test_exclusive_save_and_no_overwrite`
* `test_knowledge_chunking_contract_without_llm_imports`
* `test_import_does_not_load_whisper_or_application_settings`

Der Fehler entsteht vor der zeitlosen Verarbeitung, verhindert aber nicht den
SRT-Knowledge-Pfad. Keine Modelländerung an Zeitstempeln, keine künstlichen Zeiten
und kein TXT-Fallback wurden vorgenommen.

## Abschließende Testergebnisse in der regulären lokalen uv-Umgebung

| Prüfung | Ergebnis |
| --- | --- |
| Neuer Eingabebindungs-Testumfang einschließlich Originalpilot | 28 bestanden, 51,90 s |
| Kombinierter Lauf mit Executor, Adapter, source_id und Formelimport (damals 24 neue Fälle) | 99 bestanden, 115,53 s |
| Sechs-Kurse-Discovery-/Extraction-/Selection-Regressionen | 136 bestanden, 126,66 s |
| Offizielle Importtests, separater TXT-Blocker | 33 bestanden, 6 unveränderte TXT-Fehler |
| Ruff Check/Format für neue Python-Dateien und Diff-Whitespace | bestanden |

Damit wurden **239 unterschiedliche relevante Tests** erfolgreich ausgeführt
(28 neue + 75 Executor/Adapter/source_id/Formelimport + 136 CS50-Regressionen),
zusätzlich zu den 33 bestandenen offiziellen Importfällen. Der letzte neue
Testumfang enthält auch Hashformat-Validierung und unveränderte Weitergabe eines
synthetischen Visual-Candidates ohne visuelle Verarbeitung. Eine nach dem Chunking
geänderte Erfolgsquittung wird vor der Dokumenterstellung erneut abgewiesen.

```bash
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python -m pytest tests/test_cs50_knowledge_input.py -q
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python -m pytest tests/test_cs50_knowledge_input.py tests/test_cs50_executor.py tests/test_cs50_lecture_adapter.py tests/test_knowledge_source_id.py tests/test_consolidation_math_import.py -q
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python -m pytest tests/test_cs50_discovery.py tests/test_cs50_extraction.py tests/test_cs50_selection.py tests/test_cs50_six_courses.py tests/test_cs50_full_coverage.py tests/test_cs50_timed_selection.py -q
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python -m pytest tests/test_official_transcript_import.py -q
```

Keine zusätzlichen Abhängigkeiten, Downloads oder Installationen; keine produktiven
Knowledge-Dateien erzeugt. Synthetische Ergebnis-JSONs liegen in temporären
Testverzeichnissen. Das neue Dokumentationsmanifest ist eine exklusive neue Datei,
keine Änderung des produktiven Piloten.
