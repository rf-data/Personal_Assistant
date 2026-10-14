# PR 6 — begrenzte echte CS50-Knowledge-Extraction ermöglichen

## Ergebnis

Der vorhandene PR-5-Eingang für CS50 Python, Woche `0`, lässt sich über eine neue
isolierte CLI für genau einen oder zwei Chunks verarbeiten. Standard bleibt offline;
`--execute-llm` ist die einzige API-Freigabe des neuen Einstiegs. **Ein kostenpflichtiger
Aufruf wurde nicht ausgeführt.** Die reale Generierung ist somit vorbereitet, aber
noch nicht gegen einen echten API-Account nachgewiesen.

Die fachlichen Modelle, Extraktionsinstruktionen, zeitbasierte Chunking-Funktion,
Evidence-Regeln und deterministische Consolidation werden wiederverwendet. Kein
Discovery-, Selection-, Download-, Chunking-, Lecture- oder Knowledge-Modellumbau.

## Tatsächlich geprüfte lokale Laufzeit

Reguläre lokale uv-Umgebung: Python 3.12.12, pytest 9.1.1; HTTPX und die bestehenden
Lecture-Worker-Abhängigkeiten sind installiert. `find_spec` bestätigt, dass
`marvin`, `openai` und `pydantic_ai` in diesem Interpreter fehlen. Es wurden keine
SDKs nachinstalliert.

| Probe | Ergebnis |
| --- | --- |
| Marvin-Import im frischen isolierten Subprozess, Timeout 10 s | `ModuleNotFoundError`; Parent 0,243 s, Worker 0,0043 s, Importversuch 0,00055 s; 0 Requests |
| Offline-Pilot mit echter Eingabebindung, Timeout 45 s | erfolgreich; Parent 5,060 s, Worker 4,537 s; 1 Chunk, 0 Requests |
| Fake-HTTP-LLM mit zwei echten Pilot-Chunks | 2 Requests, validierte Aussagen/Formeln, vollständige Quellenbindung, JSON-Roundtrips und echte deterministische Consolidation |
| Echter API-Aufruf | nicht gestartet; manuell separat aktivierbar |

Die Marvin-Probe initialisiert weder einen Agenten noch SQLite: sie scheitert
bereits an der fehlenden Dependency. Der frühere SQLite-Hänger kann in diesem
Interpreter deshalb nicht erneut bestätigt oder als behoben bezeichnet werden.
`--probe-marvin` ermöglicht denselben isolierten Import später mit installierten
SDKs. Alle DB-/Home-Pfade zeigen dabei ausschließlich in das neue Testverzeichnis.

Lokale Nachweise:
`/tmp/cs50-pr6-marvin-probe-final/supervision.json` und
`/tmp/cs50-pr6-offline-final/supervision.json`.
Der Offline-Lauf ist ausdrücklich synthetisch (`result_origin=synthetic`), keine
vorgetäuschte LLM-Extraction. Er validiert auch ein korrektes irrelevantes Ergebnis
mit `extraction=None` und prüft die nachgelagerte reguläre Speicherung/Consolidation.

## Provider und unveränderte Default-Verträge

`src/tools_knowledge/cs50_extraction_provider.py` enthält zwei kleine Adapter:

* `marvin` bleibt der explizite CLI-Default. Marvin und dessen SDKs werden erst
  im autorisierten Worker geladen. Der vorhandene `extract_knowledge`-Vertrag wird
  ohne dessen allgemeine Retry-/Cache-Schleife aufgerufen. Eine begrenzte
  SDK-Transportklasse sperrt weitere Requests desselben Chunks und alle anderen
  Endpoints. Seine produktive Laufzeit bleibt wegen fehlender SDKs unbestätigt.
* `openai_http` ist eine ausdrücklich wählbare Alternative ohne Marvin/SQLite
  oder OpenAI-SDK. HTTPX ist bereits eine deklarierte Basisabhängigkeit. Ein direktes
  Chat-Completions-POST verwendet die unveränderten fachlichen Instruktionen und
  das bestehende `ChunkKnowledgeResult`-Schema. JSON-Modus ist eine Transporthilfe;
  die tatsächliche Antwort wird zwingend durch das vorhandene Pydantic-Modell
  validiert. Ungültige, verweigerte oder abgeschnittene Antworten scheitern ohne Retry.

Der HTTP-Vertrag mit JSON-Modus und `max_completion_tokens` wurde anhand der
[offiziellen Create-chat-completion-Referenz](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)
geprüft. Der bestehende CLI-Modellname `gpt-4o-mini` bleibt Standard, ist aber über
`--model` explizit konfigurierbar. Kontozugriff und Modellverfügbarkeit wurden nicht
per API überprüft. Es gibt keinen stillen Provider-Fallback.

