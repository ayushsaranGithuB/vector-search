from urllib.parse import quote

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import UploadFile

from app.api.schemas import SourceUploadCreateInput, SourceOut, UploadCreateOut
from app.core.config import get_settings
from app.db import prisma
from app.services.projects import map_source
from app.services.queue import enqueue_ingestion_for_source

settings = get_settings()


def get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.r2_base_endpoint,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="us-east-1",
        config=Config(signature_version="s3v4"),
    )


def build_r2_object_key(project_slug: str, source_id: str, file_name: str) -> str:
    encoded_name = quote(file_name, safe="")
    return f"projects/{project_slug}/sources/{source_id}/{encoded_name}"


def generate_presigned_upload_url(object_key: str) -> str:
    client = get_r2_client()
    return client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": settings.r2_bucket_name,
            "Key": object_key,
            "ContentType": "application/pdf",
        },
        ExpiresIn=900,
    )


async def upload_source_file_to_r2(
    source_id: str,
    file_bytes: bytes,
    content_type: str,
    file_name: str,
) -> None:
    source = await prisma.source.find_unique(where={"id": source_id}, include={"project": True})
    if source is None:
        raise ValueError("Source not found")

    object_key = build_r2_object_key(source.project.slug, source.id, file_name)
    client = get_r2_client()
    client.put_object(
        Bucket=settings.r2_bucket_name,
        Key=object_key,
        Body=file_bytes,
        ContentType=content_type,
    )


async def create_upload_for_project(payload: SourceUploadCreateInput) -> UploadCreateOut:
    project = await prisma.project.find_unique(where={"slug": payload.project})
    if project is None:
        raise ValueError("Project not found")

    normalized_type = payload.type.upper()
    if normalized_type not in {"PDF", "URL"}:
        raise ValueError("Invalid source type")

    if normalized_type == "PDF" and not payload.file_name:
        raise ValueError("fileName is required for PDF uploads")

    source = await prisma.source.create(
        data={
            "project_id": project.id,
            "name": payload.name.strip(),
            "source_type": normalized_type,
            "source_url": payload.source if normalized_type == "URL" else None,
            "file_name": payload.file_name if normalized_type == "PDF" else None,
            "notes": payload.notes,
            "status": "QUEUED",
            "size_bytes": None,
            "chunk_count": 0,
            "chunk_size": None,
            "chunk_overlap": None,
            "last_synced_at": None,
        }
    )

    upload_url = None
    r2_object_key = None
    if normalized_type == "PDF":
        r2_object_key = build_r2_object_key(project.slug, source.id, payload.file_name)
        upload_url = generate_presigned_upload_url(r2_object_key)

    if normalized_type == "URL":
        await enqueue_ingestion_for_source(source.id)

    return UploadCreateOut(
        source=map_source(source),
        uploadUrl=upload_url,
        r2ObjectKey=r2_object_key,
    )


async def finalize_uploaded_source(source_id: str) -> SourceOut:
    source = await prisma.source.find_unique(
        where={"id": source_id},
        include={"project": True},
    )
    if source is None:
        raise ValueError("Source not found")

    if source.source_type != "PDF":
        raise ValueError("Finalize is only supported for PDF uploads")

    if not source.file_name:
        raise ValueError("PDF source is missing file_name metadata")

    object_key = build_r2_object_key(source.project.slug, source.id, source.file_name)
    client = get_r2_client()
    try:
        metadata = client.head_object(Bucket=settings.r2_bucket_name, Key=object_key)
    except ClientError as error:
        raise ValueError("Uploaded file not found in R2") from error

    size_bytes = int(metadata.get("ContentLength", 0))
    updated_source = await prisma.source.update(
        where={"id": source_id},
        data={"size_bytes": size_bytes, "status": "QUEUED"},
    )
    await enqueue_ingestion_for_source(source_id)
    return map_source(updated_source)
