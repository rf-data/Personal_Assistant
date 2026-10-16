# C12 – Knowledge Consolidation Hardening

C12 ersetzt das Testticket C07. Grundlage ist `master` bei `09f7384`;
C10-/C11-Artefakte, produktive Daten und optionale LLM-SDKs sind nicht erforderlich.

## Tatsächlicher Ablauf und nachgewiesene Schwachstellen

Die Geschäftsmodelle stehen unverändert in
[`data_knowledge.py`](../src/model_knowledge/data_knowledge.py):
`TranscriptKnowledgeDocument` enthält `ChunkKnowledgeResult` mit `ChunkAnalysis`
und optionalem `KnowledgeExtract`. Statements und Formeln tragen Segment-IDs,
Zeitintervalle, Herkunft und optional Confidence. Dokumentmetadaten verbinden
Course, Lecture, Source, URL, Sprache, Media und `TranscriptProvenance`.
`source_id` ist am alten Extraktionsmodell optional; Konsolidierung benötigt eine
explizite Identität. Eine URL ersetzt keine verifizierte Source-ID.

Bisheriger Kursrunner:

1. Konfigurierten Knowledge-Ordner rekursiv nach `*_know_extract.json` durchsuchen.
2. Ohne Sortierung pro Datei verarbeiten; im Ausgabeordner auf den Basename
   `*_know_consol.json` abbilden. Unterordner werden dabei abgeflacht.
3. Existiert die Ausgabe, ohne Inhaltsprüfung überspringen.
4. `consolidate_knowledge` erzeugt `ConsolidatedKnowledgeDocument`.
5. `consolidate_semantic_knowledge` erzeugt über semantische Batches und
   Entity-Extraktion `LectureKnowledgeDocument`; Cache über Input, Prompt, Modell
   und Schema. `save_dict` publiziert anschließend die Datei.

Nachgewiesene Probleme und gezielte Korrekturen:

| Befund | Korrektur / Nachweis |
| --- | --- |
| Existenz-Skip prüfte weder Identität noch Inhalt oder Konfiguration | Receipt, Hashes und vollständige Output-Validierung; Resume-Matrixtests |
| Unsortierte Dateiauswahl und kollidierende Basenames | Sortierte, pfadweise deduplizierte Auswahl; Kollisionen vor Veröffentlichung melden |
| Satznormalisierung entfernte `+`/`-` und Case; Fuzzy-Matching konnte Negation übergehen | Nur konservativ exakte Matches mit gleichem Typ/Topic zusammenführen; Operator-, Case- und Negationstests |
| Formelvergleich war unscharf, Normalisierung verlor Case/Superskriptunterschiede | Beide Darstellungen, Typ und Name müssen konservativ exakt übereinstimmen; Exponenten-, Index-, Unicode- und Bruchtests |
| Identische Fakten mit disjunkter Evidence blieben mehrfach stehen | Exakte Duplikate innerhalb eines Source-Dokuments vereinigen, beide Evidence-Belege erhalten |
| Evidence wurde allein nach Chunk-/Item-ID dedupliziert | Vorher widersprüchliche Identitäten ablehnen; semantische Hilfsfunktionen bewahren unterschiedliche vollständige Evidence-Werte |
| `verified` gewann stillschweigend gegen `rejected` | Beide Belege/Begründungen behalten, Status `pending`, Konflikt im Report |
| Semantischer Cache-Hit umging ID-Validierung; doppelte Zuordnungen blieben unbemerkt | Cache-Ergebnisse ebenfalls validieren; doppelte/inventierte Statement-Zuordnungen ablehnen |
| Pydantic setzt fehlendes `acquired_at` auf aktuelle Zeit | Audit verlangt expliziten Zeitstempel bei vorhandener Provenienz; keine zeitabhängigen Defaults im Replay |

Die neuen Tests verwenden echte Konsolidierungsfunktionen und ausschließlich
synthetische Extrakte. Semantische Funktionen werden gemäß bestehender
Testkonvention isoliert aus dem Modul geladen; SDK-, Cache- und Providergrenzen
sind Testdoubles. Live-LLM-Verhalten ist damit ausdrücklich **nicht** nachgewiesen.

