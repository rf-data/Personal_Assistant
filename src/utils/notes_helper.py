## notes_helper.py
# import
from pathlib import Path

"""
docs = open("notes.txt").read().split("\n\n")
vectorizer = TfidfVectorizer()
tfidf = vectorizer.fit_transform(docs)

query = vectorizer.transform(["python multiprocessing"])
scores = (tfidf @ query.T).toarray()

print(docs[scores.argmax()])
"""


def search_notes(folder, keyword):
    for file in Path(folder).rglob("*.md"):
        try:
            content = file.read_text(encoding="utf-8")

            if keyword.lower() in content.lower():
                print(f"Found in: {file}")

        except:
            pass


"""
search_notes(
    "notes",
    "redis"
)
"""

from langchain.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()

db = Chroma(persist_directory="./knowledge", embedding_function=embeddings)

db.add_texts(["Client prefers monthly reports", "Project deadline is August 1"])
