from fastapi.testclient import TestClient

from ingestion_service.src.api.v1.main import app
import pytest

client = TestClient(app)


pytest_plugins = ["tests.conftest_db"]


@pytest.mark.docker
@pytest.mark.integration
def test_ingestion_status_persisted(client):
    response = client.post(
        "/v1/ingest",
        json={"source_type": "uri", "metadata": {}},
    )
    assert response.status_code == 202
    ingestion_id = response.json()["ingestion_id"]

    status_response = client.get(f"/v1/ingest/{ingestion_id}")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "completed"


@pytest.mark.docker
@pytest.mark.integration
def test_unknown_ingestion_returns_404(client):
    response = client.get("/v1/ingest/11111111-1111-1111-1111-111111111111")
    assert response.status_code == 404
