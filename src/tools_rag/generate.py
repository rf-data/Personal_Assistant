## generate.py
# import

from src.agent.templates.sop_template import SOP_TEMPLATE



def build_context(chunks: list[dict]) -> str:
    parts = []

    for i, chunk in enumerate(chunks, start=1):
        parts.append(
            f"[Quelle {i}]\n"
            f"{chunk['text']}\n"
        )

    return "\n\n".join(parts)


def build_sop_prompt(
                user_request: str, 
                context: str
                ) -> str:
    return f"""
Du bist ein GMP-orientierter SOP-Autor.

Aufgabe:
Erstelle eine allgemeine SOP zu folgendem Thema:

{user_request}

Verwende ausschließlich den folgenden Kontext, soweit er passt.
Wenn Informationen fehlen, schreibe allgemeine, vorsichtige Platzhalter.

Kontext:
{context}

Struktur:
{SOP_TEMPLATE}

Gib die SOP als Markdown aus.
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

'''
import pandas as pd

def generate_report():
    data = pd.read_csv("data.csv")
    summary = data.describe()
    summary.to_csv("report.csv")

generate_report()
'''