## Gehärtete Übergabekette

**Input → Selection → Consolidation → Validation → Storage**

- Input: explizite lokale Pfade unter `input_root`, striktes JSON ohne doppelte
  Schlüssel/NaN, bestehendes Pydantic-Extraktionsmodell. SHA-256 der Originalbytes.
- Selection: sortierte eindeutige absolute Pfade, optionale Course-/Lecture-Filter
  anhand deklarierter IDs. Mehrere unabhängige Sources je Lecture bleiben eigene
  Dokumente. Gleiche Source-ID in mehreren Inputs oder gleiche Basenames werden
  blockiert: ein stilles Zusammenfügen würde den bestehenden ID-Vertrag verletzen.
- Consolidation: vorhandene deterministische Stufe. Bestehende Parameter
  `statement_similarity`/`expression_similarity` bleiben aufrufbar, autorisieren
  jedoch keine unscharfen Merges mehr. NFC und Rand-Whitespace werden
  normalisiert; bei Formeln ohne TeX-Kommandos zusätzlich ASCII-Leerzeichen um
  explizite Operatoren/Klammern. Case, Operatoren, Ziffern, Indizes und
  Superskripte bleiben signifikant; `x y` bleibt verschieden von `xy`.
- Validation: Course/Lecture/Source müssen im Kursaudit vorhanden sein;
  Chunk-Identitäten, Analyse-/Extraktionsverknüpfung, Item-Identitäten,
  Segmentreferenzen, endliche geordnete Zeitintervalle, Confidence und Inhalte
  werden geprüft. Relevante Chunks ohne Extraktion sind unvollständig/ungültig.
  Fehlende Akquisitionsprovenienz bleibt als Warnung sichtbar, ohne Ergänzung.
  Entities/Relations/Summary der Extrakte werden wie bisher nicht in die
  deterministische Ausgabe projiziert; der Report warnt bei solchen Feldern.
- Output: Metadaten und Visual Candidates müssen unverändert bleiben. Die
  vollständigen Evidence-Werte müssen jeden relevanten Input-Beleg genau einmal
  abdecken, getrennt nach Statements/Formeln. Deterministische Ausgabe muss dem
  neu berechneten Ergebnis entsprechen. Bei semantischen Ergebnissen zusätzlich:
  jede deterministische Statement-ID genau einmal zugeordnet oder explizit
  verworfen, Evidence passt zu dieser Zuordnung, Entity-Referenzen existieren,
  Formeln sind unverändert. Verworfene Statements behalten Evidence.
- Storage: standardmäßig keine Ausgabe und kein Lock/Ordner. Bei explizitem
  `write=True` POSIX-`flock` für den Ausgabeordner; vorhandenes `atomic_json`
  (`fsync` + exklusiver Hardlink) für Prepared-Receipt, Ausgabe und Completed-Marker.
  Kein Ersetzen bestehender Artefakte. Eingabehash unmittelbar vor Veröffentlichung
  erneut prüfen. Ein Fehler blockiert andere gültige Sources/Lectures nicht;
  `KeyboardInterrupt` bleibt sichtbar und beendet den Lauf.

Das bestehende CS50-Chunk-Checkpoint-Modell hat Request-/Budget-/Providerzustände
und eine andere Identität. Es wird nicht zweckentfremdet. Wiederverwendet werden
`Contract`, `encoded`, `fingerprint`, `atomic_json` sowie `safe_path` aus der
vorhandenen SRT-Ausführung. Die neuen Modelle beschreiben ausschließlich Audit
und Publikationsbelege, keine neuen Knowledge-Objekte.

## Identitäten und Kompatibilität

`KS0001…`, `KF0001…` und semantische `CS0001…` behalten ihr Format und ihre
Scope: Identität ist **(course_id, lecture_id, source_id, Objekttyp, Objekt-ID)**.
Die Chunk-/Item-ID referenziert die Originalextraktion. Reihenfolge und IDs sind
für denselben geordneten Dokumentinhalt stabil; sie sind keine Content-Hashes.
Eine inhaltliche Änderung, neue Gruppierung oder geänderte Chunk-Reihenfolge
kann IDs verschieben. Das neue konservative Matching kann neue Ergebnisse
gegenüber früheren Fuzzy-Merges ändern; bestehende Dateien werden nicht migriert.

