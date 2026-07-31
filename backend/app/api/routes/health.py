from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    """Simple health check endpoint used by load balancers and monitoring."""
    return {"status": "ok"}


@router.get("/")
def root() -> dict[str, str]:
    """Root endpoint returning a welcome message."""
    return {"message": "Vector Search Backend is running"}
