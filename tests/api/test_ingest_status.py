# tests/api/test_ingest_integration.py
from fastapi.testclient import TestClient
from uuid import UUID

from ingestion_service.main import app

client = TestClient(app)


def test_ingest_returns_accepted():
    """
    Test that POST /v1/ingest returns 202 Accepted and a valid ingestion_id.
    """
    response = client.post(
        "/v1/ingest",
        json={
            "source_type": "file",
            "metadata": {"filename": "example.txt"},
        },
    )

    assert response.status_code == 202
    payload = response.json()

    # ingestion_id must be a valid UUID
    ingestion_id = payload.get("ingestion_id")
    assert ingestion_id is not None
    UUID(ingestion_id)  # will raise ValueError if not a valid UUID

    # status field must be "accepted"
    assert payload.get("status") == "accepted"


def test_ingest_status_visible():
    """
    End-to-end test that:
    1. Submitting an ingestion returns an ID
    2. Fetching /v1/ingest/{id} returns the expected status
    """

    # --- submit ingestion ---
    response = client.post(
        "/v1/ingest",
        json={
            "source_type": "file",
            "metadata": {"filename": "example.txt"},
        },
    )

    assert response.status_code == 202
    payload = response.json()
    ingestion_id = payload["ingestion_id"]

    # --- fetch status ---
    status_response = client.get(f"/v1/ingest/{ingestion_id}")

    # We assume the status endpoint is implemented; returns 200 + JSON
    assert status_response.status_code == 200
    status_payload = status_response.json()

    assert status_payload["ingestion_id"] == ingestion_id
    assert status_payload["status"] == "accepted"
