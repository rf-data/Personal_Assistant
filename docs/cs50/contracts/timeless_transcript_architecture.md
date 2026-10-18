# Zeitlose Transkripte: Architektur und Kompatibilität

**Implementierungsnachtrag C23-05 (18.10.2026):**
[Nullzeitvertrag und Verbrauchermatrix](official_transcript_unknown_time.md)
beschreiben den umgesetzten Modell-/Importerfix und Timed-Guards. Die folgenden
Aussagen zur schon vorhandenen Nullableunterstützung bezogen sich auf den
damaligen Arbeitsstand; im gemergten Master fehlte diese Änderung bis C23-05.
Der nachfolgende zusätzliche Textpfad bleibt ein Entwurf, keine Freischaltung.

Stand: 13.10.2026. Grundlage: lokaler Quellcode und `transcript_import_report.md`.
Dieser Bericht beschreibt einen Entwurf; er aktiviert keinen Verarbeitungspfad und
ändert keine Funktionen, Modelle oder vorhandenen JSON-Dateien. Keine LLM-Aufrufe.

## Entscheidung

Ein **zusätzlicher, ausdrücklich aktivierter Textpfad** soll offizielle TXT-Transkripte
mit echten Textankern verarbeiten. Der bestehende Zeitpfad bleibt der Standard.
Textpositionen sind Zeichenpositionen, keine Sekunden; unbekannte Zeiten bleiben `null`.
Visuelle Verifikation ist ohne verlässliche Medienzeit nicht ausführbar. Ihr Bedarf
bleibt als ungelöste Review-Anforderung erhalten, statt als erledigt zu gelten.

Der erste Implementierungs-PR sollte nur einen reinen, separat aufrufbaren
Text-Chunker mit neuen Zwischenverträgen und Offline-Tests liefern. Die Integration
in Extraction, Consolidation, RAG und Visual-Rebuild benötigt weitere gezielte
Anpassungen. Nur `TranscriptChunk.start/end` optional zu machen wäre nicht sicher.

## 1. Bestand: Wo werden Zeiten benötigt?

