from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status

from ingestion_service.api.v1.models import (
    IngestRequest,
    IngestResponse,
)

router = APIRouter(tags=["ingestion"])

# ------------------------------------------------------------------
# TEMPORARY in-memory registry (MS2 only)
# ------------------------------------------------------------------
_INGESTION_REGISTRY: set[UUID] = set()


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit content for ingestion",
)
def ingest(request: IngestRequest) -> IngestResponse:
    """
    Accept an ingestion request.

    This endpoint validates the request and returns an ingestion ID.
    Actual ingestion processing is synchronous/headless in MS2.
    """
    ingestion_id = uuid4()
    _INGESTION_REGISTRY.add(ingestion_id)

    return IngestResponse(
        ingestion_id=ingestion_id,
        status="accepted",
    )


@router.get(
    "/ingest/{ingestion_id}",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Get ingestion status",
)
def ingest_status(ingestion_id: UUID) -> IngestResponse:
    """
    Return the current status of an ingestion request.

    MS2 contract:
    - If known → accepted
    - If unknown → 404
    """
    if ingestion_id not in _INGESTION_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingestion ID not found",
        )

    return IngestResponse(
        ingestion_id=ingestion_id,
        status="accepted",
    )
