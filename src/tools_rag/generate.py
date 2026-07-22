## generate.py
# import
import os
import marvin
from dataclasses import asdict
from typing import List

from src.core.memory import SOPGenContext
from src.core.config import env_variables
from src.model_rag.chunks_retrieval import (
                                        ExtractedFact,
                                        IngestedFact,
                                        IngestedChunk,
                                        RetrievedChunk
                                        )
from src.utils.general_helper import (
                                load_env_vars,
                                make_cache_key,
                                load_from_cache,
                                save_to_cache
                                )

# from src.agent.templates.sop_template import CHAPTER_TEMPLATE   # , SOP_TEMPLATE

# SCOPE_DICT = {"sop_allg": "Erstelle eine allgemeine SOP zu folgendem Thema:"}


# task_scope = "Erstelle eine allgemeine SOP zu folgendem Thema:"


def _ingest_chunk(chunk: RetrievedChunk):
    """= Post-retrieval;
    - add infos / metadata / sources to each chunk
    """
    # topics = sop_context.topics
    # POST_RETRIEVAL_PROMPT = ""

    return IngestedChunk(
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                # fact="",
                topic="",
                source=chunk.source,
                section=(
                    chunk.section
                    or chunk.metadata.get("heading_context", "")
                    ),
                page=chunk.page,
                similarity=chunk.similarity,
            )

# marvin.defaults.model = f"openai:gpt-4o-mini"
# model_marvin.py

# python - <<'PY'
# import os
# import marvin
# from src.utils.general_helper import load_env_vars

# marvin.defaults.model = "openai-chat:gpt-4o-mini"

# load_env_vars()

# api_key = os.getenv("OPENAI_API_KEY")
# os.environ["OPENAI_API_KEY"] = api_key

# @marvin.fn
# def extract_test(text: str) -> list[str]:
#     """Extract the main factual statements."""

# print(extract_test("Environmental monitoring shall be performed regularly."))
# PY

def configure_marvin(
    context
    # model: str = "openai:gpt-4o-mini",
    ) -> None:
    marvin.defaults.model = context.llm_context.extraction_model

    api_key = env_variables.openai_api_key

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment."
        )

    os.environ["OPENAI_API_KEY"] = api_key

    return

'''
import marvin
from pydantic import BaseModel
from openai import OpenAI

# Aktuelle Preise für gpt-4o-mini pro 1 Million Token
PRICING = {
    "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000}
}

def log_cost_handler(response_payload):
    """Callback-Funktion zur manuellen Berechnung der Kosten aus der API-Antwort."""
    try:
        usage = response_payload.get("usage")
        model = response_payload.get("model", "gpt-4o-mini")

        # Kürzen, falls spezifischer Sub-Schnitt zurückgegeben wird
        if "gpt-4o-mini" in model:
            model = "gpt-4o-mini"

        if usage and model in PRICING:
            in_tok = usage.get("prompt_tokens", 0)
            out_tok = usage.get("completion_tokens", 0)

            cost = (in_tok * PRICING[model]["input"]) + (out_tok * PRICING[model]["output"])

            print(f"\n[COST TRACKER] Modell: {model}")
            print(f" -> Input Token: {in_tok} | Output Token: {out_tok}")
            print(f" -> Geschätzte Kosten für diesen Aufruf: ${cost:.6f}")
    except Exception as e:
        print(f"Fehler im Cost-Tracker: {e}")

# Marvin auf gpt-4o-mini einstellen
marvin.settings.llm_model = "openai/gpt-4o-mini"

class ProduktExtraktion(BaseModel):
    produktname: str
    menge: int

@marvin.ai_fn
def extrahiere_bestellung(text: str) -> ProduktExtraktion:
    """Extrahiere das Produkt und die Menge aus dem Text."""

# Achtung: Um Token nativ abzufangen, liest man üblicherweise die HTTP-Antworten aus.
# Für einen schnellen Probelauf simulieren wir den Datenstrom:
text_input = "Ich hätte gerne 5 Stück vom neuen Super-Widget"
daten = extrahiere_bestellung(text_input)

print("\nErgebnis der Extraktion:")
print(daten)

# Hinweis: Für ein lückenloses lokales Abfangen ohne Drittanbieter-Tools
# überschreiben Entwickler temporär die `client.chat.completions.create`-Methode
# von OpenAI mit einer eigenen Wrapper-Funktion.
'''