| Baustein / Funktion | Tatsächliche Zeitannahme | Behandlung im Textpfad |
|---|---|---|
| `find_knowledge.build_transcript_chunks` | Guard gegen fehlende Zeiten; berechnet `current[-1].end - current[0].start`, schneidet nach `target_duration` | Unverändert für Zeitpfad; eigener Text-Chunker |
| `TranscriptSegment`, `TranscriptDocument` | Import erlaubt bereits explizite Nullzeiten; Dokumentdauer optional | Unverändert weiterverwenden; Quelldokument nicht umschreiben |
| `TranscriptChunk` | Pflichtwerte `start/end: float` | Erst separater TextChunk, später kontrollierte gemeinsame Schnittstelle |
| `KnowledgeEvidence` | Pflichtzeiten; Basisklasse von KnowledgeStatement, MathExpression und ConsolidatedEvidence | Für integrierte Textextraktion nullable Zeiten plus Textanker erforderlich |
| `attach_chunk_provenance` | Kopiert Segment-IDs, Start/Ende in Aussagen und Formeln | Zeitpfad bleibt; Textpfad muss auch Anker/Quellenidentität kopieren |
| `make_visual_candidate`, `VisualCandidate` | Konstruktor erwartet numerische Chunk-Zeiten | Zeitlose Chunks erzeugen keine ausführbaren VisualCandidates |
| `consolidate_knowledge.build_statement_evidence/build_formula_evidence` | Übertragen Zeit-/Segmentfelder in ConsolidatedEvidence | Textanker müssen zusätzlich weitergereicht werden |
| `consolidate_knowledge.evidence_overlaps` | Gemeinsame Segment-ID genügt; sonst numerischer Intervallvergleich | Quellidentität prüfen; im Textpfad Textintervalle verwenden |
| `semantic_knowledge.get_statement_time_range` | `min/max` über Evidenzzeiten; ohne Evidenz `inf` | Eigene Textsortierung; keine Ersatzzeiten oder inf als gespeicherte Zeit |
| `build_semantic_statement_batches` | Sortiert zeitlich, begrenzt Anzahl und Sekunden-Spanne | Textreihenfolge und Wort-/Anzahlbudget statt Sekunden |
| `statement_to_llm_payload` | Ruft zeitabhängigen Range-Helper auf | Textpayload benötigt eigene Lokatoren; nicht unverändert aufrufbar |
| `merge_statement_evidence`, `merge_statement_evidence_from_canonical`, `merge_exact_canonical_statements` | Sortieren nach Evidenzstart/-ende bzw. minimaler Startzeit | Deterministischer Textanker-/Quellen-Sortierschlüssel |
| `rebuild_knowledge.evidence_overlaps_interval`, `evidence_time_range`, `evidence_time_windows` | Vergleiche, `min/max`, Sortierung, Sekunden-Merge-Gap | Nur vollständig zeitlokalisierte Evidenz berücksichtigen; Text nicht als Zeit interpretieren |
| `select_visual_verification_targets` | Candidates und Review/Formel-Evidenz werden zu Zeitfenstern | Zeitlose Reviews als blockiert dokumentieren, nicht als Videoziel erzeugen |
| `merge_visual_verification_targets`, `compile_download_windows`, `intervals_overlap` | Sortierung und Arithmetik auf Sekundenintervallen | Unverändert auf validierte zeitliche Ziele begrenzen |
| `get_batch_target_ids`, `get_batch_knowledge`, `add_frame_timestamps`, `build_visual_batches` | Verknüpfen Frame-/Videozeiten mit Ziel- und Evidenzintervallen | Für zeitlose Quellen kein automatischer Aufruf |
| `run_knowledge_improvement.visual_enrichment` | Ziele → lokale Medien oder Video-Download → Frames | Text-only-Routing muss vor Medienauflösung und Ausführung greifen |
| `run_record_upload.build_rag_records_from_transcript` | Verwendet den bisherigen Zeit-Chunker | Zusätzlicher Text-RAG-Pfad erforderlich |
| `build_rag_records_from_knowledge`, `build_formula_rag_records` | `min/max` der Evidenzzeiten, Zeitmetadaten | Gemischte Null-/Float-Listen vermeiden; Textanker und bekannte Zeiten getrennt exportieren |

Auch vollständig zeitgestempelte Untertitel können überlappende Cues enthalten.
Der bisherige Chunker nimmt als Ende das letzte Segmentende, nicht zwingend das
Maximum aller Enden. Ebenso ist `current[-seg_overlap:]` bei Überlappung `0` kein
leerer Rest (`-0 == 0`), und `max_duration` wird derzeit nicht zur Begrenzung benutzt.
Dies sind vorhandene Eigenschaften, keine Änderungen dieses Vorschlags. Ein neuer
Text-Chunker soll diese Eigenschaften nicht kopieren; der alte Zeitpfad wird deshalb
aber nicht beiläufig korrigiert.

## 2. Wiederverwendbare Textfunktionen und Grenzen

`enrich_chunks` verwendet nur Textreihenfolge und vorherige/nächste Textzeilen. Seine
Logik kann ohne Zeitwissen arbeiten, sobald die Schnittstelle einen TextChunk zulässt;
die aktuelle Annotation nennt noch `list[TranscriptChunk]`. Die Kontextfenster sind
Interpretationshilfe und dürfen nicht als Chunk-Evidenz oder Textspanne gezählt werden.

Der bestehende Extraction-Prompt verlangt Wissen aus `target_chunk`, mit Kontext nur
zur Interpretation. `extract_knowledge` erhält im tatsächlichen Aufruf Text und
Nachbarkontext; Start/Ende sind auskommentiert. Prompt und fachliche Klassifikation
benötigen daher keine Zeiten. `analyze_and_extract_chunk` ist dennoch nicht insgesamt
unverändert verwendbar: Payload/Cache referenzieren die bisherigen Chunk-Felder, und
das erwartete Ergebnis enthält zeitgebundene KnowledgeEvidence. Der Textpfad muss
Cache-Version, Schema und Provenienzbindung ausdrücklich behandeln. Kein LLM soll
Textpositionen oder Zeiten erfinden; der Anwendungscode setzt die Quellanker.

