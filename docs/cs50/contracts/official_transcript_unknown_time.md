# C23-05: Offizielle Transkripte und unbekannte Medienzeiten

Stand 18.10.2026. Implementierungsbasis: Master
`b2b994a3bc09b061992ba5f4ba7c6b6a36fd9aa0` (C23-03 gemergt).
C23-04 war bei Arbeitsbeginn offen und wird nicht vorausgesetzt.
Vor PR-Erstellung auf den inzwischen um #80 ergänzten Master
`1254c2c79d99525f150cf3d84050d0e5d504d6ce` abgeglichen; beide vorhandenen
Dokumentationsnachträge erhalten, Transcriptänderungen unverändert.
[Abnahme und Grenzen](../evaluation/official_transcript_unknown_time.md).

## Ursache und Vergleich mit PR #9

Der vorhandene TXT-Importer konstruierte `TranscriptSegment` mit
`start=None, end=None`, während das gemergte Modell beide Felder als `float`
deklarierte. Sechs Tests scheiterten bereits in Pydantic, vor der Speicherung.

Der offene historische [PR #9](https://github.com/rf-data/Personal_Assistant/pull/9)
wurde anhand seiner Metadaten und sämtlicher sechs Dateipatches geprüft
(Head `3d1317347018fce47f49331fbfea92e4a055a337`). Importer, Herkunftsenums,
synthetischer TXT-Beispieltext und Importtests sind bereits vorhanden; der
Importbericht liegt inzwischen im Archiv. Noch nötig waren Nullablezeiten
und der Timed-Chunker-Guard. C23-05 implementiert diese mit Intervallvalidierung
und Verbraucherprüfung. Kein Merge/Cherry-pick und keine Schließung von #9.

## Modell- und JSON-Vertrag

- `start/end` bleiben Pflichtfelder: entweder beide endliche, nichtnegative
  Sekunden mit `end >= start`, oder beide explizit `null`. Null-/Zahlenpaare,
  negative Werte, NaN/Infinity und umgekehrte Intervalle werden bei Konstruktion
  und JSON-Laden abgewiesen. Überlappende und Null-Dauer-Cues bleiben gültig.
- `None` bezeichnet fehlende Medienzeit, `0.0` einen bekannten Medienbeginn.
  Dokumente dürfen bekannte und unbekannte Segmente enthalten; Timed-Verbraucher
  lehnen solche gemischten Dokumente insgesamt ab.
- Bei unbekannten Segmentzeiten muss `duration=None` bleiben. Textlänge und
  das letzte bekannte Segment liefern keine sichere Dauer.
- `TranscriptSegment.require_timestamps()` liefert geprüfte Sekunden oder
  `ValueError` mit Präfix `unknown_transcript_time` und Hinweis auf Text-Chunking.
  Ungültige nachträglich kopierte Intervalle erhalten `invalid_transcript_time`.
  `TranscriptDocument.require_timestamps()` prüft sämtliche Segmente.
- Methoden sind keine serialisierten Felder. Bestehende gültige numerische
  Transcript-JSONs benötigen weder Versionsfeld noch Migration. Werte, Feldnamen,
  Metadaten und Enums bleiben erhalten; das Payloadschema bleibt
  `TranscriptDocument:legacy-unversioned`. Alte Float-only-Programme können neue
  Nullzeiten nicht lesen. Ungültige historische Intervalle werden nicht repariert.
- Pydantic-Zuweisungen und `model_copy(update=...)` bleiben wie bisher ungeprüft;
  Konstruktion/`model_validate`/JSON-Laden validieren. Der Saver revalidiert den
  Dump vor Dateierzeugung; Timed-Grenzen prüfen erneut die Zeiten.

## Lokaler Import und Speicherung

```python
from pathlib import Path
from src.tools_transcribe.import_transcript import import_txt, save_imported_transcript

document = import_txt(
    Path("local/official.txt"), language="en",
    original_url="https://example.invalid/official.txt",
)
assert document.duration is None
assert all(s.start is None and s.end is None for s in document.segments)
save_imported_transcript(document, Path("local/official.json"))
```

UTF-8 mit optionalem BOM ist Standard; weitere Encodings, beispielsweise
CP1252/UTF-16, verlangen explizites `encoding`. Decodierungsfehler werden nicht
ersetzt, NUL-Text wird mit Encodinghinweis abgewiesen. Leere/Whitespace-Eingaben
bleiben Fehler. Keine Encodingheuristik oder Initialisierung von Settings/Whisper/LLM.

CRLF/CR werden zu LF und ein UTF-8-BOM wird entfernt. TXT-`document.text` erhält
danach den vollständigen Text einschließlich Einrückung, Mehrfachleerzeilen und
abschließendem Zeilenumbruch. Unicode bleibt ohne NFC-/NFKC-Normierung erhalten.
Nichtleere Absätze werden in Quellreihenfolge fortlaufend nummerierte Segmente;
Leerzeilenfolgen trennen Absätze, innere Textzeilen und Randspaces bleiben erhalten.
Die vollständigen Trenner bleiben im Dokumenttext. Gegenüber dem vorherigen
TXT-Importer gehen Randspaces/Leerzeilen nicht mehr durch `strip()` und
Zusammenfügen verloren. Bestehende Dateien werden nicht umgeschrieben.

Sprache, Sourcepfad, Original-URL, `official_transcript` und `media_format=txt`
bleiben in der Provenienz. Die URL ist die Transkriptressource, keine erfundene
Videozuordnung. Keine Whisper-/VAD-/Runtimewerte werden ergänzt. Wiederholter
Import liefert gleiche Segment-/Text-/Quellenwerte; `acquired_at` bezeichnet
weiterhin den jeweiligen Importzeitpunkt und ist deshalb nicht byteidentisch.
Speichern/Laden desselben Dokuments erhält auch diesen Zeitpunkt.

`save_imported_transcript` bleibt getrennt und exklusiv (`x`, UTF-8-JSON).
Vorhandene Dateien/Symlinks werden abgewiesen, `.json` ist Pflicht, der Elternordner
muss existieren. Import erzeugt keine Dateien, Originalbytes bleiben unverändert.
Normalisierter Text beansprucht wegen BOM-/Zeilenendebehandlung keine Rawbyteidentität.
SRT/VTT behalten Parsingregeln, Cuezeiten, Textaggregation und den expliziten
`preserve_empty_cues`-Vertrag unverändert.

## Konstruktoren, Serializer und Verbraucher

| Baustein | Zeitannahme / Behandlung nach C23-05 |
| --- | --- |
| `model_transcribe.data_transcribe`: Konstruktion, Modell-/JSON-Laden, Dumps | Explizite Nullpaare oder gültige Sekunden; keine neuen JSON-Felder |
| `tools_transcribe.import_transcript`: TXT/SRT/VTT, Saver | TXT zeitlos, SRT/VTT numerisch; Dump vor exklusiver Ausgabe revalidieren |
| `model_transcribe.provider_transcript.FasterWhisperProvider` | Übernimmt numerische Providerzeiten; Fortschrittsarithmetik betrifft externe Whispersegmente, keine TXT-Dokumente; keine Inferenz ausgeführt |
| `tools_transcribe.process_subtitle.parse_subtitle` | Legacy-VTT-Konstruktor liefert echte Cuezeiten; eigene Overlap-/Speicherlogik unverändert, kein TXT-Routing |
| `utils.dict_helper.load_dict/save_dict` | Pydantic-Dumps/-Reads; Settings-/Überschreibverhalten macht diesen Saver für isolierten offiziellen Import ungeeignet |
| `tools_lecture.plan_lecture`, `process_lecture`, `select_cs50`, `adapt_cs50` | JSON-/Resourceplanung nicht erweitert; Normalisierung autorisiert keinen TXT-Task/Binding |
| `tools_lecture.execute_cs50.validate_document`, `validate_order` | Guard vor SRT-Reparse bzw. Zeitvergleich; `ExecutionConflict` mit Unknown-Time-Präfix beim Binding; Raw-/Provenienzprüfung bleibt erhalten |
| `tools_knowledge.find_knowledge.build_transcript_chunks` | Dokumentguard vor Dauerarithmetik; schützt auch `run_knowledge_extraction` und `run_record_upload.build_rag_records_from_transcript` |
| `tools_knowledge.bind_cs50_transcript`: bind/load/build chunks/document | Hash-/Receipt-/Original-SRT-Validierung verwendet den abgesicherten Executor; kein TXT-Fallback |
| `tools_knowledge.cs50_precise_evidence`: input/bind | Prüft referenzierte Originalsegmente vor Promptpayload/min/max; Binder meldet `EvidenceValidationError` samt Invalid-Audit |
| `tools_rag.cs50_embeddings.map_transcript`, `cs50_ingestion.revalidate_plan`, `cs50_knowledge_index.map_knowledge_document`, `cs50_retrieval_evaluation.create_evaluation_template` | Gemeinsames `source_time_window` prüft Cuezeiten vor min/max; Textoffsetfenster bleiben Zeichenpositionen |
| `tools_rag.cs50_retrieval.verify_hit` | `revalidate_plan`-Kette prüft Receipt/Hash/SRT-Binding; keine verifizierten zeitlosen Treffer |
| `tools_knowledge.cs50_evaluation` | Originalcues aus geprüftem Lecturejob; kein neuer Chunker oder Zeitfallback |
| KnowledgeEvidence, TranscriptChunk, VisualCandidate; Consolidation, Semantic/Rebuild/Visual; `tools_rag.chunk` Knowledgeexport | Numerische Knowledge-/Visualverträge unverändert; kein direkter TXT-Segmentkonstruktor. `_chunk_by_sentences` verwendet Zeichenoffsets, keine Medienzeiten |
| `content_store.adapters` SRT-Publikation / `operations` SRT-Recovery | Nur bekannte Zeiten; Recovery prüft explizit auch ohne Reparse; keine allgemeine TXT-Publikation |
| `scripts.cs50_llm_smoke` | Bereits vorhandener Timed-Guard; keine Änderung oder LLM-Ausführung |

Geprüft wurden Modell-/Konstruktorreferenzen, direkte `.start/.end`-Nutzung und
Dictionaryzeitfelder in Transcribe/Lecture/Knowledge/RAG, Contentadaptern und
aufrufenden Runnern/Skripten. Textfähige Datenhaltung ersetzt den fehlenden
Text-Chunker-/Evidence-/Retrievalvertrag nicht.

## ContentStore und spätere TXT-Integration

`ContentLocator(time_status="unknown", start=None, end=None)` bleibt kompatibel.
`known` verlangt Zahlen; `not_applicable` ist eine andere Aussage als unbekannte
Medienzeit. Kein DDL-, ID-, Hash-, Originalpfad-, Receipt- oder Slotwechsel.

`cs50_srt_content_v1` bleibt ausschließlich SRT. Die öffentliche Bundleprüfung
redigiert ungültige Nutzdaten weiterhin zu `UnverifiedBinding`/`unverified_binding`;
kein Durchreichen interner Pfade oder TXT-Fallback.

TXT-Publikation braucht einen eigenen überprüften Vertrag für Discovery-/Course-/
Lecture-/Source-Identität, unveränderte Rawbytes/Hashes, exakte Pfad-/URL-/Sprachbindung,
Receipt mit Parser-/Implementierungsrevision, deterministische Absatz-/Zeichenanker
und Projektion, Quality-/Handoffnachweis, ACL/Ownership sowie Veröffentlichung,
Recovery und Reimport. Vorher bleiben TXTadapter und zeitlose Knowledge-/Visual-/
Transcript-RAG-Pipelines gesperrt. Keine globale CS50- oder Korpusfreigabe.