Als kleine nachgewiesene Kompatibilitätskorrektur importiert das ältere
`scripts/cs50_llm_smoke.py` den tatsächlich vorhandenen Factory-Namen
`_get_knowledge_extractor` unter seinem bisherigen lokalen Alias. Seine CLI,
Modelldefaults, Budgets und Ausführung bleiben unverändert. Damit erreicht dessen
Offline-Regressionsprobe wieder die kontrollierte Marvin-Initialisierungsgrenze.

## Grenzen, Validierung und persistierte Informationen

Die CLI akzeptiert nur genau einen manifestierten Eingang für `cs50_python`,
Abschnitt `0`. PR-5-Plan-, Beleg-, Hash-, Sprach- und Provenienzprüfungen laufen vor
Chunk-Auswahl und erneut vor Ergebniskonstruktion. Genau die ersten ein/zwei echten
Chunks werden ausgewählt; maximal 6000 Zeichen pro Chunk. Der bestehende Chunker
liefert hierfür weiterhin die 157 Pilot-Chunks als Metadatenliste, aber die anderen
155/156 Chunks erhalten weder LLM-Aufruf noch Knowledge-Ergebnis.

* Default 45 s Prozessdeadline, maximal 120 s; der vorhandene POSIX-Supervisor
  beendet bei Timeout die gesamte Prozessgruppe mit TERM und anschließend KILL.
* Höchstens ein tatsächlicher POST je ausgewähltem Chunk, insgesamt höchstens zwei.
  Keine Wiederholungen bei 401/429/5xx, Timeout, ungültigem JSON oder Modellfehlern.
  Ein Fehler stoppt den Lauf; kein weiterer Chunk wird automatisch versucht.
* I/O-Timeout 20 s, feste API-URL, keine Redirects oder Proxy-Umgebungsvariablen.
* Default maximal 1200 Completion-Tokens je Request, konfigurierbar bis 2000.
  Konservatives Eingangsbudget über UTF-8-Bytes des kompletten Request-Payloads
  plus 2048 Framing-Reserve: Default 28000, maximal 30000. Vor jedem POST werden
  Eingang plus reservierter Output gegen ein Gesamtbudget geprüft (Default 60000,
  maximal 64000). Dies ist eine konservative lokale Schätzung, kein gemessener
  Eingangsverbrauch; tatsächliche API-Usage wird separat protokolliert, falls vorhanden.
* API-Key nur aus ausdrücklich gesetztem `OPENAI_API_KEY`; kein Key im Manifest,
  Report oder gespeicherten Konfigurationsobjekt. Offline-Worker erhalten harmlose
  Platzhalter, Socket-/DNS-Aufrufe sind gesperrt. Kein SDK ist für Offline erforderlich.

Provider-Chunks werden durch `ChunkKnowledgeResult` validiert. Vom LLM genannte
Chunk-/Segment-IDs und Zeiten sind keine Quellenidentität: Chunk-ID wird aus dem
geprüften Chunk gebunden, Segment-IDs/Zeitgrenzen/Modalität durch die vorhandene
Evidence-Funktion überschrieben und gegen echte Quellsegmente geprüft. Leere Cues
liefern weiterhin keine inhaltliche Evidence. Vollständige `TranscriptProvenance`,
`course_id`, `lecture_id`, `source_id`, URL, Sprache und `media_id` bleiben erhalten;
zusätzliche `resource_id`/Abschnitts-/Hashbindungen bleiben im kopierten Eingabemanifest.

Jeder Lauf fordert ein **neues** Ausgabeverzeichnis außerhalb produktiver `data`-
Pfade, auch bei Symlink-Alias. Ergebnisse werden exklusiv angelegt, nicht fortgesetzt
oder überschrieben: Eingabemanifest, ausgewählte Chunks, einzelne Chunk-Ergebnisse,
reguläre Extraction-/Consolidation-JSONs, Konfiguration und Reports. JSONs durchlaufen
normale Modell-Roundtrips. Bei Abbruch können unvollständige Testläufe verbleiben;
für einen neuen Versuch ist ein anderes neues Verzeichnis erforderlich.

`supervision.json` ist der Gesamtstatus mit Prozesslaufzeit, Timeout, Exitcode und
verfügbarem Worker-Ergebnis. `worker_result.json` enthält Provider, angefordertes
Modell, Antwortmodell soweit verfügbar, Promptversion/Hash, Initialisierungsdauer,
Chunk-Laufzeiten, Request-/Retry-Zähler, reservierte Tokens, native API-Usage,
HTTP-Status soweit erhalten sowie Validierung/Fehlerklasse. Ein Worker-Erfolg allein
überschreibt keinen Timeout oder fehlgeschlagenen Prozess-Exitcode.

Promptversion `knowledge_extraction_v1`, SHA-256 der unveränderten Instruktionen:
`6b1e7609d4be14987a610439d0d82b4ebe91853164c2cdf969c7843748c0ff92`.

