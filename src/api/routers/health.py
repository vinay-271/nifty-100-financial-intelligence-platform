from fastapi import APIRouter


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("")
def health_check():
    """Return API health status."""

    return {
        "status": "ok",
        "service": "N100 Financial Intelligence API",
    }
