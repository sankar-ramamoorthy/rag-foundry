# tests/core/test_pipeline.py
from ingestion_service.core.pipeline import IngestionPipeline
from ingestion_service.core.chunks import Chunk
from ingestion_service.core.chunkers.base import BaseChunker
from ingestion_service.core.chunkers.selector import ChunkerFactory
from typing import Any, List


class DummyChunker(BaseChunker):
    name = "dummy"
    chunk_strategy = "dummy"

    def chunk(self, content: Any, **params) -> List[Chunk]:
        return [Chunk(chunk_id="1", content=content[:5], metadata={})]


class DummyEmbedder:
    def embed(self, chunks: List[Chunk]) -> List[List[float]]:
        return [[0.1, 0.2]] * len(chunks)


class DummyVectorStore:
    def __init__(self):
        self.persisted = []

    def persist(
        self, chunks: List[Chunk], embeddings: List[List[float]], ingestion_id: str
    ):
        self.persisted.append((chunks, embeddings, ingestion_id))


class DummyValidator:
    def validate(self, text: str):
        pass


def test_pipeline_dynamic_chunker(monkeypatch):
    text = "This is a test of dynamic chunker selection."
    ingestion_id = "ing123"

    embedder = DummyEmbedder()
    vector_store = DummyVectorStore()
    validator = DummyValidator()

    dummy_chunker = DummyChunker()
    monkeypatch.setattr(
        ChunkerFactory,
        "choose_strategy",
        lambda content, **context: (dummy_chunker, {"chunk_size": 5, "overlap": 0}),
    )

    pipeline = IngestionPipeline(
        validator=validator,
        chunker=None,
        embedder=embedder,
        vector_store=vector_store,
    )

    # Use the public `run()` method, ingestion_id is now actually used
    pipeline.run(text=text, ingestion_id=ingestion_id)

    # Check that chunks were persisted
    persisted_chunks, persisted_embeddings, persisted_id = vector_store.persisted[0]
    assert persisted_id == ingestion_id
    assert len(persisted_chunks) == 1
    assert persisted_chunks[0].content == text[:5]
    assert persisted_chunks[0].metadata["chunk_strategy"] == "dummy"
    assert persisted_chunks[0].metadata["chunker_params"] == {
        "chunk_size": 5,
        "overlap": 0,
    }


def test_pipeline_explicit_chunker():
    text = "Explicit chunker test"
    ingestion_id = "explicit123"

    chunker = DummyChunker()
    embedder = DummyEmbedder()
    vector_store = DummyVectorStore()
    validator = DummyValidator()

    pipeline = IngestionPipeline(
        validator=validator,
        chunker=chunker,
        embedder=embedder,
        vector_store=vector_store,
    )

    pipeline.run(text=text, ingestion_id=ingestion_id)

    persisted_chunks, _, persisted_id = vector_store.persisted[0]
    assert persisted_id == ingestion_id
    assert persisted_chunks[0].metadata["chunk_strategy"] == "dummy"
    assert persisted_chunks[0].metadata["chunker_params"] == {}
