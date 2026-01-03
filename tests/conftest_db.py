# tests/conftest_db.py
import os
import pytest
from psycopg import connect, sql

# -------------------------------------------------------------------------
# Database fixtures for Docker / pgvector integration tests
#
# IMPORTANT NOTE ABOUT psycopg.sql.SQL AND CURLY BRACES:
#
# psycopg.sql.SQL(...) uses Python-style `{}` formatting internally.
# This means:
#
#   - ANY literal `{}` inside the SQL string will be treated as a
#     positional format placeholder
#   - If you intend a literal JSON default '{}', you MUST escape it as '{{}}'
#
# Failure to do this results in:
#     IndexError: tuple index out of range
#
# This exact issue previously caused flaky test failures.
# Do NOT remove the double braces.
# -------------------------------------------------------------------------


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """
    Return DATABASE_URL from environment.

    Must be set before running Docker tests, e.g.:
    postgresql://ingestion_user:ingestion_pass@postgres:5432/ingestion_test
    """
    return os.environ["DATABASE_URL"]


@pytest.fixture
def clean_vectors_table(test_database_url):
    """
    Ensure a clean 'vectors' table in 'ingestion_service' schema for each test.

    This fixture intentionally DROPS and RECREATES the table to guarantee:
    - schema correctness
    - no cross-test contamination
    - alignment with Alembic MVP schema
    """
    schema = "ingestion_service"
    table = "vectors"

    create_table_sql = sql.SQL(
        """
        CREATE TABLE {schema}.{table} (
            id SERIAL PRIMARY KEY,
            vector vector(3) NOT NULL,

            ingestion_id TEXT NOT NULL,
            chunk_id TEXT NOT NULL,
            chunk_index INT NOT NULL,
            chunk_strategy TEXT NOT NULL,

            chunk_text TEXT NOT NULL,
            source_metadata JSONB NOT NULL DEFAULT '{{}}'
        )
        """
    ).format(
        schema=sql.Identifier(schema),
        table=sql.Identifier(table),
    )

    with connect(test_database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("DROP TABLE IF EXISTS {schema}.{table} CASCADE").format(
                    schema=sql.Identifier(schema),
                    table=sql.Identifier(table),
                )
            )
            cur.execute(create_table_sql)

    # Run the test
    yield

    # Optional cleanup (kept for clarity and safety)
    with connect(test_database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("TRUNCATE TABLE {schema}.{table}").format(
                    schema=sql.Identifier(schema),
                    table=sql.Identifier(table),
                )
            )
