# src/ingestion_service/core/chunk_assembly/pdf_chunk_assembler.py
from __future__ import annotations

from typing import Dict, List, Set

from ingestion_service.core.chunks import Chunk
from ingestion_service.core.document_graph.models import DocumentGraph
from ingestion_service.core.chunkers.selector import ChunkerFactory


class PDFChunkAssembler:
    """
    Converts a DocumentGraph into chunks using real chunkers.

    Rules:
    - Only text artifacts are chunked
    - Chunking is delegated to ChunkerFactory
    - Chunk IDs are deterministic
    - Image → text associations are preserved in metadata

    DEBUG MODE: Prints edges, artifact IDs, and image associations
    """

    def assemble(self, graph: DocumentGraph) -> List[Chunk]:
        chunks: List[Chunk] = []

        print("\n=== PDFChunkAssembler Debug Start ===")

        # ---------------------------------------------------------
        # Precompute image → text associations
        # ---------------------------------------------------------
        images_by_text: Dict[str, Set[str]] = {}
        print("\n--- DocumentGraph Edges ---")
        for edge in graph.edges:
            print(f"Edge: {edge.relation}: {edge.from_id} → {edge.to_id}")
            if edge.relation == "image_to_text":
                images_by_text.setdefault(edge.to_id, set()).add(edge.from_id)

        print("\n--- images_by_text mapping ---")
        for text_id, image_ids in images_by_text.items():
            print(f"{text_id}: {image_ids}")

        print("\n--- Graph Nodes ---")
        for node in graph.nodes.values():
            artifact = node.artifact
            print(
                f"Node ID: {node.artifact_id}, \
                    type: {artifact.type}, page: {artifact.page_number}"
            )

        # ---------------------------------------------------------
        # Chunk text artifacts
        # ---------------------------------------------------------
        for node in graph.nodes.values():
            artifact = node.artifact

            if artifact.type != "text" or not artifact.text:
                continue

            # Choose chunker dynamically
            chunker, chunker_params = ChunkerFactory.choose_strategy(artifact.text)
            chunk_strategy = getattr(chunker, "chunk_strategy", "unknown")
            chunker_name = getattr(chunker, "name", chunker.__class__.__name__)

            produced_chunks = chunker.chunk(artifact.text, **chunker_params)

            for idx, produced_chunk in enumerate(produced_chunks):
                produced_chunk.chunk_id = f"{node.artifact_id}:chunk:{idx}"

                associated_image_ids = list(images_by_text.get(node.artifact_id, []))
                produced_chunk.metadata.update(
                    {
                        "source_file": artifact.source_file,
                        "page_numbers": [artifact.page_number],
                        "artifact_ids": [node.artifact_id],
                        "associated_image_ids": associated_image_ids,
                        "chunk_strategy": chunk_strategy,
                        "chunker_name": chunker_name,
                        "chunker_params": dict(chunker_params),
                    }
                )

                print(
                    f"Produced chunk {produced_chunk.chunk_id}, "
                    f"associated_image_ids={associated_image_ids}"
                )

                chunks.append(produced_chunk)

        print("\n=== PDFChunkAssembler Debug End ===\n")
        return chunks
