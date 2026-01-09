# tests/integration/test_ingest_image_ocr.py
import io
import json
import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from typing import cast
from ingestion_service.core.embedders.ollama import OllamaEmbedder
from ingestion_service.main import app
from ingestion_service.core.vectorstore.pgvector_store import PgVectorStore
from ingestion_service.core.embedders.factory import get_embedder
from ingestion_service.core.chunks import Chunk
from ingestion_service.core.config import reset_settings_cache
from pathlib import Path
from uuid import UUID

client = TestClient(app)
pytest_plugins = ["tests.conftest_db"]


@pytest.mark.integration
@pytest.mark.docker
def test_image_ingest_creates_vectors(test_database_url, clean_vectors_table):
    """
    Test uploading an image with text is ingested, OCR applied,
    and vectors stored in the real Postgres database.
    """
    reset_settings_cache()

    # --- Create a simple image with text ---
    image = Image.new("RGB", (200, 50), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.text((10, 10), "OCR TEST", fill=(0, 0, 0))

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)

    metadata = {"ocr_provider": "tesseract"}
    response = client.post(
        "/v1/ingest/file",
        files={"file": ("ocr_test.png", buf, "image/png")},
        data={"metadata": json.dumps(metadata)},
    )

    assert response.status_code == 202
    data = response.json()
    ingestion_id = data["ingestion_id"]
    assert data["status"] == "accepted"

    # --- Verify that vector records exist in Postgres ---
    # embedder = get_embedder("ollama")
    embedder = cast(OllamaEmbedder, get_embedder("ollama"))
    store = PgVectorStore(
        dsn=test_database_url, dimension=embedder.dimension, provider="ollama"
    )

    # Search for vectors related to ingestion_id
    query_chunk = Chunk(chunk_id="query", content="OCR TEST", metadata={})
    query_embedding = embedder.embed([query_chunk])[0]

    results = store.similarity_search(query_vector=query_embedding, k=1)
    assert any(r.metadata.ingestion_id == ingestion_id for r in results)


@pytest.mark.docker
@pytest.mark.integration
def test_image_ingest_creates_vectorsv2(clean_vectors_table, test_database_url):
    image_path = Path("tests/fixtures/images/ocr_sample.png")

    with image_path.open("rb") as f:
        files = {"file": ("ocr_sample.png", f, "image/png")}

        response = client.post(
            "/v1/ingest/file",
            files=files,
            data={"metadata": json.dumps({"ocr_provider": "tesseract"})},
        )

    assert response.status_code == 202

    payload = response.json()
    UUID(payload["ingestion_id"])
    assert payload["status"] == "accepted"
