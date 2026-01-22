from ingestion_service.src.core.vectorstore.memory import MemoryVectorStore
from ingestion_service.src.core.chunks import Chunk  # ✅ use real Chunk class


def test_memory_store_persist_and_dump():
    store = MemoryVectorStore()

    chunks = [
        Chunk(chunk_id="chunk-1", content="Hello", metadata={"chunk_strategy": "split"})
    ]
    embeddings = [[1.0, 2.0, 3.0]]

    store.persist(chunks=chunks, embeddings=embeddings, ingestion_id="test-id")
    rows = store.dump()

    assert len(rows) == 1
    assert rows[0]["ingestion_id"] == "test-id"
    assert rows[0]["chunk_index"] == 0
    assert rows[0]["chunk_strategy"] == "split"
    assert rows[0]["vector"] == [1.0, 2.0, 3.0]


def test_memory_store_multiple_chunks():
    store = MemoryVectorStore()

    chunks = [
        Chunk("A", {"chunk_strategy": "split"}),
        Chunk("B", {"chunk_strategy": "split"}),
    ]
    embeddings = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
    ]

    store.persist(chunks=chunks, embeddings=embeddings, ingestion_id="multi-id")
    rows = store.dump()

    assert len(rows) == 2
    assert rows[1]["chunk_index"] == 1
    assert rows[1]["vector"] == [0.4, 0.5, 0.6]