@marvin.fn
def extract_chunk_facts(
        chunk_text: str,
        allowed_topics: list[str],
        ) -> list[ExtractedFact]:
    """
    Extract all SOP-relevant factual statements from the source text.

    Assign each fact to exactly one of the provided allowed_topics.

    Rules:
    - Preserve the factual meaning of the source.
    - Do not add information not present in the source.
    - Split independent requirements or statements into separate facts.
    - Ignore irrelevant text such as headers, footers and document titles.
    - Use only topics from allowed_topics.
    """


def extract_facts(
            chunk: IngestedChunk,
            sop_context: SOPGenContext,
            ) -> List[IngestedFact]:
    cache_folder = "fact_extraction"
    cache_key = make_cache_key(params={
                        "id": chunk.chunk_id,
                        "run_name": "fact_extraction_v1",
                        "prompt_version": "prompt_v1",
                        "model": "marvin_gpt-4o"
                        # topics_hash
                        })

    cached = load_from_cache(key=cache_key, folder=cache_folder)

    if cached is not None:
        return [
            IngestedFact(**chunk_dict)
            for chunk_dict in cached["facts"]
            ]


    configure_marvin(sop_context)

    extracted = extract_chunk_facts(
        chunk_text=chunk.text,
        allowed_topics=sop_context.topics,
    )

    fact_list = [
            IngestedFact(
                fact=item.fact,
                topic=item.topic,
                chunk_id=chunk.chunk_id,
                source=chunk.source,
                section=chunk.section,
                page=chunk.page,
                similarity=chunk.similarity,
            )
            for item in extracted
            ]

    save_to_cache(
                key=cache_key,
                folder=cache_folder,
                data={"facts": [asdict(fact) for fact in fact_list]}
                )
            # chunks_serialized =
    return fact_list


def summarize_chunks(
                chunks: list[RetrievedChunk],
                sop_context: SOPGenContext
                ) -> List[dict]:
    """
    ingest and summarize retrieved chunks
    """

    chunk_facts = []
    for chunk in chunks:
        chunk_ing = _ingest_chunk(chunk)
        # chunk_fact =
        chunk_facts.append({
                "facts": extract_facts(
                    chunk=chunk_ing,
                    sop_context=sop_context
                    # allowed_topics=sop_context.topics,
                    ),
                "chunk": chunk_ing
                })

    return chunk_facts


    # chunks_ing = []
    # for chunk in chunks:
    #     chunks_ing.append(_ingest_chunk(chunk, context))

    # return ChunkSummary(
    #     content="",
    #     sources=[(source, section), (...)],
    # )


# def summarize_chunks(
#     chunks: list[IngestedChunk],
#     context: SOPGenContext,
#     llm_client,
# ) -> ChunkSummary:
#     ...


# def build_context(
#     topic: str, chapter_name: str, chunk_summary: ChunkSummary
# ) -> PromptContext:
#     # parts = []

#     # for i, chunk in enumerate(chunks, start=1):
#     #     parts.append(
#     #         f"[Quelle {i}]\n"
#     #         f"{chunk['text']}\n"
#     #     )

#     return PromptContext(
#         chunk_summary="\n\n".join(parts),
#         task_scope=SCOPE_DICT[""],
#         chapter="",
#         mode="",  # ["new", "update"]
#         template=CHAPTER_TEMPLATE[""],
#     )


# GMP-orientierter .
# Berücksichtige, dass die SOPs zu einer
# gehören und man sich an GMP orientiert aber nicht daran gebunden ist.


# def build_sop_gen_prompt(context: SOPGenContext) -> str:
#     # return
#     """
#         Du bist GMP-Experte.

#     Erstelle aus dem bereitgestellten Wissenspool eine SOP.

#     Regeln:

#     keine neuen Inhalte
#     keine Halluzinationen
#     nichts weglassen
#     fachlich konsistent
#     logisch strukturieren
#     keine Quellen zitieren
#     professioneller SOP-Stil
#     Markdown
#     """

#     return f"""
# Du bist ein SOP-Autor, der GMP-relevante SOPs für eine
# herstellende Apotheke schreibt. Man ist nicht an GMP gebunden,
# will sich aber daran orientieren.

# Aufgabe:
# {context.task_scope}

# {user_request}

# Verwende ausschließlich den folgenden Kontext, soweit er passt.
# Wenn Informationen fehlen, schreibe allgemeine, vorsichtige Platzhalter.

# Kontext:
# {context.chunks}

# Vorlage:
# {context.template}

# Überarbeite die SOP kapitelweise und gibt den Inhalt als Markdown aus.
# Du kannst auch neue Unterkapitel erstellen, um den Inhalt besser zu strukturieren.
# """


# def generate_sop(prompt: str, client) -> str:
#     response = client.responses.create(
#         model="gpt-4.1-mini",
#         input=prompt,
#     )
#     return response.output_text


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