## Offline-Regressionen und verbleibende Blocker

Neue Tests prüfen Fake-LLM-Antworten, echte PR-5-Quellenbindung, Aussagen/Formeln und
Consolidation, zweifache begrenzte Requests, HTTP-/Timeoutfehler ohne Retry,
Tokenbudget vor Netzwerk, beschädigtes JSON/Schema, Refusal/Truncation, CLI-Limits,
API-Autorisierung, exklusives Speichern, Produktionspfad-/Symlink-Ablehnung und den
kompletten Offline-Lauf im frischen Subprozess ohne API-Zugang.

Der ältere Smoke-Testsatz: **8 bestanden, 1 fehlgeschlagen**.
`test_installed_provider_configuration_without_api` benötigt das hier nicht
installierte `openai`-/Pydantic-AI-SDK und scheitert mit `ModuleNotFoundError`.
Dieser Test wird nicht als bestanden oder still übersprungen dargestellt. Die
bestehenden Prozessgruppen-/Enkelprozess-Timeouttests sind bestanden.

Die sechs bekannten TXT-Importerfehler bleiben ein separater unveränderter Blocker
(`None`-Zeitstempel gegen `TranscriptSegment` mit `float`-Feldern); kein TXT-Fallback
und keine Zeitmodelländerung. Der neue SRT-/HTTPX-Pfad benötigt weder diese Korrektur
noch die LLM-Extras. Reale Qualität, API-Berechtigung, Tokenverbrauch und Marvin-
SDK-/SQLite-Laufzeit sind vor einem tatsächlichen autorisierten API-Pilot unbestätigt.

## Separat aktivierbare CLI

Aus dem Repository, mit jeweils neuem Ausgabeverzeichnis:

```bash
# Offline: keine API-Keys und kein Marvin nötig
uv run --offline --no-sync python -m scripts.cs50_knowledge_pilot \
  --plan docs/course_sources/cs50/cs50_lecture_plan.v1.json \
  --manifest docs/course_sources/cs50/cs50_python_week0_knowledge_input.v1.json \
  --output /tmp/cs50-python0-offline-manual --max-chunks 1
```

```bash
# Separat: nur Marvin-Import, isolierter DB-Pfad, keine LLM-Requests
uv run --offline --no-sync python -m scripts.cs50_knowledge_pilot \
  --plan docs/course_sources/cs50/cs50_lecture_plan.v1.json \
  --manifest docs/course_sources/cs50/cs50_python_week0_knowledge_input.v1.json \
  --output /tmp/cs50-python0-marvin-manual --probe-marvin --timeout 10
```

**Nur manuell nach eigener ausdrücklicher Freigabe**, mit zuvor sicher gesetztem
`OPENAI_API_KEY` (nicht in den Befehl oder Reports schreiben):

```bash
uv run --offline --no-sync python -m scripts.cs50_knowledge_pilot \
  --plan docs/course_sources/cs50/cs50_lecture_plan.v1.json \
  --manifest docs/course_sources/cs50/cs50_python_week0_knowledge_input.v1.json \
  --output /tmp/cs50-python0-llm-manual --provider openai_http \
  --model gpt-4o-mini --max-chunks 1 --timeout 45 \
  --output-limit 1200 --token-budget 60000 --execute-llm
```

`uv --offline` verhindert Paketdownloads, nicht den ausdrücklich freigegebenen
API-POST des Workers. Der echte Befehl wurde von Codex nicht ausgeführt.

### Abschließende Tests

| Testlauf | Ergebnis |
| --- | --- |
| Neue Provider-/Pilot-Tests (finaler Stand) | 19 bestanden, 8,04 s |
| Pilot + PR-5-Bindung + source_id + Formelimport (vor zusätzlichem Pfadtest) | 58 bestanden, 75,45 s |
| Älterer Smoke-Testumfang nach Factory-Importkorrektur | 8 bestanden, 1 SDK-Dependency-Fehler, 5,87 s |
| Ruff Check für alle vier betroffenen Python-Dateien | bestanden |
| Formatprüfung für neue Python-Dateien und Diff-Whitespace | bestanden |

Insgesamt 59 verschiedene neue/unmittelbar beteiligte Knowledge-Tests bestanden,
zusätzlich zu den acht bestandenen älteren Smoke-Fällen. Der verbleibende ältere
SDK-Test ist ausdrücklich als Fehler ausgewiesen. Keine echten API-Calls,
Medien-/SRT-Downloads, SDK-Installationen, produktiven Artefaktänderungen oder
automatischen Merges.

```bash
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python -m pytest tests/test_cs50_knowledge_pilot.py -q
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python -m pytest tests/test_cs50_knowledge_pilot.py tests/test_cs50_knowledge_input.py tests/test_knowledge_source_id.py tests/test_consolidation_math_import.py -q
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python -m pytest tests/test_cs50_llm_smoke.py -q
```
