# tests/api/test_ingest_integration.py
from fastapi.testclient import TestClient
from uuid import UUID

from ingestion_service.main import app

client = TestClient(app)


def test_ingest_returns_accepted():
    response = client.post(
        "/v1/ingest",
        json={"source_type": "file", "metadata": {"filename": "example.txt"}},
    )
    assert response.status_code == 202
    payload = response.json()
    UUID(payload["ingestion_id"])
    assert payload["status"] == "accepted"


def test_ingest_status_visible():
    response = client.post(
        "/v1/ingest",
        json={"source_type": "file", "metadata": {"filename": "example.txt"}},
    )
    assert response.status_code == 202
    ingestion_id = response.json()["ingestion_id"]

    status_response = client.get(f"/v1/ingest/{ingestion_id}")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["ingestion_id"] == ingestion_id
    assert status_payload["status"] == "accepted"
