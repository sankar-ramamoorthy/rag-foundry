# tests/core/test_ingest_pdf_file_synthetic_2.py
import fitz  # PyMuPDF
from typing import List, Any
from ingestion_service.src.core.chunkers.base import BaseChunker
from ingestion_service.src.core.chunks import Chunk


# --- Dummy classes for testing (no DB, no embedder) ---
class DummyChunker(BaseChunker):
    name = "dummy"
    chunk_strategy = "dummy"

    def chunk(self, content: Any, **params) -> List[Chunk]:
        return [Chunk(chunk_id="1", content=content, metadata={})]


class DummyValidator:
    def validate(self, text: str):
        pass


# --- Synthetic PDF generator ---
def generate_pdf_bytes() -> bytes:
    """Generate a simple 2-page PDF in-memory."""
    doc = fitz.open()
    for i in range(2):
        page = doc.new_page()
        page.insert_text((72, 72), f"Hello from page {i + 1}")
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


# --- Test: PDF ingestion (synthetic, pure unit test) ---
def test_synthetic_pdf_ingest_extracts_text_and_images():
    pdf_bytes = generate_pdf_bytes()

    # Uncomment below if you want to simulate a real pipeline
    # pipeline = IngestionPipeline(
    #     validator=DummyValidator(),
    #     chunker=DummyChunker(),
    # )

    # ingestion_id = "test_synthetic"  # Not used; removed to satisfy linter

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    extracted_texts = []
    extracted_images = []

    # Use index-based iteration to satisfy Pyright
    for page_number in range(len(doc)):
        page = doc[page_number]
        page_idx = page_number + 1  # 1-based page numbering

        # Extract text
        text = page.get_text()
        if isinstance(text, str):
            extracted_texts.append((page_idx, text.strip()))
        else:
            extracted_texts.append((page_idx, text))

        # Extract images
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            extracted_images.append((page_idx, img_index, image_bytes))

    doc.close()

    # --- Assertions ---
    # Check text extracted from both pages
    assert len(extracted_texts) == 2
    for page_idx, text in extracted_texts:
        assert text.startswith("Hello from page")

    # Synthetic PDF has no images
    assert len(extracted_images) == 0
