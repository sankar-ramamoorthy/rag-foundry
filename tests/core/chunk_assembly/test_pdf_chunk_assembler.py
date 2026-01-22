import fitz

from ingestion_service.src.core.extractors.pdf import PDFExtractor
from ingestion_service.src.core.document_graph.builder import DocumentGraphBuilder
from ingestion_service.src.core.chunk_assembly.pdf_chunk_assembler import PDFChunkAssembler
from ingestion_service.src.core.chunks import Chunk


def test_pdf_chunk_assembler_produces_chunks_with_text():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Chunk me")
    pdf_bytes = doc.write()
    doc.close()

    extractor = PDFExtractor()
    artifacts = extractor.extract(pdf_bytes, source_name="chunk.pdf")

    graph = DocumentGraphBuilder().build(artifacts)
    assembler = PDFChunkAssembler()
    chunks = assembler.assemble(graph)

    assert len(chunks) > 0
    assert all(isinstance(c, Chunk) for c in chunks)

    for chunk in chunks:
        assert isinstance(chunk.content, str)
        assert chunk.content.strip() != ""
        assert "chunk_strategy" in chunk.metadata
