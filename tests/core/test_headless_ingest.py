# tests/core/test_headless_ingest.py
import uuid
import pytest

from ingestion_service.core.headless_ingest import HeadlessIngestor
from ingestion_service.core.pipeline import IngestionPipeline
from ingestion_service.core.embedders.mock import MockEmbedder
from ingestion_service.core.chunkers.text import TextChunker
from ingestion_service.core.vectorstore.pgvector_store import PgVectorStore

pytest_plugins = ["tests.conftest_db"]


@pytest.mark.integration
@pytest.mark.docker
def test_headless_ingestion_adds_vectors(test_database_url):
    dsn = test_database_url

    # Use MockEmbedder and PgVectorStore
    vector_store = PgVectorStore(dsn=dsn, dimension=3)
    embedder = MockEmbedder()
    chunker = TextChunker(chunk_size=100, overlap=10, strategy="simple")

    pipeline = IngestionPipeline(
        validator=type("Validator", (), {"validate": lambda self, text: None})(),
        chunker=chunker,
        embedder=embedder,
        vector_store=vector_store,
    )

    ingestor = HeadlessIngestor(pipeline)

    text = "This is a test document. It has multiple sentences. And multiple chunks."
    ingestion_id = str(uuid.uuid4())

    # Run ingestion
    ingestor.ingest_text(text, ingestion_id)

    # Verify that vectors are persisted
    results = vector_store.similarity_search([1.0, 1.0, 1.0], k=10)
    assert any(r.metadata.ingestion_id == ingestion_id for r in results)
