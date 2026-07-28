from fastapi import APIRouter, HTTPException, status

from app.services.sources import cancel_source, delete_source

router = APIRouter(prefix="/sources")


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_source(source_id: str):
    """Delete a source and all its data (Pinecone vectors, DB records, R2 file)."""
    try:
        await delete_source(source_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{source_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_source_route(source_id: str):
    """Cancel a QUEUED or PROCESSING source."""
    try:
        await cancel_source(source_id)
        return {"status": "cancelled"}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc