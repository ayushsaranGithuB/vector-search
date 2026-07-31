from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Vector Search Backend"
    app_env: str = Field(default="development", alias="APP_ENV")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    database_url: str = Field(alias="NEON_CONNECTION_STRING")
    pinecone_api_key: str = Field(default="", alias="PINECONE_API_KEY")
    pinecone_index: str = Field(default="vector-search", alias="PINECONE_INDEX")
    pinecone_cloud: str = Field(default="aws", alias="PINECONE_CLOUD")
    pinecone_region: str = Field(default="us-east-1", alias="PINECONE_REGION")
    pinecone_environment: str | None = Field(default=None, alias="PINECONE_ENVIRONMENT")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    cloudamqp_url: str = Field(default="", alias="CLOUDAMQP_URL")
    r2_access_key_id: str = Field(default="", alias="R2_ACCESS_KEY_ID")
    r2_secret_access_key: str = Field(default="", alias="R2_SECRET_ACCESS_KEY")
    r2_bucket_name: str = Field(default="", alias="R2_BUCKET_NAME")
    r2_account_id: str = Field(default="", alias="R2_ACCOUNT_ID")
    r2_endpoint: str | None = Field(default=None, alias="R2_ENDPOINT")
    s3_api_endpoint: str | None = Field(default=None, alias="S3_API_ENDPOINT")
    r2_public_url: str = Field(default="", alias="R2_PUBLIC_URL")
    enable_comparison: bool = Field(default=False, alias="ENABLE_COMPARISON")
    cohere_api_key: str = Field(default="", alias="COHERE_API_KEY")
    rerank_top_k: int = Field(default=20, alias="RERANK_TOP_K")  # how many Pinecone results to fetch before reranking

    @property
    def r2_base_endpoint(self) -> str:
        if self.r2_endpoint:
            return self.r2_endpoint
        if self.s3_api_endpoint:
            parsed = urlparse(self.s3_api_endpoint)
            return f"{parsed.scheme}://{parsed.hostname}"
        return f"https://{self.r2_account_id}.r2.cloudflarestorage.com"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