`validate_extraction` filtert leere fachliche Ergebnisse und markiert visuell unsichere
Formeln als `pending`; diese Logik ist textfähig. `statement_score`, `expression_score`,
`merged_verification_status`, Text-/LaTeX-Normalisierung und Ähnlichkeitsberechnung
sind zeitunabhängig. Die umgebende Duplicate-Gruppierung ist erst nach Anpassung des
Evidenzvergleichs sicher. Deep-Copies von Evidenz können unverändert bleiben, sofern
neue Felder tatsächlich im Modell und in sämtlichen Buildern erhalten werden.

`run_knowledge_extraction.knowledge_extraction` lädt das bestehende TranscriptDocument,
konfiguriert Marvin bereits vor der Quelleinstufung, baut Chunks, extrahiert Wissen,
hängt Evidenz an und erzeugt VisualCandidates. Für Integration: Quelle/Policy vor
LLM-Konfiguration validieren, gezielt Chunker wählen und zeitlose visuelle Wünsche
separat protokollieren. Sein Dateinamen-basierter `source_id` ist für prüfbare
Quellenidentität allein unzureichend. Die URL eines offiziellen TXT-Imports ist eine
Transkript-URL, nicht automatisch die URL des zugehörigen Videos.

**Zusätzliche bestehende Vertragslücke:** TranscriptKnowledgeDocument deklariert im
aktuellen Code keinen `source_id`. Der Runner übergibt ihn beim Konstruktor, Pydantic
ignoriert ihn jedoch, während `consolidate_knowledge` später `document.source_id`
verwendet. Eine lokale Modellprobe bestätigt dies. Ein Integrationstest muss diese
Lücke separat absichern; sie darf nicht als TXT-Problem verborgen bleiben. Eine
spätere additive Deklaration darf Alt-JSON ohne source_id nicht unlesbar machen:
fehlende Identität explizit aus vertrauenswürdigem Kontext auflösen oder Integration
mit verständlichem Fehler ablehnen, keinen unbelegten Default erzeugen.

## 3. Textanker, Segment-IDs und Provenienz

### Referenztext und Positionen

Referenz ist der **exakte normalisierte Text des importierten Dokuments**, nicht die
ursprüngliche Bytefolge. Offizieller TXT-Import verbindet Segmenttexte mit `\n\n`.
Der Text-Chunker prüft im ersten PR exakt diese Konsistenz; abweichende oder nur
teilweise rekonstruierbare Dokumente werden mit einem Grund abgelehnt. Andere
Legacy-Normalisierungen brauchen später einen eigenen versionierten Adapter.

Offsets sind Python-Unicode-Codepoint-Indizes, nullbasiert, halboffen `[start, end)`.
Sie sind weder UTF-8-Bytes noch JavaScript-UTF-16-Indizes. Kein erneutes Trimmen,
Unicode-Normalisieren oder Zusammenziehen von Whitespace nach dem Festlegen der
Offsets. Ein Chunk muss exakt dem Slice des Referenztextes entsprechen. Unterschiedliche
Bytecodierungen können denselben normalisierten Text liefern; das wird bewusst von
der Originaldatei-Provenienz unterschieden.

Pro Textanker vorgeschlagen:

- `source_id`: deterministische Identität der logischen Quelle, etwa aus Original-URL,
  Sprache und Ressourcenformat; lokale Dateinamen und acquired_at sind keine IDs.
- `text_sha256`: Hash des exakten normalisierten UTF-8-Textes; Änderung invalidiert Anker.
- `normalization_version`: z. B. `official_txt_v1`; keine implizite Migration.
- `char_start/char_end`: globales Intervall im Dokumenttext.
- `segment_spans`: geordnete Liste aus `seg_id`, lokalem `char_start/char_end` innerhalb
  des jeweiligen Segmenttexts. Separatoren zwischen Segmenten gehören zum globalen
  Slice, aber zu keinem Segment.

