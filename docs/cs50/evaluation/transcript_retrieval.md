# Retrieval-Evaluation v1

Vorlage: [python0_retrieval_questions.v1.json](python0_retrieval_questions.v1.json).
Zehn Fragen zu Funktionen, Argumenten, Variablen, Rückgabewerten/Zuweisung,
Kommentaren, Stringverkettung, strip, split, numerischen Typen und def. Alle
vorgeschlagenen Cue-Fenster wurden read-only gegen den vorhandenen echten Pilot
geprüft; kein echter Embedding-/Retrievallauf oder Relevanzurteil wird behauptet.

Vier getrennte Nachweise: technische Contracttests; Fake-Embedding/Qdrant-Tests;
separat aktivierte echte lokale Modellintegration; fachliche Retrieval-Evaluation.
Fake-Wortvektoren beweisen keine semantische Qualität. Es sind keine Modellgewichte
bereitgestellt, deshalb kein echter CPU-/RAM-/Rankingbenchmark ausgeführt.

Die versionierte Python-0-Fragenvorlage basiert auf erneut validierter echter
lokaler offizieller SRT-/Transcript-/Receiptbindung, nicht auf erfundenen
Goldaussagen. Zehn fachliche Fragen referenzieren echte Cue-IDs/Zeiten und
geprüfte Quellhashes. Das sind vorgeschlagene Belegfenster; Relevanz-/Nutzenurteile,
tatsächliche Treffer und Rankings müssen nach echter Modellintegration manuell
ergänzt werden. Originaltranskript und Maschinenpfade werden nicht versioniert.

ManualRetrievalJudgment verlangt konkrete relevante Point-/Segmentreferenzen,
Reviewer, Sourcehash, semantische Quellenkorrektheit und Nutzenbegründung.
reviewed_metrics verweigert Fake-/synthetische Läufe, unvollständige oder fremde
Urteile und nicht erneut originalverifizierte Treffer. Erst mindestens zehn
vollständig fachlich beurteilte echte Fragen erlauben Recall@k und MRR@k.
Die reine Rankingarithmetik wird separat mit als solchen markierten Toy-Zahlen
getestet; keine solchen Zahlen werden als CS50-Leistungswerte veröffentlicht.

Die vorgeschlagenen Fragen adaptiert aus CS50's Introduction to Programming with
Python, David J. Malan / Harvard University. Attribution und Quelle stehen in der
Vorlage; [CC BY-NC-SA 4.0](https://cs50.harvard.edu/python/license/).
