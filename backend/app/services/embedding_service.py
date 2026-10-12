import logging
import numpy as np
from typing import Optional
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
# MiniLM's transformer tokenizer has an input limit of 256 tokens.
# Code chunks longer than 256 tokens are truncated at token 256 during embedding.
MAX_SEQ_LENGTH = 256

_model_instance: Optional[SentenceTransformer] = None

def get_embedding_model() -> SentenceTransformer:
    """
    Load the SentenceTransformer model once on CPU and cache it in memory.
    Reuses the singleton instance across all requests to prevent memory churn.
    """
    global _model_instance
    if _model_instance is None:
        logger.info("Loading local embedding model '%s' on CPU...", MODEL_NAME)
        # Force CPU execution to keep memory small and avoid GPU/VRAM issues
        _model_instance = SentenceTransformer(MODEL_NAME, device="cpu")
        _model_instance.max_seq_length = MAX_SEQ_LENGTH
        logger.info(
            "Model '%s' loaded successfully. Dim: %d, MaxSeqLength: %d tokens.",
            MODEL_NAME,
            EMBEDDING_DIM,
            _model_instance.max_seq_length,
        )
    return _model_instance

def embed_texts(texts: list[str], batch_size: int = 32) -> np.ndarray:
    """
    Generate 384-dimensional embeddings for a list of texts in batches.
    Returns a NumPy float32 array of shape (N, 384).
    """
    if not texts:
        return np.empty((0, EMBEDDING_DIM), dtype=np.float32)

    model = get_embedding_model()
    # show_progress_bar is False in server environment to avoid noisy terminal logs
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return embeddings.astype(np.float32)

def embed_query(query: str) -> np.ndarray:
    """
    Generate a 384-dimensional normalized embedding for a single search question.
    Returns a 1D NumPy float32 array of shape (384,).
    """
    model = get_embedding_model()
    embedding = model.encode(
        query,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return embedding.astype(np.float32)
