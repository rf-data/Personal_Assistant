# Erster echter Pilot: Qualität, Evidence und explizite Chunk-Auswahl

## Geprüfter Stand und Grenzen

Analysiert wurden ausschließlich vorhandene lokale Ergebnisse unter
`/home/robfra/0_Portfolio_Projekte/_test_folder/cs50-python0-llm-manual` sowie die
bestehende geprüfte CS50-Python-Woche-0-SRT. Der echte API-Lauf wurde vom Nutzer
zuvor ausgeführt; Codex hat keinen neuen API-Aufruf gestartet und diese Dateien
nicht verändert. Keine `.env`-Inhalte oder API-Keys wurden ausgegeben;
sämtliche neu gestarteten Piloten liefen offline oder über Fake-Provider.

`worker_result.json`: ein Request, 3316 Prompt-Tokens, 491 Completion-Tokens,
3807 Gesamt-Tokens; angefordert `gpt-4o-mini`, Antwortmodell
`gpt-4o-mini-2024-07-18`, 6,058 s Requestlaufzeit, 9,493 s Workerlaufzeit.
Extraction und deterministische Consolidation enthalten jeweils sechs Statements,
keine Formeln. Modelle und Quellenbindung haben den Lauf erfolgreich validiert.
Das beweist syntaktische/strukturelle Gültigkeit, nicht automatisch Lernwert oder
statement-spezifische fachliche Belegbarkeit.

## Bestätigte Beobachtungen versus Hypothesen

| Kategorie | Beobachtung / Aussage | Nachweis |
| --- | --- | --- |
| Bestätigtes Verhalten / Granularitätsdefizit | Alle sechs Statements erhalten identische Segment-IDs und Zeiten des ganzen Chunks, unabhängig von ihren ursprünglichen Evidence-Feldern | `attach_chunk_provenance`: bedingungslose Zuweisungen für jede Aussage und Formel; Quellzitat-Test belegt Verlust eines tatsächlich kleineren Segment-Subsets |
| Bestätigte Beobachtung | Vier Statement-Topics fehlen; keine exakten Textduplikate | vorhandenes `extraction.json`, deterministische Zählung |
| Fachliches Qualitätsproblem | Begrüßung/Kursbezeichnung, Sprecher-/Wochenvorstellung, Annahme über das Publikum und bloßer Übergang haben hier geringen Konzept-Lernwert | tatsächliche sechs gespeicherte Texte, nicht künstlich erzeugte Gold-Aussagen |
| Fachliches Qualitätsproblem | „which is just a very popular program nowadays“ ist isoliert unspezifisch; „So let's start by doing just that“ enthält keine eigenständige fachliche Aussage | tatsächliche Texte; Pydantic prüft weder Aussagevollständigkeit noch pädagogischen Nutzen |
| Offene Hypothese | Ein fachlicher Chunk statt Kursintro liefert bessere Konzept-Statements | Chunk 20 enthält fachlichen Input-Text; keine neue echte LLM-Extraction durchgeführt |
| Offene Hypothese | Eine präzisere Relevanzdefinition verbessert den Prompt | bisher keine kontrollierte Prompt-Variante oder Gold-Evaluation; Prompt bleibt unverändert |
| Nicht rekonstruierbar | Welche Segment-IDs/Zeiten das LLM im ersten Lauf wirklich ausgegeben hat | nur nachgebundene Ergebnisse gespeichert; kein Provider-Sidecar bzw. roher HTTP-Response vorhanden |

Es ist deshalb falsch, aus den gleichartigen gespeicherten Evidenzen auf gleichartige
**LLM-Ausgaben** zu schließen. Die Ursache der Gleichförmigkeit im Endergebnis ist
bereits deterministisch erklärt. Eine ursprünglich präzise Antwort würde ebenfalls
zu Voll-Chunk-Evidence umgeschrieben.

## Instruktionen, Modellfähigkeit und überschreibende Schritte

`build_knowledge_extraction_prompt()` verlangt relevante, zuverlässige, vollständig
im `target_chunk` belegte Aussagen, keine Ergänzungen aus Kontext/externer Mathematik
und die passende semantische Kategorie. Er beschreibt Belegbarkeit, aber keine
operationalisierte Mindestanforderung an Konzept-Lernwert bzw. eine explizite
Ausschlussliste für Kursintro/Publikumsansprache/Moderation. „relevant“ allein ist
keine reproduzierbare pädagogische Bewertungsregel.

