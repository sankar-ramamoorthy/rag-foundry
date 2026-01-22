import fitz

from ingestion_service.src.core.extractors.pdf import PDFExtractor
from ingestion_service.src.core.document_graph.builder import DocumentGraphBuilder
from ingestion_service.src.core.document_graph.models import GraphNode


def test_document_graph_builder_is_deterministic():
    # --- create synthetic PDF ---
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Same input every time")
    pdf_bytes = doc.write()
    doc.close()

    extractor = PDFExtractor()
    artifacts = extractor.extract(pdf_bytes, source_name="deterministic.pdf")

    builder = DocumentGraphBuilder()
    graph_a = builder.build(artifacts)
    graph_b = builder.build(artifacts)

    # --- assertions ---
    assert len(graph_a.nodes) == len(graph_b.nodes)

    for node_a, node_b in zip(graph_a.nodes.values(), graph_b.nodes.values()):
        assert isinstance(node_a, GraphNode)
        assert isinstance(node_b, GraphNode)

        # Compare artifact IDs at the node level
        assert node_a.artifact_id == node_b.artifact_id

        # Compare text, page_number if they exist in ExtractedArtifact
        if hasattr(node_a.artifact, "text") and hasattr(node_b.artifact, "text"):
            assert node_a.artifact.text == node_b.artifact.text
        if hasattr(node_a.artifact, "page_number") and hasattr(
            node_b.artifact, "page_number"
        ):
            assert node_a.artifact.page_number == node_b.artifact.page_number
