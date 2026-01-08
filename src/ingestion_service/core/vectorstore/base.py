# src/ingestion_service/core/vectorstore/base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable, Sequence, List, Dict, Optional


@dataclass
class VectorMetadata:
    ingestion_id: str
    chunk_id: str
    chunk_index: int
    chunk_strategy: str
    chunk_text: str
    source_metadata: Optional[Dict] = field(default_factory=dict)
    provider: str = "mock"  # New attribute for provider name


@dataclass
class VectorRecord:
    vector: Sequence[float]
    metadata: VectorMetadata


class VectorStore(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimension of the vectors."""
        ...

    @abstractmethod
    def add(self, records: Iterable[VectorRecord]) -> None:
        """Add a list of VectorRecords to the store."""
        ...

    @abstractmethod
    def similarity_search(
        self,
        query_vector: Sequence[float],
        k: int,
    ) -> List[VectorRecord]:
        """Return the top k most similar vectors."""
        ...

    @abstractmethod
    def delete_by_ingestion_id(self, ingestion_id: str) -> None:
        """Delete all vectors associated with a given ingestion_id."""
        ...