HTTP-Provider: `messages_for()` sendet target_chunk als unnummerierten Text, optionalen
Kontext und das bestehende Ergebnisschema. Es liefert **keine Zuordnung von tatsächlichen
Segment-IDs zu einzelnen Cue-Texten und Zeiten**. Das Schema erlaubt eine
`segment_ids`-Liste sowie `start/end`, macht deren Herkunft jedoch nicht überprüfbar.
Ein Modell könnte IDs raten oder pauschale Zeiten liefern; das ist keine sichere
Grundlage für präzise Belege.

Vorhandene Modelle unterstützen bereits unterschiedliche Referenzen pro Aussage:
`KnowledgeStatement` und `MathExpression` erben `KnowledgeEvidence(segment_ids,
start, end, source)`. `ConsolidatedEvidence` ergänzt `chunk_id/item_id` und kann
unterschiedliche Belege weiterreichen. Eine neue fachliche Ergebnisarchitektur ist
für eine ausgewählte Teilmenge tatsächlicher Cue-IDs nicht erforderlich. Die Modelle
allein prüfen aber nicht die Existenz von IDs im SRT oder fachliches Entailment.

Aktuelles Post-Processing:

1. Pilot setzt Analysis-/Extraction-Chunk-ID auf die geprüfte lokale Chunk-ID.
2. `build_cs50_knowledge_document` kopiert den Ergebnisvertrag und prüft Input,
   Artefakte, Chunk-Referenzen und Provenienz erneut.
3. `attach_chunk_provenance` überschreibt **für jedes Statement und jede Formel**
   `segment_ids`, `start`, `end`, `source` mit vollständigen Chunk-IDs/-Zeiten und
   Modalität `transcript`. Bereits vorhandene Referenzen werden nicht erhalten.
4. `validate_extraction` entfernt leere Inhalte und markiert ggf. visuellen
   Prüfbedarf, erstellt aber keine präzisere Evidence und bewertet keinen Lernwert.
5. Deterministische Consolidation übernimmt die gebundenen Evidence-Referenzen;
   sie ist nicht der Ursprung der Granularität.

Course/Lecture/Resource/Source-IDs, SRT-URL, Sprache und vollständige
TranscriptProvenance stammen unverändert aus dem geprüften Eingang, nicht vom LLM.
`KnowledgeEvidence.source` bleibt Modalität, `official_subtitle` bleibt Herkunft.

## Minimaler Folgeentwurf für präzise Evidence — hier nicht implementiert

Separater opt-in Evidence-PR nach Review dieser Ursache:

* Den ausgewählten Chunk zusätzlich als Liste echter Cue-Datensätze mit unveränderten
  `seg_id`, `start/end`, `text` bereitstellen. Dann kann das LLM Referenzen auswählen,
  statt Positionen oder Zeiten zu erfinden. Das ist eine bewusst zu versionierende
  Eingabe-/Promptänderung, keine Änderung in diesem Auftrag.
* Modellseitige Referenzen als **Kandidaten**, nicht als geprüfte Wahrheit betrachten.
  Nur nicht leere, eindeutige, tatsächlich existierende IDs innerhalb des ausgewählten
  Chunks erlauben; leere Cues dürfen keine inhaltliche Evidence liefern.
* Zeitgrenzen ausschließlich aus den referenzierten Originalsegmenten ableiten
  (min Start / max Ende), keine Modellzeitstempel übernehmen oder Zwischenzeiten
  schätzen. Original-Segment-IDs unverändert erhalten.
* source_id, course/lecture/resource-ID, URL, Sprache, Modalität und TranscriptProvenance
  weiterhin ausschließlich aus geprüften Bindungen setzen. Das LLM darf diese Identität
  nicht bestimmen. Die kleinere Evidence darf diese Prüfungen nicht umgehen.
* Fehlende/ungültige Referenzen explizit als unpräzise oder Fehler behandeln.
  Ein bewusst erlaubter Voll-Chunk-Fallback muss im Report als `chunk_only` erkennbar
  bleiben und darf nicht als statement-präzise Evidence ausgegeben werden.
* Legacy-/Whisper-Verhalten durch einen expliziten optionalen Modus erhalten;
  Default bleibt das bisherige gebundene Chunk-Verhalten. Tests: gültige Teilmengen,
  erfundene/duplizierte/außerhalb liegende IDs, stille Cues, fremde Quelle, widersprüchliche
  Modellzeiten, JSON-Roundtrip und unterschiedliche Consolidation-Evidenzen.

