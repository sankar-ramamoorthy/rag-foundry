import pytest

from ingestion_service.core.vectorstore.pgvector_store import PgVectorStore
from ingestion_service.core.vectorstore.base import (
    VectorRecord,
    VectorMetadata,
)

TEST_DSN = (
    "postgresql://ingestion_user:ingestion_pass@localhost:5433/ingestion_test"
)


@pytest.mark.integration
def test_pgvector_add_search_delete_cycle() -> None:
    store = PgVectorStore(dsn=TEST_DSN, dimension=3)

    # Ensure clean state
    store.reset()

    records = [
        VectorRecord(
            vector=[1.0, 0.0, 0.0],
            metadata=VectorMetadata(
                ingestion_id="ing-1",
                chunk_id="c1",
                chunk_index=0,
                chunk_strategy="fixed",
            ),
        ),
        VectorRecord(
            vector=[0.0, 1.0, 0.0],
            metadata=VectorMetadata(
                ingestion_id="ing-2",
                chunk_id="c2",
                chunk_index=0,
                chunk_strategy="fixed",
            ),
        ),
    ]

    # ---- add ----
    store.add(records)

    # ---- search ----
    results = store.similarity_search([1.0, 0.0, 0.0], k=1)

    assert len(results) == 1
    assert results[0].metadata.ingestion_id == "ing-1"
    assert results[0].metadata.chunk_id == "c1"

    # ---- delete ----
    store.delete_by_ingestion_id("ing-1")

    remaining = store.similarity_search([1.0, 0.0, 0.0], k=5)

    assert all(
        r.metadata.ingestion_id != "ing-1"
        for r in remaining
    )
