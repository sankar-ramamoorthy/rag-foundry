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
def test_pdf_images_use_standard_ocr_adapter(
    monkeypatch,
    clean_vectors_table,
    test_database_url,
):
    """
    Ensures PDF-extracted images go through the OCR adapter abstraction
    (not a PDF-specific OCR path).
    """

    reset_settings_cache()

    calls = {"count": 0}

    def spy_ocr(self, image_bytes):
        calls["count"] += 1
        return ""

    monkeypatch.setattr(
        "ingestion_service.core.ocr.tesseract_ocr.TesseractOCR.extract_text",
        spy_ocr,
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

    ingestor.ingest_pdf(
        file_bytes=pdf_bytes,
        source_name=pdf_path.name,
        ingestion_id=ingestion_id,
    )

    assert calls["count"] > 0, (
        "OCR adapter was never invoked for PDF images; "
        "possible PDF-specific OCR path regression"
    )
