import uuid
import pytest
from typing import cast
from ingestion_service.core.embedders.ollama import OllamaEmbedder
from ingestion_service.core.embedders.factory import get_embedder
from ingestion_service.core.vectorstore.base import VectorMetadata, VectorRecord
from ingestion_service.core.vectorstore.pgvector_store import PgVectorStore
from ingestion_service.core.chunks import Chunk
from ingestion_service.core.config import reset_settings_cache


@pytest.mark.integration
@pytest.mark.docker
def test_pgvector_store_add_search_delete(clean_vectors_table, test_database_url):
    reset_settings_cache()
    embedder = cast(OllamaEmbedder, get_embedder("ollama"))
    assert embedder.dimension == 768

    store = PgVectorStore(
        dsn=test_database_url,
        dimension=embedder.dimension,
        provider="ollama",
    )

    ingestion_id = str(uuid.uuid4())
    chunk_id = str(uuid.uuid4())
    text = "PgVectorStore integration test with Ollama embeddings"

    # FIXED: Create Chunk objects for embedder
    test_chunk = Chunk(chunk_id=chunk_id, content=text, metadata={"test": True})
    embedding = embedder.embed([test_chunk])[0]

    record = VectorRecord(
        vector=embedding,
        metadata=VectorMetadata(
            ingestion_id=ingestion_id,
            chunk_id=chunk_id,
            chunk_index=0,
            chunk_strategy="test",
            chunk_text=text,
            source_metadata={"test": True},
            provider="ollama",
        ),
    )

    store.add([record])

    query_chunk = Chunk(chunk_id="query-id", content=text, metadata={"test": True})
    query_embedding = embedder.embed([query_chunk])[0]
    results = store.similarity_search(query_vector=query_embedding, k=1)

    assert len(results) == 1
    r = results[0]
    assert r.metadata.ingestion_id == ingestion_id
    assert r.metadata.chunk_id == chunk_id
    assert r.metadata.provider == "ollama"
    assert r.metadata.chunk_text == text

    store.delete_by_ingestion_id(ingestion_id)
    results_after_delete = store.similarity_search(query_vector=query_embedding, k=1)
    assert results_after_delete == []