Segment-IDs des Imports bleiben unverändert. Beim Aufteilen langer Absätze wird dieselbe
`seg_id` mit verschiedenen lokalen Spannen referenziert, nicht künstlich neu vergeben.
Segment-IDs sind nur innerhalb einer Quelle eindeutig. Reihenfolge folgt der
Segmentliste; numerische IDs müssen nicht sortiert oder fortlaufend sein. Keine
Textsuche ab Dokumentanfang: wiederholte Absätze sind über die fortlaufend berechnete
Position und Segmentreferenz eindeutig zu verorten.

Chunk-ID deterministisch aus Quelle, Text-Hash, Algorithmusversion, allen Chunking-
Parametern und Textspanne ableiten. Identischer Text an zwei Stellen muss verschiedene
IDs ergeben. Wiederholte Läufe auf unveränderter Quelle/Policy sind stabil; geänderte
Quelle oder Policy bilden eine neue Chunking-Revision. Bestehende `chunk_0000`-IDs
zeitbasierter Daten werden nicht rückwirkend ersetzt.

### Evidenz und Herkunft

Provenienz bleibt am Quelldokument erhalten: Original-URL, Sprache, Format,
`official_transcript`, Quelldatei, acquired_at. Ein neues Chunking-Ergebnis speichert
zusätzlich die referenzierte Quellenrevision und die Chunking-Policy; keine Whisper-
Metriken. Die spätere Knowledge-Ausgabe muss diese Informationen bzw. eine stabile
Referenz darauf bis zur Consolidation erhalten, nicht nur die URL.

`attach_chunk_provenance` sollte später geprüfte Textanker in Aussagen und Formeln
kopieren. Das ist **Chunk-Evidenz**, keine behauptete genaue Belegstelle innerhalb des
Chunks. Genauere Item-Spannen benötigen eine separate validierte Zuordnung. LLM-
Antworten dürfen geprüfte Anker nicht überschreiben. Neue Evidenzfelder müssen durch
build_statement_evidence/build_formula_evidence und alle Materialisierungen reichen.

Für zeitlose Duplicate-Erkennung: zuerst gleiche Quelle **und Textrevision** prüfen,
dann tatsächliche Textspanne vergleichen. Überlappung bedeutet `a.start < b.end` und
`b.start < a.end` für halboffene Zeichenintervalle; bloße Berührung genügt nicht.
Gemeinsame Segment-ID allein genügt nicht, wenn zwei Chunks verschiedene Bereiche
desselben langen Absatzes enthalten. Wiederholte Aussage an anderer Position bleibt
eine andere Evidenzstelle; semantische Zusammenfassung muss beide Belege behalten.
Legacy-Zeitevidenz behält ihren bisherigen Vergleich im bestehenden Zeitpfad. Neue
Textverträge ohne ausreichende Anker werden konservativ nicht als überlappend gewertet.

## 4. Minimale Modelländerungen: zwei Stufen

| Vertrag | Erster PR: isoliertes Chunking | Spätere Integration |
|---|---|---|
| TranscriptDocument / TranscriptSegment | Keine Änderung; bereits nullfähige Zeiten | Keine notwendige Änderung; zusätzliche Herkunft über Ergebnis-Envelope |
| Neue TextAnchor / SegmentTextSpan | Hinzufügen als neue kleine Pydantic-Verträge | Für Chunk und Evidenz wiederverwenden |
| Neuer TextTranscriptChunk | Text, n_words, chunk_id, Segment-IDs/-Spannen, Anker, optionaler Kontext; explizit zeitlos | Adapter oder gemeinsame Schnittstelle zum Extraction-Code |
| Neues TextChunkingResult | Quellenrevision/Provenienz, Policy-Version und Chunks | Persistierbarer Quellenbezug für Knowledge-Ausgabe |
| Bestehender TranscriptChunk | Unverändert | Optional `start/end: float | None` plus optionaler Textanker; beide Zeiten gemeinsam bekannt oder unbekannt |
| KnowledgeEvidence und Erben | Unverändert | Gleiche nullable Zeiten und optionaler Textanker; neue Textfälle verlangen Anker |
| VisualCandidate / VisualVerificationTarget / Frame-Modelle | Unverändert numerisch | **Numerisch lassen**; zeitlose Reviews separat von ausführbaren Kandidaten halten |
| Knowledge-Ergebnisdokumente | Unverändert | Optionale Quellenrevision/Provenienz-Referenz; source_id-Vertragslücke beheben |

