from fastapi import APIRouter, HTTPException, status

from app.api.schemas import SourceUploadCreateInput, UploadCreateOut
from app.services.uploads import create_upload_for_project, finalize_uploaded_source

router = APIRouter(prefix="/uploads")


@router.post("", response_model=UploadCreateOut, status_code=status.HTTP_201_CREATED)
async def create_upload(payload: SourceUploadCreateInput) -> UploadCreateOut:
    try:
        return await create_upload_for_project(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{source_id}/finalize", response_model=UploadCreateOut, status_code=status.HTTP_200_OK)
async def finalize_upload(source_id: str) -> UploadCreateOut:
    try:
        source = await finalize_uploaded_source(source_id)
        return UploadCreateOut(source=source, uploadUrl=None, r2ObjectKey=None)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
