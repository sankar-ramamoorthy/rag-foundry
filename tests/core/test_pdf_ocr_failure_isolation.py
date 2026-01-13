import uuid
import pytest
from pathlib import Path
from typing import cast

from ingestion_service.core.embedders.ollama import OllamaEmbedder
from ingestion_service.core.headless_ingest_pdf import HeadlessPDFIngestor
from ingestion_service.core.pipeline import IngestionPipeline
from ingestion_service.core.chunkers.text import TextChunker
from ingestion_service.core.embedders.factory import get_embedder
from ingestion_service.core.vectorstore.pgvector_store import PgVectorStore
from ingestion_service.core.config import reset_settings_cache

pytest_plugins = ["tests.conftest_db"]


@pytest.mark.integration
@pytest.mark.docker
def test_pdf_ocr_failure_does_not_abort_ingestion(
    monkeypatch,
    clean_vectors_table,
    test_database_url,
):
    """
    OCR failures must be logged and swallowed.
    Ingestion must continue with native PDF text.
    """

    reset_settings_cache()

    # ---- Force OCR engine to fail ----
    def failing_ocr(self, image_bytes):
        raise RuntimeError("Simulated OCR failure")

    monkeypatch.setattr(
        "ingestion_service.core.ocr.tesseract_ocr.TesseractOCR.extract_text",
        failing_ocr,
    )

    embedder = cast(OllamaEmbedder, get_embedder("ollama"))
    vector_store = PgVectorStore(
        dsn=test_database_url,
        dimension=embedder.dimension,
        provider="ollama",
    )

    chunker = TextChunker(
        chunk_size=100,
        overlap=10,
        chunk_strategy="simple",
    )
    validator = type("Validator", (), {"validate": lambda self, text: None})()

    pipeline = IngestionPipeline(
        validator=validator,
        chunker=chunker,
        embedder=embedder,
        vector_store=vector_store,
    )

    pdf_path = (
        Path(__file__).parent.parent
        / "fixtures"
        / "pdfs"
        / "sample_with_test_andscreenshot.pdf"
    )

    ingestion_id = str(uuid.uuid4())
    pdf_bytes = pdf_path.read_bytes()

    ingestor = HeadlessPDFIngestor(pipeline=pipeline)

    # ---- Must NOT raise ----
    chunks = ingestor.ingest_pdf(
        file_bytes=pdf_bytes,
        source_name=pdf_path.name,
        ingestion_id=ingestion_id,
    )

    assert chunks, "Ingestion failed due to OCR exception"

    # Native PDF text must still exist
    assert any(c.content and c.content.strip() for c in chunks), (
        "No native PDF text survived OCR failure"
    )
