# tests/integration/test_ingest_ocr_provider_override.py
import io
import json
import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

from ingestion_service.main import app
from ingestion_service.core.config import reset_settings_cache

client = TestClient(app)
pytest_plugins = ["tests.conftest_db"]


@pytest.mark.integration
@pytest.mark.docker
def test_ocr_provider_override_metadata(test_database_url, clean_vectors_table):
    """
    Test that OCR engine can be overridden via metadata['ocr_provider'].
    Currently only 'tesseract' is implemented.
    """
    reset_settings_cache()

    # --- Create a simple image ---
    image = Image.new("RGB", (200, 50), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.text((10, 10), "OVERRIDE TEST", fill=(0, 0, 0))

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)

    metadata = {"ocr_provider": "tesseract"}  # override
    response = client.post(
        "/v1/ingest/file",
        files={"file": ("override_test.png", buf, "image/png")},
        data={"metadata": json.dumps(metadata)},
    )

    assert response.status_code == 202
    data = response.json()
    assert "ingestion_id" in data
    assert data["status"] == "accepted"


@pytest.mark.docker
@pytest.mark.integration
def test_ocr_provider_override_does_not_allow_empty_ocr(
    clean_vectors_table, test_database_url
):
    """
    Images that produce empty OCR output must be rejected,
    even when an OCR provider is explicitly specified via metadata.
    """
    # Small PNG with overridden OCR provider
    image_content = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\nIDATx\xdacd\xf8\x0f\x00\x01\x01\x01\x00"
        b"\x18\xdd\x8d\xdc\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    files = {"file": ("override.png", io.BytesIO(image_content), "image/png")}
    metadata = {"ocr_provider": "tesseract"}

    response = client.post(
        "/v1/ingest/file",
        files=files,
        data={"metadata": json.dumps(metadata)},  # use the variable
    )
    assert response.status_code == 400

    payload = response.json()
    # print(payload)
    assert "ingestion_id" not in payload
    assert payload["detail"] == "No extractable text found in uploaded file"
