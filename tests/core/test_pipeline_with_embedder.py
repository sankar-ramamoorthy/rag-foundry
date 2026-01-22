from ingestion_service.src.core.pipeline import IngestionPipeline
from ingestion_service.src.core.embedders.mock import MockEmbedder
from ingestion_service.src.core.chunkers.base import BaseChunker
from ingestion_service.src.core.chunks import Chunk
from typing import Any, List


class DummyChunker(BaseChunker):
    name = "dummy"
    chunk_strategy = "dummy"  # ← ADDED THIS LINE

    def chunk(self, content: Any, **params) -> List[Chunk]:
        return [Chunk(chunk_id="1", content=content, metadata={})]


class DummyVectorStore:
    def __init__(self):
        self.persisted = []

    def persist(self, chunks, embeddings, ingestion_id):
        self.persisted.append((chunks, embeddings, ingestion_id))


class DummyValidator:
    def validate(self, text: str):
        pass


def test_pipeline_with_mock_embedder():
    pipeline = IngestionPipeline(
        validator=DummyValidator(),
        chunker=DummyChunker(),
        embedder=MockEmbedder(),
        vector_store=DummyVectorStore(),
    )

    pipeline.run(
        text="hello", ingestion_id="test123", source_type="text", provider="mock"
    )
