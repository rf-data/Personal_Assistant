# Portable CS50-Pilot-Testfixtures

Stand: 14. Oktober 2026. Basis: origin/master `3e99a06` einschließlich
Fixture-PR #21. Implementiert und geprüft in einem frischen separaten Worktree,
ohne lokale Original-SRTs, normalisierte Transkripte oder Execution-Belege.

## Änderung und Identifikation

Die acht bisherigen Testfehler lagen in drei Modulen:

| Modul | Bisher fehlgeschlagene Fälle |
|---|---|
| test_cs50_knowledge_pilot | test_fake_llm_full_pilot_binding, test_fake_worker_two_chunks |
| test_cs50_precise_evidence | test_full_pilot_preserves_source_and_consolidates, test_invalid_provider_saved_no_precise_output |
| test_cs50_quality | drei erfolgreiche Bereichsauswahlen (20/1, 20/2, letzter Chunk/1) und Provider-Sidecar-/Voll-Chunk-Vergleich |

Sie verwendeten `docs/course_sources/cs50/cs50_python_week0_knowledge_input.v1.json`
und darüber lokal erzeugte absolute Artefaktpfade. Das Dokument ist bewusst kein
versioniertes Testfixture: Es bindet den produktiven Originalpilot.

`tests/conftest.py` erzeugt jetzt für die ausdrücklich benannten Pilotfälle unter
`tmp_path` einen eigenen Workspace. Nach den bestehenden Settings-/Socket-
Guards werden der echte CS50AdapterPlan und CS50Executor geladen. Fake-HTTP
liefert 500 synthetische UTF-8-SRT-Cues mit eigenen bekannten Testzeiten und
zwei unterschiedlichen Python-Beispieltexten. Diese Testzeiten sind Teil der
synthetischen Quelldaten, keine im Importer oder Chunker erfundenen Zeitmarken.

DOWNLOAD und PARSE_SUBTITLE laufen tatsächlich im Fake-Executor: Der bestehende
offizielle Importer erzeugt TranscriptDocument und Execution-Belege, anschließend
prüft bind_cs50_knowledge_input Identitäten, Hashes und Provenienz. Das regulär
gespeicherte CS50KnowledgeInputManifest und die echten Chunking-Ergebnisse werden
dem jeweiligen Test bereitgestellt. Es gibt keine Modell-Stubs für diese Stufen.
Die bestehende echte deterministische Consolidation und JSON-Roundtrips bleiben
Teil der bisherigen Pilot-/Präzisionstests.

Nur die benötigten Testmodul-Konstanten ROOT und MANIFEST werden innerhalb der
jeweiligen pytest-Funktion mit monkeypatch auf den temporären Kontext gebunden
und danach zurückgesetzt. Produktionsmodule werden nicht umkonfiguriert. Die
Fixture wird insbesondere nicht für Produktionspfad-/Symlink-Tests aktiviert:
Sie benötigen weiterhin den echten CLI-ROOT-Vertrag. Ein erster zu breiter
Fixture-Entwurf verletzte genau diese Testannahme; die Aktivierung ist deshalb
auf die ausdrücklich benannten Pilotfälle begrenzt.

Der frühere Standalone-Audithelper delegiert jetzt direkt an dieselben pytest-
Fixtures. Er erzeugt keine zweite Artefaktfabrik und kein globales Variablen-
Overlay mehr.

## Erhaltene Abdeckung

- Chunk 20, ein und zwei Chunks, letzter Chunk sowie ungültiger Überlauf.
  Die Grenzen kommen aus der tatsächlichen synthetischen Chunkanzahl; weder
  die ursprünglichen 157 Chunks noch Originalpilot-Zeiten sind vorausgesetzt.
- Echter synchroner CLI-Subprozess ohne LLM-Freigabe, Request-/Zeit-/Tokenlimits,
  Autorisierungsgate und bereits bestehende Prozessgruppen-Timeout-Tests.
- Roh-Provider-Sidecars vor Legacy-Postprocessing; vollständige Chunk-Evidenz
  im Legacy-Modus und getrennte validierte Segment-Evidenz in segment_v1.
- Unbekannte, doppelte, leere und fremde Segmentreferenzen sowie falsche
  Modellzeiten; kein präziser Fallback für ungültige Referenzen.
- Quellenbindung, Modelle, JSON-Roundtrip und echte Consolidation.

Der neue `test_offline_local_original_pilot` bewahrt den früheren lokalen
CLI-Originaltest separat und überspringt ausdrücklich bei fehlendem Manifest.
Die bestehenden optionalen Original-SRT-/Importtests im Executor und Knowledge-
Eingang bleiben unverändert. Keiner davon erhält synthetische Ersatzartefakte.
Der Originalpilot wurde in diesem sauberen Checkout nicht getestet und sein
Produktionsverhalten wurde nicht geändert.

## Reproduktion und Umgebung

Verwendet wurde die reguläre bestehende uv-Worker-Umgebung mit Python 3.12.12,
pytest 9.1.1 und Pydantic 2.13.4. Kein Sync, keine Dependency-Installation und
keine Upgrades. Der vorher dokumentierte Offline-Sync-Blocker durch ungecachte
spaCy-Wheel-Metadaten bleibt bestehen. Die Tests benötigen kein LLM-SDK.

