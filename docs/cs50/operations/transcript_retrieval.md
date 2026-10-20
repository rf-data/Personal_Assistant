# Transcript-Retrieval

C23-05: [Zeitlose TXT-Dokumente](../contracts/official_transcript_unknown_time.md)
sind noch kein autorisierter Transcript-Retrievalbestand. Die bestehende
Originalprüfung (`verify_hit` → `revalidate_plan` → Source-Binding) verlangt
weiterhin echte SRTzeiten. Cuefenster prüfen `unknown_transcript_time` vor min/max;
numerische Altbestände behalten ihre ursprünglichen Zeitwerte.

search_cs50_transcripts übernimmt eine explizite IngestionPlan-/Embeddingbindung.
Queryencoding nutzt denselben Modell-/Revisions-/Normalisierungsvertrag, bei E5
mit query:-Präfix. Kein Remote-Embedding, keine LLM-Antwort oder implizite Writes.
top_k 1–100, optionale Cosine-Schwelle und Kurs-/Lecture-/Quellen-/Sprachfilter.
Treffer sind zusätzlich auf die im Plan ausdrücklich enthaltenen Sources begrenzt.

TranscriptHit enthält unveränderten Original-Unittext, Chunktext/-ID, echte Cue-IDs,
Originalzeiten, Original-URL, Score und vollständige Hash-/Provenienzreferenzen in
seiner Payload. Jeder Treffer muss dem konkreten geplanten Point exakt entsprechen;
fremde/kaputte Points sind Fehler statt ungeprüfter Suchbelege.

Mit adapter + workspace wird jeder Treffer gegen die originale lokale
TranscriptDocument-/SRT-/Receiptbindung neu geprüft: original_source_checked=True.
Ohne lokale Quellen ist dieser Wert False; Index-/Plan-Abgleich ist kein Nachweis
einer gerade erneut validierten Originaldatei. verify_hit erlaubt den separaten
Originalabgleich ohne Modellinferenz. Die Dateien bleiben unverändert.

Fake-Embedding-Suche prüft ausschließlich Technik und Filterung, nicht semantische
Retrievalqualität. Ein Score ist weder Wahrheits- noch didaktischer Qualitätswert.
Neue Modellversion: neue explizite Collection, dann separat freigegebener Wechsel
des Retrieval-Plans; keine stillschweigende Mischung inkompatibler Vektoren.
