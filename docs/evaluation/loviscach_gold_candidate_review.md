# Loviscach: Humanreview und Übergabe

Stand v1: **0 Kandidaten / 0 approve / 0 revise / 0 reject**. Leerer Reviewexport
unter [loviscach/review.v1.csv](loviscach/review.v1.csv). Alle künftigen Kandidaten
starten pending_human_review; derzeit existiert keine bestätigte Ground Truth.

Der Reviewer prüft Originaldatei und SHA-256, Originalversion, Quellenfundstelle,
Frage und erwartete Antwort ohne Retrievalprediction als Referenz. Er hält pro
Question-ID eine begründete Entscheidung `approve`, `revise` oder `reject`,
Revieweridentität, Datum und Evidenzreferenz fest. `approve` in einer CSV ist
noch kein kanonischer Goldexport. Es gibt keinen automatischen Import dieser
Entscheidung oder Statuswechsel durch das Vorbereitungstool.

`revise`: Frage/Antwort/Mehrdeutigkeit/Fundstelle korrigieren, Revision und
change_note erhöhen, Datensatzversion in Git fortschreiben. Bei geänderter Frage
neue deterministische ID; historische Versionen behalten. `reject`: ursprüngliche
Kandidatenversion in Git erhalten und begründete Reviewentscheidung separat
versionieren. Originalmaterialien bleiben unverändert.

Nach freigegebener Source-/Parsed-/Kursbindung werden die bestehenden
[Humanreviewverträge](../api/human_review_v1.md) genutzt:
Dataset-/Sourcegrants, unabhängige Originalannotation, Draft/Confirm, CAS-/
Idempotenz und append-only Revisionen. Dafür sind explizite Realreviewfreigabe,
Reviewer und Belege nötig. Die Pendingreferenzen bilden schon heute C23
GoldReference ab. Retrieval benötigt zusätzlich echte Parsed-/Blockregionen,
Grade und vollständigen Pool. Formelreferenzen separat im vorhandenen C11-Modell
prüfen; kein Textvergleich ersetzt mathematische Äquivalenz.

Nicht evaluierbare Fälle bleiben im Nennerbericht als ausgeschlossen mit Grund
sichtbar. Parser-, Retrieval- und Formelbefunde getrennt berichten. Keine echte
Qualitätsrate aus diesem leeren Pool oder synthetischen Tests ableiten.

Offene Entscheidungen: dokumentierte Loviscach-Originalfreigabe, private
Rootzuordnung, Kursbindung, Themenstichprobe, Reviewer, Formel-/Visualbelege,
fachliche Grenzwerte und manuelle Abnahme. C26 bleibt HOLD.
