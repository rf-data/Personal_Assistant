## text_q&a.py
# import


def score_doc(doc, query):
    """
    Scores aggregated info which was extracted from several texts 
    in terms of a questions entered as prompt. 
    """
    text = " ".join([
        doc.summary,
        " ".join(doc.key_findings),
        " ".join(doc.key_entities)
    ]).lower()

    query = query.lower()

    score = sum(1 for word in query.split() if word in text)

    return score


def retrieve_docs(docs, query, top_k=3):
    """
    Gather scores from all available/provided documents and 
    returns top_k documents as list
    """
    scored = [(doc, score_doc(doc, query)) for doc in docs]

    ranked = sorted(scored, key=lambda x: x[1], reverse=True)

    return [doc for doc, score in ranked if score > 0][:top_k]


def build_qa_input(docs):

    return [
        {
            "id": i,
            "summary": d.summary,
            "findings": d.key_findings,
            "entitites": d.key_entities,
        }
        for i, d in enumerate(docs, 1)
    ]