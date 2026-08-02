# ml_service/embeddings.py
from sentence_transformers import SentenceTransformer

# This model runs entirely locally — no API calls, no cost.
# "all-MiniLM-L6-v2" is small, fast, and good enough for this kind of task.
_model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text(text: str):
    """Turns one string of text into a 384-number vector representing its meaning."""
    return _model.encode(text).tolist()