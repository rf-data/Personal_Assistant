# test_embedding.py

from sentence_transformers import SentenceTransformer

print("1 - loading model")

model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

print("2 - model loaded")

texts = [
    "Hygienemonitoring in der aseptischen Herstellung",
    "Mikrobiologische Überwachung von Oberflächen",
]

print("3 - start encoding")

embeddings = model.encode(
    texts,
    batch_size=2,
    normalize_embeddings=True,
    show_progress_bar=False,
)

print("4 - encoding finished")
print(embeddings.shape)