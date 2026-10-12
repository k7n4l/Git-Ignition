import numpy as np

def calculate_cosine_similarity(
    query_vector: np.ndarray,
    chunk_vectors: np.ndarray,
) -> np.ndarray:
    """
    Calculate cosine similarity between a single 1D query vector (384,)
    and a 2D matrix of chunk vectors (N, 384).
    Returns a 1D array of similarity scores between -1.0 and 1.0 of length N.
    """
    if len(chunk_vectors) == 0:
        return np.empty(0, dtype=np.float32)

    # Dot products between all chunk vectors and the query vector
    dot_products = np.dot(chunk_vectors, query_vector)

    # Vector norms
    query_norm = np.linalg.norm(query_vector)
    chunk_norms = np.linalg.norm(chunk_vectors, axis=1)

    denominator = chunk_norms * query_norm
    # Prevent division by zero with small epsilon
    denominator = np.where(denominator == 0, 1e-9, denominator)

    similarities = dot_products / denominator
    return similarities.astype(np.float32)

def retrieve_top_chunks(
    query_vector: np.ndarray,
    chunks: list[dict],
    top_k: int = 4,
) -> list[tuple[dict, float]]:
    """
    Retrieve the top_k most similar chunks for a given query vector.
    Each chunk dict must contain an 'embedding' key (np.ndarray).
    Returns list of (chunk_dict, similarity_score) sorted descending by score.
    """
    if not chunks:
        return []

    # Stack all chunk embeddings into a 2D array of shape (N, 384)
    chunk_vectors = np.vstack([c["embedding"] for c in chunks])

    scores = calculate_cosine_similarity(query_vector, chunk_vectors)

    # Top K indices sorted by descending score
    ranked_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in ranked_indices:
        results.append((chunks[idx], float(scores[idx])))

    return results
