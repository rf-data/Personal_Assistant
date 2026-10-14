# B02 – Vollständiger Lecture-Abschluss

Abhängigkeit: B01-Runner (PR #31). complete_lecture hält den A01-Joblock,
revalidiert jede erwartete Chunkantwort samt Budgetreferenz und verlangt exakt
die vollständige Quellreihenfolge. Irrelevante Ergebnisse mit extraction=None
zählen als verarbeitet; es werden keine Aussagen erfunden.

Bestehende TranscriptKnowledgeDocument-/ConsolidatedKnowledgeDocument-Modelle
werden regulär konstruiert und per JSON-Roundtrip geprüft. Deterministische
Consolidation bleibt unverändert. Quality und Coverage enthalten alle erwarteten
Chunks; synthetische Herkunft bleibt ausdrücklich sichtbar.

Zwei-Phasen-Publikation: completion.prepared.v1.json bindet erwartete Identität,
Chunkliste und vier Hashes; dann exklusiv/atomar extraction.json, consolidated.json,
quality.json und coverage.json im festen completion-Unterverzeichnis; erst danach
completion.v1.json mit phase=done. Prepared mit vollständig publizierten und erneut
validierten Dateien kann ohne Request fertiggestellt werden. Fehlende/kaputte
Dateien, Marker, fremde Chunkreceipts und unreceipted Outputs sind Konflikte;
keine automatische Reparatur oder Überschreibung. Der CLI-Worker setzt
lecture_complete erst nach diesem überprüften Abschluss.

Die Vorlesungsartefakte werden beim Resume aus validierten Chunks deterministisch
rekonstruiert und exakt mit den gespeicherten Hashes/Inhalten verglichen. Ein
bestehender Marker allein genügt nie. Tests prüfen Partialität, irrelevante Chunks,
Korruption, fremde Chunks und Abbruch nach Publikation vor Completion-Marker.
