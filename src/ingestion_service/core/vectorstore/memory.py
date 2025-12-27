# core/vectorstore/memory.py
from __future__ import annotations

import math
from typing import Iterable, Sequence

from ingestion_service.core.vectorstore.base import (
    VectorRecord,
    VectorStore,
)


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class InMemoryVectorStore(VectorStore):
    def __init__(self, dimension: int) -> None:
        self._dimension = dimension
        self._records: list[VectorRecord] = []

    @property
    def dimension(self) -> int:
        return self._dimension

    def add(self, records: Iterable[VectorRecord]) -> None:
        for record in records:
            if len(record.vector) != self._dimension:
                raise ValueError(
                    f"Vector dimension mismatch: "
                    f"expected {self._dimension}, "
                    f"got {len(record.vector)}"
                )
            self._records.append(record)

    def similarity_search(
        self,
        query_vector: Sequence[float],
        k: int,
    ) -> list[VectorRecord]:
        if len(query_vector) != self._dimension:
            raise ValueError(
                f"Query vector dimension mismatch: "
                f"expected {self._dimension}, "
                f"got {len(query_vector)}"
            )

        scored = [
            (record, _cosine_similarity(query_vector, record.vector))
            for record in self._records
        ]

        scored.sort(key=lambda pair: pair[1], reverse=True)
        return [record for record, _ in scored[:k]]

    def delete_by_ingestion_id(self, ingestion_id: str) -> None:
        self._records = [
            r for r in self._records if r.metadata.ingestion_id != ingestion_id
        ]

    def reset(self) -> None:
        self._records.clear()
