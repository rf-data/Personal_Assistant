# Optionaler präziser Evidenzmodus im CS50-Pilot

## Vertrag und Kompatibilität

`--evidence-mode segment_v1` aktiviert die versionierte Eingabe
`cs50_segment_evidence_v1`. Der Default `chunk` bleibt unverändert. Die
fachlichen Extraktionsinstruktionen, Ergebnismodelle, Whisper-Helfer und
deterministische Consolidation wurden nicht verändert.

Die Eingabe enthält die tatsächlichen Original-Cues des ausgewählten Chunks
einzeln mit `seg_id`, `start`, `end` und `text`, außerdem den bisherigen
Chunktext und Nachbarkontext. Der Provider soll pro Aussage und Formel nur die
belegenden `segment_ids` zurückgeben. Das angepasste Ausgabeschema verlangt
Referenzen; es fordert keine Modellzeiten oder Quellenmodalität mehr an.
Nachbarkontext darf keine Referenzen außerhalb des Zielchunks begründen.

Der neue Modus ist für `openai_http` verfügbar. Eine Kombination mit Marvin
wird ausdrücklich abgelehnt. Bestehende Provider- und CLI-Defaults bleiben
erhalten; Request-, Retry-, Token-, Chunk- und Subprozesslimits gelten weiter.

## Prüfung und Quellenbindung

`bind_precise_candidates()` behandelt die Providerantwort als ungeprüfte
Kandidaten. Referenzen müssen nicht leere Listen echter Integer-IDs sein,
dürfen keine Duplikate enthalten und müssen zu nicht leeren Originalsegmenten
des Zielchunks gehören. Fremde Chunk-IDs, Quellenidentitäten, unbekannte
Ergebnisfelder und eine abweichende Modalität werden abgelehnt. Es gibt keinen
Voll-Chunk-Fallback für ungültige Referenzen. Die gesamte Chunkantwort schlägt
dann fehl; gültige Teilantworten werden nicht als erfolgreiches Ergebnis
veröffentlicht.

Die validierten IDs erhalten die Originalreihenfolge. Start und Ende sind das
Minimum beziehungsweise Maximum der referenzierten Original-Cues. Modellzeiten
werden ignoriert. Nicht zusammenhängende Belegstellen bleiben durch ihre IDs
unterscheidbar; ihr Zeitintervall umfasst auch die Lücken. Es entstehen keine
künstlichen Zeitmarken.

Die Bindung wird erneut in `build_cs50_knowledge_document()` anhand des
hashgeprüften TranscriptDocument und der geprüften Eingabebindung validiert.
`source_id`, `transcript_url`, Sprache, Kurs-/Vorlesungszuordnung, `media_id`
und TranscriptProvenance stammen weiterhin ausschließlich aus diesem Kontext.
`resource_id` und Abschnitt bleiben zusätzlich im Eingabemanifest und den
externen Bindungen erhalten. `KnowledgeEvidence.source` bleibt `transcript`;
dies ersetzt nicht die Herkunftsstrategie `official_subtitle`.

## Vergleich der Granularität

Die folgende kleine synthetische Syntaxfixture testet Referenzbindung, nicht
fachliche Extraktionsqualität und keine erfundenen Gold-Aussagen:

| Ergebnis | Default: IDs / Zeit | segment_v1: IDs / Originalzeit |
|---|---|---|
| Aussage S1 | 10, 11, 12 / 1–6 s | 10 / 1–2 s |
| Aussage S2 | 10, 11, 12 / 1–6 s | 11 / 3–4 s |
| Formel F1 | 10, 11, 12 / 1–6 s | 12 / 5–6 s |

Der Offline-Integrationstest nutzt außerdem Chunk 20 des vorhandenen echten
CS50-Python-Woche-0-Transkripts. Fake-HTTP liefert zwei wörtliche Original-Cue-
Texte mit unterschiedlichen Referenzen. Die reguläre Dokumenterstellung,
JSON-Speicherung und deterministische Consolidation erhalten diese Belegstellen.
Dies ist ein echter Quellen-/Pipeline-Test mit synthetischer Providerantwort,
kein neuer LLM-Lauf und keine Bewertung eines echten präzisen LLM-Ergebnisses.