Die gemeinsame Variante in Stufe 2 vermeidet eine große Union-Migration aller
Knowledge-Erben. Bei optionaler KnowledgeEvidence-Zeit betrifft dies aber auch
`LocalVisualBatchResult` als Erben: visuelle Ergebnisse müssen weiterhin eigene
strenge Zeitvalidierung behalten. Ein globales Aufweichen ohne diesen Audit wäre
gefährlich. Neue Ankerfelder haben Defaults `None`/leere Listen, sodass alte numerische
JSON-Daten ohne neue Felder geladen werden können. Keine Pflicht-Schemaversion oder
neuer Pflicht-Discriminator in Altdateien. Neue Textfälle werden am eigenen Eingang
strikt validiert; Legacy-Dateien dürfen nicht nachträglich einen Textanker benötigen.

Ein optionaler `timing_mode` in einem neuen Ergebnis-Envelope kann `timed`/`text`/
`mixed` kennzeichnen. Für Altdateien wird der Modus anhand vorhandener Segmentdaten
im Verarbeitungskontext ermittelt, ohne die Datei umzuschreiben. Ein neues Feld darf
nicht pauschal `timed` behaupten, wenn der Modus unbekannt ist.

## 5. Verhalten des bestehenden Zeitpfads erhalten

1. `build_transcript_chunks` bleibt für Whisper/SRT/VTT unverändert inklusive
   Segmentauswahl, Chunk-IDs, Überlappung und Fehlern für fehlende Zeiten.
2. Neue Funktion `build_text_transcript_chunks` ist separat; kein stiller Fallback.
   Zeitquellen werden standardmäßig weiterhin ausschließlich zeitbasiert verarbeitet.
3. Spätere Auswahl über explizite Policy, zunächst Default `timed`, opt-in `text` nur
   nach validierter Quelle. Klassifikation und Routing sind getrennt vom Dateisuffix:
   eine JSON-Datei kann zeitlos sein; eine TXT-Herkunft allein beweist keine Timing-Form.
4. Text-Parameter separat: z. B. `target_words=300`, `max_words=450`,
   `overlap_words=0`. Dies sind vorgeschlagene Testdefaults, keine Zeitumrechnung.
   Absätze bevorzugen; überlange Segmente deterministisch an Whitespace-Grenzen teilen.
   Unteilbare überlange Wörter erhalten einen dokumentierten Ausnahmefall oder führen
   zu einem expliziten Fehler, niemals einen Endlosloop.
5. Erst ohne Chunk-Überlappung implementieren; Kontext bleibt getrennt. Spätere
   Überlappung referenziert echte, erneut enthaltene Textspannen. Keine Cue-Deduplizierung.
6. Zeit- und Text-Caches über Algorithmus-/Schemaversion und Policy trennen. Bestehende
   Zeit-Cachekeys und Legacy-IDs beibehalten. Sprache, Quelle und Textrevision gehören
   in neue Text-Cacheidentitäten, nicht acquired_at oder maschinenabhängige Pfade.
7. Keine Migration/Überschreibung alter JSON-Dateien; neue Ergebnisse exklusiv speichern.
   Neue Leser können Alt-JSON laden. Rückwärtslesbarkeit neuer Null-/Ankerdaten durch
   alte Programmversionen wird nicht behauptet.

Im integrierten Textpfad bedeutet ein leerer VisualCandidate-Satz nicht „kein visueller
Bedarf“. Ein getrennter Review-Eintrag muss etwa `visual_unavailable_no_timestamps`
mit Chunk/Item/Anker/Grund festhalten. `pending`/needs_review bleiben erhalten. Erst
nach validierter externer Ausrichtung zu einem Medium kann ein eigener zeitlicher
Verifikationsauftrag entstehen. Keine Ableitung aus Wortzahl, Absatznummer oder Dauer.
Visual-Rebuild muss auch zeitlose Review-/Formelbelege sicher überspringen; nur das
Unterdrücken von make_visual_candidate reicht nicht, weil weitere Targets daraus
entstehen. Der aktuelle „No visual verification needed“-Zweig benötigt dann eine
präzisere Zustandsmeldung für blockierte Prüfungen.

