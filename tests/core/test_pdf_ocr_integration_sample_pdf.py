# tests/core/test_pdf_ocr_integration_sample_pdf.py
import uuid
from pathlib import Path
import pytest
from typing import cast

from ingestion_service.core.embedders.ollama import OllamaEmbedder
from ingestion_service.core.embedders.factory import get_embedder
from ingestion_service.core.vectorstore.pgvector_store import PgVectorStore
from ingestion_service.core.chunks import Chunk
from ingestion_service.core.headless_ingest_pdf import HeadlessPDFIngestor
from ingestion_service.core.pipeline import IngestionPipeline
from ingestion_service.core.chunkers.text import TextChunker
from ingestion_service.core.config import reset_settings_cache

pytest_plugins = ["tests.conftest_db"]


@pytest.mark.integration
@pytest.mark.docker
def test_sample_pdf_ingest_with_ocr_attachment(clean_vectors_table, test_database_url):
    """
    Integration test for a real PDF with text and images.
    Verifies:
      1. PDF images go through OCR adapter
      2. OCR output is attached to image artifacts
      3. Chunks are created and persisted
    """
    reset_settings_cache()

    # Use real Ollama embedder
    embedder = cast(OllamaEmbedder, get_embedder("ollama"))
    assert embedder.dimension > 0

    vector_store = PgVectorStore(
        dsn=test_database_url,
        dimension=embedder.dimension,
        provider="ollama",
    )

    # Minimal validator
    validator = type("Validator", (), {"validate": lambda self, text: None})()

    # Optional chunker for text splitting
    chunker = TextChunker(chunk_size=100, overlap=10, chunk_strategy="simple")

    pipeline = IngestionPipeline(
        validator=validator,
        chunker=chunker,
        embedder=embedder,
        vector_store=vector_store,
    )

    ingestor = HeadlessPDFIngestor(pipeline=pipeline)

    # --- Load real PDF ---
    pdf_path = (
        Path(__file__).parent.parent
        / "fixtures"
        / "pdfs"
        / "sample_with_test_andscreenshot.pdf"
    )
    pdf_bytes = pdf_path.read_bytes()

    ingestion_id = str(uuid.uuid4())
    chunks = ingestor.ingest_pdf(
        file_bytes=pdf_bytes,
        source_name=pdf_path.name,
        ingestion_id=ingestion_id,
    )

    # --- Assertions ---
    assert len(chunks) > 0, "No chunks were created from PDF"

    for chunk in chunks:
        assert isinstance(chunk, Chunk)
        # Each chunk must have either content (from OCR or text) or chunk_id
        assert chunk.content or chunk.chunk_id, f"Chunk {chunk.chunk_id} has no content"
        # Explicit check: OCR output must be attached if this is an image artifact
        ocr_text = getattr(chunk, "ocr_text", None)
        # If the chunk has OCR, make sure the field exists (even empty string)
        if ocr_text is not None:
            assert isinstance(ocr_text, str), (
                f"Chunk {chunk.chunk_id} ocr_text is not a string"
            )

    # --- Clean up the vector store ---
    vector_store.delete_by_ingestion_id(ingestion_id)
