import uuid
import pytest

from ingestion_service.core.pipeline import IngestionPipeline
from ingestion_service.core.headless_ingest import HeadlessIngestor
from ingestion_service.core.chunkers.text import TextChunker
from ingestion_service.core.embedders.mock import MockEmbedder
from ingestion_service.core.vectorstore.pgvector_store import PgVectorStore

pytest_plugins = ["tests.conftest_db"]


@pytest.mark.docker
@pytest.mark.integration
def test_pipeline_persists_vectors_pgvector(clean_vectors_table, test_database_url):
    """
    GIVEN text input
    WHEN the ingestion pipeline runs
    THEN chunk embeddings are persisted to pgvector with correct metadata
    """

    vector_store = PgVectorStore(
        dsn=test_database_url,
        dimension=3,
    )

    pipeline = IngestionPipeline(
        validator=type(
            "Validator",
            (),
            {"validate": lambda self, text: None},
        )(),
        chunker=TextChunker(chunk_size=50, overlap=0, chunk_strategy="simple"),
        embedder=MockEmbedder(),
        vector_store=vector_store,
    )

    ingestor = HeadlessIngestor(pipeline)

    text = "This is chunk one. This is chunk two. This is chunk three."

    ingestion_id = str(uuid.uuid4())

    ingestor.ingest_text(text, ingestion_id)

    results = vector_store.similarity_search(
        query_vector=[1.0, 1.0, 1.0],
        k=10,
    )

    persisted = [r for r in results if r.metadata.ingestion_id == ingestion_id]

    assert len(persisted) > 0

    for record in persisted:
        assert record.vector is not None
        assert record.metadata.chunk_id
        assert record.metadata.chunk_index >= 0
        assert record.metadata.chunk_strategy == "simple"