## 6. Gemischte oder teilweise gestempelte Quellen

| Segmentzustand | Klassifikation / Verhalten |
|---|---|
| Alle Segmente haben gültige Start- und Endzeiten | `timed`, bestehender Pfad |
| Alle Segmente haben beide Zeiten `null` | `text`, nur ausdrücklicher Textpfad |
| Ein Segment hat nur einen der beiden Werte | `partial`, standardmäßig ablehnen und Segment-ID melden |
| Zeitsegmente und vollständig zeitlose Segmente nebeneinander | `mixed`, erster PR lehnt ab; kein Überspringen, kein automatischer Fallback |
| NaN/Inf, negative Zeiten oder Ende vor Start | Ungültig; Quelle melden, nicht reparieren oder als zeitlos umdeuten |
| Keine Segmente / leerer Text | Keine sinnvolle Quelle; verständlicher Validierungsfehler |

Später kann `text_all` als explizite Option eine gemischte Quelle vollständig über Text
verarbeiten. Originale bekannte Segmentzeiten bleiben im unveränderten Dokument
gespeichert; der Text-Chunk beansprucht trotzdem keinen durchgehenden Zeitbereich.
Ein min/max über bekannte Teile wäre irreführend, weil die Zeitposition der übrigen
Textteile unbekannt ist. Unvollständige Paare bleiben zunächst Fehler.

Ein komplexerer späterer Hybridpfad könnte maximal zusammenhängende gültige Zeitläufe
und zeitlose Läufe getrennt chunken. Grenzen dürfen nicht überbrückt werden; IDs müssen
laufübergreifend eindeutig sein. Teilweise lokalisierte Evidenz muss ihre Abdeckung
bewahren; Videoziele dürfen nur bekannte Belegteile verwenden. Dieser Hybridpfad ist
kein Bestandteil des kleinen ersten PRs.

## 7. Tests und Integrationskriterien

### Erster Text-Chunking-PR: ohne LLM und ohne bestehende Pipelineimporte

- Bestehendes normalisiertes TXT-Beispiel laden; Quelle bleibt exakt unverändert,
  Zeiten und Dauer bleiben `null`; Herkunft/Sprache/Original-URL erhalten.
- Absätze, Mehrzeilen-Text, Leerraum, Unicode einschließlich Emoji/Combining-Zeichen;
  Jeder Slice `document.text[start:end]` entspricht exakt dem Chunktext.
- Wiederholte Absätze haben verschiedene Anker/IDs; Quell-Segment-IDs und Reihenfolge
  erhalten, auch nicht fortlaufende IDs. Doppelte seg_id im Dokument ablehnen.
- Langer Einzelabsatz wird mit unveränderter seg_id in präzise Teilspannen aufgeteilt;
  kein überaggressives Zusammenführen von Wiederholungen.
- Wortlimits, Grenzfälle, langes unteilbares Wort, leere Quelle, inkonsistenter
  Referenztext, ungültige Policy; begrenzte Laufzeit und keine stillen Textverluste.
- Gesamtabdeckung: kein nichtleerer Quelltext geht verloren; nur explizite Separatoren
  dürfen zwischen Chunk-Slices liegen. Kontext ist nicht Evidenz.
- Stabile IDs bei Wiederholung/anderem lokalen Pfad; andere Quelle, Position,
  Textrevision oder Policy verändert die Identität.
- Gemischte, teilweise oder ungültige Zeitdaten werden ausdrücklich abgelehnt.
- Model-/JSON-Roundtrip; neue Zwischenergebnisse überschreiben keine Datei.
- Netzwerk, Provider-, App-Konfigurations- und LLM-Imports ausgeschlossen.