`ConsolidatedKnowledgeDocument` und `LectureKnowledgeDocument` bleiben lesbar.
Der Offline-Pfad publiziert `*_know_deterministic.json`, damit er nicht mit
semantischen `*_know_consol.json` verwechselt wird. `process_course_knowledge`
und `process_knowledge_file` behalten ihre bisherigen Positionsargumente;
beide sind nun standardmäßig lesend und liefern Ergebnis/Report zurück.
`run_knowledge_consolidation()` liest weiterhin eine konfigurierte Kursauswahl,
führt aber nur den Audit aus. Die CLI verlangt explizite Pfade. Auch der frühere interaktive Demo-Einstieg
in `consolidate_knowledge` delegiert jetzt an diese CLI; seine hartcodierten
Ausgabepfade und impliziten SDK-Aufrufe entfallen.

Die semantische Stufe bleibt erhalten. Ein bewusst bereitgestellter Callable
`semantic_stage(document=..., model_name=...)` kann die bestehende Funktion
anbinden und muss `LectureKnowledgeDocument` liefern. Kursläufe benötigen dann
zusätzlich `semantic_contract` als versionierten Fingerprint-Vertrag für
Prompts, Schema, Provider und alle weiteren semantischen Einstellungen. Die CLI
bietet keinen Live-LLM-Schalter; Dry-Run ruft diesen Callable nicht auf. Tests
belegen den Übergang mit der echten Materialisierung und einem deterministischen
Providerdouble. Einzeldatei-Helfer haben keinen Resume-Vertrag; dafür den
Kursrunner verwenden.

## Resume-/Skip-Vertrag v1

Pro Ausgabe `X.json` gibt es unveränderliche Belege
`X.json.prepared.v1.json` und `X.json.completed.v1.json`. Der Prepared-Beleg bindet
Input-/Outputpfad, Course/Lecture/Source, Inputbytehash, Konfigurationshash und
Outputbytehash. Der Completed-Beleg stimmt bis auf `phase` exakt damit überein.
Nur der Runner-eigene `.consolidation.lock` ist ein zusätzliches Betriebsartefakt.

| Beobachtung | Status und Verhalten |
| --- | --- |
| Gültiger neuer Input, kein Artefakt | `pending` im Audit; `completed` nach expliziter Veröffentlichung |
| Prepared vorhanden, Ausgabe fehlt oder ist korrekt, Completed fehlt | `pending` / `resume_prepared`; Schreiben reproduziert den Hash und vervollständigt ausschließlich fehlende Artefakte |
| Alle Belege korrekt, Input/Config unverändert, Output valide | `skipped` / `verified_completed`; kein Stage-Callable und keine Artefaktänderung |
| Bewusst nicht ausgewählte Lecture/Course | `skipped` / `not_selected`, `selected=false` |
| Input oder Konfiguration gegenüber Prepared geändert | `stale`; keine Adoption/Änderung, neuen Ausgabeordner wählen |
| Fehlender Input, kaputtes JSON, falsche Referenzen, kollidierende Identitäten | `invalid`; weitere Inputs weiterprüfen |
| Kaputter Beleg/Output, abweichender Hash, Completed mit fehlendem Output | `invalid`; keine automatische Reparatur/Überschreibung |
| Bestehender Output ohne Prepared-Beleg, auch mit gültigem alten Schema | `invalid`; lesbar, aber Herkunft des Laufes nicht verifiziert |
| Stage wirft Laufzeitfehler | `failed`; Fehler mit Input-Bezug, Kurs wird weitergeführt |

Es gibt keinen veränderlichen Kurscache. Beschädigte frühere semantische
Batchcaches werden durch die bestehende Stage validiert; beschädigte neue
Publikationsbelege sind `invalid`. Die sechs Reportstatus sind Beobachtungen
eines Laufes, keine Umbenennung der bestehenden Request-Checkpointstatus.
Ein unterbrochener Lauf lässt Prepared/Output zur erneuten Prüfung zurück;
erzeugt er noch keinen Beleg, bleibt er bei der nächsten Prüfung `pending`.

