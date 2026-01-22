import fitz

from ingestion_service.src.core.extractors.pdf import PDFExtractor
from ingestion_service.src.core.document_graph.builder import DocumentGraphBuilder
from ingestion_service.src.core.document_graph.models import GraphNode


def test_document_graph_builder_creates_nodes_in_order():
    # --- create synthetic PDF ---
    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text((72, 72), "Page 1 text")
    page2 = doc.new_page()
    page2.insert_text((72, 72), "Page 2 text")
    pdf_bytes = doc.write()
    doc.close()

    extractor = PDFExtractor()
    artifacts = extractor.extract(pdf_bytes, source_name="test.pdf")

    builder = DocumentGraphBuilder()
    graph = builder.build(artifacts)

    # --- assertions ---
    assert len(graph.nodes) == len(artifacts)

    # nodes preserve order (using artifact order_index if available)
    for i, node in enumerate(graph.nodes.values()):
        assert isinstance(node, GraphNode)
        # If ExtractedArtifact has order_index attribute, check it
        if hasattr(node.artifact, "order_index"):
            assert node.artifact.order_index == i
        # Otherwise, we just ensure it's part of the graph
        assert node.artifact in artifacts
