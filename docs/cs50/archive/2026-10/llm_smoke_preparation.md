# Kontrollierter CS50-LLM-Smoke-Test

## Ergebnis der Offline-Vorbereitung (13.10.2026)

Die Vorbereitung funktioniert; die echte synchrone Marvin-Initialisierung bleibt
in dieser lokalen uv-Umgebung blockiert. Kein API-Aufruf wurde ausgeführt. Ein
erfolgreich vom LLM erzeugtes `ChunkKnowledgeResult` wird deshalb nicht behauptet.

Die neue CLI ist `scripts/cs50_llm_smoke.py`. Produktionsmodule, Prompts,
Discovery, Selection und Chunking wurden nicht geändert. Sie verwendet
`TranscriptDocument`, `KnowledgeSettings`, `build_transcript_chunks()`, den
vorhandenen Lazy-Decorator und für einen ausdrücklich aktivierten LLM-Test
`configure_marvin()`, `extract_knowledge()`, `attach_chunk_provenance()` sowie
`validate_extraction()`. Cache und `analyze_chunk_with_retry()` werden umgangen.

Die frühere normalisierte Pilotdatei aus `/tmp` war nicht mehr vorhanden. Aus der
lokalen Originaldatei `data/lectures/cs50_python/lecture0.srt.txt` wurde deshalb
mit dem vorhandenen SRT-Importer eine neue normalisierte Kopie ausschließlich
unter `/tmp/cs50-smoke-source/lecture0.json` erzeugt. Die Originaldatei blieb
unverändert (SHA256
`719c9905c3908594dd459224b78d5ac9f5cfbc6e06b4dadd67d9f1ea98ecac2c`).
2228 Segmente einschließlich sechs ausdrücklich bewahrter leerer Cues;
Sprache `en`, Herkunft `official_subtitle`, Original-URL
`https://cdn.cs50.net/python/2022/x/lectures/0/lang/en/lecture0.srt`.
Der Hash der neu normalisierten JSON steht im Ergebnisbericht und umfasst auch
den neuen Importzeitpunkt; er ist daher kein dauerhaft reproduzierbarer Hash.

| Prüfung | Ergebnis |
| --- | --- |
| Normalisiertes TranscriptDocument laden/validieren | bestanden |
| Begrenztes Eingabefenster und echtes zeitbasiertes Chunking | bestanden: 10 Segmente, ein Chunk, 81 Wörter |
| Chunk-/Segment-IDs und Zeiten | `chunk_0000`, Segment-IDs 0–9, 0–45,65 Sekunden |
| Synthetischer Pydantic-Ergebnisvertrag vor Initialisierung | bestanden, keine LLM-Generierung |
| Echter synchroner Marvin-Import mit neuer isolierter SQLite-Datei | Timeout |
| Beendigung der gesamten Prozessgruppe | bestanden; zusätzliche Regression mit Enkelprozess |
| Marvin-Task-Schema und tatsächliche Generierung | wegen Initialisierung nicht erreicht |
| API-Aufrufe / Tokenverbrauch | 0 / nicht verfügbar |

Die letzte Originalquellen-Probe dauerte 12,04 Sekunden; die Vorbereitung
2,24 Sekunden. Nach weiteren rund 9,79 Sekunden war die Initialisierung noch
nicht abgeschlossen. Die Deadline beendet den Prozess mit SIGTERM und sendet
anschließend SIGKILL an die gesamte Gruppe, auch wenn der Gruppenführer schon
beendet ist. Die Deadline umfasst Vorbereitung, Initialisierung und Generierung;
die begrenzte Beendigung kann wenige zusätzliche Sekunden benötigen.
Der Elternprozess speichert den zuletzt vollständig geschriebenen Status.