Keine impliziten Löschungen, kein Force-/Overwrite-Schalter und keine
Altartefakt-Adoption. Ersatz produktiver Ergebnisse ist ein separat zu planender
Vorgang; dieses Paket erzeugt dafür nur neue Ausgaben in einem neuen Ordner.
Die atomare Hilfsfunktion räumt lediglich ihre eigenen temporären Dateien auf.

## CLI und Reportvertrag

Im Repository mit bereits installierter Umgebung, ohne Netz/API-Schlüssel:

```bash
python -m src.run_knowledge_consolidation \
  --input-root tests/fixtures/consolidation/synthetic_course \
  --input tests/fixtures/consolidation/synthetic_course/lecture0_notes_know_extract.json \
  --input tests/fixtures/consolidation/synthetic_course/lecture0_captions_know_extract.json \
  --output-root /tmp/new-consolidation-c12 \
  --course synthetic-calculus --lecture lecture0 \
  --report /tmp/new-consolidation-c12-report.json
```

Für neue Ausgaben zusätzlich `--write`. Ein JSON-Report wird ausschließlich auf
expliziten `--report`-Pfad geschrieben. Sein Elternordner muss existieren, der
Pfad muss außerhalb beider Artefaktwurzeln liegen. Vorhandene Dateien werden vor
Verarbeitung abgewiesen und auch beim finalen Schreiben exklusiv geschützt.
Exitcodes: `0` für erfolgreiche Prüfung/Publikation (auch Warnungen), `1` für
`failed`/`invalid`/`stale`, `2` für CLI-/globale Pfad-/Lock-/Reportkonflikte.

[`RunReport`](../src/tools_knowledge/consolidation_run.py) hat `schema_version=1`,
Konfiguration, Schreibmodus, geordnete `inputs`, abgeleitete `counts` und
`report_sha256`. Jeder Input nennt Status/Entscheidung, Pfade, Identitäten,
Hashes, Zählwerte sowie Befunde mit Severity, Code, Chunk-/Item-Referenz und Text.
JSON ist UTF-8, sortierte Schlüssel, kompakte Separatoren, ein abschließender LF;
keine Laufzeitstempel. `report_sha256` ist SHA-256 dieser kanonischen Darstellung
**ohne** das Feld `report_sha256`. Input-/Outputhashes betreffen Datei-Bytes.
Im Dry-Run ohne Datei ist der Outputhash der Hash der vorgeschlagenen Ausgabe.
Gleiche Eingaben, Konfiguration, Pfade und Artefaktzustände erzeugen denselben
Report. Ein erfolgreicher Schreibdurchlauf und dessen Wiederholung haben
absichtlich unterschiedliche Entscheidungen (`completed` gegenüber `skipped`).

Zählerdefinitionen:

- `lectures_examined`: eindeutige bekannte (Course,Lecture)-Paare, einschließlich
  nicht ausgewählter gültiger Inputs. Nicht parsebare Identitäten werden nicht geraten.
- `inputs_examined`: eindeutige Pfade; `inputs_selected`: alle nicht ausdrücklich
  ausgeschlossenen Inputs, einschließlich nicht identifizierbarer defekter Dateien.
- `objects_processed`: nichtleere Statements/Formeln relevanter Chunks, deren
  Konsolidierung erfolgreich geprüft wurde, auch bei Dry-Run oder verifiziertem Skip.
- `duplicates` und `objects_merged`: Raw-Anzahl minus deterministisch verbliebene
  Gruppen. Beide sind hier gleich, da ausschließlich exakte Duplikate vereinigt
  werden. Sie behaupten keine zusätzlichen semantischen LLM-Merges.
- `objects_remaining`: tatsächlich verbliebene Statements/Formeln der betrachteten
  Ausgabe; bei einer externen semantischen Stage nach deren Verarbeitung.
