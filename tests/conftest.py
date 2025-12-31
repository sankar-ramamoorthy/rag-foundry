# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from ingestion_service.main import app  # Import the FastAPI app


# Define the client fixture to be used across your tests
@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def pytest_configure(config):
    # Register custom markers
    config.addinivalue_line("markers", "docker: mark test to run with Docker/Postgres")
    config.addinivalue_line("markers", "integration: mark test as integration test")
