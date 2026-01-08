# src/ingestion_service/core/pipeline.py
from __future__ import annotations
from typing import Any, Optional
import logging

from ingestion_service.core.chunks import Chunk
from ingestion_service.core.chunkers.base import BaseChunker
from ingestion_service.core.chunkers.selector import ChunkerFactory

logging.basicConfig(level=logging.DEBUG)


class IngestionPipeline:
    def __init__(
        self,
        *,
        validator,
        chunker: Optional[BaseChunker] = None,
        embedder,
        vector_store,
    ) -> None:
        self._validator = validator
        self._chunker = chunker
        self._embedder = embedder
        self._vector_store = vector_store

    def run(self, *, text: str, ingestion_id: str) -> None:
        self._validate(text)
        chunks = self._chunk(text)
        embeddings = self._embed(chunks)
        self._persist(chunks, embeddings, ingestion_id)

    def _validate(self, text: str) -> None:
        self._validator.validate(text)

    def _chunk(self, text: str) -> list[Chunk]:
        if self._chunker is None:
            selected_chunker, chunker_params = ChunkerFactory.choose_strategy(text)
        else:
            selected_chunker = self._chunker
            chunker_params = {}

        chunks: list[Chunk] = selected_chunker.chunk(text, **chunker_params)
        chunk_strategy = getattr(selected_chunker, "chunk_strategy", None)

        for chunk in chunks:
            chunk.metadata["chunk_strategy"] = (
                chunk_strategy if chunk_strategy is not None else "unknown"
            )
            chunk.metadata["chunker_name"] = getattr(
                selected_chunker, "name", selected_chunker.__class__.__name__
            )
            chunk.metadata["chunker_params"] = dict(chunker_params)

        return chunks

    def _embed(self, chunks: list[Chunk]) -> list[Any]:
        embeddings = self._embedder.embed(chunks)
        if len(embeddings) != len(chunks):
            raise ValueError(
                f"Embedder mismatch: {len(chunks)} chunks, {len(embeddings)} embeddings"
            )
        return embeddings

    def _persist(
        self,
        chunks: list[Chunk],
        embeddings: list[Any],
        ingestion_id: str,
    ) -> None:
        logging.debug(
            "Pipeline: starting _persist: %d chunks, %d embeddings",
            len(chunks),
            len(embeddings),
        )
        self._vector_store.persist(
            chunks=chunks,
            embeddings=embeddings,
            ingestion_id=ingestion_id,
        )
