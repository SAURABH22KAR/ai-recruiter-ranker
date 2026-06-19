from functools import lru_cache
import numpy as np
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def embed(texts: list[str]) -> np.ndarray:
    """Embed a list of texts. Returns (N, D) float32 array."""
    model = get_model()
    return model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two normalized vectors (already unit-norm)."""
    return float(np.dot(a, b))


def max_pool_sim(query_embs: np.ndarray, doc_embs: np.ndarray) -> float:
    """
    For each query embedding, find the best matching doc embedding.
    Returns mean of those best-match scores — good for skill matching.
    """
    if len(query_embs) == 0 or len(doc_embs) == 0:
        return 0.0
    sim_matrix = query_embs @ doc_embs.T  # (Q, D)
    best_per_query = sim_matrix.max(axis=1)  # (Q,)
    return float(best_per_query.mean())


def text_similarity(text_a: str, text_b: str) -> float:
    """Quick single-pair semantic similarity."""
    if not text_a.strip() or not text_b.strip():
        return 0.0
    embs = embed([text_a, text_b])
    return cosine_sim(embs[0], embs[1])
