import pytest
from typing import cast

from ingestion_service.core.embedders.ollama import OllamaEmbedder
from ingestion_service.core.embedders.factory import get_embedder
from ingestion_service.core.vectorstore.base import VectorMetadata, VectorRecord
from ingestion_service.core.vectorstore.pgvector_store import PgVectorStore
from ingestion_service.core.chunks import Chunk
from ingestion_service.core.config import reset_settings_cache
import logging

logging.basicConfig(level=logging.DEBUG)
pytest_plugins = ["tests.conftest_db"]


@pytest.mark.integration
@pytest.mark.docker
def test_pgvector_similarity_search(clean_vectors_table, test_database_url):
    reset_settings_cache()

    # Use real Ollama embedder (768D)
    embedder = cast(OllamaEmbedder, get_embedder("ollama"))
    assert embedder.dimension == 768

    store = PgVectorStore(
        dsn=test_database_url,
        dimension=embedder.dimension,  # 768, not 3!
        provider="ollama",
    )

    # Create test texts that should have distinct embeddings
    # Create test texts with CLEAR semantic distance from query
    texts = [
        "Chunk 1: machine learning algorithms",  # MOST similar to query
        "Chunk 2: machine learning models",  # 2nd most similar
        "Chunk 3: database indexing techniques",  # LEAST similar
    ]

    # Generate real embeddings
    chunks = [
        Chunk(chunk_id=f"c{i}", content=text, metadata={})
        for i, text in enumerate(texts)
    ]
    embeddings = embedder.embed(chunks)

    records = [
        VectorRecord(
            vector=embeddings[0],
            metadata=VectorMetadata(
                ingestion_id="ing-1",
                chunk_id="c1",
                chunk_index=0,
                chunk_strategy="fixed",
                chunk_text=texts[0],
                source_metadata={},
            ),
        ),
        VectorRecord(
            vector=embeddings[1],
            metadata=VectorMetadata(
                ingestion_id="ing-2",
                chunk_id="c2",
                chunk_index=1,
                chunk_strategy="fixed",
                chunk_text=texts[1],
                source_metadata={},
            ),
        ),
        VectorRecord(
            vector=embeddings[2],
            metadata=VectorMetadata(
                ingestion_id="ing-3",
                chunk_id="c3",
                chunk_index=2,
                chunk_strategy="fixed",
                chunk_text=texts[2],
                source_metadata={},
            ),
        ),
    ]

    store.add(records)

    # Query closest to first chunk
    query_chunk = Chunk(chunk_id="query", content=texts[0], metadata={})
    query_embedding = embedder.embed([query_chunk])[0]
    results = store.similarity_search(query_vector=query_embedding, k=2)

    assert len(results) == 2
    assert results[0].metadata.ingestion_id == "ing-1"  # Closest to itself
    assert results[1].metadata.ingestion_id == "ing-2"  # Next closest

    store.delete_by_ingestion_id("ing-1")
    remaining = store.similarity_search(query_vector=query_embedding, k=3)
    assert all(r.metadata.ingestion_id != "ing-1" for r in remaining)