Ein Faulthandler-Dump im isolierten Kindprozess zeigt erneut
`marvin.__init__ → ensure_db_tables_exist → asyncio.run`, einen wartenden
aiosqlite-Worker und die Asyncio-Selector-Schleife. Eine neue beschreibbare
SQLite-Datei allein behebt den Hänger also nicht. Die genaue zugrunde liegende
Ursache innerhalb dieser installierten Asyncio/aiosqlite-Umgebung ist damit
nicht abschließend bestimmt. Es wurde kein globaler Event-Loop-Workaround gesetzt.

## Konfiguration und Begrenzungen

Marvin 3.2.7 initialisiert beim Import seine Tabellen. Der synchrone Pfad benutzt
`asyncio.run(create_db_and_tables(...))`. `MARVIN_AUTO_INIT_SQLITE=False` ist kein
verlässlicher Schalter zum Unterdrücken dieses Aufrufs. Der Smoke-Test setzt nur
im Kindprozess `MARVIN_HOME_PATH` und `MARVIN_DATABASE_URL` auf den neuen
Ergebnisordner. Eine neue Testdatenbank ist beabsichtigt; vorhandene Datenbanken
werden weder geöffnet noch migriert. App-Settings/Logger werden ebenfalls isoliert.
Der minimale Kindprozess-Environment übernimmt keine produktiven `.env`-Dateien,
Proxy- oder Telemetrie-Konfiguration. API-Schlüssel werden nicht protokolliert.

Standard ist **offline**, ein Chunk, Modell `openai:gpt-4o-mini`, 30 Sekunden
Gesamtdeadline. Offline werden Socket/DNS-Zugriffe im Kindprozess abgewiesen.
Der Interpreter läuft mit `-I` in einem neuen Ordner. Maximal zwei Chunks sind
erlaubt: Das Eingabefenster endet am ersten Cue über 45 bzw. 90 Sekunden und
enthält höchstens 64 Segmente. Der bestehende Chunker erhält nur dieses Fenster;
ausgewählt werden höchstens zwei Ergebnisse, jeweils höchstens 6000 Zeichen.
Es werden nicht die 157 vollständigen Vorlesungs-Chunks verarbeitet.

Bei `--enable-api` sind höchstens **ein HTTP-Versuch pro Chunk**, insgesamt
höchstens zwei, erlaubt. OpenAI-Client und HTTP-Transport haben Retries 0.
Ein fehlgeschlagener Request sperrt weitere Versuche. Eine interne zusätzliche
Modellrunde wird am Transport abgewiesen, auch nach einer erfolgreichen ersten
Antwort. Das kann Marvin-Generierung bewusst scheitern lassen, falls mehrere
Runden erforderlich sind. Es gibt keine automatische Wiederholung oder Budget-
Erhöhung. Nur POST an `api.openai.com` ist im Modelltransport zugelassen;
Client-Timeout 20 Sekunden, Ausgabe-Limit 1200 Tokens je Request. Dieses Limit
ersetzt keine Kostenprüfung des gewählten Modells und begrenzt keine Eingabetokens.

Die echte Lazy-Funktion, das vorhandene Prompt und die Pydantic-Schemata bleiben
erhalten. Der separate Smoke-Test ersetzt im isolierten Prozess lediglich den
Marvin-Modellprovider durch den begrenzten OpenAI-Client. Ein explizit exportierter
`OPENAI_API_KEY` ist erforderlich. SDK-/HTTP-Fehler werden ohne Response-Bodies
protokolliert; Tokenzahlen werden aus `usage` aufgezeichnet, soweit geliefert,
ansonsten als unbekannt. Der SDK-Provider-Vertrag wird offline geprüft; echte
Agenten-/API-Kompatibilität bleibt wegen des Initialisierungsblockers unbewiesen.

## CLI: offline und separat aktivierbarer API-Test

Aus dem Repository-Verzeichnis mit einer vorhandenen normalisierten Datei:

```bash
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python scripts/cs50_llm_smoke.py \
  --transcript /tmp/cs50-smoke-source/lecture0.json \
  --output /tmp/cs50-smoke-offline-next --timeout 12
```