Auch eine korrekte Cue-Teilmenge ist noch kein automatischer Beweis, dass die Aussage
inhaltlich folgt. Dafür wird später ein getrenntes, manuell belegtes Qualitäts-/Eval-
Verfahren benötigt. In diesem PR werden weder Prompt noch Evidence-Algorithmus geändert.

## Implementierte kleine Erweiterungen

### Explizite Auswahl

`--chunk-index` ist der **nullbasierte Startindex** im Ergebnis des unveränderten
Chunkers; Default `0`. `--max-chunks 1|2` wählt ein oder zwei aufeinanderfolgende
Chunks ab dort. Damit ist z. B. 20/21 möglich, nicht nur 0/1. Keine Neuordnung,
Renummerierung oder Auswahl anhand des Dateinamens.

Negativer Index wird vor Erzeugung des Ausgabeverzeichnisses abgewiesen. Ein zu
hoher Index bzw. nicht ausreichend viele verbleibende Chunks scheitert nach Prüfung
und Auswahl **vor Provider-Initialisierung/API-Request**. Bestehende Konfigurations-
JSONs ohne chunk_index verwenden weiterhin 0. Request-/Retry-/Zeit-/Tokenlimits,
6000-Zeichen-Grenze, Prozessgruppen-Timeout und API-Opt-in bleiben unverändert.
Der Chunker bildet weiterhin die vorhandene Metadatenliste; nur ein/zwei ausgewählte
Chunks werden als Knowledge-Input verarbeitet. Keine Vollkurs-Extraction.

### Unüberschriebene Provider-Felder als neuer Sidecar

Künftige Läufe schreiben `<chunk_id>.provider.json` vor Chunk-/Evidence-Zuweisungen,
mit `model_dump(exclude_unset=True)`. Damit bleiben tatsächlich gesetzte Felder des
bereits Pydantic-validierten Provider-Ergebnisses sichtbar; nicht gesetzte Defaults
werden nicht als LLM-Angaben ausgegeben. Es ist **kein byteidentischer roher HTTP-
Response**, sondern die validierte Modellrepräsentation. Offline-Sidecars sind
synthetische Verträge, keine LLM-Ausgaben. Keine nachträgliche Änderung des ersten
realen Piloten und keine Wiederherstellung seiner verlorenen Originalfelder.

### Deterministischer Qualitätsreport

`src/tools_knowledge/cs50_quality.py`, automatisch als `quality_report.json` in neuen
Pilotläufen und separat read-only über `scripts.report_cs50_quality` ausführbar.
Keine LLM-, Netzwerk- oder Konfigurationsinitialisierung im Reportmodul.

| Kennzahl des ersten realen Laufs | Wert | Interpretation |
| --- | ---: | --- |
| Statements / Formeln | 6 / 0 | tatsächliche Ergebnisse |
| Statements in als irrelevant markierten Chunks | 0 | analysis.relevant war true; **nicht** „alle sechs sind relevant“ |
| Niedrig-Lernwert-Proxys | 5 | transparente englische Muster für Intro, Publikumsannahme, Übergang, vage Popularität; keine Gold-Labels |
| Fehlende Statement-Topics | 4 | fehlend/null/leer, ohne automatische Topic-Vererbung |
| Exakte Textduplikate, überzählige Vorkommen | 0 | Normalisierung nur Case/Whitespace; keine semantische Duplikatentscheidung |
| Voll-Chunk-Evidence / Gesamt | 6 / 6 | 100 % grobe Evidence |
| Unterschiedliche Evidence-Signaturen | 1 | Chunk-ID + Segmentliste + Zeiten |
| Ungültige Referenzen relativ zum Chunk | 0 | syntaktische ID-/Range-Prüfung, keine fachliche Belegprüfung |
| Dokument-Pydantic / gespeicherter LLM-Workerstatus | gültig / reported_valid | keine neue LLM-Validierung des ursprünglichen Responses |

Heuristiken sind versioniert (`cs50_quality_v1`), verändern/filtern keine Statements
und gelten nur als nachvollziehbare Screening-Proxys. Wiederholte Textaussagen können
auch didaktisch sinnvoll sein; der Report führt sie nicht automatisch zusammen.
Ohne Evidence wird die Granularitätsquote `null`, nicht eine erfundene Nullbewertung.

## Fachlicher Offline-Test mit realen lokalen Cue-Texten

Index **20**, `chunk_0020`, Zeiten **792,44–837,44 s** (ca. 13:12–13:57):
Passage über den Argumentparameter von `input`, das Ersetzen eines separaten `print`-
Prompts und die Interaktion mit dem Terminal. Diese Themen wurden direkt im
Originaltranskript gefunden, nicht als Gold-Aussagen erfunden.

