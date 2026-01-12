# src/ingestion_service/core/headless_ingest_pdf.py
from __future__ import annotations
from typing import List
from ingestion_service.core.extractors.pdf import PDFExtractor
from ingestion_service.core.document_graph.builder import DocumentGraphBuilder
from ingestion_service.core.chunk_assembly.pdf_chunk_assembler import PDFChunkAssembler
from ingestion_service.core.pipeline import IngestionPipeline
from ingestion_service.core.chunks import Chunk


class HeadlessPDFIngestor:
    """
    Headless ingestion of PDFs using PDFExtractor.

    - Extracts text blocks and images from PDF bytes
    - Builds a deterministic document graph
    - Chunks text artifacts
    - Preserves provenance and metadata
    - Persists embeddings to vector store
    """

    def __init__(self, pipeline: IngestionPipeline):
        self.pipeline = pipeline

    def ingest_pdf(
        self, file_bytes: bytes, source_name: str, ingestion_id: str
    ) -> List[Chunk]:
        # 1️⃣ Extract artifacts from PDF bytes
        extractor = PDFExtractor()
        artifacts = extractor.extract(file_bytes, source_name)

        # 2️⃣ Build document graph
        graph_builder = DocumentGraphBuilder()
        doc_graph = graph_builder.build(artifacts)

        # 3️⃣ Assemble text chunks
        assembler = PDFChunkAssembler()
        chunks = assembler.assemble(doc_graph)

        # 4️⃣ Embed & persist chunks
        embeddings = self.pipeline._embed(chunks)
        self.pipeline._vector_store.persist(
            chunks=chunks, embeddings=embeddings, ingestion_id=ingestion_id
        )

        return chunks
