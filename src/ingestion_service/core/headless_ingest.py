# src/ingestion_service/core/headless_ingest.py
from __future__ import annotations
from typing import List

from ingestion_service.core.pipeline import IngestionPipeline
from ingestion_service.core.vectorstore.base import VectorRecord, VectorMetadata


class HeadlessIngestor:
    """
    Runs a headless ingestion pipeline (no FastAPI involved).
    Converts chunks → vectors → persists them to the vector store.
    """

    def __init__(self, pipeline: IngestionPipeline):
        self.pipeline = pipeline

    def ingest_text(self, text: str, ingestion_id: str) -> None:
        """
        Run the pipeline and persist vectors.
        """
        # Step 1-3: validate, chunk, embed
        chunks = self.pipeline._chunk(text)
        embeddings = self.pipeline._embed(chunks)

        # Step 4: convert to VectorRecord for vector store
        vector_records: List[VectorRecord] = []
        for chunk, embedding in zip(chunks, embeddings):
            record = VectorRecord(
                vector=embedding,
                metadata=VectorMetadata(
                    ingestion_id=ingestion_id,
                    chunk_id=chunk.chunk_id,
                    chunk_index=0,  # optional: could number chunks
                    chunk_strategy=chunk.metadata.get("chunking_strategy", "unknown"),
                ),
            )
            vector_records.append(record)

        # Persist to the vector store
        self.pipeline._vector_store.add(vector_records)
