from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, Connection
# Database URL for the Postgres container
DATABASE_URL = "postgresql://ingestion_user:ingestion_pass@postgres:5432/ingestion_db"

# Create engine and try to connect to the DB
engine: Engine = create_engine(DATABASE_URL)


try:
    conn: Connection
    conn = engine.connect()
    with conn:
        print("Successfully connected to the database!")
except Exception as e:
    print(f"Error connecting to the database: {e}")
