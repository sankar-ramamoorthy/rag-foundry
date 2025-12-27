from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class VectorMetadata:
    ingestion_id: str
    chunk_id: str
    chunk_index: int
    chunk_strategy: str


@dataclass(frozen=True)
class VectorRecord:
    vector: Sequence[float]
    metadata: VectorMetadata


class VectorStore(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Expected dimensionality of stored vectors."""

    @abstractmethod
    def add(self, records: Iterable[VectorRecord]) -> None:
        """Persist vectors and metadata."""

    @abstractmethod
    def similarity_search(
        self,
        query_vector: Sequence[float],
        k: int,
    ) -> list[VectorRecord]:
        """Return top-k most similar vectors."""

    @abstractmethod
    def delete_by_ingestion_id(self, ingestion_id: str) -> None:
        """Remove all vectors associated with an ingestion."""

    @abstractmethod
    def reset(self) -> None:
        """Clear store (testing / dev only)."""
