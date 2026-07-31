from urllib.parse import quote

import boto3
from botocore.config import Config

from app.core.config import get_settings

settings = get_settings()


def get_r2_client():
    """Return a boto3 S3 client configured for Cloudflare R2."""
    return boto3.client(
        "s3",
        endpoint_url=settings.r2_base_endpoint,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="us-east-1",
        config=Config(signature_version="s3v4"),
    )


def build_r2_object_key(project_slug: str, source_id: str, file_name: str) -> str:
    """Build a unique R2 object key for a source file within a project."""
    encoded_name = quote(file_name, safe="")
    return f"projects/{project_slug}/sources/{source_id}/{encoded_name}"


def generate_presigned_upload_url(object_key: str) -> str:
    """Generate a presigned URL for direct browser-to-R2 PDF upload."""
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
