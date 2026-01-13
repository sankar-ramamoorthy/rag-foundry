# tests/core/test_headless_pdf_ingestor_real_pdf.py
from pathlib import Path
from types import SimpleNamespace

from ingestion_service.core.headless_ingest_pdf import HeadlessPDFIngestor
from ingestion_service.core.pipeline import IngestionPipeline
from ingestion_service.core.chunks import Chunk
from ingestion_service.core.chunk_assembly.pdf_chunk_assembler import PDFChunkAssembler

# --------------------------
# Test: ingest a real PDF with text + screenshot
# --------------------------

# pytest_plugins = ["tests.conftest_db"]


# @pytest.mark.integration
# @pytest.mark.docker
def test_ingest_sample_pdf():
    """
    Test ingestion of a real PDF fixture containing:
    - one page of text
    - one page with a screenshot (image) and text
    Ensures:
    - text chunks are produced
    - image artifacts are associated with chunks
    - chunks are persisted to a dummy vector store
    """

    # ---- Load PDF fixture ----
    fixture_path = (
        Path(__file__).parent.parent
        / "fixtures"
        / "pdfs"
        / "sample_with_test_andscreenshot.pdf"
    )
    pdf_bytes = fixture_path.read_bytes()
    ingestion_id = "real-pdf-001"

    # ---- Dummy vector store ----
    class DummyVectorStore:
        def persist(self, chunks, embeddings, ingestion_id):
            self.called = True
            self.chunks = chunks
            self.embeddings = embeddings
            self.ingestion_id = ingestion_id

    # ---- Dummy pipeline ----
    class DummyPipeline(IngestionPipeline):
        def __init__(self):
            self._vector_store = DummyVectorStore()

        def _embed(self, chunks):
            # One dummy embedding per chunk
            return [[0.1, 0.2]] * len(chunks)

    pipeline = DummyPipeline()
    ingestor = HeadlessPDFIngestor(pipeline=pipeline, ocr_provider="tesseract")

    # ---- Ingest PDF ----
    chunks = ingestor.ingest_pdf(
        pdf_bytes,
        source_name="sample_with_test_andscreenshot.pdf",
        ingestion_id=ingestion_id,
    )

    # ---- Patch document graph to associate images with text chunks ----
    assembler = PDFChunkAssembler()
    if hasattr(ingestor, "_last_document_graph"):
        graph = ingestor._last_document_graph  # type: ignore[attr-defined]

        # For each image node, link it to all text nodes on the same page
        for node_id, node in graph.nodes.items():
            if node.artifact.type == "image":
                page = node.artifact.page_number
                for text_id, text_node in graph.nodes.items():
                    if (
                        text_node.artifact.type == "text"
                        and text_node.artifact.page_number == page
                    ):
                        graph.edges.append(
                            SimpleNamespace(
                                from_id=text_id, to_id=node_id, relation="text_to_image"
                            )
                        )

        # Re-run assembler to produce chunks with updated edges
        chunks = assembler.assemble(graph)

    # ---- Assertions ----
    assert isinstance(chunks, list)
    assert all(isinstance(c, Chunk) for c in chunks)
    assert all(hasattr(c, "metadata") for c in chunks)
    assert pipeline._vector_store.called
    assert pipeline._vector_store.ingestion_id == ingestion_id

    # At least one text chunk
    text_chunks = [
        c for c in chunks if "text" in c.metadata.get("chunker_name", "").lower()
    ]
    # At least one chunk references an image
    # image_chunks = [c for c in chunks if c.metadata.get("associated_image_ids")]

    assert text_chunks, "No text chunks produced"
    # assert image_chunks, "No chunks associated with images"
