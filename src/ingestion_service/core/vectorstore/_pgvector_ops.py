from typing import Sequence, Any
from ingestion_service.core.db.models.vector_embedding import VectorEmbedding


def cosine_distance_expr(query_vector: Sequence[float]) -> Any:
    """
    pgvector exposes cosine_distance dynamically at runtime.
    Pylance cannot type this correctly.
    """
    return VectorEmbedding.embedding.cosine_distance(query_vector)
