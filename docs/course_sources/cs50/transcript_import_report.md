# Offline-Import offizieller Transkripte

## Ergebnis und Umfang

`src/tools_transcribe/import_transcript.py` importiert lokale TXT-, SRT- und VTT-Dateien
als vorhandenes `TranscriptDocument`, ohne Whisper, HTTP, LLM oder App-Konfiguration.
`import_txt`, `import_srt`, `import_vtt` und die generische Funktion `import_transcript`
lesen ausschließlich die angegebene Datei. Sprache und Original-URL sind Pflichtangaben.
Das Speichern ist separat und ausdrücklich: `save_imported_transcript` erzeugt UTF-8-
JSON exklusiv mit Dateimodus `x`; bestehende Dateien und Symlinks werden nicht überschrieben.
Der Zielordner muss bereits existieren, das Ziel muss auf `.json` enden.

SRT/VTT lassen sich auf Daten- und Chunking-Ebene in der vorhandenen zeitbasierten
Knowledge Extraction verwenden. **TXT ist importierbar und speicherbar, aber noch
nicht durch das zeitbasierte Knowledge-Chunking verarbeitbar.** Das Chunking meldet
jetzt diese Inkompatibilität ausdrücklich statt mit einer None-Arithmetik zu scheitern.
Ein späterer PR kann wort-/absatzbasiertes Chunking und zeitlose Knowledge-Evidenz
ergänzen. Diese Grenze wird nicht durch erfundene Zeitmarken umgangen.

## Bestandsaufnahme

| Baustein | Vorhandener Vertrag / Verwendung | Konsequenz für den Import |
|---|---|---|
| `model_transcribe/data_transcribe.py`: TranscriptSegment | `seg_id`, `start`, `end`, Text; optionale Speaker/Confidence | TXT benötigt unbekannte Zeiten als `null`; Untertitel liefern echte Sekunden |
| TranscriptDocument | Quelle, Sprache, Text, Segmente, optionale Dauer/VAD/Runtime/Provenienz | Direkt wiederverwendbar, keine erfundenen Whisper-Metriken |
| TranscriptProvenance | TranscriptSource, DownloadStrategy, Original-URL, Quelldatei, Sprache, Format, Provider/Model, acquired_at | Herkunft über zwei neue TranscriptSource-Werte; DownloadStrategy und Whisper-Felder bleiben `null` |
| `tools_transcribe/process_subtitle.py`: parse_subtitle | Nur VTT mit Stundenformat; Defaultsprache Deutsch; überschneidende Wortpräfixe werden entfernt; schreibt JSON über save_dict | Für offizielle Dateien ungeeignet: neue isolierte Importer erhalten alle Cues, auch identische |
| FasterWhisperProvider / transcribe_files | Audiodateien → TranscriptDocument → JSON mit Provenienz | Unverändert; für externe Transkripte nicht erforderlich |
| `utils/dict_helper.py`: save_dict/load_dict | JSON mit `.json`-Suffix, Model-Dump/Model-Validation; save_dict schreibt standardmäßig `w`; lädt App-Konfiguration | JSON-Vertrag wiederverwendbar; keine Wiederverwendung des überschreibenden, konfigurationsabhängigen Speichercodes |
| `tools_lecture/plan_lecture.py` | Erkennt lokale Transcript-JSONs; VTT als Untertitel; sonst Audio-/Downloadpfad | Normalisiertes JSON kann später als lokales Transkript zugeordnet werden; Importer ändern keine Planung |
| `tools_lecture/process_lecture.py` | Task-Ausführung lädt AudioContext/Transkriptionsprovider auch vor Dokumentaktionen | Import läuft separat; kein automatischer ResourceTask- oder Runner-Aufruf |
| `tools_knowledge/find_knowledge.py`: build_transcript_chunks | Zeitbasiert: Endzeit minus Startzeit, Zielzeit und Segmentüberlappung | SRT/VTT kompatibel; zeitlose TXT-Segmente werden verständlich abgelehnt |
| `run_knowledge_extraction.py` | Lädt JSON als TranscriptDocument, Chunking, Kontext, LLM-Analyse, Provenienz, visuelle Kandidaten | Nur Daten-/Chunking-Kompatibilität offline geprüft; keine reale Knowledge Extraction ausgeführt |
| KnowledgeEvidence / TranscriptChunk / VisualCandidate | Pflichtwerte `start`/`end` als float; Consolidation/Visual-Rebuild vergleichen Zeitfenster | TXT braucht spätere gezielte Erweiterung bis zur Evidenz; Bilder/Videoausschnitte lassen sich ohne Zeiten nicht lokalisieren |
| `run_record_upload.py` | Verwendet ebenfalls build_transcript_chunks für Transkript-RAG | Gleiche TXT-Grenze; durch Chunking-Guard geschützt |

Original-URL in TranscriptProvenance ist die URL der tatsächlich importierten TXT/SRT/VTT-
Ressource, nicht automatisch eine YouTube-/Video-URL. Nachgelagerte `extract_media_id`
kann deshalb keine Video-ID aus ihr ableiten. Ein späterer Course-Export muss die
Medienzuordnung separat aus Discovery erhalten. Dateinamen und lokale Pfade müssen
explizit zur Vorlesung zugeordnet werden; dieser PR verbindet keine Discovery- oder
Selection-Ressource automatisch mit LectureResource.

