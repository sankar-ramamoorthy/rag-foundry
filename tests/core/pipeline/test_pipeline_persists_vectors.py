import uuid
import pytest
from typing import cast

from ingestion_service.core.pipeline import IngestionPipeline
from ingestion_service.core.embedders.ollama import OllamaEmbedder
from ingestion_service.core.embedders.factory import get_embedder
from ingestion_service.core.chunkers.text import TextChunker
from ingestion_service.core.vectorstore.pgvector_store import PgVectorStore
from ingestion_service.core.chunks import Chunk
from ingestion_service.core.config import reset_settings_cache

pytest_plugins = ["tests.conftest_db"]


@pytest.mark.integration
@pytest.mark.docker
def test_pipeline_persists_vectors_pgvector(clean_vectors_table, test_database_url):
    reset_settings_cache()

    embedder = cast(OllamaEmbedder, get_embedder("ollama"))
    assert embedder.dimension == 768

    vector_store = PgVectorStore(
        dsn=test_database_url,
        dimension=embedder.dimension,
        provider="ollama",
    )

    chunker = TextChunker(chunk_size=50, overlap=5, chunk_strategy="simple")
    validator = type("Validator", (), {"validate": lambda self, text: None})()

    pipeline = IngestionPipeline(
        validator=validator,
        chunker=chunker,
        embedder=embedder,
        vector_store=vector_store,
    )

    ingestion_id = str(uuid.uuid4())
    text = "This is a test document for Docker integration pipeline."

    # --- Test end-to-end pipeline ---
    pipeline.run(text=text, ingestion_id=ingestion_id)

    # --- Verify vectors persisted correctly ---
    query_chunk = Chunk(chunk_id="query", content=text, metadata={})
    query_embedding = embedder.embed([query_chunk])[0]
    results = vector_store.similarity_search(query_vector=query_embedding, k=1)

    assert any(r.metadata.ingestion_id == ingestion_id for r in results)
    assert any(r.metadata.chunk_strategy == "simple" for r in results)
