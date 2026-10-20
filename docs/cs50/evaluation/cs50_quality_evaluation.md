# C01–C03 – Fachliche Evaluation und manuelle Freigabe

Abhängigkeit: B05-Branch/PR #35. Implementiert werden nur Vertrag und Infrastruktur,
keine neuen Extraktionsinstruktionen, Goldaussagen, Reviewerurteile oder LLM-Aufrufe.

## Vier getrennte Achsen

GoldReviewSet v1 bindet Kurs/Abschnitt/Lecture/Resource/Source, beide Quellhashes,
Provenienzdigest und tatsächlichen Chunkplan. ReviewWindow enthält echte Cue-IDs
und bestehende TranscriptSegment-Objekte mit Originaltext/-zeiten. ManualReview
kann Aussage, Formel oder Negativbeispiel tragen. ReviewAxes trennt:

1. schema_valid – strukturelle Validität;
2. source_binding_valid – korrekte Quellen-/Cuezuordnung;
3. semantically_supported – manuell bestätigte vollständige Belegbarkeit;
4. didactic_value – manuelles Urteil 0–3 (kein Lernwert / gering / brauchbar / hoch).

Keine Achse folgt automatisch aus einer anderen. Urteile erfordern expliziten
Reviewer und Begründung; Templates haben keine Claims und keine Reviews. Das
Counting berichtet unbewertete Werte ausdrücklich, ohne Quoten zu erfinden oder
Proxyregeln aus Quality als Gold zu behandeln. quality_established bleibt False;
eine Freigabe braucht menschliche Adjudikation und vorab definierte Kriterien.

validate_review_set revalidiert den echten Input, Hashes, Provenienz, Chunkplan,
Cue-IDs, Texte und Originalzeiten. Unbekannte, leere, duplizierte oder fremde
Referenzen und geänderte Cue-Texte werden abgewiesen. origin ist eine deklarierte
Herkunft (synthetic/operator_declared_original), keine aus URLs abgeleitete
Authentizitätsbehauptung. Source-Hashes sind keine kryptografischen Signaturen.

## Acht Originalfenster und spätere sechs-Kurse-Stichprobe

Der lokale erfolgreich importierte Python-0-Originalpilot ist vorhanden und wurde
read-only erneut geprüft. Daraus wurden **acht unannotierte Fenster aus 157 echten
Chunks** in einer temporären Datei erstellt. Keine produktiven Dateien verändert,
keine Original-Transkripte/Belege/maschinenlokalen Pfade im Git aufgenommen.
Raw-SRT-SHA: 719c9905c3908594dd459224b78d5ac9f5cfbc6e06b4dadd67d9f1ea98ecac2c.
Zero Claims/Reviews: keine fachliche Qualität dadurch behauptet.

```bash
# In kontrollierter bestehender Worker-Umgebung, mit geprüftem Originalinput:
uv run --offline --no-sync python -m scripts.cs50_review_template \
  --plan docs/course_sources/cs50/cs50_lecture_plan.v1.json \
  --manifest /explicit/input.v2.json --workspace /explicit/source-workspace \
  --output /scratch/new-review.v1.json --origin operator_declared_original --windows 8
```

Defaultfenster sind deterministisch über die Quelle verteilt. Menschen ersetzen
sie vor Evaluation durch Intro/Moderation, vier echte Python-Konzeptpassagen,
Kontextgrenze und Schluss/Negativfall. Keine Konzepte aus Chunknummern erfinden.
Mindestens einen Teil doppelt annotieren, Uneinigkeit und Adjudikation dokumentieren.
Je Claim minimale/zulässige Cue-Mengen, Topic, Relevanz, Vollständigkeit der Belege,
Überverallgemeinerung und didaktischen Nutzen begründen. Code nicht als Formel
umetikettieren. Später vier echte Fenster je Kurs (24), erst nach freigegebenen
Downloads/Imports. Noch keine dieser zusätzlichen Originalquellen bezogen.

Legacy/segment_v1-Vergleich: dieselben geprüften Quellenfenster/Modell/Promptversion,
separate Run-/Budgetordner und Provider-Sidecars. Chunkgrobe Evidenz, präzise gültige
IDs und semantisch tragfähige Belege getrennt bewerten. Ein echter segment_v1-
Qualitätstest bleibt **ausstehend**; technische Tests ersetzen ihn nicht.

## C03: Freigabepunkte

| Stufe | Technische Voraussetzung | Menschliche Freigabe / Qualitätsnachweis |
|---|---|---|
| Kleiner echter Modelltest | genau 1–2 explizite Chunks, Import/Hashes gültig, Budget/Timeout/unknown-Regeln, neue Scratchausgabe | reale Quelle bestätigen, Modell/Kostenobergrenze ausdrücklich wählen, Goldfenster/Reviewplan, execute-llm erst manuell. |
| Ganze Python-Vorlesung | vollständiger Plan, reservierbares globales Budget, alle Chunk-/Completionmarker und Coverage validiert | vorherige präzise Mini-Eval prüfen, feste Relevanz-/Entailment-/Didaktikgrenzen vorab festlegen, Budget/Stichprobenreview genehmigen. |
| Python-Kurs | zehn verifizierte Quellen, next-pending/shared-budget/Resume, gewichteter Report | Lecture-Abnahme, Stichproben über Themen/Negativfälle, Unknown/Fehlerbehandlung und Gesamtaufwand genehmigen. |
| Alle sechs | 50 Inputs/100 Sourceaktionen, ein Budget/Scope, Offline-E2E und Source-/ID-Kollisionsprüfung | Kursabnahme plus domänenspezifische Reviews (SQL/AI/Web/Security), mögliche Visual-/Formellücken offen behandeln. |

Manuelle Checkliste vor echten Aufrufen:

- PRs in dokumentierter Reihenfolge reviewen/integrieren; keine automatischen Merges.
- Workerprofil/Cache vorhanden; optionale SDKs für HTTP nicht erforderlich.
- Sources über ausdrücklich freigegebene SRT-Downloads/importierte Belege prüfen.
- Offline-Plan/Audit prüfen: Chunkzahl, Parent-/Resource-/Source-/Media-Zuordnung.
- Modell sowie globale Request-/Token-/Zeitgrenzen konservativ explizit bestimmen;
  Preis/Geldbudget anhand des dann gültigen Modells manuell prüfen. Keine Preisannahme
  im Code und kein Versprechen monetärer Genauigkeit allein durch Tokenreserven.
- API-Key ausschließlich über Umgebung, niemals in Manifeste/Logs schreiben.
- Nach unbekannter Anfrage stoppen; keine automatische Wiederholung oder Budgetlöschung.
- Source-/Usage-/Quality-/Completionberichte kontrollieren und fachlich reviewen.

Defaultbudgets/Laufzeit reichen bewusst nicht automatisch für reale Großläufe.
Die Scope-Deadline läuft über Neustarts weiter. Eine abgelaufene/ungewisse Session
wird nicht mit neuem Budget stillschweigend fortgesetzt. Erweiterte Caps oder eine
explizite Unknown-Auflösung brauchen einen gesonderten, nachvollziehbaren Auftrag.
TXT/Visual/Whisper/semantische LLM-Consolidation bleiben außerhalb dieses Projekts.
