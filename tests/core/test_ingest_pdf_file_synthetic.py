# tests/core/test_ingest_pdf_file_synthetic.py
import fitz  # PyMuPDF
from ingestion_service.src.core.chunks import Chunk
from ingestion_service.src.core.chunkers.base import BaseChunker
from typing import Any, List


# --- Dummy classes for isolated testing ---
class DummyChunker(BaseChunker):
    name = "dummy"
    chunk_strategy = "dummy"

    def chunk(self, content: Any, **params) -> List[Chunk]:
        return [Chunk(chunk_id="1", content=str(content), metadata={})]


class DummyValidator:
    def validate(self, text: str):
        pass


# --- Helper to generate a simple in-memory PDF ---
def generate_pdf_bytes() -> bytes:
    import io
    import fitz

    pdf_stream = io.BytesIO()
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Hello synthetic PDF!")  # add sample text
    doc.save(pdf_stream)
    doc.close()
    pdf_stream.seek(0)
    return pdf_stream.read()


# --- Test function ---
def test_synthetic_pdf_extraction_order_and_page_number():
    pdf_bytes = generate_pdf_bytes()

    # Open PDF from in-memory bytes
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    extracted_texts = []

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        text = str(page.get_text("text"))  # cast to str for Pyright
        extracted_texts.append(
            {
                "page_number": page_idx + 1,
                "order_index": 1,  # only one chunk per page in DummyChunker
                "content": text.strip(),
            }
        )

    doc.close()

    # --- Assertions ---
    assert len(extracted_texts) == 1
    assert extracted_texts[0]["content"] == "Hello synthetic PDF!"
    assert extracted_texts[0]["page_number"] == 1
    assert extracted_texts[0]["order_index"] == 1
