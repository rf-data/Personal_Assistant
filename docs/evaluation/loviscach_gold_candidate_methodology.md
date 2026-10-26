# Loviscach: Kandidatenmethodik

Dies ist eine Vorbereitung für #107/#108, keine reale Qualitätsabnahme.
`GoldCandidatePool` ist ein begrenzter Pending-Umschlag um vorhandene
C23 `GoldReference`, C24 `QuerySpec` und `ContentLocator`. Er ersetzt keinen
Evaluator, ContentStore, Source-/Parsedvertrag oder Humanreviewservice.
Keine Kandidaten aus Realmaterial, solange dessen Verarbeitung nicht belegt ist.

## Auswahl und Evidenz

Nach Freigabe höchstens 30 fachlich vielfältige Kandidaten mit Fakten,
Definitionen, Zusammenhängen, Regeln, mehrteiligen/kontrastierenden Fragen,
Formeln und kontrolliert nicht beantwortbaren Fragen. Originalquellen lesen,
Frage/Antwort unabhängig vom Retrievalresultat annotieren; abgeleitete Parser-
oder Visualausgaben nur zur Fehleranalyse nutzen. Dateihash/Sourceversion,
Kurs-/Vorlesungsidentität, Sprache, Typ und relative Originalreferenz festhalten.
Die private Rootzuordnung bleibt außerhalb öffentlicher Git-Artefakte.

Question-ID: `gc_` plus deterministischer Digest aus entry_id und exakter Frage.
Antwort-/Reviewänderungen behalten die ID, geänderte Fragen bekommen eine neue.
Version, Revision und Änderungsnotiz sind Pflicht. Pool und Schema begrenzen
Datenmengen, verbieten doppelte Fragen/Referenzen und gemischte Herkunft.
Original- und Locatorhash, Source-/Versions-ID und Targetpointer müssen passen.
Pendingstatus lässt sich weder am Kandidaten noch an eingebetteten Referenzen
in bestätigtes Gold umwandeln.

## Getrennte Evaluationsebenen

| Ebene | Vorbereitet | Fachliche Prüfung und späterer bestehender Vertrag |
|---|---|---|
| Parsing | GoldReference.dimension/expected_content/expected_structure/Locator | Original vs. Parsed: Vollständigkeit, Notation, Bilder/Tabellen/Code, Seite/Abschnitt; C23 GoldDataset |
| Retrieval | QuerySpec und originale relevante Fundstellen | erst nach Source-/Parsedbindung vollständige Reviewpools/Grade und konfigurierte Nenner festlegen; C24 ContentRelevanceJudgment/ReviewPool |
| Formeln | explizite Originalnotation oder null bei fehlendem Kontext | Vorzeichen/Notation/semantische Äquivalenz unabhängig prüfen; anschließend bestehende C11 FormulaCase-Paare |

Keine rekonstruierte Formel definiert ihre Referenz. Bei unvollständiger
visueller Evidenz: needs_visual_context=true, visual_context_complete=false,
evaluability=not_evaluable. Mehrdeutigkeit erfordert eine Notiz und Ausschluss.
Auch vollständig belegbare Kandidaten bleiben bis Humanreview pending_review.
Nicht beantwortbare Fragen besitzen expected_answer=null und eine explizite
begrenzte Suchbereichsnotiz, keine erfundene relevante Stelle. Ihre C23-Referenz
markiert die erwartete Abwesenheit mit leerem Text und occurrences=0; die
menschliche Poolvollständigkeitsprüfung bleibt erforderlich.

## Validatorgrenzen und reproduzierbare Nutzung

```sh
python -m src.tools_evaluation.gold_candidates \
  --dataset docs/evaluation/loviscach/candidates.v1.json
python -m src.tools_evaluation.gold_candidates \
  --dataset "$CANDIDATE_FILE" --grants "$PRIVATE_AUTHORIZED_GRANTS" \
  --review-csv /tmp/new-exclusive-candidate-review.csv
```

Private Grants ordnen root_key einem absoluten root, permission=evaluation,
permission_reference, origin und entry_ids zu. Die Datei dokumentiert eine
bereits erteilte Betreiberfreigabe; sie erzeugt selbst keine Rechte und darf
niemals zum Umgehen von D06/D07 erfunden werden. Der Validator verifiziert alle
Grants vor Inhaltsreads, öffnet ausschließlich deklarierte Originaldateien mit
gehaltenen Directory-FDs/O_NOFOLLOW, lehnt Symlinks/FIFOs/Traversal und Dateien
über 16 MiB ab. Keine Suche, Rekursion, Downloads oder Änderungen an Originalen.
Hashes und deklarierte Textzeilenbereiche werden geprüft. PDFseiten, DOM-/
Zeitanker, mathematische Aussagen und die Unabhängigkeit einer Annotation kann
ein Hashvalidator **nicht fachlich bestätigen**; das bleibt Humanreview.
Source-/Parsedversionen sind vor einem operativen Export kanonisch zu verifizieren.

Reviewexport ist exklusiv neu, außerhalb sämtlicher deklarierter Originalwurzeln;
CSV-Formelausführung wird durch Escaping verhindert. Fehlerausgaben enthalten
keine Originalpfade/-texte. Der leere reale Pool benötigt keine Materialreads.
Synthetische Fixtures bleiben ausschließlich in Tests und liefern keine realen Raten.
