## generation_metrics.py
# imports

"""
Zur automatisierten Messung dieser Metriken setzen Entwickler meist auf sogenannte "LLM-as-a-Judge"-Frameworks.
--> Ragas (Retrieval Augmented Generation Assessment):
Das derzeit führende Open-Source-Framework zur Bewertung von RAG-Pipelines.

--> TruLens:
Bietet ein umfassendes Dashboard zur Echtzeit-Überwachung der "RAG Triad" (Kontextrelevanz, Fundiertheit und Antwortrelevanz).
"""

"""
# Faithfulness (Treue):
Überprüft, ob die generierte Antwort strikt auf den abgerufenen Dokumenten basiert. Eine hohe Treue verhindert Halluzinationen.

# Answer Relevancy:
Bewertet, ob die Antwort des Modells direkt auf die ursprüngliche Benutzerfrage eingeht und nicht am Thema vorbeigeht.

# Answer Correctness:
Vergleicht die generierte Antwort inhaltlich mit einer definierten Referenzantwort ("Ground Truth"), um die tatsächliche inhaltliche
Richtigkeit zu messen.
"""
