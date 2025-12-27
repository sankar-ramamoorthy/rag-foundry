from __future__ import annotations

from ingestion_service.core.vectorstore.base import VectorStore


class PgVectorStore(VectorStore):
    """
    pgvector-backed VectorStore.

    Implementation intentionally deferred.
    See ADR-005: Vector Store Implementation Without ORM.
    """

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError(
            "PgVectorStore is intentionally not implemented in IS5-MS2. "
            "See ADR-005."
        )