```bash
# Vorhandene installierte Worker-Umgebung; Code aus dem frischen Worktree.
UV_PROJECT_ENVIRONMENT=/path/to/worker/.venv UV_CACHE_DIR=/tmp/cs50-uv-cache \
  uv run --offline --no-sync python -m pytest tests -q --junitxml=/tmp/portable-all.xml

UV_PROJECT_ENVIRONMENT=/path/to/worker/.venv UV_CACHE_DIR=/tmp/cs50-uv-cache \
  uv run --offline --no-sync python -m pytest \
  tests/test_cs50_knowledge_pilot.py tests/test_cs50_precise_evidence.py \
  tests/test_cs50_quality.py -q
```

Alle generierten Artefakte bleiben in pytest-Temp-Verzeichnissen. Keine festen
Maschinenpfade, Original-SRTs, produktiven Transcript-/Execution-Dateien oder
echten API-Keys werden versioniert. API-Antworten sind Fake-HTTP bzw. bestehende
Fake-Provider. Der reguläre CLI-Test hat keine execute-llm-Freigabe; in Fake-
Provider-Tests bleibt die echte Netzwerkgrenze gesperrt. Marvin wird nicht geladen.

## Getrennte, unveränderte Blocker

| Gruppe | Erwartete bekannte Fälle | Ursache / eigener Folge-PR |
|---|---|---|
| TXT | 6 | Import liefert unbekannte Zeiten None, TranscriptSegment verlangt float; nullable Zeitvertrag und explizite zeitbasierte Chunking-Ablehnung fehlen. |
| Provenienz | 14 | Fehlende transcript_metadata()-Methode/Validatoren und Metadatenweitergabe im allgemeinen Runner bzw. semantischen Ergebnisvertrag. |
| Lazy-Imports | 4 | llm_helper lädt optionale SDKs weiterhin eager; das vorhandene SDK-freie Pilot-HTTP-Modul wird hierdurch nicht korrigiert. |
| SDK-Smoke | 1 | OpenAI-SDK in der verwendeten Worker-Umgebung nicht installiert. Optionales Extra/Testmatrix separat behandeln. |

Diese Produktions-/Abhängigkeitsprobleme werden weder repariert noch durch
Test-Stubs verdeckt. Discovery, Selection, Download-/Import-, Chunking- und
Consolidation-Funktionsmodule bleiben unverändert. Keine API-/LLM-/Whisper-
Aufrufe, keine echten Medien-Downloads und keine produktiven Datenänderungen.

## Tatsächlich ausgeführte Ergebnisse

Gesamtlauf: **336 passed, 25 failed, 0 errors, 3 skipped**, 364 Fälle in
362,03 Sekunden. Die acht Pilotfehler sind beseitigt; die 25 Fehler gehören
ausschließlich zu den vier oben getrennten Altgruppen.

Der zusätzliche optionale CLI-Originaltest wurde nach Collection des Gesamtlaufs
ergänzt und im abschließenden Drei-Modul-Lauf mitgeprüft: **46 passed, 1 skipped**,
47 Fälle in 72,08 Sekunden. Der Standalone-helper bestand mit **5 passed** in
30,08 Sekunden. Keine dieser Summen wird als vollständig grüne Gesamtsuite ausgegeben.

Ruff-Lint und Formatprüfung aller vier betroffenen Python-Dateien sowie
git diff --check bestanden. Keine Dateien unter src/ oder scripts/ wurden geändert.

| Modul | Passed | Failed | Error | Skipped |
|---|---:|---:|---:|---:|
| test_consolidation_math_import | 1 | 0 | 0 | 0 |
| test_cs50_discovery | 30 | 0 | 0 | 0 |
| test_cs50_executor | 32 | 0 | 0 | 1 |
| test_cs50_extraction | 44 | 0 | 0 | 0 |
| test_cs50_fixture_checkout | 2 | 0 | 0 | 0 |
| test_cs50_full_coverage | 10 | 0 | 0 | 0 |
| test_cs50_knowledge_input | 27 | 0 | 0 | 1 |
| test_cs50_knowledge_pilot | 19 | 0 | 0 | 0 |
| test_cs50_lecture_adapter | 30 | 0 | 0 | 0 |
| test_cs50_llm_smoke | 8 | 1 | 0 | 0 |
| test_cs50_precise_evidence | 18 | 0 | 0 | 0 |
| test_cs50_quality | 9 | 0 | 0 | 0 |
| test_cs50_selection | 24 | 0 | 0 | 0 |
| test_cs50_six_courses | 9 | 0 | 0 | 0 |
| test_cs50_srt_knowledge_integration | 5 | 0 | 0 | 0 |
| test_cs50_timed_selection | 19 | 0 | 0 | 0 |
| test_cs50_uv_installed_integration | 0 | 0 | 0 | 1 |
| test_knowledge_source_id | 11 | 0 | 0 | 0 |
| test_knowledge_transcript_provenance | 5 | 14 | 0 | 0 |
| test_lazy_marvin_import | 0 | 4 | 0 | 0 |
| test_official_transcript_import | 33 | 6 | 0 | 0 |
