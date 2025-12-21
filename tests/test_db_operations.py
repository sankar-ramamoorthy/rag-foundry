# src/ingestion_service/tests/test_db_operations.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.ingestion_service.core.models import IngestionRequest
# Adjust import according to your structure

DATABASE_URL = "postgresql://ingestion_user:ingestion_pass@postgres:5432/ingestion_db"

# Create the engine and session maker
engine = create_engine(DATABASE_URL)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Test inserting and fetching a row
def test_insert_fetch_row():
    # Create a new session
    session = Session()

    # Insert a dummy row
    new_ingestion = IngestionRequest(
        ingestion_id="123e4567-e89b-12d3-a456-426614174000",  # Use UUID if you prefer
        source_type="test_source",
        ingestion_metadata={"key": "value"},
        status="pending",
    )
    session.add(new_ingestion)
    session.commit()

    # Fetch the row back
    fetched_row = session.query(IngestionRequest) \
    .filter_by(ingestion_id="123e4567-e89b-12d3-a456-426614174000") \
    .first()

    # Assert that the fetched row matches the inserted one
    assert fetched_row is not None
    assert fetched_row.source_type == "test_source"
    assert fetched_row.status == "pending"

    session.close()