- `conflicts`: Anzahl Befunde mit `conflict` im Code; umfasst echte
  Identitäts-/Verifikationskonflikte und ausdrücklich nur mögliche inhaltliche
  Konflikte. Kein Anteil „nachgewiesen falscher Aussagen“.
- `missing_evidence_references`: Befunde dieses Codes (Chunk/Item/Segment/Visual),
  keine geschätzte Anzahl fehlender Transkriptsegmente.
- `warnings`/`errors`: Anzahl entsprechender Befunde. Statuszähler zählen Inputs.
  Vor erfolgreicher Ergebnisprüfung sind Objektzähler null; es werden keine
  Verarbeitungsleistungen aus ungültigen Dateien behauptet.

Der [Beispielreport](examples/consolidation-run.v1.json) stammt aus dem Dry-Run
aller vier synthetischen Fixtures. Nur Pfade wurden auf portable relative
Referenzen umgestellt; anschließend wurde der Reporthash neu berechnet. Es
zeigt zwei Lectures, vier Quellen, 32 geprüfte Objekte, 24 verbleibende Objekte
und acht exakte Duplikate. Es ist keine Modellqualitätsmessung.

## Grenzen und nächster Integrationsschritt

- Deklarierte Course-/Lecture-Zuordnung wird auf Konsistenz im Lauf geprüft;
  ohne externen Kurs-/Transkriptbeleg ist ihre Authentizität nicht beweisbar.
  Segmentexistenz im Originaltranskript und vollständige Chunk-Abdeckung eines
  realen Kurses lassen sich aus Extrakten allein ebenfalls nicht beweisen.
- Ähnlichkeit >= 0,8 erzeugt lediglich Review-Kandidaten für verschiedene
  Statements/Formeln. Sie beweist weder Widerspruch noch Äquivalenz und findet
  nicht alle Konflikte. Paarvergleich ist quadratisch; keine große Skalierung
  oder automatische semantische Konfliktauflösung behauptet.
- Keine Merges zwischen unterschiedlichen Source-Dokumenten. Gleiche Fakten
  über Sources hinweg bleiben separat referenzierbar; doppelte Source-Inputs
  werden zur expliziten Klärung blockiert.
- Bestehende semantische LLM-Stufe bleibt fachlich probabilistisch. Die Prüfung
  schützt Identitäten/Evidence, beweist aber nicht die Wahrheit umformulierter
  Aussagen. Fehlende Batchzuordnungen werden wie bisher verlustfrei im
  Materialisierungs-Fallback behalten; doppelte Zuordnungen werden abgewiesen.
- POSIX-Locks und Hardlinks setzen ein geeignetes lokales Dateisystem und
  kooperierende Writer voraus. Symlinks und `..` werden abgewiesen. Schutz
  gegen einen Angreifer, der gleichzeitig Elternverzeichnisse austauscht, ist
  kein behaupteter Vertrag. Dry-Run liest eine Momentaufnahme ohne Schreiblock.
- Hashes belegen Konsistenz, keine kryptografisch authentifizierte Herkunft.
  Receipts sind an absolute Pfade gebunden; Umzug erfordert einen neuen Lauf.
- `semantic_contract` muss vom aufrufenden Adapter vollständig versioniert
  werden. Das Paket führt keinen produktiven Provider, Request-Retry oder neue
  Prompt-/Cache-Architektur ein. Teilweise publizierte semantische Ergebnisse
  werden nur bei reproduziertem Hash vervollständigt.

Empfehlung: Als Nächstes den bestehenden verifizierten Lecture-Completion-Beleg
als expliziten Input zum Kursaudit binden. Damit lassen sich erwartete Chunks,
Original-Segmentreferenzen und Kurszuordnung gegen die bereits vorhandenen
Receipt-Verträge prüfen. Erst danach eine gesondert freizugebende produktive
semantische Ausführung mit vollständig versionierter Stage-Konfiguration und
Review der Konfliktkandidaten anbinden.

## Offline-Validierung

Die Befehle und abschließenden Ergebnisse stehen in
[`knowledge_consolidation_test_results.md`](knowledge_consolidation_test_results.md).
