import pytest
import psycopg
from psycopg import sql

from ingestion_service.src.core.vectorstore.pgvector_store import PgVectorStore

pytest_plugins = ["tests.conftest_db"]


@pytest.mark.docker
@pytest.mark.integration
def test_pgvector_store_fails_fast_when_table_missing(test_database_url):
    """
    PgVectorStore should fail fast with a clear error if the expected
    vectors table does not exist.
    """

    # Ensure the table is absent
    drop_sql = sql.SQL("DROP TABLE IF EXISTS {schema}.{table} CASCADE").format(
        schema=sql.Identifier("ingestion_service"), table=sql.Identifier("vectors")
    )

    with psycopg.connect(test_database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(drop_sql)

    # Instantiating the store should now fail immediately
    with pytest.raises(
        RuntimeError,
        match=r"PgVectorStore schema validation failed.*vectors.*migrations",
    ):
        PgVectorStore(
            dsn=test_database_url,
            dimension=3,
        )
