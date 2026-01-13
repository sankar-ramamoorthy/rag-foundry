# tests/core/test_pdf_ocr_integration_a_pdf.py
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
from ingestion_service.core.config import reset_settings_cache


@pytest.mark.integration
@pytest.mark.docker
def test_headless_pdf_ingest_a_pdf(clean_vectors_table, test_database_url):
    reset_settings_cache()

    # Use real Ollama embedder
    embedder = cast(OllamaEmbedder, get_embedder("ollama"))
    assert embedder.dimension > 0

    vector_store = PgVectorStore(
        dsn=test_database_url,
        dimension=embedder.dimension,
        provider="ollama",
    )

    validator = type("Validator", (), {"validate": lambda self, text: None})()

    pipeline = IngestionPipeline(
        validator=validator,
        vector_store=vector_store,
        embedder=embedder,
    )

    ingestor = HeadlessPDFIngestor(pipeline=pipeline)

    # Directly reference the PDF fixture file
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
        source_name=pdf_path.name,  # now uses the real file name
        ingestion_id=ingestion_id,
    )

    # Basic assertions
    assert len(chunks) > 0
    for chunk in chunks:
        assert isinstance(chunk, Chunk)
        assert chunk.content or chunk.chunk_id

    # Cleanup
    vector_store.delete_by_ingestion_id(ingestion_id)