## Audit und Fehlerausgaben

Die unverarbeiteten Providerfelder bleiben in `<chunk_id>.provider.json`
erhalten, auch bei ungültigen Segmentreferenzen. Erfolgreiche Bindungen werden
separat in `evidence_bindings.v1.json` gespeichert, einschließlich geprüfter
Quellenidentität, Transcript-Hash, referenzierter IDs und abgeleiteter Zeiten.
Bei ungültigen Kandidaten entsteht ein Fehler-/Qualitätsreport und kein
normalisiertes `extraction.json`.

`cs50_quality_v2` unterscheidet pro Aussage und Formel:

- `statement_precise`: exakte Übereinstimmung mit dem geprüften Bindungsaudit
  derselben Quelle; auch Formeln verwenden diesen gemeinsamen Scope-Namen.
- `chunk_only`: kein entsprechender geprüfter Präzisionsnachweis. Auch eine
  lediglich im JSON vorhandene ID-Teilmenge wird konservativ so eingestuft.
- `invalid`: unzulässige Referenzen oder ungültige Zeit-/Chunkzuordnung.

Der separate Report-CLI kann das Audit über `--evidence-bindings` laden und
prüft dessen Version sowie Quellenidentität. Das Audit ist eine lokale
Validierungsaufzeichnung, keine kryptografisch signierte Beglaubigung. Es
ersetzt weder erneute Quellenprüfung noch semantische Entailment-Prüfung.

## Offline-Verifikation

Reproduzierbarer Aufruf in der installierten lokalen uv-Umgebung:

```bash
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python -m pytest \
  tests/test_cs50_precise_evidence.py tests/test_cs50_quality.py \
  tests/test_cs50_knowledge_pilot.py tests/test_cs50_knowledge_input.py -q
```

Die Tests decken echte Segmentteilmengen, getrennte Aussagen/Formelbelege,
fehlende und fremde IDs, leere Cues, Duplikate, falsche Quellenmodalität,
fremde Chunk-/Quellenreferenzen, ignorierte Modellzeiten, JSON-Roundtrip,
Rohantwortspeicherung, echte Quellenbindung und unveränderten Legacy-/Whisper-
Voll-Chunk-Modus ab. HTTP ist ausschließlich Fake-HTTP; es erfolgen keine
API-, Marvin-, Whisper- oder Netzwerkaufrufe und keine produktiven Schreibzugriffe.

Ergebnis des Abschlusslaufs: **74 bestanden in 92,78 Sekunden**, davon 18
Tests des neuen Präzisionsmodus. Python 3.12.12 / pytest 9.1.1; Ruff meldet
für alle sieben beteiligten Python-Dateien `All checks passed!`.

Der Stack basiert auf PR #19 (`feat/cs50-pilot-quality-selection`), da dessen
Chunk-Auswahl und Qualitätsreport vorausgesetzt werden. Die lokal vorhandenen
Pilot-/Planfixtures sind weiterhin Voraussetzung der Integrationssuite.

## Nutzung ohne API-Freigabe

```bash
uv run --offline --no-sync python -m scripts.cs50_knowledge_pilot \
  --plan docs/course_sources/cs50/cs50_lecture_plan.v1.json \
  --manifest docs/course_sources/cs50/cs50_python_week0_knowledge_input.v1.json \
  --output /tmp/cs50-precise-offline-new \
  --provider openai_http --chunk-index 20 --max-chunks 1 \
  --evidence-mode segment_v1 --timeout 45 --output-limit 1200 --token-budget 60000
```

Ohne `--execute-llm` bleibt dieser Aufruf offline. Ein späterer ausdrücklich
freigegebener API-Lauf ist weiterhin erforderlich, um zu beurteilen, ob das
Modell tatsächlich passende Belegstellen liefert. Bestätigt ist die bisherige
Überschreibung durch Voll-Chunk-Provenienz und der neue deterministische
Validierungs-/Bindungsvertrag. Ob präzise Referenzen den Lernwert der Aussagen
verbessern, bleibt offen; die fachlichen Relevanzinstruktionen sind unverändert.
