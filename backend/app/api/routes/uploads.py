from fastapi import APIRouter, HTTPException, status

from app.api.schemas import SourceUploadCreateInput, UploadCreateOut
from app.services.uploads import create_upload_for_project

router = APIRouter(prefix="/uploads")


@router.post("", response_model=UploadCreateOut, status_code=status.HTTP_201_CREATED)
async def create_upload(payload: SourceUploadCreateInput) -> UploadCreateOut:
    try:
        return await create_upload_for_project(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
