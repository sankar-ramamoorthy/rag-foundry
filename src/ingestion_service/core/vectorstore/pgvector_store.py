from __future__ import annotations

from typing import Sequence, Iterable, List
import psycopg  # pip install psycopg[binary]

from .base import VectorStore, VectorRecord, VectorMetadata


class PgVectorStore(VectorStore):
    """PostgreSQL + pgvector vector store (psycopg, raw SQL, no ORM)."""

    def __init__(self, dsn: str, dimension: int):
        self._dsn = dsn
        self._dimension = dimension
        self._table_name = "vectors"
        self._ensure_table_exists()

    @property
    def dimension(self) -> int:
        return self._dimension

    def add(self, records: Iterable[VectorRecord]) -> None:
        """Insert vectors and metadata into PostgreSQL using raw SQL."""
        insert_sql = f"""
        INSERT INTO {self._table_name}
        (vector, ingestion_id, chunk_id, chunk_index, chunk_strategy)
        VALUES (%s, %s, %s, %s, %s)
        """
        with psycopg.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                for record in records:
                    vector = record.vector
                    ingestion_id = record.metadata.ingestion_id
                    chunk_id = record.metadata.chunk_id
                    chunk_index = record.metadata.chunk_index
                    chunk_strategy = record.metadata.chunk_strategy

                    params = (
                        vector,
                        ingestion_id,
                        chunk_id,
                        chunk_index,
                        chunk_strategy,
                    )
                    cur.execute(insert_sql, params)  # type: ignore

    def similarity_search(
        self,
        query_vector: Sequence[float],
        k: int,
    ) -> List[VectorRecord]:
        """Return top-k most similar vectors using <-> operator."""
        search_sql = f"""
        SELECT vector, ingestion_id, chunk_id, chunk_index, chunk_strategy
        FROM {self._table_name}
        ORDER BY vector <-> %s
        LIMIT %s
        """
        results: List[VectorRecord] = []
        with psycopg.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(search_sql, (query_vector, k))  # type: ignore
                rows = cur.fetchall()
                for row in rows:
                    vector, ingestion_id, chunk_id, chunk_index, chunk_strategy = row
                    metadata = VectorMetadata(
                        ingestion_id=ingestion_id,
                        chunk_id=chunk_id,
                        chunk_index=chunk_index,
                        chunk_strategy=chunk_strategy,
                    )
                    results.append(VectorRecord(vector=vector, metadata=metadata))
        return results

    def delete_by_ingestion_id(self, ingestion_id: str) -> None:
        """Delete vectors for a given ingestion_id."""
        delete_sql = f"DELETE FROM {self._table_name} WHERE ingestion_id = %s"
        params = (ingestion_id,)
        with psycopg.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(delete_sql, params)  # type: ignore

    def reset(self) -> None:
        """Clear all vectors (for testing/dev)."""
        truncate_sql = f"TRUNCATE TABLE {self._table_name}"
        with psycopg.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(truncate_sql)  # type: ignore

    def _ensure_table_exists(self) -> None:
        """Create table if not exists with pgvector column."""
        table = self._table_name
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table} (
            id SERIAL PRIMARY KEY,
            vector vector({self._dimension}) NOT NULL,
            ingestion_id TEXT NOT NULL,
            chunk_id TEXT NOT NULL,
            chunk_index INT NOT NULL,
            chunk_strategy TEXT NOT NULL
        )
        """
        with psycopg.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(create_sql)  # type: ignore
