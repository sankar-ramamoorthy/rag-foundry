# tests/vectorstore/test_memory_store.py
from ingestion_service.core.vectorstore.base import (
    VectorMetadata,
    VectorRecord,
)
from ingestion_service.core.vectorstore.memory import InMemoryVectorStore


def test_add_and_search() -> None:
    store = InMemoryVectorStore(dimension=3)

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
                ingestion_id="ing-1",
                chunk_id="c2",
                chunk_index=1,
                chunk_strategy="fixed",
            ),
        ),
    ]

    store.add(records)

    results = store.similarity_search([1.0, 0.0, 0.0], k=1)

    assert len(results) == 1
    assert results[0].metadata.chunk_id == "c1"


def test_delete_by_ingestion_id() -> None:
    store = InMemoryVectorStore(dimension=2)

    store.add(
        [
            VectorRecord(
                vector=[1.0, 0.0],
                metadata=VectorMetadata(
                    ingestion_id="ing-1",
                    chunk_id="c1",
                    chunk_index=0,
                    chunk_strategy="fixed",
                ),
            ),
            VectorRecord(
                vector=[0.0, 1.0],
                metadata=VectorMetadata(
                    ingestion_id="ing-2",
                    chunk_id="c2",
                    chunk_index=0,
                    chunk_strategy="fixed",
                ),
            ),
        ]
    )

    store.delete_by_ingestion_id("ing-1")

    results = store.similarity_search([1.0, 0.0], k=10)
    assert len(results) == 1
    assert results[0].metadata.ingestion_id == "ing-2"
