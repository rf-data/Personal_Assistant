## generate.py
# import

from src.core.memory import SOPGenContext

# from src.agent.templates.sop_template import CHAPTER_TEMPLATE   # , SOP_TEMPLATE

SCOPE_DICT = {"sop_allg": "Erstelle eine allgemeine SOP zu folgendem Thema:"}


# task_scope = "Erstelle eine allgemeine SOP zu folgendem Thema:"


def _ingest_chunks(chunks: list, sop_context: SOPGenContext):
    """= Post-retrieval;
    - add infos / metadata / sources to each chunk
    """

    POST_RETRIEVAL_PROMPT = ""

    return IngestedChunk(
        chunk_id="",
        fact="",
        topic="",
        source="",
        section="",
        # page=""?,
        confidence="",
    )


def summarize_chunks(chunks: list[str], context: SOPGenContext):
    """
    ingest and summarize retrieved chunks
    """

    chunks_ing = _ingest_chunks(chunks, context)

    return ChunkSummary(
        content="",
        sources=[(source, section), (...)],
    )


def build_context(
    topic: str, chapter_name: str, chunk_summary: ChunkSummary
) -> PromptContext:
    # parts = []

    # for i, chunk in enumerate(chunks, start=1):
    #     parts.append(
    #         f"[Quelle {i}]\n"
    #         f"{chunk['text']}\n"
    #     )

    return PromptContext(
        chunk_summary="\n\n".join(parts),
        task_scope=SCOPE_DICT[""],
        chapter="",
        mode="",  # ["new", "update"]
        template=CHAPTER_TEMPLATE[""],
    )


# GMP-orientierter .
# Berücksichtige, dass die SOPs zu einer
# gehören und man sich an GMP orientiert aber nicht daran gebunden ist.


def build_sop_gen_prompt(context: SOPGenContext) -> str:
    # return
    """
        Du bist GMP-Experte.

    Erstelle aus dem bereitgestellten Wissenspool eine SOP.

    Regeln:

    keine neuen Inhalte
    keine Halluzinationen
    nichts weglassen
    fachlich konsistent
    logisch strukturieren
    keine Quellen zitieren
    professioneller SOP-Stil
    Markdown
    """

    return f"""
Du bist ein SOP-Autor, der GMP-relevante SOPs für eine
herstellende Apotheke schreibt. Man ist nicht an GMP gebunden,
will sich aber daran orientieren.

Aufgabe:
{context.task_scope}

{user_request}

Verwende ausschließlich den folgenden Kontext, soweit er passt.
Wenn Informationen fehlen, schreibe allgemeine, vorsichtige Platzhalter.

Kontext:
{context.chunks}

Vorlage:
{context.template}

Überarbeite die SOP kapitelweise und gibt den Inhalt als Markdown aus.
Du kannst auch neue Unterkapitel erstellen, um den Inhalt besser zu strukturieren.
"""


def generate_sop(prompt: str, client) -> str:
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )
    return response.output_text


# - Zweck
# - Geltungsbereich
# - Verantwortlichkeiten
# - Durchführung
# - Dokumentation
# - Abweichungen
# - Referenzen
'''
def generate_report(data):
prompt = f"""
    Analyze this business data.
    Provide:
    - Key Metrics
    - Growth Analysis
    - Risks
    - Opportunities
    - Recommendations
    Data:
    {data}
    """
    return llm(prompt)
'''

"""
import pandas as pd

def generate_report():
    data = pd.read_csv("data.csv")
    summary = data.describe()
    summary.to_csv("report.csv")

generate_report()
"""