Der Ergebnisordner muss neu sein und außerhalb des produktiven `data/`-Baums
liegen. Exit 0 bedeutet erfolgreicher Offline-Vertrag plus Marvin-Initialisierung
bzw. erfolgreicher aktivierter Test; Exit 1 umfasst Timeout/Workerfehler. Ein
Offline-Ergebnis ist ausdrücklich keine Bestätigung einer LLM-Generierung.

Falls die temporäre normalisierte Datei fehlt, kann sie aus der unveränderten
lokalen Quelle neu erstellt werden (kein Download, exklusives Schreiben):

```bash
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python - <<'PY'
from pathlib import Path
from src.tools_transcribe.import_transcript import import_srt, save_imported_transcript
destination = Path('/tmp/cs50-smoke-source')
destination.mkdir(parents=True, exist_ok=True)
document = import_srt(
    Path('data/lectures/cs50_python/lecture0.srt.txt'),
    language='en',
    original_url='https://cdn.cs50.net/python/2022/x/lectures/0/lang/en/lecture0.srt',
    preserve_empty_cues=True,
)
save_imported_transcript(document, destination / 'lecture0.json')
PY
```

**Separat, vom Benutzer bewusst zu starten:** Nach erfolgreicher Initialisierungs-
prüfung und mit bereits sicher exportiertem `OPENAI_API_KEY`:

```bash
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python scripts/cs50_llm_smoke.py \
  --transcript /tmp/cs50-smoke-source/lecture0.json \
  --output /tmp/cs50-smoke-api-once \
  --model openai:gpt-4o-mini --max-chunks 1 --timeout 60 --enable-api
```

`uv --offline` verhindert Dependency-Netzwerkzugriffe; erst `--enable-api` erlaubt
dem Smoke-Worker den kostenpflichtigen Modellaufruf. Der interne Worker-Einstieg
benötigt zusätzlich die vom Elternprozess gesetzte Aktivierung und lässt sich
nicht allein durch Bearbeiten einer Offline-Plan-Datei aktivieren. Die Aktivierung
ist eine Bedienungssicherung, keine Sicherheitsgrenze gegen eigenen Python-Code.
Solange der dokumentierte Initialisierungshänger besteht, ist ein echter API-Test
nicht sinnvoll. Timeout-Verlängerung beweist keine Reparatur.

Dateien im neuen Ordner: `plan.json`, `chunks.json`, `offline_contract.json`,
`worker.json`, `report.json`, `stdout.log`, `stderr.log`, neue Marvin-Testdatenbank;
nur bei tatsächlichem Erfolg `chunk_0000.json` und gegebenenfalls `chunk_0001.json`.
Ergebnisse werden als `ChunkKnowledgeResult` validiert, mit echter Chunk-Provenienz
verknüpft und per JSON erneut validiert. Es entsteht keine produktive
Knowledge-Datei, keine Konsolidierung und kein Visual-/Whisper-Aufruf.

## Regression

Ausgeführt in der tatsächlich installierten uv-Umgebung (Python 3.12.12):

```bash
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python -m pytest tests -q
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python -m pytest tests/test_cs50_llm_smoke.py -q
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python -m ruff check scripts/cs50_llm_smoke.py tests/test_cs50_llm_smoke.py
```

Der Gesamtlauf bestand mit **181 Tests**. Der abschließende fokussierte Lauf
bestand mit **9 Tests** und prüft zusätzlich den real installierten
OpenAI-/Pydantic-AI-Provider-Konstruktor
mit gesperrtem Netzwerk. Die Smoke-Tests prüfen Offline-Default, isolierte Settings,
fehlende Credentials, Chunk-/Timeout-Grenzen, Ablehnung vorhandener Ergebnisordner,
Budget/Fehlersperre, API-Worker-Aktivierung, tatsächliche Offline-Modellvalidierung
vor einem kontrollierten Initialisierungsfehler und Prozessgruppenbeendigung.
Kein Test führt einen echten Modellaufruf aus. Ruff und `git diff --check` prüfen
die neuen Dateien. Keine neuen Dependencies und kein automatisches Mergen.
