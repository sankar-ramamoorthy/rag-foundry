# src/ingestion_service/core/pipeline.py

from __future__ import annotations
from typing import Any, Optional

from ingestion_service.core.chunks import Chunk
from ingestion_service.core.chunkers.base import BaseChunker
from ingestion_service.core.chunkers.selector import ChunkerFactory


class IngestionPipeline:
    def __init__(
        self,
        *,
        validator,
        chunker: Optional[BaseChunker] = None,
        embedder,
        vector_store,
    ) -> None:
        """
        Initialize the pipeline with injected collaborators.

        If `chunker` is None, a dynamic chunker will be selected at runtime
        using ChunkerFactory.
        """
        self._validator = validator
        self._chunker = chunker
        self._embedder = embedder
        self._vector_store = vector_store

    # ============================================================
    # Public entrypoint
    # ============================================================

    def run(self, *, text: str, ingestion_id: str) -> None:
        """
        Execute the ingestion pipeline:

        1. Validate input
        2. Chunk into pieces
        3. Generate embeddings
        4. Persist chunks + embeddings
        """

        self._validate(text)
        chunks = self._chunk(text)
        embeddings = self._embed(chunks)
        self._persist(chunks, embeddings, ingestion_id)

    # ============================================================
    # Pipeline steps
    # ============================================================

    def _validate(self, text: str) -> None:
        self._validator.validate(text)

    def _chunk(self, text: str) -> list[Chunk]:
        """
        Chunk text using either:
        - an explicitly provided chunker, or
        - a dynamically selected chunker (factory / heuristic).

        Enriches each Chunk with:
        - chunk_strategy  (semantic strategy: simple / sentence / paragraph)
        - chunker_name    (implementation identity)
        - chunker_params  (parameters used)
        """
        if self._chunker is None:
            selected_chunker, chunker_params = ChunkerFactory.choose_strategy(text)
        else:
            selected_chunker = self._chunker
            chunker_params = {}

        chunks: list[Chunk] = selected_chunker.chunk(text, **chunker_params)

        # Determine semantic strategy (preferred)
        chunk_strategy = getattr(selected_chunker, "chunk_strategy", None)

        for chunk in chunks:
            # Semantic strategy used for chunking (THIS is what tests assert)
            chunk.metadata["chunk_strategy"] = (
                chunk_strategy if chunk_strategy is not None else "unknown"
            )

            # Concrete implementation name (useful for debugging / audits)
            chunk.metadata["chunker_name"] = getattr(
                selected_chunker, "name", selected_chunker.__class__.__name__
            )

            # Parameters used for chunking
            chunk.metadata["chunker_params"] = dict(chunker_params)

        return chunks

    def _embed(self, chunks: list[Chunk]) -> list[Any]:
        """
        Produce embeddings for a list of chunks.
        """
        return self._embedder.embed(chunks)

    def _persist(
        self,
        chunks: list[Chunk],
        embeddings: list[Any],
        ingestion_id: str,
    ) -> None:
        """
        Persist chunks and embeddings to the vector store.
        """
        self._vector_store.persist(
            chunks=chunks,
            embeddings=embeddings,
            ingestion_id=ingestion_id,
        )