Offline-CLI-Lauf unter `/tmp/cs50-concepts-quality-index20` erfolgreich, null Requests.
Ein weiterer Test liefert über eine Fake-Provider-Grenze ein **wortgetreues Zitat von
originalen Cue-Texten** mit deren tatsächlichen drei Segment-IDs/Zeiten. Er prüft
speziell, dass das neue Sidecar diese Teilmenge erhält, während die unveränderte
Evidence-Bindung sie weiterhin auf den vollen Chunk erweitert. Dieser Test beweist
Datenfluss und Auswahl, nicht eine echte LLM-Qualitätsverbesserung. Keine erfundenen
Referenzantworten, Gold-Labels oder kostenpflichtigen Calls.

Tests zusätzlich: letzter Index 156 erfolgreich; Index 157 ohne Request abgewiesen;
negativer Index vor Ausgabeerzeugung abgewiesen; Proxy-/Topic-/Duplikatmetriken;
Default-Pilot und PR-5-Bindung unverändert. Eingabefiles bleiben unverändert.

## Reproduzierbare Befehle

Vorhandenen realen Lauf nur lesen, Report in eine neue Datei schreiben:

```bash
uv run --offline --no-sync python -m scripts.report_cs50_quality \
  --extraction /home/robfra/0_Portfolio_Projekte/_test_folder/cs50-python0-llm-manual/extraction.json \
  --chunks /home/robfra/0_Portfolio_Projekte/_test_folder/cs50-python0-llm-manual/chunks.json \
  --worker-report /home/robfra/0_Portfolio_Projekte/_test_folder/cs50-python0-llm-manual/worker_result.json \
  --output /tmp/cs50-first-real-quality-new.json
```

Fachlichen Abschnitt **offline**, ohne API-Key oder --execute-llm auswählen:

```bash
uv run --offline --no-sync python -m scripts.cs50_knowledge_pilot \
  --plan docs/course_sources/cs50/cs50_lecture_plan.v1.json \
  --manifest docs/course_sources/cs50/cs50_python_week0_knowledge_input.v1.json \
  --output /tmp/cs50-python0-concepts-offline-new \
  --chunk-index 20 --max-chunks 1 --timeout 45
```

Unveränderter Prompt-SHA-256:
`6b1e7609d4be14987a610439d0d82b4ebe91853164c2cdf969c7843748c0ff92`.
Reale Extraction des Konzeptabschnitts bleibt eine später separat freizugebende
Probe, ebenso Änderungen an Relevanzinstruktionen oder präziser Evidence.

Bekannte Checkout-/Fixture- und optionale SDK-Probleme aus dem Integrationsbericht
bleiben getrennte Voraussetzungen; sie werden nicht durch neue Architekturänderungen
in diesem Qualitäts-PR verdeckt. Lokale Originalpilot-/Manifesttests benötigen den
vorhandenen geprüften lokalen Stand. Keine produktiven Artefakte, Discovery,
Selection, Download, SRT-Import oder fachliche Knowledge-Modelle verändert.

## Abschließende Validierung und PR-Basis

**56 Tests bestanden, 72,51 s** in der tatsächlichen lokalen uv-Umgebung:
9 neue Quality-/Auswahlfälle, 19 bestehende Provider-/Pilotfälle und 28 vorhandene
Knowledge-Eingangs-/Provenienzfälle. Der Test mit zwei Chunks ab Index 20 und der
unzulässige Zwei-Chunk-Bereich ab 156 sind ebenfalls enthalten. Ruff Check/Format
für alle vier betroffenen Python-Dateien und Diff-Whitespace bestanden.

```bash
UV_CACHE_DIR=/tmp/cs50-uv-cache uv run --offline --no-sync python -m pytest tests/test_cs50_quality.py tests/test_cs50_knowledge_pilot.py tests/test_cs50_knowledge_input.py -q
```

Der PR richtet sich direkt gegen den überprüften aktuellen `master`
`bd5491e63966f5bb3d53593f06604dcadf5bfc98`, der den PR-6-Code bereits durch einen
Sammelcommit enthält. Nur fünf Dateien dieses Qualitätsauftrags gehören zum Diff;
der vorherige separate GitHub-Integrationsbericht bleibt unberührt. Die bekannten
fehlenden versionierten JSON-/HTML-Fixtures des master sind eine bestehende
Integrationsvoraussetzung, nicht in diesem kleinen PR stillschweigend behoben.
Kein Merge, Promptwechsel, Download, SRT-Import oder neuer echter LLM-Aufruf.