## Kleine begründete Modelländerung

Nur `TranscriptSegment.start/end` werden von `float` auf `float | None` erweitert;
beide Felder bleiben Pflichtfelder. Explizite Nullwerte bedeuten unbekannte Zeit,
`0.0` bleibt eine echte bekannte Zeit. Alte numerische Whisper-/VTT-JSONs bleiben
unverändert validierbar. TranscriptSource erhält `official_transcript` und
`official_subtitle`; bestehende Enum-Werte bleiben erhalten. Keine Änderung an
Lecture-, Knowledge-, Discovery- oder Selection-Modellen und keine Änderung an
Loviscach-Funktionen. Die sechs zusätzlichen Zeilen im Knowledge-Chunker prüfen
fehlende Zeitmarken, ohne das Verhalten für bekannte Zeiten zu ändern.

Ältere Programmversionen ohne diese Modelländerung können die neuen Herkunftswerte
und Nullzeiten nicht lesen; der Importvertrag verlangt diese aktualisierte Version.

## Parsingregeln

- UTF-8 mit optionalem BOM; andere Codierungen nur ausdrücklich über `encoding`.
  Decodierungsfehler werden nicht durch Ersatzzeichen versteckt. CRLF/CR werden
  normalisiert; Unicode und Textreihenfolge bleiben erhalten.
- TXT: Absätze werden Segmente; interne Zeilen bleiben erhalten. Start/Ende und Dauer
  sind `null`; keine Schätzung aus Wortzahl oder Vorlesungsdauer.
- SRT: numerische Cue-ID, `HH:MM:SS,mmm`; Quell-IDs werden in der ursprünglichen
  Reihenfolge zu fortlaufenden `seg_id` normalisiert.
- VTT: WEBVTT-Header mit Leerzeile; optionale Cue-IDs, `MM:SS.mmm` oder
  `HH:MM:SS.mmm`, Timing-Settings werden nicht in Text/Zeiten übernommen. NOTE/STYLE/
  REGION-Blöcke werden ignoriert. Präsentationstags und Inline-VTT-Zeiten werden
  entfernt, HTML-Entities decodiert. Speaker-Namen aus Voice-Tags werden nicht
  automatisch als Sprecheridentität behauptet.
- Pro Cue genau ein Segment, Mehrzeilen-Text bleibt mehrzeilig. Wiederholte Zeilen,
  identische Cues und zeitlich überlappende Cues werden nicht dedupliziert.
  Kein Sortieren oder Zusammenführen; Dateireihenfolge bleibt maßgeblich.
- Zeitangaben müssen syntaktisch stimmen, Minuten/Sekunden kleiner als 60 sein und
  Ende darf nicht vor Start liegen. Defekte oder leere Cues und leere Dateien werden
  als Fehler gemeldet; kein stilles Überspringen beschädigter Cues.
- Untertitel-Dauer ist das maximale bekannte Cue-Ende, keine garantierte Mediendauer.
  Nicht chronologisch sortierte Quell-Cues werden nicht repariert; für sinnvolle
  zeitbasierte Knowledge-Chunks muss die Quelle chronologisch geordnet sein.

## Verwendung und Beispiel

```python
from pathlib import Path
from src.tools_transcribe.import_transcript import import_srt, save_imported_transcript

transcript = import_srt(
    Path("local/lecture.en.srt"),
    language="en",
    original_url="https://example.com/lecture.en.srt",
)
save_imported_transcript(transcript, Path("local/transcripts/lecture.json"))
```

`examples/official_transcript.txt` und `examples/official_transcript.normalized.json`
enthalten ein ausdrücklich synthetisches TXT-Beispiel. Seine zwei Segmente haben
`start: null`, `end: null`, Herkunft `official_transcript`, Sprache `en` und keine
Whisper-Metriken. `acquired_at` ist für das Beispiel auf einen festen Wert gesetzt.
Das JSON kann mit `TranscriptDocument.model_validate_json(...)` geladen werden.

## Validierung

37 pytest-Fälle in `tests/test_official_transcript_import.py` mit synthetischen Dateien:
Segmentreihenfolge, echte Zeiten einschließlich Stunden, überlappende und identische
Cues, Mehrzeilen-Untertitel, Unicode/BOM/CRLF, explizite CP1252/UTF-16-Codierung,
leere Dateien, beschädigte Zeitangaben, VTT-Metadaten, Pflichtmetadaten, JSON-Roundtrip,
Kompatibilität numerischer Altsegmente und Überschreibschutz einschließlich Symlinks.
Socket/DNS sind gesperrt. Ein Import-Isolationstest prüft, dass Whisper und die
App-Konfiguration nicht geladen werden. Der tatsächliche Knowledge-Chunker wird per
AST isoliert ausgeführt: zeitbasierte SRT-Chunks funktionieren, zeitlose TXT-Daten
führen zur dokumentierten Ablehnung, ohne Marvin-/LLM-Imports.

Aufruf: `python -m pytest tests/test_official_transcript_import.py -q`.
Zusätzlich laufen die 93 bestehenden CS50-Tests als Regression gegen den aktualisierten
Workspace. Ruff, Commit-Hooks und `git diff --check` prüfen die geänderten Dateien.
Keine Downloads, Transkriptionen oder LLM-Aufrufe wurden gestartet.
