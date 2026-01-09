# tests/integration/test_ingest_text_file.py
import io
import json
import pytest
from fastapi.testclient import TestClient
from typing import cast
from ingestion_service.core.embedders.ollama import OllamaEmbedder
from ingestion_service.main import app
from ingestion_service.core.vectorstore.pgvector_store import PgVectorStore
from ingestion_service.core.embedders.factory import get_embedder
from ingestion_service.core.chunks import Chunk
from ingestion_service.core.config import reset_settings_cache

client = TestClient(app)
pytest_plugins = ["tests.conftest_db"]


@pytest.mark.integration
@pytest.mark.docker
def test_text_file_ingest_creates_vectors(test_database_url, clean_vectors_table):
    """
    Test uploading a simple text file is ingested correctly and vectors stored.
    """
    reset_settings_cache()

    text_content = "This is a simple test file for embeddings."

    buf = io.BytesIO(text_content.encode("utf-8"))

    metadata = {}
    response = client.post(
        "/v1/ingest/file",
        files={"file": ("test.txt", buf, "text/plain")},
        data={"metadata": json.dumps(metadata)},
    )

    assert response.status_code == 202
    data = response.json()
    ingestion_id = data["ingestion_id"]
    assert data["status"] == "accepted"

    embedder = cast(OllamaEmbedder, get_embedder("ollama"))
    store = PgVectorStore(
        dsn=test_database_url, dimension=embedder.dimension, provider="ollama"
    )

    query_chunk = Chunk(chunk_id="query", content=text_content, metadata={})
    query_embedding = embedder.embed([query_chunk])[0]

    results = store.similarity_search(query_vector=query_embedding, k=1)
    assert any(r.metadata.ingestion_id == ingestion_id for r in results)


@pytest.mark.docker
@pytest.mark.integration
def test_text_file_ingest_creates_vectorsv2(clean_vectors_table, test_database_url):
    from uuid import UUID

    text_content = b"Hello, this is a test text file for ingestion."

    files = {"file": ("test.txt", io.BytesIO(text_content), "text/plain")}
    metadata = {"filename": "test.txt"}

    response = client.post(
        "/v1/ingest/file", files=files,
        data={"metadata": json.dumps(metadata)},  # use the variable
    )
    assert response.status_code == 202

    payload = response.json()
    UUID(payload["ingestion_id"])
    assert payload["status"] == "accepted"