### Vor Aktivierung von Knowledge Extraction und Consolidation

- Golden-Master-Tests alter Whisper-/SRT-/VTT-Chunks inklusive Zeitwerte, IDs,
  Überlappung 0/1/2, letzte Restchunks und überlappende Cues; keine unbeabsichtigte Änderung.
- Legacy-Transcript/Knowledge/Evidence/Visual-JSON ohne neue Felder weiterhin lesbar;
  neue Nullzeiten samt Ankern durch sämtliche Builder und Erben erhalten.
- Vorbereitungs-/Routingfunktion ohne Marvin testbar; Quelle wird vor LLM-Konfiguration
  geprüft. Nicht aktivierte Textverarbeitung lehnt früh verständlich ab.
- Extraction mit lokalem synthetischem Ergebnis: attach → Consolidation → semantische
  Materialisierung → RAG behält Quelle, Anker, Segment-IDs und Nullzeiten. Keine reale
  LLM-Extraktion erforderlich, um diese Verträge zu testen.
- Evidenzüberlappung: gleiche Revision/überlappender Text, bloße Berührung, verschiedene
  Quellen, lange gesplittete Segmente, getrennte Wiederholungen und fehlende Anker.
- Semantische Textbatches haben stabile Textreihenfolge/Größenlimits und rechnen keine
  Sekundenspannen; bestehende Zeitbatches bleiben unverändert.
- Bekannte Zeitfenster und zeitlose Anker koexistieren ohne None-Sortierfehler;
  RAG min/max nur über vollständig bekannte Paare und separate Textlokatoren.
- Source-ID im TranscriptKnowledgeDocument überlebt Konstruktion, Speichern und Laden;
  Alt-JSON ohne ID wird explizit und nachvollziehbar behandelt.
- Visueller Bedarf zeitloser Quellen bleibt sichtbar/blockiert; keine Targets,
  Medienauflösung, Downloads, Frame-Auswahl oder LLM-Aufrufe. Auch indirekte Targets
  aus needs_review/Formelbegründungen müssen ausgeschlossen sein.
- Zeitfähige Visual-Modelle/LocalVisualBatchResult akzeptieren weiterhin ausschließlich
  reale Zeitintervalle; zeitgestützte visuelle Verarbeitung bleibt regressionsgeprüft.

## Vorschlag für den kleinen ersten Implementierungs-PR

Titel: **Add isolated text chunking for official untimed transcripts**.

Neue kleine Verträge in einem unabhängigen Modul, eine reine Chunking-Funktion,
ein optionaler exklusiver JSON-Saver, synthetische Tests und ein normalisiertes
Chunking-Beispiel. Abhängigkeiten ausschließlich Standardbibliothek und Pydantic.
Keine Änderung an build_transcript_chunks, KnowledgeEvidence, VisualCandidate,
Extraction-Runner, Loviscach, Discovery oder Selection. Keine automatische Taskplanung.

Der PR beweist den Textanker-/Chunking-Vertrag, schließt aber noch keine vollständige
Knowledge-Integration ab. Folge-PRs: (1) nullable Chunk-/Knowledge-Evidenz und
Provenienz-Binding samt Quellen-ID, (2) Text-Consolidation/RAG und sichere Visual-
Abgrenzung, (3) opt-in Runner-Routing erst nach bestandenen Kompatibilitätstests.
Ein produktiver Textpfad darf nicht aktiviert werden, solange Folgestufen Nullzeiten
noch als Zahlen verwenden oder Provenienz verlieren.

## Durchgeführte Analyseprüfung

Quelltexte der genannten Modelle, Importer, Chunking-/Extraction-Funktionen,
syntaktischen und semantischen Consolidation, Visual-Rebuild sowie RAG-Export lokal
geprüft. Eine isolierte Pydantic-Probe bestätigt die bestehende source_id-Vertragslücke.
Keine Produktionsmodule mit LLM-/Whisper-Ausführung importiert und keine Pipeline
gestartet. Die oben genannten Tests sind vorgeschlagene Anforderungen für künftige
Implementierung, keine Behauptung über bereits ausgeführte Integrationstests.
