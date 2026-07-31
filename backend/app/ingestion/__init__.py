# Re-export the main pipeline entry point for easy access.
from app.ingestion.pipeline import run_pipeline

__all__ = ["run_pipeline"]